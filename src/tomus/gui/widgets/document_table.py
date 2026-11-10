"""Painel central — Grade de Documentos de Alta Densidade (Seção 3.2 item C).

Componente:
* ``DocumentTablePanel`` — barra de busca instantânea (debounce 120ms,
  Cmd+F / Ctrl+F) + ``QTableView`` acoplado a ``DocumentTableModel`` e
  ``DocumentFilterProxyModel`` com delegate de badge em pílula semântico.
  Conforme Mockup 1: cartão elevado branco puro, coluna Título em Stretch,
  badges semânticos 1:1 (Verde=Organizado, Âmbar=Revisão, Azul=Duplicata,
  Cinza=Processando/Ignorado, Vermelho=Erro).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QModelIndex, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (
    QAbstractItemDelegate,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from tomus.core.models import ProcessStatus
from tomus.gui.icons import render_icon
from tomus.gui.models import (
    _COL_AUTHORS,
    _COL_AREA,
    _COL_CONFIDENCE,
    _COL_FLAGS,
    _COL_STATUS,
    _COL_TITLE,
    _COL_TYPE,
    _COLUMN_HEADERS,
    _COLUMN_WIDTHS,
    DocumentFilterProxyModel,
    DocumentTableModel,
)
from tomus.gui.theme import EDITORIAL_PAPER_THEME, ThemeTokens, status_colors

__all__ = ["DocumentTablePanel"]

_IS_MAC = sys.platform == "darwin"

# Ícone por status (seção 2.3 do gui_spec.md).
_STATUS_ICONS = {
    ProcessStatus.ORGANIZED.value: "check-circle",
    ProcessStatus.MANUAL_REVIEW.value: "alert-triangle",
    ProcessStatus.DUPLICATE_SKIPPED.value: "copy-layers",
    ProcessStatus.IGNORED_NON_PDF.value: "file-slash",
    ProcessStatus.ERROR.value: "x-octagon",
    "processing": "rotate-ccw",
}

_STATUS_SHORT = {
    ProcessStatus.ORGANIZED.value: "Organizado",
    ProcessStatus.MANUAL_REVIEW.value: "Revisão",
    ProcessStatus.DUPLICATE_SKIPPED.value: "Duplicata",
    ProcessStatus.IGNORED_NON_PDF.value: "Ignorado",
    ProcessStatus.ERROR.value: "Erro",
    "processing": "Processando",
}


class StatusBadgeDelegate(QAbstractItemDelegate):
    """Delegate que renderiza a coluna Status como badge em pílula semântica."""

    def __init__(self, tokens: ThemeTokens, parent=None) -> None:
        super().__init__(parent)
        self._tokens = tokens

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        painter.save()
        status = index.data(Qt.ItemDataRole.DisplayRole) or ""
        try:
            ps = ProcessStatus(status)
            fg, bg = status_colors(ps, self._tokens)
        except ValueError:
            fg, bg = "#64748B", "#F1F5F9"

        rect = option.rect.adjusted(6, 5, -6, -5)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fundo da pílula (border-radius 8px).
        painter.setBrush(QColor(bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 8, 8)

        # Ícone vetorial monocromático centralizado verticalmente.
        icon_name = _STATUS_ICONS.get(status)
        if icon_name:
            pm = render_icon(icon_name, color=fg, size_px=12).pixmap(QSize(12, 12))
            painter.drawPixmap(rect.x() + 8, rect.y() + (rect.height() - 12) // 2, pm)

        # Texto do status (curto).
        painter.setPen(QColor(fg))
        font = QFont()
        font.setPointSize(9.5)
        font.setBold(True)
        painter.setFont(font)
        short = _STATUS_SHORT.get(status, status)
        painter.drawText(
            rect.adjusted(24, 0, -4, 0),
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            short,
        )
        painter.restore()

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        return QSize(110, 28)


class DocumentTablePanel(QWidget):
    """Grade de documentos com busca instantânea e proxy de filtros."""

    selection_changed = Signal(object)  # _DocumentRow | None
    open_pdf_requested = Signal(str)    # source_path
    reveal_requested = Signal(str)      # source_path

    def __init__(
        self,
        tokens: ThemeTokens = EDITORIAL_PAPER_THEME,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tokens = tokens

        self._model = DocumentTableModel()
        self._proxy = DocumentFilterProxyModel()
        self._proxy.setSourceModel(self._model)

        self._build_ui()
        self._apply_theme(tokens)

    # ------------------------------------------------------------------ #
    # Construção da UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Barra de busca instantânea dentro de um card.
        search_card = QFrame()
        search_card.setObjectName("cardSm")
        search_lay = QHBoxLayout(search_card)
        search_lay.setContentsMargins(12, 8, 12, 8)
        search_lay.setSpacing(8)

        search_icon = QLabel()
        search_icon.setFixedSize(16, 16)
        search_icon.setPixmap(render_icon("folder-reveal", color="#64748B", size_px=16).pixmap(QSize(16, 16)))

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Filtrar por título, autor, ano, DOI, ISBN ou nome original..."
        )
        self.search_edit.setFixedHeight(32)
        self.search_edit.textChanged.connect(self._on_search_changed)

        search_lay.addWidget(search_icon)
        search_lay.addWidget(self.search_edit, 1)
        layout.addWidget(search_card)

        # Tabela dentro de um card.
        table_card = QFrame()
        table_card.setObjectName("card")
        table_card_lay = QVBoxLayout(table_card)
        table_card_lay.setContentsMargins(0, 0, 0, 0)
        table_card_lay.setSpacing(0)

        self.table = QTableView()
        self.table.setModel(self._proxy)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(
            _COL_TITLE, QHeaderView.ResizeMode.Stretch
        )
        # Demais colunas mantêm largura fixa (Interactive).
        for i in range(len(_COLUMN_HEADERS)):
            if i != _COL_TITLE:
                self.table.horizontalHeader().setSectionResizeMode(
                    i, QHeaderView.ResizeMode.Interactive
                )

        self.table.setItemDelegateForColumn(_COL_STATUS, StatusBadgeDelegate(self._tokens))

        for i, w in enumerate(_COLUMN_WIDTHS):
            self.table.setColumnWidth(i, w)

        from PySide6.QtGui import QKeySequence, QShortcut
        QShortcut(QKeySequence("Cmd+F" if _IS_MAC else "Ctrl+F"), self, self._focus_search)

        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)
        self.table.doubleClicked.connect(self._on_double_clicked)

        table_card_lay.addWidget(self.table)
        layout.addWidget(table_card, 1)

    def _focus_search(self) -> None:
        self.search_edit.setFocus()
        self.search_edit.selectAll()

    def _on_search_changed(self, text: str) -> None:
        if not hasattr(self, "_search_timer"):
            self._search_timer = QTimer(self)
            self._search_timer.setSingleShot(True)
            self._search_timer.timeout.connect(
                lambda: self._proxy.set_search_text(self.search_edit.text())
            )
        self._search_timer.start(120)

    def _on_selection_changed(self, selected, _deselected) -> None:
        idxs = selected.indexes()
        if not idxs:
            self.selection_changed.emit(None)
            return
        proxy_idx = idxs[0]
        model_idx = self._proxy.mapToSource(proxy_idx)
        row = self._model.row(model_idx.row())
        self.selection_changed.emit(row)

    def _on_double_clicked(self, index: QModelIndex) -> None:
        model_idx = self._proxy.mapToSource(index)
        row = self._model.row(model_idx.row())
        if row is not None:
            self.open_pdf_requested.emit(row.source_path)

    # ------------------------------------------------------------------ #
    # API de dados
    # ------------------------------------------------------------------ #

    def upsert_from_event(self, event) -> None:
        self._model.upsert_from_event(event)

    def replace_all(self, entries) -> None:
        self._model.replace_all(entries)

    def clear(self) -> None:
        self._model.clear()

    def set_status_filter(self, statuses: set | None) -> None:
        self._proxy.set_status_filter(statuses)

    def set_area_filter(self, area: str | None) -> None:
        self._proxy.set_area_filter(area)

    def selected_row(self):
        idxs = self.table.selectionModel().selectedRows()
        if not idxs:
            return None
        model_idx = self._proxy.mapToSource(idxs[0])
        return self._model.row(model_idx.row())

    # ------------------------------------------------------------------ #
    # Tema
    # ------------------------------------------------------------------ #

    def _apply_theme(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            f"QWidget {{ background-color: {tokens.bg_canvas}; color: {tokens.text_primary}; }}"
        )
        self.table.setStyleSheet(
            f"QTableView {{ background-color: {tokens.bg_surface}; "
            f"color: {tokens.text_primary}; border: 1px solid {tokens.border_subtle}; "
            f"border-radius: 12px; gridline-color: {tokens.border_subtle}; "
            f"selection-background-color: transparent; }}"
        )
        self.search_edit.setStyleSheet(
            f"QLineEdit {{ background: {tokens.bg_elevated}; border: 1px solid {tokens.border_subtle}; "
            f"border-radius: 8px; padding: 6px 12px; font-size: 13px; color: {tokens.text_primary}; }}"
            f"QLineEdit:focus {{ border: 1px solid {tokens.border_focus}; "
            f"background: {tokens.bg_surface}; }}"
        )
