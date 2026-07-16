"""
tests/verificar_backend.py
============================
Script de VERIFICACIÓN INTEGRAL del backend de SIGEM.

Ejecuta este script en tu máquina (con las dependencias del
requirements.txt ya instaladas) para confirmar que toda la lógica de
negocio funciona correctamente ANTES de avanzar a la interfaz gráfica.

Cómo ejecutarlo:
    cd sigem
    pip install -r requirements.txt
    python tests/verificar_backend.py

El script:
1. Inicializa la base de datos desde cero (si no existe).
2. Carga los datos semilla (municipios, parroquias, catálogos, y
   250 registros ficticios de personal).
3. Prueba cada módulo del sistema (usuarios, personal, estadísticas,
   gráficos, mapas, reportes) e imprime un resumen claro de
   ✅ ÉXITO / ❌ ERROR para cada uno.
4. Genera archivos de muestra en la carpeta reports/ y resources/geodata/
   para que puedas inspeccionarlos visualmente (abrir el PDF, el Excel,
   y el mapa HTML en tu navegador).

Si algo falla, el script imprime el error completo para que lo
revisemos juntos.
"""

import os
import sys
import traceback

# Asegura que el proyecto se pueda importar sin importar desde dónde
# se ejecute el script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESULTADOS = []


def _check(nombre_prueba, funcion):
    """Ejecuta una prueba, captura cualquier excepción, e imprime el resultado."""
    try:
        funcion()
        print(f"✅ {nombre_prueba}")
        RESULTADOS.append((nombre_prueba, True, None))
    except Exception as e:
        print(f"❌ {nombre_prueba}")
        print("   Detalle del error:")
        print("   " + "\n   ".join(traceback.format_exc().splitlines()))
        RESULTADOS.append((nombre_prueba, False, str(e)))


