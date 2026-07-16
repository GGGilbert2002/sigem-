"""
database/migrations.py
=======================
Sistema simple de migraciones para evolucionar el esquema de la base
de datos SIN perder los datos ya existentes.

Cada migración se identifica con un número de versión. La tabla
'schema_version' guarda cuál fue la última migración aplicada, así
que cada migración se ejecuta una sola vez por base de datos, sin
importar cuántas veces se llame a aplicar_migraciones().
"""

import logging

from database.connection import get_connection

logger = logging.getLogger("sigem.migrations")


def _version_actual(conn) -> int:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL DEFAULT 0)"
    )
    row = conn.execute("SELECT version FROM schema_version").fetchone()
    if row is None:
        conn.execute("INSERT INTO schema_version (version) VALUES (0)")
        return 0
    return row["version"]


def _set_version(conn, version: int) -> None:
    conn.execute("UPDATE schema_version SET version = ?", (version,))


def _columna_existe(conn, tabla: str, columna: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({tabla})")
    return any(row["name"] == columna for row in cur.fetchall())


# ---------------------------------------------------------------------
# Migración 1: agregar columnas telefono y direccion a personal_militar
# ---------------------------------------------------------------------
def _migracion_1_telefono_direccion(conn) -> None:
    if not _columna_existe(conn, "personal_militar", "telefono"):
        conn.execute("ALTER TABLE personal_militar ADD COLUMN telefono TEXT")
        logger.info("Columna 'telefono' agregada a personal_militar.")
    if not _columna_existe(conn, "personal_militar", "direccion"):
        conn.execute("ALTER TABLE personal_militar ADD COLUMN direccion TEXT")
        logger.info("Columna 'direccion' agregada a personal_militar.")


# Lista ordenada de migraciones: (numero_version, funcion)
MIGRACIONES = [
    (1, _migracion_1_telefono_direccion),
]


def aplicar_migraciones() -> None:
    conn = get_connection()
    try:
        version = _version_actual(conn)
        for numero, funcion in MIGRACIONES:
            if numero > version:
                logger.info("Aplicando migración %d...", numero)
                funcion(conn)
                _set_version(conn, numero)
                conn.commit()
        logger.info("Base de datos al día (versión %d).", MIGRACIONES[-1][0] if MIGRACIONES else 0)
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    aplicar_migraciones()
    print("✅ Migraciones aplicadas correctamente.")
