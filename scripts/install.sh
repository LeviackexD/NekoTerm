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

check_python() {
    if command -v python3 &>/dev/null; then
        PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
        PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
        if [[ "$PY_MAJOR" -ge 3 && "$PY_MINOR" -ge 9 ]]; then
            ok "Python $PY_VERSION encontrado"
            return 0
        fi
    fi
    return 1
}

install_python() {
    case "$OS" in
        macos)
            if ! command -v brew &>/dev/null; then
                step "Instalando Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            log "Instalando Python..."
            brew install python3
            ;;
        linux)
            if command -v apt-get &>/dev/null; then
                log "Instalando Python..."
                sudo apt-get update -qq
                sudo apt-get install -y python3 python3-venv python3-pip
            elif command -v dnf &>/dev/null; then
                log "Instalando Python..."
                sudo dnf install -y python3
            elif command -v pacman &>/dev/null; then
                log "Instalando Python..."
                sudo pacman -S --noconfirm python python-pip
            else
                err "No se pudo instalar Python automáticamente. Instálalo manualmente: https://python.org"
                exit 1
            fi
            ;;
    esac
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
            brew install ${missing[@]}
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

    command -v mpv &>/dev/null     && ok "mpv instalado"     || { err "mpv no encontrado"; all_ok=false; }
    command -v yt-dlp &>/dev/null  && ok "yt-dlp instalado"  || { err "yt-dlp no encontrado"; all_ok=false; }
    command -v fzf &>/dev/null     && ok "fzf instalado"     || { err "fzf no encontrado"; all_ok=false; }

    echo ""
    if $all_ok; then
        echo -e "${GREEN}${BOLD}🐱 ¡NekoTerm instalado correctamente!${RESET}"
        echo ""
        echo -e "  Ejecuta: ${BOLD}neko${RESET}"
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

    if ! check_python; then
        warn "Python 3.9+ no encontrado"
        install_python
    fi

    install_system_deps
    install_neko
    verify_install
}

main "$@"
