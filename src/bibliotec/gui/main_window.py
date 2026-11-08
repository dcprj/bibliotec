"""Janela principal da bancada desktop do BiblioTEC baseada em QWebEngineView.

Hospeda a interface moderna HTML5/CSS (Mockup 1 / Dribbble Aesthetics) com
comunicação bidirecional nativa via QWebChannel para o motor Python.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QWidget

from bibliotec.core.config import AppConfig
from bibliotec.gui.bridge import WebBridge

__all__ = ["BiblioTECMainWindow"]

_MIN_SIZE = (1080, 680)
_DEFAULT_SIZE = (1360, 840)


class BiblioTECWebPage(QWebEnginePage):
    """Página customizada que repassa logs e erros do console JS para o terminal Python."""

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        src_name = Path(sourceID).name if sourceID else "inline"
        print(f"[BiblioTEC-JS] ({src_name}:{lineNumber}) {message}")


class BiblioTECMainWindow(QMainWindow):
    """Janela principal do BiblioTEC com casca Web moderna e motor Python."""

    def __init__(
        self,
        config: AppConfig,
        source_dir: Path | str | None = None,
        target_dir: Path | str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._source_dir = Path(source_dir) if source_dir else None
        self._target_dir = Path(target_dir) if target_dir else None

        self.setWindowTitle("BiblioTEC — Organizador Acadêmico de PDFs")
        self.setMinimumSize(*_MIN_SIZE)
        self.resize(*_DEFAULT_SIZE)

        # Configurar WebEngineView com página de logging personalizada
        self.web_page = BiblioTECWebPage(self)
        self.web_view = QWebEngineView(self)
        self.web_view.setPage(self.web_page)
        self.setCentralWidget(self.web_view)

        # Configurar QWebChannel e Ponte Python <-> JS
        self.channel = QWebChannel(self.web_page)
        self.bridge = WebBridge(self._config, parent_widget=self, parent=self)
        if self._source_dir:
            self.bridge.source_dir = str(self._source_dir)
        if self._target_dir:
            self.bridge.target_dir = str(self._target_dir)

        self.channel.registerObject("backend", self.bridge)
        self.web_page.setWebChannel(self.channel)

        # Carregar interface HTML5 (compatível com desenvolvimento local e bundle PyInstaller)
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            meipass = Path(sys._MEIPASS)
            candidates = [
                meipass / "bibliotec" / "gui" / "web",
                meipass / "web",
                Path(__file__).parent / "web",
            ]
            web_dir = next((p for p in candidates if p.exists()), candidates[0])
        else:
            web_dir = Path(__file__).parent / "web"

        index_file = web_dir / "index.html"
        self.web_view.load(QUrl.fromLocalFile(str(index_file.resolve())))

        self.setAcceptDrops(True)

    # ------------------------------------------------------------------ #
    # Drag & Drop de pastas nativo
    # ------------------------------------------------------------------ #

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        p = Path(path)
        if p.is_dir():
            if not self.bridge.source_dir:
                self.bridge.source_dir = str(p)
                self.bridge.sourceChanged.emit(str(p))
            else:
                self.bridge.target_dir = str(p)
                self.bridge.targetChanged.emit(str(p))
            event.acceptProposedAction()
