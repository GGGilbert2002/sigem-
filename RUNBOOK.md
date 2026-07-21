# RUNBOOK.md — Guía Operativa de SIGEM

**Sistema:** SIGEM — Sistema de Análisis Estadístico y Territorial  
**Unidad:** Batallón de Infantería Mecanizada "Cnel. Atanasio Girardot" — Coro, Edo. Falcón  
**Versión:** 1.0.0  
**Último mantenimiento:** Julio 2026

> Este documento es la guía de primeros auxilios del sistema. Ante cualquier
> incidente, seguir los pasos en orden sin improvisar.

---

## FASE #1 — DIAGNÓSTICO: Verificar el estado del sistema

### 1.1 Verificar que el sistema arranca correctamente

```bash
cd C:\Users\USUARIO\Downloads\sigem
py -3.14 main.py
```

**Resultado esperado en consola:**
```
[INFO] sigem.main: Iniciando SIGEM v1.0.0
[INFO] sigem.database: Base de datos inicializada correctamente en ...
[INFO] sigem.migrations: Base de datos al día (versión X).
```

Si **no aparece** alguna de estas líneas, pasar a la sección correspondiente.

---

### 1.2 Verificar integridad de la base de datos

```bash
py -3.14 -c "
from database.connection import get_connection
conn = get_connection()
tablas = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print('Tablas encontradas:', [t['name'] for t in tablas])
conn.close()
"
```

**Resultado esperado:** lista con al menos 9 tablas (personal_militar, municipios, parroquias, usuarios, etc.)

---

### 1.3 Verificar que las pruebas unitarias pasan

```bash
py -3.14 -m pytest tests/test_sigem.py -v
```

**Resultado esperado:** `28 passed` sin ningún FAILED.

---

### 1.4 Verificar los logs del sistema

Los logs se guardan en `logs/sigem.log`. Para ver los últimos 50 eventos:

```bash
py -3.14 -c "
import json
with open('logs/sigem.log', encoding='utf-8') as f:
    lineas = f.readlines()
for linea in lineas[-50:]:
    print(linea.strip())
"
```

---

### 1.5 Verificar dependencias instaladas

```bash
py -3.14 -m pip check
py -3.14 -c "import PyQt6; import pandas; import matplotlib; import folium; print('Dependencias OK')"
```

---

## FASE #2 — PROTOCOLO ANTE CAÍDAS

### Nivel L1 — Usuario final (sin conocimientos técnicos)

**Síntoma:** La aplicación no abre o se cierra sola.

**Pasos:**
1. Cerrar completamente la aplicación (verificar en el Administrador de Tareas que no haya procesos `python.exe` activos).
2. Reiniciar la computadora.
3. Volver a ejecutar `py -3.14 main.py`.
4. Si el problema persiste, escalar a L2.

---

### Nivel L2 — Administrador del sistema

**Síntoma:** Error en consola al iniciar, base de datos corrupta, o módulo no encontrado.

**Paso A — Error de módulo no encontrado:**
```bash
cd C:\Users\USUARIO\Downloads\sigem
py -3.14 -m pip install -r requirements.txt
py -3.14 main.py
```

**Paso B — Base de datos corrupta o esquema desactualizado:**
```bash
# ADVERTENCIA: esto elimina todos los datos. Hacer backup primero (ver Fase 3).
del database\sigem.db
py -3.14 main.py
# El sistema recrea la BD automáticamente al arrancar.
```

**Paso C — Error de permisos en Windows:**
```bash
# Ejecutar CMD como Administrador y repetir el comando de arranque.
py -3.14 main.py
```

**Paso D — Verificar logs de error:**
```bash
type logs\sigem.log | findstr "ERROR"
```

Si ningún paso L2 resuelve el problema, escalar a L3.

---

### Nivel L3 — Desarrollador / Soporte técnico avanzado

**Síntoma:** Fallo persistente no resuelto por L1/L2, error en pipeline CI, o corrupción total.

**Paso A — Restaurar desde el repositorio de GitHub:**
```bash
git status
git stash
git pull origin main
py -3.14 -m pip install -r requirements.txt
py -3.14 main.py
```

**Paso B — Revisar historial de cambios recientes:**
```bash
git log --oneline -10
```

Si un commit reciente rompió el sistema, revertirlo:
```bash
git revert HEAD --no-edit
git push
```

**Paso C — Restauración completa desde cero (ver Fase 3).**

---

## FASE #3 — RECUPERACIÓN ANTE DESASTRES

> Se aplica cuando hay corrupción total de datos o pérdida completa del sistema.
> Sigue la **regla 3-2-1 de respaldos**:
> - **3** copias de los datos
> - **2** en medios distintos (disco local + repositorio GitHub)
> - **1** fuera del sitio (GitHub / almacenamiento en la nube)

---

### 3.1 Procedimiento de backup manual (antes de cualquier cambio de riesgo)

```bash
cd C:\Users\USUARIO\Downloads\sigem

# 1. Copiar la base de datos con timestamp
copy database\sigem.db database\sigem_backup_%date:~-4,4%%date:~-7,2%%date:~0,2%.db

# 2. Subir todo al repositorio (la BD está en .gitignore — solo el código)
git add .
git commit -m "chore: backup previo a mantenimiento"
git push
```

---

### 3.2 Restauración completa desde cero

**Escenario:** computadora nueva o corrupción total del directorio del proyecto.

```bash
# Paso 1: Clonar el repositorio desde GitHub
git clone https://github.com/GGGilbert2002/sigem-.git
cd sigem-

# Paso 2: Instalar Python 3.14 desde python.org (si no está instalado)
# Descargar desde: https://www.python.org/downloads/

# Paso 3: Instalar todas las dependencias
py -3.14 -m pip install -r requirements.txt

# Paso 4: Descargar recursos locales de Leaflet (para los mapas)
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js' -OutFile 'resources\leaflet\leaflet.js'"
powershell -Command "Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css' -OutFile 'resources\leaflet\leaflet.css'"

# Paso 5: Ejecutar el sistema (crea la BD automáticamente)
py -3.14 main.py
```

**Resultado esperado:** El sistema arranca con la BD recién creada y datos semilla cargados (municipios reales de Falcón + 250 registros ficticios de prueba).

---

### 3.3 Restaurar datos reales desde backup

Si existe un archivo de backup de la base de datos:

```bash
# Detener la aplicación primero.
# Copiar el backup sobre la BD activa:
copy database\sigem_backup_YYYYMMDD.db database\sigem.db

# Verificar integridad:
py -3.14 -c "
from database.connection import get_connection
conn = get_connection()
total = conn.execute('SELECT COUNT(*) as c FROM personal_militar').fetchone()['c']
print(f'Registros restaurados: {total}')
conn.close()
"
```

---

## Contacto de soporte

| Rol | Responsable |
|-----|-------------|
| Desarrollador principal | Gilberto Freitez — GitHub: @GGGilbert2002 |
| Repositorio | https://github.com/GGGilbert2002/sigem- |
| Documentación técnica | README.md + CONTRIBUTING.md en el repositorio |
