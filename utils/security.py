"""
utils/security.py
==================
Manejo seguro de contraseñas para el sistema de login.

Se usa PBKDF2-HMAC-SHA256 (disponible nativamente en hashlib, sin
dependencias externas) con una "sal" (salt) aleatoria por usuario.
Esto evita guardar contraseñas en texto plano y protege contra
ataques de diccionario / tablas precalculadas (rainbow tables).

Formato de almacenamiento del hash (todo en un solo campo de texto):
    pbkdf2_sha256$<iteraciones>$<salt_hex>$<hash_hex>
"""

import hashlib
import hmac
import os

ALGORITMO = "pbkdf2_sha256"
ITERACIONES = 260_000  # recomendado por OWASP (2023+) para PBKDF2-SHA256


def hash_password(password_plano: str) -> str:
    """
    Genera el hash seguro de una contraseña en texto plano.
    Cada llamada genera una sal distinta, por lo que la misma
    contraseña producirá hashes distintos cada vez (esto es correcto
    y esperado).
    """
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac(
        "sha256",
        password_plano.encode("utf-8"),
        salt,
        ITERACIONES,
    )
    return f"{ALGORITMO}${ITERACIONES}${salt.hex()}${hash_bytes.hex()}"


def verificar_password(password_plano: str, hash_almacenado: str) -> bool:
    """
    Verifica si una contraseña en texto plano coincide con el hash
    almacenado. Usa comparación en tiempo constante (hmac.compare_digest)
    para evitar ataques de temporización (timing attacks).
    """
    try:
        algoritmo, iteraciones_str, salt_hex, hash_hex = hash_almacenado.split("$")
    except ValueError:
        # Formato de hash corrupto o inválido
        return False

    if algoritmo != ALGORITMO:
        return False

    iteraciones = int(iteraciones_str)
    salt = bytes.fromhex(salt_hex)
    hash_esperado = bytes.fromhex(hash_hex)

    hash_calculado = hashlib.pbkdf2_hmac(
        "sha256",
        password_plano.encode("utf-8"),
        salt,
        iteraciones,
    )
    return hmac.compare_digest(hash_calculado, hash_esperado)
