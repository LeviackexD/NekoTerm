from __future__ import annotations

"""
core/player.py — Lanza el reproductor del sistema con resolución dinámica.

Estrategia:
  - URLs directas (.mp4/.m3u8) → mpv directo
  - URLs de embed/página → mpv --ytdl-format=best (yt-dlp interno)
  - yt-dlp resuelve en tiempo real → URLs no caducan
"""

import logging
import os
import shutil
import subprocess
import sys

from neko.core.library import guardar_posicion, obtener_posicion
from neko.utils.helpers import titulo_a_hash

logger = logging.getLogger("neko.player")

REPRODUCTORES = [
    ("mpv", []),
    ("vlc", ["--intf", "dummy"]),
    ("ffplay", ["-autoexit", "-loglevel", "quiet"]),
    ("xdg-open", []),
    ("open", []),
]

YTDLP_DISPONIBLE = shutil.which("yt-dlp") is not None
ANI_SKIP_DISPONIBLE = shutil.which("ani-skip") is not None


def detectar_reproductor() -> tuple[str, list] | None:
    for nombre, args in REPRODUCTORES:
        if shutil.which(nombre):
            return nombre, args
    return None


def _es_url_directa(url: str) -> bool:
    url_lower = url.lower()
    return any(ext in url_lower for ext in [".mp4", ".m3u8", ".mkv", ".webm", ".avi"])


def resolver_stream_ios(url: str, referer: str = "", formato_id: str = "best") -> str | None:
    """Resuelve la URL del stream y devuelve el URL scheme de VLC para iOS.

    Si yt-dlp está disponible y la URL no es directa, la resuelve primero.
    Retorna el string 'vlc://<url>' o None si no se pudo resolver.
    """
    url_final = url
    if YTDLP_DISPONIBLE and not _es_url_directa(url):
        try:
            cmd = ["yt-dlp", "-g", "-f", formato_id or "best"]
            if referer:
                cmd.extend(["--referer", referer])
            cmd.extend(["--no-warnings", "--quiet", url])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                url_final = result.stdout.strip()
        except Exception as e:
            logger.debug("Error resolviendo yt-dlp para iOS: %s", e)
            return None

    return f"vlc://{url_final}"


def obtener_calidades(url: str, referer: str = "") -> list[dict]:
    if not YTDLP_DISPONIBLE:
        return []

    try:
        cmd = ["yt-dlp", "-J", "--no-warnings", "--quiet"]
        if referer:
            cmd.extend(["--referer", referer])
        cmd.append(url)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0 or not result.stdout.strip():
            return []

        import json

        data = json.loads(result.stdout)
        formats = data.get("formats", [])

        calidades = []
        seen = set()
        for fmt in formats:
            if not fmt.get("vcodec") or fmt.get("vcodec") == "none":
                continue

            height = fmt.get("height")
            if not height:
                continue

            res_key = f"{height}p"
            if res_key in seen:
                continue
            seen.add(res_key)

            ext = fmt.get("ext", "mp4")
            calidades.append(
                {
                    "id": fmt.get("format_id", "best"),
                    "resolution": res_key,
                    "ext": ext,
                    "label": f"{res_key} ({ext})",
                }
            )

        calidades.sort(key=lambda x: int(x["resolution"].replace("p", "")), reverse=True)

        if not calidades:
            calidades.append(
                {
                    "id": "best",
                    "resolution": "best",
                    "ext": "auto",
                    "label": "Mejor calidad (auto)",
                }
            )

        return calidades
    except Exception as e:
        logger.debug("Error obteniendo calidades: %s", e)
        return []


