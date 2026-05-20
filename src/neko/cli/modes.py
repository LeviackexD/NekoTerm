from __future__ import annotations

"""
cli/modes.py — Modos de operación y loop de reproducción.
"""

import logging
import select
import sys
import termios
import threading
import time
import tty

from neko.config import load_config, set_provider
from neko.core.library import (
    es_favorito,
    guardar_serie,
    obtener_posicion,
    obtener_series,
    obtener_watch_later,
    toggle_favorito,
)
from neko.core.player import (
    ANI_SKIP_DISPONIBLE,
    mpv_guardar_posicion,
    mpv_matar,
    obtener_ani_skip_args,
    obtener_calidades,
    reproducir,
    reproducir_background,
)
from neko.core.ui import UI, Colores, menu_seleccionar
from neko.exceptions import ProviderError, StreamNotFoundError
from neko.utils.anilist import (
    buscar_anilist,
    descubrir_anilist,
    estrenos_semanales,
    mostrar_descubrimiento,
    mostrar_info_anilist,
)

logger = logging.getLogger("neko.cli.modes")

ATAJOS_HINT = f"  {Colores.DIM}[n] siguiente  [p] anterior  [r] repetir  [q] salir{Colores.RESET}"


def _leer_tecla_no_bloqueante() -> str | None:
    """Lee una tecla sin bloquear. Retorna la tecla o None si no hay input."""
    if not sys.stdin.isatty():
        return None
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
        if ready:
            ch = sys.stdin.read(1)
            return ch if ch else None
    except (OSError, termios.error, ValueError):
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return None


def _obtener_episodios_vistos(anime_url: str) -> set:
    """Retorna un set de URLs de episodios ya vistos para un anime."""
    series = obtener_series()
    vistos = set()
    for s in series:
        if s.get("url") == anime_url:
            vistos.add(s.get("url", ""))
    entradas = obtener_watch_later()
    for e in entradas:
        vistos.add(e.get("titulo", ""))
    return vistos


def _parse_episodio_range(range_str: str, total_eps: int) -> list[int]:
    """Parse rango como '1-12', '5', '5-', '-12'. Retorna lista de números 1-based."""
    range_str = range_str.strip()
    if "-" in range_str:
        parts = range_str.split("-", 1)
        start = int(parts[0]) if parts[0] else 1
        end = int(parts[1]) if parts[1] else total_eps
        return list(range(start, end + 1))
    else:
        return [int(range_str)]


# --- MENÚS ---


def _menu_duracion(anime: dict, episodios: list, idx_actual: int, ui: UI) -> str | None:
    """Menú durante reproducción. Retorna acción o None."""
    ui._refresh()
    acciones = []
    if idx_actual < len(episodios) - 1:
        acciones.append(("next", f"▶  Siguiente (Ep.{episodios[idx_actual + 1].get('numero', '?')})"))
    if idx_actual > 0:
        acciones.append(("prev", f"◀  Anterior (Ep.{episodios[idx_actual - 1].get('numero', '?')})"))
    acciones.append(("replay", "🔄  Repetir episodio"))
    acciones.append(("quality", "🎨  Cambiar calidad"))
    acciones.append(("select", "📺  Seleccionar episodio"))

    opciones = [(str(i), desc) for i, (_, desc) in enumerate(acciones, 1)]
    opciones.append(("0", "⏹  Salir"))

    accion_map = {str(i): acc for i, (acc, _) in enumerate(acciones, 1)}
    accion_map["0"] = "quit"

    ep_num = episodios[idx_actual].get("numero", "?")
    print(f"  {Colores.DIM}[Esc] Volver al menú principal{Colores.RESET}")
    result = menu_seleccionar(f"📺 {anime['titulo']} · Ep.{ep_num}", opciones)
    if result is None:
        return None
    return accion_map.get(result)


