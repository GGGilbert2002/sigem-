"""
utils/validators.py
====================
Validaciones reutilizables para los datos de entrada del sistema.
Centralizar esto evita duplicar reglas de validación entre la interfaz
gráfica y la capa de modelos.
"""

import re
from datetime import date, datetime

CEDULA_REGEX = re.compile(r"^\d{6,9}$")
TELEFONO_REGEX = re.compile(r"^0(412|414|416|424|426)-?\d{7}$")


class ValidationError(Exception):
    """Error de validación de datos de entrada, pensado para mostrarse al usuario."""
    pass


def validar_cedula(cedula: str) -> str:
    cedula = cedula.strip().replace(".", "").replace("-", "")
    if not CEDULA_REGEX.match(cedula):
        raise ValidationError(
            "La cédula debe contener solo números, entre 6 y 9 dígitos."
        )
    return cedula


def validar_nombre_texto(valor: str, campo: str, minimo: int = 2) -> str:
    valor = valor.strip()
    if len(valor) < minimo:
        raise ValidationError(f"El campo '{campo}' debe tener al menos {minimo} caracteres.")
    if not all(c.isalpha() or c.isspace() for c in valor):
        raise ValidationError(f"El campo '{campo}' solo debe contener letras y espacios.")
    return valor


def validar_fecha_nacimiento(fecha_str: str) -> str:
    """
    Valida que la fecha tenga formato ISO (YYYY-MM-DD), sea una fecha
    real, no esté en el futuro, y que la persona tenga entre 18 y 60 años
    (rango razonable para personal militar activo o en proceso de
    reclutamiento).
    """
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError("La fecha de nacimiento debe tener el formato AAAA-MM-DD.")

    hoy = date.today()
    if fecha >= hoy:
        raise ValidationError("La fecha de nacimiento no puede ser hoy o en el futuro.")

    edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
    if edad < 18:
        raise ValidationError("La persona debe ser mayor de edad (18 años o más).")
    if edad > 60:
        raise ValidationError("La edad calculada supera el rango esperado (60 años). Verifique la fecha.")

    return fecha_str


def validar_genero(genero: str) -> str:
    genero = genero.strip().capitalize()
    if genero not in ("Masculino", "Femenino"):
        raise ValidationError("El género debe ser 'Masculino' o 'Femenino'.")
    return genero


def validar_telefono(telefono: str) -> str:
    """El teléfono es opcional; si se proporciona, debe tener formato venezolano válido."""
    telefono = telefono.strip()
    if not telefono:
        return ""
    telefono_normalizado = telefono.replace(" ", "")
    if not TELEFONO_REGEX.match(telefono_normalizado):
        raise ValidationError(
            "El teléfono debe tener formato venezolano válido, ej: 0414-1234567."
        )
    return telefono_normalizado


def calcular_edad(fecha_nacimiento_str: str) -> int:
    """Calcula la edad actual a partir de una fecha de nacimiento ISO (YYYY-MM-DD)."""
    fecha = datetime.strptime(fecha_nacimiento_str, "%Y-%m-%d").date()
    hoy = date.today()
    return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
