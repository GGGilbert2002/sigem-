"""
models/geografia.py
====================
Modelo y operaciones de acceso a datos (DAO) para la jerarquía
territorial: Municipios -> Parroquias.

Esta capa es usada por:
- El formulario de registro de personal (combos dependientes)
- El módulo de mapas territoriales / mapas de calor
- El módulo de estadísticas comparativas por zona
"""

from dataclasses import dataclass
from typing import List, Optional

from database.connection import get_connection


@dataclass
class Municipio:
    id_municipio: int
    nombre: str
    capital: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]
    es_adyacente_coro: bool

    @staticmethod
    def desde_fila(fila) -> "Municipio":
        return Municipio(
            id_municipio=fila["id_municipio"],
            nombre=fila["nombre"],
            capital=fila["capital"],
            latitud=fila["latitud"],
            longitud=fila["longitud"],
            es_adyacente_coro=bool(fila["es_adyacente_coro"]),
        )


@dataclass
class Parroquia:
    id_parroquia: int
    nombre: str
    id_municipio: int
    latitud: Optional[float]
    longitud: Optional[float]

    @staticmethod
    def desde_fila(fila) -> "Parroquia":
        return Parroquia(
            id_parroquia=fila["id_parroquia"],
            nombre=fila["nombre"],
            id_municipio=fila["id_municipio"],
            latitud=fila["latitud"],
            longitud=fila["longitud"],
        )


def listar_municipios(solo_adyacentes_coro: bool = False) -> List[Municipio]:
    """
    Retorna todos los municipios. Si solo_adyacentes_coro=True, filtra
    solo los municipios definidos como parte del alcance del estudio
    (Capítulo I: municipios cercanos a la ciudad de Coro).
    """
    conn = get_connection()
    try:
        query = "SELECT * FROM municipios"
        if solo_adyacentes_coro:
            query += " WHERE es_adyacente_coro = 1"
        query += " ORDER BY nombre"
        filas = conn.execute(query).fetchall()
        return [Municipio.desde_fila(f) for f in filas]
    finally:
        conn.close()


def obtener_municipio(id_municipio: int) -> Optional[Municipio]:
    conn = get_connection()
    try:
        fila = conn.execute(
            "SELECT * FROM municipios WHERE id_municipio = ?", (id_municipio,)
        ).fetchone()
        return Municipio.desde_fila(fila) if fila else None
    finally:
        conn.close()


def listar_parroquias_por_municipio(id_municipio: int) -> List[Parroquia]:
    """Retorna las parroquias de un municipio específico, ordenadas alfabéticamente."""
    conn = get_connection()
    try:
        filas = conn.execute(
            "SELECT * FROM parroquias WHERE id_municipio = ? ORDER BY nombre",
            (id_municipio,),
        ).fetchall()
        return [Parroquia.desde_fila(f) for f in filas]
    finally:
        conn.close()


def obtener_parroquia(id_parroquia: int) -> Optional[Parroquia]:
    conn = get_connection()
    try:
        fila = conn.execute(
            "SELECT * FROM parroquias WHERE id_parroquia = ?", (id_parroquia,)
        ).fetchone()
        return Parroquia.desde_fila(fila) if fila else None
    finally:
        conn.close()


def resumen_por_municipio() -> List[dict]:
    """
    Retorna el resumen agregado (total de registros, por género) de
    cada municipio, usando la vista SQL vw_resumen_municipio.
    Ideal para alimentar mapas de calor y gráficos comparativos.
    """
    conn = get_connection()
    try:
        filas = conn.execute(
            "SELECT * FROM vw_resumen_municipio ORDER BY total_registros DESC"
        ).fetchall()
        return [dict(f) for f in filas]
    finally:
        conn.close()


def resumen_por_parroquia(id_municipio: Optional[int] = None) -> List[dict]:
    """
    Retorna el resumen agregado de cada parroquia. Si se especifica
    id_municipio, filtra solo las parroquias de ese municipio.
    """
    conn = get_connection()
    try:
        query = "SELECT * FROM vw_resumen_parroquia"
        params = ()
        if id_municipio is not None:
            query += " WHERE id_municipio = ?"
            params = (id_municipio,)
        query += " ORDER BY total_registros DESC"
        filas = conn.execute(query, params).fetchall()
        return [dict(f) for f in filas]
    finally:
        conn.close()
