"""
views/animaciones.py
=====================
Utilidades de animación reutilizables para toda la interfaz:

1. aplicar_fade_in(widget): transición de desvanecimiento al mostrar
   una vista (usada por MainWindow al navegar entre pantallas).
2. animar_texto_numerico(label, texto_final): efecto de "contador"
   que anima los números de un QLabel desde 0 hasta su valor final
   (usado por las tarjetas KPI del Dashboard).

Diseño: las animaciones son cortas (< 1 segundo) y se auto-limpian al
terminar, para no interferir con el renderizado normal ni acumular
objetos en memoria.
"""

import re

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer
from PyQt6.QtWidgets import QGraphicsOpacityEffect

_PATRON_NUMERO = re.compile(r"\d+(?:\.\d+)?")


# =====================================================================
# 1) FADE-IN de vistas
# =====================================================================

def aplicar_fade_in(widget, duracion_ms: int = 280) -> None:
    """
    Aplica un efecto de aparición gradual (fade-in) al widget.
    Al terminar, remueve el efecto de opacidad para devolver el
    renderizado normal (algunos widgets, como los canvas de matplotlib,
    pueden verse borrosos si el efecto queda activo permanentemente).
    """
    efecto = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(efecto)

    animacion = QPropertyAnimation(efecto, b"opacity", widget)
    animacion.setDuration(duracion_ms)
    animacion.setStartValue(0.0)
    animacion.setEndValue(1.0)
    animacion.setEasingCurve(QEasingCurve.Type.InOutQuad)
    animacion.finished.connect(lambda w=widget: w.setGraphicsEffect(None))
    animacion.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


# =====================================================================
# 2) CONTADOR ANIMADO para KPIs
# =====================================================================

def _texto_en_progreso(texto_final: str, progreso: float) -> str:
    """
    Función pura (testeable sin Qt): interpola TODOS los números que
    aparezcan en 'texto_final' según el progreso (0.0 a 1.0).

    Ejemplos con progreso=0.5:
        "250"       -> "125"
        "126 / 124" -> "63 / 62"
        "26.5"      -> "13.3"  (respeta la cantidad de decimales)
    """
    progreso = max(0.0, min(1.0, progreso))

    def reemplazo(match):
        texto_num = match.group()
        valor_final = float(texto_num)
        valor_actual = valor_final * progreso
        if "." in texto_num:
            decimales = len(texto_num.split(".")[1])
            return f"{valor_actual:.{decimales}f}"
        return str(int(round(valor_actual)))

    return _PATRON_NUMERO.sub(reemplazo, texto_final)


def animar_texto_numerico(label, texto_final: str,
                          duracion_ms: int = 850, pasos: int = 30) -> None:
    """
    Anima los números dentro del texto de un QLabel, contando desde 0
    hasta su valor final con desaceleración suave (ease-out).
    Si el texto no contiene números, simplemente lo asigna directo.
    """
    if not _PATRON_NUMERO.search(texto_final):
        label.setText(texto_final)
        return

    # Detener cualquier animación previa sobre el mismo label
    timer_previo = label.property("_timer_contador")
    if timer_previo is not None:
        try:
            timer_previo.stop()
        except RuntimeError:
            pass  # el timer previo ya fue destruido por Qt

    paso_actual = {"n": 0}
    timer = QTimer(label)
    label.setProperty("_timer_contador", timer)

    def _tick():
        paso_actual["n"] += 1
        t = paso_actual["n"] / pasos
        # Ease-out cúbico: arranca rápido y frena al final
        progreso = 1 - (1 - t) ** 3
        label.setText(_texto_en_progreso(texto_final, progreso))
        if paso_actual["n"] >= pasos:
            timer.stop()
            label.setText(texto_final)  # asegurar el valor exacto final

    timer.timeout.connect(_tick)
    timer.start(max(10, duracion_ms // pasos))
