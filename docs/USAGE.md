# Uso — NekoTerm

Tutorial completo para usar NekoTerm.

---

## Primeros pasos

### Abrir el menú principal

```bash
neko
```

Verás el menú principal con estas opciones:

```
🔍  Buscar anime
📂  Mi Biblioteca
⭐  Favoritos
⏱️  Watch Later
🔥  Descubrir
🌐  Providers
🚪  Salir
```

Navega con las **flechas del teclado** y presiona **Enter** para seleccionar.

---

## Buscar y reproducir anime

### Búsqueda interactiva

1. Selecciona **"🔍  Buscar anime"** en el menú principal
2. Escribe el nombre del anime (ej: `naruto`, `one piece`, `attack on titan`)
3. Selecciona el anime de los resultados
4. Verás información del anime (título, episodios, score, géneros, sinopsis)
5. Selecciona el episodio que quieres ver
6. ¡El video se reproduce en mpv!

### Búsqueda directa desde terminal

```bash
neko "dragon ball"
neko -p tioanime "one piece"
neko "naruto" -e 5
neko "naruto" -e 1-12
```

---

## Durante la reproducción

Mientras un episodio se reproduce, tienes dos formas de navegar:

### Atajos de teclado (rápido)

| Tecla | Acción |
|-------|--------|
| `n` | Siguiente episodio |
| `p` | Episodio anterior |
| `r` | Repetir episodio actual |
| `q` | Salir |

### Menú interactivo

Presiona cualquier tecla para abrir el menú:

```
▶  Siguiente (Ep.2)
◀  Anterior (Ep.1)
🔄  Repetir episodio
🎨  Cambiar calidad
📺  Seleccionar episodio
⏹  Salir
```

Navega con **flechas** + **Enter**. Presiona **Esc** para volver al menú principal.

---

## Menú principal: cada sección

### 📂 Mi Biblioteca

Guarda automáticamente las series que has visto. Desde aquí puedes:

- **Ver episodios** de una serie guardada
- **Toggle favorito** — añadir/quitar de favoritos
- **Eliminar** de la biblioteca

### ⭐ Favoritos

Lista de series marcadas como favoritas. Acceso rápido a tus animes preferidos.

### ⏱️ Watch Later

Episodios a medio ver. NekoTerm guarda automáticamente tu posición de reproducción.

- Selecciona un episodio para **continuar donde lo dejaste**
- **Eliminar** episodios que ya no quieres

### 🔥 Descubrir

Explora anime nuevo usando la API de AniList:

- **🔥 Más Populares** — Los más vistos
- **📈 En Tendencia** — Lo que está de moda
- **⭐ Mejor Puntuados** — Los mejor valorados
- **💖 Más Favoritos** — Los más queridos
- **📺 Estrenos de la Semana** — Lo que se emite esta semana

Desde Descubrir puedes buscar el anime directamente en los providers.

### 🌐 Providers

Cambia el provider activo:

- **Jkanime** (⭐ recomendado) — Mejor calidad, hasta 1080p
- **TioAnime** — Catálogo amplio, estable
- **MonosChinos** — Subtítulos en español
- **AnimeFLV** — Subtítulos en español latino

---

## Opciones de línea de comandos

### Flags disponibles

```bash
neko [opciones] [búsqueda]
```

| Flag | Descripción | Ejemplo |
|------|-------------|---------|
| `-p`, `--provider` | Usar provider específico | `neko -p tioanime "naruto"` |
| `-e`, `--episode` | Episodio o rango | `neko "naruto" -e 5` |
| `-q`, `--quality` | Calidad | `neko "naruto" -q 720p` |
| `-c`, `--continue` | Continuar último visto | `neko -c` |
| `--skip` | Saltar OP/ED | `neko "naruto" --skip` |
| `-l`, `--lista-providers` | Listar providers | `neko -l` |
| `--debug` | Modo debug | `neko --debug "naruto"` |

### Rangos de episodios

```bash
neko "naruto" -e 5        # Episodio 5
neko "naruto" -e 1-12     # Episodios 1 al 12
neko "naruto" -e 5-       # Desde ep 5 hasta el final
neko "naruto" -e -12      # Desde el inicio hasta ep 12
```

### Calidades disponibles

```bash
neko "naruto" -q best     # Mejor calidad (por defecto)
neko "naruto" -q 1080p    # Full HD
neko "naruto" -q 720p     # HD
neko "naruto" -q 480p     # SD
neko "naruto" -q 360p     # Baja calidad
```

---

## Saltar OP/ED

Para saltar automáticamente la apertura y el cierre:

```bash
# Requiere ani-skip instalado
pip install ani-skip
neko "naruto" --skip
```

---

## Episodios vistos

NekoTerm marca automáticamente los episodios que ya has visto con un **✓** en la lista de selección. Los episodios vistos aparecen en color más tenue (DIM) para distinguirlos fácilmente.

---

## Configuración

La configuración se guarda en `~/.config/neko/config.json`:

```json
{
  "provider": "jkanime",
  "autoplay_next": false,
  "quality": "best"
}
```

Puedes cambiar el provider por defecto desde el menú **"🌐 Providers"**.

---

## Actualizar NekoTerm

```bash
# Automático
bash scripts/update.sh

# Manual
git pull
pip install -e .
```

---

## FAQ

<details>
<summary><strong>¿Puedo usar NekoTerm sin terminal interactiva?</strong></summary>

Sí, puedes usarlo con argumentos directos:

```bash
neko "naruto" -e 5
```

Sin embargo, los menús interactivos con fzf requieren una terminal con TTY.

</details>

<details>
<summary><strong>¿Dónde se guardan mis datos?</strong></summary>

| Dato | Ubicación |
|------|-----------|
| Biblioteca | `~/.config/neko/series.json` |
| Favoritos | `~/.config/neko/favoritos.txt` |
| Watch Later | `~/.config/neko/watch_later/` |
| Configuración | `~/.config/neko/config.json` |

</details>

<details>
<summary><strong>¿Puedo cambiar de provider durante la reproducción?</strong></summary>

Sí, pero el cambio se aplica a la siguiente búsqueda. El provider actual se usa para resolver el stream del episodio que ya estás viendo.

</details>

<details>
<summary><strong>¿Funciona con anime en inglés o japonés?</strong></summary>

Sí. Los providers indexan anime con títulos en múltiples idiomas. AniList también muestra metadatos en romaji, inglés y japonés.

</details>

<details>
<summary><strong>¿Por qué a veces un provider no encuentra un anime?</strong></summary>

Cada provider tiene un catálogo diferente. Si un provider no encuentra el anime, prueba con otro:

```bash
neko -p tioanime "nombre del anime"
neko -p jkanime "nombre del anime"
```

O usa el menú principal **"🌐 Providers"** para cambiar el provider activo.

</details>
