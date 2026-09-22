import pandas as pd

def cargar_reporte_spi(archivo):
    """
    Lee el archivo CSV de la SPI y regresa un DataFrame de Pandas.
    """
    try:
        df = pd.read_csv(archivo)
        return df
    except Exception as e:
        print(f"Error al cargar el archivo SPI: {e}")
        return None

def obtener_defectos(df):
    """
    Filtra los registros que no tengan estado PASS.
    """
    if df is not None and not df.empty:
        return df[df["Estado"] != "PASS"]
    return pd.DataFrame()