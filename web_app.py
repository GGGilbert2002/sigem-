"""
web_app.py
===========
Version web completa de SIGEM con todas las funcionalidades de la
version de escritorio, adaptadas al navegador, mas medidas de seguridad:

Seguridad implementada (Avance #6 - BlueTeam):
- Timeout de sesion: 30 minutos de inactividad cierra la sesion
- Limite de intentos de login: bloqueo temporal tras 5 intentos fallidos
- Cabeceras de seguridad HTTP: X-Frame-Options, CSP, X-Content-Type, etc.
- Proteccion CSRF: token unico por sesion en todos los formularios POST
- Sanitizacion de entradas: validacion antes de tocar la BD
- Modo de falla seguro: errores internos no exponen detalles tecnicos
- Logs estructurados: cada accion queda registrada con contexto
"""

import io
import base64
import os
import time
import secrets
import logging
from functools import wraps
from datetime import datetime

from flask import (Flask, render_template, request, redirect,
                   url_for, session, jsonify, flash, abort, g)
import matplotlib
matplotlib.use("Agg")

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.connection import inicializar_base_datos, get_connection
from database.seed_data import ejecutar_seed
from models.usuario import autenticar, CredencialesInvalidasError
from models.militar import (buscar_personal, obtener_personal,
                             crear_personal, actualizar_personal,
                             eliminar_personal, CedulaDuplicadaError,
                             RegistroNoEncontradoError, listar_personal)
from models import geografia
from controllers import estadisticas_controller as ec
from controllers import graficos_controller as gc
from controllers import mapas_controller as mc
from utils.validators import ValidationError
from utils.exporters import (exportar_personal_excel,
                              generar_reporte_estadistico_pdf,
                              generar_reporte_personal_pdf,
                              exportar_resumen_estadistico_excel)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "sigem-clave-secreta-2026")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 1800  # 30 minutos

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sigem.web")

# Almacen en memoria de intentos fallidos: {ip: {"intentos": N, "bloqueado_hasta": T}}
_intentos_login: dict = {}
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 300  # 5 minutos


# ── Inicializacion de la BD ───────────────────────────────────────────────────

with app.app_context():
    try:
        inicializar_base_datos()
        ejecutar_seed(incluir_datos_ficticios=True, cantidad_ficticios=250)
        from models.usuario import crear_usuario, existe_algun_usuario
        if not existe_algun_usuario():
            crear_usuario("admin", "Administrador del Sistema", "admin123")
            logger.info("Usuario admin creado")
        logger.info("BD inicializada correctamente")
    except Exception as e:
        logger.error(f"Error al inicializar BD: {e}")


# ── Seguridad: cabeceras HTTP en cada respuesta ───────────────────────────────

@app.after_request
def agregar_cabeceras_seguridad(response):
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:;"
    )
    return response


# ── Seguridad: CSRF token ─────────────────────────────────────────────────────

def _generar_csrf():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)
    return session["csrf_token"]


def _validar_csrf():
    token_form = request.form.get("csrf_token", "")
    token_sesion = session.get("csrf_token", "")
    if not secrets.compare_digest(token_form, token_sesion):
        logger.warning(f"CSRF invalido desde {request.remote_addr}")
        abort(403)


@app.context_processor
def _inyectar_csrf():
    return {"csrf_token": _generar_csrf()}


# ── Seguridad: timeout de sesion ──────────────────────────────────────────────

@app.before_request
def _verificar_timeout_sesion():
    if "usuario" in session:
        ultima = session.get("ultima_actividad", 0)
        if time.time() - ultima > 1800:
            session.clear()
            flash("Tu sesion expiro por inactividad. Inicia sesion nuevamente.", "warning")
            return redirect(url_for("login"))
        session["ultima_actividad"] = time.time()
        session.permanent = True


# ── Decoradores ───────────────────────────────────────────────────────────────

