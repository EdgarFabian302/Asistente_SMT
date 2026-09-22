import streamlit as st
import plotly.express as px
from modules.spi_parser import cargar_reporte_spi, obtener_defectos
from modules.dss_engine import evaluar_condiciones_gkg, generar_recomendaciones_dss

st.set_page_config(page_title="DSS SMT - GKG & SPI", layout="wide")

# CSS personalizado para compactar y agregar clases de atenuado/sombreado
st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
        h1 { font-size: 1.6rem !important; margin-bottom: 0rem !important; }
        h2, h3, h4 { font-size: 1.1rem !important; margin-top: 0.2rem !important; margin-bottom: 0.2rem !important; }
        div[data-testid="stVerticalBlock"] > div { gap: 0.25rem !important; }
        .stNumberInput input { height: 32px !important; }
        div[data-baseweb="input"] { min-height: 32px !important; }
        
        /* Estilos para sombreado cuando un ciclo está deshabilitado */
        .cycle-disabled {
            opacity: 0.35;
            pointer-events: none;
            filter: grayscale(80%);
            transition: all 0.3s ease;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Asistente Inteligente SMT - GKG & SPI")

# --- DISTRIBUCIÓN SUPERIOR EN 3 COLUMNAS ---
col_param, col_c1, col_c2 = st.columns([1, 1.25, 1.25], gap="small")

# --- COLUMNA 1: PARÁMETROS Y CLIMA ---
with col_param:
    st.markdown("### ⚙️ Proceso & Clima")
    
    cp1, cp2 = st.columns(2)
    temp_interna = cp1.number_input("Temp (°C)", 18.0, 35.0, 23.5, step=0.5)
    humedad = cp2.number_input("Humedad (%)", 30, 80, 50, step=1)
    
    cp3, cp4 = st.columns(2)
    presion = cp3.number_input("Presión (Kg)", 3.0, 15.0, 8.5, step=0.5)
    velocidad = cp4.number_input("Velocidad (mm/s)", 10, 100, 40, step=5)
    
    direccion_limpieza = st.selectbox(
        "Dirección Limpieza Carro",
        ["Unidireccional (Front to Rear)", "Bidireccional (Front-Rear-Front)"],
        index=0
    )

OPCIONES_ETAPAS = ["Ninguna", "W (Mojado)", "D (Seco)", "V (Vacío)"]

# --- COLUMNA 2: CICLO 1 ---
with col_c1:
    st.markdown("### 🔹 Ciclo 1 (Frecuente)")
    head_c1, toggle_c1 = st.columns([1.2, 1])
    c1_activo = toggle_c1.toggle("Habilitar C1", value=True, key="c1_activo")
    
    css_class_c1 = "" if c1_activo else "cycle-disabled"
    st.markdown(f'<div class="{css_class_c1}">', unsafe_allow_html=True)
    
    frec1 = head_c1.number_input("Frecuencia (Cada N PCBs)", 1, 10, 1, key="frec1", disabled=not c1_activo)
    
    # Encabezados
    h1, h2, h3, h4 = st.columns([1.3, 0.6, 1.1, 0.9])
    h1.caption("Paso / Etapa")
    h2.caption("On")
    h3.caption("Vel (mm/s)")
    h4.caption("Rotar")

    # Paso 1
    r1, r2, r3, r4 = st.columns([1.3, 0.6, 1.1, 0.9])
    etapa1_c1 = r1.selectbox("Paso 1 C1", OPCIONES_ETAPAS, index=1, key="etapa1_c1", disabled=not c1_activo, label_visibility="collapsed")
    use_p1_c1 = r2.checkbox("", value=(etapa1_c1 != "Ninguna"), key="use_p1_c1", disabled=(not c1_activo or etapa1_c1 == "Ninguna"))
    v_p1_c1 = r3.number_input("", 10, 100, 60, key="v_p1_c1", disabled=(not c1_activo or not use_p1_c1), label_visibility="collapsed")
    rot_p1_c1 = r4.checkbox("Papel", value=False, key="rot_p1_c1", disabled=(not c1_activo or not use_p1_c1))

    # Paso 2
    r1, r2, r3, r4 = st.columns([1.3, 0.6, 1.1, 0.9])
    etapa2_c1 = r1.selectbox("Paso 2 C1", OPCIONES_ETAPAS, index=2, key="etapa2_c1", disabled=not c1_activo, label_visibility="collapsed")
    use_p2_c1 = r2.checkbox("", value=(etapa2_c1 != "Ninguna"), key="use_p2_c1", disabled=(not c1_activo or etapa2_c1 == "Ninguna"))
    v_p2_c1 = r3.number_input("", 10, 100, 50, key="v_p2_c1", disabled=(not c1_activo or not use_p2_c1), label_visibility="collapsed")
    rot_p2_c1 = r4.checkbox("Papel", value=True, key="rot_p2_c1", disabled=(not c1_activo or not use_p2_c1))

    # Paso 3
    r1, r2, r3, r4 = st.columns([1.3, 0.6, 1.1, 0.9])
    etapa3_c1 = r1.selectbox("Paso 3 C1", OPCIONES_ETAPAS, index=3, key="etapa3_c1", disabled=not c1_activo, label_visibility="collapsed")
    use_p3_c1 = r2.checkbox("", value=(etapa3_c1 != "Ninguna"), key="use_p3_c1", disabled=(not c1_activo or etapa3_c1 == "Ninguna"))
    v_p3_c1 = r3.number_input("", 10, 100, 30, key="v_p3_c1", disabled=(not c1_activo or not use_p3_c1), label_visibility="collapsed")
    rot_p3_c1 = r4.checkbox("Papel", value=True, key="rot_p3_c1", disabled=(not c1_activo or not use_p3_c1))

    st.markdown('</div>', unsafe_allow_html=True)

c1_config = {
    'activo': c1_activo,
    'frecuencia': frec1 if c1_activo else 0,
    'pasos': [
        {'etapa': etapa1_c1, 'on': use_p1_c1 if c1_activo else False, 'vel': v_p1_c1, 'rotar': rot_p1_c1 if (c1_activo and use_p1_c1) else False},
        {'etapa': etapa2_c1, 'on': use_p2_c1 if c1_activo else False, 'vel': v_p2_c1, 'rotar': rot_p2_c1 if (c1_activo and use_p2_c1) else False},
        {'etapa': etapa3_c1, 'on': use_p3_c1 if c1_activo else False, 'vel': v_p3_c1, 'rotar': rot_p3_c1 if (c1_activo and use_p3_c1) else False},
    ]
}

# --- COLUMNA 3: CICLO 2 ---
with col_c2:
    st.markdown("### 🔸 Ciclo 2 (Profundo)")
    head_c2, toggle_c2 = st.columns([1.2, 1])
    c2_activo = toggle_c2.toggle("Habilitar C2", value=True, key="c2_activo")
    
    css_class_c2 = "" if c2_activo else "cycle-disabled"
    st.markdown(f'<div class="{css_class_c2}">', unsafe_allow_html=True)
    
    frec2 = head_c2.number_input("Frecuencia (Cada N PCBs)", 1, 20, 3, key="frec2", disabled=not c2_activo)
    
    # Encabezados
    h1, h2, h3, h4 = st.columns([1.3, 0.6, 1.1, 0.9])
    h1.caption("Paso / Etapa")
    h2.caption("On")
    h3.caption("Vel (mm/s)")
    h4.caption("Rotar")

    # Paso 1
    r1, r2, r3, r4 = st.columns([1.3, 0.6, 1.1, 0.9])
    etapa1_c2 = r1.selectbox("Paso 1 C2", OPCIONES_ETAPAS, index=1, key="etapa1_c2", disabled=not c2_activo, label_visibility="collapsed")
    use_p1_c2 = r2.checkbox("", value=(etapa1_c2 != "Ninguna"), key="use_p1_c2", disabled=(not c2_activo or etapa1_c2 == "Ninguna"))
    v_p1_c2 = r3.number_input("", 10, 100, 60, key="v_p1_c2", disabled=(not c2_activo or not use_p1_c2), label_visibility="collapsed")
    rot_p1_c2 = r4.checkbox("Papel", value=False, key="rot_p1_c2", disabled=(not c2_activo or not use_p1_c2))

    # Paso 2
    r1, r2, r3, r4 = st.columns([1.3, 0.6, 1.1, 0.9])
    etapa2_c2 = r1.selectbox("Paso 2 C2", OPCIONES_ETAPAS, index=2, key="etapa2_c2", disabled=not c2_activo, label_visibility="collapsed")
    use_p2_c2 = r2.checkbox("", value=(etapa2_c2 != "Ninguna"), key="use_p2_c2", disabled=(not c2_activo or etapa2_c2 == "Ninguna"))
    v_p2_c2 = r3.number_input("", 10, 100, 50, key="v_p2_c2", disabled=(not c2_activo or not use_p2_c2), label_visibility="collapsed")
    rot_p2_c2 = r4.checkbox("Papel", value=True, key="rot_p2_c2", disabled=(not c2_activo or not use_p2_c2))

    # Paso 3
    r1, r2, r3, r4 = st.columns([1.3, 0.6, 1.1, 0.9])
    etapa3_c2 = r1.selectbox("Paso 3 C2", OPCIONES_ETAPAS, index=3, key="etapa3_c2", disabled=not c2_activo, label_visibility="collapsed")
    use_p3_c2 = r2.checkbox("", value=(etapa3_c2 != "Ninguna"), key="use_p3_c2", disabled=(not c2_activo or etapa3_c2 == "Ninguna"))
    v_p3_c2 = r3.number_input("", 10, 100, 30, key="v_p3_c2", disabled=(not c2_activo or not use_p3_c2), label_visibility="collapsed")
    rot_p3_c2 = r4.checkbox("Papel", value=True, key="rot_p3_c2", disabled=(not c2_activo or not use_p3_c2))

    st.markdown('</div>', unsafe_allow_html=True)

c2_config = {
    'activo': c2_activo,
    'frecuencia': frec2 if c2_activo else 0,
    'pasos': [
        {'etapa': etapa1_c2, 'on': use_p1_c2 if c2_activo else False, 'vel': v_p1_c2, 'rotar': rot_p1_c2 if (c2_activo and use_p1_c2) else False},
        {'etapa': etapa2_c2, 'on': use_p2_c2 if c2_activo else False, 'vel': v_p2_c2, 'rotar': rot_p2_c2 if (c2_activo and use_p2_c2) else False},
        {'etapa': etapa3_c2, 'on': use_p3_c2 if c2_activo else False, 'vel': v_p3_c2, 'rotar': rot_p3_c2 if (c2_activo and use_p3_c2) else False},
    ]
}

# Alertas del microclima en cinta delgada
alertas_clima = evaluar_condiciones_gkg(temp_interna, humedad)
for alerta in alertas_clima:
    st.info(alerta)

st.markdown("---")

# --- SECCIÓN INFERIOR: SPI Y RESULTADOS ---
col_file, col_tabs = st.columns([1, 2.5])

with col_file:
    st.markdown("### 📊 Reporte SPI")
    archivo_cargado = st.file_uploader("Subir CSV SPI", type=["csv"], label_visibility="collapsed")

if archivo_cargado is not None:
    df_spi = cargar_reporte_spi(archivo_cargado)
    
    if df_spi is not None:
        with col_tabs:
            tab1, tab2, tab3, tab4 = st.tabs([
                "📋 Datos", 
                "⚠️ Defectos", 
                "📊 Histograma",
                "💡 Recomendaciones DSS"
            ])
            
            with tab1:
                st.dataframe(df_spi, use_container_width=True, height=220)
                
            with tab2:
                defectos = obtener_defectos(df_spi)
                if not defectos.empty:
                    st.warning(f"Se detectaron {len(defectos)} pad(s) con anomalías:")
                    st.dataframe(defectos[["Componente", "Pad_ID", "Volumen_Porcentaje", "Estado"]], use_container_width=True, height=180)
                else:
                    st.success("No se encontraron defectos en esta PCB.")

            with tab3:
                fig_vol = px.histogram(
                    df_spi, 
                    x="Volumen_Porcentaje", 
                    color="Estado",
                    nbins=20,
                    height=220,
                    title="Distribución de Volumen (%)",
                    labels={"Volumen_Porcentaje": "Volumen (%)", "count": "Pads"},
                    color_discrete_map={
                        "PASS": "#2ecc71",
                        "LOW_VOL": "#e74c3c",
                        "HIGH_VOL": "#f39c12",
                        "BRIDGE": "#9b59b6"
                    }
                )
                fig_vol.update_layout(margin=dict(l=10, r=10, t=30, b=10))
                fig_vol.add_vline(x=100, line_dash="dash", line_color="green")
                fig_vol.add_vline(x=70, line_dash="dot", line_color="red")
                fig_vol.add_vline(x=150, line_dash="dot", line_color="red")
                st.plotly_chart(fig_vol, use_container_width=True)

            with tab4:
                recs = generar_recomendaciones_dss(
                    df_spi, 
                    temp_interna, 
                    humedad, 
                    presion, 
                    velocidad, 
                    c1_config, 
                    c2_config, 
                    direccion_limpieza
                )
                for r in recs:
                    st.write(r)