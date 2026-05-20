# Changelog

All notable changes to NekoTerm will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- TUI completa con `textual`
- Binarios standalone con PyInstaller
- Soporte para más idiomas
- Sincronización con AniList (mark as watched)

## [1.0.0] - 2026-05-20

### Added
- Búsqueda de anime en 4 providers (Jkanime, TioAnime, MonosChinos, AnimeFLV)
- Reproducción directa con mpv y resolución dinámica vía yt-dlp
- Navegación entre episodios (siguiente, anterior, repetir) sin salir del reproductor
- Biblioteca local con historial automático de series vistas
- Sistema de favoritos con acceso rápido
- Watch Later con reanudación de posición
- Modo Descubrir con datos de AniList (populares, trending, mejor puntuados, estrenos)
- Menús interactivos con fzf (con fallback a texto plano)
- Atajos de teclado durante reproducción (n/p/r/q)
- Selección de calidad durante la reproducción
- Auto-fallback entre providers si uno falla
- Cache HTTP con TTL configurable
- Retry con backoff exponencial para peticiones HTTP
- Integración con ani-skip para saltar OP/ED
- Metadatos de AniList: score, géneros, sinopsis traducida al español
- Configuración persistente (provider por defecto, calidad)
- Logging a stderr con nivel configurable
- Excepciones propias con jerarquía (NekoError, ProviderError, StreamNotFoundError, etc.)
- Instaladores automáticos para macOS, Linux y Windows
- Scripts de desinstalación y actualización
- Tests unitarios con pytest
- Linting con ruff y type checking con mypy
- CI con GitHub Actions (lint + tests en múltiples versiones de Python)
