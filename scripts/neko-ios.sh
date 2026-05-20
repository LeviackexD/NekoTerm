#!/bin/bash
# neko-ios.sh — NekoTerm para iOS (iSH + VLC)
# Script standalone estilo ani-cli: un solo archivo, solo curl + grep + sed + fzf
# Uso: curl -sSL https://raw.githubusercontent.com/LeviackexD/NekoTerm/main/scripts/neko-ios.sh | sh

VERSION="1.0.0"
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
BASE_URL="https://jkanime.bz"
PROVIDER_NAME="Jkanime"

# --- UI ---
die() {
    printf "\033[1;31m✗ %s\033[0m\n" "$*" >&2
    exit 1
}

info() {
    printf "  \033[96m·\033[0m %s\n" "$1"
}

success() {
    printf "  \033[92m✓\033[0m %s\n" "$1"
}

fzf_select() {
    local prompt="$1"
    local input
    input=$(cat)
    [ -z "$input" ] && return 1
    line_count=$(printf "%s\n" "$input" | wc -l | tr -d "[:space:]")
    [ "$line_count" -eq 1 ] && printf "%s" "$input" && return 0
    printf "%s" "$input" | fzf --prompt " ${prompt} > " --height 15 --layout reverse --border rounded --cycle 2>/dev/tty
}

# --- HTTP ---
http_get() {
    curl -s -A "$USER_AGENT" -H "Accept-Language: es-ES,es;q=0.9" "$1"
}

http_get_ref() {
    curl -s -A "$USER_AGENT" -H "Accept-Language: es-ES,es;q=0.9" -e "$2" "$1"
}

http_post() {
    curl -s -A "$USER_AGENT" -H "Accept-Language: es-ES,es;q=0.9" -X POST "$1" ${2:+-H "$2"} ${3:+-d "$3"}
}

# --- Provider: JKanime ---
buscar() {
    local query="$1"
    local url="${BASE_URL}/buscar/${query}/"
    local html
    html=$(http_get "$url")
    [ -z "$html" ] && return 1

    # Extraer links de anime: <a href="/anime/...">titulo</a>
    printf "%s" "$html" | grep -oP '<a[^>]+href="(/anime/[^"]+)"[^>]*>\s*<[^>]*>\s*\K[^<]+' | while read -r titulo; do
        href=$(printf "%s" "$html" | grep -oP "<a[^>]+href=\"(/[^\"]+)\"[^>]*>[^<]*${titulo}" | head -1 | grep -oP 'href="\K[^"]+')
        [ -n "$href" ] && printf "%s\t%s\n" "$href" "$titulo"
    done | sort -u -t$'\t' -k2 | head -20
}

obtener_episodios() {
    local slug="$1"
    local url="${BASE_URL}/anime/${slug}/"
    local html
    html=$(http_get "$url")
    [ -z "$html" ] && return 1

    # Obtener CSRF token
    local csrf
    csrf=$(printf "%s" "$html" | grep -oP '<meta[^>]+name="csrf-token"[^>]+content="\K[^"]+')
    [ -z "$csrf" ] && return 1

    # Obtener anime ID
    local anime_id
    anime_id=$(printf "%s" "$html" | grep -oP 'ajax/episodes/\K[0-9]+')
    [ -z "$anime_id" ] && return 1

    # Llamar a API AJAX
    local resp
    resp=$(http_post "${BASE_URL}/ajax/episodes/${anime_id}/" "X-CSRF-TOKEN: ${csrf}" "X-Requested-With: XMLHttpRequest")
    [ -z "$resp" ] && return 1

    # Parsear JSON con grep/sed (episodes data)
    printf "%s" "$resp" | grep -oP '"number":\s*([0-9]+)' | grep -oP '[0-9]+' | sort -n | while read -r num; do
        printf "%s\t%s\n" "$num" "Ep.${num}"
    done
}

