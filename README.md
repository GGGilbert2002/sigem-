# SIGEM — Sistema de Análisis Estadístico y Territorial

**Batallón de Infantería Mecanizada "Cnel. Atanasio Girardot"**  
Coro, Estado Falcón — República Bolivariana de Venezuela

[![CI — Verificación de Código](https://github.com/GGGilbert2002/sigem-/actions/workflows/ci.yml/badge.svg)](https://github.com/GGGilbert2002/sigem-/actions/workflows/ci.yml)

Sistema de escritorio para el análisis estadístico y georreferenciado de la
participación en el servicio militar, desarrollado con Python 3.14 + PyQt6.

---

## Instalación rápida

```bash
# 1. Clonar el repositorio
git clone https://github.com/GGGilbert2002/sigem-.git
cd sigem-

# 2. Instalar dependencias
py -3.14 -m pip install -r requirements.txt

# 3. Ejecutar
py -3.14 main.py
```

**Credenciales por defecto:** usuario `admin` / contraseña `admin123`

---

## Generar documentación técnica

```bash
py -3.14 -m pydoc -b
```

Esto abre un servidor local con la documentación autogenerada de todos
los módulos del proyecto (docstrings en formato Python estándar).

---

## Ejecutar pruebas unitarias

```bash
py -3.14 -m pytest tests/test_sigem.py -v
```

---

## Diagrama de Arquitectura

```mermaid
graph TB
    subgraph UI["Capa de Presentación (PyQt6)"]
        LOGIN[LoginWindow]
        MAIN[MainWindow + Sidebar]
        DASH[DashboardView]
        PERS[PersonalView]
        REG[RegistroView]
        ESTAD[EstadisticasView]
        MAPA[MapaView]
        REP[ReportesView]
    end

    subgraph CTRL["Capa de Controladores"]
        CE[estadisticas_controller]
        CG[graficos_controller]
        CM[mapas_controller]
    end

    subgraph MOD["Capa de Modelos"]
        MM[militar.py]
        MG[geografia.py]
        MU[usuario.py]
    end

    subgraph DATA["Capa de Datos"]
        DB[(SQLite\nsigem.db)]
        GEO[GeoJSON\nFalcón]
    end

    subgraph UTILS["Utilidades"]
        VAL[validators.py]
        SEC[security.py]
        SESS[session.py]
        EXP[exporters.py]
        LOG[logger.py]
    end

    LOGIN --> MU
    MAIN --> DASH & PERS & REG & ESTAD & MAPA & REP
    DASH --> CE & CG
    ESTAD --> CE & CG
    MAPA --> CM
    REP --> EXP
    PERS & REG --> MM & MG
    MM & MG & MU --> DB
    CM --> GEO
    MM --> VAL
    MU --> SEC
    MAIN --> SESS
    DATA --> LOG
```

---

## Diagrama Entidad-Relación

```mermaid
erDiagram
    PERSONAL_MILITAR {
        int id_personal PK
        string cedula UK
        string nombres
        string apellidos
        date fecha_nacimiento
        string genero
        int id_municipio FK
        int id_parroquia FK
        int id_nivel_educativo FK
        int id_grado FK
        int id_estatus FK
        string telefono
        string direccion
        string observaciones
        datetime fecha_registro
    }

    MUNICIPIOS {
        int id_municipio PK
        string nombre
        float latitud
        float longitud
        bool es_adyacente_coro
    }

    PARROQUIAS {
        int id_parroquia PK
        string nombre
        int id_municipio FK
        float latitud
        float longitud
    }

    NIVELES_EDUCATIVOS {
        int id_nivel_educativo PK
        string descripcion
    }

    GRADOS_MILITARES {
        int id_grado PK
        string nombre
        string abreviatura
    }

    ESTATUS_PARTICIPACION {
        int id_estatus PK
        string descripcion
    }

    USUARIOS {
        int id_usuario PK
        string nombre_usuario UK
        string nombre_completo
        string hash_password
        bool activo
        datetime ultimo_acceso
    }

    PERSONAL_MILITAR ||--o{ MUNICIPIOS : "pertenece a"
    PERSONAL_MILITAR ||--o{ PARROQUIAS : "reside en"
    PERSONAL_MILITAR ||--o{ NIVELES_EDUCATIVOS : "tiene"
    PERSONAL_MILITAR ||--o{ GRADOS_MILITARES : "ostenta"
    PERSONAL_MILITAR ||--o{ ESTATUS_PARTICIPACION : "tiene"
    PARROQUIAS ||--o{ MUNICIPIOS : "pertenece a"
```

---

## Diagrama de Caso de Uso

```mermaid
graph LR
    U([Administrador])

    U --> A[Iniciar sesión]
    U --> B[Ver Dashboard]
    U --> C[Gestionar Personal]
    U --> D[Registrar Personal]
    U --> E[Ver Estadísticas]
    U --> F[Ver Mapas Territoriales]
    U --> G[Generar Reportes]
    U --> H[Cerrar sesión]

    C --> C1[Buscar / Filtrar]
    C --> C2[Crear Registro]
    C --> C3[Editar Registro]
    C --> C4[Eliminar Registro]

    F --> F1[Mapa de Municipios]
    F --> F2[Mapa de Parroquias]
    F --> F3[Mapa de Calor]
    F --> F4[Abrir Interactivo en Navegador]

    G --> G1[PDF Estadístico]
    G --> G2[Excel de Personal]
    G --> G3[PDF Listado]
    G --> G4[Excel Resumen]
```

---

## Diagrama de Secuencia — Flujo de Login

```mermaid
sequenceDiagram
    actor Usuario
    participant LW as LoginWindow
    participant MU as models/usuario.py
    participant SEC as utils/security.py
    participant DB as SQLite
    participant SESS as utils/session.py
    participant MW as MainWindow

    Usuario->>LW: Ingresa usuario + contraseña
    LW->>MU: autenticar(usuario, contraseña)
    MU->>DB: SELECT hash_password WHERE nombre_usuario=?
    DB-->>MU: registro del usuario
    MU->>SEC: verify_password(contraseña, hash_almacenado)
    SEC-->>MU: True / False
    alt Credenciales válidas
        MU-->>LW: objeto Usuario
        LW->>SESS: iniciar_sesion(usuario)
        LW->>MW: MainWindow().show()
        LW->>LW: close()
    else Credenciales inválidas
        MU-->>LW: CredencialesInvalidasError
        LW->>Usuario: Mostrar mensaje de error
    end
```

---

## Diagrama de Flujo — Registro de Personal

```mermaid
flowchart TD
    A([Inicio]) --> B[Abrir formulario de registro]
    B --> C[Ingresar datos del personal]
    C --> D{¿Todos los campos\nobligatorios completos?}
    D -- No --> E[Mostrar error de validación]
    E --> C
    D -- Sí --> F{¿Cédula válida?\n6-9 dígitos}
    F -- No --> E
    F -- Sí --> G{¿Fecha nacimiento\n18-60 años?}
    G -- No --> E
    G -- Sí --> H{¿Cédula ya\nexiste en BD?}
    H -- Sí --> I[Mostrar error: cédula duplicada]
    I --> C
    H -- No --> J[Guardar registro en SQLite]
    J --> K[Registrar en log JSON]
    K --> L[Mostrar mensaje de éxito]
    L --> M{¿Registrar\notro?}
    M -- Sí --> N[Limpiar formulario]
    N --> C
    M -- No --> O([Fin])
```

---

## Estructura del Proyecto

```
sigem/
├── main.py                    # Punto de entrada
├── config.py                  # Configuración global
├── requirements.txt            # Dependencias
├── .env.example               # Variables de entorno (plantilla)
├── CONTRIBUTING.md            # Guía de contribución y GitFlow
├── RUNBOOK.md                 # Guía operativa y recuperación ante desastres
├── .github/workflows/ci.yml   # Pipeline CI (GitHub Actions)
├── database/                  # Esquema, conexión, migraciones y seed
├── models/                    # Acceso a datos (militar, geografía, usuario)
├── controllers/               # Lógica de negocio (estadísticas, gráficos, mapas)
├── views/                     # Interfaz gráfica PyQt6
├── utils/                     # Validadores, seguridad, sesión, exportadores, logger
├── tests/                     # Pruebas unitarias (pytest)
├── resources/                 # Datos geográficos (GeoJSON) y assets locales
└── reports/                   # Reportes generados (PDF, Excel, HTML)
```
