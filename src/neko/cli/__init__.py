#!/usr/bin/env python3
"""
neko/cli/ — CLI principal de NekoTerm.
Entry point, argument parsing y menú principal.
"""

from __future__ import annotations

import argparse
import logging

from neko.cli.modes import (
    modo_biblioteca,
    modo_busqueda,
    modo_continuar,
    modo_descubrir,
    modo_favoritos,
    modo_providers,
    modo_watch_later,
)
from neko.config import get_provider, load_config
from neko.core.ui import UI
from neko.providers.animeflv import AnimeFLV
from neko.providers.jkanime import JKanime
from neko.providers.monoschinos import MonosChinos
from neko.providers.tioanime import TioAnime
from neko.utils.logging_setup import setup_logging

logger = logging.getLogger("neko.cli")

PROVIDERS = {
    "jkanime": JKanime(),
    "monoschinos": MonosChinos(),
    "animeflv": AnimeFLV(),
    "tioanime": TioAnime(),
}

PROVIDER_ORDER = ["jkanime", "tioanime", "monoschinos", "animeflv"]


def verificar_salud_provider(key: str, provider) -> bool:
    """Verifica si un provider responde. Retorna True si está sano."""
    logger.debug("Verificando salud de %s (%s)...", key, provider.base_url)
    return provider.salud()


def obtener_provider_sano(preferido: str) -> tuple[str, str | None]:
    """Busca un provider que responda. Retorna (key_proveedor, fallback_de).

    Si el preferido funciona, retorna (preferido, None).
    Si no, prueba en orden y retorna (primero_sano, preferido).
    Si ninguno funciona, retorna (preferido, None).
    """
    if verificar_salud_provider(preferido, PROVIDERS[preferido]):
        return preferido, None

    logger.warning("Provider '%s' no responde, buscando fallback...", preferido)
    for key in PROVIDER_ORDER:
        if key == preferido:
            continue
        if key in PROVIDERS and verificar_salud_provider(key, PROVIDERS[key]):
            logger.info("Fallback: usando '%s' en lugar de '%s'", key, preferido)
            return key, preferido

    logger.error("Ningún provider responde")
    return preferido, None


def main():
    config = load_config()
    default_provider = config.get("provider", "jkanime")

    parser = argparse.ArgumentParser(
        prog="neko",
        description="🐱 NekoTerm — Anime en español desde tu terminal",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("busqueda", nargs="?", help="Término de búsqueda")
    parser.add_argument(
        "-p",
        "--provider",
        default=default_provider,
        choices=list(PROVIDERS.keys()),
        help=f"Fuente a usar (default: {default_provider})",
    )
    parser.add_argument(
        "-l",
        "--lista-providers",
        action="store_true",
        help="Listar providers disponibles",
    )
    parser.add_argument(
        "-c",
        "--continue",
        dest="continuar",
        action="store_true",
        help="Continuar desde el último episodio visto",
    )
    parser.add_argument(
        "-e",
        "--episode",
        "--range",
        dest="episodio",
        type=str,
        help="Episodio o rango (ej: 5, 1-12, 5-)",
    )
    parser.add_argument(
        "--skip",
        action="store_true",
        help="Saltar OP/ED automáticamente (requiere ani-skip)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=str,
        default="best",
        help="Calidad (best, 1080p, 720p, 480p, 360p)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Modo debug: muestra logs detallados en stderr",
    )
    args = parser.parse_args()

    setup_logging(debug=args.debug)

    ui = UI()

    if args.lista_providers:
        ui.titulo("Providers disponibles")
        for nombre, p in PROVIDERS.items():
            sano = "✅" if p.salud() else "❌"
            ui.info(f"  {sano} {nombre} → {p.base_url}")
        return

    if args.continuar:
        provider_key, fallback_de = obtener_provider_sano(args.provider)
        if fallback_de:
            ui.warning(f"'{args.provider}' no responde, usando '{provider_key}'")
        provider = PROVIDERS[provider_key]
        modo_continuar(ui, provider)
        return

    if args.busqueda:
        provider_key, fallback_de = obtener_provider_sano(args.provider)
        if fallback_de:
            ui.warning(f"'{args.provider}' no responde, usando '{provider_key}'")
        provider = PROVIDERS[provider_key]
        ui.titulo(f"NEKOTERM [{provider_key}]")
        modo_busqueda(ui, provider, args.busqueda, args.episodio, args.skip, args.quality)
        return

    while True:
        opcion = ui.menu_principal()
        provider_key, fallback_de = obtener_provider_sano(get_provider())
        if fallback_de:
            ui.warning(f"Provider por defecto no responde, usando '{provider_key}'")
        active_provider = PROVIDERS[provider_key]

        if opcion == "0":
            ui.info("¡Hasta luego! 🐱")
            break
        elif opcion == "1":
            modo_busqueda(ui, active_provider, episodio_range=args.episodio, skip=args.skip, quality=args.quality)
        elif opcion == "2":
            modo_biblioteca(ui, active_provider, skip=args.skip, quality=args.quality)
        elif opcion == "3":
            modo_favoritos(ui, active_provider, skip=args.skip, quality=args.quality)
        elif opcion == "4":
            modo_watch_later(ui, active_provider, skip=args.skip, quality=args.quality)
        elif opcion == "5":
            modo_descubrir(ui, active_provider, skip=args.skip, quality=args.quality)
        elif opcion == "6":
            modo_providers(ui, PROVIDERS)


if __name__ == "__main__":
    main()
