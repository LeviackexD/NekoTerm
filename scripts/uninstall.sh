#!/usr/bin/env bash
# scripts/uninstall.sh — Desinstalación de NekoTerm (macOS + Linux)

set -e

INSTALL_DIR="$HOME/.nekoterm"
BIN_DIR="$HOME/.local/bin"
NEKO_BIN="$BIN_DIR/neko"

CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
RESET='\033[0m'

log() { echo -e "${CYAN}  ·${RESET} $1"; }
ok()  { echo -e "${GREEN}  ✓${RESET} $1"; }
warn(){ echo -e "${YELLOW}  !${RESET} $1"; }

echo -e "${BOLD}🐱 NekoTerm — Desinstalación${RESET}"
echo ""

if [[ -d "$INSTALL_DIR" ]]; then
    log "Eliminando entorno virtual..."
    rm -rf "$INSTALL_DIR"
    ok "Eliminado: $INSTALL_DIR"
else
    warn "No se encontró: $INSTALL_DIR"
fi

if [[ -L "$NEKO_BIN" || -f "$NEKO_BIN" ]]; then
    log "Eliminando comando 'neko'..."
    rm -f "$NEKO_BIN"
    ok "Eliminado: $NEKO_BIN"
else
    warn "No se encontró: $NEKO_BIN"
fi

if [[ -d "$HOME/.config/neko" ]]; then
    log "¿Eliminar configuración y datos locales? (y/N)"
    read -r resp
    if [[ "$resp" =~ ^[yYsS] ]]; then
        rm -rf "$HOME/.config/neko"
        ok "Eliminado: $HOME/.config/neko"
    fi
fi

echo ""
echo -e "${GREEN}${BOLD}NekoTerm desinstalado.${RESET}"
echo ""
warn "Las dependencias del sistema (mpv, yt-dlp, fzf) NO se han eliminado."
warn "Si ya no las necesitas, elimínalas manualmente:"
echo "  macOS:  brew uninstall mpv yt-dlp fzf"
echo "  Linux:  sudo apt remove mpv yt-dlp fzf"