def _menu_post_playback(episodios: list, idx_actual: int, ui: UI) -> str | None:
    """Menú después de que mpv cierra naturalmente."""
    ui._refresh()
    acciones = []
    if idx_actual < len(episodios) - 1:
        acciones.append(("next", f"▶  Siguiente episodio (Ep.{episodios[idx_actual + 1].get('numero', '?')})"))
    if idx_actual > 0:
        acciones.append(("prev", f"◀  Episodio anterior (Ep.{episodios[idx_actual - 1].get('numero', '?')})"))
    acciones.append(("replay", "🔄  Repetir episodio"))
    acciones.append(("select", "📺  Seleccionar episodio"))

    opciones = [(str(i), desc) for i, (_, desc) in enumerate(acciones, 1)]
    opciones.append(("0", "⏹  Salir"))

    accion_map = {str(i): acc for i, (acc, _) in enumerate(acciones, 1)}
    accion_map["0"] = "quit"

    print(f"  {Colores.DIM}[Esc] Volver al menú principal{Colores.RESET}")
    result = menu_seleccionar("📺 Playback finalizado", opciones)
    if result is None:
        return None
    return accion_map.get(result)


def _menu_acciones(prompt: str, acciones: list[tuple[str, str]]) -> str | None:
    """Menú de acciones con fzf. Retorna el id de la acción o None."""
    opciones = [(str(i), desc) for i, (_, desc) in enumerate(acciones, 1)]
    opciones.append(("0", "⏹  Volver"))
    accion_map = {str(i): acc for i, (acc, _) in enumerate(acciones, 1)}
    accion_map["0"] = "volver"
    print(f"  {Colores.DIM}[Esc] Volver atrás{Colores.RESET}")
    result = menu_seleccionar(prompt, opciones)
    if result is None:
        return None
    return accion_map.get(result)


# --- FLUJO COMÚN ---


def _continuar_con_anime(ui: UI, provider, anime: dict, skip: bool = False, quality: str = "best") -> None:
    """Flujo comun: cargar episodios y reproducir."""
    ya_fav = es_favorito(anime.get("url", ""))
    if ya_fav:
        ui.info(f"⭐ '{anime['titulo']}' ya esta en favoritos")
    else:
        resp = ui.preguntar("⭐ Añadir a favoritos? (y/n)")
        if resp.lower() in ("y", "s", "si", "sí"):
            añadido = toggle_favorito(anime)
            if añadido:
                ui.exito(f"Añadido a favoritos: {anime['titulo']}")
            else:
                ui.info(f"Eliminado de favoritos: {anime['titulo']}")

    ui.info(f"Cargando episodios de '{anime['titulo']}'...")
    try:
        episodios = provider.obtener_episodios(anime)
    except Exception as e:
        ui.error(f"Error al obtener episodios: {e}")
        return

    if not episodios:
        ui.error("No se encontraron episodios.")
        return

    vistos = _obtener_episodios_vistos(anime.get("url", ""))
    episodio_seleccionado = ui.seleccionar_episodios(
        f"📺 {anime['titulo']} - Elige episodio",
        episodios,
        vistos,
        lambda e: f"Ep.{e.get('numero', '?')}",
    )
    if not episodio_seleccionado:
        return
    idx_actual = episodios.index(episodio_seleccionado)
    reproducir_con_navegacion(ui, provider, episodios, idx_actual, anime, skip=skip, quality=quality)


# --- REPRODUCCIÓN ---


