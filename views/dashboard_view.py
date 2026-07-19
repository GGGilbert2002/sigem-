"""
views/dashboard_view.py
========================
Dashboard con mejoras visuales:
- Fade-in al entrar a la vista
- Contadores animados en las tarjetas KPI (ease-out desde 0)
- Indicador de carga mientras se generan los gráficos
- Efectos hover en las tarjetas KPI (vía QSS dinámico)
"""

from datetime import datetime

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from controllers import estadisticas_controller as ec
from controllers import graficos_controller as gc
from views.animaciones import aplicar_fade_in, animar_texto_numerico
from views.widgets_carga import IndicadorCarga


# =====================================================================
# Worker: genera los gráficos en un hilo separado para no bloquear
# la interfaz mientras matplotlib trabaja
# =====================================================================
class _WorkerGraficos(QThread):
    """
    Genera las figuras matplotlib en un hilo de fondo para que la
    interfaz no se congele durante la generación. Emite las figuras
    listas mediante señales Qt.
    """
    figura_municipio_lista = pyqtSignal(object)
    figura_genero_lista    = pyqtSignal(object)
    terminado              = pyqtSignal()
    error                  = pyqtSignal(str)

    def run(self) -> None:
        try:
            self.figura_municipio_lista.emit(gc.grafico_distribucion_municipio())
            self.figura_genero_lista.emit(gc.grafico_distribucion_genero())
            self.terminado.emit()
        except Exception as e:
            self.error.emit(str(e))


