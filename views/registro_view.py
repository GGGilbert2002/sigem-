"""
views/registro_view.py
=======================
Pantalla completa dedicada al registro manual de personal militar,
accesible desde el menú lateral ("Registrar Personal"). Complementa
al diálogo modal rápido de Gestión de Personal: esta versión es más
espaciosa, con el formulario en dos columnas, mensajes de confirmación
visibles, y botón de limpiar para registrar varios seguidos.
"""

from datetime import date

from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database.connection import get_connection
from models import geografia
from models.militar import CedulaDuplicadaError, crear_personal
from utils.validators import ValidationError


def _cargar_catalogo(tabla: str, columna_id: str, columna_desc: str) -> list:
    conn = get_connection()
    try:
        filas = conn.execute(
            f"SELECT {columna_id}, {columna_desc} FROM {tabla} ORDER BY {columna_desc}"
        ).fetchall()
        return [(f[columna_id], f[columna_desc]) for f in filas]
    finally:
        conn.close()


class _CampoEtiquetado(QWidget):
    """Etiqueta + widget de entrada apilados verticalmente."""

    def __init__(self, etiqueta: str, widget: QWidget, obligatorio: bool = False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        texto = etiqueta + (" *" if obligatorio else "")
        lbl = QLabel(texto)
        color = "#A33" if obligatorio else "#555"
        lbl.setStyleSheet(
            f"font-size: 11.5px; font-weight: 600; color: {color}; border: none;"
        )
        layout.addWidget(lbl)
        layout.addWidget(widget)


class RegistroView(QWidget):
    """Pantalla de registro manual de personal (formulario amplio)."""

    def __init__(self):
        super().__init__()
        self._construir_interfaz()
        self._cargar_combos()

    # -----------------------------------------------------------------
    def _construir_interfaz(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(28, 22, 28, 22)
        raiz.setSpacing(14)

        # Encabezado
        fila_enc = QHBoxLayout()
        titulo = QLabel("Registrar Personal")
        titulo.setObjectName("tituloVista")
        subtitulo = QLabel("Ingreso manual de datos de participación")
        subtitulo.setObjectName("subtituloVista")
        fila_enc.addWidget(titulo)
        fila_enc.addStretch()
        fila_enc.addWidget(subtitulo)
        raiz.addLayout(fila_enc)

        # Tarjeta del formulario (con scroll por si la ventana es pequeña)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        tarjeta = QFrame()
        tarjeta.setStyleSheet(
            "QFrame { background-color: white; border: 1px solid #DDDDDD; "
            "border-radius: 10px; }"
        )
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(28, 24, 28, 24)
        layout_tarjeta.setSpacing(18)

        # ---- Sección: Datos personales ----
        layout_tarjeta.addWidget(self._titulo_seccion("Datos Personales"))
        grid1 = QGridLayout()
        grid1.setHorizontalSpacing(20)
        grid1.setVerticalSpacing(14)

        self.input_cedula = QLineEdit()
        self.input_cedula.setPlaceholderText("Ej: 12345678")
        self.input_nombres = QLineEdit()
        self.input_apellidos = QLineEdit()
        self.input_fecha_nac = QDateEdit()
        self.input_fecha_nac.setCalendarPopup(True)
        self.input_fecha_nac.setDisplayFormat("yyyy-MM-dd")
        self.input_fecha_nac.setDate(QDate(2000, 1, 1))
        self.combo_genero = QComboBox()
        self.combo_genero.addItems(["Masculino", "Femenino"])
        self.input_telefono = QLineEdit()
        self.input_telefono.setPlaceholderText("Ej: 0414-1234567")

        grid1.addWidget(_CampoEtiquetado("Cédula", self.input_cedula, True), 0, 0)
        grid1.addWidget(_CampoEtiquetado("Nombres", self.input_nombres, True), 0, 1)
        grid1.addWidget(_CampoEtiquetado("Apellidos", self.input_apellidos, True), 0, 2)
        grid1.addWidget(_CampoEtiquetado("Fecha de nacimiento", self.input_fecha_nac, True), 1, 0)
        grid1.addWidget(_CampoEtiquetado("Género", self.combo_genero, True), 1, 1)
        grid1.addWidget(_CampoEtiquetado("Teléfono", self.input_telefono), 1, 2)
        layout_tarjeta.addLayout(grid1)

        # ---- Sección: Ubicación territorial ----
        layout_tarjeta.addWidget(self._titulo_seccion("Ubicación Territorial"))
        grid2 = QGridLayout()
        grid2.setHorizontalSpacing(20)
        grid2.setVerticalSpacing(14)

        self.combo_municipio = QComboBox()
        self.combo_municipio.currentIndexChanged.connect(self._al_cambiar_municipio)
        self.combo_parroquia = QComboBox()
        self.input_direccion = QLineEdit()

        grid2.addWidget(_CampoEtiquetado("Municipio", self.combo_municipio, True), 0, 0)
        grid2.addWidget(_CampoEtiquetado("Parroquia", self.combo_parroquia), 0, 1)
        grid2.addWidget(_CampoEtiquetado("Dirección", self.input_direccion), 0, 2)
        layout_tarjeta.addLayout(grid2)

        # ---- Sección: Datos militares ----
        layout_tarjeta.addWidget(self._titulo_seccion("Datos Militares y de Participación"))
        grid3 = QGridLayout()
        grid3.setHorizontalSpacing(20)
        grid3.setVerticalSpacing(14)

        self.combo_nivel = QComboBox()
        self.combo_grado = QComboBox()
        self.combo_estatus = QComboBox()

        grid3.addWidget(_CampoEtiquetado("Nivel educativo", self.combo_nivel), 0, 0)
        grid3.addWidget(_CampoEtiquetado("Grado militar", self.combo_grado), 0, 1)
        grid3.addWidget(_CampoEtiquetado("Estatus de participación", self.combo_estatus, True), 0, 2)
        layout_tarjeta.addLayout(grid3)

        self.input_observaciones = QTextEdit()
        self.input_observaciones.setMaximumHeight(70)
        layout_tarjeta.addWidget(
            _CampoEtiquetado("Observaciones", self.input_observaciones)
        )

        # ---- Mensajes de resultado ----
        self.label_mensaje = QLabel("")
        self.label_mensaje.setWordWrap(True)
        self.label_mensaje.setVisible(False)
        layout_tarjeta.addWidget(self.label_mensaje)

        # ---- Botones ----
        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        btn_limpiar = QPushButton("Limpiar formulario")
        btn_limpiar.setObjectName("btnSecundario")
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.clicked.connect(self._limpiar)
        self.btn_guardar = QPushButton("💾  Guardar Registro")
        self.btn_guardar.setObjectName("btnPrimario")
        self.btn_guardar.setMinimumHeight(38)
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.clicked.connect(self._guardar)
        fila_botones.addWidget(btn_limpiar)
        fila_botones.addWidget(self.btn_guardar)
        layout_tarjeta.addLayout(fila_botones)

        scroll.setWidget(tarjeta)
        raiz.addWidget(scroll)

    def _titulo_seccion(self, texto: str) -> QLabel:
        lbl = QLabel(texto.upper())
        lbl.setStyleSheet(
            "color: #1B4332; font-size: 12px; font-weight: 700; "
            "letter-spacing: 1px; border: none; "
            "border-bottom: 2px solid #D4AF37; padding-bottom: 4px;"
        )
        return lbl

    # -----------------------------------------------------------------
    def _cargar_combos(self) -> None:
        self.combo_municipio.blockSignals(True)
        self.combo_municipio.clear()
        for m in geografia.listar_municipios(solo_adyacentes_coro=True):
            self.combo_municipio.addItem(m.nombre, m.id_municipio)
        self.combo_municipio.blockSignals(False)

        self.combo_nivel.clear()
        self.combo_nivel.addItem("(No especificado)", None)
        for id_n, desc in _cargar_catalogo("niveles_educativos", "id_nivel_educativo", "descripcion"):
            self.combo_nivel.addItem(desc, id_n)

        self.combo_grado.clear()
        self.combo_grado.addItem("(No especificado)", None)
        for id_g, nombre in _cargar_catalogo("grados_militares", "id_grado", "nombre"):
            self.combo_grado.addItem(nombre, id_g)

        self.combo_estatus.clear()
        for id_e, desc in _cargar_catalogo("estatus_participacion", "id_estatus", "descripcion"):
            self.combo_estatus.addItem(desc, id_e)

        self._al_cambiar_municipio()

    def _al_cambiar_municipio(self) -> None:
        id_municipio = self.combo_municipio.currentData()
        self.combo_parroquia.clear()
        self.combo_parroquia.addItem("(Sin especificar)", None)
        if id_municipio:
            for p in geografia.listar_parroquias_por_municipio(id_municipio):
                self.combo_parroquia.addItem(p.nombre, p.id_parroquia)

    def refrescar(self) -> None:
        """Al navegar a esta vista, recargar catálogos (por si cambiaron)."""
        self._cargar_combos()

    # -----------------------------------------------------------------
    def _guardar(self) -> None:
        fecha_q = self.input_fecha_nac.date()
        datos = {
            "cedula": self.input_cedula.text(),
            "nombres": self.input_nombres.text(),
            "apellidos": self.input_apellidos.text(),
            "fecha_nacimiento": f"{fecha_q.year():04d}-{fecha_q.month():02d}-{fecha_q.day():02d}",
            "genero": self.combo_genero.currentText(),
            "id_municipio": self.combo_municipio.currentData(),
            "id_parroquia": self.combo_parroquia.currentData(),
            "id_nivel_educativo": self.combo_nivel.currentData(),
            "id_grado": self.combo_grado.currentData(),
            "id_estatus": self.combo_estatus.currentData(),
            "telefono": self.input_telefono.text(),
            "direccion": self.input_direccion.text(),
            "observaciones": self.input_observaciones.toPlainText(),
        }
        try:
            nuevo = crear_personal(datos)
        except (ValidationError, CedulaDuplicadaError) as e:
            self._mostrar_mensaje(str(e), exito=False)
            return
        except Exception as e:
            self._mostrar_mensaje(f"Error inesperado: {e}", exito=False)
            return

        self._mostrar_mensaje(
            f"✓ Registro guardado correctamente: {nuevo.nombres} {nuevo.apellidos} "
            f"(C.I. {nuevo.cedula})",
            exito=True,
        )
        self._limpiar(mantener_mensaje=True)

    def _mostrar_mensaje(self, texto: str, exito: bool) -> None:
        if exito:
            estilo = (
                "background-color: #E3F3EA; color: #1B4332; border: 1px solid #B7DFC9; "
                "border-radius: 6px; padding: 10px; font-size: 12.5px; font-weight: 600;"
            )
        else:
            estilo = (
                "background-color: #FBE3E3; color: #A32D2D; border: 1px solid #EFC2C2; "
                "border-radius: 6px; padding: 10px; font-size: 12.5px; font-weight: 600;"
            )
        self.label_mensaje.setStyleSheet(estilo)
        self.label_mensaje.setText(texto)
        self.label_mensaje.setVisible(True)
        # El mensaje de éxito desaparece solo tras unos segundos
        if exito:
            QTimer.singleShot(6000, lambda: self.label_mensaje.setVisible(False))

    def _limpiar(self, mantener_mensaje: bool = False) -> None:
        self.input_cedula.clear()
        self.input_nombres.clear()
        self.input_apellidos.clear()
        self.input_fecha_nac.setDate(QDate(2000, 1, 1))
        self.combo_genero.setCurrentIndex(0)
        if self.combo_municipio.count() > 0:
            self.combo_municipio.setCurrentIndex(0)
        self.input_telefono.clear()
        self.input_direccion.clear()
        self.input_observaciones.setPlainText("")
        if self.combo_nivel.count() > 0:
            self.combo_nivel.setCurrentIndex(0)
        if self.combo_grado.count() > 0:
            self.combo_grado.setCurrentIndex(0)
        if self.combo_estatus.count() > 0:
            self.combo_estatus.setCurrentIndex(0)
        if not mantener_mensaje:
            self.label_mensaje.setVisible(False)
        self.input_cedula.setFocus()