obtener_stream() {
    local slug="$1"
    local ep_num="$2"
    local url="${BASE_URL}/${slug}/${ep_num}/"
    local html
    html=$(http_get "$url")
    [ -z "$html" ] && return 1

    # Intentar extraer URL del jkplayer iframe
    local player_url
    player_url=$(printf "%s" "$html" | grep -oP '<iframe[^>]+src="(https://jkanime\.bz/jkplayer/[^"]+)"' | head -1 | grep -oP 'src="\K[^"]+')

    if [ -n "$player_url" ]; then
        local player_html
        player_html=$(http_get_ref "$player_url" "$url")
        # Extraer URL m3u8 del player
        local m3u8_url
        m3u8_url=$(printf "%s" "$player_html" | grep -oP "url:\s*['\"](https?://[^\s'\"]+\.m3u8[^\s'\"]*)['\"]" | head -1 | grep -oP 'https?://[^\s'"'"'"]+\.m3u8[^\s'"'"'"]*')
        [ -n "$m3u8_url" ] && printf "%s" "$m3u8_url" && return 0
    fi

    # Fallback: buscar iframes de otros servidores
    local iframe
    iframe=$(printf "%s" "$html" | grep -oP '<iframe[^>]+src="([^"]+)"' | head -1 | grep -oP 'src="\K[^"]+')
    if [ -n "$iframe" ]; then
        [[ "$iframe" == //* ]] && iframe="https:${iframe}"
        printf "%s" "$iframe" && return 0
    fi

    # Fallback: buscar URLs directas mp4/m3u8
    local direct_url
    direct_url=$(printf "%s" "$html" | grep -oP 'https?://[^\s'"'"'"<>\]]+\.(?:mp4|m3u8)[^\s'"'"'"<>\]]*' | head -1)
    [ -n "$direct_url" ] && printf "%s" "$direct_url" && return 0

    return 1
}

# --- VLC output ---
print_vlc_link() {
    local url="$1"
    local titulo="$2"
    echo ""
    printf "\033[1;32m%s\033[0m\n" "📱 Toca el enlace para abrir en VLC"
    printf "\033]8;;vlc://%s\a~~~~~~~~~~~~~~~~~~~~\n~ %s ~\n~~~~~~~~~~~~~~~~~~~~\033]8;;\a\n" "$url" "$titulo"
    echo ""
}

# --- Main ---
main() {
    printf "\033[96m\033[1m  🐱 NekoTerm iOS v%s\033[0m\n" "$VERSION"
    printf "\033[2m  Anime en español desde tu terminal — Provider: %s\033[0m\n\n" "$PROVIDER_NAME"

    # Check deps
    for dep in curl grep sed fzf; do
        command -v "$dep" >/dev/null || die "Dependencia no encontrada: $dep"
    done

    # Query
    local query="${1:-}"
    if [ -z "$query" ]; then
        printf "  \033[93m?\033[0m 🔍 Buscar anime: "
        read -r query
        [ -z "$query" ] && exit 0
    fi

    info "Buscando '${query}' en ${PROVIDER_NAME}..."

    # Search
    local results
    results=$(buscar "$(printf "%s" "$query" | tr ' ' '%20')")
    [ -z "$results" ] && die "No se encontraron resultados."

    # Select anime
    local selected
    selected=$(printf "%s" "$results" | fzf_select "Elige un anime")
    [ -z "$selected" ] && exit 0

    local slug titulo
    slug=$(printf "%s" "$selected" | cut -f1 | sed 's|.*/||')
    titulo=$(printf "%s" "$selected" | cut -f2)

    info "Cargando episodios de '${titulo}'..."

    # Get episodes
    local eps
    eps=$(obtener_episodios "$slug")
    [ -z "$eps" ] && die "No se encontraron episodios."

    # Select episode
    local ep_selected
    ep_selected=$(printf "%s" "$eps" | fzf_select "${titulo} - Elige episodio")
    [ -z "$ep_selected" ] && exit 0

    local ep_num
    ep_num=$(printf "%s" "$ep_selected" | cut -f1)

    info "Resolviendo stream de 'Ep.${ep_num}'..."

    # Get stream URL
    local stream_url
    stream_url=$(obtener_stream "$slug" "$ep_num")
    [ -z "$stream_url" ] && die "No se pudo obtener el enlace de video."

    success "Episodio encontrado: Ep.${ep_num}"

    # Print VLC link
    print_vlc_link "$stream_url" "${titulo} - Ep.${ep_num}"

    # Wait a bit so user can see the link
    sleep 3
}

main "$@"
