from __future__ import annotations

"""
providers/tioanime.py — Provider para TioAnime (tioanime.com)
Anime sub español, buena calidad y catálogo amplio.

Estructura técnica:
  - Búsqueda: /directorio?q=query (HTML scraping)
  - Episodios: /anime/{slug} → parsea `var episodes = [1,2,3...]` del HTML
  - Stream: /ver/{slug}-{ep} → parsea `var videos = [["server","url"],...]`
  - Sin Cloudflare agresivo — más estable que AnimeFLV
"""

import json
import logging
import re

from bs4 import BeautifulSoup

from neko.core.base_provider import BaseProvider
from neko.exceptions import ProviderError, StreamNotFoundError
from neko.utils.http import get_html

logger = logging.getLogger("neko.providers.tioanime")


class TioAnime(BaseProvider):
    nombre = "TioAnime"
    base_url = "https://tioanime.com"

    def buscar(self, query: str) -> list[dict]:
        url = f"{self.base_url}/directorio?q={query.replace(' ', '+')}"
        try:
            html = get_html(url)
        except Exception as e:
            logger.error("Error buscando en TioAnime: %s", e)
            raise ProviderError(f"No se pudo conectar a {self.base_url}", provider=self.nombre, original=e) from e

        soup = BeautifulSoup(html, "html.parser")

        resultados = []

        selectors = [
            "ul.animes li article a",
            "div.row main ul li article a",
            "ul.list-unstyled li article a",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for a in items:
                    href = a.get("href", "")
                    if "/anime/" not in href:
                        continue

                    titulo_tag = a.select_one("h3.title")
                    titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""

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
        html = get_html(anime["url"])
        soup = BeautifulSoup(html, "html.parser")

        episodios = []
        slug = anime["id"]

        matches = re.finditer(r"var episodes\s*=\s*(\[.*?\]);", html, re.DOTALL)
        for m in matches:
            try:
                eps_data = json.loads(m.group(1))
                for ep_num in eps_data:
                    if isinstance(ep_num, (int, float)):
                        ep_num = int(ep_num)
                        ep_url = f"{self.base_url}/ver/{slug}-{ep_num}"
                        episodios.append(
                            {
                                "titulo": f"Episodio {ep_num}",
                                "url": ep_url,
                                "numero": ep_num,
                            }
                        )
            except json.JSONDecodeError:
                pass

        if not episodios:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/ver/" not in href:
                    continue
                if slug.split("-")[0] not in href:
                    continue

                m = re.search(r"ver/.*?-(\d+)", href)
                numero = int(m.group(1)) if m else None

                if numero:
                    if href.startswith("/"):
                        href = self.base_url + href
                    episodios.append(
                        {
                            "titulo": f"Episodio {numero}",
                            "url": href,
                            "numero": numero,
                        }
                    )

        vistos = set()
        unicos = []
        for ep in episodios:
            if ep["url"] not in vistos:
                vistos.add(ep["url"])
                unicos.append(ep)

        unicos.sort(key=lambda e: e["numero"])
        return unicos

    def obtener_stream(self, episodio: dict) -> str | None:
        try:
            html = get_html(episodio["url"])
        except Exception as e:
            logger.error("Error resolviendo stream de TioAnime: %s", e)
            raise StreamNotFoundError("No se pudo resolver stream", provider=self.nombre, original=e) from e

        soup = BeautifulSoup(html, "html.parser")

        matches = re.finditer(r"var videos\s*=\s*(\[.*?\]);", html, re.DOTALL)
        for m in matches:
            try:
                videos = json.loads(m.group(1))
                for video in videos:
                    if isinstance(video, (list, tuple)) and len(video) >= 2:
                        server = video[0]
                        url = video[1]
                        if any(
                            s in server.lower()
                            for s in ["streamtape", "filemoon", "ok.ru", "dood", "voe", "mega", "yourupload"]
                        ):
                            return url
            except json.JSONDecodeError:
                pass

        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"]
            if src.startswith("//"):
                src = "https:" + src
            if any(p in src for p in ["streamtape", "filemoon", "ok.ru", "dood", "voe"]):
                return src

        for match in re.finditer(r'https?://[^\s\'"<>]+\.(?:mp4|m3u8)[^\s\'"<>]*', html):
            return match.group(0)

        return episodio["url"]
