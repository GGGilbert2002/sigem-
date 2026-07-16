"""
utils/session.py
=================
Gestor de sesión en memoria para la aplicación de escritorio.

Como SIGEM es una aplicación de escritorio de un solo usuario por
ejecución (no un servidor web con múltiples sesiones concurrentes),
basta con guardar el usuario autenticado en una variable de módulo,
accesible desde cualquier ventana mientras la aplicación esté abierta.
"""

from typing import Optional

from models.usuario import Usuario

_usuario_actual: Optional[Usuario] = None


def iniciar_sesion(usuario: Usuario) -> None:
    global _usuario_actual
    _usuario_actual = usuario


def cerrar_sesion() -> None:
    global _usuario_actual
    _usuario_actual = None


def usuario_actual() -> Optional[Usuario]:
    return _usuario_actual


def hay_sesion_activa() -> bool:
    return _usuario_actual is not None