def reproducir_con_navegacion(
    ui: UI,
    provider,
    episodios: list,
    idx_actual: int,
    anime: dict,
    skip: bool = False,
    quality: str = "best",
) -> None:
    """Loop principal de reproducción con menú durante y después."""
    while True:
        episodio = episodios[idx_actual]
        ep_num = episodio.get("numero", "?")

        ui.spinner_start(f"Resolviendo stream de 'Ep.{ep_num}'...")
        try:
            url_video = provider.obtener_stream(episodio)
        except StreamNotFoundError as e:
            ui.spinner_stop()
            ui.error(f"No se pudo resolver stream: {e}")
            logger.debug("StreamNotFoundError: %s", e)
            return
        except ProviderError as e:
            ui.spinner_stop()
            ui.error(f"Error del provider: {e}")
            logger.debug("ProviderError en reproducir_con_navegacion: %s", e)
            return
        except Exception as e:
            ui.spinner_stop()
            ui.error(f"Error al resolver stream: {e}")
            logger.debug("Error inesperado en reproducir_con_navegacion: %s", e)
            return
        finally:
            ui.spinner_stop()

        if not url_video:
            ui.error("No se pudo obtener el enlace de video.")
            return

        titulo_ep = episodio.get("titulo", f"Ep.{ep_num}")
        skip_args = None
        if skip:
            if ANI_SKIP_DISPONIBLE:
                ui.info("Buscando tiempos de skip (ani-skip)...")
                skip_args = obtener_ani_skip_args(anime["titulo"], ep_num)
                if skip_args:
                    ui.exito("OP/ED skip activado")
                else:
                    ui.warning("No se encontraron tiempos de skip para este episodio")
            else:
                ui.warning("ani-skip no instalado. Instala con: pip install ani-skip")

        ui.exito(f"Reproduciendo: Ep.{ep_num}")
        proc = reproducir_background(
            url_video, titulo=titulo_ep, referer=episodio["url"], formato_id=quality, skip_args=skip_args
        )

        if proc is None:
            return

        proc._neko_titulo = titulo_ep  # type: ignore[attr-defined]

        mpv_cerro = [False]

        def _monitor_mpv():
            proc.wait()  # type: ignore[union-attr]
            mpv_guardar_posicion(proc, titulo_ep)
            mpv_cerro[0] = True

        monitor = threading.Thread(target=_monitor_mpv, daemon=True)
        monitor.start()

        print(ATAJOS_HINT)

        try:
            while not mpv_cerro[0]:
                time.sleep(0.2)

                tecla = _leer_tecla_no_bloqueante()
                if tecla:
                    if tecla == "n" and idx_actual < len(episodios) - 1:
                        ui.info("▶ Siguiente episodio")
                        mpv_matar(proc)
                        guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                        idx_actual += 1
                        break
                    elif tecla == "p" and idx_actual > 0:
                        ui.info("◀ Episodio anterior")
                        mpv_matar(proc)
                        guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                        idx_actual -= 1
                        break
                    elif tecla == "r":
                        ui.info("🔄 Repitiendo episodio")
                        mpv_matar(proc)
                        break
                    elif tecla == "q":
                        ui.info("Saliendo...")
                        mpv_matar(proc)
                        guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                        ui._clear()
                        return

                if mpv_cerro[0]:
                    break

                opcion = _menu_duracion(anime, episodios, idx_actual, ui)
                if opcion is None:
                    mpv_matar(proc)
                    guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                    ui._clear()
                    return

                if opcion == "quit":
                    mpv_matar(proc)
                    guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                    ui._clear()
                    return
                elif opcion == "next" and idx_actual < len(episodios) - 1:
                    mpv_matar(proc)
                    guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                    idx_actual += 1
                    break
                elif opcion == "prev" and idx_actual > 0:
                    mpv_matar(proc)
                    guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                    idx_actual -= 1
                    break
                elif opcion == "replay":
                    mpv_matar(proc)
                    break
                elif opcion == "quality":
                    ui.info("Detectando calidades disponibles...")
                    calidades = obtener_calidades(url_video, referer=episodio["url"])
                    if calidades:
                        calidad_sel = ui.seleccionar("🎨 Elige calidad", calidades, lambda c: c["label"])
                        if calidad_sel:
                            ui.info(f"Reproduciendo con calidad: {calidad_sel['label']}")
                            mpv_matar(proc)
                            reproducir(
                                url_video, titulo=titulo_ep, referer=episodio["url"], formato_id=calidad_sel["id"]
                            )
                            proc = reproducir_background(
                                url_video,
                                titulo=titulo_ep,
                                referer=episodio["url"],
                                formato_id=calidad_sel["id"],
                                skip_args=skip_args,
                            )
                            if proc is None:
                                guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                                ui._clear()
                                return
                            proc._neko_titulo = titulo_ep  # type: ignore[attr-defined]
                            mpv_cerro[0] = False

                            def _monitor_mpv2():
                                proc.wait()
                                mpv_guardar_posicion(proc, titulo_ep)
                                mpv_cerro[0] = True

                            monitor2 = threading.Thread(target=_monitor_mpv2, daemon=True)
                            monitor2.start()
                    else:
                        ui.error("No se pudieron detectar calidades alternativas.")
                elif opcion == "select":
                    nuevo_ep = ui.seleccionar_episodios(
                        f"📺 {anime['titulo']} - Elige episodio",
                        episodios,
                        _obtener_episodios_vistos(anime.get("url", "")),
                        lambda e: f"Ep.{e.get('numero', '?')}",
                    )
                    if nuevo_ep:
                        mpv_matar(proc)
                        guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
                        idx_actual = episodios.index(nuevo_ep)
                        break
        except KeyboardInterrupt:
            mpv_matar(proc)
            guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)
            ui._clear()
            return

        if mpv_cerro[0]:
            guardar_serie({"titulo": titulo_ep, "url": episodio["url"]}, provider.nombre)

            ep_num = episodios[idx_actual].get("numero", "?")
            ui.titulo(f"📺 Ep.{ep_num} finalizado")

            opcion = _menu_post_playback(episodios, idx_actual, ui)

            if opcion is None or opcion == "quit":
                ui._clear()
                return
            elif opcion == "next" and idx_actual < len(episodios) - 1:
                idx_actual += 1
            elif opcion == "prev" and idx_actual > 0:
                idx_actual -= 1
            elif opcion == "replay":
                continue
            elif opcion == "select":
                nuevo_ep = ui.seleccionar_episodios(
                    f"📺 {anime['titulo']} - Elige episodio",
                    episodios,
                    _obtener_episodios_vistos(anime.get("url", "")),
                    lambda e: f"Ep.{e.get('numero', '?')}",
                )
                if nuevo_ep:
                    idx_actual = episodios.index(nuevo_ep)
            else:
                ui.error("Opción no válida.")


