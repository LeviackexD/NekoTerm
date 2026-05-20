"""
neko/exceptions.py — Excepciones propias para NekoTerm.

Jerarquía:
    NekoError (base)
    ├── ProviderError          — Provider no responde, sitio caído, cambio de estructura
    ├── StreamNotFoundError    — No se pudo resolver URL de stream
    ├── ConfigError            — Config corrupta o inválida
    └── LibraryError           — Error leyendo/escribiendo biblioteca
"""

from __future__ import annotations


class NekoError(Exception):
    """Excepción base para todos los errores de NekoTerm."""

    def __init__(self, message: str = "", provider: str = "", original: Exception | None = None):
        self.message = message
        self.provider = provider
        self.original = original
        parts = [message]
        if provider:
            parts.insert(0, f"[{provider}]")
        super().__init__(" ".join(parts))


class ProviderError(NekoError):
    """Error específico de un provider (sitio caído, cambio de HTML, etc.)."""

    pass


class StreamNotFoundError(NekoError):
    """No se pudo resolver la URL de stream para un episodio."""

    pass


class ConfigError(NekoError):
    """Error de configuración (archivo corrupto, valor inválido)."""

    pass


class LibraryError(NekoError):
    """Error operando la biblioteca local (favoritos, watch later, series)."""

    pass
