"""Barra superior de operação e banner de retomada de sessão (Seção 3.2 item A).

Componentes:
* ``OperationalToolbar`` — cabeçalho de controle em 2 linhas conforme Mockup 1:
  Linha 1: marca "BiblioTEC" | Origem | Destino | Organizar Acervo (primário)
  Linha 2: seletor de modelo em pílula | badge chave ativa | Copiar | Mover |
           Recursivo | Simulação | Preferências | Cache
* ``SessionResumeBanner`` — faixa fina (34px) exibida quando há sessão
  interrompida (``.bibliotec_session.json`` válida).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from bibliotec.gui.theme import EDITORIAL_PAPER_THEME, ThemeTokens

__all__ = ["OperationalToolbar", "SessionResumeBanner"]

# Provedores oficiais suportados pelo motor (seção 3.2 item A).
PROVIDERS = [
    ("gemini", "Gemini (gemini-3.5-flash)"),
    ("groq", "Groq (openai/gpt-oss-20b)"),
    ("nvidia", "NVIDIA NIM"),
    ("deepseek", "DeepSeek"),
    ("claude", "Anthropic Claude"),
    ("github", "GitHub Models"),
]

_IS_MAC = sys.platform == "darwin"


class _PathField(QWidget):
    """Campo de diretório com cantos suaves (mockup 1)."""

    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.label = QLabel(label)
        self.label.setFixedWidth(70)
        self.label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")

        self.edit = QLabel("—")
        self.edit.setStyleSheet(
            "QLabel { background: #F1F5F9; border: 1px solid #E2E8F0; "
            "border-radius: 8px; padding: 6px 12px; font-family: monospace; "
            "font-size: 12.5px; color: #0F172A; }"
        )
        self.edit.setCursor(Qt.CursorShape.IBeamCursor)
        self.edit.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.btn = QPushButton("Procurar")
        self.btn.setFixedWidth(90)
        self.btn.setProperty("kind", "outline")

        layout.addWidget(self.label)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.btn)

    def set_path(self, path: str | None) -> None:
        if path:
            self.edit.setText(str(Path(path)))
        else:
            self.edit.setText("—")

    def path(self) -> str:
        text = self.edit.text()
        return text if text and text != "—" else ""

    def set_error(self, error: bool) -> None:
        border = "#B91C1C" if error else "#E2E8F0"
        bg = "#FEE2E2" if error else "#F1F5F9"
        self.edit.setStyleSheet(
            f"QLabel {{ background: {bg}; border: 1px solid {border}; "
            "border-radius: 8px; padding: 6px 12px; font-family: monospace; "
            "font-size: 12.5px; color: #0F172A; }}"
        )


class OperationalToolbar(QWidget):
    """Barra de comando e operação da bancada principal (Mockup 1)."""

    source_changed = Signal(str)
    target_changed = Signal(str)
    browse_source = Signal()
    browse_target = Signal()
    organize_requested = Signal()
    cancel_requested = Signal()
    preferences_requested = Signal()
    cache_requested = Signal()
    dry_run_toggled = Signal(bool)

    def __init__(
        self,
        tokens: ThemeTokens = EDITORIAL_PAPER_THEME,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tokens = tokens
        self._file_operation = "copy"  # "copy" | "move"
        self.setObjectName("toolbar")

        self._build_ui()
        self._apply_theme(tokens)

    # ------------------------------------------------------------------ #
    # Construção da UI — Mockup 1: cabeçalho em 2 linhas
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ================================================================= #
        # Linha 1: Marca | Origem | Destino | Organizar Acervo (primário)   #
        # ================================================================= #
        row1 = QHBoxLayout()
        row1.setContentsMargins(16, 12, 16, 10)
        row1.setSpacing(12)

        # Marca BiblioTEC à esquerda.
        self.brand_lbl = QLabel("BiblioTEC", self)
        self.brand_lbl.setObjectName("brand")
        self.brand_lbl.setFixedWidth(120)
        row1.addWidget(self.brand_lbl)

        row1.addSpacing(8)

        # Origem (expandida).
        self.source_field = _PathField("Origem", self)
        self.source_field.btn.clicked.connect(self.browse_source.emit)
        row1.addWidget(self.source_field, 1)

        # Destino (expandida).
        self.target_field = _PathField("Destino", self)
        self.target_field.btn.clicked.connect(self.browse_target.emit)
        row1.addWidget(self.target_field, 1)

        # Botão de ação primária (azul profundo #1E3A8A).
        self.btn_action = QPushButton("Organizar Acervo", self)
        self.btn_action.setObjectName("primary")
        self.btn_action.setMinimumWidth(170)
        self.btn_action.clicked.connect(self._on_action_clicked)
        self.btn_action.setShortcut(
            QKeySequence("Cmd+R" if _IS_MAC else "Ctrl+R")
        )
        row1.addWidget(self.btn_action)

        layout.addLayout(row1)

        # Divisória sutil entre linhas.
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #E2E8F0; border: none;")
        layout.addWidget(sep)

        # =================================================================== #
        # Linha 2: Modelo | Chave | Copiar | Mover | Recursivo | DryRun       #
        #           | Preferências | Cache                                   #
        # =================================================================== #
        row2 = QHBoxLayout()
        row2.setContentsMargins(16, 10, 16, 12)
        row2.setSpacing(10)

        # Seletor de modelo em pílula.
        prov_box = QHBoxLayout()
        prov_box.setSpacing(6)
        prov_label = QLabel("Modelo")
        prov_label.setFixedWidth(50)
        prov_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        prov_label.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 600;")
        self.provider_combo = QComboBox(self)
        self.provider_combo.setObjectName("segmented")
        for key, label in PROVIDERS:
            self.provider_combo.addItem(label, key)
        self.provider_combo.setFixedWidth(200)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)

        # Badge translúcido "● Chave Ativa".
        self.key_dot = QLabel("●", self)
        self.key_dot.setFixedSize(10, 10)
        self.key_dot.setStyleSheet("color: #15803D;")
        self.key_text = QLabel("Chave Ativa", self)
        self.key_text.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 600;")

        prov_box.addWidget(prov_label)
        prov_box.addWidget(self.provider_combo)
        prov_box.addSpacing(10)
        prov_box.addWidget(self.key_dot)
        prov_box.addWidget(self.key_text)
        prov_box.addStretch(1)
        row2.addLayout(prov_box)

        # Separador visual sutil.
        sep2 = QFrame(self)
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFixedHeight(16)
        sep2.setStyleSheet("background-color: #E2E8F0; border: none;")
        row2.addWidget(sep2)

        # Controle segmentado Copiar | Mover.
        mode_box = QHBoxLayout()
        mode_box.setSpacing(0)
        mode_box.setContentsMargins(0, 0, 0, 0)

        self.btn_copy = QPushButton("Copiar", self)
        self.btn_copy.setObjectName("segmented")
        self.btn_copy.setCheckable(True)
        self.btn_copy.setChecked(True)
        self.btn_copy.clicked.connect(lambda: self._set_mode("copy"))

        self.btn_move = QPushButton("Mover", self)
        self.btn_move.setObjectName("segmented")
        self.btn_move.setCheckable(True)
        self.btn_move.clicked.connect(lambda: self._set_mode("move"))

        # Remover bordas duplas entre os botões segmentados.
        self.btn_copy.setStyleSheet(
            "QPushButton#segmented { border-top-left-radius: 8px; "
            "border-bottom-left-radius: 8px; border-right: none; }"
            "QPushButton#segmented:checked { border-right: none; }"
        )
        self.btn_move.setStyleSheet(
            "QPushButton#segmented { border-top-right-radius: 8px; "
            "border-bottom-right-radius: 8px; border-left: none; }"
            "QPushButton#segmented:checked { border-left: none; }"
        )

        mode_box.addWidget(self.btn_copy)
        mode_box.addWidget(self.btn_move)
        row2.addLayout(mode_box)

        row2.addSpacing(12)

        # Checkboxes arejados.
        self.chk_recursive = QCheckBox("Recursivo", self)
        self.chk_recursive.setChecked(True)
        self.chk_dry = QCheckBox("Simulação (Dry-Run)", self)
        self.chk_dry.stateChanged.connect(
            lambda s: self.dry_run_toggled.emit(s == Qt.CheckState.Checked)
        )

        row2.addWidget(self.chk_recursive)
        row2.addWidget(self.chk_dry)

        row2.addStretch(1)

        # Botões outline à direita.
        self.btn_prefs = QPushButton("Preferências", self)
        self.btn_prefs.setObjectName("outline")
        self.btn_prefs.clicked.connect(self.preferences_requested.emit)
        self.btn_prefs.setShortcut(QKeySequence("Cmd+," if _IS_MAC else "Ctrl+,"))

        self.btn_cache = QPushButton("Cache", self)
        self.btn_cache.setObjectName("outline")
        self.btn_cache.clicked.connect(self.cache_requested.emit)

        row2.addWidget(self.btn_prefs)
        row2.addWidget(self.btn_cache)

        layout.addLayout(row2)

    def _on_provider_changed(self, _idx: int) -> None:
        pass  # A janela principal lê provider_key() quando necessário.

    def _set_mode(self, mode: str) -> None:
        self._file_operation = mode
        self.btn_copy.setChecked(mode == "copy")
        self.btn_move.setChecked(mode == "move")

    # ------------------------------------------------------------------ #
    # Ações
    # ------------------------------------------------------------------ #

    def _on_action_clicked(self) -> None:
        if self.btn_action.property("running"):
            self.cancel_requested.emit()
        else:
            self.organize_requested.emit()

    # ------------------------------------------------------------------ #
    # Estado
    # ------------------------------------------------------------------ #

    def set_source(self, path: str | None) -> None:
        self.source_field.set_path(path)
        self.source_changed.emit(self.source_field.path())

    def set_target(self, path: str | None) -> None:
        self.target_field.set_path(path)
        self.target_changed.emit(self.target_field.path())

    def set_provider(self, key: str) -> None:
        for i in range(self.provider_combo.count()):
            if self.provider_combo.itemData(i) == key:
                self.provider_combo.setCurrentIndex(i)
                break

    def provider_key(self) -> str:
        return self.provider_combo.currentData() or "gemini"

    def set_key_status(self, has_key: bool, message: str = "") -> None:
        """Atualizar badge de chave ativa (● Chave Ativa)."""
        color = "#15803D" if has_key else "#B45309"
        self.key_dot.setStyleSheet(f"color: {color};")
        self.key_text.setText(message or ("Chave Ativa" if has_key else "Chave Não Configurada"))
        self.key_text.setStyleSheet(
            f"color: {color}; font-size: 12px; font-weight: 600;"
        )

    def set_running(self, running: bool) -> None:
        """Alternar entre estado ocioso e executando."""
        self.btn_action.setProperty("running", running)
        if running:
            self.btn_action.setText("Interromper Lote")
            self.btn_action.setStyleSheet(
                "QPushButton#primary { background: #B91C1C; color: #FFFFFF; border: none; "
                "border-radius: 8px; padding: 8px 16px; font-weight: 600; font-size: 13px; }"
                "QPushButton#primary:hover { background: #991B1B; }"
            )
            self.btn_action.setShortcut(QKeySequence("Esc"))
            self.btn_action.setToolTip("Interromper lote (Esc)")
        else:
            self.btn_action.setText("Organizar Acervo")
            self.btn_action.setStyleSheet("")
            self.btn_action.setShortcut(
                QKeySequence("Cmd+R" if _IS_MAC else "Ctrl+R")
            )
            self.btn_action.setToolTip("Organizar Acervo (Cmd+R / Ctrl+R)")
        self.source_field.btn.setEnabled(not running)
        self.target_field.btn.setEnabled(not running)
        self.provider_combo.setEnabled(not running)
        self.btn_copy.setEnabled(not running)
        self.btn_move.setEnabled(not running)
        self.chk_recursive.setEnabled(not running)
        self.chk_dry.setEnabled(not running)

    def file_operation(self) -> str:
        return self._file_operation

    def dry_run(self) -> bool:
        return self.chk_dry.isChecked()

    def recursive(self) -> bool:
        return self.chk_recursive.isChecked()

    def _apply_theme(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            f"QWidget#toolbar {{ background-color: {tokens.bg_canvas}; "
            f"color: {tokens.text_primary}; }}"
        )


class SessionResumeBanner(QWidget):
    """Faixa fina (34px) exibida quando há sessão interrompida válida.

    Exibe os detalhes da sessão e dois botões: Retomar Sessão e Descartar.
    """

    resume_requested = Signal()
    discard_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setVisible(False)
        self.setObjectName("sessionBanner")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 12, 2)
        layout.setSpacing(10)

        self.icon_lbl = QLabel("⚠")
        self.icon_lbl.setFixedSize(16, 16)
        self.icon_lbl.setStyleSheet("color: #B45309; font-weight: 700; font-size: 12px;")

        self.msg_lbl = QLabel("Sessão interrompida detectada")
        self.msg_lbl.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 600;")

        self.detail_lbl = QLabel("")
        self.detail_lbl.setStyleSheet("color: #64748B; font-size: 11px; font-family: monospace;")

        self.btn_resume = QPushButton("Retomar Sessão")
        self.btn_resume.setFixedWidth(105)
        self.btn_resume.setObjectName("primary")
        self.btn_resume.clicked.connect(self.resume_requested.emit)

        self.btn_discard = QPushButton("Descartar")
        self.btn_discard.setFixedWidth(80)
        self.btn_discard.setObjectName("outline")
        self.btn_discard.clicked.connect(self.discard_requested.emit)

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.msg_lbl)
        layout.addWidget(self.detail_lbl, 1)
        layout.addStretch(1)
        layout.addWidget(self.btn_resume)
        layout.addWidget(self.btn_discard)

    def set_session(self, summary: str) -> None:
        self.msg_lbl.setText("Sessão interrompida detectada")
        self.detail_lbl.setText(summary)
        self.setVisible(True)

    def hide_banner(self) -> None:
        self.setVisible(False)
