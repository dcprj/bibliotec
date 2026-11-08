#!/usr/bin/env bash
# ==============================================================================
# Script de Build do BiblioTEC para macOS (.app e .dmg)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERSION="1.0.0"
APP_NAME="BiblioTEC"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"
DMG_NAME="${APP_NAME}-${VERSION}-macOS.dmg"

echo "=========================================================="
echo " Início do Build macOS para ${APP_NAME} v${VERSION}"
echo "=========================================================="

cd "${PROJECT_ROOT}"

# 1. Verificar PyInstaller no ambiente ativo
if ! command -v pyinstaller &> /dev/null; then
    if [ -f ".venv/bin/pyinstaller" ]; then
        PYINSTALLER=".venv/bin/pyinstaller"
    else
        echo "❌ Erro: pyinstaller não encontrado. Instale com: pip install pyinstaller"
        exit 1
    fi
else
    PYINSTALLER="pyinstaller"
fi

# 2. Limpar builds anteriores e configurar cache local
echo "🧹 Limpando pastas dist/ e build/..."
rm -rf "${DIST_DIR}/${APP_NAME}.app" "${DIST_DIR}/${DMG_NAME}" "${BUILD_DIR}"
export PYINSTALLER_CONFIG_DIR="${BUILD_DIR}/pyinstaller_cache"
mkdir -p "${PYINSTALLER_CONFIG_DIR}"

# 3. Executar PyInstaller
echo "⚙️ Compilando bundle macOS (.app) via PyInstaller..."
"${PYINSTALLER}" --clean -y "${SCRIPT_DIR}/pyinstaller.spec"

APP_PATH="${DIST_DIR}/${APP_NAME}.app"
if [ ! -d "${APP_PATH}" ]; then
    echo "❌ Erro: O bundle ${APP_PATH} não foi gerado com sucesso."
    exit 1
fi

echo "✅ Bundle ${APP_PATH} gerado com sucesso!"

# 4. Assinatura Ad-Hoc (para execução local sem crash de assinatura)
echo "🔏 Aplicando assinatura ad-hoc (codesign)..."
codesign --force --deep --sign - "${APP_PATH}"

# 5. Criar Imagem de Disco (.dmg) com atalho para /Applications
echo "📦 Criando imagem de disco ${DMG_NAME}..."
DMG_TEMP_DIR="${BUILD_DIR}/dmg_staging"
rm -rf "${DMG_TEMP_DIR}"
mkdir -p "${DMG_TEMP_DIR}"

# Copiar .app para a pasta temporária do DMG
cp -R "${APP_PATH}" "${DMG_TEMP_DIR}/"

# Criar atalho simbólico para /Applications
ln -s /Applications "${DMG_TEMP_DIR}/Applications"

# Gerar arquivo .dmg final via hdiutil nativo do macOS
hdiutil create \
    -volname "${APP_NAME} Installer" \
    -srcfolder "${DMG_TEMP_DIR}" \
    -ov \
    -format UDZO \
    "${DIST_DIR}/${DMG_NAME}"

rm -rf "${DMG_TEMP_DIR}"

echo "=========================================================="
echo "🎉 Build concluído com sucesso!"
echo "📁 Bundle: ${APP_PATH}"
echo "💿 Imagem DMG: ${DIST_DIR}/${DMG_NAME}"
echo "=========================================================="
