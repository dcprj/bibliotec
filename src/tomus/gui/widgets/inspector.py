"""Painel direito — Inspetor ABNT NBR 6023, Metadados e Triagem Manual (Seção 3.2 item D).

Componentes:
* ``ABNTReferenceCard`` — cartão de referência bibliográfica (Modo 1: Organizado).
* ``ManualTriageBox`` — assistente de triagem manual (Modo 2: Revisão / Erro).
* ``DocumentInspectorPanel`` — adapta a visão conforme o ProcessStatus selecionado.
  Conforme Mockup 1: Empty State refinado (ícone catálogo, título "Nenhum documento
  selecionado", texto explicativo), cartões limpos, citação ABNT NBR 6023 em destaque
  com botão "Copiar Citação" e botões contextuais no rodapé.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tomus.core.models import DocumentType, FileManifestEntry, ProcessStatus
from tomus.gui.icons import render_icon
from tomus.gui.theme import EDITORIAL_PAPER_THEME, ThemeTokens
from tomus.storage.companion import format_abnt_reference

__all__ = ["ABNTReferenceCard", "DocumentInspectorPanel", "ManualTriageBox"]

_SEMANTIC_STATUS_COLORS = {
    ProcessStatus.ORGANIZED: ("#15803D", "#DCFCE7"),
    ProcessStatus.MANUAL_REVIEW: ("#B45309", "#FEF3C7"),
    ProcessStatus.DUPLICATE_SKIPPED: ("#0369A1", "#E0F2FE"),
    ProcessStatus.IGNORED_NON_PDF: ("#64748B", "#F1F5F9"),
    ProcessStatus.ERROR: ("#B91C1C", "#FEE2E2"),
}


class _SectionHeader(QLabel):
    """Cabeçalho de seção (11px, SemiBold, caixa-alta discreta, altura fixa 28px)."""

    def __init__(self, text: str) -> None:
        super().__init__(text)
        self.setFixedHeight(28)
        self.setStyleSheet(
            "color: #64748B; font-size: 11px; font-weight: 700; "
            "letter-spacing: 0.4px; text-transform: uppercase;"
        )


class _KVRow(QWidget):
    """Linha de metadados: rótulo (muted) + valor (mono ou primário)."""

    def __init__(self, label: str, value: str = "", copyable: bool = False) -> None:
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.lbl = QLabel(label)
        self.lbl.setFixedWidth(110)
        self.lbl.setStyleSheet("color: #64748B; font-size: 12px;")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.val = QLabel(value or "—")
        self.val.setStyleSheet("color: #0F172A; font-size: 12.5px; font-family: monospace;")
        self.val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.val.setWordWrap(True)

        layout.addWidget(self.lbl)
        layout.addWidget(self.val, 1)

        if copyable:
            btn = QPushButton("Copiar")
            btn.setFixedWidth(55)
            btn.setProperty("kind", "outline")
            btn.setStyleSheet("QPushButton { font-size: 11px; padding: 2px 8px; }")
            layout.addWidget(btn)
            self._copy_btn = btn

    def set_value(self, text: str) -> None:
        self.val.setText(text or "—")


class ABNTReferenceCard(QFrame):
    """Cartão de referência ABNT NBR 6023 (Modo 1: Obra Organizada)."""

    copy_citation_requested = Signal(str)
    copy_markdown_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(
            "QFrame#card { background-color: #FFFFFF; border: 1px solid #E2E8F0; "
            "border-radius: 12px; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.header = _SectionHeader("REFERÊNCIA ABNT NBR 6023")
        layout.addWidget(self.header)

        self.reference_text = QTextEdit()
        self.reference_text.setReadOnly(True)
        self.reference_text.setFixedHeight(88)
        self.reference_text.setStyleSheet(
            "QTextEdit { background: transparent; border: none; "
            "font-size: 13px; line-height: 1.5; color: #0F172A; }"
        )
        layout.addWidget(self.reference_text)

        btns = QHBoxLayout()
        self.btn_copy_cit = QPushButton("Copiar Citação")
        self.btn_copy_cit.setProperty("kind", "outline")
        self.btn_copy_cit.setFixedWidth(120)
        self.btn_copy_cit.clicked.connect(
            lambda: self.copy_citation_requested.emit(self.reference_text.toPlainText())
        )
        self.btn_copy_md = QPushButton("Copiar .md")
        self.btn_copy_md.setProperty("kind", "outline")
        self.btn_copy_md.setFixedWidth(90)
        self.btn_copy_md.clicked.connect(
            lambda: self.copy_markdown_requested.emit(self.reference_text.toPlainText())
        )
        btns.addWidget(self.btn_copy_cit)
        btns.addWidget(self.btn_copy_md)
        btns.addStretch(1)
        layout.addLayout(btns)

    def set_reference(self, texto: str) -> None:
        self.reference_text.setPlainText(texto)


class ManualTriageBox(QFrame):
    """Assistente de triagem manual assistida (Modo 2: MANUAL_REVIEW / ERROR)."""

    approve_requested = Signal(str, str, str, str, str, str, list, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(
            "QFrame#card { background-color: #FFFFFF; border: 1px solid #E2E8F0; "
            "border-radius: 12px; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.header = _SectionHeader("TRIAGEM MANUAL ASSISTIDA")
        layout.addWidget(self.header)

        self.diag_lbl = QLabel("Motivo do encaminhamento: ...")
        self.diag_lbl.setWordWrap(True)
        self.diag_lbl.setStyleSheet("color: #0F172A; font-size: 12.5px;")
        layout.addWidget(self.diag_lbl)

        # Seletores de taxonomia acoplados.
        tax = QHBoxLayout()
        tax.setSpacing(8)
        self.cmb_grande = QComboBox()
        self.cmb_grande.setFixedWidth(150)
        self.cmb_area = QComboBox()
        self.cmb_area.setFixedWidth(150)
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.setFixedWidth(110)
        self.cmb_grande.currentIndexChanged.connect(self._on_grande_changed)
        tax.addWidget(QLabel("Grande Área:"))
        tax.addWidget(self.cmb_grande)
        tax.addWidget(QLabel("Área Básica:"))
        tax.addWidget(self.cmb_area)
        tax.addWidget(QLabel("Tipo:"))
        tax.addWidget(self.cmb_tipo)
        tax.addStretch(1)
        layout.addLayout(tax)

        # Campos editáveis.
        form = QHBoxLayout()
        form.setSpacing(8)
        self.edit_title = QLineEdit()
        self.edit_title.setPlaceholderText("Título")
        self.edit_subtitle = QLineEdit()
        self.edit_subtitle.setPlaceholderText("Subtítulo")
        self.edit_authors = QLineEdit()
        self.edit_authors.setPlaceholderText("Autor(es) separados por ;")
        self.edit_year = QLineEdit()
        self.edit_year.setPlaceholderText("Ano")
        self.edit_year.setFixedWidth(70)
        form.addWidget(QLabel("Título:"))
        form.addWidget(self.edit_title, 2)
        form.addWidget(QLabel("Subtítulo:"))
        form.addWidget(self.edit_subtitle, 2)
        form.addWidget(QLabel("Autor(es):"))
        form.addWidget(self.edit_authors, 2)
        form.addWidget(QLabel("Ano:"))
        form.addWidget(self.edit_year)
        layout.addLayout(form)

        # Pré-visualização ao vivo.
        self.prev_lbl = QLabel("Pré-visualização do nome padronizado: —")
        self.prev_lbl.setStyleSheet("color: #64748B; font-size: 11.5px; font-family: monospace;")
        self.prev_lbl.setWordWrap(True)
        layout.addWidget(self.prev_lbl)

        # Botão de aprovação.
        self.btn_approve = QPushButton("Aprovar e Materializar na Tomusa")
        self.btn_approve.setFixedWidth(220)
        self.btn_approve.setStyleSheet(
            "QPushButton { background: #1E3A8A; color: #FFFFFF; border: none; "
            "border-radius: 8px; padding: 8px 16px; font-weight: 600; font-size: 13px; }"
            "QPushButton:hover { background: #1E40AF; }"
        )
        self.btn_approve.clicked.connect(self._emit_approve)
        layout.addWidget(self.btn_approve)

        self._grandes_areas: list[str] = []
        self._areas_by_grande: dict[str, list[str]] = {}

    def set_taxonomy(self, grandes_areas: list[str], areas_by_grande: dict[str, list[str]]) -> None:
        self._grandes_areas = list(grandes_areas)
        self._areas_by_grande = dict(areas_by_grande)
        self.cmb_grande.clear()
        self.cmb_grande.addItems(self._grandes_areas)
        if self._grandes_areas:
            self._on_grande_changed(0)

    def _on_grande_changed(self, index: int) -> None:
        if index < 0 or index >= len(self._grandes_areas):
            return
        grande = self._grandes_areas[index]
        basicas = self._areas_by_grande.get(grande, [])
        self.cmb_area.clear()
        self.cmb_area.addItems(basicas)
        self.cmb_tipo.clear()
        self.cmb_tipo.addItems([t.value for t in DocumentType])

    def set_diagnostic(self, message: str) -> None:
        self.diag_lbl.setText(f"Motivo do encaminhamento: {message}")

    def set_suggestion(
        self,
        title: str = "",
        authors: list[str] | None = None,
        year: int | None = None,
        grande_area: str = "",
        area_basica: str = "",
        tipo: str = "",
    ) -> None:
        self.edit_title.setText(title)
        self.edit_authors.setText("; ".join(authors or []))
        self.edit_year.setText(str(year) if year else "")
        if grande_area and grande_area in self._grandes_areas:
            self.cmb_grande.setCurrentText(grande_area)
        if area_basica:
            self.cmb_area.setCurrentText(area_basica)
        if tipo:
            self.cmb_tipo.setCurrentText(tipo)

    def _emit_approve(self) -> None:
        grande = self.cmb_grande.currentText()
        area = self.cmb_area.currentText()
        tipo = self.cmb_tipo.currentText()
        title = self.edit_title.text()
        subtitle = self.edit_subtitle.text()
        authors = [a.strip() for a in self.edit_authors.text().split(";") if a.strip()]
        year_text = self.edit_year.text()
        year = int(year_text) if year_text.isdigit() else None
        self.approve_requested.emit(grande, area, tipo, title, subtitle, authors, year)


class DocumentInspectorPanel(QWidget):
    """Inspetor direito — adapta a visão conforme o ProcessStatus selecionado."""

    open_pdf_requested = Signal(str)
    reveal_requested = Signal(str)
    triage_approve_requested = Signal(
        object, str, str, str, str, str, str, list, object
    )  # entry, grande, area, tipo, title, subtitle, authors, year

    def __init__(
        self,
        tokens: ThemeTokens = EDITORIAL_PAPER_THEME,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tokens = tokens
        self._current_entry: FileManifestEntry | None = None

        self._build_ui()
        self._apply_theme(tokens)

    # ------------------------------------------------------------------ #
    # Construção da UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameStyle(QFrame.Shape.NoFrame)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(12)

        self._show_empty_state()

        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

    # ------------------------------------------------------------------ #
    # Exibição por status
    # ------------------------------------------------------------------ #

    def show_entry(self, entry: FileManifestEntry | None) -> None:
        self._clear_content()
        self._current_entry = entry

        if entry is None:
            self._show_empty_state()
            return

        status = ProcessStatus(entry.status) if isinstance(entry.status, str) else entry.status

        # Cabeçalho com chip de status.
        hdr = QFrame()
        hdr.setFixedHeight(30)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(0, 0, 0, 0)
        hdr_lay.setSpacing(6)
        fg, bg = _SEMANTIC_STATUS_COLORS.get(status, ("#64748B", "#F1F5F9"))
        chip = QLabel(status.value.replace("_", " ").title())
        chip.setFixedWidth(150)
        chip.setStyleSheet(
            f"QLabel {{ background: {bg}; color: {fg}; border-radius: 8px; "
            f"padding: 2px 10px; font-size: 11px; font-weight: 600; }}"
        )
        hdr_lay.addWidget(chip)
        hdr_lay.addStretch(1)
        self.content_layout.addWidget(hdr)

        if status == ProcessStatus.ORGANIZED:
            self._show_organized(entry)
        elif status in (ProcessStatus.MANUAL_REVIEW, ProcessStatus.ERROR):
            self._show_manual_review(entry)
        elif status == ProcessStatus.DUPLICATE_SKIPPED:
            self._show_duplicate(entry)
        elif status == ProcessStatus.IGNORED_NON_PDF:
            self._show_ignored(entry)

        self.content_layout.addStretch(1)

    def _clear_content(self) -> None:
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _show_empty_state(self) -> None:
        """Empty State refinado: ícone catálogo, título e texto explicativo."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(16)
        container_layout.addStretch(1)

        # Ícone de catálogo com opacidade suave.
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(56, 56)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pm = render_icon("catalog-empty", color="#94A3B8", size_px=36).pixmap(
            QSize(56, 56)
        )
        icon_lbl.setPixmap(pm)
        icon_lbl.setStyleSheet("QLabel { opacity: 0.4; }")
        container_layout.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Título.
        title_lbl = QLabel("Nenhum documento selecionado")
        title_lbl.setStyleSheet(
            "color: #0F172A; font-size: 15px; font-weight: 700; letter-spacing: -0.2px;"
        )
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        # Texto explicativo.
        desc_lbl = QLabel(
            "Selecione um documento na grade para visualizar "
            "sua referência ABNT NBR 6023, metadados e justificativa."
        )
        desc_lbl.setStyleSheet("color: #64748B; font-size: 13px; line-height: 1.5;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setFixedWidth(260)
        container_layout.addWidget(desc_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        container_layout.addStretch(1)
        self.content_layout.addWidget(container)

    # --- Modo 1: Organizado ------------------------------------------------- #

    def _show_organized(self, entry: FileManifestEntry) -> None:
        cls = entry.classification or {}

        card = ABNTReferenceCard()
        card.set_reference(format_abnt_reference(cls))
        card.copy_citation_requested.connect(self._copy_to_clipboard)
        card.copy_markdown_requested.connect(self._copy_to_clipboard)
        self.content_layout.addWidget(card)

        self.content_layout.addWidget(_SectionHeader("CLASSIFICAÇÃO CAPES/CNPq"))
        self.content_layout.addWidget(_KVRow("Grande Área", cls.get("grande_area", "—")))
        self.content_layout.addWidget(_KVRow("Área Básica", cls.get("area_basica", "—")))
        self.content_layout.addWidget(_KVRow("Tipo", str(cls.get("tipo", "—"))))
        self.content_layout.addWidget(
            _KVRow("Confiança", f"{float(cls.get('confidence_score', 0) or 0):.0%}")
        )
        prov = f"{cls.get('provider', '—')} / {cls.get('model', '—')}"
        self.content_layout.addWidget(_KVRow("Provedor / Modelo", prov))

        self.content_layout.addWidget(_SectionHeader("METADADOS & AUDITORIA"))
        self.content_layout.addWidget(_KVRow("DOI", cls.get("doi", "—")))
        self.content_layout.addWidget(_KVRow("ISBN", cls.get("isbn", "—")))
        self.content_layout.addWidget(_KVRow("SHA-256", entry.sha256, copyable=True))
        self.content_layout.addWidget(_KVRow("Origem", Path(entry.source_path).name))
        self.content_layout.addWidget(_KVRow("Destino", entry.destination_path or "—"))
        self.content_layout.addWidget(_KVRow("OCR (Docling)", "Sim" if entry.used_ocr else "Não"))

        reasoning = cls.get("reasoning") or entry.error_message or ""
        if reasoning:
            self.content_layout.addWidget(_SectionHeader("JUSTIFICATIVA LLM (REASONING)"))
            reason_txt = QTextEdit()
            reason_txt.setReadOnly(True)
            reason_txt.setFixedHeight(80)
            reason_txt.setPlainText(reasoning)
            reason_txt.setStyleSheet(
                "QTextEdit { background: #F8F9FA; border: 1px solid #E2E8F0; "
                "border-radius: 8px; padding: 8px; font-size: 12px; }"
            )
            self.content_layout.addWidget(reason_txt)

        btns = QHBoxLayout()
        btn_open = QPushButton("Abrir PDF")
        btn_open.setFixedWidth(100)
        btn_open.setProperty("kind", "outline")
        btn_open.clicked.connect(lambda: self.open_pdf_requested.emit(entry.source_path))
        btn_reveal = QPushButton("Mostrar na Pasta")
        btn_reveal.setFixedWidth(120)
        btn_reveal.setProperty("kind", "outline")
        btn_reveal.clicked.connect(lambda: self.reveal_requested.emit(entry.source_path))
        btns.addWidget(btn_open)
        btns.addWidget(btn_reveal)
        btns.addStretch(1)
        self.content_layout.addLayout(btns)

    # --- Modo 2: Revisão Manual / Erro -------------------------------------- #

    def _show_manual_review(self, entry: FileManifestEntry) -> None:
        cls = entry.classification or {}

        self.content_layout.addWidget(_SectionHeader("QUADRO DE DIAGNÓSTICO DE PENDÊNCIA"))
        diag = QFrame()
        diag.setObjectName("card")
        diag.setStyleSheet(
            "QFrame#card { background-color: #FEF3C7; border: 1px solid #FCD34D; "
            "border-radius: 12px; }"
        )
        diag_lay = QVBoxLayout(diag)
        diag_msg = QLabel(entry.error_message or cls.get("reasoning") or "Pendente de revisão manual.")
        diag_msg.setWordWrap(True)
        diag_msg.setStyleSheet("color: #0F172A; font-size: 12.5px;")
        diag_lay.addWidget(diag_msg)
        self.content_layout.addWidget(diag)

        triage = ManualTriageBox()
        triage.set_diagnostic(entry.error_message or cls.get("reasoning") or "")
        triage.set_suggestion(
            title=cls.get("title", ""),
            authors=cls.get("authors", []),
            year=cls.get("year"),
            grande_area=cls.get("grande_area", ""),
            area_basica=cls.get("area_basica", ""),
            tipo=str(cls.get("tipo", "")),
        )
        triage.approve_requested.connect(self._on_triage_approve)
        self.content_layout.addWidget(triage)

        btn_open = QPushButton("Abrir PDF para Inspeção")
        btn_open.setFixedWidth(150)
        btn_open.setProperty("kind", "outline")
        btn_open.clicked.connect(lambda: self.open_pdf_requested.emit(entry.source_path))
        self.content_layout.addWidget(btn_open)

    # --- Modo 3: Duplicata -------------------------------------------------- #

    def _show_duplicate(self, entry: FileManifestEntry) -> None:
        self.content_layout.addWidget(_SectionHeader("DUPLICATA EXATA"))
        self.content_layout.addWidget(_KVRow("SHA-256", entry.sha256, copyable=True))
        self.content_layout.addWidget(
            _KVRow("Caminho", entry.destination_path or "revisao_manual/")
        )
        btn_show = QPushButton("Mostrar Obra Canônica na Pasta")
        btn_show.setFixedWidth(170)
        btn_show.setProperty("kind", "outline")
        btn_show.clicked.connect(lambda: self.reveal_requested.emit(entry.source_path))
        self.content_layout.addWidget(btn_show)

    # --- Modo 3b: Não-PDF ignorado ------------------------------------------ #

    def _show_ignored(self, entry: FileManifestEntry) -> None:
        self.content_layout.addWidget(_SectionHeader("NÃO-PDF IGNORADO"))
        self.content_layout.addWidget(
            _KVRow("Diagnóstico", entry.error_message or "Não-PDF ignorado")
        )
        btn_reveal = QPushButton("Revelar Arquivo Original")
        btn_reveal.setFixedWidth(130)
        btn_reveal.setProperty("kind", "outline")
        btn_reveal.clicked.connect(lambda: self.reveal_requested.emit(entry.source_path))
        self.content_layout.addWidget(btn_reveal)

    # ------------------------------------------------------------------ #
    # Handlers
    # ------------------------------------------------------------------ #

    def _on_triage_approve(self, grande, area, tipo, title, subtitle, authors, year) -> None:
        if self._current_entry is not None:
            self.triage_approve_requested.emit(
                self._current_entry, grande, area, tipo, title, subtitle, authors, year
            )

    @staticmethod
    def _copy_to_clipboard(texto: str) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(texto)

    # ------------------------------------------------------------------ #
    # Tema
    # ------------------------------------------------------------------ #

    def _apply_theme(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            f"QWidget {{ background-color: {tokens.bg_surface}; color: {tokens.text_primary}; }}"
        )
