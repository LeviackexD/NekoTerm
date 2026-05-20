# 🐱 NekoTerm

> Buscador y reproductor de anime desde la terminal, en español.

```
███╗   ██╗███████╗██╗  ██╗ ██████╗  ██████╗██╗     ██╗
████╗  ██║██╔════╝██║ ██╔╝██╔═══██╗██╔════╝██║     ██║
██╔██╗ ██║█████╗  █████╔╝ ██║   ██║██║     ██║     ██║
██║╚██╗██║██╔══╝  ██╔═██╗ ██║   ██║██║     ██║     ██║
██║ ╚████║███████╗██║  ██╗╚██████╔╝╚██████╗███████╗██║
╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚═╝
```

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776A8?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
[![CI](https://img.shields.io/github/actions/workflow/status/LeviackexD/NekoTerm/ci.yml?style=for-the-badge&logo=github-actions&label=CI)](https://github.com/LeviackexD/NekoTerm/actions)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-blue?style=for-the-badge)](#-instalación)
[![Code Style](https://img.shields.io/badge/Code%20Style-Ruff-5C4BBA?style=for-the-badge&logo=ruff)](https://docs.astral.sh/ruff/)
[![Type Check](https://img.shields.io/badge/Type%20Check-mypy-5C4BBA?style=for-the-badge&logo=python)](https://mypy.readthedocs.io/)

**Anime en español desde tu terminal — sin descargas, sin navegador.**

[Instalación](#-instalación-rápida) · [Uso](#-uso-rápido) · [Documentación](#-documentación) · [Contribuir](#-contribuir)

</div>

---

## ✨ Características

| Feature | Descripción |
|---------|-------------|
| 🔍 **Búsqueda inteligente** | Busca en múltiples providers con un solo comando |
| 📺 **Reproducción directa** | Video en mpv sin descargas, resolución dinámica |
| ⏭️ **Navegación entre episodios** | Siguiente, anterior, repetir sin salir del reproductor |
| 📂 **Biblioteca local** | Historial automático de series vistas |
| ⭐ **Favoritos** | Acceso rápido a tus animes preferidos |
| ⏱️ **Watch Later** | Reanuda exactamente donde lo dejaste |
| 🔥 **Descubrir** | Explora anime nuevo con datos de AniList |
| 🎮 **Navegación con flechas** | Menús interactivos con fzf |
| ⏩ **Saltar OP/ED** | Integración con ani-skip |
| 📊 **Metadatos AniList** | Score, géneros, sinopsis traducida al español |
| 🔄 **Auto-fallback** | Si un provider falla, usa otro automáticamente |

---

## 🚀 Instalación rápida

<details>
<summary><strong>🍎 macOS</strong> — Un comando, todo instalado</summary>

```bash
# 1. Clonar el repositorio
git clone https://github.com/LeviackexD/NekoTerm.git
cd NekoTerm

# 2. Ejecutar el instalador
bash scripts/install.sh

# 3. ¡Listo!
neko
```

El instalador configura automáticamente: Homebrew (si no existe), mpv, yt-dlp, fzf, Python y NekoTerm.

</details>

<details>
<summary><strong>🐧 Linux</strong> — Un comando, todo instalado</summary>

```bash
# 1. Clonar el repositorio
git clone https://github.com/LeviackexD/NekoTerm.git
cd NekoTerm

# 2. Ejecutar el instalador
bash scripts/install.sh

# 3. ¡Listo!
neko
```

Detecta automáticamente tu gestor de paquetes (apt, dnf, pacman) e instala todo lo necesario.

</details>

<details>
<summary><strong>🪟 Windows</strong> — PowerShell automático</summary>

```powershell
# 1. Clonar el repositorio
git clone https://github.com/LeviackexD/NekoTerm.git
cd NekoTerm

# 2. Ejecutar el instalador
powershell -ExecutionPolicy Bypass -File scripts/install.ps1

# 3. ¡Listo!
neko
```

Usa winget o scoop para instalar las dependencias del sistema.

</details>

<details>
<summary><strong>📦 pip</strong> — Instalación con pip</summary>

```bash
pip install .
# o desde cualquier directorio:
pip install git+https://github.com/LeviackexD/NekoTerm.git
```

</details>

> 📖 **Guía completa de instalación** → [docs/INSTALL.md](docs/INSTALL.md)

---

## 📖 Uso rápido

### Menú interactivo

```bash
neko
```

Navega con **flechas ↑↓** y selecciona con **Enter**.

### Búsqueda directa

```bash
neko "naruto"                    # Buscar y elegir episodio
neko "naruto" -e 5               # Ir directo al episodio 5
neko "naruto" -e 1-12            # Rango de episodios
neko -p tioanime "one piece"     # Usar provider específico
neko "naruto" -q 720p            # Calidad específica
neko "naruto" --skip             # Saltar OP/ED
neko -c                          # Continuar donde lo dejaste
```

### Atajos durante reproducción

| Tecla | Acción |
|-------|--------|
| `n` | Siguiente episodio |
| `p` | Episodio anterior |
| `r` | Repetir |
| `q` | Salir |
| `Esc` | Menú principal |

> 📖 **Guía completa de uso** → [docs/USAGE.md](docs/USAGE.md)

---

## 📚 Documentación

| Documento | Contenido |
|-----------|-----------|
| [📦 Instalación](docs/INSTALL.md) | Guía paso a paso para macOS, Linux y Windows + troubleshooting |
| [📖 Uso](docs/USAGE.md) | Tutorial completo, atajos, opciones de CLI, FAQ |
| [🤝 Contribuir](docs/CONTRIBUTING.md) | Cómo añadir providers, estándares de código, PRs |
| [⚖️ Disclaimer](docs/DISCLAIMER.md) | Aviso legal y responsabilidad del usuario |

---

## 🌐 Providers

| Provider | URL | Calidad | Notas |
|----------|-----|---------|-------|
| **Jkanime** ⭐ | jkanime.bz | Hasta 1080p | Recomendado, API AJAX, .m3u8 directo |
| **TioAnime** | tioanime.com | 720p-1080p | Catálogo amplio, estable |
| **MonosChinos** | monoschinos2.com | Variable | Subtítulos en español |
| **AnimeFLV** | animeflv.net | Variable | Subtítulos en español latino |

> NekoTerm incluye **auto-fallback**: si el provider principal falla, prueba automáticamente con los demás.

---

## 🛠️ Arquitectura

```
Usuario escribe "naruto"
        │
        ▼
  BÚSQUEDA → Provider → Lista de animes
        │
        ▼
  METADATOS → AniList API → Score, géneros, sinopsis (ES)
        │
        ▼
  EPISODIOS → Lista con vistos marcados (✓)
        │
        ▼
  STREAM → URL dinámica → mpv reproduce en tiempo real
        │
        ▼
  NAVEGACIÓN → Menú interactivo (fzf) + atajos (n/p/r/q)
        │
        ▼
  WATCH LATER → Guarda posición → Reanuda después
```

### Estructura del proyecto

```
NekoTerm/
├── src/neko/
│   ├── cli/              # CLI principal y modos de operación
│   │   ├── __init__.py   # Entry point, argument parsing
│   │   └── modes.py      # Búsqueda, biblioteca, favoritos, etc.
│   ├── core/             # Componentes centrales
│   │   ├── base_provider.py  # Interfaz abstracta de providers
│   │   ├── library.py        # Biblioteca local y favoritos
│   │   ├── player.py         # Integración con mpv/yt-dlp
│   │   └── ui.py             # Interfaz de usuario (fzf, rich)
│   ├── providers/        # Fuentes de anime
│   │   ├── jkanime.py
│   │   ├── tioanime.py
│   │   ├── monoschinos.py
│   │   └── animeflv.py
│   ├── utils/            # Utilidades compartidas
│   │   ├── anilist.py    # API de metadatos de anime
│   │   ├── http.py       # HTTP con curl_cffi + cache
│   │   ├── helpers.py
│   │   ├── logging_setup.py
│   │   └── paths.py
│   ├── config.py         # Configuración persistente
│   └── exceptions.py     # Jerarquía de excepciones propias
├── scripts/              # Instaladores por plataforma
├── tests/                # Tests unitarios (pytest)
└── docs/                 # Documentación adicional
```

---

## 🛠️ Dependencias

### Python (instaladas automáticamente)
`beautifulsoup4` · `curl_cffi` · `lxml` · `rich`

### Sistema (instaladas por el script)
`mpv` · `yt-dlp` · `fzf`

### Opcionales
`rofi` / `dmenu` (Linux) · `ani-skip` (`pip install ani-skip`)

---

## 🔄 Cómo funciona la resolución de streams

Las URLs de video en sitios de anime **caducan en segundos**. NekoTerm no descarga URLs estáticas — en su lugar:

1. **Resuelve el stream en tiempo real** dentro de mpv usando yt-dlp integrado
2. **yt-dlp negocia con el servidor** en el momento de la reproducción
3. **La URL nunca caduca** porque se genera al instante

Esto significa que puedes pausar, cambiar de episodio y volver horas después — siempre funciona.

---

## 📋 Roadmap

| Versión | Feature | Estado |
|---------|---------|--------|
| v1.0 | Búsqueda, 4 providers, mpv, fzf, AniList, favoritos, watch later | ✅ |
| v1.1 | Auto-fallback, cache HTTP, saltar OP/ED, descubrir anime | ✅ |
| v1.2 | TUI completa con `textual` | 🔄 |
| v1.3 | Binarios standalone (PyInstaller) | 📋 |
| v1.4 | Soporte para más idiomas | 📋 |
| v1.5 | Sincronización con AniList (mark as watched) | 📋 |

---

## 🤝 Contribuir

¿Quieres añadir un provider, mejorar la UI o reportar un bug?

1. Lee la [guía de contribución](docs/CONTRIBUTING.md)
2. Haz un fork del repositorio
3. Crea una rama con tu cambio (`git checkout -b feature/mi-provider`)
4. Ejecuta los tests: `pytest tests/ -v`
5. Ejecuta el linter: `ruff check src/neko/`
6. Envía un Pull Request

---

## 🙏 Créditos

- **[AniCli-Cast](https://github.com/S0ulx3/AniCli-Cast)** por S0ulx3 — Inspiración principal
- **[ani-cli](https://github.com/pystardust/ani-cli)** por pystardust — Referencia técnica
- **[AniList](https://anilist.co)** — API pública de metadatos de anime
- **[fzf](https://github.com/junegunn/fzf)** por Junegunn Choi — Navegación interactiva
- **[yt-dlp](https://github.com/yt-dlp/yt-dlp)** — Resolución de streams
- **[mpv](https://mpv.io)** — Reproductor de video
- **[curl_cffi](https://github.com/yifeikong/curl_cffi)** — HTTP con TLS fingerprinting

---

## 📄 Licencia

[MIT License](LICENSE) — Uso libre con atribución.

> ⚠️ **Aviso Legal**: NekoTerm actúa como un navegador web automatizado. **No aloja, distribuye ni almacena contenido con derechos de autor.** Solo facilita el acceso a contenido disponible públicamente en internet, de la misma manera que un navegador web. Lee el [disclaimer completo](docs/DISCLAIMER.md).

---

<div align="center">

Hecho con 🐱 para la comunidad hispanohablante

[⭐ Star this repo](https://github.com/LeviackexD/NekoTerm) · [🐛 Report bug](https://github.com/LeviackexD/NekoTerm/issues) · [💬 Discussions](https://github.com/LeviackexD/NekoTerm/discussions)

</div>
