import streamlit as st
from modules.spi_parser import cargar_reporte_spi, obtener_defectos
from modules.dss_engine import evaluar_condiciones_gkg, generar_recomendaciones_dss

st.set_page_config(page_title="DSS SMT - GKG & SPI", layout="wide")

st.title("Asistente Inteligente SMT - GKG & SPI")
st.subheader("Sistema de Soporte a Decisiones para Impresión de Pasta")

# --- SECCIÓN 1: CAPTURA DE PARÁMETROS OPERATIVOS ---
st.header("1. Condición Ambiental Interna y de Proceso (GKG P6 Max)")
col1, col2 = st.columns(2)

with col1:
    temperatura_interna = st.slider("Temperatura Interna GKG (°C)", 18.0, 35.0, 23.5)
    presion = st.slider("Presión de Squeegee (Kg)", 3.0, 15.0, 8.5)

with col2:
    humedad = st.slider("Humedad Relativa (%)", 30, 80, 50)
    velocidad = st.slider("Velocidad de Impresión (mm/s)", 10, 100, 40)

# Monitoreo de microclima
alertas_clima = evaluar_condiciones_gkg(temperatura_interna, humedad)
for alerta in alertas_clima:
    st.info(alerta)

st.divider()

# --- SECCIÓN 2: CARGA Y ANÁLISIS DEL ARCHIVO SPI ---
st.header("2. Reporte de Inspección de Pasta (SPI)")

archivo_cargado = st.file_uploader("Sube el archivo CSV del reporte SPI", type=["csv"])

if archivo_cargado is not None:
    df_spi = cargar_reporte_spi(archivo_cargado)
    
    if df_spi is not None:
        st.success("¡Archivo cargado y procesado correctamente!")
        
        tab1, tab2, tab3 = st.tabs(["📋 Datos Completos", "⚠️ Defectos Detectados", "💡 Diagnóstico & Recomendaciones DSS"])
        
        with tab1:
            st.dataframe(df_spi, use_container_width=True)
            
        with tab2:
            defectos = obtener_defectos(df_spi)
            if not defectos.empty:
                st.warning(f"Se detectaron {len(defectos)} pad(s) con anomalías:")
                st.dataframe(defectos[["Componente", "Pad_ID", "Volumen_Porcentaje", "Estado"]], use_container_width=True)
            else:
                st.success("No se encontraron defectos en esta PCB.")
                
        with tab3:
            st.subheader("Recomendaciones del Motor DSS para GKG P6 Max")
            recs = generar_recomendaciones_dss(df_spi, temperatura_interna, humedad, presion, velocidad)
            for r in recs:
                st.write(r)