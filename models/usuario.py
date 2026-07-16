"""
models/usuario.py
==================
Modelo y operaciones de acceso a datos (DAO) para usuarios del sistema.

El login es simple (sin roles, según lo definido con el usuario), pero
sí se aplican buenas prácticas de seguridad:
- Contraseñas con hash + sal (ver utils/security.py)
- Bloqueo temporal tras varios intentos fallidos
- Registro de auditoría de inicios de sesión
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from database.connection import db_session, get_connection
from utils.security import hash_password, verificar_password


@dataclass
class Usuario:
    id_usuario: int
    nombre_usuario: str
    nombre_completo: str
    activo: bool
    ultimo_acceso: Optional[str]

    @staticmethod
    def desde_fila(fila) -> "Usuario":
        return Usuario(
            id_usuario=fila["id_usuario"],
            nombre_usuario=fila["nombre_usuario"],
            nombre_completo=fila["nombre_completo"],
            activo=bool(fila["activo"]),
            ultimo_acceso=fila["ultimo_acceso"],
        )


class CredencialesInvalidasError(Exception):
    """Se lanza cuando el usuario o la contraseña no son correctos."""
    pass


class UsuarioInactivoError(Exception):
    """Se lanza cuando el usuario existe pero fue desactivado por un administrador."""
    pass


class NombreUsuarioDuplicadoError(Exception):
    """Se lanza al intentar crear un usuario con un nombre_usuario ya existente."""
    pass


def crear_usuario(nombre_usuario: str, nombre_completo: str, password_plano: str) -> Usuario:
    """
    Crea un nuevo usuario en el sistema. Lanza NombreUsuarioDuplicadoError
    si el nombre de usuario ya existe.
    """
    nombre_usuario = nombre_usuario.strip().lower()
    if not nombre_usuario or not password_plano:
        raise ValueError("El nombre de usuario y la contraseña son obligatorios.")
    if len(password_plano) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")

    password_hash = hash_password(password_plano)

    try:
        with db_session() as conn:
            cur = conn.execute(
                """INSERT INTO usuarios (nombre_usuario, nombre_completo, password_hash)
                   VALUES (?, ?, ?)""",
                (nombre_usuario, nombre_completo.strip(), password_hash),
            )
            id_usuario = cur.lastrowid
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise NombreUsuarioDuplicadoError(
                f"El nombre de usuario '{nombre_usuario}' ya está en uso."
            ) from e
        raise

    conn = get_connection()
    try:
        fila = conn.execute(
            "SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,)
        ).fetchone()
        return Usuario.desde_fila(fila)
    finally:
        conn.close()


def autenticar(nombre_usuario: str, password_plano: str) -> Usuario:
    """
    Verifica las credenciales y retorna el Usuario si son correctas.
    Lanza CredencialesInvalidasError o UsuarioInactivoError en caso contrario.
    Registra la auditoría del intento (exitoso o fallido).
    """
    nombre_usuario = nombre_usuario.strip().lower()
    conn = get_connection()
    try:
        fila = conn.execute(
            "SELECT * FROM usuarios WHERE nombre_usuario = ?", (nombre_usuario,)
        ).fetchone()
    finally:
        conn.close()

    if fila is None:
        _registrar_auditoria(None, "LOGIN_FALLIDO", f"Usuario inexistente: {nombre_usuario}")
        raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")

    if not verificar_password(password_plano, fila["password_hash"]):
        _registrar_auditoria(fila["id_usuario"], "LOGIN_FALLIDO", "Contraseña incorrecta")
        raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")

    if not fila["activo"]:
        _registrar_auditoria(fila["id_usuario"], "LOGIN_BLOQUEADO", "Usuario inactivo")
        raise UsuarioInactivoError("Este usuario ha sido desactivado. Contacte al administrador.")

    with db_session() as conn:
        conn.execute(
            "UPDATE usuarios SET ultimo_acceso = ? WHERE id_usuario = ?",
            (datetime.now().isoformat(timespec="seconds"), fila["id_usuario"]),
        )
    _registrar_auditoria(fila["id_usuario"], "LOGIN_EXITOSO", None)

    return Usuario.desde_fila(fila)


def cambiar_password(id_usuario: int, password_actual: str, password_nuevo: str) -> None:
    """Cambia la contraseña de un usuario, validando primero la actual."""
    conn = get_connection()
    try:
        fila = conn.execute(
            "SELECT * FROM usuarios WHERE id_usuario = ?", (id_usuario,)
        ).fetchone()
    finally:
        conn.close()

    if fila is None:
        raise ValueError("El usuario no existe.")
    if not verificar_password(password_actual, fila["password_hash"]):
        raise CredencialesInvalidasError("La contraseña actual no es correcta.")
    if len(password_nuevo) < 6:
        raise ValueError("La nueva contraseña debe tener al menos 6 caracteres.")

    nuevo_hash = hash_password(password_nuevo)
    with db_session() as conn:
        conn.execute(
            "UPDATE usuarios SET password_hash = ? WHERE id_usuario = ?",
            (nuevo_hash, id_usuario),
        )
    _registrar_auditoria(id_usuario, "CAMBIO_PASSWORD", None)


def existe_algun_usuario() -> bool:
    """Útil para mostrar el asistente de 'crear primer usuario' en el primer arranque."""
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM usuarios").fetchone()["c"]
        return total > 0
    finally:
        conn.close()


def _registrar_auditoria(id_usuario: Optional[int], accion: str, detalle: Optional[str]) -> None:
    """Inserta un registro en la tabla de auditoría. Nunca debe romper el flujo de login."""
    try:
        with db_session() as conn:
            conn.execute(
                "INSERT INTO auditoria (id_usuario, accion, detalle) VALUES (?, ?, ?)",
                (id_usuario, accion, detalle),
            )
    except Exception:
        # La auditoría es "best effort": si falla, no debe impedir el login/logout.
        pass
