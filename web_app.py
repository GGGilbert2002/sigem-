"""
web_app.py
===========
Version web completa de SIGEM usando Flask.
Incluye: Dashboard, Personal (CRUD completo), Registro, Estadisticas, Mapas.
"""

import io
import base64
import os
import logging

from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash)
import matplotlib
matplotlib.use("Agg")

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import inicializar_base_datos
from database.seed_data import ejecutar_seed
from models.usuario import autenticar, CredencialesInvalidasError
from models.militar import (buscar_personal, obtener_personal,
                             crear_personal, actualizar_personal,
                             eliminar_personal, CedulaDuplicadaError,
                             RegistroNoEncontradoError)
from models import geografia
from controllers import estadisticas_controller as ec
from controllers import graficos_controller as gc
from controllers import mapas_controller as mc
from utils.validators import ValidationError
from database.connection import get_connection

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sigem-clave-secreta-2026")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sigem.web")


def _fig_b64(figura) -> str:
    buf = io.BytesIO()
    figura.savefig(buf, format="png", bbox_inches="tight",
                   facecolor=figura.get_facecolor())
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return img


def _login_req(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def _cargar_catalogo(tabla, col_id, col_desc):
    conn = get_connection()
    try:
        filas = conn.execute(
            f"SELECT {col_id}, {col_desc} FROM {tabla} ORDER BY {col_desc}"
        ).fetchall()
        return [(f[col_id], f[col_desc]) for f in filas]
    finally:
        conn.close()


with app.app_context():
    try:
        inicializar_base_datos()
        ejecutar_seed(incluir_datos_ficticios=True, cantidad_ficticios=250)
        from models.usuario import crear_usuario, existe_algun_usuario
        if not existe_algun_usuario():
            crear_usuario("admin", "Administrador del Sistema", "admin123")
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar la BD: {e}")


# ── Login / Logout ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "usuario" in session else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        try:
            usuario = autenticar(request.form["usuario"], request.form["password"])
            session["usuario"] = usuario.nombre_completo
            return redirect(url_for("dashboard"))
        except CredencialesInvalidasError:
            error = "Usuario o contraseña incorrectos."
            logger.warning(f"Login fallido: {request.form.get('usuario')}")
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@_login_req
def dashboard():
    resumen = ec.resumen_general()
    return render_template("dashboard.html",
                           resumen=resumen,
                           img_municipio=_fig_b64(gc.grafico_distribucion_municipio()),
                           img_genero=_fig_b64(gc.grafico_distribucion_genero()),
                           usuario=session["usuario"])


# ── Gestión de Personal (listado + eliminar) ──────────────────────────────────

@app.route("/personal")
@_login_req
def personal():
    texto = request.args.get("q", "").strip() or None
    municipio_id = request.args.get("municipio") or None
    if municipio_id:
        municipio_id = int(municipio_id)
    registros = buscar_personal(texto=texto, id_municipio=municipio_id)
    municipios = geografia.listar_municipios(solo_adyacentes_coro=True)
    return render_template("personal.html",
                           registros=registros,
                           municipios=municipios,
                           busqueda=texto or "",
                           municipio_sel=municipio_id,
                           usuario=session["usuario"])


@app.route("/personal/eliminar/<int:id_personal>", methods=["POST"])
@_login_req
def eliminar(id_personal):
    try:
        eliminar_personal(id_personal)
        flash("Registro eliminado correctamente.", "success")
    except RegistroNoEncontradoError:
        flash("El registro ya no existe.", "warning")
    except Exception as e:
        flash(f"Error al eliminar: {e}", "error")
    return redirect(url_for("personal"))


# ── Nuevo registro ────────────────────────────────────────────────────────────

@app.route("/personal/nuevo", methods=["GET", "POST"])
@_login_req
def nuevo_registro():
    error = None
    if request.method == "POST":
        datos = _datos_desde_form(request.form)
        try:
            crear_personal(datos)
            flash("Registro guardado correctamente.", "success")
            return redirect(url_for("personal"))
        except (ValidationError, CedulaDuplicadaError) as e:
            error = str(e)
        except Exception as e:
            error = f"Error inesperado: {e}"
    return render_template("formulario.html",
                           titulo="Nuevo Registro de Personal",
                           accion=url_for("nuevo_registro"),
                           registro=None,
                           error=error,
                           **_contexto_formulario(),
                           usuario=session["usuario"])


# ── Editar registro ───────────────────────────────────────────────────────────

@app.route("/personal/editar/<int:id_personal>", methods=["GET", "POST"])
@_login_req
def editar_registro(id_personal):
    registro = obtener_personal(id_personal)
    error = None
    if request.method == "POST":
        datos = _datos_desde_form(request.form)
        try:
            actualizar_personal(id_personal, datos)
            flash("Registro actualizado correctamente.", "success")
            return redirect(url_for("personal"))
        except (ValidationError, CedulaDuplicadaError) as e:
            error = str(e)
        except Exception as e:
            error = f"Error inesperado: {e}"
    return render_template("formulario.html",
                           titulo="Editar Registro de Personal",
                           accion=url_for("editar_registro",
                                          id_personal=id_personal),
                           registro=registro,
                           error=error,
                           **_contexto_formulario(),
                           usuario=session["usuario"])


def _datos_desde_form(form):
    return {
        "cedula": form.get("cedula", ""),
        "nombres": form.get("nombres", ""),
        "apellidos": form.get("apellidos", ""),
        "fecha_nacimiento": form.get("fecha_nacimiento", ""),
        "genero": form.get("genero", ""),
        "id_municipio": int(form["id_municipio"]) if form.get("id_municipio") else None,
        "id_parroquia": int(form["id_parroquia"]) if form.get("id_parroquia") else None,
        "id_nivel_educativo": int(form["id_nivel_educativo"]) if form.get("id_nivel_educativo") else None,
        "id_grado": int(form["id_grado"]) if form.get("id_grado") else None,
        "id_estatus": int(form["id_estatus"]) if form.get("id_estatus") else None,
        "telefono": form.get("telefono", ""),
        "direccion": form.get("direccion", ""),
        "observaciones": form.get("observaciones", ""),
    }


def _contexto_formulario():
    return {
        "municipios": geografia.listar_municipios(solo_adyacentes_coro=True),
        "niveles": _cargar_catalogo("niveles_educativos",
                                    "id_nivel_educativo", "descripcion"),
        "grados": _cargar_catalogo("grados_militares", "id_grado", "nombre"),
        "estatus_lista": _cargar_catalogo("estatus_participacion",
                                          "id_estatus", "descripcion"),
    }


# ── Parroquias por municipio (AJAX) ───────────────────────────────────────────

@app.route("/api/parroquias/<int:id_municipio>")
@_login_req
def api_parroquias(id_municipio):
    parroquias = geografia.listar_parroquias_por_municipio(id_municipio)
    return jsonify([{"id": p.id_parroquia, "nombre": p.nombre}
                    for p in parroquias])


# ── Estadísticas ──────────────────────────────────────────────────────────────

@app.route("/estadisticas")
@_login_req
def estadisticas():
    graficos = {
        "edad":      _fig_b64(gc.grafico_distribucion_edad()),
        "nivel":     _fig_b64(gc.grafico_nivel_educativo()),
        "estatus":   _fig_b64(gc.grafico_distribucion_estatus()),
        "parroquia": _fig_b64(gc.grafico_distribucion_parroquia("Miranda")),
        "tendencia": _fig_b64(gc.grafico_tendencia_temporal()),
    }
    return render_template("estadisticas.html", graficos=graficos,
                           usuario=session["usuario"])


# ── Mapas ─────────────────────────────────────────────────────────────────────

@app.route("/mapas")
@_login_req
def mapas():
    modo = request.args.get("modo", "municipios")
    img_preview = _fig_b64(mc.generar_figura_preview(modo=modo))
    return render_template("mapas.html", modo=modo,
                           img_preview=img_preview,
                           usuario=session["usuario"])


# ── Health check ──────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    try:
        resumen = ec.resumen_general()
        return jsonify({"status": "ok", "version": "1.0.0",
                        "sistema": "SIGEM",
                        "total_registros": resumen.get("total_registros", 0)}), 200
    except Exception as e:
        return jsonify({"status": "error", "detalle": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
