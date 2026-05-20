from __future__ import annotations

"""
core/ui.py — Interfaz de usuario para NekoTerm.
Menú colorido con iconos + fzf/rofi/dmenu para navegación con flechas.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import threading

FZF_DISPONIBLE = shutil.which("fzf") is not None
ROFI_DISPONIBLE = shutil.which("rofi") is not None
DMENU_DISPONIBLE = shutil.which("dmenu") is not None

SPINNER_CHARS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧"]


class Colores:
    CYAN = "\033[96m"
    VERDE = "\033[92m"
    AMARILLO = "\033[93m"
    ROJO = "\033[91m"
    MAGENTA = "\033[95m"
    DIM = "\033[2m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


LOGO = """
███╗   ██╗███████╗██╗  ██╗ ██████╗  ██████╗██╗     ██╗
████╗  ██║██╔════╝██║ ██╔╝██╔═══██╗██╔════╝██║     ██║
██╔██╗ ██║█████╗  █████╔╝ ██║   ██║██║     ██║     ██║
██║╚██╗██║██╔══╝  ██╔═██╗ ██║   ██║██║     ██║     ██║
██║ ╚████║███████╗██║  ██╗╚██████╔╝╚██████╗███████╗██║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚═╝
"""


LOGO_LINES = 9  # lineas que ocupa el bloque logo + subtitulo


def _es_terminal_interactiva() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _terminal_height() -> int:
    """Devuelve la altura de la terminal en líneas."""
    try:
        return os.get_terminal_size().lines
    except Exception:
        return 24


def _header_height() -> int:
    """Lineas reservadas para el logo + separador."""
    return LOGO_LINES + 1


def _fzf_height(footer_lines: int = 0) -> int:
    """Calcula la altura maxima para fzf sin tapar el logo."""
    term_h = _terminal_height()
    available = term_h - _header_height() - footer_lines - 2
    return max(5, min(available, 30))


class UI:
    def __init__(self):
        self._spinner_stop = threading.Event()
        self._spinner_thread = None

    def _spinner_loop(self, mensaje: str):
        """Loop interno del spinner."""
        idx = 0
        sys.stdout.write(f"\r  {Colores.CYAN}{SPINNER_CHARS[0]}{Colores.RESET} {mensaje}")
        sys.stdout.flush()
        while not self._spinner_stop.is_set():
            idx = (idx + 1) % len(SPINNER_CHARS)
            sys.stdout.write(f"\r  {Colores.CYAN}{SPINNER_CHARS[idx]}{Colores.RESET} {mensaje}")
            sys.stdout.flush()
            self._spinner_stop.wait(0.1)
        sys.stdout.write("\r" + " " * (len(mensaje) + 4) + "\r")
        sys.stdout.flush()

    def spinner_start(self, mensaje: str = "Cargando..."):
        """Inicia un spinner animado en la terminal."""
        self._spinner_stop.clear()
        self._spinner_thread = threading.Thread(target=self._spinner_loop, args=(mensaje,), daemon=True)
        self._spinner_thread.start()

    def spinner_stop(self):
        """Detiene el spinner."""
        self._spinner_stop.set()
        if self._spinner_thread:
            self._spinner_thread.join(timeout=1)

    def _clear(self):
        os.system("clear" if os.name != "nt" else "cls")

    def _refresh(self):
        """Redibuja el logo en su lugar sin añadir líneas (cursor home + clear below)."""
        sys.stdout.write("\033[H")
        sys.stdout.write(f"{Colores.CYAN}{LOGO}{Colores.RESET}")
        print(f"{Colores.DIM}  NekoTerm V1.0 · Anime en español desde tu terminal{Colores.RESET}")
        print(f"{Colores.DIM}  jkanime.bz · monoschinos2.com · animeflv.net · tioanime.com{Colores.RESET}")
        sys.stdout.write("\n")
        sys.stdout.flush()

    def logo(self):
        self._clear()
        self._refresh()

    def titulo(self, texto: str):
        print(f"\n{Colores.CYAN}{Colores.BOLD}{'─' * 50}{Colores.RESET}")
        print(f"{Colores.CYAN}{Colores.BOLD}  {texto}{Colores.RESET}")
        print(f"{Colores.CYAN}{Colores.BOLD}{'─' * 50}{Colores.RESET}\n")

    def info(self, texto: str):
        print(f"  {Colores.CYAN}·{Colores.RESET} {texto}")

    def exito(self, texto: str):
        print(f"  {Colores.VERDE}✓{Colores.RESET} {texto}")

    def error(self, texto: str):
        print(f"  {Colores.ROJO}✗{Colores.RESET} {Colores.ROJO}{texto}{Colores.RESET}")

    def warning(self, texto: str):
        print(f"  {Colores.AMARILLO}!{Colores.RESET} {texto}")

    def dim(self, texto: str):
        print(f"  {Colores.DIM}{texto}{Colores.RESET}")

    def preguntar(self, prompt: str) -> str:
        try:
            return input(f"  {Colores.AMARILLO}?{Colores.RESET} {prompt}: ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            return ""

    def menu_principal(self) -> str:
        self._clear()
        self.logo()

        opciones = [
            ("1", "🔍  Buscar anime"),
            ("2", "📂  Mi Biblioteca"),
            ("3", "⭐  Favoritos"),
            ("4", "⏱️  Watch Later"),
            ("5", "🔥  Descubrir"),
            ("6", "🌐  Providers"),
            ("0", "🚪  Salir"),
        ]

        if FZF_DISPONIBLE:
            return self._menu_fzf(opciones)
        return self._menu_texto(opciones)

    def _menu_fzf(self, opciones: list) -> str:
        items = []
        for num, icono in opciones:
            items.append(f"{num}  {icono}")

        tmpfile = None
        result_file = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("\n".join(items))
                tmpfile = f.name

            result_file = tempfile.mktemp(suffix=".result")

            h = _fzf_height()
            cmd = f'fzf --prompt " NEKOTERM > " --height {h} --layout reverse --border rounded --color "prompt:cyan,pointer:magenta,border:cyan" --no-info --no-multi < "{tmpfile}" > "{result_file}" 2>/dev/tty'

            ret = os.system(cmd)

            if ret != 0:
                return "0"

            with open(result_file) as f:
                seleccionado = f.read().strip()

            if not seleccionado:
                return "0"

            num = seleccionado.split("  ")[0]
            return num
        except OSError:
            return "0"
        finally:
            if tmpfile and os.path.exists(tmpfile):
                os.unlink(tmpfile)
            if result_file and os.path.exists(result_file):
                os.unlink(result_file)

    def _menu_texto(self, opciones: list) -> str:
        while True:
            try:
                respuesta = input(f"  {Colores.CYAN}?{Colores.RESET} Elige una opción: ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                return "0"

            validas = [num for num, _ in opciones]
            if respuesta in validas:
                return respuesta

            self.error(f"Opción no válida. Elige: {', '.join(validas)}")

    def seleccionar(self, prompt: str, opciones: list, label_fn=None) -> dict | None:
        if not opciones:
            return None

        label_fn = label_fn or str

        if FZF_DISPONIBLE:
            return self._seleccionar_fzf(prompt, opciones, label_fn)
        return self._seleccionar_tabla(prompt, opciones, label_fn)

    def seleccionar_episodios(self, prompt: str, episodios: list, vistos: set, label_fn=None) -> dict | None:
        """
        Selección de episodios con indicador visual de episodios vistos.
        Los episodios vistos se muestran en color DIM.
        """
        if not episodios:
            return None

        label_fn = label_fn or (lambda e: f"Ep.{e.get('numero', '?')}")

        if FZF_DISPONIBLE:
            return self._seleccionar_episodios_fzf(prompt, episodios, vistos, label_fn)
        return self._seleccionar_episodios_tabla(prompt, episodios, vistos, label_fn)

    def _seleccionar_episodios_fzf(self, prompt: str, episodios: list, vistos: set, label_fn) -> dict | None:
        """fzf con colores ANSI para episodios vistos."""
        self._refresh()
        items = []
        for ep in episodios:
            label = label_fn(ep)
            ep_id = ep.get("url", ep.get("titulo", ""))
            if ep_id in vistos:
                items.append(f"\033[2m✓ {label}\033[0m")
            else:
                items.append(f"  {label}")

        tmpfile = None
        result_file = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("\n".join(items))
                tmpfile = f.name

            result_file = tempfile.mktemp(suffix=".result")

            h = _fzf_height(footer_lines=3)
            cmd = f'fzf --prompt " {prompt} > " --height {h} --layout reverse --border rounded --color "prompt:cyan,pointer:magenta,border:cyan" --no-info --no-multi --ansi < "{tmpfile}" > "{result_file}" 2>/dev/tty'

            ret = os.system(cmd)

            if ret != 0:
                return None

            with open(result_file) as f:
                seleccionado = f.read().strip()

            if not seleccionado:
                return None

            seleccionado_limpio = seleccionado.replace("\033[2m✓ ", "").replace("\033[0m", "").strip()

            for i, ep in enumerate(episodios):
                if label_fn(ep) == seleccionado_limpio:
                    return episodios[i]

            return None
        except (OSError, ValueError):
            return None
        finally:
            if tmpfile and os.path.exists(tmpfile):
                os.unlink(tmpfile)
            if result_file and os.path.exists(result_file):
                os.unlink(result_file)

    def _seleccionar_episodios_tabla(self, prompt: str, episodios: list, vistos: set, label_fn) -> dict | None:
        """Tabla numerada con indicador de vistos."""
        print(f"\n  {Colores.CYAN}{Colores.BOLD}{prompt}{Colores.RESET}")
        for i, ep in enumerate(episodios, 1):
            label = label_fn(ep)
            ep_id = ep.get("url", ep.get("titulo", ""))
            if ep_id in vistos:
                print(f"  {Colores.AMARILLO}{i}.{Colores.RESET} {Colores.DIM}✓ {label}{Colores.RESET}")
            else:
                print(f"  {Colores.AMARILLO}{i}.{Colores.RESET} {label}")

        print(f"\n  {Colores.DIM}0. Salir{Colores.RESET}")
        print(f"  {Colores.DIM}[Esc] Volver al menú principal{Colores.RESET}\n")

        while True:
            try:
                respuesta = input(f"  {Colores.AMARILLO}Elige [1-{len(episodios)}]: {Colores.RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                return None

            if respuesta == "0" or respuesta.lower() in ("q", "salir", "exit"):
                return None

            try:
                idx = int(respuesta) - 1
                if 0 <= idx < len(episodios):
                    return episodios[idx]
                else:
                    self.error(f"Elige un número entre 1 y {len(episodios)}.")
            except ValueError:
                self.error("Entrada inválida. Introduce un número.")

    def _seleccionar_fzf(self, prompt: str, opciones: list, label_fn) -> dict | None:
        self._refresh()
        items = [label_fn(op) for op in opciones]

        tmpfile = None
        result_file = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("\n".join(items))
                tmpfile = f.name

            result_file = tempfile.mktemp(suffix=".result")

            h = _fzf_height(footer_lines=3)
            cmd = f'fzf --prompt " {prompt} > " --height {h} --layout reverse --border rounded --color "prompt:cyan,pointer:magenta,border:cyan" --no-info --no-multi < "{tmpfile}" > "{result_file}" 2>/dev/tty'

            ret = os.system(cmd)

            if ret != 0:
                return None

            with open(result_file) as f:
                seleccionado = f.read().strip()

            if not seleccionado:
                return None

            idx = items.index(seleccionado)
            return opciones[idx]
        except (OSError, ValueError):
            return None
        finally:
            if tmpfile and os.path.exists(tmpfile):
                os.unlink(tmpfile)
            if result_file and os.path.exists(result_file):
                os.unlink(result_file)

    def _seleccionar_tabla(self, prompt: str, opciones: list, label_fn) -> dict | None:
        print(f"\n  {Colores.CYAN}{Colores.BOLD}{prompt}{Colores.RESET}")
        for i, opcion in enumerate(opciones, 1):
            print(f"  {Colores.AMARILLO}{i}.{Colores.RESET} {label_fn(opcion)}")

        print(f"\n  {Colores.DIM}0. Salir{Colores.RESET}")
        print(f"  {Colores.DIM}[Esc] Volver al menú principal{Colores.RESET}\n")

        while True:
            try:
                respuesta = input(f"  {Colores.AMARILLO}Elige [1-{len(opciones)}]: {Colores.RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                return None

            if respuesta == "0" or respuesta.lower() in ("q", "salir", "exit"):
                return None

            try:
                idx = int(respuesta) - 1
                if 0 <= idx < len(opciones):
                    return opciones[idx]
                else:
                    self.error(f"Elige un número entre 1 y {len(opciones)}.")
            except ValueError:
                self.error("Entrada inválida. Introduce un número.")


def menu_seleccionar(prompt: str, opciones: list[tuple[str, str]]) -> str | None:
    """
    Menú de selección unificado: rofi > dmenu > fzf > texto.
    opciones: lista de (numero, descripcion)
    Retorna el numero seleccionado o None.
    """
    items = [desc for _, desc in opciones]
    nums = [num for num, _ in opciones]

    if ROFI_DISPONIBLE:
        return _menu_rofi(prompt, items, nums)
    elif DMENU_DISPONIBLE:
        return _menu_dmenu(prompt, items, nums)
    elif FZF_DISPONIBLE:
        return _menu_fzf_unificado(prompt, items, nums)
    else:
        return _menu_texto_unificado(prompt, opciones)


def _menu_rofi(prompt: str, items: list[str], nums: list[str]) -> str | None:
    try:
        input_text = "\n".join(items)
        result = subprocess.run(
            [
                "rofi",
                "-dmenu",
                "-i",
                "-p",
                prompt,
                "-lines",
                str(len(items)),
                "-theme-str",
                "window {width: 600px;}",
                "-theme-str",
                "listview {columns: 1;}",
                "-theme-str",
                "element {padding: 8px;}",
                "-theme-str",
                'textbox-prompt-colon {str: "";}',
            ],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=60,
        )
        seleccionado = result.stdout.strip()
        if seleccionado and seleccionado in items:
            idx = items.index(seleccionado)
            return nums[idx]
    except Exception:
        pass
    return None


def _menu_dmenu(prompt: str, items: list[str], nums: list[str]) -> str | None:
    try:
        input_text = "\n".join(items)
        result = subprocess.run(
            ["dmenu", "-l", "10", "-p", prompt],
            input=input_text,
            capture_output=True,
            text=True,
            timeout=60,
        )
        seleccionado = result.stdout.strip()
        if seleccionado and seleccionado in items:
            idx = items.index(seleccionado)
            return nums[idx]
    except Exception:
        pass
    return None


def _menu_fzf_unificado(prompt: str, items: list[str], nums: list[str]) -> str | None:
    tmpfile = None
    result_file = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("\n".join(items))
            tmpfile = f.name

        result_file = tempfile.mktemp(suffix=".result")

        h = _fzf_height(footer_lines=3)
        cmd = f'fzf --prompt " {prompt} > " --height {h} --layout reverse --border rounded --color "prompt:cyan,pointer:magenta,border:cyan" --no-info --no-multi < "{tmpfile}" > "{result_file}" 2>/dev/tty'

        ret = os.system(cmd)

        if ret != 0:
            return None

        with open(result_file) as f:
            seleccionado = f.read().strip()

        if not seleccionado:
            return None

        if seleccionado in items:
            idx = items.index(seleccionado)
            return nums[idx]
    except (OSError, ValueError):
        pass
    finally:
        if tmpfile and os.path.exists(tmpfile):
            os.unlink(tmpfile)
        if result_file and os.path.exists(result_file):
            os.unlink(result_file)
    return None


def _menu_texto_unificado(prompt: str, opciones: list[tuple[str, str]]) -> str | None:
    print(f"\n  {Colores.CYAN}{Colores.BOLD}{prompt}{Colores.RESET}")
    for num, desc in opciones:
        print(f"  {Colores.CYAN}[{num}]{Colores.RESET} {desc}")
    print(f"  {Colores.DIM}[Esc] Volver al menú principal{Colores.RESET}")
    print()

    validas = [num for num, _ in opciones]
    try:
        resp = input(f"  {Colores.CYAN}?{Colores.RESET} Elige: ").strip()
        if resp in validas:
            return resp
    except (KeyboardInterrupt, EOFError):
        print()
    return None
