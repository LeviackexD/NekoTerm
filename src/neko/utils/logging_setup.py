"""
utils/logging_setup.py — Configuración de logging para NekoTerm.

Los prints en UI (ui.py, cli/) se mantienen para la interfaz de usuario.
El logging va a stderr para no mezclarse con la UI.
"""

from __future__ import annotations

import logging
import sys

_logger_initialized = False


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configura el logger global de NekoTerm.

    Args:
        debug: Si True, setea nivel DEBUG. Por defecto INFO.

    Returns:
        Logger configurado.
    """
    global _logger_initialized
    if _logger_initialized:
        return logging.getLogger("neko")

    level = logging.DEBUG if debug else logging.INFO

    logger = logging.getLogger("neko")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    formatter = logging.Formatter(
        fmt="[%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    _logger_initialized = True

    return logger


def get_logger(name: str = "neko") -> logging.Logger:
    """Obtiene un logger hijo del namespace 'neko'."""
    return logging.getLogger(name)