# =====================================================================
# Tarjeta KPI con hover y contador animado
# =====================================================================
class TarjetaKPI(QFrame):

    _QSS_BASE = (
        "QFrame {{ background-color: white; border: 1px solid #E5E5DD; "
        "border-top: 3px solid {color}; border-radius: 6px; }}"
    )
    _QSS_HOVER = (
        "QFrame {{ background-color: #F7FBF9; border: 1px solid #C8DDD3; "
        "border-top: 3px solid {color}; border-radius: 6px; }}"
    )

    def __init__(self, etiqueta: str, color: str = "#40916C"):
        super().__init__()
        self._color = color
        self._setQSS(hover=False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.label_valor = QLabel("—")
        self.label_valor.setStyleSheet(
            f"color: #1B4332; font-size: 24px; font-weight: 700; border: none;"
        )
        self.label_etiqueta = QLabel(etiqueta)
        self.label_etiqueta.setStyleSheet(
            "color: #888888; font-size: 11px; border: none;"
        )
        layout.addWidget(self.label_valor)
        layout.addWidget(self.label_etiqueta)

    def _setQSS(self, hover: bool) -> None:
        plantilla = self._QSS_HOVER if hover else self._QSS_BASE
        self.setStyleSheet(plantilla.format(color=self._color))

    def enterEvent(self, event) -> None:
        self._setQSS(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._setQSS(hover=False)
        super().leaveEvent(event)

    def actualizar(self, texto: str, animar: bool = True) -> None:
        if animar:
            animar_texto_numerico(self.label_valor, texto)
        else:
            self.label_valor.setText(texto)


# =====================================================================
# Panel de gráfico con hover sutil
# =====================================================================
class PanelGrafico(QFrame):

    def __init__(self, titulo: str):
        super().__init__()
        self._qss_base = (
            "QFrame { background-color: white; border: 1px solid #DDDDDD; "
            "border-radius: 8px; }"
        )
        self._qss_hover = (
            "QFrame { background-color: white; border: 1px solid #B0CFC0; "
            "border-radius: 8px; }"
        )
        self.setStyleSheet(self._qss_base)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 14, 16, 14)

        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet(
            "color: #1B4332; font-size: 13px; font-weight: 700; border: none;"
        )
        self._layout.addWidget(label_titulo)
        self._canvas = None

    def enterEvent(self, event) -> None:
        self.setStyleSheet(self._qss_hover)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.setStyleSheet(self._qss_base)
        super().leaveEvent(event)

    def establecer_figura(self, figura) -> None:
        if self._canvas is not None:
            self._layout.removeWidget(self._canvas)
            self._canvas.deleteLater()
        self._canvas = FigureCanvasQTAgg(figura)
        self._layout.addWidget(self._canvas)


# =====================================================================
# Vista del Dashboard
# =====================================================================
class DashboardView(QWidget):

    def __init__(self):
        super().__init__()
        self._worker = None
        self._construir_interfaz()
        self.refrescar()

    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(16)

        # Encabezado
        fila_enc = QHBoxLayout()
        titulo = QLabel("Dashboard General")
        titulo.setObjectName("tituloVista")
        self.label_fecha = QLabel("")
        self.label_fecha.setObjectName("subtituloVista")
        fila_enc.addWidget(titulo)
        fila_enc.addStretch()
        fila_enc.addWidget(self.label_fecha)
        layout.addLayout(fila_enc)

        # Fila de KPIs
        fila_kpi = QHBoxLayout()
        fila_kpi.setSpacing(14)
        self.kpi_total      = TarjetaKPI("Total de registros",        "#40916C")
        self.kpi_genero     = TarjetaKPI("Masculino / Femenino",      "#2D6A4F")
        self.kpi_edad       = TarjetaKPI("Edad promedio",             "#52796F")
        self.kpi_municipios = TarjetaKPI("Municipios con registros",  "#1B4332")
        for tarjeta in (self.kpi_total, self.kpi_genero,
                        self.kpi_edad, self.kpi_municipios):
            fila_kpi.addWidget(tarjeta)
        layout.addLayout(fila_kpi)

        # Fila de gráficos
        fila_graficos = QHBoxLayout()
        fila_graficos.setSpacing(14)
        self.panel_municipio = PanelGrafico("Participación por Municipio")
        self.panel_genero    = PanelGrafico("Distribución por Género")
        fila_graficos.addWidget(self.panel_municipio, stretch=2)
        fila_graficos.addWidget(self.panel_genero,    stretch=1)
        layout.addLayout(fila_graficos)
        layout.addStretch()

        # Indicador de carga (superpuesto, invisible por defecto)
        self._indicador = IndicadorCarga(self)

    # -----------------------------------------------------------------
    def refrescar(self) -> None:
        # Fecha
        dias_es = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
            "Thursday": "Jueves", "Friday": "Viernes",
            "Saturday": "Sábado", "Sunday": "Domingo",
        }
        meses_es = {
            "January": "enero", "February": "febrero", "March": "marzo",
            "April": "abril", "May": "mayo", "June": "junio",
            "July": "julio", "August": "agosto", "September": "septiembre",
            "October": "octubre", "November": "noviembre", "December": "diciembre",
        }
        ahora = datetime.now()
        dia_sem = dias_es.get(ahora.strftime("%A"), ahora.strftime("%A"))
        mes = meses_es.get(ahora.strftime("%B"), ahora.strftime("%B"))
        self.label_fecha.setText(f"{dia_sem}, {ahora.day} de {mes} de {ahora.year}")

        # KPIs desde la BD (sin hilo, son consultas rápidas)
        resumen = ec.resumen_general()
        self.kpi_total.actualizar(str(resumen["total_registros"]))
        self.kpi_genero.actualizar(
            f"{resumen['total_masculino']} / {resumen['total_femenino']}"
        )
        self.kpi_edad.actualizar(str(resumen["edad_promedio"]))
        self.kpi_municipios.actualizar(str(resumen["total_municipios_con_registros"]))

        # Gráficos en hilo de fondo
        self._generar_graficos_async()

    def _generar_graficos_async(self) -> None:
        """Lanza el worker en un hilo separado y muestra el indicador."""
        if self._worker and self._worker.isRunning():
            return  # ya hay uno corriendo, no lanzar otro

        self._indicador.mostrar(
            "Generando gráficos...",
            "Esto puede tardar unos segundos"
        )

        self._worker = _WorkerGraficos()
        self._worker.figura_municipio_lista.connect(
            self.panel_municipio.establecer_figura
        )
        self._worker.figura_genero_lista.connect(
            self.panel_genero.establecer_figura
        )
        self._worker.terminado.connect(self._al_terminar_graficos)
        self._worker.error.connect(self._al_error_graficos)
        self._worker.start()

    def _al_terminar_graficos(self) -> None:
        self._indicador.ocultar()
        aplicar_fade_in(self)

    def _al_error_graficos(self, mensaje: str) -> None:
        self._indicador.ocultar()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._indicador.resize(self.size())
