"""
tests/test_sigem.py
====================
Suite de pruebas unitarias automatizadas para SIGEM (pytest).
Cubre: validadores, seguridad, animaciones y configuración.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Bloque 1: Validación de cédula ────────────────────────────────────────

class TestValidacionCedula:
    def _ok(self, cedula):
        from utils.validators import validar_cedula
        try:
            validar_cedula(cedula)
            return True
        except Exception:
            return False

    def test_cedula_6_digitos_valida(self):
        assert self._ok("123456") is True

    def test_cedula_9_digitos_valida(self):
        assert self._ok("123456789") is True

    def test_cedula_muy_corta_invalida(self):
        assert self._ok("12345") is False

    def test_cedula_muy_larga_invalida(self):
        assert self._ok("1234567890") is False

    def test_cedula_con_letras_invalida(self):
        assert self._ok("1234AB") is False

    def test_cedula_vacia_invalida(self):
        assert self._ok("") is False


# ── Bloque 2: Validación de edad ──────────────────────────────────────────

class TestValidacionFechaNacimiento:
    def _ok(self, edad_anios):
        from utils.validators import validar_fecha_nacimiento
        from datetime import date
        anio = date.today().year - edad_anios
        try:
            validar_fecha_nacimiento(f"{anio}-06-15")
            return True
        except Exception:
            return False

    def test_edad_18_valida(self):
        assert self._ok(18) is True

    def test_edad_35_valida(self):
        assert self._ok(35) is True

    def test_edad_60_valida(self):
        assert self._ok(60) is True

    def test_menor_de_18_invalido(self):
        assert self._ok(17) is False

    def test_mayor_de_60_invalido(self):
        assert self._ok(61) is False


# ── Bloque 3: Seguridad — hash de contraseñas ─────────────────────────────

class TestSeguridad:
    def test_hash_no_es_texto_plano(self):
        from utils.security import hash_password
        assert hash_password("admin123") != "admin123"

    def test_verificacion_correcta(self):
        from utils.security import hash_password, verify_password
        h = hash_password("clave_secreta")
        assert verify_password("clave_secreta", h) is True

    def test_verificacion_incorrecta(self):
        from utils.security import hash_password, verify_password
        h = hash_password("clave_correcta")
        assert verify_password("clave_erronea", h) is False

    def test_hashes_con_salt_distintos(self):
        from utils.security import hash_password
        h1 = hash_password("misma_clave")
        h2 = hash_password("misma_clave")
        assert h1 != h2

    def test_hash_longitud_segura(self):
        from utils.security import hash_password
        assert len(hash_password("test")) >= 50


# ── Bloque 4: Animaciones — interpolador numérico ─────────────────────────

class TestInterpoladorNumerico:
    def _i(self, texto, progreso):
        from views.animaciones import _texto_en_progreso
        return _texto_en_progreso(texto, progreso)

    def test_progreso_0_da_cero(self):
        assert self._i("250", 0.0) == "0"

    def test_progreso_1_da_valor_final(self):
        assert self._i("250", 1.0) == "250"

    def test_progreso_mitad(self):
        assert self._i("100", 0.5) == "50"

    def test_texto_sin_numeros_no_cambia(self):
        assert self._i("Sin datos", 0.5) == "Sin datos"

    def test_progreso_mayor_a_1_acotado(self):
        assert self._i("100", 1.5) == "100"

    def test_progreso_negativo_da_cero(self):
        assert self._i("100", -0.5) == "0"

    def test_formato_doble_numero(self):
        r = self._i("126 / 124", 1.0)
        assert "126" in r and "124" in r


# ── Bloque 5: Configuración del sistema ───────────────────────────────────

class TestConfiguracion:
    def test_latitud_coro_valida(self):
        import config
        assert 10.0 < config.CORO_LAT < 12.0

    def test_longitud_coro_valida(self):
        import config
        assert -71.0 < config.CORO_LON < -68.0

    def test_version_formato_semver(self):
        import config
        partes = config.VERSION.split(".")
        assert len(partes) == 3 and all(p.isdigit() for p in partes)

    def test_nombre_sistema_no_vacio(self):
        import config
        assert len(config.NOMBRE_SISTEMA.strip()) > 0

    def test_zoom_mapa_valido(self):
        import config
        assert 1 <= config.ZOOM_INICIAL_MAPA <= 18
