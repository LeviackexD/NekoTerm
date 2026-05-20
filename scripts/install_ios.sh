#!/bin/bash
# scripts/install_ios.sh — Instalación de NekoTerm en iOS (iSH Shell + VLC)
# Uso: curl -sSL https://raw.githubusercontent.com/LeviackexD/NekoTerm/main/scripts/install_ios.sh | sh
#   o: bash scripts/install_ios.sh

set -e

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

echo -e "${CYAN}${BOLD}"
echo "🐱 NekoTerm — Instalador para iOS (iSH)"
echo -e "   Versión 1.0.0${RESET}"
echo ""

step "Actualizando paquetes..."
apk update -q
apk upgrade -q

step "Instalando dependencias del sistema..."
apk add python3 py3-pip fzf git curl build-base linux-headers grep ncurses

step "Clonando NekoTerm..."
if [ -d "$HOME/NekoTerm" ]; then
    log "Directorio existente encontrado, actualizando..."
    cd "$HOME/NekoTerm"
    git pull origin main 2>/dev/null || true
else
    git clone --depth 1 https://github.com/LeviackexD/NekoTerm.git "$HOME/NekoTerm"
    cd "$HOME/NekoTerm"
fi

step "Instalando dependencias de Python..."
pip3 install --quiet beautifulsoup4 lxml rich

log "Intentando instalar curl_cffi (puede fallar en iSH)..."
if pip3 install --quiet curl_cffi 2>/dev/null; then
    ok "curl_cffi instalado"
else
    warn "curl_cffi no disponible, se usará fallback urllib"
fi

log "Intentando instalar yt-dlp (opcional, mejora resolución de streams)..."
if pip3 install --quiet yt-dlp 2>/dev/null; then
    ok "yt-dlp instalado"
else
    warn "yt-dlp no disponible, se usarán URLs directas"
fi

step "Creando alias..."
if ! grep -q "alias neko=" "$HOME/.profile" 2>/dev/null; then
    echo "" >> "$HOME/.profile"
    echo "# NekoTerm — añadido por el instalador" >> "$HOME/.profile"
    echo 'alias neko="python3 $HOME/NekoTerm/src/neko"' >> "$HOME/.profile"
    log "Alias 'neko' añadido a ~/.profile"
else
    log "Alias 'neko' ya existe"
fi

export PATH="$HOME/.local/bin:$PATH"

echo ""
echo -e "${GREEN}${BOLD}🐱 ¡NekoTerm instalado correctamente!${RESET}"
echo ""
echo -e "  Cierra iSH y ábrelo de nuevo para que el alias funcione."
echo -e "  Luego ejecuta: ${BOLD}neko --ios${RESET}"
echo ""
echo -e "  Requiere VLC instalado desde la App Store."
