"""
views/estadisticas_view.py
============================
Pantalla de Estadísticas: muestra los gráficos de distribución por
edad, nivel educativo, estatus de participación y tendencia temporal,
según el wireframe aprobado (paneles de 2 columnas + panel ancho).
"""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from controllers import graficos_controller as gc


class PanelGraficoEstadistica(QFrame):
    """Panel blanco con título + gráfico embebido, reutilizado en toda la vista."""

    def __init__(self, titulo: str):
        super().__init__()
        self.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #DDDDDD; border-radius: 8px; }"
        )
        self.layout_interno = QVBoxLayout(self)
        self.layout_interno.setContentsMargins(16, 14, 16, 14)

        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet(
            "color: #1B4332; font-size: 13px; font-weight: 700; border: none;"
        )
        self.layout_interno.addWidget(label_titulo)
        self._canvas_actual = None

    def establecer_figura(self, figura) -> None:
        if self._canvas_actual is not None:
            self.layout_interno.removeWidget(self._canvas_actual)
            self._canvas_actual.deleteLater()
        self._canvas_actual = FigureCanvasQTAgg(figura)
        self.layout_interno.addWidget(self._canvas_actual)


class EstadisticasView(QWidget):
    """Vista de análisis estadístico demográfico y territorial."""

    def __init__(self):
        super().__init__()
        self._construir_interfaz()
        self.refrescar()

    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        fila_encabezado = QHBoxLayout()
        titulo = QLabel("Estadísticas")
        titulo.setObjectName("tituloVista")
        subtitulo = QLabel("Análisis demográfico y territorial")
        subtitulo.setObjectName("subtituloVista")
        fila_encabezado.addWidget(titulo)
        fila_encabezado.addStretch()
        fila_encabezado.addWidget(subtitulo)
        layout.addLayout(fila_encabezado)

        # --- Fila superior: edad + nivel educativo ---
        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(14)
        self.panel_edad = PanelGraficoEstadistica("Rango de Edad")
        self.panel_nivel_educativo = PanelGraficoEstadistica("Nivel Educativo")
        fila_superior.addWidget(self.panel_edad)
        fila_superior.addWidget(self.panel_nivel_educativo)
        layout.addLayout(fila_superior)

        # --- Fila media: estatus de participación + parroquias top ---
        fila_media = QHBoxLayout()
        fila_media.setSpacing(14)
        self.panel_estatus = PanelGraficoEstadistica("Estatus de Participación")
        self.panel_parroquia = PanelGraficoEstadistica("Participación por Parroquia (Miranda)")
        fila_media.addWidget(self.panel_estatus)
        fila_media.addWidget(self.panel_parroquia)
        layout.addLayout(fila_media)

        # --- Panel ancho: tendencia temporal ---
        self.panel_tendencia = PanelGraficoEstadistica("Tendencia de Registros por Mes")
        layout.addWidget(self.panel_tendencia)

    def refrescar(self) -> None:
        """Recarga todos los gráficos con los datos más recientes de la base de datos."""
        self.panel_edad.establecer_figura(gc.grafico_distribucion_edad())
        self.panel_nivel_educativo.establecer_figura(gc.grafico_nivel_educativo())
        self.panel_estatus.establecer_figura(gc.grafico_distribucion_estatus())
        self.panel_parroquia.establecer_figura(gc.grafico_distribucion_parroquia(municipio="Miranda"))
        self.panel_tendencia.establecer_figura(gc.grafico_tendencia_temporal())
