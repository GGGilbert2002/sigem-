-- =====================================================================
-- SIGEM - Sistema de Análisis Estadístico y Territorial de Participación
-- y Reclutamiento del Servicio Militar - Coro, Edo. Falcón
-- Esquema de Base de Datos (SQLite)
-- =====================================================================
-- Basado en el Cuadro de Operacionalización de Variables (Capítulo II):
--   - Datos demográficos: edad, género, nivel educativo
--   - Datos territoriales: municipio, parroquia
--   - Participación / reclutamiento en el servicio militar
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- TABLA: municipios
-- Jerarquía territorial nivel 1 (Estado Falcón -> Municipios)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS municipios (
    id_municipio    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    capital         TEXT,
    latitud         REAL,                       -- centroide aproximado (para mapas)
    longitud        REAL,
    es_adyacente_coro INTEGER NOT NULL DEFAULT 0 -- 1 = municipio cercano a Coro (alcance del estudio)
);

-- ---------------------------------------------------------------------
-- TABLA: parroquias
-- Jerarquía territorial nivel 2 (Municipio -> Parroquias)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS parroquias (
    id_parroquia    INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    id_municipio    INTEGER NOT NULL,
    latitud         REAL,
    longitud         REAL,
    FOREIGN KEY (id_municipio) REFERENCES municipios(id_municipio) ON DELETE CASCADE,
    UNIQUE (nombre, id_municipio)
);

-- ---------------------------------------------------------------------
-- TABLA: niveles_educativos  (catálogo controlado, evita texto libre)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS niveles_educativos (
    id_nivel_educativo INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion         TEXT NOT NULL UNIQUE
);

-- ---------------------------------------------------------------------
-- TABLA: grados_militares (catálogo)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS grados_militares (
    id_grado        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    categoria       TEXT NOT NULL CHECK (categoria IN ('Tropa Profesional','Sub-Oficial','Oficial','Conscripto/Alistado'))
);

-- ---------------------------------------------------------------------
-- TABLA: componentes (catálogo: a qué proceso pertenece el registro)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS estatus_participacion (
    id_estatus      INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion     TEXT NOT NULL UNIQUE   -- Ej: Registrado, Alistado, Incorporado, Rechazado, Diferido
);

-- ---------------------------------------------------------------------
-- TABLA: personal_militar
-- Tabla central: registros de participación / reclutamiento
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS personal_militar (
    id_personal         INTEGER PRIMARY KEY AUTOINCREMENT,
    cedula              TEXT NOT NULL UNIQUE,
    nombres             TEXT NOT NULL,
    apellidos           TEXT NOT NULL,
    fecha_nacimiento    TEXT NOT NULL,           -- ISO 8601 'YYYY-MM-DD'
    genero              TEXT NOT NULL CHECK (genero IN ('Masculino','Femenino')),
    id_nivel_educativo  INTEGER,
    id_grado            INTEGER,
    id_municipio        INTEGER NOT NULL,
    id_parroquia        INTEGER,
    id_estatus          INTEGER NOT NULL,
    fecha_registro      TEXT NOT NULL,           -- fecha en que se registró/incorporó
    unidad              TEXT DEFAULT 'Batallón de Infantería Mecanizada Cnel. Atanasio Girardot',
    telefono            TEXT,
    direccion           TEXT,
    observaciones       TEXT,
    creado_en           TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    actualizado_en      TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (id_nivel_educativo) REFERENCES niveles_educativos(id_nivel_educativo),
    FOREIGN KEY (id_grado) REFERENCES grados_militares(id_grado),
    FOREIGN KEY (id_municipio) REFERENCES municipios(id_municipio),
    FOREIGN KEY (id_parroquia) REFERENCES parroquias(id_parroquia),
    FOREIGN KEY (id_estatus) REFERENCES estatus_participacion(id_estatus)
);

CREATE INDEX IF NOT EXISTS idx_personal_municipio ON personal_militar(id_municipio);
CREATE INDEX IF NOT EXISTS idx_personal_parroquia ON personal_militar(id_parroquia);
CREATE INDEX IF NOT EXISTS idx_personal_genero ON personal_militar(genero);
CREATE INDEX IF NOT EXISTS idx_personal_estatus ON personal_militar(id_estatus);
CREATE INDEX IF NOT EXISTS idx_personal_fecha_registro ON personal_militar(fecha_registro);

-- ---------------------------------------------------------------------
-- TABLA: usuarios (acceso simple al sistema, sin roles)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_usuario  TEXT NOT NULL UNIQUE,
    nombre_completo TEXT NOT NULL,
    password_hash   TEXT NOT NULL,           -- hash + salt (nunca texto plano)
    activo          INTEGER NOT NULL DEFAULT 1,
    creado_en       TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    ultimo_acceso   TEXT
);

-- ---------------------------------------------------------------------
-- TABLA: auditoria (trazabilidad básica de acciones - opcional pero recomendable)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS auditoria (
    id_log          INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario      INTEGER,
    accion          TEXT NOT NULL,
    detalle         TEXT,
    fecha           TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
);

-- ---------------------------------------------------------------------
-- VISTA: resumen por municipio (acelera consultas de dashboard/mapas)
-- ---------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_resumen_municipio AS
SELECT
    m.id_municipio,
    m.nombre AS municipio,
    m.latitud,
    m.longitud,
    COUNT(p.id_personal)                                            AS total_registros,
    SUM(CASE WHEN p.genero = 'Masculino' THEN 1 ELSE 0 END)         AS total_masculino,
    SUM(CASE WHEN p.genero = 'Femenino' THEN 1 ELSE 0 END)          AS total_femenino
FROM municipios m
LEFT JOIN personal_militar p ON p.id_municipio = m.id_municipio
GROUP BY m.id_municipio, m.nombre, m.latitud, m.longitud;

-- ---------------------------------------------------------------------
-- VISTA: resumen por parroquia
-- ---------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS vw_resumen_parroquia AS
SELECT
    pq.id_parroquia,
    pq.nombre AS parroquia,
    m.id_municipio,
    m.nombre AS municipio,
    pq.latitud,
    pq.longitud,
    COUNT(p.id_personal) AS total_registros
FROM parroquias pq
JOIN municipios m ON m.id_municipio = pq.id_municipio
LEFT JOIN personal_militar p ON p.id_parroquia = pq.id_parroquia
GROUP BY pq.id_parroquia, pq.nombre, m.id_municipio, m.nombre, pq.latitud, pq.longitud;
