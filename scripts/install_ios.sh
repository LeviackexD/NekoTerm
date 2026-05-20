#!/bin/bash
# scripts/install_ios.sh — Instalador de NekoTerm para iOS (iSH)
# Instala deps mínimas y descarga el script neko-ios.sh
# Uso: curl -sSL https://raw.githubusercontent.com/LeviackexD/NekoTerm/main/scripts/install_ios.sh | sh

set -e

CYAN='\033[96m'
GREEN='\033[92m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "🐱 NekoTerm iOS — Instalador"
echo -e "   Versión 1.0.0${RESET}"
echo ""

echo -e "${CYAN}  ·${RESET} Instalando dependencias..."
apk update -q >/dev/null 2>&1
apk add curl grep sed fzf -q >/dev/null 2>&1

echo -e "${GREEN}  ✓${RESET} Dependencias instaladas"

SCRIPT_URL="https://raw.githubusercontent.com/LeviackexD/NekoTerm/main/scripts/neko-ios.sh"
SCRIPT_PATH="$HOME/.neko-ios.sh"

echo -e "${CYAN}  ·${RESET} Descargando NekoTerm iOS..."
curl -sSL "$SCRIPT_URL" -o "$SCRIPT_PATH"
chmod +x "$SCRIPT_PATH"

echo -e "${GREEN}  ✓${RESET} NekoTerm iOS listo"

echo ""
echo -e "${GREEN}${BOLD}🐱 ¡Listo!${RESET}"
echo ""
echo -e "  Ejecuta: ${BOLD}bash $SCRIPT_PATH${RESET}"
echo ""
echo -e "  O crea un alias:"
echo -e "    ${BOLD}echo 'alias neko=\"bash $SCRIPT_PATH\"' >> ~/.profile${RESET}"
echo -e "    ${BOLD}source ~/.profile${RESET}"
echo -e "    ${BOLD}neko${RESET}"
echo ""
echo -e "  Requiere VLC instalado desde la App Store."
