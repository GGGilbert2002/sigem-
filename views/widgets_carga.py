"""
views/widgets_carga.py
=======================
Widget de indicador de carga (spinner + mensaje) reutilizable en
todas las vistas que generan gráficos o mapas.

Uso:
    # En el __init__ de una vista:
    self.indicador = IndicadorCarga(parent=self)

    # Al iniciar una tarea pesada:
    self.indicador.mostrar("Generando gráficos...")

    # Al terminar:
    self.indicador.ocultar()
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class IndicadorCarga(QFrame):
    """
    Panel semitransparente superpuesto que muestra un spinner de texto
    rotatorio y un mensaje mientras se ejecuta una tarea pesada.
    Bloquea la interacción del usuario con el área debajo.
    """

    _FRAMES_SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._frame_actual = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._avanzar_spinner)
        self._construir_interfaz()
        self.ocultar()

    def _construir_interfaz(self) -> None:
        self.setStyleSheet(
            "QFrame { background-color: rgba(245, 245, 240, 210); "
            "border-radius: 8px; }"
        )
        layout_outer = QVBoxLayout(self)
        layout_outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tarjeta central con el spinner y el mensaje
        tarjeta = QFrame()
        tarjeta.setStyleSheet(
            "QFrame { background-color: white; border-radius: 10px; "
            "border: 1px solid #DDDDDD; }"
        )
        tarjeta.setFixedWidth(260)
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(24, 20, 24, 20)
        layout_tarjeta.setSpacing(10)

        self._label_spinner = QLabel(self._FRAMES_SPINNER[0])
        self._label_spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_spinner.setStyleSheet(
            "font-size: 28px; color: #40916C; border: none; "
            "background: transparent;"
        )

        self._label_mensaje = QLabel("Cargando...")
        self._label_mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_mensaje.setWordWrap(True)
        self._label_mensaje.setStyleSheet(
            "font-size: 13px; color: #1B4332; font-weight: 600; "
            "border: none; background: transparent;"
        )

        self._label_detalle = QLabel("")
        self._label_detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_detalle.setWordWrap(True)
        self._label_detalle.setStyleSheet(
            "font-size: 11px; color: #888888; border: none; "
            "background: transparent;"
        )

        layout_tarjeta.addWidget(self._label_spinner)
        layout_tarjeta.addWidget(self._label_mensaje)
        layout_tarjeta.addWidget(self._label_detalle)
        layout_outer.addWidget(tarjeta, alignment=Qt.AlignmentFlag.AlignCenter)

    def mostrar(self, mensaje: str = "Cargando...",
                detalle: str = "Esto puede tardar unos segundos") -> None:
        """Muestra el indicador y arranca el spinner."""
        self._label_mensaje.setText(mensaje)
        self._label_detalle.setText(detalle)
        self._ajustar_tamano()
        self.raise_()
        self.setVisible(True)
        self._timer.start(80)  # fps del spinner

    def ocultar(self) -> None:
        """Oculta el indicador y detiene el spinner."""
        self._timer.stop()
        self.setVisible(False)

    def _avanzar_spinner(self) -> None:
        self._frame_actual = (self._frame_actual + 1) % len(self._FRAMES_SPINNER)
        self._label_spinner.setText(self._FRAMES_SPINNER[self._frame_actual])

    def _ajustar_tamano(self) -> None:
        """Se ajusta al tamaño del widget padre para cubrirlo por completo."""
        if self.parent():
            self.resize(self.parent().size())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._ajustar_tamano()
