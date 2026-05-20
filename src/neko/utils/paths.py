"""
utils/paths.py — Rutas de datos centralizadas para NekoTerm.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SERIES_FILE = DATA_DIR / "series.json"
FAVORITOS_FILE = DATA_DIR / "favoritos.txt"
WATCH_LATER_DIR = DATA_DIR / "watch_later"
CONFIG_FILE = DATA_DIR / "config.json"


def ensure_data_dirs() -> None:
    """Crea los directorios de datos si no existen."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    WATCH_LATER_DIR.mkdir(parents=True, exist_ok=True)
    if not FAVORITOS_FILE.exists():
        FAVORITOS_FILE.touch()
