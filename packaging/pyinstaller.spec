# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file multiplataforma para o BiblioTEC (macOS, Windows, Linux).

Gera:
- macOS: BiblioTEC.app (bundle nativo sem console)
- Windows: BiblioTEC.exe (GUI noconsole com ícone)
- Linux: BiblioTEC (binário para empacotamento em AppImage)
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Raiz do projeto (no PyInstaller spec, SPECPATH contém o diretório do arquivo .spec)
try:
    SPEC_DIR = Path(SPECPATH).resolve()
except NameError:
    SPEC_DIR = Path.cwd() / "packaging"

ROOT_DIR = SPEC_DIR.parent
SRC_DIR = ROOT_DIR / "src"
ICONS_DIR = ROOT_DIR / "packaging" / "icons"

# Dados estáticos obrigatórios
datas = [
    (str(SRC_DIR / "bibliotec" / "gui" / "web"), "bibliotec/gui/web"),
]

# Hidden imports essenciais para PySide6 WebEngine e dependências dinâmicas
hiddenimports = [
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebChannel",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "fitz",
    "rapidfuzz",
    "rapidfuzz.distance",
    "tenacity",
    "stdnum",
    "stdnum.isbn",
    "stdnum.doi",
    "tomli_w",
    "rich",
    "typer",
    "pydantic",
    "pydantic_settings",
    "google.genai",
    "httpx",
]

# Tentar coletar dados adicionais de pacotes se instalados no ambiente
try:
    datas += collect_data_files("docling")
except Exception:
    pass

try:
    hiddenimports += collect_submodules("bibliotec")
except Exception:
    pass

a = Analysis(
    [str(SRC_DIR / "bibliotec" / "gui" / "app.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "IPython", "notebook", "scipy"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Configuração de Ícone (se presente)
icon_macos = str(ICONS_DIR / "icon.icns")
icon_win = str(ICONS_DIR / "icon.ico")

icon_target = None
if sys.platform == "darwin" and os.path.exists(icon_macos):
    icon_target = icon_macos
elif sys.platform == "win32" and os.path.exists(icon_win):
    icon_target = icon_win

# Modo diretório (melhor para aplicações ricas com QtWebEngine)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BiblioTEC",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sem janela de terminal/prompt de comando preta
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_target,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BiblioTEC",
)

# No macOS, encapsula o diretório em um bundle .app nativo com metadados Apple
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="BiblioTEC.app",
        icon=icon_target,
        bundle_identifier="org.bibliotec.app",
        info_plist={
            "CFBundleName": "BiblioTEC",
            "CFBundleDisplayName": "BiblioTEC",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundlePackageType": "APPL",
            "CFBundleSignature": "????",
            "LSMinimumSystemVersion": "12.0.0",
            "NSHighResolutionCapable": True,
            "NSSupportsAutomaticGraphicsSwitching": True,
            "LSApplicationCategoryType": "public.app-category.education",
            "NSHumanReadableCopyright": "Copyright © 2026 BiblioTEC. Licença Gratuita.",
        },
    )
