"""
controllers/graficos_controller.py
====================================
Generación de gráficos estadísticos (barras, tortas, líneas) usando
matplotlib, a partir de los datos calculados en estadisticas_controller.

Cada función retorna un objeto matplotlib.figure.Figure, NO lo muestra
ni lo guarda directamente. Esto es intencional: una Figure se puede
- embeber en PyQt6 mediante FigureCanvasQTAgg (ver views/widgets_graficos.py)
- guardar como imagen para los reportes PDF (ver utils/exporters.py)
- mostrarse en modo standalone para pruebas

Paleta de colores alineada con la identidad visual definida en config.py.
"""

import matplotlib
matplotlib.use("Agg")  # Backend sin pantalla; en la app PyQt6 se usa QtAgg (ver views)

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import config
from controllers import estadisticas_controller as ec

# Paleta de colores consistente en todos los gráficos del sistema
PALETA = ["#1B4332", "#40916C", "#74C69D", "#D4AF37", "#B08968",
          "#52796F", "#84A98C", "#CAD2C5", "#2D6A4F", "#95D5B2"]

plt.rcParams["font.size"] = 9
plt.rcParams["axes.titleweight"] = "bold"


def _figura_vacia(mensaje: str) -> Figure:
    """Genera una figura con un mensaje informativo cuando no hay datos
    suficientes para graficar (evita que la interfaz se rompa o muestre
    un gráfico en blanco sin explicación)."""
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, mensaje, ha="center", va="center", fontsize=11,
             color="#666666", wrap=True)
    ax.axis("off")
    return fig


def grafico_distribucion_genero() -> Figure:
    """Gráfico de torta: distribución por género."""
    datos = ec.distribucion_por_genero()
    if not datos:
        return _figura_vacia("No hay registros de personal para graficar.")

    fig = Figure(figsize=(5, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.pie(
        datos.values(), labels=datos.keys(), autopct="%1.1f%%",
        colors=PALETA[:len(datos)], startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    ax.set_title("Distribución por Género")
    ax.set_aspect("equal")  # asegura que el círculo no se vea ovalado
    fig.tight_layout()
    return fig


def grafico_distribucion_edad() -> Figure:
    """Gráfico de barras: distribución por rango de edad."""
    datos = ec.distribucion_por_rango_edad()
    if not datos:
        return _figura_vacia("No hay registros de personal para graficar.")

    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
    barras = ax.bar(list(datos.keys()), list(datos.values()), color=PALETA[1])
    ax.bar_label(barras, padding=3)
    ax.set_title("Distribución por Rango de Edad")
    ax.set_xlabel("Rango de edad")
    ax.set_ylabel("Cantidad de personal")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def grafico_nivel_educativo() -> Figure:
    """Gráfico de barras horizontales: distribución por nivel educativo."""
    datos = ec.distribucion_por_nivel_educativo()
    if not datos:
        return _figura_vacia("No hay registros de personal para graficar.")

    # Ordenar de mayor a menor para mejor lectura visual
    datos_ordenados = dict(sorted(datos.items(), key=lambda x: x[1]))

    fig = Figure(figsize=(6.5, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    barras = ax.barh(list(datos_ordenados.keys()), list(datos_ordenados.values()), color=PALETA[2])
    ax.bar_label(barras, padding=3)
    ax.set_title("Distribución por Nivel Educativo")
    ax.set_xlabel("Cantidad de personal")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def grafico_distribucion_municipio(top_n: int = 10) -> Figure:
    """Gráfico de barras: municipios con mayor cantidad de registros (top_n)."""
    datos = ec.distribucion_por_municipio()
    if not datos:
        return _figura_vacia("No hay registros de personal para graficar.")

    top = dict(list(datos.items())[:top_n])

    fig = Figure(figsize=(7, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    barras = ax.bar(list(top.keys()), list(top.values()), color=PALETA[0])
    ax.bar_label(barras, padding=3)
    ax.set_title(f"Participación por Municipio (Top {top_n})")
    ax.set_ylabel("Cantidad de personal")
    ax.tick_params(axis="x", rotation=35)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def grafico_distribucion_parroquia(municipio: str) -> Figure:
    """Gráfico de barras: distribución de registros por parroquia de un municipio específico."""
    datos = ec.distribucion_por_parroquia(municipio=municipio)
    if not datos:
        return _figura_vacia(f"No hay registros para el municipio '{municipio}'.")

    fig = Figure(figsize=(6.5, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    barras = ax.bar(list(datos.keys()), list(datos.values()), color=PALETA[4])
    ax.bar_label(barras, padding=3)
    ax.set_title(f"Participación por Parroquia — Municipio {municipio}")
    ax.set_ylabel("Cantidad de personal")
    ax.tick_params(axis="x", rotation=30)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def grafico_distribucion_estatus() -> Figure:
    """Gráfico de torta: distribución por estatus de participación/reclutamiento."""
    datos = ec.distribucion_por_estatus()
    if not datos:
        return _figura_vacia("No hay registros de personal para graficar.")

    fig = Figure(figsize=(6, 6), dpi=100)
    ax = fig.add_subplot(111)
    ax.pie(
        datos.values(), labels=datos.keys(), autopct="%1.1f%%",
        colors=PALETA[:len(datos)], startangle=90,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    ax.set_title("Distribución por Estatus de Participación")
    ax.set_aspect("equal")
    fig.tight_layout()
    return fig


def grafico_tendencia_temporal() -> Figure:
    """Gráfico de líneas: tendencia de registros de participación a lo largo del tiempo."""
    datos = ec.tendencia_registros_por_mes()
    if not datos:
        return _figura_vacia("No hay registros de personal para graficar.")

    fig = Figure(figsize=(7, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(list(datos.keys()), list(datos.values()), marker="o",
            color=PALETA[0], linewidth=2, markersize=5)
    ax.fill_between(list(datos.keys()), list(datos.values()), alpha=0.15, color=PALETA[0])
    ax.set_title("Tendencia de Registros de Participación por Mes")
    ax.set_ylabel("Cantidad de registros")
    ax.tick_params(axis="x", rotation=45)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def guardar_figura_temporal(fig: Figure, nombre_archivo: str) -> str:
    """
    Guarda una figura como imagen PNG en la carpeta de reportes, para
    ser incrustada posteriormente en un PDF (ver utils/exporters.py).
    Retorna la ruta completa del archivo generado.
    """
    import os
    ruta = os.path.join(config.REPORTS_DIR, nombre_archivo)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    return ruta
