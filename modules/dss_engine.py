# modules/dss_engine.py

def evaluar_condiciones_gkg(temp_interna, humedad_relativa):
    """
    Evalúa las condiciones ambientales internas del gabinete de la GKG P6 Max.
    """
    alertas = []
    
    if temp_interna > 25.0:
        alertas.append(
            f"⚠️ **Alerta Ambiental (GKG):** Temperatura interna elevada ({temp_interna:.1f}°C). "
            f"Verifique y active el enfriador auxiliar tipo 'pingüino' para evitar la pérdida de viscosidad de la pasta de soldadura."
        )
    elif temp_interna < 20.0:
        alertas.append(
            f"ℹ️ **Condición Ambiental:** Temperatura interna baja ({temp_interna:.1f}°C). "
            f"La pasta puede presentar alta tixotropía / rigidez; considere aumentar los pases de amasadura previa."
        )
        
    if humedad_relativa > 60:
        alertas.append(
            f"⚠️ **Alerta de Humedad:** Humedad relativa alta ({humedad_relativa}% RH). "
            f"Riesgo de absorción de humedad en el flux (causa de 'slump', puentes y 'solder balls' en reflujo)."
        )
    elif humedad_relativa < 30:
        alertas.append(
            f"⚠️ **Alerta de Humedad Bajas:** Humedad relativa muy baja ({humedad_relativa}% RH). "
            f"Acelera el secado del solvente de la pasta en el stencil."
        )
        
    return alertas


def evaluar_secuencia_limpieza(c1_config, c2_config):
    """
    Analiza la secuencia dinámica de pasos (Paso 1, 2, 3) configurada en C1 y C2
    y genera advertencias sobre la efectividad del proceso de limpieza.
    """
    recom = []
    
    for idx, c_config in enumerate([c1_config, c2_config], start=1):
        if not c_config.get('activo', True):
            continue
            
        pasos = c_config.get('pasos', [])
        pasos_activos = [p['etapa'] for p in pasos if p.get('on') and p.get('etapa') != "Ninguna"]
        
        if not pasos_activos:
            recom.append(f"⚠️ **Ciclo {idx}:** Está habilitado pero no tiene ninguna etapa seleccionada en 'On'.")
            continue
            
        # Validar si el ciclo empieza con Vacío (V) sin secado previo
        if pasos_activos[0].startswith("V"):
            recom.append(
                f"⚠️ **Ciclo {idx}:** Iniciar el ciclo directamente con **Vacío (V)** puede succionar "
                "demasiada pasta fresca de las aberturas finas. Se sugiere iniciar con **Seco (D)** "
                "para remover residuos superficiales primero."
            )
            
        # Validar si hay mojado (W) sin un secado posterior
        if any(p.startswith("W") for p in pasos_activos):
            pos_w = next(i for i, p in enumerate(pasos_activos) if p.startswith("W"))
            pasos_posteriores = pasos_activos[pos_w + 1:]
            if not any(p.startswith("D") for p in pasos_posteriores):
                recom.append(
                    f"💡 **Ciclo {idx}:** Tienes una etapa de **Mojado (W)** sin un paso de **Seco (D)** "
                    "posterior. Se recomienda agregar un paso Seco al final para evitar solvente "
                    "residual debajo del stencil."
                )
                
    return recom


