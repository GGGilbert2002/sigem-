"""
views/estadisticas_view.py
============================
Vista de estadísticas con indicador de carga y fade-in al mostrar.
"""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea,
    QVBoxLayout, QWidget,
)

from controllers import graficos_controller as gc
from views.animaciones import aplicar_fade_in
from views.widgets_carga import IndicadorCarga


class _WorkerEstadisticas(QThread):
    figura_lista = pyqtSignal(str, object)   # (nombre_panel, figura)
    terminado    = pyqtSignal()
    error        = pyqtSignal(str)

    def run(self) -> None:
        try:
            tareas = [
                ("edad",             gc.grafico_distribucion_edad),
                ("nivel_educativo",  gc.grafico_nivel_educativo),
                ("estatus",          gc.grafico_distribucion_estatus),
                ("parroquia",        lambda: gc.grafico_distribucion_parroquia("Miranda")),
                ("tendencia",        gc.grafico_tendencia_temporal),
            ]
            for nombre, fn in tareas:
                self.figura_lista.emit(nombre, fn())
            self.terminado.emit()
        except Exception as e:
            self.error.emit(str(e))


class PanelEstad(QFrame):
    def __init__(self, titulo: str):
        super().__init__()
        self.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #DDDDDD; "
            "border-radius: 8px; }"
        )
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)
        lbl = QLabel(titulo)
        lbl.setStyleSheet(
            "color: #1B4332; font-size: 13px; font-weight: 700; border: none;"
        )
        self._layout.addWidget(lbl)
        self._canvas = None

    def establecer_figura(self, figura) -> None:
        if self._canvas:
            self._layout.removeWidget(self._canvas)
            self._canvas.deleteLater()
        self._canvas = FigureCanvasQTAgg(figura)
        self._layout.addWidget(self._canvas)


class EstadisticasView(QWidget):

    def __init__(self):
        super().__init__()
        self._worker = None
        self._paneles: dict[str, PanelEstad] = {}
        self._construir_interfaz()
        self.refrescar()

    def _construir_interfaz(self) -> None:
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(28, 22, 28, 22)
        layout_raiz.setSpacing(14)

        fila_enc = QHBoxLayout()
        titulo = QLabel("Estadísticas")
        titulo.setObjectName("tituloVista")
        subtitulo = QLabel("Análisis demográfico y territorial")
        subtitulo.setObjectName("subtituloVista")
        fila_enc.addWidget(titulo)
        fila_enc.addStretch()
        fila_enc.addWidget(subtitulo)
        layout_raiz.addLayout(fila_enc)

        # Área de scroll para los gráficos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        contenedor = QWidget()
        contenedor.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(contenedor)
        layout.setSpacing(14)

        def _fila(*claves_titulos):
            fila = QHBoxLayout()
            fila.setSpacing(14)
            for clave, titulo_panel in claves_titulos:
                panel = PanelEstad(titulo_panel)
                self._paneles[clave] = panel
                fila.addWidget(panel)
            layout.addLayout(fila)

        _fila(("edad", "Rango de Edad"),
              ("nivel_educativo", "Nivel Educativo"))
        _fila(("estatus", "Estatus de Participación"),
              ("parroquia", "Participación por Parroquia (Miranda)"))
        _fila(("tendencia", "Tendencia de Registros por Mes"),)

        scroll.setWidget(contenedor)
        layout_raiz.addWidget(scroll)

        self._indicador = IndicadorCarga(self)

    def refrescar(self) -> None:
        if self._worker and self._worker.isRunning():
            return
        self._indicador.mostrar("Calculando estadísticas...", "Procesando datos de participación")
        self._worker = _WorkerEstadisticas()
        self._worker.figura_lista.connect(self._recibir_figura)
        self._worker.terminado.connect(self._al_terminar)
        self._worker.error.connect(lambda _: self._indicador.ocultar())
        self._worker.start()

    def _recibir_figura(self, nombre: str, figura) -> None:
        if nombre in self._paneles:
            self._paneles[nombre].establecer_figura(figura)

    def _al_terminar(self) -> None:
        self._indicador.ocultar()
        aplicar_fade_in(self)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._indicador.resize(self.size())