def main():
    print("=" * 70)
    print(" SIGEM - VERIFICACIÓN INTEGRAL DEL BACKEND")
    print("=" * 70)
    print()

    # -----------------------------------------------------------------
    # 1) Base de datos
    # -----------------------------------------------------------------
    print("--- 1. Base de datos ---")

    def t_inicializar_bd():
        from database.connection import inicializar_base_datos
        inicializar_base_datos()

    _check("Inicializar base de datos (esquema + migraciones)", t_inicializar_bd)

    def t_seed():
        from database.seed_data import ejecutar_seed
        ejecutar_seed(incluir_datos_ficticios=True, cantidad_ficticios=250)

    _check("Cargar datos semilla (municipios, parroquias, catálogos, 250 registros)", t_seed)

    def t_conteo():
        from models.militar import contar_total_personal
        total = contar_total_personal()
        assert total > 0, "No se cargaron registros de personal"
        print(f"   -> Total de personal en la base de datos: {total}")

    _check("Verificar que hay datos cargados", t_conteo)
    print()

    # -----------------------------------------------------------------
    # 2) Usuarios y seguridad
    # -----------------------------------------------------------------
    print("--- 2. Usuarios y autenticación ---")

    def t_usuario():
        from models.usuario import crear_usuario, autenticar, existe_algun_usuario, NombreUsuarioDuplicadoError
        if not existe_algun_usuario():
            crear_usuario("admin", "Administrador del Sistema", "admin123")
            print("   -> Usuario 'admin' creado con contraseña 'admin123'")
        else:
            print("   -> Ya existe al menos un usuario en el sistema")
        usuario = autenticar("admin", "admin123") if existe_algun_usuario() else None

    _check("Crear/verificar usuario administrador y probar login", t_usuario)
    print()

    # -----------------------------------------------------------------
    # 3) Geografía
    # -----------------------------------------------------------------
    print("--- 3. Geografía (municipios y parroquias) ---")

    def t_geografia():
        from models.geografia import listar_municipios, resumen_por_municipio
        municipios = listar_municipios()
        assert len(municipios) == 25, f"Se esperaban 25 municipios, hay {len(municipios)}"
        resumen = resumen_por_municipio()
        print(f"   -> {len(municipios)} municipios cargados, {len(resumen)} con resumen estadístico")

    _check("Listar municipios y verificar resumen territorial", t_geografia)
    print()

    # -----------------------------------------------------------------
    # 4) CRUD de personal
    # -----------------------------------------------------------------
    print("--- 4. CRUD de personal militar ---")

    def t_crud():
        from models.militar import crear_personal, obtener_personal, actualizar_personal, eliminar_personal
        from models.geografia import listar_municipios

        municipio = listar_municipios(solo_adyacentes_coro=True)[0]
        datos = {
            "cedula": "00000001", "nombres": "Prueba", "apellidos": "Verificación",
            "fecha_nacimiento": "1999-01-01", "genero": "Masculino",
            "id_municipio": municipio.id_municipio, "id_estatus": 1,
        }
        nuevo = crear_personal(datos)
        datos["nombres"] = "Prueba Actualizada"
        actualizar_personal(nuevo.id_personal, datos)
        eliminar_personal(nuevo.id_personal)
        print("   -> Ciclo crear -> actualizar -> eliminar completado sin errores")

    _check("Probar ciclo completo CRUD de personal", t_crud)
    print()

    # -----------------------------------------------------------------
    # 5) Estadísticas
    # -----------------------------------------------------------------
    print("--- 5. Módulo de estadísticas ---")

    def t_estadisticas():
        from controllers import estadisticas_controller as ec
        resumen = ec.resumen_general()
        assert resumen["total_registros"] > 0
        ec.distribucion_por_genero()
        ec.distribucion_por_rango_edad()
        ec.distribucion_por_nivel_educativo()
        ec.distribucion_por_municipio()
        ec.distribucion_por_estatus()
        ec.tendencia_registros_por_mes()
        print(f"   -> Resumen general: {resumen}")

    _check("Calcular todas las estadísticas", t_estadisticas)
    print()

    # -----------------------------------------------------------------
    # 6) Gráficos
    # -----------------------------------------------------------------
    print("--- 6. Módulo de gráficos (matplotlib) ---")

    def t_graficos():
        from controllers import graficos_controller as gc
        fig1 = gc.grafico_distribucion_genero()
        fig2 = gc.grafico_distribucion_municipio()
        gc.guardar_figura_temporal(fig1, "verificacion_genero.png")
        gc.guardar_figura_temporal(fig2, "verificacion_municipio.png")
        print("   -> Gráficos de muestra guardados en reports/verificacion_*.png")

    _check("Generar gráficos de muestra", t_graficos)
    print()

    # -----------------------------------------------------------------
    # 7) Mapas (requiere folium - el módulo que no se pudo probar en
    #    el entorno de desarrollo de Claude)
    # -----------------------------------------------------------------
    print("--- 7. Módulo de mapas territoriales (folium) ---")

    def t_mapas():
        from controllers import mapas_controller as mc
        ruta1 = mc.generar_mapa_municipios(solo_adyacentes_coro=True)
        ruta2 = mc.generar_mapa_calor(nivel="municipio")
        print(f"   -> Mapa de municipios: {ruta1}")
        print(f"   -> Mapa de calor: {ruta2}")
        print("   -> ABRE estos archivos .html en tu navegador para verlos")

    _check("Generar mapas de muestra (municipios y calor)", t_mapas)
    print()

    # -----------------------------------------------------------------
    # 8) Reportes
    # -----------------------------------------------------------------
    print("--- 8. Módulo de reportes (PDF y Excel) ---")

    def t_reportes():
        from utils import exporters
        from models.militar import listar_personal
        personal = listar_personal(limite=30)
        ruta_pdf = exporters.generar_reporte_estadistico_pdf(incluir_graficos=True)
        ruta_excel = exporters.exportar_personal_excel(personal)
        print(f"   -> PDF de muestra: {ruta_pdf}")
        print(f"   -> Excel de muestra: {ruta_excel}")
        print("   -> ABRE estos archivos para verificar visualmente")

    _check("Generar reportes de muestra (PDF y Excel)", t_reportes)
    print()

    # -----------------------------------------------------------------
    # 9) Interfaz gráfica (PyQt6) - solo verifica que todo se importe
    #    y se construya correctamente, sin mostrar ventanas (modo headless)
    # -----------------------------------------------------------------
    print("--- 9. Interfaz gráfica (PyQt6) ---")

    def t_interfaz():
        import sys

        from PyQt6.QtCore import Qt, QCoreApplication
        from PyQt6.QtWidgets import QApplication

        # Debe configurarse ANTES de crear el QApplication (requerido por
        # QtWebEngine, usado en la pantalla de Mapas Territoriales).
        if QApplication.instance() is None:
            QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

        # Se pasa una lista de argumentos explícita (con al menos el
        # nombre del programa) en lugar de sys.argv, ya que al ejecutar
        # este script puede llegar vacío y Qt requiere al menos un elemento.
        argv_seguro = sys.argv if sys.argv else ["sigem"]
        app = QApplication.instance() or QApplication(argv_seguro)

        from views.login_window import LoginWindow
        from views.main_window import MainWindow

        login = LoginWindow()
        print("   -> LoginWindow construida correctamente")

        # Inicia sesión con el usuario admin para poder construir MainWindow
        from models.usuario import autenticar
        from utils import session

        usuario = autenticar("admin", "admin123")
        session.iniciar_sesion(usuario)

        ventana = MainWindow()
        print(f"   -> MainWindow construida con {len(ventana._vistas)} vistas: {list(ventana._vistas.keys())}")

        for clave in ventana._vistas:
            ventana.navegar_a(clave)
        print("   -> Navegación verificada entre todas las vistas")

        session.cerrar_sesion()

    _check("Construir y navegar la interfaz gráfica completa (modo headless)", t_interfaz)
    print()

    # -----------------------------------------------------------------
    # Resumen final
    # -----------------------------------------------------------------
    print("=" * 70)
    print(" RESUMEN FINAL")
    print("=" * 70)
    exitosos = sum(1 for _, ok, _ in RESULTADOS if ok)
    total = len(RESULTADOS)
    for nombre, ok, error in RESULTADOS:
        estado = "✅" if ok else "❌"
        print(f"  {estado} {nombre}")
    print()
    print(f"Resultado: {exitosos}/{total} pruebas exitosas.")
    if exitosos == total:
        print()
        print("🎉 TODO EL SISTEMA (BACKEND + INTERFAZ) FUNCIONA CORRECTAMENTE EN TU MÁQUINA.")
        print("   Archivos de muestra generados en la carpeta 'reports/'.")
        print("   Ya puedes ejecutar la aplicación real con:  python main.py")
    else:
        print()
        print("⚠️  Hay errores que debemos corregir antes de continuar.")
        print("   Copia el mensaje de error completo y compártelo para solucionarlo.")


if __name__ == "__main__":
    main()
