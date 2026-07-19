"""
views/login_window.py
======================
Ventana de inicio de sesión con estética militar institucional
(rediseño basado en las referencias aprobadas por el usuario):

- Fondo oscuro con gradiente verde militar, generado programáticamente.
  Si existe resources/imagenes/fondo_login.jpg, se usa como imagen de
  fondo oscurecida (el usuario puede colocar ahí una foto institucional).
- Tarjeta central semitransparente con emblema dorado, campos con
  iconos, botón para mostrar/ocultar contraseña, y lema institucional.
- Estado de carga en el botón al autenticar (previene doble clic).
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
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

RUTA_IMAGEN_FONDO = os.path.join(config.RESOURCES_DIR, "imagenes", "fondo_login.jpg")

ORO = "#D4AF37"
VERDE_OSCURO = "#0D1F14"


class _FondoMilitar(QWidget):
    """Fondo con gradiente verde militar y soporte opcional de imagen."""

    def __init__(self):
        super().__init__()
        self._pixmap = None
        if os.path.isfile(RUTA_IMAGEN_FONDO):
            pm = QPixmap(RUTA_IMAGEN_FONDO)
            if not pm.isNull():
                self._pixmap = pm

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        # Gradiente base (siempre presente)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor("#0D1F14"))
        grad.setColorAt(0.5, QColor("#142B1D"))
        grad.setColorAt(1.0, QColor("#091510"))
        painter.fillRect(self.rect(), grad)

        # Imagen de fondo opcional, escalada y oscurecida
        if self._pixmap is not None:
            escalado = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - escalado.width()) // 2
            y = (self.height() - escalado.height()) // 2
            painter.setOpacity(0.30)   # oscurecida, como en las referencias
            painter.drawPixmap(x, y, escalado)
            painter.setOpacity(1.0)

        # Franjas decorativas doradas sutiles (esquinas)
        painter.setOpacity(0.12)
        painter.fillRect(0, self.height() - 4, self.width(), 4, QColor(ORO))
        painter.fillRect(0, 0, self.width(), 2, QColor(ORO))
        painter.setOpacity(1.0)
        painter.end()


class _CampoConIcono(QFrame):
    """Campo de entrada estilizado con icono a la izquierda
    (y opcionalmente botón de mostrar/ocultar para contraseñas)."""

    def __init__(self, icono: str, placeholder: str, es_password: bool = False):
        super().__init__()
        self.setStyleSheet(
            "QFrame { background-color: rgba(255,255,255,0.08); "
            "border: 1px solid rgba(255,255,255,0.18); border-radius: 8px; }"
            "QFrame:focus-within { border: 1px solid rgba(212,175,55,0.6); }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        lbl_icono = QLabel(icono)
        lbl_icono.setStyleSheet(
            "color: rgba(255,255,255,0.75); font-size: 15px; "
            "border: none; background: transparent;"
        )
        layout.addWidget(lbl_icono)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setStyleSheet(
            "QLineEdit { background: transparent; border: none; "
            "color: white; font-size: 13.5px; padding: 12px 4px; }"
            "QLineEdit::placeholder { color: rgba(255,255,255,0.45); }"
        )
        layout.addWidget(self.input, stretch=1)

        if es_password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
            self._btn_ojo = QPushButton("👁")
            self._btn_ojo.setFixedSize(30, 30)
            self._btn_ojo.setCursor(Qt.CursorShape.PointingHandCursor)
            self._btn_ojo.setStyleSheet(
                "QPushButton { background: transparent; border: none; "
                "color: rgba(255,255,255,0.6); font-size: 14px; }"
                "QPushButton:hover { color: white; }"
            )
            self._btn_ojo.clicked.connect(self._alternar_visibilidad)
            layout.addWidget(self._btn_ojo)

    def _alternar_visibilidad(self) -> None:
        if self.input.echoMode() == QLineEdit.EchoMode.Password:
            self.input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)


class LoginWindow(QWidget):
    """Ventana de login con estética militar institucional."""

    def __init__(self):
        super().__init__()
        self._ventana_principal = None
        self.setWindowTitle(config.NOMBRE_SISTEMA)
        self.setMinimumSize(960, 680)
        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        fondo = _FondoMilitar()
        layout_fondo = QVBoxLayout(fondo)
        layout_fondo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_fondo.addWidget(self._crear_tarjeta(),
                                alignment=Qt.AlignmentFlag.AlignCenter)
        raiz.addWidget(fondo)

    def _crear_tarjeta(self) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setFixedWidth(420)
        tarjeta.setStyleSheet(
            "QFrame { background-color: rgba(16, 26, 20, 0.92); "
            "border-radius: 14px; border: 1px solid rgba(212,175,55,0.30); }"
        )
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(40, 34, 40, 28)
        layout.setSpacing(8)

        # --- Emblema dorado ---
        emblema = QLabel("★")
        emblema.setFixedSize(76, 76)
        emblema.setAlignment(Qt.AlignmentFlag.AlignCenter)
        emblema.setStyleSheet(
            f"background-color: rgba(212,175,55,0.15); border: 2px solid {ORO}; "
            f"border-radius: 38px; color: {ORO}; font-size: 32px;"
        )
        layout.addWidget(emblema, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(10)

        # --- Títulos ---
        titulo = QLabel("SIGEM")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet(
            "color: white; font-size: 24px; font-weight: 800; "
            "letter-spacing: 3px; border: none; background: transparent;"
        )
        layout.addWidget(titulo)

        subtitulo = QLabel(config.UNIDAD_MILITAR)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitulo.setWordWrap(True)
        subtitulo.setStyleSheet(
            "color: rgba(255,255,255,0.80); font-size: 12px; "
            "border: none; background: transparent;"
        )
        layout.addWidget(subtitulo)

        pais = QLabel("REPÚBLICA BOLIVARIANA DE VENEZUELA")
        pais.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pais.setStyleSheet(
            f"color: {ORO}; font-size: 10px; letter-spacing: 1.5px; "
            "border: none; background: transparent;"
        )
        layout.addWidget(pais)
        layout.addSpacing(18)

        instruccion = QLabel("Ingrese sus credenciales para continuar")
        instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruccion.setStyleSheet(
            "color: rgba(255,255,255,0.55); font-size: 11.5px; "
            "border: none; background: transparent;"
        )
        layout.addWidget(instruccion)
        layout.addSpacing(10)

        # --- Campos ---
        self.campo_usuario = _CampoConIcono("👤", "Usuario")
        layout.addWidget(self.campo_usuario)
        layout.addSpacing(4)

        self.campo_password = _CampoConIcono("🔒", "Contraseña", es_password=True)
        self.campo_password.input.returnPressed.connect(self._intentar_login)
        layout.addWidget(self.campo_password)

        # --- Mensaje de error ---
        self.label_error = QLabel("")
        self.label_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_error.setWordWrap(True)
        self.label_error.setStyleSheet(
            "color: #E8A0A0; font-size: 11.5px; border: none; "
            "background: transparent;"
        )
        self.label_error.setVisible(False)
        layout.addWidget(self.label_error)
        layout.addSpacing(8)

        # --- Botón ---
        self.boton_entrar = QPushButton("INICIAR SESIÓN")
        self.boton_entrar.setMinimumHeight(44)
        self.boton_entrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_entrar.setStyleSheet(
            "QPushButton { background-color: #40916C; color: white; "
            "font-size: 13.5px; font-weight: 700; letter-spacing: 1.5px; "
            "border-radius: 8px; border: none; }"
            "QPushButton:hover { background-color: #52A57E; }"
            "QPushButton:pressed { background-color: #2D6A4F; }"
            "QPushButton:disabled { background-color: #3A5246; "
            "color: rgba(255,255,255,0.5); }"
        )
        self.boton_entrar.clicked.connect(self._intentar_login)
        layout.addWidget(self.boton_entrar)
        layout.addSpacing(16)

        # --- Separador + lema ---
        separador = QFrame()
        separador.setFixedHeight(1)
        separador.setStyleSheet(
            "background-color: rgba(255,255,255,0.15); border: none;"
        )
        layout.addWidget(separador)
        layout.addSpacing(10)

        lema = QLabel("DISCIPLINA  •  LEALTAD  •  HONOR")
        lema.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lema.setStyleSheet(
            f"color: {ORO}; font-size: 10.5px; letter-spacing: 2px; "
            "border: none; background: transparent;"
        )
        layout.addWidget(lema)

        version = QLabel(f"v{config.VERSION} — Acceso restringido al personal autorizado")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(
            "color: rgba(255,255,255,0.35); font-size: 9.5px; "
            "border: none; background: transparent;"
        )
        layout.addWidget(version)

        self.campo_usuario.input.setFocus()
        return tarjeta

    # -----------------------------------------------------------------
    def _intentar_login(self) -> None:
        usuario_texto = self.campo_usuario.input.text().strip()
        password_texto = self.campo_password.input.text()

        if not usuario_texto or not password_texto:
            self._mostrar_error("Debe ingresar usuario y contraseña.")
            return

        # Estado de carga: previene doble clic y avisa al usuario
        self.boton_entrar.setEnabled(False)
        self.boton_entrar.setText("VERIFICANDO...")
        QApplication.processEvents()

        try:
            usuario = autenticar(usuario_texto, password_texto)
        except CredencialesInvalidasError:
            self._restaurar_boton()
            self._mostrar_error("Usuario o contraseña incorrectos.")
            self.campo_password.input.clear()
            self.campo_password.input.setFocus()
            return
        except UsuarioInactivoError as e:
            self._restaurar_boton()
            self._mostrar_error(str(e))
            return
        except Exception as e:
            self._restaurar_boton()
            self._mostrar_error(f"Error inesperado: {e}")
            return

        session.iniciar_sesion(usuario)
        self.boton_entrar.setText("CARGANDO SISTEMA...")
        QApplication.processEvents()
        self._abrir_ventana_principal()

    def _restaurar_boton(self) -> None:
        self.boton_entrar.setEnabled(True)
        self.boton_entrar.setText("INICIAR SESIÓN")

    def _mostrar_error(self, mensaje: str) -> None:
        self.label_error.setText(mensaje)
        self.label_error.setVisible(True)

    def _abrir_ventana_principal(self) -> None:
        from views.main_window import MainWindow
        self._ventana_principal = MainWindow()
        self._ventana_principal.show()
        self.close()
