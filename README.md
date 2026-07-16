# SIGEM
### Sistema de Análisis Estadístico y Territorial de Participación y Reclutamiento Militar
**Batallón de Infantería Mecanizada "Cnel. Atanasio Girardot" — Coro, Estado Falcón**

---

## ⚙️ Instalación (Windows / Linux / macOS)

### 1. Requisitos previos
- Python 3.10 o superior instalado ([python.org](https://www.python.org/downloads/))
- Conexión a internet (solo para la instalación inicial de librerías)

### 2. Instalar las dependencias directamente
```bash
cd sigem
pip install -r requirements.txt
```

Esto instalará: PyQt6, pandas, numpy, matplotlib, folium, branca, openpyxl, reportlab, pyinstaller, directamente en tu instalación de Python (sin entorno virtual).

> Si `pip install` falla en alguna librería, dime exactamente el mensaje de error y lo resolvemos juntos — puede variar según tu sistema operativo.

> Si tu sistema usa `python3` y `pip3` en lugar de `python` y `pip` (común en Linux/macOS), usa: `pip3 install -r requirements.txt`

---

## ✅ PASO OBLIGATORIO: Verificar que todo funciona

**Antes de usar la aplicación, ejecuta este script de verificación:**

```bash
python tests/verificar_backend.py
```

Este script:
1. Crea la base de datos SQLite desde cero (si no existe).
2. Carga los 25 municipios reales de Falcón, sus parroquias, catálogos, y 250 registros ficticios de personal (para que puedas probar el sistema mientras consigues los datos reales del batallón).
3. Prueba **todos** los módulos del sistema: usuarios, personal, estadísticas, gráficos, mapas, reportes, **y la interfaz gráfica completa** (construcción de ventanas y navegación, en modo silencioso/headless).
4. Genera archivos de muestra en la carpeta `reports/` para que los abras y revises visualmente.

Si ves `🎉 TODO EL SISTEMA (BACKEND + INTERFAZ) FUNCIONA CORRECTAMENTE EN TU MÁQUINA` al final, todo está listo.

Si aparece algún ❌, copia el mensaje de error completo y lo corregimos antes de seguir.

---

## 🚀 Ejecutar la aplicación

Una vez verificado que todo funciona, abre la aplicación real con:

```bash
python main.py
```

Se abrirá la ventana de inicio de sesión. Usa las credenciales por defecto:
- **Usuario:** `admin`
- **Contraseña:** `admin123`

Tras iniciar sesión, navega usando el menú lateral: Dashboard, Gestión de Personal, Estadísticas, Mapas Territoriales, Reportes.

> La primera vez que ejecutes `main.py` (o el script de verificación), el sistema crea automáticamente la base de datos con los 25 municipios reales y 250 registros ficticios de personal, para que puedas probar todo de inmediato. Cuando tengas los datos reales del batallón, puedes eliminar los registros ficticios desde la pantalla de Gestión de Personal, o pídeme que te ayude a hacer una carga masiva desde Excel.

---

## 📁 Estructura del proyecto

```
sigem/
├── main.py                         # Punto de entrada de la aplicación
├── config.py                       # Configuración global (rutas, colores, parámetros)
├── requirements.txt                # Dependencias del proyecto
├── database/
│   ├── schema.sql                   # Definición de tablas (DDL)
│   ├── connection.py                 # Conexión y manejo de transacciones
│   ├── migrations.py                 # Sistema de migraciones (evolución del esquema)
│   └── seed_data.py                  # Datos iniciales (municipios reales + datos ficticios)
├── models/
│   ├── militar.py                    # CRUD de personal militar
│   ├── geografia.py                  # Municipios y parroquias
│   └── usuario.py                    # Login y gestión de usuarios
├── controllers/
│   ├── estadisticas_controller.py    # Cálculos estadísticos (pandas)
│   ├── graficos_controller.py        # Generación de gráficos (matplotlib)
│   └── mapas_controller.py           # Mapas territoriales (folium)
├── views/
│   ├── estilos.py                     # Hoja de estilos QSS centralizada
│   ├── login_window.py                # Ventana de inicio de sesión
│   ├── main_window.py                 # Ventana principal con sidebar de navegación
│   ├── dashboard_view.py              # Pantalla de Dashboard (KPIs + gráficos)
│   ├── personal_view.py               # Pantalla de Gestión de Personal (tabla CRUD)
│   ├── personal_form_dialog.py        # Formulario modal de creación/edición
│   ├── estadisticas_view.py           # Pantalla de Estadísticas (gráficos)
│   ├── mapa_view.py                   # Pantalla de Mapas Territoriales
│   └── reportes_view.py               # Pantalla de Reportes (exportación)
├── utils/
│   ├── validators.py                  # Validaciones de datos de entrada
│   ├── security.py                    # Hash seguro de contraseñas
│   ├── session.py                     # Gestor de sesión del usuario actual
│   └── exporters.py                   # Exportación a PDF y Excel
├── tests/
│   └── verificar_backend.py          # Script de verificación integral
└── reports/                          # Carpeta donde se generan los reportes (vacía al inicio)
```

---

## 🔑 Usuario por defecto

Tras ejecutar `verificar_backend.py`, se crea automáticamente:
- **Usuario:** `admin`
- **Contraseña:** `admin123`

(Podrás cambiar esta contraseña desde la propia aplicación una vez tengamos la interfaz lista.)

---

## 📌 Estado actual del proyecto

- ✅ Base de datos y modelos: **completo y verificado**
- ✅ Estadísticas y gráficos: **completo y verificado**
- ✅ Mapas territoriales: **completo y verificado visualmente**
- ✅ Reportes PDF/Excel: **completo y verificado**
- ✅ Interfaz gráfica (PyQt6): **completa — login, dashboard, gestión de personal, estadísticas, mapas, reportes**
- ⏳ Siguiente paso: que ejecutes `python main.py` y revisemos juntos cualquier detalle visual o de usabilidad

---

## ❓ Si algo falla

Copia el mensaje de error completo (incluyendo el "Traceback") y compártelo. No intentes interpretar el error tú mismo primero — lo revisamos juntos.
