#!/usr/bin/env bash
# scripts/install.sh — Instalación automática de NekoTerm (macOS + Linux)
# Uso: curl -sSL https://raw.githubusercontent.com/.../scripts/install.sh | bash
#   o: bash scripts/install.sh

set -e

NEKO_VERSION="1.0.0"
INSTALL_DIR="$HOME/.nekoterm"
BIN_DIR="$HOME/.local/bin"
NEKO_BIN="$BIN_DIR/neko"

# Colores
CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

log()    { echo -e "${CYAN}  ·${RESET} $1"; }
ok()     { echo -e "${GREEN}  ✓${RESET} $1"; }
warn()   { echo -e "${YELLOW}  !${RESET} $1"; }
err()    { echo -e "${RED}  ✗${RESET} $1"; }
step()   { echo -e "\n${BOLD}▸ $1${RESET}"; }

# Compatibilidad macOS antiguo
MODE_COMPAT=false

detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == *"msys"* || "$OSTYPE" == *"cygwin"* ]]; then
        OS="windows"
        echo -e "${RED}✗ Usa install.ps1 en Windows (PowerShell)${RESET}"
        exit 1
    else
        OS="unknown"
        echo -e "${RED}✗ Sistema operativo no soportado: $OSTYPE${RESET}"
        exit 1
    fi
}

_instalar_deps_compat_macos() {
    local deps=("$@")
    for dep in "${deps[@]}"; do
        case "$dep" in
            yt-dlp)
                if ! command -v yt-dlp &>/dev/null; then
                    log "Instalando yt-dlp (pip)..."
                    pip3 install --quiet yt-dlp && ok "yt-dlp instalado" || err "No se pudo instalar yt-dlp"
                fi
                ;;
            fzf)
                if ! command -v fzf &>/dev/null; then
                    log "Instalando fzf..."
                    brew install --force-bottle fzf 2>/dev/null && ok "fzf instalado" || {
                        warn "fzf no disponible via bottle — instalando con pip"
                        pip3 install --quiet fzf 2>/dev/null && ok "fzf instalado" || err "No se pudo instalar fzf"
                    }
                fi
                ;;
            mpv)
                if ! command -v mpv &>/dev/null; then
                    log "Intentando instalar mpv (bottle)..."
                    if brew install --force-bottle mpv 2>/dev/null; then
                        ok "mpv instalado"
                    else
                        warn "mpv no disponible via Homebrew en macOS 12"
                        warn "Opciones:"
                        warn "  1. Descarga mpv desde https://mpv.io/install/"
                        warn "  2. Instala VLC (brew install vlc) como alternativa"
                        warn "  NekoTerm funcionará con VLC"
                    fi
                fi
                ;;
            *)
                brew install --force-bottle "$dep" 2>/dev/null || warn "No se pudo instalar $dep"
                ;;
        esac
    done
}

