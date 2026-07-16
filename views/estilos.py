"""
views/estilos.py
=================
Hoja de estilos QSS (el "CSS" de Qt) centralizada para toda la
aplicación. Mantenerla en un solo lugar garantiza consistencia visual
en todas las pantallas y evita repetir colores/medidas por todo el
código (coherente con la paleta validada en el wireframe: verde
institucional + dorado).
"""

import config

QSS_GLOBAL = f"""
/* =================== BASE =================== */
QWidget {{
    background-color: {config.COLOR_FONDO};
    color: #333333;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {config.COLOR_FONDO};
}}

/* =================== SIDEBAR =================== */
QWidget#sidebar {{
    background-color: {config.COLOR_PRIMARIO};
    min-width: 220px;
    max-width: 220px;
}}

QLabel#sidebarNombre {{
    color: white;
    font-size: 14px;
    font-weight: 700;
}}

QLabel#sidebarUnidad {{
    color: rgba(255, 255, 255, 0.65);
    font-size: 10px;
}}

QLabel#sidebarUsuario {{
    color: rgba(255, 255, 255, 0.75);
    font-size: 11px;
}}

QPushButton#navItem {{
    background-color: transparent;
    color: rgba(255, 255, 255, 0.85);
    text-align: left;
    padding: 11px 20px;
    border: none;
    border-left: 3px solid transparent;
    font-size: 13px;
}}

QPushButton#navItem:hover {{
    background-color: rgba(255, 255, 255, 0.08);
}}

QPushButton#navItem:checked {{
    background-color: rgba(255, 255, 255, 0.12);
    border-left: 3px solid {config.COLOR_ACENTO};
    color: white;
    font-weight: 600;
}}

QPushButton#btnCerrarSesion {{
    background: transparent;
    color: {config.COLOR_ACENTO};
    border: none;
    text-align: left;
    font-size: 11px;
    padding: 4px 0;
}}
QPushButton#btnCerrarSesion:hover {{
    text-decoration: underline;
}}

/* =================== TÍTULOS Y TEXTO =================== */
QLabel#tituloVista {{
    color: {config.COLOR_PRIMARIO};
    font-size: 19px;
    font-weight: 700;
}}

QLabel#subtituloVista {{
    color: #999999;
    font-size: 12px;
}}

QLabel#seccionTitulo {{
    color: {config.COLOR_PRIMARIO};
    font-size: 13px;
    font-weight: 700;
}}

/* =================== TARJETAS KPI =================== */
QFrame.kpiCard {{
    background-color: white;
    border: 1px solid {config.COLOR_FONDO};
    border-top: 3px solid {config.COLOR_SECUNDARIO};
    border-radius: 6px;
}}

QLabel.kpiValor {{
    color: {config.COLOR_PRIMARIO};
    font-size: 24px;
    font-weight: 700;
}}

QLabel.kpiLabel {{
    color: #888888;
    font-size: 11px;
}}

/* =================== PANELES =================== */
QFrame.panel {{
    background-color: white;
    border: 1px solid #DDDDDD;
    border-radius: 8px;
}}

/* =================== BOTONES =================== */
QPushButton {{
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 12.5px;
}}

QPushButton#btnPrimario {{
    background-color: {config.COLOR_PRIMARIO};
    color: white;
    font-weight: 600;
    border: none;
}}
QPushButton#btnPrimario:hover {{
    background-color: {config.COLOR_SECUNDARIO};
}}
QPushButton#btnPrimario:pressed {{
    background-color: #0F2A1D;
}}
QPushButton#btnPrimario:disabled {{
    background-color: #A8A8A8;
}}

QPushButton#btnSecundario {{
    background-color: white;
    color: #444444;
    border: 1px solid #CCCCCC;
}}
QPushButton#btnSecundario:hover {{
    background-color: #F0F0F0;
}}
QPushButton#btnSecundario:checked {{
    background-color: {config.COLOR_PRIMARIO};
    color: white;
    border: 1px solid {config.COLOR_PRIMARIO};
}}

QPushButton#btnPeligro {{
    background-color: white;
    color: #A32D2D;
    border: 1px solid #E0B4B4;
}}
QPushButton#btnPeligro:hover {{
    background-color: #FBE3E3;
}}

/* =================== CAMPOS DE ENTRADA =================== */
QLineEdit, QComboBox, QDateEdit, QSpinBox {{
    background-color: white;
    border: 1px solid #CCCCCC;
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 12.5px;
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 1px solid {config.COLOR_SECUNDARIO};
}}

QLineEdit#inputLogin {{
    padding: 10px 12px;
    font-size: 13px;
}}

/* =================== TABLAS =================== */
QTableWidget {{
    background-color: white;
    border: 1px solid #DDDDDD;
    border-radius: 6px;
    gridline-color: #EEEEEE;
    selection-background-color: #DCEFE3;
    selection-color: #1B1B1B;
}}

QHeaderView::section {{
    background-color: {config.COLOR_PRIMARIO};
    color: white;
    padding: 8px;
    border: none;
    font-weight: 600;
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 4px;
}}

/* =================== TARJETAS DE LOGIN =================== */
QFrame#loginCard {{
    background-color: white;
    border-radius: 10px;
}}

QLabel#loginEscudo {{
    background-color: {config.COLOR_ACENTO};
    border-radius: 32px;
    color: {config.COLOR_PRIMARIO};
    font-size: 26px;
    font-weight: 700;
}}

QLabel#loginTitulo {{
    color: {config.COLOR_PRIMARIO};
    font-size: 17px;
    font-weight: 700;
}}

QLabel#loginSubtitulo {{
    color: #888888;
    font-size: 11px;
}}

QLabel#loginError {{
    color: #A32D2D;
    font-size: 11.5px;
}}

/* =================== SCROLLBARS =================== */
QScrollBar:vertical {{
    background: {config.COLOR_FONDO};
    width: 10px;
}}
QScrollBar::handle:vertical {{
    background: #C8C8C0;
    border-radius: 5px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: #A8A8A0;
}}

/* =================== TOOLBAR / BARRA DE BÚSQUEDA =================== */
QFrame#barraHerramientas {{
    background-color: transparent;
}}

/* =================== BADGES DE ESTATUS (usados vía QSS dinámico) === */
QLabel.badgeOk {{
    background-color: #E3F3EA;
    color: {config.COLOR_PRIMARIO};
    border-radius: 9px;
    padding: 2px 9px;
    font-size: 10.5px;
    font-weight: 600;
}}
QLabel.badgeWarn {{
    background-color: #FBF0D8;
    color: #8A6D11;
    border-radius: 9px;
    padding: 2px 9px;
    font-size: 10.5px;
    font-weight: 600;
}}
QLabel.badgeBad {{
    background-color: #FBE3E3;
    color: #A32D2D;
    border-radius: 9px;
    padding: 2px 9px;
    font-size: 10.5px;
    font-weight: 600;
}}
"""
