"""
controllers/graficos_controller.py
====================================
Generación de gráficos con matplotlib, compatible con la estructura
real de datos que retornan las funciones de estadisticas_controller:
- distribucion_por_*() → dict {etiqueta: total}
- tendencia_registros_por_mes() → dict {"YYYY-MM": total}
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from controllers.estadisticas_controller import (
    distribucion_por_rango_edad,
    distribucion_por_nivel_educativo,
    distribucion_por_estatus,
    distribucion_por_municipio,
    distribucion_por_genero,
    distribucion_por_parroquia,
    tendencia_registros_por_mes,
)

# Paleta institucional
VERDE_OSCURO = "#1B4332"
VERDE_MEDIO  = "#40916C"
VERDE_CLARO  = "#74C69D"
ORO          = "#D4AF37"
CAFE         = "#B08968"
GRIS_TEXTO   = "#333333"
FONDO        = "#FAFAFA"

PALETA = [VERDE_OSCURO, VERDE_MEDIO, VERDE_CLARO, ORO, CAFE,
          "#52796F", "#84A98C", "#95D5B2", "#2D6A4F", "#081C15"]


def _figura_base(ancho=7.5, alto=4.2):
    fig = Figure(figsize=(ancho, alto), dpi=100, facecolor=FONDO)
    ax = fig.add_subplot(111)
    ax.set_facecolor(FONDO)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#DDDDDD")
    ax.spines["bottom"].set_color("#DDDDDD")
    ax.tick_params(colors=GRIS_TEXTO, labelsize=8.5)
    return fig, ax


def _layout(fig, izq=0.10):
    fig.tight_layout(pad=2.5, rect=[izq, 0.04, 0.98, 0.96])


def _sin_datos(mensaje="Sin datos disponibles"):
    fig, ax = _figura_base()
    ax.text(0.5, 0.5, mensaje, ha="center", va="center",
            fontsize=10, color="#999999")
    ax.axis("off")
    return fig


# ─────────────────────────────────────────────────────────────────────
def grafico_distribucion_municipio() -> Figure:
    """Barras verticales — participación por municipio (top 10)."""
    datos = distribucion_por_municipio()   # → {"Miranda": 37, "Colina": 31, ...}
    if not datos:
        return _sin_datos()

    items = sorted(datos.items(), key=lambda x: x[1], reverse=True)[:10]
    etiquetas = [k for k, _ in items]
    valores   = [v for _, v in items]

    fig, ax = _figura_base(ancho=8.0, alto=4.8)
    colores = [VERDE_OSCURO if i == 0 else VERDE_MEDIO for i in range(len(etiquetas))]
    rects = ax.bar(etiquetas, valores, color=colores, width=0.6, zorder=2)

    for rect in rects:
        h = rect.get_height()
        if h > 0:
            ax.text(rect.get_x() + rect.get_width() / 2, h / 2,
                    str(int(h)), ha="center", va="center",
                    color="white", fontsize=9, fontweight="bold")

    ax.set_ylabel("Cantidad de personal", fontsize=9, color=GRIS_TEXTO)
    ax.set_ylim(0, max(valores) * 1.18)
    ax.yaxis.grid(True, color="#EEEEEE", zorder=0)
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8.5)
    _layout(fig, izq=0.08)
    return fig


def grafico_distribucion_genero() -> Figure:
    """Torta — distribución por género."""
    datos = distribucion_por_genero()   # → {"Masculino": 126, "Femenino": 124}
    if not datos:
        return _sin_datos()

    etiquetas = list(datos.keys())
    valores   = list(datos.values())
    colores   = [VERDE_OSCURO, VERDE_MEDIO]

    fig, ax = _figura_base(ancho=5.0, alto=4.2)
    wedges, texts, autotexts = ax.pie(
        valores, labels=etiquetas, colors=colores,
        autopct="%1.1f%%", startangle=90,
        wedgeprops=dict(linewidth=1.5, edgecolor="white"),
        textprops=dict(fontsize=9),
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.axis("equal")
    _layout(fig, izq=0.02)
    return fig


def grafico_distribucion_edad() -> Figure:
    """Barras verticales — distribución por rango de edad."""
    datos = distribucion_por_rango_edad()  # → {"18-20": 50, "21-25": 57, ...}
    if not datos:
        return _sin_datos()

    etiquetas = list(datos.keys())
    valores   = list(datos.values())

    fig, ax = _figura_base(ancho=7.5, alto=4.4)
    rects = ax.bar(etiquetas, valores, color=VERDE_MEDIO, width=0.6, zorder=2)

    for rect in rects:
        h = rect.get_height()
        if h > 0:
            ax.text(rect.get_x() + rect.get_width() / 2, h + max(valores) * 0.01,
                    str(int(h)), ha="center", va="bottom",
                    color=GRIS_TEXTO, fontsize=9, fontweight="bold")

    ax.set_xlabel("Rango de edad", fontsize=9, color=GRIS_TEXTO)
    ax.set_ylabel("Cantidad de personal", fontsize=9, color=GRIS_TEXTO)
    ax.set_ylim(0, max(valores) * 1.20)
    ax.yaxis.grid(True, color="#EEEEEE", zorder=0)
    ax.set_axisbelow(True)
    _layout(fig, izq=0.10)
    return fig


def grafico_nivel_educativo() -> Figure:
    """Barras horizontales — nivel educativo (nombres largos)."""
    datos = distribucion_por_nivel_educativo()  # → {"Técnico Medio": 40, ...}
    if not datos:
        return _sin_datos()

    items = sorted(datos.items(), key=lambda x: x[1])
    etiquetas = [k for k, _ in items]
    valores   = [v for _, v in items]

    fig, ax = _figura_base(ancho=7.5, alto=4.6)
    bars = ax.barh(etiquetas, valores, color=VERDE_MEDIO, height=0.6, zorder=2)

    for bar, valor in zip(bars, valores):
        ax.text(bar.get_width() + max(valores) * 0.01,
                bar.get_y() + bar.get_height() / 2,
                str(int(valor)), va="center", ha="left",
                fontsize=9, color=GRIS_TEXTO, fontweight="bold")

    ax.set_xlabel("Cantidad de personal", fontsize=9, color=GRIS_TEXTO)
    ax.set_xlim(0, max(valores) * 1.22)
    ax.xaxis.grid(True, color="#EEEEEE", zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", labelsize=8.5)
    # Margen izquierdo amplio para nombres largos como "Técnico Medio"
    _layout(fig, izq=0.34)
    return fig


def grafico_distribucion_estatus() -> Figure:
    """Torta — estatus de participación."""
    datos = distribucion_por_estatus()  # → {"Incorporado": 32, "Diferido": 41, ...}
    if not datos:
        return _sin_datos()

    etiquetas = list(datos.keys())
    valores   = list(datos.values())
    colores   = (PALETA * 3)[:len(etiquetas)]

    fig, ax = _figura_base(ancho=5.5, alto=4.6)
    wedges, texts, autotexts = ax.pie(
        valores, labels=etiquetas, colors=colores,
        autopct="%1.1f%%", startangle=140,
        wedgeprops=dict(linewidth=1.2, edgecolor="white"),
        textprops=dict(fontsize=7.5),
        pctdistance=0.78,
    )
    for at in autotexts:
        at.set_fontsize(7.5)
        at.set_fontweight("bold")
        at.set_color("white")
    ax.axis("equal")
    _layout(fig, izq=0.02)
    return fig


def grafico_distribucion_parroquia(municipio: str = "Miranda") -> Figure:
    """Barras verticales — participación por parroquia."""
    datos = distribucion_por_parroquia(municipio=municipio)
    # puede retornar dict {"Parroquia X": 11, ...}
    if not datos:
        return _sin_datos(f"Sin datos para el municipio {municipio}")

    items = sorted(datos.items(), key=lambda x: x[1], reverse=True)[:10]
    etiquetas = [k for k, _ in items]
    valores   = [v for _, v in items]

    fig, ax = _figura_base(ancho=7.5, alto=4.6)
    colores = [VERDE_OSCURO if i == 0 else CAFE for i in range(len(etiquetas))]
    rects = ax.bar(etiquetas, valores, color=colores, width=0.6, zorder=2)

    for rect in rects:
        h = rect.get_height()
        if h > 0:
            ax.text(rect.get_x() + rect.get_width() / 2,
                    h + max(valores) * 0.01,
                    str(int(h)), ha="center", va="bottom",
                    color=GRIS_TEXTO, fontsize=9, fontweight="bold")

    ax.set_ylabel("Cantidad de personal", fontsize=9, color=GRIS_TEXTO)
    ax.set_ylim(0, max(valores) * 1.20)
    ax.yaxis.grid(True, color="#EEEEEE", zorder=0)
    ax.set_axisbelow(True)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", fontsize=7.5)
    _layout(fig, izq=0.10)
    return fig


def grafico_tendencia_temporal() -> Figure:
    """Línea de tendencia de registros por mes."""
    datos = tendencia_registros_por_mes()  # → {"2025-01": 8, "2025-02": 10, ...}
    if not datos:
        return _sin_datos()

    periodos = list(datos.keys())
    valores  = list(datos.values())
    x = list(range(len(periodos)))

    fig, ax = _figura_base(ancho=8.5, alto=3.8)
    ax.fill_between(x, valores, alpha=0.12, color=VERDE_MEDIO)
    ax.plot(x, valores, color=VERDE_OSCURO, linewidth=2.2,
            marker="o", markersize=5,
            markerfacecolor=VERDE_MEDIO,
            markeredgecolor="white", markeredgewidth=1.2, zorder=3)

    for xi, yi in zip(x, valores):
        ax.annotate(str(yi), (xi, yi),
                    textcoords="offset points", xytext=(0, 7),
                    ha="center", fontsize=7.5,
                    color=GRIS_TEXTO, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(periodos, rotation=45, ha="right", fontsize=7.5)
    ax.set_ylabel("Registros", fontsize=9, color=GRIS_TEXTO)
    ax.set_ylim(0, max(valores) * 1.28)
    ax.yaxis.grid(True, color="#EEEEEE", zorder=0)
    ax.set_axisbelow(True)
    _layout(fig, izq=0.08)
    return fig