def reproducir_con_watch_later(
    ui: UI,
    provider,
    episodio: dict,
    url_video: str,
    skip: bool = False,
    quality: str = "best",
) -> None:
    """Reproduce un episodio guardando y reanudando posición."""
    titulo = episodio.get("titulo", "")

    pos = obtener_posicion(titulo)
    if pos:
        ui.info(f"Retomando desde {pos:.0f}s...")

    skip_args = None
    if skip and ANI_SKIP_DISPONIBLE:
        skip_args = obtener_ani_skip_args(titulo, episodio.get("numero", 1))

    ui.exito(f"Reproduciendo: {titulo}")
    reproducir(url_video, titulo=titulo, referer=episodio["url"], formato_id=quality, skip_args=skip_args)

    guardar_serie({"titulo": titulo, "url": episodio["url"]}, provider.nombre)


# --- MODOS DE OPERACIÓN ---


def modo_providers(ui: UI, providers: dict) -> None:
    """Menu para cambiar el provider activo."""
    config = load_config()
    actual = config.get("provider", "jkanime")

    while True:
        ui.titulo("🌐 Providers")

        items = []
        for key, prov in providers.items():
            marcado = "✓" if key == actual else " "
            items.append(
                {
                    "id": key,
                    "label": f"[{marcado}] {prov.nombre} — {prov.base_url}",
                    "provider": prov,
                }
            )
        items.append({"id": "__volver", "label": "← Volver al menú principal"})

        seleccion = ui.seleccionar(
            f"Provider actual: {providers[actual].nombre}",
            items,
            lambda x: x["label"],
        )
        if not seleccion or seleccion["id"] == "__volver":
            return

        nuevo = seleccion["id"]
        if nuevo == actual:
            ui.info(f"'{providers[nuevo].nombre}' ya esta activo")
        else:
            set_provider(nuevo)
            actual = nuevo
            ui.exito(f"Provider cambiado a: {providers[nuevo].nombre}")


