"""Tests para neko/utils/http.py."""

import time
from unittest.mock import MagicMock, patch

import pytest

from neko.utils import http as http_module


@pytest.fixture(autouse=True)
def reset_cache():
    http_module.clear_cache()
    yield
    http_module.clear_cache()


def test_get_html_returns_html():
    mock_resp = MagicMock()
    mock_resp.text = "<html>test</html>"
    mock_resp.raise_for_status = MagicMock()

    with patch.object(http_module.SESSION, "get", return_value=mock_resp) as mock_get:
        result = http_module.get_html("https://example.com", use_cache=False)
        assert result == "<html>test</html>"
        mock_get.assert_called_once()


def test_get_json_returns_dict():
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"key": "value"}
    mock_resp.raise_for_status = MagicMock()

    with patch.object(http_module.SESSION, "get", return_value=mock_resp):
        result = http_module.get_json("https://example.com/api")
        assert result == {"key": "value"}


def test_cache_hit():
    mock_resp = MagicMock()
    mock_resp.text = "<html>cached</html>"
    mock_resp.raise_for_status = MagicMock()

    with patch.object(http_module.SESSION, "get", return_value=mock_resp) as mock_get:
        first = http_module.get_html("https://example.com")
        second = http_module.get_html("https://example.com")
        assert first == second
        assert mock_get.call_count == 1


def test_cache_miss_after_clear():
    mock_resp1 = MagicMock()
    mock_resp1.text = "<html>v1</html>"
    mock_resp1.raise_for_status = MagicMock()

    mock_resp2 = MagicMock()
    mock_resp2.text = "<html>v2</html>"
    mock_resp2.raise_for_status = MagicMock()

    with patch.object(http_module.SESSION, "get", side_effect=[mock_resp1, mock_resp2]):
        http_module.get_html("https://example.com")
        http_module.clear_cache()
        result = http_module.get_html("https://example.com")
        assert result == "<html>v2</html>"


def test_retry_on_failure():
    fail_resp = MagicMock()
    fail_resp.raise_for_status.side_effect = Exception("timeout")

    ok_resp = MagicMock()
    ok_resp.text = "<html>ok</html>"
    ok_resp.raise_for_status = MagicMock()

    with patch.object(http_module.SESSION, "get", side_effect=[fail_resp, ok_resp]):
        result = http_module.get_html("https://example.com", retries=3, use_cache=False)
        assert result == "<html>ok</html>"


def test_raises_after_max_retries():
    fail_resp = MagicMock()
    fail_resp.raise_for_status.side_effect = Exception("server error")

    with patch.object(http_module.SESSION, "get", side_effect=[fail_resp, fail_resp, fail_resp]):
        with pytest.raises(Exception):
            http_module.get_html("https://example.com", retries=3, use_cache=False)


def test_referer_header():
    mock_resp = MagicMock()
    mock_resp.text = "ok"
    mock_resp.raise_for_status = MagicMock()

    with patch.object(http_module.SESSION, "get", return_value=mock_resp) as mock_get:
        http_module.get_html("https://example.com", referer="https://referrer.com", use_cache=False)
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["headers"]["Referer"] == "https://referrer.com"


def test_clear_cache():
    http_module._cache["test"] = ("data", time.time())
    http_module.clear_cache()
    assert len(http_module._cache) == 0