def _login_req(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Utilidades ────────────────────────────────────────────────────────────────

def _fig_b64(figura) -> str:
    buf = io.BytesIO()
    figura.savefig(buf, format="png", bbox_inches="tight",
                   facecolor=figura.get_facecolor())
    buf.seek(0)
    img = base64.b64encode(buf.read()).decode("utf-8")
    buf.close()
    return img


def _cargar_catalogo(tabla, col_id, col_desc):
    conn = get_connection()
    try:
        filas = conn.execute(
            f"SELECT {col_id}, {col_desc} FROM {tabla} ORDER BY {col_desc}"
        ).fetchall()
        return [(f[col_id], f[col_desc]) for f in filas]
    finally:
        conn.close()


def _contexto_formulario():
    return {
        "municipios": geografia.listar_municipios(solo_adyacentes_coro=True),
        "niveles": _cargar_catalogo("niveles_educativos",
                                    "id_nivel_educativo", "descripcion"),
        "grados": _cargar_catalogo("grados_militares", "id_grado", "nombre"),
        "estatus_lista": _cargar_catalogo("estatus_participacion",
                                          "id_estatus", "descripcion"),
    }


def _datos_desde_form(form):
    return {
        "cedula":            form.get("cedula", "").strip(),
        "nombres":           form.get("nombres", "").strip(),
        "apellidos":         form.get("apellidos", "").strip(),
        "fecha_nacimiento":  form.get("fecha_nacimiento", "").strip(),
        "genero":            form.get("genero", "").strip(),
        "id_municipio":      int(form["id_municipio"]) if form.get("id_municipio") else None,
        "id_parroquia":      int(form["id_parroquia"]) if form.get("id_parroquia") else None,
        "id_nivel_educativo":int(form["id_nivel_educativo"]) if form.get("id_nivel_educativo") else None,
        "id_grado":          int(form["id_grado"]) if form.get("id_grado") else None,
        "id_estatus":        int(form["id_estatus"]) if form.get("id_estatus") else None,
        "telefono":          form.get("telefono", "").strip(),
        "direccion":         form.get("direccion", "").strip(),
        "observaciones":     form.get("observaciones", "").strip(),
    }


# ── LOGIN / LOGOUT ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("dashboard") if "usuario" in session else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        _validar_csrf()
        ip = request.remote_addr
        info = _intentos_login.get(ip, {"intentos": 0, "bloqueado_hasta": 0})

        # Verificar bloqueo temporal
        if time.time() < info["bloqueado_hasta"]:
            segundos = int(info["bloqueado_hasta"] - time.time())
            error = f"Demasiados intentos fallidos. Espera {segundos} segundos."
            return render_template("login.html", error=error)

        usuario_txt = request.form.get("usuario", "").strip()
        password_txt = request.form.get("password", "")

        # Sanitizacion basica
        if len(usuario_txt) > 50 or len(password_txt) > 128:
            error = "Datos de entrada invalidos."
            return render_template("login.html", error=error)

        try:
            usuario = autenticar(usuario_txt, password_txt)
            # Login exitoso: limpiar intentos
            _intentos_login.pop(ip, None)
            session.clear()
            session["usuario"] = usuario.nombre_completo
            session["usuario_id"] = usuario.id_usuario
            session["ultima_actividad"] = time.time()
            session.permanent = True
            logger.info(f"Login exitoso: {usuario_txt} desde {ip}")
            return redirect(url_for("dashboard"))
        except CredencialesInvalidasError:
            info["intentos"] += 1
            if info["intentos"] >= MAX_INTENTOS:
                info["bloqueado_hasta"] = time.time() + BLOQUEO_SEGUNDOS
                info["intentos"] = 0
                error = "Cuenta bloqueada temporalmente por multiples intentos fallidos."
            else:
                restantes = MAX_INTENTOS - info["intentos"]
                error = f"Usuario o contrasena incorrectos. Intentos restantes: {restantes}"
            _intentos_login[ip] = info
            logger.warning(f"Login fallido: {usuario_txt} desde {ip} "
                          f"(intento {info['intentos']})")
        except Exception:
            logger.exception("Error inesperado en login")
            error = "Error interno del sistema."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    usuario = session.get("usuario", "desconocido")
    session.clear()
    logger.info(f"Logout: {usuario}")
    flash("Sesion cerrada correctamente.", "success")
    return redirect(url_for("login"))


# ── DASHBOARD ─────────────────────────────────────────────────────────────────

@app.route("/dashboard")
@_login_req
def dashboard():
    resumen = ec.resumen_general()
    return render_template("dashboard.html",
                           resumen=resumen,
                           img_municipio=_fig_b64(gc.grafico_distribucion_municipio()),
                           img_genero=_fig_b64(gc.grafico_distribucion_genero()),
                           usuario=session["usuario"])


# ── GESTION DE PERSONAL ───────────────────────────────────────────────────────

@app.route("/personal")
@_login_req
def personal():
    texto = request.args.get("q", "").strip() or None
    mun_id = request.args.get("municipio") or None
    if mun_id:
        mun_id = int(mun_id)
    registros = buscar_personal(texto=texto, id_municipio=mun_id)
    municipios = geografia.listar_municipios(solo_adyacentes_coro=True)
    return render_template("personal.html",
                           registros=registros,
                           municipios=municipios,
                           busqueda=texto or "",
                           municipio_sel=mun_id,
                           usuario=session["usuario"])


@app.route("/personal/nuevo", methods=["GET", "POST"])
@_login_req
def nuevo_registro():
    error = None
    if request.method == "POST":
        _validar_csrf()
        try:
            crear_personal(_datos_desde_form(request.form))
            flash("Registro guardado correctamente.", "success")
            return redirect(url_for("personal"))
        except (ValidationError, CedulaDuplicadaError) as e:
            error = str(e)
        except Exception:
            logger.exception("Error al crear personal")
            error = "Error interno al guardar el registro."
    return render_template("formulario.html",
                           titulo="Nuevo Registro de Personal",
                           accion=url_for("nuevo_registro"),
                           registro=None, error=error,
                           **_contexto_formulario(),
                           usuario=session["usuario"])


@app.route("/personal/editar/<int:id_personal>", methods=["GET", "POST"])
@_login_req
def editar_registro(id_personal):
    try:
        registro = obtener_personal(id_personal)
    except Exception:
        flash("Registro no encontrado.", "error")
        return redirect(url_for("personal"))
    error = None
    if request.method == "POST":
        _validar_csrf()
        try:
            actualizar_personal(id_personal, _datos_desde_form(request.form))
            flash("Registro actualizado correctamente.", "success")
            return redirect(url_for("personal"))
        except (ValidationError, CedulaDuplicadaError) as e:
            error = str(e)
        except Exception:
            logger.exception("Error al actualizar personal")
            error = "Error interno al actualizar el registro."
    return render_template("formulario.html",
                           titulo="Editar Registro de Personal",
                           accion=url_for("editar_registro", id_personal=id_personal),
                           registro=registro, error=error,
                           **_contexto_formulario(),
                           usuario=session["usuario"])


@app.route("/personal/eliminar/<int:id_personal>", methods=["POST"])
@_login_req
def eliminar(id_personal):
    _validar_csrf()
    try:
        eliminar_personal(id_personal)
        flash("Registro eliminado correctamente.", "success")
    except RegistroNoEncontradoError:
        flash("El registro ya no existe.", "warning")
    except Exception:
        logger.exception("Error al eliminar personal")
        flash("Error interno al eliminar.", "error")
    return redirect(url_for("personal"))


# ── API: parroquias por municipio (AJAX) ──────────────────────────────────────

@app.route("/api/parroquias/<int:id_municipio>")
@_login_req
def api_parroquias(id_municipio):
    parroquias = geografia.listar_parroquias_por_municipio(id_municipio)
    return jsonify([{"id": p.id_parroquia, "nombre": p.nombre}
                    for p in parroquias])


# ── ESTADISTICAS ──────────────────────────────────────────────────────────────

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


# ── MAPAS ─────────────────────────────────────────────────────────────────────

@app.route("/mapas")
@_login_req
def mapas():
    modo = request.args.get("modo", "municipios")
    if modo not in ("municipios", "parroquias", "calor"):
        modo = "municipios"
    img_preview = _fig_b64(mc.generar_figura_preview(modo=modo))
    return render_template("mapas.html", modo=modo,
                           img_preview=img_preview,
                           usuario=session["usuario"])


# ── REPORTES ──────────────────────────────────────────────────────────────────

@app.route("/reportes")
@_login_req
def reportes():
    return render_template("reportes.html", usuario=session["usuario"])


@app.route("/reportes/descargar/<tipo>")
@_login_req
def descargar_reporte(tipo):
    import flask
    try:
        if tipo == "pdf_estadistico":
            ruta = generar_reporte_estadistico_pdf(incluir_graficos=True)
            nombre = "reporte_estadistico_SIGEM.pdf"
            mime = "application/pdf"
        elif tipo == "excel_personal":
            ruta = exportar_personal_excel(listar_personal())
            nombre = "personal_SIGEM.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif tipo == "pdf_personal":
            ruta = generar_reporte_personal_pdf(listar_personal())
            nombre = "listado_personal_SIGEM.pdf"
            mime = "application/pdf"
        elif tipo == "excel_resumen":
            ruta = exportar_resumen_estadistico_excel()
            nombre = "resumen_estadistico_SIGEM.xlsx"
            mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            abort(404)
        return flask.send_file(ruta, mimetype=mime,
                               as_attachment=True, download_name=nombre)
    except Exception:
        logger.exception(f"Error generando reporte tipo={tipo}")
        flash("Error al generar el reporte.", "error")
        return redirect(url_for("reportes"))


# ── HEALTH CHECK ──────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    try:
        resumen = ec.resumen_general()
        return jsonify({
            "status": "ok",
            "version": "1.0.0",
            "sistema": "SIGEM",
            "timestamp": datetime.utcnow().isoformat(),
            "total_registros": resumen.get("total_registros", 0),
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "detalle": "Error interno"}), 500


# ── MANEJO DE ERRORES SEGURO ──────────────────────────────────────────────────

@app.errorhandler(403)
def error_403(e):
    return render_template("error.html",
                           codigo=403,
                           mensaje="Acceso denegado.",
                           usuario=session.get("usuario", "")), 403


@app.errorhandler(404)
def error_404(e):
    return render_template("error.html",
                           codigo=404,
                           mensaje="Pagina no encontrada.",
                           usuario=session.get("usuario", "")), 404


@app.errorhandler(500)
def error_500(e):
    correlation_id = secrets.token_hex(8).upper()
    logger.error(f"Error 500 [ID:{correlation_id}]: {e}")
    return render_template("error.html",
                           codigo=500,
                           mensaje=f"Error interno del sistema. Reporte el codigo: {correlation_id}",
                           usuario=session.get("usuario", "")), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