def modo_descubrir(ui: UI, provider, skip: bool = False, quality: str = "best") -> None:
    """Menu de descubrimiento AniList: populares, trending, estrenos, etc."""
    categorias = [
        {"id": "popular", "label": "🔥  Mas Populares", "sort": "POPULARITY_DESC"},
        {"id": "trending", "label": "📈  En Tendencia", "sort": "TRENDING_DESC"},
        {"id": "score", "label": "⭐  Mejor Puntuados", "sort": "SCORE_DESC"},
        {"id": "favorites", "label": "💖  Mas Favoritos", "sort": "FAVOURITES_DESC"},
        {"id": "estrenos", "label": "📺  Estrenos de la Semana", "sort": None},
    ]

    while True:
        ui.titulo("🔥 Descubrir Anime")

        opcion = ui.seleccionar("Categoria", categorias, lambda c: c["label"])
        if not opcion:
            return

        if opcion["id"] == "estrenos":
            ui.info("Cargando estrenos de la semana...")
            resultados = estrenos_semanales(per_page=25)
            if not resultados:
                ui.error("No se pudieron cargar los estrenos.")
                continue

            from datetime import datetime

            def label_estreno(r):
                fecha = datetime.fromtimestamp(r.get("airing_at", 0)).strftime("%d/%m %H:%M")
                ep = r.get("episodio_al_aire", "?")
                return f"{fecha} - Ep.{ep} - {r['titulo_romaji']}"

            seleccionado = ui.seleccionar("Estrenos de la Semana", resultados, label_estreno)
            if not seleccionado:
                continue

            ui._clear()
            mostrar_info_anilist(ui, seleccionado)

            ui.info(f"Buscando '{seleccionado['titulo_romaji']}' en {provider.nombre}...")
            try:
                resultados_provider = provider.buscar(seleccionado["titulo_romaji"])
            except ProviderError as e:
                ui.error(f"Error del provider: {e}")
                logger.debug("ProviderError en modo_descubrir (estrenos): %s", e)
                continue
            except Exception as e:
                ui.error(f"Error al buscar: {e}")
                logger.debug("Error inesperado en modo_descubrir (estrenos): %s", e)
                continue

            if not resultados_provider:
                ui.error("No se encontro en el provider.")
                continue

            anime = ui.seleccionar("Elige un anime", resultados_provider, lambda a: a["titulo"])
            if not anime:
                continue
            _continuar_con_anime(ui, provider, anime, skip=skip, quality=quality)
        else:
            sort = opcion["sort"]
            titulo = opcion["label"].strip()
            ui.info(f"Cargando {titulo.lower()}...")
            resultados = descubrir_anilist(sort=sort, per_page=25)
            if not resultados:
                ui.error("No se pudieron cargar los resultados.")
                continue

            seleccionado = mostrar_descubrimiento(ui, resultados, titulo, incluir_info_extra=True)
            if not seleccionado:
                continue

            ui._clear()
            mostrar_info_anilist(ui, seleccionado)

            ui.info(f"Buscando '{seleccionado['titulo_romaji']}' en {provider.nombre}...")
            try:
                resultados_provider = provider.buscar(seleccionado["titulo_romaji"])
            except ProviderError as e:
                ui.error(f"Error del provider: {e}")
                logger.debug("ProviderError en modo_descubrir: %s", e)
                continue
            except Exception as e:
                ui.error(f"Error al buscar: {e}")
                logger.debug("Error inesperado en modo_descubrir: %s", e)
                continue

            if not resultados_provider:
                ui.error("No se encontro en el provider.")
                continue

            anime = ui.seleccionar("Elige un anime", resultados_provider, lambda a: a["titulo"])
            if not anime:
                continue
            _continuar_con_anime(ui, provider, anime, skip=skip, quality=quality)


def modo_continuar(ui: UI, provider) -> None:
    """Continuar desde el último episodio visto."""
    entradas = obtener_watch_later()
    if not entradas:
        ui.error("No hay episodios en Watch Later.")
        return
    ultimo = entradas[0]

    titulo_completo = ultimo["titulo"]
    ui.info(f"Último visto: {titulo_completo}")
    ui.info(f"Posición: {ultimo['posicion']:.0f}s")

    nombre_anime = titulo_completo.split(" - ")[0] if " - " in titulo_completo else titulo_completo

    ui.info(f"Buscando '{nombre_anime}' en {provider.nombre}...")
    try:
        resultados = provider.buscar(nombre_anime)
    except ProviderError as e:
        ui.error(f"Error del provider: {e}")
        logger.debug("ProviderError en modo_continuar: %s", e)
        return
    except Exception as e:
        ui.error(f"Error al buscar: {e}")
        logger.debug("Error inesperado en modo_continuar: %s", e)
        return

    if not resultados:
        ui.error("No se encontró el anime en el provider.")
        return

    anime = resultados[0]
    ui.info(f"Cargando episodios de '{anime['titulo']}'...")
    try:
        episodios = provider.obtener_episodios(anime)
    except ProviderError as e:
        ui.error(f"Error del provider: {e}")
        logger.debug("ProviderError en modo_continuar (episodios): %s", e)
        return
    except Exception as e:
        ui.error(f"Error al obtener episodios: {e}")
        logger.debug("Error inesperado en modo_continuar (episodios): %s", e)
        return

    if not episodios:
        ui.error("No se encontraron episodios.")
        return

    ep_encontrado = None
    idx_encontrado = 0
    for i, ep in enumerate(episodios):
        ep_titulo = ep.get("titulo", "")
        if titulo_completo in ep_titulo or ep_titulo in titulo_completo:
            ep_encontrado = ep
            idx_encontrado = i
            break

    if not ep_encontrado:
        ui.error("No se encontró el episodio exacto. Reproduciendo desde el último.")
        idx_encontrado = len(episodios) - 1
        ep_encontrado = episodios[-1]

    reproducir_con_navegacion(ui, provider, episodios, idx_encontrado, anime)


