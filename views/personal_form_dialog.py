"""
views/personal_form_dialog.py
===============================
Diálogo modal con el formulario de creación/edición de un registro de
personal militar. Se usa tanto para "+ Nuevo Registro" como para el
botón de editar (✏️) en la tabla de gestión de personal.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from models import geografia
from models.militar import (
    CedulaDuplicadaError,
    PersonalMilitar,
    crear_personal,
    actualizar_personal,
)
from utils.validators import ValidationError
from database.connection import get_connection


def _cargar_catalogo(tabla: str, columna_id: str, columna_desc: str) -> list:
    """Carga genérico de catálogos simples (niveles educativos, grados, estatus)."""
    conn = get_connection()
    try:
        filas = conn.execute(f"SELECT {columna_id}, {columna_desc} FROM {tabla} ORDER BY {columna_desc}").fetchall()
        return [(f[columna_id], f[columna_desc]) for f in filas]
    finally:
        conn.close()


class PersonalFormDialog(QDialog):
    """
    Diálogo con el formulario completo de personal militar.
    Si se pasa 'registro_existente', el diálogo entra en modo edición
    y precarga los datos; si no, entra en modo creación.
    """

    def __init__(self, parent=None, registro_existente: PersonalMilitar = None):
        super().__init__(parent)
        self.registro_existente = registro_existente
        self.setWindowTitle(
            "Editar Registro de Personal" if registro_existente else "Nuevo Registro de Personal"
        )
        self.setMinimumWidth(480)
        self._construir_interfaz()
        self._cargar_combos()
        if registro_existente:
            self._precargar_datos(registro_existente)

    # -------------------------------------------------------------
    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)

        titulo = QLabel(
            "Editar Registro de Personal" if self.registro_existente else "Nuevo Registro de Personal"
        )
        titulo.setObjectName("tituloVista")
        layout.addWidget(titulo)

        formulario = QFormLayout()
        formulario.setSpacing(10)
        formulario.setContentsMargins(0, 14, 0, 14)

        self.input_cedula = QLineEdit()
        self.input_cedula.setPlaceholderText("Ej: 12345678")
        formulario.addRow("Cédula *", self.input_cedula)

        self.input_nombres = QLineEdit()
        formulario.addRow("Nombres *", self.input_nombres)

        self.input_apellidos = QLineEdit()
        formulario.addRow("Apellidos *", self.input_apellidos)

        self.input_fecha_nacimiento = QDateEdit()
        self.input_fecha_nacimiento.setCalendarPopup(True)
        self.input_fecha_nacimiento.setDisplayFormat("yyyy-MM-dd")
        formulario.addRow("Fecha de nacimiento *", self.input_fecha_nacimiento)

        self.combo_genero = QComboBox()
        self.combo_genero.addItems(["Masculino", "Femenino"])
        formulario.addRow("Género *", self.combo_genero)

        self.combo_municipio = QComboBox()
        self.combo_municipio.currentIndexChanged.connect(self._al_cambiar_municipio)
        formulario.addRow("Municipio *", self.combo_municipio)

        self.combo_parroquia = QComboBox()
        formulario.addRow("Parroquia", self.combo_parroquia)

        self.combo_nivel_educativo = QComboBox()
        formulario.addRow("Nivel educativo", self.combo_nivel_educativo)

        self.combo_grado = QComboBox()
        formulario.addRow("Grado militar", self.combo_grado)

        self.combo_estatus = QComboBox()
        formulario.addRow("Estatus de participación *", self.combo_estatus)

        self.input_telefono = QLineEdit()
        self.input_telefono.setPlaceholderText("Ej: 0414-1234567")
        formulario.addRow("Teléfono", self.input_telefono)

        self.input_direccion = QLineEdit()
        formulario.addRow("Dirección", self.input_direccion)

        self.input_observaciones = QTextEdit()
        self.input_observaciones.setMaximumHeight(60)
        formulario.addRow("Observaciones", self.input_observaciones)

        layout.addLayout(formulario)

        self.label_error = QLabel("")
        self.label_error.setStyleSheet("color: #A32D2D; font-size: 11.5px;")
        self.label_error.setWordWrap(True)
        self.label_error.setVisible(False)
        layout.addWidget(self.label_error)

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()
        boton_cancelar = QPushButton("Cancelar")
        boton_cancelar.setObjectName("btnSecundario")
        boton_cancelar.clicked.connect(self.reject)
        boton_guardar = QPushButton("Guardar")
        boton_guardar.setObjectName("btnPrimario")
        boton_guardar.clicked.connect(self._guardar)
        fila_botones.addWidget(boton_cancelar)
        fila_botones.addWidget(boton_guardar)
        layout.addLayout(fila_botones)

    # -------------------------------------------------------------
    def _cargar_combos(self) -> None:
        self.combo_municipio.clear()
        for municipio in geografia.listar_municipios(solo_adyacentes_coro=True):
            self.combo_municipio.addItem(municipio.nombre, municipio.id_municipio)

        self.combo_nivel_educativo.clear()
        self.combo_nivel_educativo.addItem("(No especificado)", None)
        for id_nivel, desc in _cargar_catalogo("niveles_educativos", "id_nivel_educativo", "descripcion"):
            self.combo_nivel_educativo.addItem(desc, id_nivel)

        self.combo_grado.clear()
        self.combo_grado.addItem("(No especificado)", None)
        for id_grado, nombre in _cargar_catalogo("grados_militares", "id_grado", "nombre"):
            self.combo_grado.addItem(nombre, id_grado)

        self.combo_estatus.clear()
        for id_estatus, desc in _cargar_catalogo("estatus_participacion", "id_estatus", "descripcion"):
            self.combo_estatus.addItem(desc, id_estatus)

        self._al_cambiar_municipio()

    def _al_cambiar_municipio(self) -> None:
        """Recarga el combo de parroquias según el municipio seleccionado (combos dependientes)."""
        id_municipio = self.combo_municipio.currentData()
        self.combo_parroquia.clear()
        self.combo_parroquia.addItem("(Sin especificar)", None)
        if id_municipio:
            for parroquia in geografia.listar_parroquias_por_municipio(id_municipio):
                self.combo_parroquia.addItem(parroquia.nombre, parroquia.id_parroquia)

    def _precargar_datos(self, registro: PersonalMilitar) -> None:
        from PyQt6.QtCore import QDate

        self.input_cedula.setText(registro.cedula)
        self.input_nombres.setText(registro.nombres)
        self.input_apellidos.setText(registro.apellidos)

        anio, mes, dia = (int(x) for x in registro.fecha_nacimiento.split("-"))
        self.input_fecha_nacimiento.setDate(QDate(anio, mes, dia))

        self.combo_genero.setCurrentIndex(0 if registro.genero == "Masculino" else 1)

        idx_municipio = self.combo_municipio.findData(registro.id_municipio)
        if idx_municipio >= 0:
            self.combo_municipio.setCurrentIndex(idx_municipio)
        self._al_cambiar_municipio()

        if registro.id_parroquia:
            idx_parroquia = self.combo_parroquia.findData(registro.id_parroquia)
            if idx_parroquia >= 0:
                self.combo_parroquia.setCurrentIndex(idx_parroquia)

        idx_estatus = self.combo_estatus.findData(registro.id_estatus)
        if idx_estatus >= 0:
            self.combo_estatus.setCurrentIndex(idx_estatus)

        self.input_telefono.setText(registro.telefono or "")
        self.input_direccion.setText(registro.direccion or "")
        self.input_observaciones.setPlainText(registro.observaciones or "")

    # -------------------------------------------------------------
    def _recopilar_datos(self) -> dict:
        fecha_qdate = self.input_fecha_nacimiento.date()
        fecha_iso = f"{fecha_qdate.year():04d}-{fecha_qdate.month():02d}-{fecha_qdate.day():02d}"

        return {
            "cedula": self.input_cedula.text(),
            "nombres": self.input_nombres.text(),
            "apellidos": self.input_apellidos.text(),
            "fecha_nacimiento": fecha_iso,
            "genero": self.combo_genero.currentText(),
            "id_municipio": self.combo_municipio.currentData(),
            "id_parroquia": self.combo_parroquia.currentData(),
            "id_nivel_educativo": self.combo_nivel_educativo.currentData(),
            "id_grado": self.combo_grado.currentData(),
            "id_estatus": self.combo_estatus.currentData(),
            "telefono": self.input_telefono.text(),
            "direccion": self.input_direccion.text(),
            "observaciones": self.input_observaciones.toPlainText(),
        }

    def _guardar(self) -> None:
        datos = self._recopilar_datos()
        try:
            if self.registro_existente:
                actualizar_personal(self.registro_existente.id_personal, datos)
            else:
                crear_personal(datos)
            self.accept()
        except (ValidationError, CedulaDuplicadaError) as e:
            self._mostrar_error(str(e))
        except Exception as e:
            self._mostrar_error(f"Error inesperado al guardar: {e}")

    def _mostrar_error(self, mensaje: str) -> None:
        self.label_error.setText(mensaje)
        self.label_error.setVisible(True)