def obtener_ani_skip_args(titulo: str, ep_numero: int) -> list[str]:
    if not ANI_SKIP_DISPONIBLE:
        return []
    try:
        result = subprocess.run(
            ["ani-skip", "-q", titulo, "-e", str(ep_numero)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split()
    except Exception as e:
        logger.debug("Error con ani-skip: %s", e)
    return []


def _construir_cmd_mpv(
    url: str, titulo: str, referer: str, formato_id: str, start_pos: float | None, skip_args: list[str] | None = None
) -> list[str]:
    # Derivar Origin del referer
    from urllib.parse import urlparse

    parsed = urlparse(referer)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    cmd = [
        "mpv",
        "--ontop",
        f"--force-media-title={titulo}",
        f"--referrer={referer}",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        f"--http-header-fields=Origin: {origin}",
    ]

    if start_pos and start_pos > 0:
        cmd.append(f"--start={start_pos}")

    if formato_id and formato_id != "best":
        cmd.append(f"--ytdl-format={formato_id}")
    else:
        cmd.append("--ytdl-format=best")

    if skip_args:
        cmd.extend(skip_args)

    cmd.append(url)
    return cmd


def reproducir(
    url: str, titulo: str = "", referer: str = "", formato_id: str = "best", skip_args: list[str] | None = None
):
    resultado = detectar_reproductor()

    if resultado is None:
        logger.error("No se encontró ningún reproductor compatible. URL: %s", url)
        print(
            "\n⚠️  No se encontró ningún reproductor compatible.",
            "\nInstala uno de: mpv, vlc, ffplay",
            f"\nURL: {url}",
            file=sys.stderr,
        )
        return

    nombre, args = resultado
    start_pos = obtener_posicion(titulo)

    if nombre == "mpv":
        cmd = _construir_cmd_mpv(url, titulo, referer, formato_id, start_pos, skip_args)

        log_file = "/tmp/neko_pos_$$"
        try:
            with open(log_file, "w") as log:
                subprocess.run(cmd, stdout=log, stderr=subprocess.DEVNULL)

            if os.path.exists(log_file):
                with open(log_file) as log:
                    lines = log.readlines()
                    for line in reversed(lines):
                        if line.startswith("POS="):
                            pos = float(line.strip().split("=")[1])
                            if pos > 0:
                                guardar_posicion(titulo, pos)
                            break
                os.remove(log_file)
        except Exception as e:
            logger.debug("Error en reproducir (mpv): %s", e)

    else:
        url_final = url
        if YTDLP_DISPONIBLE:
            try:
                cmd = ["yt-dlp", "-g", "-f", formato_id or "best"]
                if referer:
                    cmd.extend(["--referer", referer])
                cmd.extend(["--no-warnings", "--quiet", url])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and result.stdout.strip():
                    url_final = result.stdout.strip()
            except Exception as e:
                logger.debug("Error resolviendo yt-dlp: %s", e)

        cmd = [nombre, *args, url_final]
        try:
            subprocess.run(cmd, check=False)
        except FileNotFoundError:
            logger.error("No se pudo ejecutar: %s", nombre)
            print(f"No se pudo ejecutar: {nombre}", file=sys.stderr)


def reproducir_background(
    url: str, titulo: str = "", referer: str = "", formato_id: str = "best", skip_args: list[str] | None = None
) -> subprocess.Popen | None:
    resultado = detectar_reproductor()

    if resultado is None:
        logger.error("No se encontró ningún reproductor compatible. URL: %s", url)
        print(
            "\n⚠️  No se encontró ningún reproductor compatible.",
            "\nInstala uno de: mpv, vlc, ffplay",
            f"\nURL: {url}",
            file=sys.stderr,
        )
        return None

    nombre, args = resultado
    start_pos = obtener_posicion(titulo)

    if nombre == "mpv":
        cmd = _construir_cmd_mpv(url, titulo, referer, formato_id, start_pos, skip_args)

        log_file = f"/tmp/neko_mpv_{titulo_a_hash(titulo)}"
        try:
            log = open(log_file, "w")
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.DEVNULL)
            proc._neko_log_file = log_file  # type: ignore[attr-defined]
            return proc
        except Exception as e:
            logger.debug("Error lanzando mpv: %s", e)
            return None
    else:
        url_final = url
        if YTDLP_DISPONIBLE:
            try:
                cmd = ["yt-dlp", "-g", "-f", formato_id or "best"]
                if referer:
                    cmd.extend(["--referer", referer])
                cmd.extend(["--no-warnings", "--quiet", url])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0 and result.stdout.strip():
                    url_final = result.stdout.strip()
            except Exception as e:
                logger.debug("Error resolviendo yt-dlp: %s", e)

        cmd = [nombre, *args, url_final]
        try:
            return subprocess.Popen(cmd)
        except FileNotFoundError:
            logger.error("No se pudo ejecutar: %s", nombre)
            print(f"No se pudo ejecutar: {nombre}", file=sys.stderr)
            return None


def mpv_terminado(proc: subprocess.Popen | None) -> bool:
    if proc is None:
        return True
    return proc.poll() is not None


def mpv_matar(proc: subprocess.Popen | None):
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    if proc is not None and hasattr(proc, "_neko_log_file"):
        log_file = proc._neko_log_file
        try:
            if os.path.exists(log_file):
                with open(log_file) as log:
                    lines = log.readlines()
                    for line in reversed(lines):
                        if line.startswith("POS="):
                            pos = float(line.strip().split("=")[1])
                            if pos > 0:
                                titulo = getattr(proc, "_neko_titulo", "")
                                if titulo:
                                    guardar_posicion(titulo, pos)
                            break
                os.remove(log_file)
        except Exception as e:
            logger.debug("Error guardando posición al matar mpv: %s", e)


def mpv_guardar_posicion(proc: subprocess.Popen | None, titulo: str):
    if proc is None:
        return
    if hasattr(proc, "_neko_log_file"):
        log_file = proc._neko_log_file
        try:
            if os.path.exists(log_file):
                with open(log_file) as log:
                    lines = log.readlines()
                    for line in reversed(lines):
                        if line.startswith("POS="):
                            pos = float(line.strip().split("=")[1])
                            if pos > 0:
                                guardar_posicion(titulo, pos)
                            break
                os.remove(log_file)
        except Exception as e:
            logger.debug("Error guardando posición: %s", e)
