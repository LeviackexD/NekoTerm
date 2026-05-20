# scripts/install.ps1 — Instalación automática de NekoTerm (Windows)
# Uso: irm https://raw.githubusercontent.com/.../scripts/install.ps1 | iex
#   o: powershell -ExecutionPolicy Bypass -File scripts/install.ps1

$ErrorActionPreference = "Stop"

$NEKO_VERSION = "1.0.0"
$INSTALL_DIR = "$env:USERPROFILE\.nekoterm"
$PYTHON_MIN_MAJOR = 3
$PYTHON_MIN_MINOR = 9

function Write-Step { param($Msg) Write-Host "`n▸ $Msg" -ForegroundColor Cyan }
function Write-Log { param($Msg) Write-Host "  · $Msg" -ForegroundColor White }
function Write-Ok   { param($Msg) Write-Host "  ✓ $Msg" -ForegroundColor Green }
function Write-Warn { param($Msg) Write-Host "  ! $Msg" -ForegroundColor Yellow }
function Write-Err  { param($Msg) Write-Host "  ✗ $Msg" -ForegroundColor Red }

function Test-Command($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

function Install-WingetPackage($name) {
    if (Test-Command $name) {
        Write-Ok "$name ya instalado"
        return
    }
    Write-Log "Instalando $name con winget..."
    winget install --id $name --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
    if (Test-Command $name) {
        Write-Ok "$name instalado"
    } else {
        Write-Warn "winget no pudo instalar $name. Intenta manualmente."
    }
}

function Install-ScoopPackage($name) {
    if (Test-Command $name) {
        Write-Ok "$name ya instalado"
        return
    }
    if (-not (Test-Command scoop)) {
        Write-Log "Instalando scoop..."
        Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
    }
    Write-Log "Instalando $name con scoop..."
    scoop install $name 2>&1 | Out-Null
    if (Test-Command $name) {
        Write-Ok "$name instalado"
    } else {
        Write-Warn "scoop no pudo instalar $name. Intenta manualmente."
    }
}

function Check-Python {
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        $py = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if ($py) {
        $version = & $py.Source --version 2>&1
        if ($version -match "(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge $PYTHON_MIN_MAJOR -and $minor -ge $PYTHON_MIN_MINOR) {
                Write-Ok "Python $version encontrado"
                return $py.Source
            }
        }
    }
    return $null
}

function Install-Python {
    Write-Step "Instalando Python..."
    if (Test-Command winget) {
        winget install --id Python.Python.3.12 --silent --accept-package-agreements 2>&1 | Out-Null
    } else {
        Write-Err "winget no disponible. Descarga Python desde https://python.org/downloads"
        Write-Err "Asegúrate de marcar 'Add Python to PATH' durante la instalación."
        exit 1
    }
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    return (Get-Command python -ErrorAction SilentlyContinue).Source
}

