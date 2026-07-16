"""
views/mapa_view.py
====================
Pantalla de Mapas Territoriales con doble modalidad (acordado con el
usuario tras diagnóstico de red de QtWebEngine en su equipo):

1. VISTA PREVIA embebida (matplotlib + FigureCanvasQTAgg): mapa
   estático con el contorno real de Venezuela/Falcón y los datos
   superpuestos. Funciona sin internet, dentro de la app.
2. Botón "Abrir mapa interactivo": genera el HTML de Folium y lo abre
   en el navegador del sistema (Chrome/Edge), donde se ve el mapa
   completo con teselas, zoom y popups.
"""

import logging

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from controllers import mapas_controller as mc

logger = logging.getLogger("sigem.mapas")


class MapaView(QWidget):
    """Vista de mapas: previa embebida + apertura interactiva en navegador."""

    def __init__(self):
        super().__init__()
        self._modo_actual = "municipios"
        self._canvas_actual = None
        self._construir_interfaz()
        self.refrescar()

    def _construir_interfaz(self) -> None:
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 22, 28, 16)
        self._layout.setSpacing(14)

        # --- Encabezado ---
        fila_enc = QHBoxLayout()
        titulo = QLabel("Mapas Territoriales")
        titulo.setObjectName("tituloVista")
        subtitulo = QLabel("Georreferenciación — Edo. Falcón")
        subtitulo.setObjectName("subtituloVista")
        fila_enc.addWidget(titulo)
        fila_enc.addStretch()
        fila_enc.addWidget(subtitulo)
        self._layout.addLayout(fila_enc)

        # --- Botones de modo + botón de mapa interactivo ---
        fila_btn = QHBoxLayout()
        self._btn_municipios = QPushButton("Municipios")
        self._btn_parroquias = QPushButton("Parroquias")
        self._btn_calor = QPushButton("Mapa de Calor")

        for boton, modo in (
            (self._btn_municipios, "municipios"),
            (self._btn_parroquias, "parroquias"),
            (self._btn_calor, "calor"),
        ):
            boton.setObjectName("btnSecundario")
            boton.setCheckable(True)
            boton.setAutoExclusive(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(lambda _=False, m=modo: self._cambiar_modo(m))
            fila_btn.addWidget(boton)

        fila_btn.addStretch()

        self._btn_interactivo = QPushButton("🌐  Abrir mapa interactivo")
        self._btn_interactivo.setObjectName("btnPrimario")
        self._btn_interactivo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_interactivo.setToolTip(
            "Abre el mapa interactivo (con zoom, calles y detalles al hacer clic)\n"
            "en su navegador web. Requiere conexión a internet."
        )
        self._btn_interactivo.clicked.connect(self._abrir_interactivo)
        fila_btn.addWidget(self._btn_interactivo)

        self._layout.addLayout(fila_btn)
        self._btn_municipios.setChecked(True)

        # --- Nota informativa ---
        nota = QLabel(
            "Vista previa del territorio. Para explorar con zoom, calles y "
            "detalles por zona, use el botón \"Abrir mapa interactivo\"."
        )
        nota.setStyleSheet("color: #888888; font-size: 11px;")
        nota.setWordWrap(True)
        self._layout.addWidget(nota)

        # --- Contenedor del canvas de vista previa ---
        self._contenedor_mapa = QWidget()
        self._layout_mapa = QVBoxLayout(self._contenedor_mapa)
        self._layout_mapa.setContentsMargins(0, 0, 0, 0)
        self._layout.addWidget(self._contenedor_mapa, stretch=1)

    # -------------------------------------------------------------
    def _cambiar_modo(self, modo: str) -> None:
        self._modo_actual = modo
        self._cargar_preview()

    def refrescar(self) -> None:
        self._cargar_preview()

    def _cargar_preview(self) -> None:
        """Genera la figura de vista previa y la muestra embebida."""
        try:
            figura = mc.generar_figura_preview(modo=self._modo_actual)
        except Exception as e:
            logger.exception("Error generando vista previa (modo=%s)", self._modo_actual)
            figura = mc._figura_vacia(f"Error al generar la vista previa:\n{e}")

        if self._canvas_actual is not None:
            self._layout_mapa.removeWidget(self._canvas_actual)
            self._canvas_actual.deleteLater()

        self._canvas_actual = FigureCanvasQTAgg(figura)
        self._layout_mapa.addWidget(self._canvas_actual)
        logger.info("Vista previa de mapa cargada (modo=%s)", self._modo_actual)

    def _abrir_interactivo(self) -> None:
        """Genera el HTML interactivo del modo actual y lo abre en el navegador."""
        try:
            ruta = mc.abrir_mapa_en_navegador(modo=self._modo_actual)
            logger.info("Mapa interactivo abierto en navegador: %s", ruta)
        except Exception as e:
            logger.exception("Error al abrir el mapa interactivo")
            QMessageBox.critical(
                self, "Error",
                f"No se pudo abrir el mapa interactivo:\n{e}",
            )
