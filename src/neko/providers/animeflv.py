from __future__ import annotations

"""
providers/animeflv.py — Provider para AnimeFLV (animeflv.net)
Uno de los sitios más completos de anime en español.

Nota técnica:
  - La búsqueda usa scraping HTML (la API interna requiere Cloudflare)
  - Los episodios se extraen del JSON embebido en la página del anime
  - Usa yt-dlp como fallback para resolver streams
"""

import json
import logging
import re

from bs4 import BeautifulSoup

from neko.core.base_provider import BaseProvider
from neko.exceptions import ProviderError, StreamNotFoundError
from neko.utils.http import get_html

logger = logging.getLogger("neko.providers.animeflv")


class AnimeFLV(BaseProvider):
    nombre = "AnimeFLV"
    base_url = "https://www3.animeflv.net"

    def buscar(self, query: str) -> list[dict]:
        url_busqueda = f"{self.base_url}/browse?q={query.replace(' ', '+')}"
        try:
            html = get_html(url_busqueda)
        except Exception as e:
            logger.error("Error buscando en AnimeFLV: %s", e)
            raise ProviderError(f"No se pudo conectar a {self.base_url}", provider=self.nombre, original=e) from e

        soup = BeautifulSoup(html, "html.parser")

        resultados = []

        selectors = [
            "ul.ListAnimes li",
            "div.Container ul.ListAnimes li",
            "section.WdgtCn ul li",
        ]

        for selector in selectors:
            items = soup.select(selector)
            if items:
                for li in items:
                    a = li.find("a", href=True)
                    if not a:
                        continue
                    href = a["href"]
                    titulo_tag = li.find(["h3", "h2", "strong"])
                    titulo = titulo_tag.get_text(strip=True) if titulo_tag else a.get_text(strip=True)

                    if href.startswith("/"):
                        href = self.base_url + href

                    resultados.append(
                        {
                            "titulo": titulo,
                            "url": href,
                            "id": href.split("/")[-1],
                        }
                    )
                break

        return resultados[:20]

    def obtener_episodios(self, anime: dict) -> list[dict]:
        html = get_html(anime["url"])
        soup = BeautifulSoup(html, "html.parser")

        episodios = []

        matches = re.finditer(r"var episodes\s*=\s*(\[.*?\]);", html, re.DOTALL)
        for m in matches:
            try:
                eps_data = json.loads(m.group(1))
                slug = anime["id"]
                for ep in eps_data:
                    num = ep[0]
                    url_ep = f"{self.base_url}/ver/{slug}-{num}"
                    episodios.append(
                        {
                            "titulo": f"Episodio {num}",
                            "url": url_ep,
                            "numero": num,
                        }
                    )
            except json.JSONDecodeError:
                pass

        if not episodios:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/ver/" not in href:
                    continue
                if anime["id"] not in href:
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

        episodios.sort(key=lambda e: e["numero"])
        return episodios

    def obtener_stream(self, episodio: dict) -> str | None:
        try:
            html = get_html(episodio["url"])
        except Exception as e:
            logger.error("Error resolviendo stream de AnimeFLV: %s", e)
            raise StreamNotFoundError("No se pudo resolver stream", provider=self.nombre, original=e) from e

        soup = BeautifulSoup(html, "html.parser")

        matches = re.finditer(r"var videos\s*=\s*(\{.*?\});", html, re.DOTALL)
        for m in matches:
            try:
                videos = json.loads(m.group(1))
                servers = videos.get("SUB", []) or videos.get("LAT", [])
                for server in servers:
                    url_embed = server.get("url") or server.get("code")
                    if url_embed:
                        return url_embed
            except json.JSONDecodeError:
                pass

        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"]
            if src.startswith("//"):
                src = "https:" + src
            return src

        return episodio["url"]