function Install-SystemDeps {
    Write-Step "Verificando dependencias del sistema..."

    $missing = @()
    if (-not (Test-Command mpv))     { $missing += "mpv" }
    if (-not (Test-Command yt-dlp))  { $missing += "yt-dlp" }
    if (-not (Test-Command fzf))     { $missing += "fzf" }

    if ($missing.Count -eq 0) {
        Write-Ok "Todas las dependencias del sistema están instaladas"
        return
    }

    Write-Log "Faltan: $($missing -join ', ')"

    if (Test-Command winget) {
        foreach ($pkg in $missing) {
            switch ($pkg) {
                "mpv"     { Install-WingetPackage "incomponent.mpv" }
                "yt-dlp"  { Install-WingetPackage "yt-dlp.yt-dlp" }
                "fzf"     { Install-WingetPackage "junegunn.fzf" }
            }
        }
    } elseif (Test-Command scoop) {
        foreach ($pkg in $missing) {
            Install-ScoopPackage $pkg
        }
    } else {
        Write-Warn "Ni winget ni scoop disponibles."
        Write-Warn "Instala manualmente: mpv, yt-dlp, fzf"
        Write-Warn "  mpv:     https://mpv.io/install/"
        Write-Warn "  yt-dlp:  https://github.com/yt-dlp/yt-dlp#installation"
        Write-Warn "  fzf:     https://github.com/junegunn/fzf#windows"
    }

    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Install-Neko {
    Write-Step "Instalando NekoTerm..."

    if (-not (Test-Path $INSTALL_DIR)) {
        New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
    }

    if (Test-Path "$INSTALL_DIR\venv") {
        Write-Log "Eliminando entorno virtual existente..."
        Remove-Item -Recurse -Force "$INSTALL_DIR\venv"
    }

    $python = Check-Python
    if (-not $python) {
        $python = Install-Python
    }

    Write-Log "Creando entorno virtual..."
    & $python -m venv "$INSTALL_DIR\venv"

    $pip = "$INSTALL_DIR\venv\Scripts\pip.exe"
    $py  = "$INSTALL_DIR\venv\Scripts\python.exe"

    Write-Log "Actualizando pip..."
    & $pip install --quiet --upgrade pip

    $scriptDir = Split-Path -Parent $PSScriptRoot
    if (Test-Path "$scriptDir\pyproject.toml") {
        Write-Log "Instalando NekoTerm..."
        & $pip install --quiet -e $scriptDir
    } else {
        Write-Err "No se encontró pyproject.toml. Ejecuta este script desde la raíz del proyecto."
        exit 1
    }

    Write-Ok "NekoTerm instalado en $INSTALL_DIR"
}

function Add-ToPath {
    $nekoDir = "$INSTALL_DIR\venv\Scripts"
    $currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$nekoDir*") {
        [System.Environment]::SetEnvironmentVariable("Path", "$currentPath;$nekoDir", "User")
        $env:PATH += ";$nekoDir"
        Write-Ok "Añadido al PATH: $nekoDir"
    }
}

function Verify-Install {
    Write-Step "Verificando instalación..."

    $allOk = $true

    $nekoCmd = Get-Command neko -ErrorAction SilentlyContinue
    if ($nekoCmd) {
        Write-Ok "Comando 'neko' disponible"
    } else {
        Write-Warn "'neko' no está en PATH"
        $allOk = $false
    }

    $py = "$INSTALL_DIR\venv\Scripts\python.exe"
    if (Test-Path $py) {
        $result = & $py -c "import neko; print('ok')" 2>$null
        if ($result -eq "ok") {
            Write-Ok "Módulo neko importable"
        } else {
            Write-Err "Error: módulo neko no importable"
            $allOk = $false
        }
    }

    if (Test-Command mpv)    { Write-Ok "mpv instalado" }    else { Write-Err "mpv no encontrado"; $allOk = $false }
    if (Test-Command yt-dlp) { Write-Ok "yt-dlp instalado" } else { Write-Err "yt-dlp no encontrado"; $allOk = $false }
    if (Test-Command fzf)    { Write-Ok "fzf instalado" }    else { Write-Err "fzf no encontrado"; $allOk = $false }

    Write-Host ""
    if ($allOk) {
        Write-Host "🐱 ¡NekoTerm instalado correctamente!" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Ejecuta: " -NoNewline
        Write-Host "neko" -ForegroundColor White -BackgroundColor DarkCyan
        Write-Host ""
    } else {
        Write-Host "⚠ Instalación completada con advertencias" -ForegroundColor Yellow
        Write-Host "  Revisa los mensajes anteriores."
    }
}

function Main {
    Write-Host ""
    Write-Host "🐱 NekoTerm — Instalador automático" -ForegroundColor Cyan
    Write-Host "   Versión $NEKO_VERSION" -ForegroundColor DarkCyan
    Write-Host ""

    Install-SystemDeps
    Install-Neko
    Add-ToPath
    Verify-Install

    Write-Host ""
    Write-Host "Presiona Enter para salir..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

Main
