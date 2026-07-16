"""
models/militar.py
==================
Modelo y operaciones de acceso a datos (DAO) para el personal militar:
la entidad central del sistema, que registra la participación y
reclutamiento en el servicio militar (Cuadro de Operacionalización
de Variables, Capítulo II del proyecto).

Provee operaciones CRUD completas (Crear, Leer, Actualizar, Eliminar)
más búsqueda/filtrado, que serán consumidas por:
- La vista de gestión de personal (tabla + formulario)
- El módulo de estadísticas
- El módulo de mapas territoriales
- El módulo de reportes
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from database.connection import db_session, get_connection
from utils.validators import (
    ValidationError,
    calcular_edad,
    validar_cedula,
    validar_fecha_nacimiento,
    validar_genero,
    validar_nombre_texto,
    validar_telefono,
)


class CedulaDuplicadaError(Exception):
    """Se lanza al intentar registrar una cédula que ya existe en el sistema."""
    pass


class RegistroNoEncontradoError(Exception):
    """Se lanza al intentar leer/actualizar/eliminar un id_personal que no existe."""
    pass


@dataclass
class PersonalMilitar:
    """Representa un registro de personal, ya con los nombres de catálogos resueltos
    (no solo los IDs), listo para mostrar en la interfaz o usar en reportes."""
    id_personal: int
    cedula: str
    nombres: str
    apellidos: str
    fecha_nacimiento: str
    edad: int
    genero: str
    nivel_educativo: Optional[str]
    grado: Optional[str]
    municipio: str
    id_municipio: int
    parroquia: Optional[str]
    id_parroquia: Optional[int]
    estatus: str
    id_estatus: int
    fecha_registro: str
    telefono: Optional[str]
    direccion: Optional[str]
    observaciones: Optional[str]

    @staticmethod
    def desde_fila(fila) -> "PersonalMilitar":
        return PersonalMilitar(
            id_personal=fila["id_personal"],
            cedula=fila["cedula"],
            nombres=fila["nombres"],
            apellidos=fila["apellidos"],
            fecha_nacimiento=fila["fecha_nacimiento"],
            edad=calcular_edad(fila["fecha_nacimiento"]),
            genero=fila["genero"],
            nivel_educativo=fila["nivel_educativo"],
            grado=fila["grado"],
            municipio=fila["municipio"],
            id_municipio=fila["id_municipio"],
            parroquia=fila["parroquia"],
            id_parroquia=fila["id_parroquia"],
            estatus=fila["estatus"],
            id_estatus=fila["id_estatus"],
            fecha_registro=fila["fecha_registro"],
            telefono=fila["telefono"],
            direccion=fila["direccion"],
            observaciones=fila["observaciones"],
        )


# Consulta base reutilizada por obtener/listar/buscar: resuelve todos los
# nombres de catálogos mediante JOIN para no repetir esta consulta en cada función.
_QUERY_BASE = """
    SELECT
        p.id_personal, p.cedula, p.nombres, p.apellidos, p.fecha_nacimiento,
        p.genero, p.telefono, p.direccion, p.observaciones,
        p.fecha_registro, p.id_municipio, p.id_parroquia, p.id_estatus,
        n.descripcion AS nivel_educativo,
        g.nombre AS grado,
        m.nombre AS municipio,
        pq.nombre AS parroquia,
        e.descripcion AS estatus
    FROM personal_militar p
    LEFT JOIN niveles_educativos n ON p.id_nivel_educativo = n.id_nivel_educativo
    LEFT JOIN grados_militares g ON p.id_grado = g.id_grado
    JOIN municipios m ON p.id_municipio = m.id_municipio
    LEFT JOIN parroquias pq ON p.id_parroquia = pq.id_parroquia
    JOIN estatus_participacion e ON p.id_estatus = e.id_estatus
"""


def crear_personal(datos: dict) -> PersonalMilitar:
    """
    Crea un nuevo registro de personal. 'datos' debe incluir, como mínimo:
    cedula, nombres, apellidos, fecha_nacimiento, genero, id_municipio,
    id_estatus, fecha_registro.
    Campos opcionales: id_nivel_educativo, id_grado, id_parroquia,
    telefono, direccion, observaciones.

    Valida los datos de entrada antes de insertar. Lanza ValidationError
    si algún campo no es válido, o CedulaDuplicadaError si la cédula ya existe.
    """
    cedula = validar_cedula(datos["cedula"])
    nombres = validar_nombre_texto(datos["nombres"], "nombres")
    apellidos = validar_nombre_texto(datos["apellidos"], "apellidos")
    fecha_nacimiento = validar_fecha_nacimiento(datos["fecha_nacimiento"])
    genero = validar_genero(datos["genero"])
    telefono = validar_telefono(datos.get("telefono") or "")

    if not datos.get("id_municipio"):
        raise ValidationError("Debe seleccionar un municipio.")
    if not datos.get("id_estatus"):
        raise ValidationError("Debe seleccionar un estatus de participación.")

    fecha_registro = datos.get("fecha_registro") or datetime.now().date().isoformat()

    try:
        with db_session() as conn:
            cur = conn.execute(
                """INSERT INTO personal_militar
                   (cedula, nombres, apellidos, fecha_nacimiento, genero,
                    id_nivel_educativo, id_grado, id_municipio, id_parroquia,
                    id_estatus, fecha_registro, telefono, direccion, observaciones)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cedula, nombres, apellidos, fecha_nacimiento, genero,
                    datos.get("id_nivel_educativo"), datos.get("id_grado"),
                    datos["id_municipio"], datos.get("id_parroquia"),
                    datos["id_estatus"], fecha_registro,
                    telefono or None, datos.get("direccion") or None,
                    datos.get("observaciones") or None,
                ),
            )
            id_personal = cur.lastrowid
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise CedulaDuplicadaError(
                f"Ya existe un registro con la cédula {cedula}."
            ) from e
        raise

    return obtener_personal(id_personal)


