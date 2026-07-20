"""
utils/logger.py
================
Sistema de logging estructurado en formato JSON para SIGEM.

Requerimiento Avance #6 (Trazabilidad Avanzada): los logs deben
generarse en formato JSON legible por máquinas, con campos
estandarizados que permitan filtrar y rastrear errores fácilmente.

Cada entrada de log incluye:
- timestamp : fecha y hora ISO 8601
- level     : nivel del log (INFO, WARNING, ERROR, etc.)
- logger    : nombre del módulo que generó el log
- message   : mensaje descriptivo del evento
- extra     : datos adicionales del contexto (opcional)

Uso:
    from utils.logger import get_logger
    logger = get_logger("sigem.mi_modulo")
    logger.info("Operacion completada", extra={"registros": 250})
    logger.error("Error al guardar", extra={"cedula": "12345678"})
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import config


class _FormateadorJSON(logging.Formatter):
    """
    Formateador que convierte cada registro de log en una línea JSON,
    compatible con herramientas de observabilidad (Datadog, Loki, etc.)
    y con el requerimiento de Trazabilidad Avanzada del Avance #6.
    """

    def format(self, record: logging.LogRecord) -> str:
        entrada = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Incluir información de excepción si existe
        if record.exc_info:
            entrada["exception"] = self.formatException(record.exc_info)

        # Incluir campos extra pasados con extra={...}
        campos_reservados = {
            "name", "msg", "args", "levelname", "levelno", "pathname",
            "filename", "module", "exc_info", "exc_text", "stack_info",
            "lineno", "funcName", "created", "msecs", "relativeCreated",
            "thread", "threadName", "processName", "process", "message",
            "taskName",
        }
        extra = {k: v for k, v in record.__dict__.items()
                 if k not in campos_reservados}
        if extra:
            entrada["extra"] = extra

        return json.dumps(entrada, ensure_ascii=False)


def configurar_logging() -> None:
    """
    Configura el sistema de logging global de SIGEM con dos handlers:
    1. Archivo logs/sigem.log → formato JSON (para análisis de máquinas)
    2. Consola stdout        → formato legible (para el desarrollador)
    """
    Path(config.LOGS_DIR).mkdir(parents=True, exist_ok=True)
    ruta_log = Path(config.LOGS_DIR) / "sigem.log"

    logger_raiz = logging.getLogger()
    logger_raiz.setLevel(logging.INFO)

    # Limpiar handlers previos para evitar duplicados al reiniciar
    logger_raiz.handlers.clear()

    # Handler 1: archivo JSON
    handler_archivo = logging.FileHandler(ruta_log, encoding="utf-8")
    handler_archivo.setFormatter(_FormateadorJSON())
    logger_raiz.addHandler(handler_archivo)

    # Handler 2: consola (formato legible para el desarrollador)
    handler_consola = logging.StreamHandler(sys.stdout)
    handler_consola.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
    )
    logger_raiz.addHandler(handler_consola)


def get_logger(nombre: str) -> logging.Logger:
    """
    Retorna un logger con el nombre indicado.
    Usar el patrón 'sigem.modulo' para jerarquía consistente.
    Ejemplo: get_logger("sigem.database"), get_logger("sigem.auth")
    """
    return logging.getLogger(nombre)
