from __future__ import annotations

"""
core/library.py — Gestiona la biblioteca local, favoritos y watch later.

Todo se reproduce en tiempo real (streaming).
No se descarga ni almacena contenido con derechos de autor.
"""

import json
import logging
from datetime import datetime

from neko.exceptions import LibraryError
from neko.utils.helpers import titulo_a_hash
from neko.utils.paths import FAVORITOS_FILE, SERIES_FILE, WATCH_LATER_DIR, ensure_data_dirs

logger = logging.getLogger("neko.library")


def _load_json_list(filepath) -> list[dict]:
    if filepath.exists():
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Error leyendo %s: %s", filepath, e)
            raise LibraryError(f"No se pudo leer {filepath}", original=e) from e
    return []


def _save_json(filepath, data: list | dict) -> None:
    ensure_data_dirs()
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        logger.error("Error guardando %s: %s", filepath, e)
        raise LibraryError(f"No se pudo guardar {filepath}", original=e) from e


# --- BIBLIOTECA LOCAL ---


def guardar_serie(anime: dict, provider: str = "") -> None:
    """Guarda una serie en la biblioteca local."""
    series = _load_json_list(SERIES_FILE)

    for s in series:
        if s.get("url") == anime.get("url"):
            return

    series.append(
        {
            "titulo": anime.get("titulo", ""),
            "url": anime.get("url", ""),
            "provider": provider,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
        }
    )
    _save_json(SERIES_FILE, series)


def obtener_series() -> list[dict]:
    """Devuelve todas las series guardadas."""
    return _load_json_list(SERIES_FILE)


def eliminar_serie(url: str) -> None:
    """Elimina una serie de la biblioteca."""
    series = _load_json_list(SERIES_FILE)
    series = [s for s in series if s.get("url") != url]
    _save_json(SERIES_FILE, series)


def obtener_serie_por_url(url: str) -> dict | None:
    """Busca una serie por su URL."""
    for s in obtener_series():
        if s.get("url") == url:
            return s
    return None


# --- FAVORITOS ---


def toggle_favorito(anime: dict) -> bool:
    """Añade o quita un anime de favoritos. Devuelve True si se añadió."""
    ensure_data_dirs()
    favoritos = []
    if FAVORITOS_FILE.exists():
        favoritos = FAVORITOS_FILE.read_text(encoding="utf-8").splitlines()

    url = anime.get("url", "")
    titulo = anime.get("titulo", "")

    for i, fav in enumerate(favoritos):
        if url in fav:
            favoritos.pop(i)
            FAVORITOS_FILE.write_text("\n".join(favoritos) + "\n", encoding="utf-8")
            return False

    favoritos.append(f"{titulo} | {url}")
    FAVORITOS_FILE.write_text("\n".join(favoritos) + "\n", encoding="utf-8")
    return True


def es_favorito(url: str) -> bool:
    """Comprueba si un anime está en favoritos."""
    if not FAVORITOS_FILE.exists():
        return False
    return url in FAVORITOS_FILE.read_text(encoding="utf-8")


def obtener_favoritos() -> list[dict]:
    """Devuelve todos los favoritos."""
    if not FAVORITOS_FILE.exists():
        return []

    favoritos = []
    for linea in FAVORITOS_FILE.read_text(encoding="utf-8").splitlines():
        if "|" in linea:
            titulo, url = linea.rsplit(" | ", 1)
            favoritos.append({"titulo": titulo.strip(), "url": url.strip()})
    return favoritos


# --- WATCH LATER ---


def guardar_posicion(titulo: str, posicion: float) -> None:
    """Guarda la posición de reproducción con título legible."""
    ensure_data_dirs()
    filename = titulo_a_hash(titulo) + ".json"
    filepath = WATCH_LATER_DIR / filename
    data = {
        "titulo": titulo,
        "posicion": posicion,
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def obtener_posicion(titulo: str) -> float | None:
    """Devuelve la posición guardada o None."""
    ensure_data_dirs()
    filename = titulo_a_hash(titulo) + ".json"
    filepath = WATCH_LATER_DIR / filename
    if filepath.exists():
        try:
            with open(filepath) as f:
                data = json.load(f)
                return data.get("posicion")
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    return None


def obtener_watch_later() -> list[dict]:
    """Devuelve todas las entradas del watch later con títulos legibles."""
    ensure_data_dirs()
    entradas = []
    for pos_file in WATCH_LATER_DIR.glob("*.json"):
        try:
            with open(pos_file) as f:
                data = json.load(f)
            entradas.append(
                {
                    "titulo": data.get("titulo", pos_file.stem),
                    "posicion": data.get("posicion", 0),
                    "fecha": data.get("fecha", ""),
                    "archivo": pos_file,
                }
            )
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    entradas.sort(key=lambda e: e.get("fecha", ""), reverse=True)
    return entradas


def eliminar_watch_later(titulo: str) -> None:
    """Elimina una entrada del watch later."""
    ensure_data_dirs()
    filename = titulo_a_hash(titulo) + ".json"
    filepath = WATCH_LATER_DIR / filename
    if filepath.exists():
        filepath.unlink()


def limpiar_watch_later_antiguo() -> None:
    """Elimina archivos .pos antiguos del sistema anterior."""
    ensure_data_dirs()
    for pos_file in WATCH_LATER_DIR.glob("*.pos"):
        pos_file.unlink()
