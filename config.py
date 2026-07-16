"""
config.py
=========
Configuración global del sistema SIGEM.
Centraliza rutas de archivos, constantes y parámetros para evitar
valores "hardcodeados" dispersos por el resto del código.
"""

import os
import sys

# ---------------------------------------------------------------------
# Rutas base del proyecto
# ---------------------------------------------------------------------
# BASE_DIR funciona tanto en modo desarrollo (python main.py) como
# empaquetado con PyInstaller (sys._MEIPASS / ejecutable .exe).
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_DIR = os.path.join(BASE_DIR, "database")
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
GEODATA_DIR = os.path.join(RESOURCES_DIR, "geodata")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

DB_PATH = os.path.join(DATABASE_DIR, "sigem.db")
SCHEMA_PATH = os.path.join(DATABASE_DIR, "schema.sql")
GEOJSON_FALCON_PATH = os.path.join(GEODATA_DIR, "falcon_municipios.geojson")

# Crear carpetas necesarias si no existen (no falla si ya existen)
for _dir in (DATABASE_DIR, RESOURCES_DIR, GEODATA_DIR, REPORTS_DIR, LOGS_DIR):
    os.makedirs(_dir, exist_ok=True)

# ---------------------------------------------------------------------
# Información institucional (para encabezados de reportes y la app)
# ---------------------------------------------------------------------
NOMBRE_SISTEMA = "SIGEM - Sistema de Análisis Estadístico y Territorial"
SUBTITULO_SISTEMA = "Participación y Reclutamiento del Servicio Militar - Coro, Edo. Falcón"
UNIDAD_MILITAR = "Batallón de Infantería Mecanizada \"Cnel. Atanasio Girardot\""
VERSION = "1.0.0"

# ---------------------------------------------------------------------
# Parámetros de la aplicación
# ---------------------------------------------------------------------
COLOR_PRIMARIO = "#1B4332"      # Verde militar oscuro
COLOR_SECUNDARIO = "#40916C"    # Verde militar medio
COLOR_ACENTO = "#D4AF37"        # Dorado (insignias)
COLOR_FONDO = "#F5F5F0"

# Centro geográfico aproximado de Coro, Falcón (para centrar mapas)
CORO_LAT = 11.4046
CORO_LON = -69.6803
ZOOM_INICIAL_MAPA = 9

# Sesión
SESSION_TIMEOUT_MINUTOS = 60

# Intentos de login antes de bloqueo temporal
MAX_INTENTOS_LOGIN = 5