def modo_busqueda(
    ui: UI,
    provider,
    query_override: str | None = None,
    episodio_range: str | None = None,
    skip: bool = False,
    quality: str = "best",
) -> None:
    """Busqueda y reproduccion."""
    query = query_override or ui.preguntar("🔍 Buscar anime")
    if not query:
        return

    ui.info(f"Buscando '{query}' en {provider.nombre}...")
    try:
        resultados = provider.buscar(query)
    except ProviderError as e:
        ui.error(f"Error del provider: {e}")
        logger.debug("ProviderError en modo_busqueda: %s", e)
        return
    except Exception as e:
        ui.error(f"Error al buscar: {e}")
        logger.debug("Error inesperado en modo_busqueda: %s", e)
        return

    if not resultados:
        ui.error("No se encontraron resultados.")
        return

    anime = ui.seleccionar("Elige un anime", resultados, lambda a: a["titulo"])
    if not anime:
        return

    anilist_info = buscar_anilist(anime["titulo"])
    if anilist_info:
        ui._clear()
        mostrar_info_anilist(ui, anilist_info)

    if episodio_range:
        ya_fav = es_favorito(anime.get("url", ""))
        if not ya_fav:
            resp = ui.preguntar("⭐ Añadir a favoritos? (y/n)")
            if resp.lower() in ("y", "s", "si", "sí"):
                toggle_favorito(anime)

        ui.info(f"Cargando episodios de '{anime['titulo']}'...")
        try:
            episodios = provider.obtener_episodios(anime)
        except ProviderError as e:
            ui.error(f"Error del provider: {e}")
            logger.debug("ProviderError en modo_busqueda (episodios): %s", e)
            return
        except Exception as e:
            ui.error(f"Error al obtener episodios: {e}")
            logger.debug("Error inesperado en modo_busqueda (episodios): %s", e)
            return

        if not episodios:
            ui.error("No se encontraron episodios.")
            return

        nums = _parse_episodio_range(episodio_range, len(episodios))
        indices = []
        for n in nums:
            for i, ep in enumerate(episodios):
                if ep.get("numero") == n:
                    indices.append(i)
                    break
        if not indices:
            ui.error(f"Episodio(s) {episodio_range} no encontrado(s).")
            return
        idx_actual = indices[0]
        reproducir_con_navegacion(ui, provider, episodios, idx_actual, anime, skip=skip, quality=quality)
    else:
        _continuar_con_anime(ui, provider, anime, skip=skip, quality=quality)


