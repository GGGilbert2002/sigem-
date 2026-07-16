"""
controllers/mapas_controller.py
=================================
Generación de mapas territoriales del estado Falcón. Provee DOS modos
complementarios (decisión tomada con Gilberto tras verificar que
QtWebEngineView no puede acceder a la red en su equipo, aunque el
navegador normal sí):

1. VISTA PREVIA (matplotlib): mapa estático con el contorno geográfico
   real de Venezuela/Falcón de fondo (GeoJSON local de estados) y
   círculos de datos superpuestos. Se muestra embebido en la app con
   FigureCanvasQTAgg. Funciona 100% sin internet.

2. MAPA INTERACTIVO (Folium -> navegador del sistema): genera el HTML
   interactivo con teselas reales (OpenStreetMap) y lo abre en
   Chrome/Edge, donde ya se comprobó que se ve perfectamente con zoom,
   popups y territorio completo.

Archivos de datos requeridos en resources/geodata/:
- venezuela_estados.geojson : polígonos reales de los estados (ADM1),
  usado como fondo de la vista previa. Fuente: Apache Superset
  (github.com/apache/superset), licencia Apache 2.0.
Archivos opcionales en resources/leaflet/: JS/CSS locales de Leaflet
para el HTML del navegador (si faltan, el navegador usa el CDN, que
funciona bien fuera de la app).
"""

import json
import os
import webbrowser
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import numpy as np

# NOTA: folium se importa de forma diferida dentro de las funciones que
# generan el HTML interactivo (ver _mapa_base_folium y relacionadas).
# Así, la vista previa (matplotlib) funciona aunque folium no esté
# disponible, y la app arranca más rápido.

import config
from models import geografia

ESTADOS_GEOJSON_PATH = os.path.join(config.GEODATA_DIR, "venezuela_estados.geojson")
LEAFLET_DIR = os.path.join(config.RESOURCES_DIR, "leaflet")

COLOR_PRIMARIO   = "#1B4332"
COLOR_SECUNDARIO = "#40916C"
COLOR_ACENTO     = "#D4AF37"
COLOR_MAR        = "#D6E8F5"
COLOR_TIERRA     = "#F2EFE6"
COLOR_FALCON     = "#E8F3EC"
COLOR_BORDE      = "#B0AFA6"

# Recursos que Folium 0.20.0 referencia por CDN; se sustituyen por
# copias locales (resources/leaflet/) si existen. En el navegador del
# sistema el CDN funciona igual, así que esto es solo un refuerzo.
_RECURSOS_CDN_A_LOCAL = {
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js": "leaflet.js",
    "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css": "leaflet.css",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js": "bootstrap.bundle.min.js",
    "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css": "bootstrap.min.css",
    "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/css/all.min.css": "fontawesome.all.min.css",
    "https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css": "leaflet.awesome.rotate.min.css",
    "https://cdn.jsdelivr.net/gh/python-visualization/folium@main/folium/templates/leaflet_heat.min.js": "leaflet_heat.min.js",
    "https://code.jquery.com/jquery-3.7.1.min.js": "jquery-3.7.1.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js": "leaflet.awesome-markers.js",
    "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css": "leaflet.awesome-markers.css",
    "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap-glyphicons.css": "bootstrap-glyphicons.css",
}


# =====================================================================
# UTILIDADES COMUNES
# =====================================================================

def _figura_vacia(mensaje: str) -> Figure:
    fig = Figure(figsize=(8, 5), dpi=100)
    ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, mensaje, ha="center", va="center",
            fontsize=11, color="#666666", wrap=True)
    ax.axis("off")
    return fig


