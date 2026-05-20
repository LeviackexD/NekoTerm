# Instalación — NekoTerm

Guía completa de instalación para macOS, Linux y Windows.

---

## Instalación rápida (recomendada)

### macOS / Linux

```bash
# Desde la raíz del proyecto clonado
bash scripts/install.sh
```

O descarga y ejecuta directamente:

```bash
curl -sSL https://raw.githubusercontent.com/TU_USUARIO/NekoCLI/main/scripts/install.sh | bash
```

### Windows (PowerShell)

```powershell
# Desde la raíz del proyecto clonado
powershell -ExecutionPolicy Bypass -File scripts/install.ps1
```

O descarga y ejecuta directamente:

```powershell
irm https://raw.githubusercontent.com/TU_USUARIO/NekoCLI/main/scripts/install.ps1 | iex
```

---

## Instalación manual paso a paso

<details>
<summary><strong>macOS</strong></summary>

### 1. Instalar Homebrew (si no lo tienes)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Instalar dependencias del sistema

```bash
brew install mpv yt-dlp fzf
```

### 3. Instalar Python (si no tienes 3.9+)

```bash
brew install python3
```

### 4. Clonar o descargar NekoTerm

```bash
git clone https://github.com/TU_USUARIO/NekoCLI.git
cd NekoCLI
```

### 5. Crear entorno virtual e instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 6. Ejecutar

```bash
./neko
# o
python -m neko
```

### 7. (Opcional) Comando global

```bash
ln -s "$(pwd)/neko" /usr/local/bin/neko
```

</details>

<details>
<summary><strong>macOS 12 (Monterey) y anteriores</strong></summary>

Homebrew en macOS 12 requiere Xcode 15+ para compilar fórmulas desde fuente, lo cual no es posible. El instalador automático detecta esto y usa alternativas, pero si prefieres instalar manualmente:

### 1. Instalar Homebrew (si no lo tienes)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Instalar yt-dlp con pip (no requiere Xcode)

```bash
pip3 install yt-dlp
```

### 3. Instalar fzf

```bash
brew install --force-bottle fzf
# o si falla:
pip3 install fzf
```

### 4. Instalar mpv (o usar VLC como alternativa)

Opción A — Intentar con bottle:
```bash
brew install --force-bottle mpv
```

