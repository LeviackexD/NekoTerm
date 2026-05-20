from __future__ import annotations

"""
providers/jkanime.py — Provider para Jkanime (jkanime.bz)
Fuente principal de anime con subtítulos en español.

Basado en el scraping de AniCli-Cast original:
  - Búsqueda: /buscar/query/
  - Episodios: API AJAX con CSRF token
  - Servers: Página del episodio + yt-dlp
"""

import logging
import re

from bs4 import BeautifulSoup

from neko.core.base_provider import BaseProvider
from neko.exceptions import ProviderError, StreamNotFoundError
from neko.utils.http import SESSION, get_html

logger = logging.getLogger("neko.providers.jkanime")


class JKanime(BaseProvider):
    nombre = "Jkanime"
    base_url = "https://jkanime.bz"

    def _get_csrf_token(self, url: str) -> str | None:
        html = get_html(url)
        soup = BeautifulSoup(html, "html.parser")
        meta = soup.find("meta", attrs={"name": "csrf-token"})
        return meta.get("content") if meta else None

    def _get_anime_id(self, url: str) -> str | None:
        html = get_html(url)
        m = re.search(r"ajax/episodes/(\d+)", html)
        return m.group(1) if m else None

    def buscar(self, query: str) -> list[dict]:
        url = f"{self.base_url}/buscar/{query.replace(' ', '%20')}/"
        try:
            html = get_html(url)
        except Exception as e:
            logger.error("Error buscando en Jkanime: %s", e)
            raise ProviderError(f"No se pudo conectar a {self.base_url}", provider=self.nombre, original=e) from e

        soup = BeautifulSoup(html, "html.parser")

        resultados = []

        selectors = [
            ".anime__item__text h5 a",
            ".item a.title",
            "a[href*='/anime/'] h5",
            "ul.animes li a",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for a in items:
                    titulo = a.get_text(strip=True)
                    href = a.get("href", "")

                    if not titulo or len(titulo) < 2:
                        continue

                    if href.startswith("/"):
                        href = self.base_url + href

                    resultados.append(
                        {
                            "titulo": titulo,
                            "url": href,
                            "id": href.rstrip("/").split("/")[-1],
                        }
                    )
                break

        vistos = set()
        unicos = []
        for r in resultados:
            if r["url"] not in vistos:
                vistos.add(r["url"])
                unicos.append(r)

        return unicos[:20]

    def obtener_episodios(self, anime: dict) -> list[dict]:
        csrf_token = self._get_csrf_token(anime["url"])
        anime_id = self._get_anime_id(anime["url"])

        if not csrf_token or not anime_id:
            logger.warning("No se pudo obtener CSRF/anime ID para %s", anime["url"])
            raise ProviderError("No se pudo obtener token CSRF o ID", provider=self.nombre)

        api_url = f"{self.base_url}/ajax/episodes/{anime_id}/"
        try:
            resp = SESSION.post(
                api_url,
                headers={
                    "X-CSRF-TOKEN": csrf_token,
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": anime["url"],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("Error obteniendo episodios de Jkanime: %s", e)
            raise ProviderError("Error al obtener episodios", provider=self.nombre, original=e) from e

        episodios = []
        for ep in data.get("data", []):
            slug = anime["url"].rstrip("/").split("/")[-1]
            ep_url = f"{self.base_url}/{slug}/{ep['number']}/"
            episodios.append(
                {
                    "titulo": ep.get("title", f"Episodio {ep.get('number', '?')}"),
                    "url": ep_url,
                    "numero": ep.get("number", 0),
                    "id": ep.get("id"),
                }
            )

        episodios.sort(key=lambda e: e["numero"])
        return episodios

    def obtener_stream(self, episodio: dict) -> str | None:
        url_ep = episodio["url"]

        try:
            html = get_html(url_ep)

            m = re.search(r'<iframe[^>]+src="(https://jkanime\.bz/jkplayer/[^"]+)"', html)
            if m:
                player_url = m.group(1)
                player_html = get_html(player_url, referer=url_ep)
                m2 = re.search(r"url:\s*['\"](https?://[^\s'\"]+\.m3u8[^\s'\"]*)['\"]", player_html)
                if m2:
                    return m2.group(1)

            soup = BeautifulSoup(html, "html.parser")
            for iframe in soup.find_all("iframe", src=True):
                src = iframe["src"]
                if src.startswith("//"):
                    src = "https:" + src
                if any(p in src for p in ["streamtape", "filemoon", "ok.ru", "dood", "voe"]):
                    return src

            for match in re.finditer(r'https?://[^\s\'"<>]+\.(?:mp4|m3u8)[^\s\'"<>]*', html):
                return match.group(0)
        except Exception as e:
            logger.error("Error resolviendo stream de Jkanime: %s", e)
            raise StreamNotFoundError("No se pudo resolver stream", provider=self.nombre, original=e) from e

        return None
