"""Ponto de entrada da GUI do Tomus (PySide6 / Qt6 Fusion).

Implementa ``launch_gui()`` e ``main()`` (registro em ``pyproject.toml`` como
``tomus-gui = "tomus.gui.app:main"``).

A importação de PySide6 ocorre apenas quando a GUI é invocada, preservando a
execução headless do motor (CLI sem depender de Qt).

Inclui proteções defensivas para inicialização do ``QWebEnginePage`` em
bundles macOS (.app) via ``sys.frozen`` (evita crash SIGABRT no sandbox do
QtWebEngine) e define o ícone oficial da aplicação.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from tomus.core.config import AppConfig
from tomus.core.logging import setup_logging

__all__ = ["launch_gui", "main"]

# Caminho do ícone oficial da aplicação (marca Tomus, PNG em alta resolução; fallback para SVG).
_RES_DIR = Path(__file__).parent / "resources"
ICON_PATH = _RES_DIR / "tomus_icon.png" if (_RES_DIR / "tomus_icon.png").exists() else _RES_DIR / "tomus_icon.svg"


def _apply_webengine_defenses() -> None:
    """Aplicar variáveis de ambiente defensivas para QWebEnginePage em bundle macOS.

    Quando o aplicativo está empacotado (``sys.frozen`` é True, típico de
    pyinstaller/briefcase no macOS), o QtWebEngine pode falhar com SIGABRT
    devido ao sandbox do processo auxiliar. Definir
    ``QTWEBENGINE_DISABLE_SANDBOX=1`` desativa o sandbox, e apontar
    ``QTWEBENGINE_PROCESS_PATH`` para o binário do processo dentro do bundle
    (``sys._MEIPASS``) garante que o processo auxiliar seja encontrado.

    Chamado *antes* de qualquer instância de QApplication / QWebEnginePage.
    """
    if getattr(sys, "frozen", False):
        os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            webengine_process = Path(meipass) / "QtWebEngineProcess"
            if webengine_process.exists():
                os.environ.setdefault("QTWEBENGINE_PROCESS_PATH", str(webengine_process))


def launch_gui(
    config: AppConfig | None = None,
    source_dir: Path | str | None = None,
    target_dir: Path | str | None = None,
) -> int:
    """Inicializar a aplicação PySide6 e abrir a bancada principal.

    :param config: configuração ativa (criada por padrão se omitida).
    :param source_dir: diretório de origem pré-preenchido (opcional).
    :param target_dir: diretório de destino pré-preenchido (opcional).
    :returns: código de saída da aplicação Qt.
    """
    # Aplicar proteções defensivas do WebEngine ANTES de importar/criar qualquer
    # objeto Qt (especialmente QWebEnginePage usado pela visualização de PDF).
    _apply_webengine_defenses()

    # Inicializar o sistema de logs da GUI para que erros de OCR e runtime
    # nunca fiquem invisíveis no Windows/macOS (arquivo tomus.log na pasta do
    # usuário, evitando PermissionError em diretórios protegidos como '/' ou
    # 'Program Files').
    _log_dir = Path.home() / ".tomus"
    _log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=_log_dir / "tomus.log", verbose=False)

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QIcon, QPalette
    from PySide6.QtWidgets import QApplication

    from tomus.gui.main_window import TomusMainWindow
    from tomus.gui.theme import generate_qss, EDITORIAL_PAPER_THEME

    if config is None:
        config = AppConfig()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Tomus")
    app.setApplicationDisplayName("Tomus — Organizador Acadêmico de PDFs")

    # --- Ícone oficial da aplicação (substitui o genérico do Python) ---
    if ICON_PATH.exists():
        app_icon = QIcon(str(ICON_PATH))
        app.setWindowIcon(app_icon)

    # Forçar paleta clara contra herança de tema escuro do OS
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#0F172A"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#F8FAFC"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#0F172A"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#0F172A"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#F8FAFC"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#0F172A"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#DC2626"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1E3A8A"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(palette)

    # Estilos globais para diálogos nativos (QMessageBox, QDialog, QMenu)
    app.setStyleSheet(
        generate_qss(EDITORIAL_PAPER_THEME)
        + """
        QDialog, QMessageBox {
            background-color: #FFFFFF;
            color: #0F172A;
        }
        QMessageBox QLabel {
            background-color: transparent;
            color: #0F172A;
            font-size: 13px;
        }
        QMessageBox QPushButton {
            background-color: #1E3A8A;
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 6px 18px;
            font-weight: 600;
            font-size: 13px;
            min-width: 60px;
        }
        QMessageBox QPushButton:hover {
            background-color: #172554;
        }
        """
    )

    window = TomusMainWindow(
        config=config,
        source_dir=source_dir,
        target_dir=target_dir,
    )

    # Definir ícone também na janela principal (redundância por segurança).
    if ICON_PATH.exists():
        window.setWindowIcon(QIcon(str(ICON_PATH)))

    window.show()
    return app.exec()


def main() -> None:
    """Ponto de entrada do script GUI dedicado ``tomus-gui``."""
    sys.exit(launch_gui())


if __name__ == "__main__":
    main()
