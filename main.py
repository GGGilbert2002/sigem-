"""
main.py
=======
Punto de entrada de la aplicación SIGEM.

Ejecutar con:
    py -3.14 main.py

Flujo de arranque:
1. Configura el sistema de logging estructurado (JSON en archivo,
   legible en consola) — requerimiento Avance #6 Trazabilidad.
2. Inicializa la base de datos (crea el esquema si no existe).
3. Si es la primera ejecución, carga los datos semilla y crea el
   usuario administrador por defecto (admin/admin123).
4. Abre la ventana de login.
"""

import os
import sys

# IMPORTANTE: configurar ANTES de importar PyQt6 (requerido por QtWebEngine)
os.environ.setdefault(
    "QTWEBENGINE_CHROMIUM_FLAGS",
    "--disable-gpu --disable-gpu-compositing --disable-gpu-sandbox "
    "--no-sandbox --disable-dev-shm-usage",
)

from utils.logger import configurar_logging, get_logger

# Configurar logging al inicio, antes que cualquier otro módulo
configurar_logging()
logger = get_logger("sigem.main")

import config


def _preparar_datos_iniciales() -> None:
    """
    Inicializa el esquema de BD y carga los datos semilla en la
    primera ejecución. Operación idempotente (segura de repetir).
    """
    from database.connection import inicializar_base_datos
    from database.seed_data import ejecutar_seed
    from models.usuario import crear_usuario, existe_algun_usuario

    inicializar_base_datos()
    ejecutar_seed(incluir_datos_ficticios=True, cantidad_ficticios=250)

    if not existe_algun_usuario():
        crear_usuario("admin", "Administrador del Sistema", "admin123")
        logger.info(
            "Usuario administrador creado por defecto",
            extra={"usuario": "admin", "accion": "primer_arranque"}
        )


def main() -> None:
    logger.info(
        "Iniciando SIGEM",
        extra={"version": config.VERSION, "entorno": os.environ.get("SIGEM_ENV", "development")}
    )

    try:
        _preparar_datos_iniciales()
    except Exception:
        logger.exception("Error critico al preparar los datos iniciales")
        sys.exit(1)

    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv if sys.argv else ["sigem"])

    from views.login_window import LoginWindow
    ventana_login = LoginWindow()
    ventana_login.show()

    logger.info("Interfaz grafica iniciada correctamente")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
