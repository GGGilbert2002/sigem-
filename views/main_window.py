"""
views/main_window.py
=====================
Ventana principal de la aplicación. Contiene:
- El sidebar de navegación (igual al wireframe aprobado): Dashboard,
  Gestión de Personal, Estadísticas, Mapas Territoriales, Reportes.
- Un QStackedWidget que muestra la vista activa según el botón
  seleccionado en el sidebar.
- Información de la sesión activa y botón de cerrar sesión.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import config
from utils import session
from views.estilos import QSS_GLOBAL


class MainWindow(QMainWindow):
    """Ventana principal con navegación lateral, según el wireframe aprobado."""

    def __init__(self):
        super().__init__()
        self._ventana_login = None  # referencia al reabrir login tras cerrar sesión
        self.setWindowTitle(config.NOMBRE_SISTEMA)
        self.setMinimumSize(1180, 720)
        self.setStyleSheet(QSS_GLOBAL)

        self._botones_nav: dict[str, QPushButton] = {}
        self._vistas: dict[str, QWidget] = {}

        self._construir_interfaz()
        self._cargar_vistas()
        self.navegar_a("dashboard")

    # -------------------------------------------------------------
    # Construcción de la interfaz base (sidebar + área de contenido)
    # -------------------------------------------------------------
    def _construir_interfaz(self) -> None:
        widget_central = QWidget()
        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        layout_principal.addWidget(self._construir_sidebar())

        self.stack = QStackedWidget()
        layout_principal.addWidget(self.stack)

        self.setCentralWidget(widget_central)

    def _construir_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 18, 0, 14)
        layout.setSpacing(0)

        # --- Marca / encabezado del sidebar ---
        marca = QWidget()
        layout_marca = QVBoxLayout(marca)
        layout_marca.setContentsMargins(20, 0, 20, 18)
        nombre = QLabel("SIGEM")
        nombre.setObjectName("sidebarNombre")
        unidad = QLabel(config.UNIDAD_MILITAR)
        unidad.setObjectName("sidebarUnidad")
        unidad.setWordWrap(True)
        layout_marca.addWidget(nombre)
        layout_marca.addWidget(unidad)
        layout.addWidget(marca)

        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.Box)
        linea.setFixedSize(220, 1)
        linea.setStyleSheet("background-color: rgba(255,255,255,0.12); border: none;")
        layout.addWidget(linea)
        layout.addSpacing(8)

        # --- Botones de navegación ---
        items_navegacion = [
            ("dashboard", "▦  Dashboard"),
            ("personal", "👤  Gestión de Personal"),
            ("estadisticas", "📊  Estadísticas"),
            ("mapas", "📍  Mapas Territoriales"),
            ("reportes", "📄  Reportes"),
        ]
        for clave, etiqueta in items_navegacion:
            boton = QPushButton(etiqueta)
            boton.setObjectName("navItem")
            boton.setCheckable(True)
            boton.setAutoExclusive(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(lambda _checked=False, c=clave: self.navegar_a(c))
            layout.addWidget(boton)
            self._botones_nav[clave] = boton

        layout.addStretch()

        # --- Caja de sesión / usuario actual ---
        caja_usuario = QWidget()
        layout_usuario = QVBoxLayout(caja_usuario)
        layout_usuario.setContentsMargins(20, 12, 20, 0)

        usuario_actual = session.usuario_actual()
        nombre_mostrado = usuario_actual.nombre_completo if usuario_actual else "Invitado"
        self.label_usuario = QLabel(f"Sesión: {nombre_mostrado}")
        self.label_usuario.setObjectName("sidebarUsuario")
        layout_usuario.addWidget(self.label_usuario)

        boton_salir = QPushButton("Cerrar sesión")
        boton_salir.setObjectName("btnCerrarSesion")
        boton_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_salir.clicked.connect(self._cerrar_sesion)
        layout_usuario.addWidget(boton_salir)

        layout.addWidget(caja_usuario)

        return sidebar

    # -------------------------------------------------------------
    # Carga de las vistas (pantallas) dentro del stack
    # -------------------------------------------------------------
    def _cargar_vistas(self) -> None:
        # Importaciones diferidas: cada vista importa controladores/modelos
        # pesados (pandas, matplotlib, folium), y solo queremos cargarlos
        # cuando la ventana principal realmente se construye (después del
        # login), no al importar este módulo.
        from views.dashboard_view import DashboardView
        from views.personal_view import PersonalView
        from views.estadisticas_view import EstadisticasView
        from views.mapa_view import MapaView
        from views.reportes_view import ReportesView

        mapeo_vistas = {
            "dashboard": DashboardView,
            "personal": PersonalView,
            "estadisticas": EstadisticasView,
            "mapas": MapaView,
            "reportes": ReportesView,
        }
        for clave, clase_vista in mapeo_vistas.items():
            vista = clase_vista()
            self._vistas[clave] = vista
            self.stack.addWidget(vista)

    # -------------------------------------------------------------
    # Navegación entre vistas
    # -------------------------------------------------------------
    def navegar_a(self, clave_vista: str) -> None:
        if clave_vista not in self._vistas:
            return
        self.stack.setCurrentWidget(self._vistas[clave_vista])
        if clave_vista in self._botones_nav:
            self._botones_nav[clave_vista].setChecked(True)

        # Si la vista tiene un método de refresco de datos, se invoca
        # cada vez que el usuario navega a ella, para que muestre
        # siempre la información más reciente (ej.: tras crear un
        # nuevo registro de personal, el dashboard debe reflejarlo).
        vista_actual = self._vistas[clave_vista]
        if hasattr(vista_actual, "refrescar"):
            vista_actual.refrescar()

    # -------------------------------------------------------------
    # Cierre de sesión
    # -------------------------------------------------------------
    def _cerrar_sesion(self) -> None:
        session.cerrar_sesion()
        from views.login_window import LoginWindow

        self._ventana_login = LoginWindow()
        self._ventana_login.show()
        self.close()
