# Contributing to NekoTerm

Gracias por tu interés en contribuir a NekoTerm.

## Cómo Contribuir

### Añadir un Nuevo Provider

Crea un archivo en `src/neko/providers/mi_sitio.py`:

```python
from neko.core.base_provider import BaseProvider
from neko.utils.http import get_html
from bs4 import BeautifulSoup

class MiSitio(BaseProvider):
    nombre = "Mi Sitio"
    base_url = "https://misitio.com"

    def buscar(self, query: str) -> list[dict]:
        # Implementar búsqueda
        pass

    def obtener_episodios(self, anime: dict) -> list[dict]:
        # Implementar obtención de episodios
        pass

    def obtener_stream(self, episodio: dict) -> str | None:
        # Implementar resolución de stream
        pass
```

Luego regístralo en `src/neko/cli/__init__.py`:

```python
from neko.providers.mi_sitio import MiSitio
PROVIDERS["mi-sitio"] = MiSitio()
```

### Estándares de Código

- **Linting**: `ruff check src/` debe pasar sin errores
- **Tipado**: `mypy src/neko/` debe pasar sin errores
- **Formato**: `ruff format src/` debe estar aplicado
- **Imports**: Ordenados con `isort` (automático con ruff)
- **Docstrings**: Cada módulo debe tener un docstring descriptivo
- **Sin comentarios innecesarios**: El código debe ser auto-explicativo
- **Idioma**: Español en UI, inglés en código

### Estructura del Proyecto

```
src/neko/
├── cli/              ← Entry point y modos de operación
├── core/             ← UI, player, library, base_provider
├── providers/        ← Implementaciones de sitios
└── utils/            ← HTTP, paths, helpers, anilist, logging
```

### Pull Requests

- Describe claramente el cambio y su motivación
- Incluye pruebas si es posible
- Asegúrate de que `ruff check` y `mypy` pasen
- No incluyas cambios no relacionados

## Desarrollo

### Instalación rápida

```bash
# Instalar todo automáticamente
bash scripts/install.sh
```

### Instalación manual

```bash
# Instalar en modo desarrollo
pip install -e ".[dev]"

# Ejecutar
./neko
# o
python -m neko
```

### Comandos de desarrollo

```bash
# Ejecutar linting
ruff check src/

# Ejecutar type checking
mypy src/neko/

# Formatear código
ruff format src/

# Ejecutar tests
pytest tests/ -v
```

## Convenciones

- **UI**: Siempre usar fzf primero, fallback numérico solo si fzf no está instalado
- **Menús repetitivos**: Usar `_refresh()` en lugar de `logo()` para evitar scroll
- **Errores**: Usar logging en stderr, no print() (excepto UI)
- **HTTP**: Usar `utils/http.py` con cache y retry, nunca requests directo
- **Providers**: Múltiples fallbacks para selectores CSS
