"""
views/login_window.py
======================
Ventana de inicio de sesión. Es la primera pantalla que ve el usuario
al abrir la aplicación. Valida las credenciales contra la base de
datos (models/usuario.py) y, si son correctas, abre la ventana
principal (views/main_window.py) y cierra esta.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import config
from models.usuario import CredencialesInvalidasError, UsuarioInactivoError, autenticar
from utils import session
from views.estilos import QSS_GLOBAL


class LoginWindow(QWidget):
    """
    Ventana independiente de login. Al autenticar correctamente, crea
    la MainWindow y se cierra a sí misma.
    """

    def __init__(self):
        super().__init__()
        self._ventana_principal = None  # referencia para que no se destruya por el garbage collector
        self.setWindowTitle(config.NOMBRE_SISTEMA)
        self.setMinimumSize(900, 640)
        self.setStyleSheet(QSS_GLOBAL)
        self._construir_interfaz()

    # -------------------------------------------------------------
    # Construcción de la interfaz
    # -------------------------------------------------------------
    def _construir_interfaz(self) -> None:
        layout_general = QVBoxLayout(self)
        layout_general.setContentsMargins(0, 0, 0, 0)

        contenedor = QWidget()
        contenedor.setStyleSheet(
            f"background-color: {config.COLOR_PRIMARIO};"
        )
        layout_contenedor = QVBoxLayout(contenedor)
        layout_contenedor.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tarjeta = self._crear_tarjeta_login()
        layout_contenedor.addWidget(tarjeta, alignment=Qt.AlignmentFlag.AlignCenter)

        pie = QLabel(f"v{config.VERSION} — Acceso restringido al personal autorizado")
        pie.setStyleSheet("color: rgba(255,255,255,0.65); font-size: 11px;")
        pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_contenedor.addWidget(pie)

        layout_general.addWidget(contenedor)

    def _crear_tarjeta_login(self) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("loginCard")
        tarjeta.setFixedWidth(380)
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(6)

        escudo = QLabel("★")
        escudo.setObjectName("loginEscudo")
        escudo.setFixedSize(64, 64)
        escudo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(escudo, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)

        titulo = QLabel("SIGEM")
        titulo.setObjectName("loginTitulo")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        subtitulo = QLabel(
            f"{config.SUBTITULO_SISTEMA}\n{config.UNIDAD_MILITAR}"
        )
        subtitulo.setObjectName("loginSubtitulo")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)
        layout.addSpacing(18)

        self.input_usuario = QLineEdit()
        self.input_usuario.setObjectName("inputLogin")
        self.input_usuario.setPlaceholderText("Usuario")
        layout.addWidget(self.input_usuario)

        self.input_password = QLineEdit()
        self.input_password.setObjectName("inputLogin")
        self.input_password.setPlaceholderText("Contraseña")
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.returnPressed.connect(self._intentar_login)
        layout.addWidget(self.input_password)

        self.label_error = QLabel("")
        self.label_error.setObjectName("loginError")
        self.label_error.setWordWrap(True)
        self.label_error.setVisible(False)
        layout.addWidget(self.label_error)

        layout.addSpacing(4)

        boton_entrar = QPushButton("Iniciar sesión")
        boton_entrar.setObjectName("btnPrimario")
        boton_entrar.setMinimumHeight(40)
        boton_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
        boton_entrar.clicked.connect(self._intentar_login)
        layout.addWidget(boton_entrar)

        self.input_usuario.setFocus()
        return tarjeta

    # -------------------------------------------------------------
    # Lógica de autenticación
    # -------------------------------------------------------------
    def _intentar_login(self) -> None:
        usuario_texto = self.input_usuario.text().strip()
        password_texto = self.input_password.text()

        if not usuario_texto or not password_texto:
            self._mostrar_error("Debe ingresar usuario y contraseña.")
            return

        try:
            usuario = autenticar(usuario_texto, password_texto)
        except CredencialesInvalidasError:
            self._mostrar_error("Usuario o contraseña incorrectos.")
            self.input_password.clear()
            self.input_password.setFocus()
            return
        except UsuarioInactivoError as e:
            self._mostrar_error(str(e))
            return
        except Exception as e:
            self._mostrar_error(f"Error inesperado al iniciar sesión: {e}")
            return

        session.iniciar_sesion(usuario)
        self._abrir_ventana_principal()

    def _mostrar_error(self, mensaje: str) -> None:
        self.label_error.setText(mensaje)
        self.label_error.setVisible(True)

    def _abrir_ventana_principal(self) -> None:
        # Importación diferida para evitar import circular
        # (main_window podría necesitar referenciar login en el futuro,
        # p. ej. al cerrar sesión).
        from views.main_window import MainWindow

        self._ventana_principal = MainWindow()
        self._ventana_principal.show()
        self.close()
