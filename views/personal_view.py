"""
views/personal_view.py
========================
Pantalla de Gestión de Personal: tabla con todos los registros,
barra de búsqueda/filtros, y botones de Nuevo/Editar/Eliminar,
según el wireframe aprobado.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models import geografia
from models.militar import (
    PersonalMilitar,
    RegistroNoEncontradoError,
    buscar_personal,
    eliminar_personal,
)
from views.personal_form_dialog import PersonalFormDialog

COLUMNAS = [
    "Cédula", "Nombre", "Edad", "Género", "Municipio",
    "Estatus", "Acciones",
]

# Clasificación de estatus para el color del badge (coherente con el wireframe)
ESTATUS_OK = {"Incorporado", "Alistado", "Registrado"}
ESTATUS_WARN = {"Convocado", "Diferido"}
ESTATUS_BAD = {"Rechazado (No apto)", "Desertor"}


class PersonalView(QWidget):
    """Vista de gestión (listado + CRUD) del personal militar."""

    def __init__(self):
        super().__init__()
        self._resultados_actuales: list[PersonalMilitar] = []
        self._construir_interfaz()
        self.refrescar()

    # -------------------------------------------------------------
    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 22)
        layout.setSpacing(14)

        fila_encabezado = QHBoxLayout()
        titulo = QLabel("Gestión de Personal")
        titulo.setObjectName("tituloVista")
        self.label_total = QLabel("")
        self.label_total.setObjectName("subtituloVista")
        fila_encabezado.addWidget(titulo)
        fila_encabezado.addStretch()
        fila_encabezado.addWidget(self.label_total)
        layout.addLayout(fila_encabezado)

        # --- Barra de herramientas: búsqueda + filtro + nuevo ---
        barra = QHBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar por cédula, nombre o apellido...")
        self.input_busqueda.textChanged.connect(self._buscar)
        barra.addWidget(self.input_busqueda, stretch=2)

        self.combo_filtro_municipio = QComboBox()
        self.combo_filtro_municipio.addItem("Municipio: Todos", None)
        for municipio in geografia.listar_municipios(solo_adyacentes_coro=True):
            self.combo_filtro_municipio.addItem(municipio.nombre, municipio.id_municipio)
        self.combo_filtro_municipio.currentIndexChanged.connect(self._buscar)
        barra.addWidget(self.combo_filtro_municipio)

        boton_nuevo = QPushButton("+ Nuevo Registro")
        boton_nuevo.setObjectName("btnPrimario")
        boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)
        barra.addWidget(boton_nuevo)

        layout.addLayout(barra)

        # --- Tabla ---
        self.tabla = QTableWidget(0, len(COLUMNAS))
        self.tabla.setHorizontalHeaderLabels(COLUMNAS)
        self.tabla.horizontalHeader().setStretchLastSection(False)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        layout.addWidget(self.tabla)

    # -------------------------------------------------------------
    def refrescar(self) -> None:
        """Recarga combos y datos. Se invoca al navegar a esta vista."""
        self._buscar()

    def _buscar(self) -> None:
        texto = self.input_busqueda.text().strip()
        id_municipio = self.combo_filtro_municipio.currentData()

        self._resultados_actuales = buscar_personal(
            texto=texto or None, id_municipio=id_municipio
        )
        self._poblar_tabla(self._resultados_actuales)
        self.label_total.setText(f"{len(self._resultados_actuales)} registro(s) encontrado(s)")

    def _poblar_tabla(self, registros: list[PersonalMilitar]) -> None:
        self.tabla.setRowCount(0)
        for fila_idx, registro in enumerate(registros):
            self.tabla.insertRow(fila_idx)

            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(registro.cedula))
            self.tabla.setItem(
                fila_idx, 1, QTableWidgetItem(f"{registro.nombres} {registro.apellidos}")
            )
            self.tabla.setItem(fila_idx, 2, QTableWidgetItem(str(registro.edad)))
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(registro.genero))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(registro.municipio))
            self.tabla.setItem(fila_idx, 5, QTableWidgetItem(registro.estatus))
            self.tabla.setCellWidget(fila_idx, 6, self._crear_widget_acciones(registro))

    def _crear_widget_acciones(self, registro: PersonalMilitar) -> QWidget:
        """
        Crea el widget con los botones Editar/Eliminar para una fila de
        la tabla. Se usa setCellWidget (no setItem) porque necesitamos
        botones reales y clicables dentro de la celda, cada uno con su
        propio manejador conectado a este 'registro' específico.
        """
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        boton_editar = QPushButton("✏️")
        boton_editar.setToolTip("Editar registro")
        boton_editar.setFixedSize(28, 26)
        boton_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_editar.clicked.connect(lambda _checked=False, r=registro: self._abrir_dialogo_editar(r))

        boton_eliminar = QPushButton("🗑️")
        boton_eliminar.setToolTip("Eliminar registro")
        boton_eliminar.setFixedSize(28, 26)
        boton_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_eliminar.clicked.connect(lambda _checked=False, r=registro: self._confirmar_eliminar(r))

        layout.addWidget(boton_editar)
        layout.addWidget(boton_eliminar)
        layout.addStretch()
        return contenedor

    # -------------------------------------------------------------
    def _abrir_dialogo_nuevo(self) -> None:
        dialogo = PersonalFormDialog(self)
        if dialogo.exec():
            self._buscar()

    def _abrir_dialogo_editar(self, registro: PersonalMilitar) -> None:
        dialogo = PersonalFormDialog(self, registro_existente=registro)
        if dialogo.exec():
            self._buscar()

    def _confirmar_eliminar(self, registro: PersonalMilitar) -> None:
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de eliminar el registro de {registro.nombres} {registro.apellidos}?\n"
            "Esta acción no se puede deshacer.",
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                eliminar_personal(registro.id_personal)
                self._buscar()
            except RegistroNoEncontradoError:
                QMessageBox.warning(self, "Aviso", "El registro ya no existe.")
