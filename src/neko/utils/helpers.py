"""
utils/helpers.py — Funciones auxiliares compartidas.
"""

from __future__ import annotations

import hashlib


def titulo_a_hash(titulo: str) -> str:
    """Convierte un título a hash MD5 para nombre de archivo."""
    return hashlib.md5(titulo.encode()).hexdigest()
