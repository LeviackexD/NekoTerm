from __future__ import annotations

"""
providers/monoschinos.py — Provider para MonosChinos (monoschinos2.com)
Anime sub español, buena calidad y catálogo amplio.

Fallback cuando Jkanime no funciona.
"""

import logging
import re

from bs4 import BeautifulSoup

from neko.core.base_provider import BaseProvider
from neko.exceptions import ProviderError, StreamNotFoundError
from neko.utils.http import get_html

logger = logging.getLogger("neko.providers.monoschinos")


class MonosChinos(BaseProvider):
    nombre = "MonosChinos"
    base_url = "https://monoschinos2.com"

    def buscar(self, query: str) -> list[dict]:
        url = f"{self.base_url}/buscar?q={query.replace(' ', '+')}"
        try:
            html = get_html(url)
        except Exception as e:
            logger.error("Error buscando en MonosChinos: %s", e)
            raise ProviderError(f"No se pudo conectar a {self.base_url}", provider=self.nombre, original=e) from e

        soup = BeautifulSoup(html, "html.parser")

        resultados = []
        query_lower = query.lower()

        selectors = [
            "a[href*='/anime/']",
            "a[href*='/ver/']",
            "div.card a",
            "ul.list a",
        ]

        for _selector in selectors:
            links = soup.find_all("a", href=True)
            matching = [a for a in links if "/anime/" in a["href"]]
            if matching:
                for a in matching:
                    href = a["href"]
                    titulo_raw = a.get_text(strip=True)
                    if not titulo_raw or len(titulo_raw) < 2:
                        continue

                    titulo = re.sub(r"\s*(Anime|Pelicula|Donghua|OVA|ONA|Especial)\s*·?\s*", "", titulo_raw).strip()
                    titulo = re.sub(r"\s*·?\s*\d{4}\s*$", "", titulo).strip()

                    titulo_lower = titulo.lower()
                    url_lower = href.lower()
                    palabras_query = query_lower.split()

                    if not any(palabra in titulo_lower or palabra in url_lower for palabra in palabras_query):
                        continue

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
        slug_base = anime["id"]

        selectors_eps = [
            "a[href*='/ver/']",
            "a[href*='episodio']",
            "ul.episodes a",
        ]

        for _selector in selectors_eps:
            links = soup.find_all("a", href=True)
            matching = [a for a in links if "/ver/" in a["href"]]
            if matching:
                for a in matching:
                    href = a["href"]
                    if slug_base.split("-")[0] not in href:
                        continue

                    m = re.search(r"episodio[- _](\d+)", href, re.IGNORECASE)
                    numero = int(m.group(1)) if m else None

                    texto = a.get_text(strip=True) or f"Episodio {numero or '?'}"

                    if href.startswith("/"):
                        href = self.base_url + href

                    episodios.append(
                        {
                            "titulo": texto if texto else f"Episodio {numero}",
                            "url": href,
                            "numero": numero or 0,
                        }
                    )
                break

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
            logger.error("Error resolviendo stream de MonosChinos: %s", e)
            raise StreamNotFoundError("No se pudo resolver stream", provider=self.nombre, original=e) from e

        soup = BeautifulSoup(html, "html.parser")

        iframes = soup.find_all("iframe", src=True)
        for iframe in iframes:
            src = iframe["src"]
            if src.startswith("//"):
                src = "https:" + src
            if any(p in src for p in ["streamtape", "filemoon", "ok.ru", "dood", "voe"]):
                return src

        for script in soup.find_all("script"):
            texto = script.string or ""
            m = re.search(r'https?://[^\s\'"<>]+\.m3u8[^\s\'"<>]*', texto)
            if m:
                return m.group(0)
            m = re.search(r'https?://[^\s\'"<>]+\.mp4[^\s\'"<>]*', texto)
            if m:
                return m.group(0)

        return episodio["url"]
