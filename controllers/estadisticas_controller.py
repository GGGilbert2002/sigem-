"""
controllers/estadisticas_controller.py
========================================
Lógica de análisis estadístico sobre los datos de personal militar.

Implementa exactamente las dimensiones definidas en el Cuadro de
Operacionalización de Variables (Capítulo II):
  - Datos demográficos: edad, género, nivel educativo
  - Datos territoriales: municipio, parroquia
  - Participación / reclutamiento: estatus

Usa pandas para los cálculos agregados (tal como se definió en el
stack tecnológico), devolviendo estructuras simples (dict / DataFrame)
que luego las vistas de PyQt6 convierten en gráficos con matplotlib.
"""

from typing import Optional

import pandas as pd

from database.connection import get_connection


def _cargar_dataframe_personal() -> pd.DataFrame:
    """
    Carga todo el personal militar en un DataFrame de pandas, con los
    catálogos ya resueltos (nombres, no solo IDs) y la edad calculada.
    Esta es la única consulta SQL de todo el módulo: todos los análisis
    estadísticos posteriores se hacen en memoria con pandas sobre este
    DataFrame, lo cual es eficiente para el volumen de datos esperado
    (registros de un batallón, no millones de filas).
    """
    conn = get_connection()
    try:
        query = """
            SELECT
                p.id_personal, p.cedula, p.nombres, p.apellidos,
                p.fecha_nacimiento, p.genero, p.fecha_registro,
                n.descripcion AS nivel_educativo,
                g.nombre AS grado,
                m.nombre AS municipio,
                pq.nombre AS parroquia,
                e.descripcion AS estatus
            FROM personal_militar p
            LEFT JOIN niveles_educativos n ON p.id_nivel_educativo = n.id_nivel_educativo
            LEFT JOIN grados_militares g ON p.id_grado = g.id_grado
            JOIN municipios m ON p.id_municipio = m.id_municipio
            LEFT JOIN parroquias pq ON p.id_parroquia = pq.id_parroquia
            JOIN estatus_participacion e ON p.id_estatus = e.id_estatus
        """
        df = pd.read_sql_query(query, conn)
    finally:
        conn.close()

    if df.empty:
        return df

    # Edad calculada a partir de fecha_nacimiento (vectorizado con pandas,
    # más eficiente que calcular fila por fila en Python puro).
    df["fecha_nacimiento"] = pd.to_datetime(df["fecha_nacimiento"])
    hoy = pd.Timestamp.now().normalize()
    df["edad"] = ((hoy - df["fecha_nacimiento"]).dt.days // 365).astype(int)

    # Rangos de edad (categorías), útiles para gráficos de barras agrupados
    bins = [17, 20, 25, 30, 35, 100]
    etiquetas = ["18-20", "21-25", "26-30", "31-35", "36+"]
    df["rango_edad"] = pd.cut(df["edad"], bins=bins, labels=etiquetas)

    df["fecha_registro"] = pd.to_datetime(df["fecha_registro"])
    return df


def resumen_general() -> dict:
    """
    Indicadores generales (KPIs) para la pantalla de Dashboard:
    total de registros, distribución por género, edad promedio, etc.
    """
    df = _cargar_dataframe_personal()
    if df.empty:
        return {
            "total_registros": 0, "total_masculino": 0, "total_femenino": 0,
            "edad_promedio": 0, "edad_minima": 0, "edad_maxima": 0,
            "total_municipios_con_registros": 0,
        }

    return {
        "total_registros": int(len(df)),
        "total_masculino": int((df["genero"] == "Masculino").sum()),
        "total_femenino": int((df["genero"] == "Femenino").sum()),
        "edad_promedio": round(float(df["edad"].mean()), 1),
        "edad_minima": int(df["edad"].min()),
        "edad_maxima": int(df["edad"].max()),
        "total_municipios_con_registros": int(df["municipio"].nunique()),
    }


def distribucion_por_genero() -> dict:
    """Retorna {'Masculino': n, 'Femenino': n} para gráfico de torta."""
    df = _cargar_dataframe_personal()
    if df.empty:
        return {}
    return df["genero"].value_counts().to_dict()


def distribucion_por_rango_edad() -> dict:
    """Retorna conteo por rango de edad, ordenado (18-20, 21-25, ...) para gráfico de barras."""
    df = _cargar_dataframe_personal()
    if df.empty:
        return {}
    conteo = df["rango_edad"].value_counts().sort_index()
    return {str(k): int(v) for k, v in conteo.items()}


def distribucion_por_nivel_educativo() -> dict:
    """Retorna conteo por nivel educativo, para gráfico de barras horizontales."""
    df = _cargar_dataframe_personal()
    if df.empty:
        return {}
    conteo = df["nivel_educativo"].fillna("No especificado").value_counts()
    return conteo.to_dict()


def distribucion_por_municipio() -> dict:
    """Retorna conteo de registros por municipio, ordenado descendente."""
    df = _cargar_dataframe_personal()
    if df.empty:
        return {}
    return df["municipio"].value_counts().to_dict()


def distribucion_por_parroquia(municipio: Optional[str] = None) -> dict:
    """Retorna conteo de registros por parroquia. Si se especifica municipio, filtra solo esa zona."""
    df = _cargar_dataframe_personal()
    if df.empty:
        return {}
    if municipio:
        df = df[df["municipio"] == municipio]
    return df["parroquia"].fillna("Sin parroquia registrada").value_counts().to_dict()


def distribucion_por_estatus() -> dict:
    """Retorna conteo por estatus de participación (Registrado, Incorporado, etc.)."""
    df = _cargar_dataframe_personal()
    if df.empty:
        return {}
    return df["estatus"].value_counts().to_dict()


def tendencia_registros_por_mes() -> dict:
    """
    Retorna el conteo de registros agrupados por mes (AAAA-MM), para
    graficar la tendencia temporal de participación/reclutamiento.
    """
    df = _cargar_dataframe_personal()
    if df.empty:
        return {}
    df["mes"] = df["fecha_registro"].dt.to_period("M").astype(str)
    conteo = df.groupby("mes").size().sort_index()
    return conteo.to_dict()


def tabla_cruzada_genero_municipio() -> pd.DataFrame:
    """
    Tabla cruzada (pivot table) de género x municipio. Útil para
    análisis comparativos territoriales y para exportar a reportes.
    """
    df = _cargar_dataframe_personal()
    if df.empty:
        return pd.DataFrame()
    return pd.crosstab(df["municipio"], df["genero"], margins=True, margins_name="Total")


def tabla_cruzada_estatus_municipio() -> pd.DataFrame:
    """Tabla cruzada de estatus de participación x municipio."""
    df = _cargar_dataframe_personal()
    if df.empty:
        return pd.DataFrame()
    return pd.crosstab(df["municipio"], df["estatus"], margins=True, margins_name="Total")


def municipio_mayor_participacion() -> Optional[dict]:
    """Identifica el municipio con mayor número de registros (responde a la
    pregunta de investigación sobre zonas de mayor participación)."""
    distribucion = distribucion_por_municipio()
    if not distribucion:
        return None
    municipio = max(distribucion, key=distribucion.get)
    return {"municipio": municipio, "total": distribucion[municipio]}


def municipio_menor_participacion() -> Optional[dict]:
    """Identifica el municipio con menor número de registros (entre los que
    tienen al menos un registro)."""
    distribucion = distribucion_por_municipio()
    if not distribucion:
        return None
    municipio = min(distribucion, key=distribucion.get)
    return {"municipio": municipio, "total": distribucion[municipio]}
