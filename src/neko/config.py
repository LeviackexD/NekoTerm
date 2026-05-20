"""
src/neko/config.py — Configuración persistente para NekoTerm.
"""

from __future__ import annotations

import json
import logging

from neko.exceptions import ConfigError
from neko.utils.paths import CONFIG_FILE, ensure_data_dirs

logger = logging.getLogger("neko.config")

DEFAULT_CONFIG = {
    "provider": "jkanime",
    "autoplay_next": False,
    "quality": "best",
}


def load_config() -> dict:
    """Carga la configuración desde data/config.json."""
    ensure_data_dirs()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                config = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
        except json.JSONDecodeError as e:
            logger.error("Config corrupta, usando defaults: %s", e)
            return DEFAULT_CONFIG.copy()
        except OSError as e:
            logger.error("No se pudo leer config: %s", e)
            raise ConfigError(f"No se pudo leer {CONFIG_FILE}", original=e) from e
    return DEFAULT_CONFIG.copy()


def save_config(config: dict) -> None:
    """Guarda la configuración en data/config.json."""
    ensure_data_dirs()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_provider() -> str:
    """Devuelve el provider por defecto."""
    return load_config().get("provider", "jkanime")


def set_provider(provider: str) -> None:
    """Establece el provider por defecto."""
    config = load_config()
    config["provider"] = provider
    save_config(config)


def get_autoplay_next() -> bool:
    """Devuelve si se reproduce automáticamente el siguiente episodio."""
    return load_config().get("autoplay_next", False)


def set_autoplay_next(value: bool) -> None:
    """Establece si se reproduce automáticamente el siguiente episodio."""
    config = load_config()
    config["autoplay_next"] = value
    save_config(config)
