"""Tests para neko/exceptions.py."""

from neko.exceptions import ConfigError, LibraryError, NekoError, ProviderError, StreamNotFoundError


def test_neko_error_basic():
    err = NekoError("algo falló")
    assert str(err) == "algo falló"
    assert err.message == "algo falló"
    assert err.provider == ""
    assert err.original is None


def test_neko_error_with_provider():
    err = NekoError("no responde", provider="Jkanime")
    assert "[Jkanime]" in str(err)
    assert err.provider == "Jkanime"


def test_neko_error_with_original():
    original = ValueError("bad value")
    err = NekoError("falló", original=original)
    assert err.original is original


def test_provider_error():
    err = ProviderError("sitio caído", provider="MonosChinos")
    assert isinstance(err, NekoError)
    assert "MonosChinos" in str(err)


def test_stream_not_found_error():
    err = StreamNotFoundError("no hay stream", provider="TioAnime")
    assert isinstance(err, NekoError)
    assert "TioAnime" in str(err)


def test_config_error():
    err = ConfigError("config corrupta")
    assert isinstance(err, NekoError)


def test_library_error():
    err = LibraryError("no se pudo leer")
    assert isinstance(err, NekoError)


def test_exception_hierarchy():
    assert issubclass(ProviderError, NekoError)
    assert issubclass(StreamNotFoundError, NekoError)
    assert issubclass(ConfigError, NekoError)
    assert issubclass(LibraryError, NekoError)
    assert issubclass(NekoError, Exception)
