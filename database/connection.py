"""
database/connection.py
=======================
Gestión centralizada de la conexión a la base de datos SQLite.

Provee:
- get_connection(): conexión configurada (foreign_keys, row_factory)
- inicializar_base_datos(): crea el esquema si no existe
- db_session(): context manager para manejar commits/rollbacks de forma segura
"""

import sqlite3
import logging
from contextlib import contextmanager

import config

logger = logging.getLogger("sigem.database")


def get_connection() -> sqlite3.Connection:
    """
    Crea y retorna una nueva conexión a la base de datos SQLite.

    - row_factory = sqlite3.Row permite acceder a las columnas por nombre
      (ej: fila["nombre"]) en lugar de solo por índice, lo que hace el
      código de los modelos mucho más legible.
    - Se activan las foreign keys porque SQLite las desactiva por defecto.
    """
    conn = sqlite3.connect(config.DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_session():
    """
    Context manager para operaciones de escritura seguras:

        with db_session() as conn:
            conn.execute("INSERT INTO ...", (...))

    Si todo sale bien, se hace commit automáticamente.
    Si ocurre una excepción, se hace rollback y se vuelve a lanzar
    la excepción para que la capa superior (controlador/vista) decida
    cómo informar el error al usuario.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Error en transacción de base de datos; se hizo rollback.")
        raise
    finally:
        conn.close()


def inicializar_base_datos() -> None:
    """
    Crea las tablas y vistas del esquema si no existen todavía, y aplica
    cualquier migración pendiente. Es seguro llamarla cada vez que
    arranca la aplicación: usa 'CREATE TABLE IF NOT EXISTS' y las
    migraciones son idempotentes, por lo que no destruye datos existentes.
    """
    with open(config.SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection()
    try:
        conn.executescript(schema_sql)
        conn.commit()
        logger.info("Base de datos inicializada correctamente en %s", config.DB_PATH)
    finally:
        conn.close()

    # Importación diferida para evitar import circular
    # (migrations.py importa get_connection de este mismo módulo).
    from database.migrations import aplicar_migraciones
    aplicar_migraciones()


def existe_base_datos_poblada() -> bool:
    """
    Indica si ya hay datos cargados (al menos un municipio registrado).
    Útil para decidir si se debe ejecutar el seed de datos iniciales.
    """
    conn = get_connection()
    try:
        cur = conn.execute("SELECT COUNT(*) AS total FROM municipios;")
        return cur.fetchone()["total"] > 0
    except sqlite3.OperationalError:
        # La tabla aún no existe -> base de datos no inicializada
        return False
    finally:
        conn.close()
