"""Painel esquerdo — Filtros de status e Árvore Taxonômica CAPES/CNPq (Seção 3.2 item B).

Componente:
* ``CapesSidebarPanel`` — lista fixa de 6 filtros rápidos com contadores em
  tempo real + ``QTreeWidget`` populado dinamicamente com Grandes Áreas,
  Áreas Básicas e Tipos Documentais presentes no lote.
  Conforme Mockup 1: cartões elevados branco puro, bordas 1px #E2E8F0,
  border-radius 8-12px, badges em pílula semânticos.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from bibliotec.core.models import ProcessStatus
from bibliotec.gui.theme import EDITORIAL_PAPER_THEME, ThemeTokens

__all__ = ["CapesSidebarPanel"]

# Ordem e rótulos dos filtros de status (Seção 3.2 item B, Seção 1).
STATUS_FILTERS = [
    (None, "Todos os Itens"),
    (ProcessStatus.ORGANIZED, "Organizados"),
    (ProcessStatus.MANUAL_REVIEW, "Revisão Manual"),
    (ProcessStatus.DUPLICATE_SKIPPED, "Duplicatas"),
    (ProcessStatus.IGNORED_NON_PDF, "Ignorados (Não-PDF)"),
    (ProcessStatus.ERROR, "Erros"),
]

# Cor do badge por status (Mockup 1: Verde=Organizado, Âmbar=Revisão,
# Azul=Duplicata, Cinza=Processando/Ignorado, Vermelho=Erro).
_STATUS_BADGE_BG = {
    ProcessStatus.ORGANIZED: "#DCFCE7",
    ProcessStatus.MANUAL_REVIEW: "#FEF3C7",
    ProcessStatus.DUPLICATE_SKIPPED: "#E0F2FE",
    ProcessStatus.IGNORED_NON_PDF: "#F1F5F9",
    ProcessStatus.ERROR: "#FEE2E2",
}

_STATUS_BADGE_FG = {
    ProcessStatus.ORGANIZED: "#15803D",
    ProcessStatus.MANUAL_REVIEW: "#B45309",
    ProcessStatus.DUPLICATE_SKIPPED: "#0369A1",
    ProcessStatus.IGNORED_NON_PDF: "#64748B",
    ProcessStatus.ERROR: "#B91C1C",
}


class CapesSidebarPanel(QWidget):
    """Navegador de filtros e árvore taxonômica CAPES/CNPq."""

    status_filter_changed = Signal(set)  # conjunto de ProcessStatus ou None = todos
    area_selected = Signal(str)          # grande_area ou area_basica
    tree_item_clicked = Signal(object, int)  # QTreeWidgetItem, column

    def __init__(
        self,
        tokens: ThemeTokens = EDITORIAL_PAPER_THEME,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tokens = tokens
        self._counters: dict[str, int] = {
            (s.value if s else "total"): 0 for s, _ in STATUS_FILTERS
        }
        self.status_items: dict[str, dict] = {}

        self._build_ui()
        self._apply_theme(tokens)

    # ------------------------------------------------------------------ #
    # Construção da UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabeçalho da seção dentro de um card.
        header_card = QFrame()
        header_card.setObjectName("cardSm")
        header_lay = QVBoxLayout(header_card)
        header_lay.setContentsMargins(16, 14, 16, 14)
        header_lay.setSpacing(8)

        hdr = QLabel("FILTROS & TAXONOMIA")
        hdr.setStyleSheet(
            "color: #64748B; font-size: 11px; font-weight: 700; "
            "letter-spacing: 0.4px; text-transform: uppercase;"
        )
        header_lay.addWidget(hdr)

        layout.addWidget(header_card)

        # --- Seção 1: Visão de Status Operacional ---
        sec_card = QFrame()
        sec_card.setObjectName("card")
        sec_lay = QVBoxLayout(sec_card)
        sec_lay.setContentsMargins(16, 14, 16, 14)
        sec_lay.setSpacing(8)

        sec1 = QLabel("VISÃO DE STATUS")
        sec1.setStyleSheet(
            "color: #64748B; font-size: 11px; font-weight: 700; "
            "letter-spacing: 0.4px; text-transform: uppercase;"
        )
        sec_lay.addWidget(sec1)

        for status, label in STATUS_FILTERS:
            row = QFrame()
            row.setFixedHeight(32)
            row_lay = QHBoxLayout(row)
            row_lay.setContentsMargins(8, 2, 8, 2)
            row_lay.setSpacing(8)

            key = status.value if status else "total"
            rb = QPushButton(label)
            rb.setCheckable(True)
            rb.setFixedHeight(24)
            rb.setStyleSheet(
                "QPushButton { text-align: left; padding: 2px 10px; border: none; "
                "border-radius: 6px; background: transparent; color: #0F172A; "
                "font-size: 12.5px; }"
                "QPushButton:checked { background: #EFF6FF; color: #1E3A8A; }"
            )
            rb.clicked.connect(lambda _, st=status: self._on_status_toggled(st))

            counter = QLabel("0")
            counter.setFixedWidth(28)
            counter.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            counter.setStyleSheet("color: #64748B; font-size: 11.5px; font-family: monospace;")

            row_lay.addWidget(rb)
            row_lay.addStretch(1)
            row_lay.addWidget(counter)

            self.status_items[key] = {
                "button": rb,
                "counter": counter,
            }
            sec_lay.addWidget(row)

        self.status_items["total"]["button"].setChecked(True)

        layout.addWidget(sec_card)

        # --- Seção 2: Árvore CAPES/CNPq ---
        tree_card = QFrame()
        tree_card.setObjectName("card")
        tree_lay = QVBoxLayout(tree_card)
        tree_lay.setContentsMargins(16, 14, 16, 14)
        tree_lay.setSpacing(8)

        sec2 = QLabel("ÁRVORE CAPES/CNPq")
        sec2.setStyleSheet(
            "color: #64748B; font-size: 11px; font-weight: 700; "
            "letter-spacing: 0.4px; text-transform: uppercase;"
        )
        tree_lay.addWidget(sec2)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet(
            "QTreeWidget { background: transparent; border: none; "
            "color: #0F172A; font-size: 12.5px; }"
            "QTreeWidget::item { height: 28px; border: none; padding: 4px 8px; }"
            "QTreeWidget::item:selected { background: #EFF6FF; color: #1E3A8A; "
            "border-radius: 6px; }"
        )
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        tree_lay.addWidget(self.tree, 1)

        layout.addWidget(tree_card, 1)
        layout.addStretch(1)

    # ------------------------------------------------------------------ #
    # Contadores
    # ------------------------------------------------------------------ #

    def set_counters(self, counters: dict[str, int]) -> None:
        self._counters = dict(counters)
        for key, widget in self.status_items.items():
            widget["counter"].setText(str(self._counters.get(key, 0)))

    def increment(self, status: ProcessStatus | None) -> None:
        key = status.value if status else "total"
        self._counters[key] = self._counters.get(key, 0) + 1
        if key in self.status_items:
            self.status_items[key]["counter"].setText(str(self._counters[key]))

    # ------------------------------------------------------------------ #
    # Árvore CAPES/CNPq
    # ------------------------------------------------------------------ #

    def populate_tree(
        self,
        areas: dict[str, dict[str, list[str]]],
    ) -> None:
        """Preencher a árvore com {grande_area: {area_basica: [tipos]}}."""
        self.tree.clear()
        for grande_area, basicas in areas.items():
            ga_item = QTreeWidgetItem([grande_area])
            ga_item.setData(0, Qt.ItemDataRole.UserRole, ("grande_area", grande_area))
            for area_basica, tipos in basicas.items():
                ab_item = QTreeWidgetItem([area_basica])
                ab_item.setData(0, Qt.ItemDataRole.UserRole, ("area_basica", area_basica))
                for tipo in tipos:
                    t_item = QTreeWidgetItem([tipo])
                    t_item.setData(0, Qt.ItemDataRole.UserRole, ("tipo", tipo))
                    ab_item.addChild(t_item)
                ga_item.addChild(ab_item)
            self.tree.addTopLevelItem(ga_item)
        self.tree.expandAll()

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #

    def _on_status_toggled(self, status: ProcessStatus | None) -> None:
        for key, widget in self.status_items.items():
            is_total = key == "total"
            if status is None and is_total:
                widget["button"].setChecked(True)
            elif status is not None and key == status.value:
                widget["button"].setChecked(True)
            else:
                widget["button"].setChecked(False)

        filtros: set[str] | None = None if status is None else {status.value}
        self.status_filter_changed.emit(filtros)

    def _on_tree_item_clicked(self, item, column: int) -> None:
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        kind, value = data
        self.tree_item_clicked.emit(item, column)
        if kind in ("grande_area", "area_basica"):
            self.area_selected.emit(value)

    # ------------------------------------------------------------------ #
    # Tema
    # ------------------------------------------------------------------ #

    def _apply_theme(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            f"QWidget {{ background-color: {tokens.bg_canvas}; color: {tokens.text_primary}; }}"
        )
        # Aplicar cor de borda nos cards elevados.
        for card in self.findChildren(QFrame):
            if card.objectName() in ("card", "cardSm"):
                radius = 12 if card.objectName() == "card" else 8
                card.setStyleSheet(
                    f"QFrame#{{card.objectName()}} {{ background-color: {tokens.bg_surface}; "
                    f"border: 1px solid {tokens.border_subtle}; border-radius: {radius}px; }}"
                    .replace("{card.objectName()}", card.objectName())
                )
