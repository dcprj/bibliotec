"""Ponto de entrada da GUI do BiblioTEC (PySide6 / Qt6 Fusion).

Implementa ``launch_gui()`` e ``main()`` (registro em ``pyproject.toml`` como
``bibliotec-gui = "bibliotec.gui.app:main"``).

A importação de PySide6 ocorre apenas quando a GUI é invocada, preservando a
execução headless do motor (CLI sem depender de Qt).
"""

from __future__ import annotations

import sys
from pathlib import Path

from bibliotec.core.config import AppConfig

__all__ = ["launch_gui", "main"]


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
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QPalette
    from PySide6.QtWidgets import QApplication

    from bibliotec.gui.main_window import BiblioTECMainWindow
    from bibliotec.gui.theme import generate_qss, EDITORIAL_PAPER_THEME

    if config is None:
        config = AppConfig()

    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("BiblioTEC")
    app.setApplicationDisplayName("BiblioTEC — Organizador Acadêmico de PDFs")

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

    window = BiblioTECMainWindow(
        config=config,
        source_dir=source_dir,
        target_dir=target_dir,
    )
    window.show()
    return app.exec()


def main() -> None:
    """Ponto de entrada do script GUI dedicado ``bibliotec-gui``."""
    sys.exit(launch_gui())


if __name__ == "__main__":
    main()
