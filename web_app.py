"""
web_app.py
===========
Versión web de SIGEM usando Flask.
Reutiliza los modelos y controladores existentes del proyecto.
Desplegado en Railway para cumplir con el Avance #5.
"""

import io
import base64
import os
import logging

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import matplotlib
matplotlib.use("Agg")

# Configurar path para importar módulos de SIGEM
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import inicializar_base_datos
from database.seed_data import ejecutar_seed
from models.usuario import autenticar, CredencialesInvalidasError
from models.militar import buscar_personal, listar_personal
from controllers import estadisticas_controller as ec
from controllers import graficos_controller as gc

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sigem-clave-secreta-2026")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sigem.web")


def _figura_a_base64(figura) -> str:
    """Convierte una figura matplotlib a string base64 para mostrar en HTML."""
    buf = io.BytesIO()
    figura.savefig(buf, format="png", bbox_inches="tight",
                   facecolor=figura.get_facecolor())
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return img_base64


def _login_requerido(f):
    """Decorador que redirige al login si no hay sesión activa."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Inicialización de la BD al arrancar ──────────────────────────────────────

with app.app_context():
    try:
        inicializar_base_datos()
        ejecutar_seed(incluir_datos_ficticios=True, cantidad_ficticios=250)
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la BD: {e}")


# ── Rutas ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if "usuario" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario_txt = request.form.get("usuario", "").strip()
        password_txt = request.form.get("password", "")
        try:
            usuario = autenticar(usuario_txt, password_txt)
            session["usuario"] = usuario.nombre_completo
            session["usuario_id"] = usuario.id_usuario
            logger.info(f"Login exitoso: {usuario_txt}")
            return redirect(url_for("dashboard"))
        except CredencialesInvalidasError:
            error = "Usuario o contraseña incorrectos."
            logger.warning(f"Intento de login fallido: {usuario_txt}")
        except Exception as e:
            error = f"Error inesperado: {e}"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@_login_requerido
def dashboard():
    resumen = ec.resumen_general()
    img_municipio = _figura_a_base64(gc.grafico_distribucion_municipio())
    img_genero = _figura_a_base64(gc.grafico_distribucion_genero())
    return render_template("dashboard.html",
                           resumen=resumen,
                           img_municipio=img_municipio,
                           img_genero=img_genero,
                           usuario=session.get("usuario"))


@app.route("/personal")
@_login_requerido
def personal():
    texto = request.args.get("q", "").strip() or None
    registros = buscar_personal(texto=texto)
    return render_template("personal.html",
                           registros=registros,
                           busqueda=texto or "",
                           usuario=session.get("usuario"))


@app.route("/estadisticas")
@_login_requerido
def estadisticas():
    graficos = {
        "edad":           _figura_a_base64(gc.grafico_distribucion_edad()),
        "nivel":          _figura_a_base64(gc.grafico_nivel_educativo()),
        "estatus":        _figura_a_base64(gc.grafico_distribucion_estatus()),
        "parroquia":      _figura_a_base64(gc.grafico_distribucion_parroquia("Miranda")),
        "tendencia":      _figura_a_base64(gc.grafico_tendencia_temporal()),
    }
    return render_template("estadisticas.html",
                           graficos=graficos,
                           usuario=session.get("usuario"))


@app.route("/health")
def health():
    """Endpoint de salud requerido por Avance #5 (auto-recuperación)."""
    try:
        resumen = ec.resumen_general()
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "sistema": "SIGEM",
            "total_registros": resumen.get("total_registros", 0)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "detalle": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
