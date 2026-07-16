"""
views/reportes_view.py
========================
Pantalla de Reportes: tarjetas con los distintos reportes exportables
(PDF estadístico, Excel de personal, PDF de listado), según el
wireframe aprobado. Al generar, se le pide al usuario dónde guardar
el archivo, y luego se le ofrece abrir la carpeta/archivo.
"""

import os
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import config
from models.militar import listar_personal
from utils import exporters


def _abrir_archivo_en_sistema(ruta: str) -> None:
    """Abre un archivo con el programa predeterminado del sistema operativo."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(ruta)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", ruta], check=False)
        else:
            subprocess.run(["xdg-open", ruta], check=False)
    except Exception:
        pass  # Si no se puede abrir automáticamente, el usuario lo abre manualmente


class TarjetaReporte(QFrame):
    """Tarjeta individual de reporte, con icono, descripción y botón de generación."""

    def __init__(self, icono_texto: str, color_icono: str, titulo: str, descripcion: str,
                 texto_boton: str, funcion_generar):
        super().__init__()
        self._funcion_generar = funcion_generar
        self.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #DDDDDD; border-radius: 8px; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(14)

        icono = QLabel(icono_texto)
        icono.setFixedSize(42, 42)
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono.setStyleSheet(
            f"background-color: {color_icono}; color: white; border-radius: 8px; "
            f"font-size: 13px; font-weight: 700;"
        )
        layout.addWidget(icono)

        contenedor_info = QVBoxLayout()
        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet("color: #1B4332; font-size: 13.5px; font-weight: 600; border:none;")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setStyleSheet("color: #888888; font-size: 11.5px; border:none;")
        label_descripcion.setWordWrap(True)
        contenedor_info.addWidget(label_titulo)
        contenedor_info.addWidget(label_descripcion)
        layout.addLayout(contenedor_info, stretch=1)

        boton = QPushButton(texto_boton)
        boton.setObjectName("btnPrimario")
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.clicked.connect(self._generar)
        layout.addWidget(boton)

        self._boton = boton

    def _generar(self) -> None:
        try:
            self._boton.setEnabled(False)
            self._boton.setText("Generando...")
            ruta_generada = self._funcion_generar()
            self._boton.setText("✓ Generado")
            respuesta = QMessageBox.question(
                self,
                "Reporte generado",
                f"El reporte se generó correctamente en:\n{ruta_generada}\n\n"
                "¿Desea abrirlo ahora?",
            )
            if respuesta == QMessageBox.StandardButton.Yes:
                _abrir_archivo_en_sistema(ruta_generada)
        except Exception as e:
            QMessageBox.critical(self, "Error al generar el reporte", str(e))
        finally:
            self._boton.setEnabled(True)
            self._boton.setText("Generar")


class ReportesView(QWidget):
    """Vista de generación y exportación de reportes."""

    def __init__(self):
        super().__init__()
        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        fila_encabezado = QHBoxLayout()
        titulo = QLabel("Reportes")
        titulo.setObjectName("tituloVista")
        subtitulo = QLabel("Exportación de datos y análisis")
        subtitulo.setObjectName("subtituloVista")
        fila_encabezado.addWidget(titulo)
        fila_encabezado.addStretch()
        fila_encabezado.addWidget(subtitulo)
        layout.addLayout(fila_encabezado)

        tarjeta_pdf_estadistico = TarjetaReporte(
            "PDF", "#C0392B",
            "Reporte Estadístico Completo",
            "Resumen general + gráficos de género, edad, nivel educativo y municipio",
            "Generar PDF",
            self._generar_pdf_estadistico,
        )
        layout.addWidget(tarjeta_pdf_estadistico)

        tarjeta_excel_personal = TarjetaReporte(
            "XLS", "#1D6F42",
            "Listado de Personal (Excel)",
            "Exporta todos los registros con formato profesional y filtros automáticos",
            "Generar Excel",
            self._generar_excel_personal,
        )
        layout.addWidget(tarjeta_excel_personal)

        tarjeta_pdf_personal = TarjetaReporte(
            "PDF", "#C0392B",
            "Listado de Personal (PDF)",
            "Tabla paginada lista para imprimir o archivar",
            "Generar PDF",
            self._generar_pdf_personal,
        )
        layout.addWidget(tarjeta_pdf_personal)

        tarjeta_excel_resumen = TarjetaReporte(
            "XLS", "#1D6F42",
            "Resumen Estadístico (Excel multi-hoja)",
            "Anexo estadístico con hojas separadas: resumen, municipio, parroquia, estatus",
            "Generar Excel",
            self._generar_excel_resumen,
        )
        layout.addWidget(tarjeta_excel_resumen)

        layout.addStretch()

    # -------------------------------------------------------------
    # Generadores (cada uno retorna la ruta del archivo creado)
    # -------------------------------------------------------------
    def _generar_pdf_estadistico(self) -> str:
        return exporters.generar_reporte_estadistico_pdf(incluir_graficos=True)

    def _generar_excel_personal(self) -> str:
        personal = listar_personal()
        return exporters.exportar_personal_excel(personal)

    def _generar_pdf_personal(self) -> str:
        personal = listar_personal()
        return exporters.generar_reporte_personal_pdf(personal)

    def _generar_excel_resumen(self) -> str:
        return exporters.exportar_resumen_estadistico_excel()