def modo_biblioteca(ui: UI, provider, skip: bool = False, quality: str = "best") -> None:
    series = obtener_series()
    if not series:
        ui.info("No hay series guardadas.")
        return

    while True:
        ui.titulo("📂 Mi Biblioteca")

        serie = ui.seleccionar("Elige una serie", series, lambda s: f"{s['titulo']} ({s.get('provider', '')})")
        if not serie:
            return

        while True:
            ui.titulo(f"📂 {serie['titulo']}")
            fav_status = "⭐ En favoritos" if es_favorito(serie.get("url", "")) else "☆ No en favoritos"
            ui.info(f"Provider: {serie.get('provider', 'N/A')}")
            ui.info(f"Estado: {fav_status}")
            print()

            acciones_bib = [
                ("ver", "▶  Ver episodios"),
                ("fav", "⭐  Toggle favorito"),
                ("del", "🗑️  Eliminar de biblioteca"),
            ]
            resp = _menu_acciones(f"📂 {serie['titulo']}", acciones_bib)

            if resp is None or resp == "volver":
                break
            elif resp == "ver":
                ui.info(f"Buscando '{serie['titulo']}' en {provider.nombre}...")
                try:
                    resultados = provider.buscar(serie["titulo"])
                except ProviderError as e:
                    ui.error(f"Error del provider: {e}")
                    logger.debug("ProviderError en modo_biblioteca: %s", e)
                    continue
                except Exception as e:
                    ui.error(f"Error al buscar: {e}")
                    logger.debug("Error inesperado en modo_biblioteca: %s", e)
                    continue

                if not resultados:
                    ui.error("No se encontró la serie en el provider.")
                    continue

                anime = resultados[0]
                try:
                    episodios = provider.obtener_episodios(anime)
                except ProviderError as e:
                    ui.error(f"Error del provider: {e}")
                    logger.debug("ProviderError en modo_biblioteca (episodios): %s", e)
                    continue
                except Exception as e:
                    ui.error(f"Error al obtener episodios: {e}")
                    logger.debug("Error inesperado en modo_biblioteca (episodios): %s", e)
                    continue

                if not episodios:
                    ui.error("No se encontraron episodios.")
                    continue

                vistos = _obtener_episodios_vistos(anime.get("url", ""))
                episodio = ui.seleccionar_episodios(
                    f"📺 {anime['titulo']} - Elige episodio",
                    episodios,
                    vistos,
                    lambda e: f"Ep.{e.get('numero', '?')}",
                )
                if episodio:
                    ui.info("Resolviendo stream...")
                    url_video = provider.obtener_stream(episodio)
                    if url_video:
                        reproducir_con_watch_later(ui, provider, episodio, url_video, skip=skip, quality=quality)
                    else:
                        ui.error("No se pudo obtener el enlace de video.")
            elif resp == "fav":
                añadido = toggle_favorito(serie)
                if añadido:
                    ui.exito(f"Añadido a favoritos: {serie['titulo']}")
                else:
                    ui.info(f"Eliminado de favoritos: {serie['titulo']}")
            elif resp == "del":
                from neko.core.library import eliminar_serie

                eliminar_serie(serie.get("url", ""))
                ui.exito(f"Eliminado: {serie['titulo']}")
                series = obtener_series()
                if not series:
                    return
                break


def modo_favoritos(ui: UI, provider, skip: bool = False, quality: str = "best") -> None:
    from neko.core.library import obtener_favoritos

    favoritos = obtener_favoritos()
    if not favoritos:
        ui.info("No hay favoritos.")
        return

    while True:
        ui.titulo("⭐ Favoritos")

        fav = ui.seleccionar("Elige un favorito", favoritos, lambda f: f["titulo"])
        if not fav:
            return

        while True:
            ui.titulo(f"⭐ {fav['titulo']}")
            print()

            acciones_fav = [
                ("ver", "▶  Ver episodios"),
                ("del", "🗑️  Eliminar de favoritos"),
            ]
            resp = _menu_acciones(f"⭐ {fav['titulo']}", acciones_fav)

            if resp is None or resp == "volver":
                break
            elif resp == "ver":
                ui.info(f"Buscando '{fav['titulo']}' en {provider.nombre}...")
                try:
                    resultados = provider.buscar(fav["titulo"])
                except ProviderError as e:
                    ui.error(f"Error del provider: {e}")
                    logger.debug("ProviderError en modo_favoritos: %s", e)
                    continue
                except Exception as e:
                    ui.error(f"Error al buscar: {e}")
                    logger.debug("Error inesperado en modo_favoritos: %s", e)
                    continue

                if not resultados:
                    ui.error("No se encontró el anime en el provider.")
                    continue

                anime = resultados[0]
                try:
                    episodios = provider.obtener_episodios(anime)
                except ProviderError as e:
                    ui.error(f"Error del provider: {e}")
                    logger.debug("ProviderError en modo_favoritos (episodios): %s", e)
                    continue
                except Exception as e:
                    ui.error(f"Error al obtener episodios: {e}")
                    logger.debug("Error inesperado en modo_favoritos (episodios): %s", e)
                    continue

                if not episodios:
                    ui.error("No se encontraron episodios.")
                    continue

                vistos = _obtener_episodios_vistos(anime.get("url", ""))
                episodio = ui.seleccionar_episodios(
                    f"📺 {anime['titulo']} - Elige episodio",
                    episodios,
                    vistos,
                    lambda e: f"Ep.{e.get('numero', '?')}",
                )
                if episodio:
                    ui.info("Resolviendo stream...")
                    url_video = provider.obtener_stream(episodio)
                    if url_video:
                        reproducir_con_watch_later(ui, provider, episodio, url_video, skip=skip, quality=quality)
                    else:
                        ui.error("No se pudo obtener el enlace de video.")
            elif resp == "del":
                toggle_favorito(fav)
                ui.exito(f"Eliminado de favoritos: {fav['titulo']}")
                favoritos = obtener_favoritos()
                if not favoritos:
                    return
                break


