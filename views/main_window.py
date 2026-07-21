"""
views/main_window.py
=====================
Ventana principal con fade-in al navegar entre vistas y botones de
navegación con efecto hover mejorado (vía QSS :checked ya definido
en estilos.py, reforzado con cursor de mano y feedback visual).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

import config
from utils import session
from views.animaciones import aplicar_fade_in
from views.estilos import QSS_GLOBAL


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._ventana_login = None
        self.setWindowTitle(config.NOMBRE_SISTEMA)
        self.setMinimumSize(1180, 720)
        self.setStyleSheet(QSS_GLOBAL)

        self._botones_nav: dict[str, QPushButton] = {}
        self._vistas: dict[str, QWidget] = {}

        self._construir_interfaz()
        self._cargar_vistas()
        self.navegar_a("dashboard")

    def _construir_interfaz(self) -> None:
        widget_central = QWidget()
        layout = QHBoxLayout(widget_central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._construir_sidebar())
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        self.setCentralWidget(widget_central)

    def _construir_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 18, 0, 14)
        layout.setSpacing(0)

        # Marca
        marca = QWidget()
        marca.setStyleSheet("background: transparent;")
        lm = QVBoxLayout(marca)
        lm.setContentsMargins(20, 0, 20, 18)
        nombre = QLabel("SIGEM")
        nombre.setObjectName("sidebarNombre")
        nombre.setStyleSheet("background: transparent; color: white; font-size: 14px; font-weight: 700;")
        unidad = QLabel(config.UNIDAD_MILITAR)
        unidad.setObjectName("sidebarUnidad")
        unidad.setStyleSheet("background: transparent; color: rgba(255,255,255,0.65); font-size: 10px;")
        unidad.setWordWrap(True)
        lm.addWidget(nombre)
        lm.addWidget(unidad)
        layout.addWidget(marca)

        linea = QFrame()
        linea.setFrameShape(QFrame.Shape.Box)
        linea.setFixedSize(220, 1)
        linea.setStyleSheet("background-color: rgba(255,255,255,0.12); border: none;")
        layout.addWidget(linea)
        layout.addSpacing(8)

        # Ítems de navegación
        items = [
            ("dashboard",    "▦  Dashboard"),
            ("personal",     "👤  Gestión de Personal"),
            ("registro",     "📝  Registrar Personal"),
            ("estadisticas", "📊  Estadísticas"),
            ("mapas",        "📍  Mapas Territoriales"),
            ("reportes",     "📄  Reportes"),
        ]
        for clave, etiqueta in items:
            boton = QPushButton(etiqueta)
            boton.setObjectName("navItem")
            boton.setCheckable(True)
            boton.setAutoExclusive(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(
                lambda _checked=False, c=clave: self.navegar_a(c)
            )
            layout.addWidget(boton)
            self._botones_nav[clave] = boton

        layout.addStretch()

        # Caja de usuario
        caja = QWidget()
        caja.setStyleSheet("background: transparent;")
        lu = QVBoxLayout(caja)
        lu.setContentsMargins(20, 12, 20, 0)
        usuario = session.usuario_actual()
        nombre_mostrado = usuario.nombre_completo if usuario else "Invitado"
        self.label_usuario = QLabel(f"Sesión: {nombre_mostrado}")
        self.label_usuario.setObjectName("sidebarUsuario")
        self.label_usuario.setStyleSheet("background: transparent; color: rgba(255,255,255,0.75); font-size: 11px;")
        lu.addWidget(self.label_usuario)
        btn_salir = QPushButton("Cerrar sesión")
        btn_salir.setObjectName("btnCerrarSesion")
        btn_salir.setStyleSheet("background: transparent; color: #D4AF37; border: none; text-align: left; font-size: 11px; padding: 4px 0;")
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.clicked.connect(self._cerrar_sesion)
        lu.addWidget(btn_salir)
        layout.addWidget(caja)

        return sidebar

    def _cargar_vistas(self) -> None:
        from views.dashboard_view    import DashboardView
        from views.personal_view     import PersonalView
        from views.registro_view     import RegistroView
        from views.estadisticas_view import EstadisticasView
        from views.mapa_view         import MapaView
        from views.reportes_view     import ReportesView

        for clave, Clase in [
            ("dashboard",    DashboardView),
            ("personal",     PersonalView),
            ("registro",     RegistroView),
            ("estadisticas", EstadisticasView),
            ("mapas",        MapaView),
            ("reportes",     ReportesView),
        ]:
            vista = Clase()
            self._vistas[clave] = vista
            self.stack.addWidget(vista)

    def navegar_a(self, clave: str) -> None:
        if clave not in self._vistas:
            return
        vista = self._vistas[clave]
        self.stack.setCurrentWidget(vista)
        if clave in self._botones_nav:
            self._botones_nav[clave].setChecked(True)

        # Fade-in de la vista recién seleccionada
        aplicar_fade_in(vista, duracion_ms=250)

        # Refrescar datos si la vista lo soporta
        if hasattr(vista, "refrescar"):
            vista.refrescar()

    def _cerrar_sesion(self) -> None:
        session.cerrar_sesion()
        from views.login_window import LoginWindow
        self._ventana_login = LoginWindow()
        self._ventana_login.show()
        self.close()
