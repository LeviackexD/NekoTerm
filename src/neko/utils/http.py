from __future__ import annotations

"""
utils/http.py — Peticiones HTTP con curl_cffi para bypass Cloudflare.

Features:
  - Cache HTTP con TTL configurable (evita re-scrapear la misma URL)
  - Retry con backoff exponencial (3 intentos por defecto)
  - curl_cffi usa TLS fingerprinting de Chrome real
"""

import time

from curl_cffi import requests

from neko.utils.logging_setup import get_logger

logger = get_logger("neko.http")

# Sesión con fingerprint de Chrome
SESSION: requests.Session = requests.Session(impersonate="chrome")
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }
)

# Cache simple: {url: (html, timestamp)}
_cache: dict[str, tuple[str, float]] = {}
CACHE_TTL = 300  # 5 minutos
CACHE_MAX = 50


def _cache_get(url: str) -> str | None:
    if url in _cache:
        html, ts = _cache[url]
        if time.time() - ts < CACHE_TTL:
            return html
        del _cache[url]
    return None


def _cache_set(url: str, html: str):
    if len(_cache) >= CACHE_MAX:
        oldest = min(_cache, key=lambda k: _cache[k][1])
        del _cache[oldest]
    _cache[url] = (html, time.time())


def get_html(url: str, referer: str = "", timeout: int = 20, retries: int = 3, use_cache: bool = True) -> str:
    """
    Hace GET y devuelve HTML con retry y cache.

    Args:
        url: URL a solicitar
        referer: Header Referer
        timeout: Timeout en segundos
        retries: Intentos con backoff exponencial
        use_cache: Si True, usa cache para evitar re-scrapear
    """
    if use_cache:
        cached = _cache_get(url)
        if cached is not None:
            return cached

    headers = {}
    if referer:
        headers["Referer"] = referer

    last_error: Exception = RuntimeError("Unknown error")
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            html = resp.text
            if use_cache:
                _cache_set(url, html)
            return html
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                delay = 1 * (2**attempt)
                logger.debug("Reintento %d/%d para %s (%s)", attempt + 1, retries, url, e)
                time.sleep(delay)

    logger.error("Falló GET %s tras %d intentos: %s", url, retries, last_error)
    raise last_error


def get_json(url: str, referer: str = "", timeout: int = 15, retries: int = 3) -> dict:
    """Hace GET y devuelve JSON con retry."""
    headers = {}
    if referer:
        headers["Referer"] = referer

    last_error: Exception = RuntimeError("Unknown error")
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                delay = 1 * (2**attempt)
                logger.debug("Reintento %d/%d para %s (%s)", attempt + 1, retries, url, e)
                time.sleep(delay)

    logger.error("Falló GET JSON %s tras %d intentos: %s", url, retries, last_error)
    raise last_error


def clear_cache():
    """Limpia el cache HTTP."""
    _cache.clear()
