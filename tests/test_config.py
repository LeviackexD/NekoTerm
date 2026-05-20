"""Tests para neko/config.py."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from neko.config import DEFAULT_CONFIG, load_config, save_config


@pytest.fixture
def tmp_config(tmp_path):
    """Redirect config paths to a temporary directory."""
    config_file = tmp_path / "config.json"
    with patch("neko.config.CONFIG_FILE", config_file):
        with patch("neko.config.ensure_data_dirs"):
            yield config_file


def test_load_default_when_no_file(tmp_path):
    config_file = tmp_path / "config.json"
    with patch("neko.config.CONFIG_FILE", config_file):
        with patch("neko.config.ensure_data_dirs"):
            config = load_config()
            assert config == DEFAULT_CONFIG


def test_load_existing_config(tmp_config):
    tmp_config.write_text(json.dumps({"provider": "tioanime", "quality": "720p"}))
    config = load_config()
    assert config["provider"] == "tioanime"
    assert config["quality"] == "720p"
    assert "autoplay_next" in config


def test_save_and_load(tmp_config):
    save_config({"provider": "allanime", "autoplay_next": True})
    config = load_config()
    assert config["provider"] == "allanime"
    assert config["autoplay_next"] is True


def test_corrupt_config_returns_defaults(tmp_config):
    tmp_config.write_text("{bad json}")
    config = load_config()
    assert config == DEFAULT_CONFIG


def test_missing_keys_get_defaults(tmp_config):
    tmp_config.write_text(json.dumps({"provider": "jkanime"}))
    config = load_config()
    assert config["provider"] == "jkanime"
    assert config["autoplay_next"] is False
    assert config["quality"] == "best"
