# scripts/uninstall.ps1 — Desinstalación de NekoTerm (Windows)

$INSTALL_DIR = "$env:USERPROFILE\.nekoterm"

function Write-Log { param($Msg) Write-Host "  · $Msg" -ForegroundColor White }
function Write-Ok   { param($Msg) Write-Host "  ✓ $Msg" -ForegroundColor Green }
function Write-Warn { param($Msg) Write-Host "  ! $Msg" -ForegroundColor Yellow }

Write-Host "`n🐱 NekoTerm — Desinstalación" -ForegroundColor Cyan
Write-Host ""

if (Test-Path $INSTALL_DIR) {
    Write-Log "Eliminando entorno virtual..."
    Remove-Item -Recurse -Force $INSTALL_DIR
    Write-Ok "Eliminado: $INSTALL_DIR"
} else {
    Write-Warn "No se encontró: $INSTALL_DIR"
}

$nekoCmd = Get-Command neko -ErrorAction SilentlyContinue
if ($nekoCmd) {
    Write-Log "Nota: 'neko' sigue en PATH. Reinicia la terminal."
}

Write-Host ""
Write-Host "NekoTerm desinstalado." -ForegroundColor Green
Write-Host ""
Write-Host "Las dependencias del sistema (mpv, yt-dlp, fzf) NO se han eliminado." -ForegroundColor Yellow
Write-Host "Si ya no las necesitas, elimínalas con winget:"
Write-Host "  winget uninstall mpv yt-dlp fzf"
