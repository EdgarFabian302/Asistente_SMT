import pandas as pd

def evaluar_condiciones_gkg(temp_interna, humedad_relativa):
    """
    Evalúa el microclima interno de la GKG P6 Max y sugiere acciones
    sobre el enfriador auxiliar (pingüino) o alertas ambientales.
    """
    alertas = []
    
    # Evaluación de temperatura interna
    if temp_interna > 25.0:
        alertas.append("⚠️ Temp. interna alta (>25°C): Activar/Verificar enfriador auxiliar (pingüino) para evitar degradación de viscosidad de la pasta.")
    elif temp_interna < 20.0:
        alertas.append("ℹ️ Temp. interna baja (<20°C): La viscosidad puede aumentar, revisar la fluidez en el primer pase del squeegee.")
    
    # Evaluación de humedad
    if humedad_relativa > 60:
        alertas.append("⚠️ Humedad alta (>60% RH): Riesgo de absorción de humedad en pasta (slump/puentes). Mantener el flujo de aire seco del enfriador.")
    elif humedad_relativa < 40:
        alertas.append("ℹ️ Humedad baja (<40% RH): Riesgo de secado rápido de la pasta en el stencil.")
        
    return alertas

def generar_recomendaciones_dss(df_spi, temp_interna, humedad_relativa, presion_actual, velocidad_actual):
    """
    Analiza defectos de SPI y el microclima para recomendar ajustes de impresión en la GKG P6 Max.
    """
    recomendaciones = []
    
    if df_spi is None or df_spi.empty:
        return ["No hay datos de SPI cargados para generar diagnóstico."]
    
    # Conteo de defectos por tipo
    defectos = df_spi[df_spi["Estado"] != "PASS"]
    
    if defectos.empty:
        return ["✅ Proceso dentro de especificación. No se requieren ajustes inmediatos en la GKG P6 Max."]
    
    # Evaluar bajo volumen
    bajo_volumen = defectos[defectos["Estado"].str.contains("LOW_VOL", case=False, na=False)]
    if not bajo_volumen.empty:
        recomendaciones.append(
            f"🔻 **Bajo Volumen detectado ({len(bajo_volumen)} pad/s):** "
            f"Considerar reducir velocidad de impresión (actual: {velocidad_actual} mm/s) "
            f"o reducir levemente la presión del squeegee (actual: {presion_actual} Kg) si hay sangrado por sobre-presión."
        )
        
    # Evaluar puentes / exceso de volumen
    puentes = defectos[defectos["Estado"].str.contains("BRIDGE|HIGH_VOL", case=False, na=False)]
    if not puentes.empty:
        recomendaciones.append(
            f"⚠️ **Puentes / Exceso de Volumen ({len(puentes)} pad/s):** "
            f"Aumentar frecuencia de limpieza de stencil (Underside Wipe). "
            f"Verificar si la presión del squeegee es insuficiente ({presion_actual} Kg) o si la temperatura interna ({temp_interna}°C) redujo de más la viscosidad."
        )
        
    # Evaluar alineación
    desfase = defectos[defectos["Estado"].str.contains("SHIFT|OFFSET", case=False, na=False)]
    if not desfase.empty:
        recomendaciones.append(
            f"🎯 **Desfase X/Y detectado ({len(desfase)} pad/s):** "
            f"Ejecutar calibración de visión / cámara en GKG P6 Max o inspeccionar el clamping/soporte de la PCB."
        )
        
    return recomendaciones