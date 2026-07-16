"""
main.py
=======
Punto de entrada de la aplicación SIGEM.

Ejecutar con:
    python main.py

Flujo de arranque:
1. Inicializa la base de datos (crea el esquema si no existe, aplica
   migraciones pendientes).
2. Si es la primera vez que se ejecuta el sistema (no hay usuarios ni
   datos), carga los datos semilla (municipios reales + datos
   ficticios de personal) y crea el usuario administrador por defecto.
3. Abre la ventana de login.
"""

import os

# IMPORTANTE: estas variables de entorno deben configurarse ANTES de
# importar cualquier módulo de PyQt6 (incluyendo QtCore/QtWidgets),
# porque QtWebEngine lee esta configuración al cargar su motor interno
# de Chromium. Se usan para forzar un modo de renderizado por software,
# ya que en algunos equipos Windows (especialmente con drivers de video
# antiguos, máquinas virtuales, o ciertas tarjetas integradas) la
# aceleración por GPU dentro de QtWebEngine causa que la página cargue
# en blanco (sin teselas de mapa) aunque el HTML sea válido — el mismo
# archivo sí se ve bien en un navegador normal porque ese usa su propia
# configuración de GPU, independiente de la de la aplicación.
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu --disable-gpu-compositing --disable-gpu-sandbox "
    "--no-sandbox --disable-dev-shm-usage",
)

import logging
import sys

from PyQt6.QtWidgets import QApplication

import config


def _configurar_logging() -> None:
    import os

    ruta_log = os.path.join(config.LOGS_DIR, "sigem.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(ruta_log, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def _preparar_datos_iniciales() -> None:
    """
    Inicializa el esquema de base de datos y, si es la primera
    ejecución del sistema, carga los datos semilla (municipios reales,
    catálogos, datos ficticios de personal) y crea el usuario
    administrador por defecto.
    """
    from database.connection import inicializar_base_datos
    from database.seed_data import ejecutar_seed
    from models.usuario import crear_usuario, existe_algun_usuario

    inicializar_base_datos()
    ejecutar_seed(incluir_datos_ficticios=True, cantidad_ficticios=250)

    if not existe_algun_usuario():
        crear_usuario("admin", "Administrador del Sistema", "admin123")
        logging.getLogger("sigem.main").info(
            "Usuario administrador creado por defecto (usuario: admin / contraseña: admin123)."
        )


def main() -> None:
    _configurar_logging()
    logger = logging.getLogger("sigem.main")
    logger.info("Iniciando SIGEM v%s", config.VERSION)

    try:
        _preparar_datos_iniciales()
    except Exception:
        logger.exception("Error crítico al preparar los datos iniciales.")
        raise

    # IMPORTANTE: este atributo debe configurarse ANTES de crear el
    # QApplication. Es requerido por QtWebEngine (usado en la pantalla
    # de Mapas Territoriales para mostrar los mapas de Folium). Si no
    # se configura aquí, QtWebEngine muestra advertencias en consola
    # y puede comportarse de forma inestable en algunos sistemas.
    from PyQt6.QtCore import Qt, QCoreApplication

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    app.setStyleSheet("")  # los estilos se aplican por ventana (ver views/estilos.py)

    from views.login_window import LoginWindow

    ventana_login = LoginWindow()
    ventana_login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
