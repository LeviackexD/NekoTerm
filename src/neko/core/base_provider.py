from __future__ import annotations

"""
core/base_provider.py — Clase base que deben implementar todos los providers.

Cada provider es responsable de:
  1. buscar(query)         → lista de animes
  2. obtener_episodios(anime) → lista de episodios
  3. obtener_stream(episodio) → URL directa del video
  4. salud()               → verifica si el sitio responde
"""

from abc import ABC, abstractmethod

from neko.utils.http import get_html


class BaseProvider(ABC):
    """Interfaz mínima que debe cumplir cualquier provider."""

    nombre: str = "base"
    base_url: str = ""

    # Headers comunes para evitar bloqueos básicos
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "es-ES,es;q=0.9",
    }

    def salud(self, timeout: int = 10) -> bool:
        """Verifica si el sitio del provider responde. Override si necesita check específico."""
        try:
            get_html(self.base_url, timeout=timeout, retries=1, use_cache=False)
            return True
        except Exception:
            return False

    @abstractmethod
    def buscar(self, query: str) -> list[dict]:
        """
        Busca animes por nombre.
        Devuelve lista de dicts con al menos: {titulo, url, id}
        """

    @abstractmethod
    def obtener_episodios(self, anime: dict) -> list[dict]:
        """
        Dado un anime (con su url/id), obtiene su lista de episodios.
        Devuelve lista de dicts: {titulo, url, numero}
        """

    @abstractmethod
    def obtener_stream(self, episodio: dict) -> str | None:
        """
        Dado un episodio, resuelve la URL directa del video (m3u8, mp4...).
        Devuelve str o None si no se pudo resolver.
        """
