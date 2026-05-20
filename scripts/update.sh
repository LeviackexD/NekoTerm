#!/bin/bash
# scripts/update.sh — Auto-actualización de NekoTerm
# Uso: bash scripts/update.sh

set -e

echo "🐱 NekoTerm — Actualizando..."
echo ""

# Si es un repo git, hacer pull
if [ -d ".git" ]; then
    echo "📦 Actualizando código desde Git..."
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "⚠️  No se pudo actualizar desde Git"
fi

# Actualizar dependencias
echo "📦 Actualizando dependencias..."
pip install -e . --quiet 2>/dev/null || pip install -r requirements.txt --quiet 2>/dev/null || echo "⚠️  No se pudieron actualizar las dependencias"

echo ""
echo "✅ NekoTerm actualizado correctamente"
echo "📖 Ejecuta: python -m neko"