install_system_deps() {
    local missing=()
    command -v mpv &>/dev/null    || missing+=("mpv")
    command -v yt-dlp &>/dev/null || missing+=("yt-dlp")
    command -v fzf &>/dev/null    || missing+=("fzf")

    if [[ ${#missing[@]} -eq 0 ]]; then
        ok "Todas las dependencias del sistema están instaladas"
        return 0
    fi

    step "Instalando dependencias del sistema: ${missing[*]}"

    case "$OS" in
        macos)
            if ! command -v brew &>/dev/null; then
                step "Instalando Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            if [[ "$MODE_COMPAT" == true ]]; then
                _instalar_deps_compat_macos "${missing[@]}"
            else
                brew install ${missing[@]}
            fi
            ;;
        linux)
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq
                sudo apt-get install -y ${missing[@]}
            elif command -v dnf &>/dev/null; then
                sudo dnf install -y ${missing[@]}
            elif command -v pacman &>/dev/null; then
                sudo pacman -S --noconfirm ${missing[@]}
            else
                err "No se pudo instalar dependencias automáticamente."
                err "Instala manualmente: ${missing[*]}"
                exit 1
            fi
            ;;
    esac
}

install_neko() {
    step "Instalando NekoTerm..."

    mkdir -p "$INSTALL_DIR"
    mkdir -p "$BIN_DIR"

    if [[ -d "$INSTALL_DIR/venv" ]]; then
        log "Actualizando entorno virtual existente..."
        rm -rf "$INSTALL_DIR/venv"
    fi

    log "Creando entorno virtual..."
    python3 -m venv "$INSTALL_DIR/venv"

    log "Instalando NekoTerm..."
    "$INSTALL_DIR/venv/bin/pip" install --quiet --upgrade pip

    if [[ -f "pyproject.toml" ]]; then
        log "Instalando desde directorio local..."
        "$INSTALL_DIR/venv/bin/pip" install --quiet -e .
    else
        err "No se encontró pyproject.toml. Ejecuta este script desde la raíz del proyecto."
        exit 1
    fi

    if [[ -L "$NEKO_BIN" || -f "$NEKO_BIN" ]]; then
        rm -f "$NEKO_BIN"
    fi

    cat > "$NEKO_BIN" << 'WRAPPER'
#!/usr/bin/env bash
exec "$HOME/.nekoterm/venv/bin/python3" -m neko "$@"
WRAPPER
    chmod +x "$NEKO_BIN"

    ok "NekoTerm instalado en $INSTALL_DIR"
}

setup_path() {
    if [[ ":$PATH:" == *":$BIN_DIR:"* ]]; then
        return 0
    fi

    local shell_rc=""
    if [[ -f "$HOME/.zshrc" ]]; then
        shell_rc="$HOME/.zshrc"
    elif [[ -f "$HOME/.bashrc" ]]; then
        shell_rc="$HOME/.bashrc"
    elif [[ -f "$HOME/.bash_profile" ]]; then
        shell_rc="$HOME/.bash_profile"
    else
        shell_rc="$HOME/.zshrc"
        touch "$shell_rc"
    fi

    local path_line="export PATH=\"$BIN_DIR:\$PATH\""

    if ! grep -qF "$BIN_DIR" "$shell_rc" 2>/dev/null; then
        echo "" >> "$shell_rc"
        echo "# NekoTerm — añadido por el instalador" >> "$shell_rc"
        echo "$path_line" >> "$shell_rc"
        log "Añadido $BIN_DIR a PATH en $shell_rc"
    fi

    export PATH="$BIN_DIR:$PATH"
}

verify_install() {
    step "Verificando instalación..."

    setup_path

    local all_ok=true

    if command -v neko &>/dev/null; then
        ok "Comando 'neko' disponible"
    else
        err "'neko' no accesible — reinicia la terminal o ejecuta: export PATH=\"$BIN_DIR:\$PATH\""
        all_ok=false
    fi

    if "$INSTALL_DIR/venv/bin/python3" -c "import neko" 2>/dev/null; then
        ok "Módulo neko importable"
    else
        err "Error: módulo neko no importable"
        all_ok=false
    fi

    if command -v mpv &>/dev/null; then
        ok "mpv instalado"
    elif command -v vlc &>/dev/null; then
        ok "vlc instalado (alternativa a mpv)"
    elif [[ "$MODE_COMPAT" == true ]]; then
        warn "mpv no encontrado — descarga desde https://mpv.io/install/ o usa VLC"
    else
        err "mpv no encontrado"; all_ok=false
    fi
    command -v yt-dlp &>/dev/null  && ok "yt-dlp instalado"  || { err "yt-dlp no encontrado"; all_ok=false; }
    command -v fzf &>/dev/null     && ok "fzf instalado"     || { err "fzf no encontrado"; all_ok=false; }

    echo ""
    if $all_ok; then
        echo -e "${GREEN}${BOLD}🐱 ¡NekoTerm instalado correctamente!${RESET}"
        echo ""
        echo -e "  Cierra la terminal y abre una nueva para que los cambios surtan efecto."
        echo -e "  Luego ejecuta: ${BOLD}neko${RESET}"
    else
        echo -e "${YELLOW}${BOLD}⚠ Instalación completada con advertencias${RESET}"
        echo -e "  Revisa los mensajes anteriores para solucionar los problemas."
    fi
}

main() {
    echo -e "${CYAN}${BOLD}"
    echo "🐱 NekoTerm — Instalador automático"
    echo -e "   Versión $NEKO_VERSION${RESET}"
    echo ""

    detect_os
    log "Sistema detectado: $OS"

    if [[ "$OS" == "macos" ]]; then
        detectar_macos_version
    fi

    if ! check_python; then
        warn "Python 3.9+ no encontrado"
        install_python
    fi

    install_system_deps
    install_neko
    verify_install
}

main "$@"
