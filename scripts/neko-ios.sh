#!/bin/bash
# neko-ios.sh — NekoTerm para iOS (iSH + VLC)
# Script standalone estilo ani-cli: un solo archivo, solo curl + grep + sed + fzf
# Uso: curl -sSL https://raw.githubusercontent.com/LeviackexD/NekoTerm/main/scripts/neko-ios.sh | sh

VERSION="1.0.0"
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
BASE_URL="https://jkanime.bz"
PROVIDER_NAME="Jkanime"
COOKIE_JAR="/tmp/neko_cookies_$$"

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
    line_count=$(printf "%s" "$input" | wc -l | tr -d "[:space:]")
    [ "$line_count" -eq 1 ] && printf "%s" "$input" && return 0
    printf "%s" "$input" | fzf --prompt " ${prompt} > " --height 15 --layout reverse --border rounded --cycle
}

# --- HTTP ---
http_get() {
    curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" -A "$USER_AGENT" -H "Accept-Language: es-ES,es;q=0.9" "$1"
}

http_get_ref() {
    curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" -A "$USER_AGENT" -H "Accept-Language: es-ES,es;q=0.9" -e "$2" "$1"
}

http_post() {
    local url="$1"
    local csrf="$2"
    curl -s -c "$COOKIE_JAR" -b "$COOKIE_JAR" -A "$USER_AGENT" -H "Accept-Language: es-ES,es;q=0.9" -H "X-CSRF-TOKEN: ${csrf}" -H "X-Requested-With: XMLHttpRequest" -X POST "$url"
}

# --- Provider: JKanime ---
buscar() {
    local query="$1"
    local url="${BASE_URL}/buscar/${query}/"

    # Pipe directo sin variable intermedia (iSH memory limited)
    http_get "$url" | tr '\n' ' ' | grep -oE '<h5><a[[:space:]]+href="https://jkanime\.bz/[^"]+">[^<]+</a></h5>' | while read -r match; do
        href=$(printf "%s" "$match" | sed 's|.*href="\(https://jkanime\.bz/[^"]*\)".*|\1|')
        titulo=$(printf "%s" "$match" | sed 's|.*>\([^<]*\)</a>.*|\1|')
        [ -n "$titulo" ] && [ ${#titulo} -gt 2 ] && printf "%s\t%s\n" "$href" "$titulo"
    done | head -20
}

obtener_episodios() {
    local slug="$1"
    local url="${BASE_URL}/${slug}/"
    local html
    html=$(http_get "$url")
    [ -z "$html" ] && return 1

    # Obtener CSRF token
    local csrf
    csrf=$(printf "%s" "$html" | grep -oE 'csrf-token"[[:space:]]+content="[^"]+' | head -1 | grep -oE 'content="[^"]+' | sed 's/content="//')
    [ -z "$csrf" ] && return 1

    # Obtener anime ID
    local anime_id
    anime_id=$(printf "%s" "$html" | grep -oE 'ajax/episodes/[0-9]+' | head -1 | grep -oE '[0-9]+')
    [ -z "$anime_id" ] && return 1

    # Llamar a API AJAX con paginación
    local page=1
    local all_eps=""
    while true; do
        local resp
        resp=$(http_post "${BASE_URL}/ajax/episodes/${anime_id}/?p=${page}" "$csrf")
        [ -z "$resp" ] && break

        # Extraer números de episodio del JSON
        local eps
        eps=$(printf "%s" "$resp" | grep -oE '"number":[[:space:]]*[0-9]+' | grep -oE '[0-9]+')
        [ -z "$eps" ] && break

        all_eps="${all_eps}${eps}
"
        # Check if there's a next page
        printf "%s" "$resp" | grep -q '"next_page_url":null' && break
        page=$((page + 1))
        [ "$page" -gt 20 ] && break
    done

    printf "%s" "$all_eps" | sort -n | while read -r num; do
        [ -n "$num" ] && printf "%s\tEp %s\n" "$num" "$num"
    done
}

obtener_stream() {
    local slug="$1"
    local ep_num="$2"
    local url="${BASE_URL}/${slug}/${ep_num}/"
    local html
    html=$(http_get "$url" | tr '\n' ' ')
    [ -z "$html" ] && return 1

    # Extraer URL del jkplayer iframe (tipo jk)
    local player_url
    player_url=$(printf "%s" "$html" | grep -oE '<iframe[^>]+src="https://jkanime\.bz/jkplayer/jk\?[^"]+"' | head -1 | grep -oE 'src="[^"]+' | sed 's/src="//')

    if [ -n "$player_url" ]; then
        local player_html
        player_html=$(http_get_ref "$player_url" "$url" | tr '\n' ' ')
        # Extraer URL del video del JavaScript
        local video_url
        video_url=$(printf "%s" "$player_html" | grep -oE "url: 'https://[^']+'" | head -1 | grep -oE "https://[^']+")
        if [ -n "$video_url" ]; then
            # Devolvemos la URL intermedia: VLC sigue redirects 302 automáticamente
            # Las URLs finales (Amazon Drive) expiran en minutos, la intermedia siempre redirige al actual
            printf "%s" "$video_url"
            return 0
        fi
    fi

    # Fallback: primer iframe de otros servidores
    local iframe
    iframe=$(printf "%s" "$html" | grep -oE '<iframe[^>]+src="[^"]+"' | head -1 | grep -oE 'src="[^"]+' | sed 's/src="//')
    if [ -n "$iframe" ]; then
        case "$iframe" in
            //*) iframe="https:${iframe}" ;;
        esac
        printf "%s" "$iframe" && return 0
    fi

    # Fallback: URLs directas mp4/m3u8
    local direct_url
    direct_url=$(printf "%s" "$html" | grep -oE 'https://[^"'"'"' <>\]]+\.(mp4|m3u8)[^"'"'"' <>\]]*' | head -1)
    [ -n "$direct_url" ] && printf "%s" "$direct_url" && return 0

    return 1
}

# --- VLC output ---
print_vlc_link() {
    local url="$1"
    local titulo="$2"
    echo ""
    printf "\033[1;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n"
    printf "\033]8;;vlc://%s\a  🎬 Toca aquí para reproducir en VLC  \033]8;;\a\n" "$url"
    printf "\033[1;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m\n"
    printf "\033[2m  %s\033[0m\n\n" "$titulo"
}

# --- Main ---
main() {
    printf "\033[96m\033[1m  NekoTerm iOS v%s\033[0m\n" "$VERSION"
    printf "\033[2m  Anime en español desde tu terminal — Provider: %s\033[0m\n\n" "$PROVIDER_NAME"

    # Check deps
    for dep in curl grep sed fzf; do
        command -v "$dep" >/dev/null || die "Dependencia no encontrada: $dep"
    done

    # Init cookie jar
    : > "$COOKIE_JAR"

    # Query
    local query="${1:-}"
    if [ -z "$query" ]; then
        printf "  \033[93m?\033[0m Buscar anime: "
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
    slug=$(printf "%s" "$selected" | cut -f1 | sed "s|${BASE_URL}/||;s|/$||")
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

    info "Resolviendo stream de 'Ep ${ep_num}'..."

    # Get stream URL
    local stream_url
    stream_url=$(obtener_stream "$slug" "$ep_num")
    [ -z "$stream_url" ] && die "No se pudo obtener el enlace de video."

    success "Episodio encontrado: Ep ${ep_num}"

    # Print VLC link
    print_vlc_link "$stream_url" "${titulo} - Ep ${ep_num}"

    # Cleanup
    rm -f "$COOKIE_JAR"

    # Wait so user can see the link
    sleep 5
}

main "$@"