def modo_watch_later(ui: UI, provider, skip: bool = False, quality: str = "best") -> None:
    from neko.core.library import eliminar_watch_later

    entradas = obtener_watch_later()
    if not entradas:
        ui.info("No hay episodios en Watch Later.")
        return

    while True:
        ui.titulo("⏱️  Watch Later")

        entrada = ui.seleccionar("Elige un episodio", entradas, lambda e: f"{e['titulo']} ({e['posicion']:.0f}s)")
        if not entrada:
            return

        while True:
            ui.titulo(f"⏱️  {entrada['titulo']}")
            ui.info(f"Posición: {entrada['posicion']:.0f}s")
            print()

            acciones_wl = [
                ("cont", "▶  Continuar viendo"),
                ("del", "🗑️  Eliminar de Watch Later"),
            ]
            resp = _menu_acciones(f"⏱️  {entrada['titulo']}", acciones_wl)

            if resp is None or resp == "volver":
                break
            elif resp == "cont":
                nombre_anime = entrada["titulo"].split(" - ")[0] if " - " in entrada["titulo"] else entrada["titulo"]
                ui.info(f"Buscando '{nombre_anime}'...")
                try:
                    resultados = provider.buscar(nombre_anime)
                except ProviderError as e:
                    ui.error(f"Error del provider: {e}")
                    logger.debug("ProviderError en modo_watch_later: %s", e)
                    continue
                except Exception as e:
                    ui.error(f"Error al buscar: {e}")
                    logger.debug("Error inesperado en modo_watch_later: %s", e)
                    continue

                if not resultados:
                    ui.error("No se encontró el anime en el provider.")
                    continue

                anime = resultados[0]
                try:
                    episodios = provider.obtener_episodios(anime)
                except ProviderError as e:
                    ui.error(f"Error del provider: {e}")
                    logger.debug("ProviderError en modo_watch_later (episodios): %s", e)
                    continue
                except Exception as e:
                    ui.error(f"Error al obtener episodios: {e}")
                    logger.debug("Error inesperado en modo_watch_later (episodios): %s", e)
                    continue

                if not episodios:
                    ui.error("No se encontraron episodios.")
                    continue

                ep_encontrado = None
                for ep in episodios:
                    if entrada["titulo"] in ep.get("titulo", "") or ep.get("titulo", "") in entrada["titulo"]:
                        ep_encontrado = ep
                        break
                if not ep_encontrado:
                    ui.error("No se encontró el episodio exacto.")
                    continue

                ui.info("Resolviendo stream...")
                url_video = provider.obtener_stream(ep_encontrado)
                if url_video:
                    reproducir_con_watch_later(ui, provider, ep_encontrado, url_video, skip=skip, quality=quality)
                else:
                    ui.error("No se pudo obtener el enlace de video.")
            elif resp == "del":
                eliminar_watch_later(entrada["titulo"])
                ui.exito(f"Eliminado: {entrada['titulo']}")
                entradas = obtener_watch_later()
                if not entradas:
                    return
                break
