"""
database/seed_data.py
======================
Carga de datos iniciales (seed) para el sistema SIGEM:

1. Los 25 municipios reales del estado Falcón, Venezuela (fuente:
   división político-territorial oficial; coordenadas aproximadas de
   cada capital municipal para ubicación en el mapa).
2. Parroquias de los municipios adyacentes a Coro (alcance del estudio:
   Miranda, Colina, Falcón, Zamora, Carirubana, Los Taques) según el
   Capítulo I (Delimitación Geográfica) del proyecto.
3. Catálogos: niveles educativos, grados militares, estatus de
   participación.
4. Datos FICTICIOS de personal militar para pruebas del sistema,
   mientras se obtienen los datos reales del batallón.

Este script es IDEMPOTENTE: puede ejecutarse varias veces sin duplicar
información (usa INSERT OR IGNORE / verifica existencia previa).
"""

import logging
import random
from datetime import date, timedelta

from database.connection import db_session, get_connection

logger = logging.getLogger("sigem.seed")

# ---------------------------------------------------------------------
# 1. Municipios reales del estado Falcón (25 municipios)
#    (nombre, capital, latitud, longitud, es_adyacente_a_coro)
#    Coordenadas aproximadas de la capital de cada municipio.
# ---------------------------------------------------------------------
MUNICIPIOS_FALCON = [
    ("Acosta", "San Juan de los Cayos", 11.1500, -68.6333, 0),
    ("Bolívar", "San Luis", 11.1167, -69.6833, 0),
    ("Buchivacoa", "Capatárida", 11.1833, -70.3333, 0),
    ("Cacique Manaure", "Yaracal", 11.1667, -69.6167, 0),
    ("Carirubana", "Punto Fijo", 11.6997, -70.2026, 1),
    ("Colina", "La Vela de Coro", 11.4667, -69.5833, 1),
    ("Dabajuro", "Dabajuro", 11.0167, -70.5667, 0),
    ("Democracia", "Pedregal", 11.0167, -70.1167, 0),
    ("Falcón", "Pueblo Nuevo", 12.0500, -70.0667, 1),
    ("Federación", "Churuguara", 10.4667, -69.5667, 0),
    ("Jacura", "Jacura", 10.8333, -69.1167, 0),
    ("José Laurencio Silva", "Tucacas", 10.8000, -68.3167, 0),
    ("Los Taques", "Santa Cruz de Los Taques", 11.7667, -70.2167, 1),
    ("Mauroa", "Mene de Mauroa", 10.9667, -70.6167, 0),
    ("Miranda", "Santa Ana de Coro", 11.4046, -69.6803, 1),
    ("Monseñor Iturriza", "Chichiriviche", 10.9500, -68.2667, 0),
    ("Palmasola", "Palmasola", 10.4833, -69.0333, 0),
    ("Petit", "Cabure", 11.1333, -69.5333, 0),
    ("Píritu", "Píritu", 11.1667, -69.3667, 0),
    ("San Francisco", "Mirimire", 11.0667, -68.5167, 0),
    ("Sucre", "La Cruz de Taratara", 10.9333, -69.4167, 0),
    ("Tocópero", "Tocópero", 11.3667, -69.7833, 1),
    ("Unión", "Santa Cruz de Bucaral", 10.6167, -69.7667, 0),
    ("Urumaco", "Urumaco", 11.1500, -70.5167, 0),
    ("Zamora", "Puerto Cumarebo", 11.4833, -69.3500, 1),
]

# ---------------------------------------------------------------------
# 2. Parroquias de municipios adyacentes a Coro
#    (nombre_parroquia, nombre_municipio_padre, lat, lon)
#    Foco principal del estudio según Capítulo I.
# ---------------------------------------------------------------------
PARROQUIAS_ADYACENTES = [
    # Municipio Miranda (donde está Coro)
    ("Santa Ana de Coro (Centro)", "Miranda", 11.4046, -69.6803),
    ("San Antonio", "Miranda", 11.4100, -69.6700),
    ("San Gabriel", "Miranda", 11.3950, -69.6750),
    ("Manaure (Coro)", "Miranda", 11.4200, -69.6600),
    ("Curimagua", "Miranda", 11.1167, -69.5667),
    ("Guaibacoa", "Miranda", 11.3667, -69.5500),
    ("Mariano Roscio (La Vela vía Miranda)", "Miranda", 11.4300, -69.6300),
    # Municipio Colina
    ("La Vela de Coro", "Colina", 11.4667, -69.5833),
    ("La Pastora", "Colina", 11.4500, -69.6000),
    ("Macoruca", "Colina", 11.3000, -69.6000),
    # Municipio Falcón (Paraguaná)
    ("Pueblo Nuevo", "Falcón", 12.0500, -70.0667),
    ("Capadare", "Falcón", 11.9667, -70.0167),
    ("Adaure", "Falcón", 11.9000, -69.9667),
    # Municipio Carirubana (Paraguaná)
    ("Punto Fijo", "Carirubana", 11.6997, -70.2026),
    ("Carirubana", "Carirubana", 11.6833, -70.2167),
    ("Punta Cardón", "Carirubana", 11.6333, -70.2167),
    ("Norte de Punto Fijo", "Carirubana", 11.7333, -70.2167),
    # Municipio Los Taques
    ("Santa Cruz de Los Taques", "Los Taques", 11.7667, -70.2167),
    ("Judibana", "Los Taques", 11.7500, -70.1833),
    # Municipio Tocópero
    ("Tocópero", "Tocópero", 11.3667, -69.7833),
    # Municipio Zamora
    ("Puerto Cumarebo", "Zamora", 11.4833, -69.3500),
    ("La Soledad", "Zamora", 11.4167, -69.3167),
    ("Tocuyo de la Costa", "Zamora", 11.0833, -69.5833),
]

