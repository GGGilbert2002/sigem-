"""
views/dashboard_view.py
========================
Pantalla de Dashboard: primera vista tras iniciar sesión. Muestra los
indicadores generales (KPIs) y dos gráficos resumen (municipio y
género), igual a la distribución aprobada en el wireframe.
"""

from datetime import datetime

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from controllers import estadisticas_controller as ec
from controllers import graficos_controller as gc


class TarjetaKPI(QFrame):
    """Tarjeta individual de indicador (KPI) para la fila superior del dashboard."""

    def __init__(self, valor_inicial: str, etiqueta: str):
        super().__init__()
        self.setProperty("class", "kpiCard")
        self.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #E5E5DD; "
            "border-top: 3px solid #40916C; border-radius: 6px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        self.label_valor = QLabel(valor_inicial)
        self.label_valor.setStyleSheet(
            "color: #1B4332; font-size: 24px; font-weight: 700; border: none;"
        )
        self.label_etiqueta = QLabel(etiqueta)
        self.label_etiqueta.setStyleSheet("color: #888888; font-size: 11px; border: none;")

        layout.addWidget(self.label_valor)
        layout.addWidget(self.label_etiqueta)

    def actualizar_valor(self, nuevo_valor: str) -> None:
        self.label_valor.setText(nuevo_valor)


class PanelGrafico(QFrame):
    """Panel contenedor blanco con título + un gráfico de matplotlib embebido."""

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
        """Reemplaza el gráfico actual por una nueva figura de matplotlib."""
        if self._canvas_actual is not None:
            self.layout_interno.removeWidget(self._canvas_actual)
            self._canvas_actual.deleteLater()

        self._canvas_actual = FigureCanvasQTAgg(figura)
        self.layout_interno.addWidget(self._canvas_actual)


class DashboardView(QWidget):
    """Vista principal de Dashboard, mostrada justo después del login."""

    def __init__(self):
        super().__init__()
        self._construir_interfaz()
        self.refrescar()

    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(16)

        # --- Encabezado ---
        fila_encabezado = QHBoxLayout()
        titulo = QLabel("Dashboard General")
        titulo.setObjectName("tituloVista")
        self.label_fecha = QLabel("")
        self.label_fecha.setObjectName("subtituloVista")
        fila_encabezado.addWidget(titulo)
        fila_encabezado.addStretch()
        fila_encabezado.addWidget(self.label_fecha)
        layout.addLayout(fila_encabezado)

        # --- Fila de KPIs ---
        fila_kpi = QHBoxLayout()
        fila_kpi.setSpacing(14)
        self.kpi_total = TarjetaKPI("0", "Total de registros")
        self.kpi_genero = TarjetaKPI("0 / 0", "Masculino / Femenino")
        self.kpi_edad = TarjetaKPI("0.0", "Edad promedio")
        self.kpi_municipios = TarjetaKPI("0", "Municipios con registros")
        for tarjeta in (self.kpi_total, self.kpi_genero, self.kpi_edad, self.kpi_municipios):
            fila_kpi.addWidget(tarjeta)
        layout.addLayout(fila_kpi)

        # --- Fila de gráficos ---
        fila_graficos = QHBoxLayout()
        fila_graficos.setSpacing(14)
        self.panel_municipio = PanelGrafico("Participación por Municipio")
        self.panel_genero = PanelGrafico("Distribución por Género")
        fila_graficos.addWidget(self.panel_municipio, stretch=2)
        fila_graficos.addWidget(self.panel_genero, stretch=1)
        layout.addLayout(fila_graficos)

        layout.addStretch()

    def refrescar(self) -> None:
        """
        Recarga los datos del dashboard desde la base de datos. Se
        invoca automáticamente cada vez que el usuario navega a esta
        vista (ver MainWindow.navegar_a), así siempre muestra
        información actualizada.
        """
        self.label_fecha.setText(datetime.now().strftime("%A, %d de %B de %Y").capitalize())

        resumen = ec.resumen_general()
        self.kpi_total.actualizar_valor(str(resumen["total_registros"]))
        self.kpi_genero.actualizar_valor(
            f"{resumen['total_masculino']} / {resumen['total_femenino']}"
        )
        self.kpi_edad.actualizar_valor(str(resumen["edad_promedio"]))
        self.kpi_municipios.actualizar_valor(str(resumen["total_municipios_con_registros"]))

        self.panel_municipio.establecer_figura(gc.grafico_distribucion_municipio())
        self.panel_genero.establecer_figura(gc.grafico_distribucion_genero())
