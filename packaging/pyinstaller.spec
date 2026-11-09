# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file multiplataforma para o Tomus (macOS e Windows).

Gera:
- macOS: Tomus.app (bundle nativo sem console)
- Windows: Tomus.exe (GUI noconsole com ícone)
"""

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

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
    (str(SRC_DIR / "bibliotec" / "gui" / "resources"), "bibliotec/gui/resources"),
    (str(SRC_DIR / "bibliotec" / "core" / "resources"), "bibliotec/core/resources"),
]

# Hidden imports essenciais para PySide6 WebEngine, dependências dinâmicas e OCR Docling
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
    "torch",
    "torchvision",
    "docling",
    "docling.document_converter",
    "docling.datamodel.base_models",
    "docling.datamodel.pipeline_options",
    "docling.backend.docling_parse_backend",
    "docling.pipeline.standard_pdf_pipeline",
    "rapidocr",
    "onnxruntime",
]

# Coletar submódulos e arquivos de dados do Docling e motor de OCR
for pkg in ["docling", "docling_core", "docling_parse", "docling_ibm_models", "rapidocr", "onnxruntime"]:
    try:
        datas += collect_data_files(pkg)
    except Exception:
        pass
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# Coletar binários/DLLs do onnxruntime (essenciais no Windows para RapidOCR)
binaries += collect_dynamic_libs("onnxruntime")

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
    excludes=["tkinter", "matplotlib", "IPython", "notebook", "scipy", "pkg_resources", "setuptools"],
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
    name="Tomus",
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
    name="Tomus",
)

# No macOS, encapsula o diretório em um bundle .app nativo com metadados Apple
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Tomus.app",
        icon=icon_target,
        bundle_identifier="org.tomus.app",
        info_plist={
            "CFBundleName": "Tomus",
            "CFBundleDisplayName": "Tomus — Organizador Acadêmico de PDFs",
            "CFBundleVersion": "1.1.0",
            "CFBundleShortVersionString": "1.1.0",
            "CFBundlePackageType": "APPL",
            "CFBundleSignature": "????",
            "LSMinimumSystemVersion": "12.0.0",
            "NSHighResolutionCapable": True,
            "NSSupportsAutomaticGraphicsSwitching": True,
            "LSApplicationCategoryType": "public.app-category.education",
            "NSHumanReadableCopyright": "Copyright © 2026 Tomus. Licença Gratuita.",
        },
    )
