#!/usr/bin/env bash
# ==============================================================================
# Script de Empacotamento do BiblioTEC para Linux (AppImage universal)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERSION="1.0.0"
APP_NAME="BiblioTEC"
DIST_DIR="${PROJECT_ROOT}/dist"
BUILD_DIR="${PROJECT_ROOT}/build"
APP_DIR="${BUILD_DIR}/AppDir"

echo "=========================================================="
echo " Início do Build Linux (AppImage) para ${APP_NAME} v${VERSION}"
echo "=========================================================="

cd "${PROJECT_ROOT}"

# 1. Verificar PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    if [ -f ".venv/bin/pyinstaller" ]; then
        PYINSTALLER=".venv/bin/pyinstaller"
    else
        echo "❌ Erro: pyinstaller não encontrado."
        exit 1
    fi
else
    PYINSTALLER="pyinstaller"
fi

# 2. Compilar binários via PyInstaller
echo "⚙️ Compilando binários com PyInstaller..."
export PYINSTALLER_CONFIG_DIR="${BUILD_DIR}/pyinstaller_cache"
mkdir -p "${PYINSTALLER_CONFIG_DIR}"
"${PYINSTALLER}" --clean -y "${SCRIPT_DIR}/pyinstaller.spec"

# 3. Estruturar AppDir
echo "📦 Montando estrutura do AppDir..."
rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/512x512/apps"

# Copiar bundle
cp -R "${DIST_DIR}/${APP_NAME}/"* "${APP_DIR}/usr/bin/"

# Criar arquivo .desktop
cat <<EOF > "${APP_DIR}/usr/share/applications/bibliotec.desktop"
[Desktop Entry]
Type=Application
Name=BiblioTEC
Exec=BiblioTEC
Icon=bibliotec
Comment=Organizador Acadêmico de PDFs baseado na taxonomia CAPES/CNPq
Categories=Education;Science;Office;
Terminal=false
StartupWMClass=BiblioTEC
EOF

cp "${APP_DIR}/usr/share/applications/bibliotec.desktop" "${APP_DIR}/bibliotec.desktop"

# Criar AppRun
cat <<'EOF' > "${APP_DIR}/AppRun"
#!/usr/bin/env bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${HERE}/usr/bin:${LD_LIBRARY_PATH:-}"
exec "${HERE}/usr/bin/BiblioTEC" "$@"
EOF
chmod +x "${APP_DIR}/AppRun"

# 4. Baixar appimagetool se não existir
APPIMAGETOOL="${BUILD_DIR}/appimagetool"
if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "⬇️ Baixando appimagetool..."
    curl -sLo "${APPIMAGETOOL}" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "${APPIMAGETOOL}"
fi

# 5. Gerar AppImage
OUTPUT_APPIMAGE="${DIST_DIR}/${APP_NAME}-${VERSION}-x86_64.AppImage"
echo "🚀 Gerando ${OUTPUT_APPIMAGE}..."
ARCH=x86_64 "${APPIMAGETOOL}" "${APP_DIR}" "${OUTPUT_APPIMAGE}"

echo "=========================================================="
echo "🎉 Build Linux concluído com sucesso!"
echo "📁 AppImage: ${OUTPUT_APPIMAGE}"
echo "=========================================================="