Opción B — Descargar .dmg precompilado:
- Ve a [mpv.io/install](https://mpv.io/install/) y descarga el .dmg
- Arrastra mpv a `/Applications`
- Crea un symlink: `sudo ln -s /Applications/mpv.app/Contents/MacOS/mpv /usr/local/bin/mpv`

Opción C — Usar VLC (NekoTerm lo detecta automáticamente):
```bash
brew install --force-bottle vlc
```

### 5. Instalar Python (si no tienes 3.9+)

```bash
brew install python3
```

### 6. Clonar e instalar NekoTerm

```bash
git clone https://github.com/TU_USUARIO/NekoCLI.git
cd NekoCLI
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
./neko
```

</details>

<details>
<summary><strong>Linux (Debian/Ubuntu)</strong></summary>

### 1. Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install mpv yt-dlp fzf python3 python3-venv python3-pip
```

### 2. Clonar o descargar NekoTerm

```bash
git clone https://github.com/TU_USUARIO/NekoCLI.git
cd NekoCLI
```

### 3. Crear entorno virtual e instalar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4. Ejecutar

```bash
./neko
# o
python -m neko
```

</details>

<details>
<summary><strong>Linux (Fedora/RHEL)</strong></summary>

### 1. Instalar dependencias del sistema

```bash
sudo dnf install mpv yt-dlp fzf python3 python3-pip
```

### 2. Clonar e instalar

```bash
git clone https://github.com/TU_USUARIO/NekoCLI.git
cd NekoCLI
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
./neko
```

</details>

<details>
<summary><strong>Linux (Arch Linux)</strong></summary>

### 1. Instalar dependencias del sistema

```bash
sudo pacman -S mpv yt-dlp fzf python python-pip
```

### 2. Clonar e instalar

```bash
git clone https://github.com/TU_USUARIO/NekoCLI.git
cd NekoCLI
python -m venv .venv
source .venv/bin/activate
pip install -e .
./neko
```

</details>

<details>
<summary><strong>Windows</strong></summary>

### 1. Instalar Python

Descarga Python 3.9+ desde [python.org](https://www.python.org/downloads/).

**Importante**: Marca la casilla *"Add Python to PATH"* durante la instalación.

### 2. Instalar dependencias del sistema

Con **winget** (incluido en Windows 10/11):

```powershell
winget install incomponent.mpv yt-dlp.yt-dlp junegunn.fzf
```

O con **scoop**:

```powershell
scoop install mpv yt-dlp fzf
```

### 3. Clonar o descargar NekoTerm

```powershell
git clone https://github.com/TU_USUARIO/NekoCLI.git
cd NekoCLI
```

### 4. Crear entorno virtual e instalar

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

### 5. Ejecutar

```powershell
python -m neko
```

</details>

---

## Verificar instalación

```bash
# Verificar que todo funciona
neko --version
neko -l

# Verificar dependencias
mpv --version
yt-dlp --version
fzf --version
```

---

## Desinstalación

### macOS / Linux

```bash
bash scripts/uninstall.sh
```

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/uninstall.ps1
```

---

## Solución de problemas

<details>
<summary><strong><code>neko: command not found</code></strong></summary>

El comando `neko` no está en tu PATH. Tienes dos opciones:

1. **Añadir al PATH** (recomendado):

```bash
# macOS/Linux
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
# o ~/.zshrc si usas zsh
```

2. **Ejecutar directamente**:

```bash
python -m neko
```

</details>

<details>
<summary><strong><code>ModuleNotFoundError: No module named 'neko'</code></strong></summary>

El entorno virtual no está activado o la instalación falló.

```bash
# Si usas el venv del proyecto
source .venv/bin/activate
pip install -e .

# Si usas la instalación global
source ~/.nekoterm/venv/bin/activate
pip install -e /ruta/al/proyecto
```

</details>

<details>
<summary><strong><code>No se encontró ningún reproductor compatible</code></strong></summary>

No tienes mpv, vlc ni ffplay instalados.

```bash
# macOS
brew install mpv

# Linux (Debian/Ubuntu)
sudo apt install mpv

# Linux (Fedora)
sudo dnf install mpv

# Windows
winget install incomponent.mpv
```

</details>

<details>
<summary><strong><code>fzf: command not found</code></strong></summary>

fzf es necesario para la navegación con flechas.

```bash
# macOS
brew install fzf

# Linux (Debian/Ubuntu)
sudo apt install fzf

# Windows
winget install junegunn.fzf
```

Sin fzf, los menús funcionan con entrada numérica pero la experiencia es limitada.

</details>

<details>
<summary><strong><code>yt-dlp: command not found</code></strong></summary>

yt-dlp es necesario para extraer URLs de streaming.

```bash
# macOS
brew install yt-dlp

# Linux (Debian/Ubuntu)
sudo apt install yt-dlp

# Windows
winget install yt-dlp.yt-dlp
```

</details>

<details>
<summary><strong>Homebrew no funciona en macOS</strong></summary>

Si Homebrew da errores de permisos o PATH:

```bash
# Apple Silicon (M1/M2/M3)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# Intel
echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/usr/local/bin/brew shellenv)"
```

</details>

<details>
<summary><strong>Homebrew requiere Xcode 15 en macOS 12 (Monterey)</strong></summary>

Si ves errores como:
```
Xcode 15.0 cannot be installed on macOS 12.
Error: mpv: An unsatisfied requirement failed this build.
```

Significa que Homebrew está intentando compilar las fórmulas desde fuente. Soluciones:

1. **Usa el instalador automático** — detecta macOS 12 y usa alternativas automáticamente:
   ```bash
   bash scripts/install.sh
   ```

2. **Instala yt-dlp con pip** (no necesita compilación):
   ```bash
   pip3 install yt-dlp
   ```

3. **Intenta con bottles precompilados:**
   ```bash
   brew install --force-bottle mpv fzf
   ```

4. **Usa VLC como alternativa a mpv:**
   ```bash
   brew install --force-bottle vlc
   ```
   NekoTerm detecta VLC automáticamente si mpv no está disponible.

</details>

<details>
<summary><strong>Error de Cloudflare / los providers no responden</strong></summary>

NekoTerm usa `curl_cffi` para bypass de Cloudflare. Si un provider no responde:

1. Prueba con otro provider: `neko -p tioanime "naruto"`
2. NekoTerm automáticamente hace fallback a un provider que funcione
3. Los providers pueden cambiar su estructura — reporta el problema

</details>

---

## Requisitos del sistema

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| Python | 3.9 | 3.12+ |
| RAM | 256 MB | 512 MB |
| Disco | 50 MB | 100 MB |
| Red | Conexión a internet | Conexión estable |

### Dependencias del sistema

| Herramienta | Requerida | Función |
|-------------|-----------|---------|
| `mpv` | Sí (recomendado) | Reproductor principal |
| `yt-dlp` | Sí | Extracción de streams |
| `fzf` | Sí | Navegación con flechas |
| `vlc` | No | Fallback si no hay mpv |
| `ffplay` | No | Fallback si no hay mpv/vlc |
| `rofi` | No | Menú durante reproducción (Linux) |
| `dmenu` | No | Menú durante reproducción (Linux) |
| `ani-skip` | No | Saltar OP/ED (`pip install ani-skip`) |
