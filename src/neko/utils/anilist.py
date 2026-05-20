from __future__ import annotations

"""
utils/anilist.py — Metadatos de anime desde la API pública de AniList.

API GraphQL pública y gratuita: https://graphql.anilist.co
No requiere API key ni registro.
Solo metadatos (títulos, sinopsis, géneros, puntuación) — 100% legal.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request

ANILIST_API = "https://graphql.anilist.co"
MYMEMORY_API = "https://api.mymemory.translated.net/get"


def _traducir_texto(texto: str, max_length: int = 1000) -> str | None:
    """Traduce texto del ingles al espanol usando MyMemory API."""
    if not texto or len(texto) < 3:
        return None

    texto = texto[:max_length]
    try:
        url = f"{MYMEMORY_API}?q={urllib.parse.quote(texto)}&langpair=en|es"
        req = urllib.request.Request(url, headers={"User-Agent": "NekoTerm/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        response_data = data.get("responseData", {})
        translated = response_data.get("translatedText", "")
        if translated and translated != texto:
            return translated
    except Exception:
        pass
    return None


QUERY = """
query ($search: String) {
    Media(search: $search, type: ANIME) {
        id
        title {
            romaji
            english
            native
        }
        episodes
        status
        averageScore
        genres
        description(asHtml: false)
        startDate {
            year
        }
        format
        seasonYear
        coverImage {
            medium
        }
    }
}
"""

QUERY_DISCOVERY = """
query ($page: Int, $perPage: Int, $sort: [MediaSort]) {
    Page(page: $page, perPage: $perPage) {
        media(type: ANIME, sort: $sort) {
            id
            title {
                romaji
                english
                native
            }
            episodes
            status
            averageScore
            genres
            description(asHtml: false)
            startDate {
                year
            }
            format
            seasonYear
            popularity
            trending
        }
    }
}
"""

QUERY_AIRING = """
query ($page: Int, $perPage: Int, $airingAt_greater: Int, $airingAt_lesser: Int) {
    Page(page: $page, perPage: $perPage) {
        airingSchedules(
            sort: [TIME],
            airingAt_greater: $airingAt_greater,
            airingAt_lesser: $airingAt_lesser
        ) {
            airingAt
            episode
            media {
                id
                title {
                    romaji
                    english
                    native
                }
                episodes
                status
                averageScore
                genres
                description(asHtml: false)
                startDate {
                    year
                }
                format
            }
        }
    }
}
"""


def buscar_anilist(titulo: str) -> dict | None:
    """
    Busca metadatos de un anime en AniList.

    Args:
        titulo: Nombre del anime a buscar

    Returns:
        Dict con metadatos o None si no se encuentra o hay error.
    """
    result = _anilist_request(QUERY, {"search": titulo})
    if not result:
        return None

    media = result.get("data", {}).get("Media")
    if not media:
        return None

    return _parse_media(media, traducir=True)


def _anilist_request(query: str, variables: dict | None = None) -> dict | None:
    """Hace una peticion a la API de AniList."""
    try:
        body = json.dumps(
            {
                "query": query,
                "variables": variables or {},
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            ANILIST_API,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "NekoTerm/1.0 (https://github.com/neko-term/neko)",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _parse_media(media: dict, traducir: bool = False) -> dict:
    title = media.get("title", {})
    romaji = title.get("romaji", "")
    english = title.get("english", "")
    native = title.get("native", "")

    sinopsis_en = _limpiar_sinopsis(media.get("description", ""))
    sinopsis_es = None
    if traducir and sinopsis_en:
        sinopsis_es = _traducir_texto(sinopsis_en)
        if not sinopsis_es:
            sinopsis_es = sinopsis_en

    return {
        "titulo_romaji": romaji,
        "titulo_english": english,
        "titulo_native": native,
        "episodios": media.get("episodes") or "?",
        "estado": _traducir_estado(media.get("status", "")),
        "estado_enum": media.get("status", "NOT_YET_RELEASED"),
        "puntuacion": media.get("averageScore"),
        "generos": media.get("genres", []) or [],
        "sinopsis": sinopsis_en,
        "sinopsis_es": sinopsis_es,
        "anio": media.get("startDate", {}).get("year"),
        "formato": media.get("format", ""),
    }


def descubrir_anilist(sort: str = "POPULARITY_DESC", page: int = 1, per_page: int = 20) -> list[dict]:
    """
    Descubre anime por categoria.

    Args:
        sort: Criterio de orden (POPULARITY_DESC, TRENDING_DESC, SCORE_DESC, FAVOURITES_DESC)
        page: Numero de pagina
        per_page: Cantidad de resultados (max 50)

    Returns:
        Lista de dicts con metadatos de anime.
    """
    result = _anilist_request(
        QUERY_DISCOVERY,
        {
            "page": page,
            "perPage": min(per_page, 50),
            "sort": [sort],
        },
    )
    if not result:
        return []

    page_data = result.get("data", {}).get("Page", {})
    media_list = page_data.get("media", [])
    return [_parse_media(m) for m in media_list if m]


def estrenos_semanales(page: int = 1, per_page: int = 20) -> list[dict]:
    """
    Obtiene los estrenos de la semana (airing schedule proximos 7 dias).

    Args:
        page: Numero de pagina
        per_page: Cantidad de resultados

    Returns:
        Lista de dicts con metadatos + fecha de emision y numero de episodio.
    """
    import time

    ahora = int(time.time())
    semana = ahora + (7 * 24 * 60 * 60)

    result = _anilist_request(
        QUERY_AIRING,
        {
            "page": page,
            "perPage": min(per_page, 50),
            "airingAt_greater": ahora,
            "airingAt_lesser": semana,
        },
    )
    if not result:
        return []

    page_data = result.get("data", {}).get("Page", {})
    schedules = page_data.get("airingSchedules", [])
    entradas = []
    for s in schedules:
        media = s.get("media")
        if not media:
            continue
        info = _parse_media(media)
        info["airing_at"] = s.get("airingAt", 0)
        info["episodio_al_aire"] = s.get("episode")
        entradas.append(info)
    return entradas


def _traducir_estado(status: str) -> str:
    estados = {
        "FINISHED": "Finalizado",
        "RELEASING": "En emisión",
        "NOT_YET_RELEASED": "Próximamente",
        "CANCELLED": "Cancelado",
        "HIATUS": "En pausa",
    }
    return estados.get(status, status)


def _limpiar_sinopsis(text: str) -> str:
    """Elimina tags HTML y trunca la sinopsis."""
    limpio = re.sub(r"<[^>]+>", "", text or "")
    limpio = limpio.replace("(Source: Crunchyroll)", "").strip()
    if len(limpio) > 200:
        limpio = limpio[:197] + "..."
    return limpio


def mostrar_info_anilist(ui, info: dict):
    """Muestra la informacion de AniList encuadrada con rich Panel."""
    if not info:
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    console.print()

    titulo_anime = info["titulo_romaji"]
    if info.get("anio") and str(info["anio"]) not in titulo_anime:
        titulo_anime = f"{titulo_anime} ({info['anio']})"
    console.print(Panel(f"📋 {titulo_anime}", border_style="cyan", padding=(0, 1)))

    if info["titulo_english"] and info["titulo_english"] != info["titulo_romaji"]:
        console.print(f"  🇬🇧 {info['titulo_english']}", style="dim")
    if info["titulo_native"]:
        console.print(f"  🇯🇵 {info['titulo_native']}", style="dim")

    console.print()

    partes1 = []
    if info["episodios"] != "?":
        partes1.append(f"📊 {info['episodios']} eps")
    if info["anio"]:
        partes1.append(f"📅 {info['anio']}")
    if info["formato"]:
        partes1.append(f"📺 {info['formato']}")
    console.print("│ " + " │ ".join(partes1) + " │")

    partes2 = []
    if info["puntuacion"]:
        partes2.append(f"⭐ {info['puntuacion']}/100")
    if info["generos"]:
        partes2.append(f"🎭 {', '.join(info['generos'][:3])}")
    if partes2:
        console.print("│ " + " │ ".join(partes2) + " │")

    console.print()

    sinopsis = info.get("sinopsis_es") or info.get("sinopsis") or ""
    if sinopsis:
        console.print(Panel(f"📝 Sinopsis (ES)\n{sinopsis}", border_style="cyan", padding=(1, 2)))

    console.print()
    try:
        input("[Presiona Enter para continuar...]")
    except (KeyboardInterrupt, EOFError):
        print()


def mostrar_descubrimiento(ui, resultados: list[dict], titulo: str, incluir_info_extra: bool = False) -> dict | None:
    """
    Muestra resultados de descubrimiento con fzf y permite seleccionar uno.

    Args:
        ui: Instancia de UI
        resultados: Lista de dicts con metadatos
        titulo: Titulo del menu
        incluir_info_extra: Si True, incluye score y episodios en la etiqueta

    Returns:
        El dict seleccionado o None.
    """
    if not resultados:
        ui.error("No hay resultados.")
        return None

    def label_fn(anime):
        partes = [anime["titulo_romaji"]]
        if incluir_info_extra:
            if anime["puntuacion"]:
                partes.append(f"⭐{anime['puntuacion']}")
            if anime["episodios"] != "?":
                partes.append(f"[{anime['episodios']}eps]")
            else:
                partes.append("[?eps]")
        return "  ".join(partes)

    return ui.seleccionar(titulo, resultados, label_fn)