# ---------------------------------------------------------------------
# 3. Catálogos
# ---------------------------------------------------------------------
NIVELES_EDUCATIVOS = [
    "Sin estudios",
    "Educación Primaria",
    "Educación Media (Bachillerato)",
    "Técnico Medio",
    "Técnico Superior Universitario",
    "Universitario (Pregrado)",
    "Postgrado",
]

GRADOS_MILITARES = [
    # (nombre, categoria)
    ("Conscripto", "Conscripto/Alistado"),
    ("Soldado", "Tropa Profesional"),
    ("Cabo Segundo", "Tropa Profesional"),
    ("Cabo Primero", "Tropa Profesional"),
    ("Sargento Segundo", "Sub-Oficial"),
    ("Sargento Primero", "Sub-Oficial"),
    ("Sargento Mayor", "Sub-Oficial"),
    ("Sub-Teniente", "Oficial"),
    ("Teniente", "Oficial"),
    ("Capitán", "Oficial"),
]

ESTATUS_PARTICIPACION = [
    "Registrado",
    "Convocado",
    "Alistado",
    "Incorporado",
    "Diferido",
    "Rechazado (No apto)",
    "Desertor",
]

NOMBRES_M = ["José", "Luis", "Carlos", "Juan", "Miguel", "Pedro", "Ángel", "Rafael",
             "Francisco", "Daniel", "Alejandro", "Gabriel", "Ricardo", "Eduardo", "Manuel"]
NOMBRES_F = ["María", "Carmen", "Ana", "Rosa", "Luisa", "Andrea", "Daniela", "Valentina",
             "Gabriela", "Yolanda", "Marisol", "Yusneidy", "Mariangel", "Génesis"]
APELLIDOS = ["González", "Rodríguez", "Pérez", "Sánchez", "Romero", "Torres", "Díaz",
             "Ramírez", "Flores", "Acosta", "Medina", "Castillo", "Vargas", "Rojas",
             "Marín", "Chirinos", "Petit", "Colina", "Reyes", "Mavárez"]
SECTORES_DIRECCION = ["Sector Curazaito", "Av. Los Médanos", "Sector La Floresta",
                       "Calle Falcón", "Sector El Carmen", "Av. Josefa Camejo",
                       "Sector La Guajira", "Calle Zamora", "Urb. Cruz Verde",
                       "Sector Las Velitas", "Av. Independencia", "Sector Los Olivos"]


def _poblar_municipios(conn):
    cur = conn.execute("SELECT COUNT(*) AS c FROM municipios;")
    if cur.fetchone()["c"] > 0:
        logger.info("Municipios ya cargados, se omite este paso.")
        return
    conn.executemany(
        """INSERT INTO municipios (nombre, capital, latitud, longitud, es_adyacente_coro)
           VALUES (?, ?, ?, ?, ?)""",
        MUNICIPIOS_FALCON,
    )
    logger.info("Se insertaron %d municipios.", len(MUNICIPIOS_FALCON))


def _poblar_parroquias(conn):
    cur = conn.execute("SELECT COUNT(*) AS c FROM parroquias;")
    if cur.fetchone()["c"] > 0:
        logger.info("Parroquias ya cargadas, se omite este paso.")
        return

    municipios_id = {
        row["nombre"]: row["id_municipio"]
        for row in conn.execute("SELECT id_municipio, nombre FROM municipios;")
    }

    registros = []
    for nombre_parroquia, nombre_municipio, lat, lon in PARROQUIAS_ADYACENTES:
        id_municipio = municipios_id.get(nombre_municipio)
        if id_municipio is None:
            logger.warning("Municipio '%s' no encontrado; se omite parroquia '%s'.",
                            nombre_municipio, nombre_parroquia)
            continue
        registros.append((nombre_parroquia, id_municipio, lat, lon))

    conn.executemany(
        """INSERT INTO parroquias (nombre, id_municipio, latitud, longitud)
           VALUES (?, ?, ?, ?)""",
        registros,
    )
    logger.info("Se insertaron %d parroquias.", len(registros))