def _cargar_estados() -> list:
    """Carga las features de los estados de Venezuela (GeoJSON local)."""
    if not os.path.isfile(ESTADOS_GEOJSON_PATH):
        return []
    with open(ESTADOS_GEOJSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("features", [])


def _anillos_de_geometria(geom: dict) -> list:
    """Extrae la lista de anillos exteriores de un Polygon/MultiPolygon."""
    if geom["type"] == "Polygon":
        return [geom["coordinates"][0]]
    if geom["type"] == "MultiPolygon":
        return [pol[0] for pol in geom["coordinates"]]
    return []


# =====================================================================
# 1) VISTA PREVIA (matplotlib, sin internet)
# =====================================================================

def generar_figura_preview(modo: str = "municipios") -> Figure:
    """
    Genera la vista previa estática del mapa para embeber en la app.

    modo: 'municipios' | 'parroquias' | 'calor'
    - municipios: círculo por municipio, tamaño/color según registros.
    - parroquias: círculos más pequeños por parroquia.
    - calor: círculos difusos tipo mancha de calor por municipio.

    El fondo es el contorno geográfico real de los estados de
    Venezuela (Falcón resaltado), tomado del GeoJSON local.
    """
    estados = _cargar_estados()
    if not estados:
        return _figura_vacia(
            "Falta el archivo de contornos geográficos.\n"
            "Descárguelo según el README (venezuela_estados.geojson) y\n"
            f"colóquelo en:\n{ESTADOS_GEOJSON_PATH}"
        )

    fig = Figure(figsize=(10, 7.2), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_facecolor(COLOR_MAR)
    fig.patch.set_facecolor("#FFFFFF")

    # --- Fondo: estados de Venezuela (Falcón resaltado) ---
    for feature in estados:
        # El GeoJSON real puede tener features con NAME_1 = None
        # (cuerpos de agua, dependencias sin nombre); se tratan como "".
        nombre_estado = feature["properties"].get("NAME_1") or ""
        es_falcon = ("falc" in nombre_estado.lower())
        for anillo in _anillos_de_geometria(feature["geometry"]):
            coords = np.array(anillo)
            patch = MplPolygon(coords, closed=True)
            pc = PatchCollection(
                [patch],
                facecolor=COLOR_FALCON if es_falcon else COLOR_TIERRA,
                edgecolor=COLOR_BORDE, linewidth=0.7,
                alpha=1.0 if es_falcon else 0.9,
            )
            ax.add_collection(pc)

    # --- Datos según el modo ---
    resumen_m = geografia.resumen_por_municipio()
    datos_validos = [r for r in resumen_m
                     if r["latitud"] is not None and r["longitud"] is not None]
    valor_max = max((r["total_registros"] for r in datos_validos), default=1) or 1
    cmap = plt.get_cmap("Greens")

    if modo == "parroquias":
        resumen_p = geografia.resumen_por_parroquia()
        parr_validas = [r for r in resumen_p
                        if r["latitud"] is not None and r["longitud"] is not None]
        pmax = max((r["total_registros"] for r in parr_validas), default=1) or 1
        for r in parr_validas:
            total = r["total_registros"]
            if total <= 0:
                continue
            tam = 40 + 260 * (total / pmax)
            ax.scatter(r["longitud"], r["latitud"], s=tam,
                       color=COLOR_SECUNDARIO, alpha=0.75,
                       edgecolors="white", linewidths=0.8, zorder=5)
            ax.annotate(f"{r['parroquia']} ({total})",
                        (r["longitud"], r["latitud"]),
                        xytext=(0, 9), textcoords="offset points",
                        ha="center", fontsize=5.5, color="#1B2B20",
                        bbox=dict(boxstyle="round,pad=0.15",
                                  facecolor="white", alpha=0.65,
                                  edgecolor="none"), zorder=6)
        titulo = "Participación por Parroquia — Estado Falcón"

    elif modo == "calor":
        for r in datos_validos:
            total = r["total_registros"]
            if total <= 0:
                continue
            intensidad = total / valor_max
            # Manchas concéntricas difusas (efecto heatmap)
            for factor, alfa in ((3.0, 0.10), (2.2, 0.16), (1.5, 0.25), (0.9, 0.40)):
                tam = (300 + 2600 * intensidad) * factor
                ax.scatter(r["longitud"], r["latitud"], s=tam,
                           color=plt.get_cmap("YlOrRd")(0.35 + 0.6 * intensidad),
                           alpha=alfa, edgecolors="none", zorder=4)
        titulo = "Mapa de Calor — Concentración de Participación"

    else:  # municipios
        for r in datos_validos:
            total = r["total_registros"]
            if total <= 0:
                continue
            tam = 120 + 1400 * (total / valor_max)
            color = cmap(0.35 + 0.6 * (total / valor_max))
            ax.scatter(r["longitud"], r["latitud"], s=tam, color=color,
                       alpha=0.82, edgecolors="white", linewidths=1.2, zorder=5)
            ax.annotate(f"{r['municipio']}\n({total})",
                        (r["longitud"], r["latitud"]),
                        xytext=(0, 12), textcoords="offset points",
                        ha="center", fontsize=6.5, fontweight="bold",
                        color="#1B2B20",
                        bbox=dict(boxstyle="round,pad=0.2",
                                  facecolor="white", alpha=0.7,
                                  edgecolor="none"), zorder=6)
        titulo = "Participación por Municipio — Estado Falcón"

    # Encuadre: zona de Falcón y alrededores
    ax.set_xlim(-71.4, -68.1)
    ax.set_ylim(10.3, 12.35)
    ax.set_aspect("equal")
    ax.set_title(titulo, fontsize=13, fontweight="bold",
                 color=COLOR_PRIMARIO, pad=12)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color(COLOR_BORDE)

    fig.tight_layout()
    return fig


# =====================================================================
# 2) MAPA INTERACTIVO (Folium -> navegador del sistema)
# =====================================================================

def _mapa_base_folium():
    import folium
    return folium.Map(
        location=[config.CORO_LAT, config.CORO_LON],
        zoom_start=config.ZOOM_INICIAL_MAPA,
        tiles="OpenStreetMap",
        control_scale=True,
    )


def _usar_recursos_locales(ruta_html: str) -> None:
    """Reemplaza URLs de CDN por copias locales si existen (refuerzo)."""
    with open(ruta_html, "r", encoding="utf-8") as f:
        contenido = f.read()
    cambios = False
    for url_cdn, nombre in _RECURSOS_CDN_A_LOCAL.items():
        ruta_local = os.path.join(LEAFLET_DIR, nombre)
        if os.path.isfile(ruta_local) and url_cdn in contenido:
            contenido = contenido.replace(
                url_cdn, "file:///" + ruta_local.replace("\\", "/")
            )
            cambios = True
    if cambios:
        with open(ruta_html, "w", encoding="utf-8") as f:
            f.write(contenido)


def _guardar_html(mapa, nombre_archivo: str) -> str:
    ruta = os.path.join(config.REPORTS_DIR, nombre_archivo)
    mapa.save(ruta)
    _usar_recursos_locales(ruta)
    return ruta


def _radio_proporcional(valor, valor_max, radio_min=8, radio_max=35) -> float:
    if valor_max <= 0:
        return radio_min
    return radio_min + (valor / valor_max) * (radio_max - radio_min)


def generar_html_municipios() -> str:
    import folium
    mapa = _mapa_base_folium()
    resumen = geografia.resumen_por_municipio()
    valores = [r["total_registros"] for r in resumen]
    vmax = max(valores) if valores else 0
    for r in resumen:
        if r["latitud"] is None or r["longitud"] is None:
            continue
        radio = _radio_proporcional(r["total_registros"], vmax)
        color = COLOR_PRIMARIO if r["total_registros"] > 0 else "#999999"
        popup = folium.Popup(
            f"<b>Municipio:</b> {r['municipio']}<br>"
            f"<b>Total:</b> {r['total_registros']}<br>"
            f"<b>Masculino:</b> {r['total_masculino']} &nbsp; "
            f"<b>Femenino:</b> {r['total_femenino']}",
            max_width=250,
        )
        folium.CircleMarker(
            location=[r["latitud"], r["longitud"]], radius=radio,
            color=color, fill=True, fill_color=color, fill_opacity=0.65,
            weight=2, popup=popup,
            tooltip=f"{r['municipio']}: {r['total_registros']}",
        ).add_to(mapa)
    return _guardar_html(mapa, "mapa_municipios.html")


def generar_html_parroquias() -> str:
    import folium
    mapa = _mapa_base_folium()
    resumen = geografia.resumen_por_parroquia()
    valores = [r["total_registros"] for r in resumen]
    vmax = max(valores) if valores else 0
    for r in resumen:
        if r["latitud"] is None or r["longitud"] is None:
            continue
        radio = _radio_proporcional(r["total_registros"], vmax, 6, 26)
        color = COLOR_SECUNDARIO if r["total_registros"] > 0 else "#999999"
        popup = folium.Popup(
            f"<b>Parroquia:</b> {r['parroquia']}<br>"
            f"<b>Municipio:</b> {r['municipio']}<br>"
            f"<b>Total:</b> {r['total_registros']}",
            max_width=250,
        )
        folium.CircleMarker(
            location=[r["latitud"], r["longitud"]], radius=radio,
            color=color, fill=True, fill_color=color, fill_opacity=0.65,
            weight=2, popup=popup,
            tooltip=f"{r['parroquia']}: {r['total_registros']}",
        ).add_to(mapa)
    return _guardar_html(mapa, "mapa_parroquias.html")


def generar_html_calor() -> str:
    from folium.plugins import HeatMap
    mapa = _mapa_base_folium()
    resumen = geografia.resumen_por_municipio()
    puntos = [
        [r["latitud"], r["longitud"], r["total_registros"]]
        for r in resumen
        if r["latitud"] is not None and r["longitud"] is not None
        and r["total_registros"] > 0
    ]
    if puntos:
        HeatMap(puntos, radius=35, blur=25, max_zoom=11).add_to(mapa)
    return _guardar_html(mapa, "mapa_calor_municipio.html")


def abrir_mapa_en_navegador(modo: str = "municipios") -> str:
    """
    Genera el HTML interactivo del modo indicado y lo abre en el
    navegador predeterminado del sistema. Retorna la ruta generada.
    """
    if modo == "parroquias":
        ruta = generar_html_parroquias()
    elif modo == "calor":
        ruta = generar_html_calor()
    else:
        ruta = generar_html_municipios()
    webbrowser.open("file:///" + ruta.replace("\\", "/"))
    return ruta
