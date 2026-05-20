"""Tests para neko/core/library.py."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from neko.core import library


@pytest.fixture
def tmp_data(tmp_path):
    """Redirect all data paths to a temporary directory."""
    series_file = tmp_path / "series.json"
    favoritos_file = tmp_path / "favoritos.txt"
    watch_later_dir = tmp_path / "watch_later"
    watch_later_dir.mkdir()

    patches = [
        patch("neko.core.library.SERIES_FILE", series_file),
        patch("neko.core.library.FAVORITOS_FILE", favoritos_file),
        patch("neko.core.library.WATCH_LATER_DIR", watch_later_dir),
        patch("neko.core.library.ensure_data_dirs"),
    ]
    for p in patches:
        p.start()

    yield {
        "series": series_file,
        "favoritos": favoritos_file,
        "watch_later": watch_later_dir,
    }

    for p in patches:
        p.stop()


def test_guardar_y_obtener_series(tmp_data):
    library.guardar_serie({"titulo": "Naruto", "url": "https://example.com/naruto"}, "jkanime")
    series = library.obtener_series()
    assert len(series) == 1
    assert series[0]["titulo"] == "Naruto"
    assert series[0]["provider"] == "jkanime"


def test_no_duplicados_series(tmp_data):
    anime = {"titulo": "Naruto", "url": "https://example.com/naruto"}
    library.guardar_serie(anime, "jkanime")
    library.guardar_serie(anime, "jkanime")
    series = library.obtener_series()
    assert len(series) == 1


def test_eliminar_serie(tmp_data):
    library.guardar_serie({"titulo": "Naruto", "url": "https://example.com/naruto"}, "jkanime")
    library.eliminar_serie("https://example.com/naruto")
    assert library.obtener_series() == []


def test_toggle_favorito(tmp_data):
    anime = {"titulo": "Naruto", "url": "https://example.com/naruto"}
    assert library.toggle_favorito(anime) is True
    assert library.es_favorito("https://example.com/naruto") is True
    assert library.toggle_favorito(anime) is False
    assert library.es_favorito("https://example.com/naruto") is False


def test_obtener_favoritos(tmp_data):
    anime = {"titulo": "Naruto", "url": "https://example.com/naruto"}
    library.toggle_favorito(anime)
    favs = library.obtener_favoritos()
    assert len(favs) == 1
    assert favs[0]["titulo"] == "Naruto"


def test_watch_later(tmp_data):
    library.guardar_posicion("Naruto - Ep.1", 120.5)
    pos = library.obtener_posicion("Naruto - Ep.1")
    assert pos == 120.5


def test_obtener_watch_later(tmp_data):
    library.guardar_posicion("Naruto - Ep.1", 120.5)
    library.guardar_posicion("One Piece - Ep.5", 300.0)
    entradas = library.obtener_watch_later()
    assert len(entradas) == 2


def test_eliminar_watch_later(tmp_data):
    library.guardar_posicion("Naruto - Ep.1", 120.5)
    library.eliminar_watch_later("Naruto - Ep.1")
    assert library.obtener_posicion("Naruto - Ep.1") is None