def generar_recomendaciones_dss(
    df_spi, temp_interna, humedad_relativa, presion_actual, velocidad_actual,
    c1_config, c2_config, direccion_limpieza
):
    """
    Motor de Decisiones Avanzado (DSS) adaptado a la arquitectura modular por ciclo (Ciclo 1 y Ciclo 2)
    y secuencias de pasos dinámicas con retrocompatibilidad segura.
    """
    recomendaciones = []
    
    if df_spi is None or df_spi.empty:
        return ["Sin datos de SPI para analizar."]
    
    # -------------------------------------------------------------
    # HELPERS SEGUROS PARA VERIFICAR ETAPAS (NUEVO + ANTIGUO ESQUEMA)
    # -------------------------------------------------------------
    def tiene_etapa(c_config, prefijo_etapa, clave_antigua):
        if not c_config.get('activo', True):
            return False
        if 'pasos' in c_config and c_config['pasos']:
            return any(p.get('etapa', '').startswith(prefijo_etapa) for p in c_config['pasos'] if p.get('on'))
        return c_config.get(clave_antigua, False)

    def etapa_tiene_rotacion(c_config, prefijo_etapa, clave_antigua_w, clave_antigua_rot):
        if not c_config.get('activo', True):
            return False
        if 'pasos' in c_config and c_config['pasos']:
            return any(p.get('etapa', '').startswith(prefijo_etapa) and p.get('rotar') for p in c_config['pasos'] if p.get('on'))
        return c_config.get(clave_antigua_w, False) and c_config.get(clave_antigua_rot, False)

    def obtener_vel_etapa(c_config, prefijo_etapa, clave_antigua_v, clave_antigua_vel):
        if not c_config.get('activo', True):
            return 0
        if 'pasos' in c_config and c_config['pasos']:
            for p in c_config['pasos']:
                if p.get('on') and p.get('etapa', '').startswith(prefijo_etapa):
                    return p.get('vel', 0)
            return 0
        return c_config.get(clave_antigua_vel, 0) if c_config.get(clave_antigua_v, False) else 0

    # 1. VERIFICACIONES TÉCNICAS DE CONFIGURACIÓN DE LIMPIEZA (GKG)
    c1_rot_w = etapa_tiene_rotacion(c1_config, "W", 'use_w', 'rot_w')
    c2_rot_w = etapa_tiene_rotacion(c2_config, "W", 'use_w', 'rot_w')
    
    if c1_rot_w or c2_rot_w:
        ciclos_afectados = []
        if c1_rot_w: ciclos_afectados.append("Ciclo 1")
        if c2_rot_w: ciclos_afectados.append("Ciclo 2")
        
        recomendaciones.append(
            f"⚙️ **Optimización de Solvente (GKG):** Se detectó giro/rotación de papel activo durante la sub-etapa **Mojado (W)** en {', '.join(ciclos_afectados)}. "
            "Desactívelo en la etapa W para evitar desperdiciar solvente y permitir que el rollo se impregne de manera uniforme."
        )
        
    v_v1 = obtener_vel_etapa(c1_config, "V", 'use_v', 'v_v')
    v_v2 = obtener_vel_etapa(c2_config, "V", 'use_v', 'v_v')
    if v_v1 > 45 or v_v2 > 45:
        recomendaciones.append(
            "⚠️ **Velocidad de Vacío Elevada:** La sub-etapa Vacío (V) supera los 45 mm/s. "
            "Se recomienda ajustarla entre **20 - 30 mm/s** para garantizar tiempo de succión suficiente en aberturas finas (Fine-Pitch / BGA)."
        )

    # Evaluación de orden y secuencia lógica de pasos
    alertas_secuencia = evaluar_secuencia_limpieza(c1_config, c2_config)
    for s in alertas_secuencia:
        recomendaciones.append(s)

    # 2. CONTEO Y ANÁLISIS DE DEFECTOS DEL REPORTE SPI
    conteo_estados = df_spi['Estado'].value_counts().to_dict()
    num_low = conteo_estados.get('LOW_VOL', 0)
    num_high = conteo_estados.get('HIGH_VOL', 0)
    num_bridge = conteo_estados.get('BRIDGE', 0)
    total_pads = len(df_spi)
    
    defectos_df = df_spi[df_spi['Estado'] != 'PASS']
    comp_criticos = []
    if not defectos_df.empty:
        comp_criticos = defectos_df['Componente'].unique().tolist()
    
    c1_tiene_v = tiene_etapa(c1_config, "V", 'use_v')
    c2_tiene_v = tiene_etapa(c2_config, "V", 'use_v')
    c2_tiene_w = tiene_etapa(c2_config, "W", 'use_w')

    # 3. DIAGNÓSTICO MATRICIAL Y ACCIONES CORRECTIVAS
    if num_low > 0 and (num_bridge > 0 or num_high > 0):
        recomendaciones.append("🚨 **Diagnóstico Crítico: Defectos Inversos Simultáneos (Bajo Volumen + Puentes/Exceso)**")
        recomendaciones.append(
            "• **Causa Raíz:** Inestabilidad por contaminación inferior del stencil o flexión de la PCB durante el proceso de impresión."
        )
        
        if not c2_config.get('activo', True):
            recomendaciones.append(
                "• **Estrategia Limpieza:** **Active el Ciclo 2** en modo profundo (Mojado + Seco + Vacío) cada 2 o 3 PCBs para limpiar la cara inferior del stencil."
            )
        elif not c2_tiene_w:
            recomendaciones.append(
                "• **Estrategia Limpieza:** Habilite la sub-etapa **Mojado (W)** en el Ciclo 2 para disolver la pasta reseca adherida a las paredes de los apertures."
            )
            
        frecuencia_c2 = c2_config.get('frecuencia', 0)
        if c2_config.get('activo', True) and frecuencia_c2 > 3:
            recomendaciones.append(
                f"• **Frecuencia de Limpieza:** Su Ciclo 2 está programado cada {frecuencia_c2} PCBs. "
                "Reduzca el intervalo a **cada 2 PCBs** de forma temporal."
            )

        if "Bidireccional" in direccion_limpieza and num_bridge > 0:
            recomendaciones.append(
                "• **Dirección de Limpieza:** Cambie de Bidireccional a **Unidireccional**. El barrido de retorno en bidireccional puede re-contaminar pads limpios."
            )

        recomendaciones.append(
            "• **Soporte Mecánico:** Revise la alineación y altura de los pines de soporte (Support Pins / Vac Block). La flexión del circuito provoca este patrón variante."
        )

    elif num_low > 0 and num_bridge == 0 and num_high == 0:
        pct_low = (num_low / total_pads) * 100
        recomendaciones.append(f"🔍 **Diagnóstico SPI: Bajo Volumen de Pasta (LOW_VOL) - {pct_low:.1f}% de los pads**")
        
        recomendaciones.append(
            f"• **Ajuste Mecánico:** Aumente levemente la presión de racleta (+0.5 Kg, Actual: {presion_actual} Kg) "
            f"o reduzca la velocidad de impresión (-5 a -10 mm/s, Actual: {velocidad_actual} mm/s) para mejorar el llenado de apertura."
        )
        
        if not c1_tiene_v and not c2_tiene_v:
            recomendaciones.append(
                "• **Ajuste de Limpieza:** Habilite la etapa **Vacío (V)** en el Ciclo 1 para desobstruir aperturas pequeñas obstruidas."
            )
        
        if any(c in str(comp_criticos) for c in ['BGA', 'QFN', '0201', '0402']):
            recomendaciones.append(
                "• **Atención Fine-Pitch:** Defectos detectados en componentes de paso fino. "
                "Verifique la relación de área (Area Ratio > 0.66) y el desmolde (Separation Speed)."
            )

    elif (num_bridge > 0 or num_high > 0) and num_low == 0:
        recomendaciones.append("🔍 **Diagnóstico SPI: Puentes y Exceso de Pasta (BRIDGE / HIGH_VOL)**")
        
        recomendaciones.append(
            f"• **Ajuste Mecánico:** Reduzca la presión de racleta (-0.5 a -1.0 Kg, Actual: {presion_actual} Kg). "
            "La presión excesiva genera sangrado de pasta por debajo de la plantilla."
        )
        
        if not c2_tiene_w:
            recomendaciones.append(
                "• **Limpieza con Solvente:** Active la sub-etapa **Mojado (W)** en el Ciclo 2 con velocidad moderada (50-60 mm/s) "
                "para remover residuos acumulados en la cara inferior."
            )

    else:
        recomendaciones.append("✅ **Proceso Estable:** La inspección SPI indica que la distribución de volumen está dentro de especificación.")

    # 4. IMPACTO TÉRMICO Y AMBIENTAL EN LA PASTA
    if temp_interna > 25.0 and (num_bridge > 0 or num_high > 0):
        recomendaciones.append(
            "🌡️ **Efecto Térmico:** La alta temperatura reduce la viscosidad de la pasta (fenómeno tixotrópico), "
            "propiciando desbordamientos. Enfríe el área interna antes de realizar cambios mecánicos bruscos."
        )
    elif temp_interna < 20.0 and num_low > 0:
        recomendaciones.append(
            "❄️ **Efecto Térmico:** La baja temperatura incrementa la viscosidad, dificultando que la pasta llene y libere las aberturas."
        )

    return recomendaciones