def obtener_personal(id_personal: int) -> PersonalMilitar:
    conn = get_connection()
    try:
        fila = conn.execute(
            _QUERY_BASE + " WHERE p.id_personal = ?", (id_personal,)
        ).fetchone()
    finally:
        conn.close()

    if fila is None:
        raise RegistroNoEncontradoError(f"No existe personal con id {id_personal}.")
    return PersonalMilitar.desde_fila(fila)


def actualizar_personal(id_personal: int, datos: dict) -> PersonalMilitar:
    """
    Actualiza un registro existente. Acepta los mismos campos que
    crear_personal(). Valida los datos antes de actualizar.
    """
    # Aseguramos que el registro exista antes de intentar actualizar
    obtener_personal(id_personal)

    cedula = validar_cedula(datos["cedula"])
    nombres = validar_nombre_texto(datos["nombres"], "nombres")
    apellidos = validar_nombre_texto(datos["apellidos"], "apellidos")
    fecha_nacimiento = validar_fecha_nacimiento(datos["fecha_nacimiento"])
    genero = validar_genero(datos["genero"])
    telefono = validar_telefono(datos.get("telefono") or "")

    try:
        with db_session() as conn:
            conn.execute(
                """UPDATE personal_militar SET
                    cedula = ?, nombres = ?, apellidos = ?, fecha_nacimiento = ?,
                    genero = ?, id_nivel_educativo = ?, id_grado = ?,
                    id_municipio = ?, id_parroquia = ?, id_estatus = ?,
                    telefono = ?, direccion = ?, observaciones = ?,
                    actualizado_en = datetime('now','localtime')
                   WHERE id_personal = ?""",
                (
                    cedula, nombres, apellidos, fecha_nacimiento, genero,
                    datos.get("id_nivel_educativo"), datos.get("id_grado"),
                    datos["id_municipio"], datos.get("id_parroquia"),
                    datos["id_estatus"], telefono or None,
                    datos.get("direccion") or None, datos.get("observaciones") or None,
                    id_personal,
                ),
            )
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise CedulaDuplicadaError(
                f"Ya existe otro registro con la cédula {cedula}."
            ) from e
        raise

    return obtener_personal(id_personal)


def eliminar_personal(id_personal: int) -> None:
    """Elimina un registro de personal de forma permanente."""
    obtener_personal(id_personal)  # valida que exista, lanza error claro si no
    with db_session() as conn:
        conn.execute("DELETE FROM personal_militar WHERE id_personal = ?", (id_personal,))


def listar_personal(limite: Optional[int] = None, offset: int = 0) -> List[PersonalMilitar]:
    """Lista todo el personal, ordenado por fecha de registro descendente (más reciente primero)."""
    conn = get_connection()
    try:
        query = _QUERY_BASE + " ORDER BY p.fecha_registro DESC, p.id_personal DESC"
        params: tuple = ()
        if limite is not None:
            query += " LIMIT ? OFFSET ?"
            params = (limite, offset)
        filas = conn.execute(query, params).fetchall()
        return [PersonalMilitar.desde_fila(f) for f in filas]
    finally:
        conn.close()


def buscar_personal(
    texto: Optional[str] = None,
    id_municipio: Optional[int] = None,
    id_parroquia: Optional[int] = None,
    genero: Optional[str] = None,
    id_estatus: Optional[int] = None,
    id_nivel_educativo: Optional[int] = None,
    edad_min: Optional[int] = None,
    edad_max: Optional[int] = None,
) -> List[PersonalMilitar]:
    """
    Búsqueda flexible de personal con múltiples filtros opcionales,
    todos combinables entre sí (AND lógico). Usado por la pantalla de
    gestión de personal y por el módulo de estadísticas/reportes
    filtrados.

    'texto' busca coincidencias parciales en cédula, nombres o apellidos.
    """
    condiciones = []
    params: list = []

    if texto:
        condiciones.append(
            "(p.cedula LIKE ? OR p.nombres LIKE ? OR p.apellidos LIKE ?)"
        )
        comodin = f"%{texto.strip()}%"
        params.extend([comodin, comodin, comodin])

    if id_municipio:
        condiciones.append("p.id_municipio = ?")
        params.append(id_municipio)

    if id_parroquia:
        condiciones.append("p.id_parroquia = ?")
        params.append(id_parroquia)

    if genero:
        condiciones.append("p.genero = ?")
        params.append(genero)

    if id_estatus:
        condiciones.append("p.id_estatus = ?")
        params.append(id_estatus)

    if id_nivel_educativo:
        condiciones.append("p.id_nivel_educativo = ?")
        params.append(id_nivel_educativo)

    query = _QUERY_BASE
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)
    query += " ORDER BY p.apellidos, p.nombres"

    conn = get_connection()
    try:
        filas = conn.execute(query, params).fetchall()
        resultados = [PersonalMilitar.desde_fila(f) for f in filas]
    finally:
        conn.close()

    # El filtro de edad se aplica en Python porque la edad se calcula
    # dinámicamente a partir de fecha_nacimiento (no es una columna en BD).
    if edad_min is not None:
        resultados = [r for r in resultados if r.edad >= edad_min]
    if edad_max is not None:
        resultados = [r for r in resultados if r.edad <= edad_max]

    return resultados


def contar_total_personal() -> int:
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) AS c FROM personal_militar").fetchone()["c"]
    finally:
        conn.close()