def _poblar_catalogos(conn):
    cur = conn.execute("SELECT COUNT(*) AS c FROM niveles_educativos;")
    if cur.fetchone()["c"] == 0:
        conn.executemany(
            "INSERT INTO niveles_educativos (descripcion) VALUES (?)",
            [(n,) for n in NIVELES_EDUCATIVOS],
        )
        logger.info("Se insertaron %d niveles educativos.", len(NIVELES_EDUCATIVOS))

    cur = conn.execute("SELECT COUNT(*) AS c FROM grados_militares;")
    if cur.fetchone()["c"] == 0:
        conn.executemany(
            "INSERT INTO grados_militares (nombre, categoria) VALUES (?, ?)",
            GRADOS_MILITARES,
        )
        logger.info("Se insertaron %d grados militares.", len(GRADOS_MILITARES))

    cur = conn.execute("SELECT COUNT(*) AS c FROM estatus_participacion;")
    if cur.fetchone()["c"] == 0:
        conn.executemany(
            "INSERT INTO estatus_participacion (descripcion) VALUES (?)",
            [(e,) for e in ESTATUS_PARTICIPACION],
        )
        logger.info("Se insertaron %d estatus de participación.", len(ESTATUS_PARTICIPACION))


def _generar_cedula_unica(cedulas_usadas: set) -> str:
    while True:
        cedula = str(random.randint(5_000_000, 32_000_000))
        if cedula not in cedulas_usadas:
            cedulas_usadas.add(cedula)
            return cedula


def poblar_datos_ficticios_personal(conn, cantidad: int = 250) -> int:
    """
    Genera registros FICTICIOS de personal para que el usuario pueda
    probar estadísticas, mapas y reportes mientras consigue los datos
    reales del batallón. Devuelve la cantidad de registros insertados.
    """
    cur = conn.execute("SELECT COUNT(*) AS c FROM personal_militar;")
    if cur.fetchone()["c"] > 0:
        logger.info("Ya existen registros de personal; no se generan datos ficticios.")
        return 0

    municipios = conn.execute(
        "SELECT id_municipio FROM municipios WHERE es_adyacente_coro = 1;"
    ).fetchall()
    parroquias_por_municipio = {}
    for m in municipios:
        parroquias_por_municipio[m["id_municipio"]] = [
            r["id_parroquia"] for r in conn.execute(
                "SELECT id_parroquia FROM parroquias WHERE id_municipio = ?",
                (m["id_municipio"],),
            )
        ]

    niveles = [r["id_nivel_educativo"] for r in conn.execute("SELECT id_nivel_educativo FROM niveles_educativos;")]
    grados = [r["id_grado"] for r in conn.execute("SELECT id_grado FROM grados_militares;")]
    estatus = [r["id_estatus"] for r in conn.execute("SELECT id_estatus FROM estatus_participacion;")]

    cedulas_usadas = set()
    registros = []
    hoy = date.today()

    for _ in range(cantidad):
        genero = random.choice(["Masculino", "Femenino"])
        nombres = random.choice(NOMBRES_M if genero == "Masculino" else NOMBRES_F)
        apellidos = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"

        edad = random.randint(18, 35)
        fecha_nacimiento = (hoy - timedelta(days=edad * 365 + random.randint(0, 364))).isoformat()

        id_municipio = random.choice(municipios)["id_municipio"]
        parroquias_disp = parroquias_por_municipio.get(id_municipio, [])
        id_parroquia = random.choice(parroquias_disp) if parroquias_disp else None

        dias_desde_registro = random.randint(0, 365 * 2)  # últimos 2 años
        fecha_registro = (hoy - timedelta(days=dias_desde_registro)).isoformat()

        telefono = f"04{random.choice(['12','14','16','24','26'])}-{random.randint(1000000,9999999)}"
        direccion = f"{random.choice(SECTORES_DIRECCION)}, Casa N° {random.randint(1, 200)}"

        registros.append((
            _generar_cedula_unica(cedulas_usadas),
            nombres,
            apellidos,
            fecha_nacimiento,
            genero,
            random.choice(niveles),
            random.choice(grados),
            id_municipio,
            id_parroquia,
            random.choice(estatus),
            fecha_registro,
            telefono,
            direccion,
        ))

    conn.executemany(
        """INSERT INTO personal_militar
           (cedula, nombres, apellidos, fecha_nacimiento, genero,
            id_nivel_educativo, id_grado, id_municipio, id_parroquia,
            id_estatus, fecha_registro, telefono, direccion)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        registros,
    )
    logger.info("Se generaron %d registros ficticios de personal.", len(registros))
    return len(registros)


def ejecutar_seed(incluir_datos_ficticios: bool = True, cantidad_ficticios: int = 250) -> None:
    """
    Punto de entrada principal del seed. Ejecuta todo dentro de una
    única transacción: si algo falla, no queda data parcial.
    """
    with db_session() as conn:
        _poblar_municipios(conn)
        _poblar_parroquias(conn)
        _poblar_catalogos(conn)
        if incluir_datos_ficticios:
            poblar_datos_ficticios_personal(conn, cantidad_ficticios)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    ejecutar_seed()
    print("✅ Seed ejecutado correctamente.")
