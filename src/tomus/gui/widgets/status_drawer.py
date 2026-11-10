"""Barra inferior de telemetria ao vivo e gaveta de diagnóstico (Seção 3.2 item E).

Componentes:
* ``TelemetryStatusBar`` — barra de progresso determinística, indicador de
  estágio e monitor do teto de revisão manual (<= 20%).
* ``LogCacheDrawer`` — gaveta expansível (Cmd+` / Ctrl+`) com Log de Execução
  e Estado do Cache SQLite (botão Limpar Cache).
  Conforme Mockup 1: fundo suave #F8F9FA, bordas 1px #E2E8F0, border-radius 8-12px.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from tomus.core.cache import CACHE_DB_PATH
from tomus.gui.theme import EDITORIAL_PAPER_THEME, ThemeTokens

__all__ = ["TelemetryStatusBar", "LogCacheDrawer"]

_STAGE_LABELS = {
    "scanner": "Scanner",
    "cache": "Cache",
    "extractor": "Extração",
    "enricher": "Enriquecimento",
    "llm": "Classificação LLM",
    "organizer": "Organização",
    "pipeline": "Concluído",
}


class TelemetryStatusBar(QWidget):
    """Barra de progresso determinística + estágio + teto de revisão manual."""

    filter_manual_review_requested = Signal()

    def __init__(
        self,
        tokens: ThemeTokens = EDITORIAL_PAPER_THEME,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tokens = tokens
        self._completed = 0
        self._total = 0
        self._stage = ""
        self._manual_ratio = 0.0
        self._exceeded = False

        self._build_ui()
        self._apply_theme(tokens)

    # ------------------------------------------------------------------ #
    # Construção da UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        self.setFixedHeight(32)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 4, 16, 4)
        layout.setSpacing(12)

        # Barra de progresso.
        self.progress = QProgressBar()
        self.progress.setFixedWidth(200)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.pct_lbl = QLabel("0%")
        self.pct_lbl.setFixedWidth(35)
        self.pct_lbl.setStyleSheet("color: #0F172A; font-size: 12px; font-family: monospace; font-weight: 600;")
        layout.addWidget(self.pct_lbl)

        self.frac_lbl = QLabel("0 / 0")
        self.frac_lbl.setFixedWidth(50)
        self.frac_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-family: monospace;")
        layout.addWidget(self.frac_lbl)

        self.rem_lbl = QLabel("Restam: 0")
        self.rem_lbl.setFixedWidth(60)
        self.rem_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-family: monospace;")
        layout.addWidget(self.rem_lbl)

        # Indicador de estágio.
        self.stage_lbl = QLabel("Ocioso")
        self.stage_lbl.setStyleSheet("color: #64748B; font-size: 12px;")
        layout.addWidget(self.stage_lbl)

        layout.addStretch(1)

        # Teto de revisão manual.
        self.ceiling_lbl = QLabel("Revisão Manual: 0,0% (dentro do teto <= 20%)")
        self.ceiling_lbl.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 600;")
        self.ceiling_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ceiling_lbl.mousePressEvent = lambda _e: self.filter_manual_review_requested.emit()
        layout.addWidget(self.ceiling_lbl)

    # ------------------------------------------------------------------ #
    # API de atualização (chamada pelos sinais do PipelineWorker)
    # ------------------------------------------------------------------ #

    def set_progress(self, completed: int, total: int) -> None:
        self._completed = completed
        self._total = total
        pct = int((completed / total) * 100) if total else 0
        self.progress.setValue(pct)
        self.pct_lbl.setText(f"{pct}%")
        self.frac_lbl.setText(f"{completed} / {total}")
        self.rem_lbl.setText(f"Restam: {max(0, total - completed)}")

    def set_stage(self, stage: str) -> None:
        self._stage = stage
        label = _STAGE_LABELS.get(stage, stage)
        self.stage_lbl.setText(f"Estágio: {label}")

    def set_manual_review(self, ratio: float, exceeded: bool) -> None:
        self._manual_ratio = ratio
        self._exceeded = exceeded
        pct_text = f"{ratio * 100:.1f}".replace(".", ",")
        if exceeded:
            self.ceiling_lbl.setText(
                f"Revisão Manual: {pct_text}% — Acima do teto de 20%"
            )
            self.ceiling_lbl.setStyleSheet(
                "color: #B45309; font-size: 12px; font-weight: 600;"
            )
        else:
            self.ceiling_lbl.setText(
                f"Revisão Manual: {pct_text}% (dentro do teto <= 20%)"
            )
            self.ceiling_lbl.setStyleSheet(
                "color: #15803D; font-size: 12px; font-weight: 600;"
            )

    def reset(self) -> None:
        self.set_progress(0, 0)
        self.set_stage("")
        self.set_manual_review(0.0, False)

    # ------------------------------------------------------------------ #
    # Tema
    # ------------------------------------------------------------------ #

    def _apply_theme(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            f"QWidget {{ background-color: {tokens.bg_canvas}; color: {tokens.text_primary}; }}"
            f"QProgressBar {{ border: 1px solid {tokens.border_subtle}; "
            f"border-radius: 6px; background: {tokens.bg_elevated}; text-align: center; }}"
            f"QProgressBar::chunk {{ background: {tokens.accent_primary}; border-radius: 6px; }}"
        )


class LogCacheDrawer(QWidget):
    """Gaveta expansível (180px) com Log de Execução e Estado do Cache SQLite."""

    clear_cache_requested = Signal()

    def __init__(
        self,
        tokens: ThemeTokens = EDITORIAL_PAPER_THEME,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tokens = tokens
        self._expanded = False
        self.setFixedHeight(0)  # colapsada por padrão

        self._build_ui()
        self._apply_theme(tokens)

    # ------------------------------------------------------------------ #
    # Construção da UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de toggle.
        self.toggle_btn = QPushButton("Logs ^")
        self.toggle_btn.setFixedHeight(28)
        self.toggle_btn.setStyleSheet(
            "QPushButton { background: #F1F5F9; border: none; border-top: 1px solid #E2E8F0; "
            "border-left: 1px solid #E2E8F0; border-right: 1px solid #E2E8F0; "
            "text-align: left; padding: 2px 16px; font-size: 12px; color: #64748B; font-weight: 600; }"
            "QPushButton:hover { background: #E2E8F0; }"
        )
        self.toggle_btn.clicked.connect(self.toggle)
        layout.addWidget(self.toggle_btn)

        # Conteúdo (duas abas).
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #E2E8F0; background: #FFFFFF; border-radius: 0 0 12px 12px; }"
            "QTabBar::tab { background: #F8F9FA; color: #64748B; padding: 6px 14px; font-size: 12px; font-weight: 600; }"
            "QTabBar::tab:selected { background: #FFFFFF; color: #0F172A; font-weight: 700; }"
        )

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            "QTextEdit { background: #F8F9FA; color: #0F172A; font-family: monospace; font-size: 11.5px; border: none; }"
        )
        self.tabs.addTab(self.log_view, "Log de Execução")

        self.cache_view = QTextEdit()
        self.cache_view.setReadOnly(True)
        self.cache_view.setStyleSheet(
            "QTextEdit { background: #F8F9FA; color: #0F172A; font-family: monospace; font-size: 11.5px; border: none; }"
        )
        self.tabs.addTab(self.cache_view, "Estado do Cache SQLite")

        layout.addWidget(self.tabs)

        # Botão limpar cache.
        btn_bar = QHBoxLayout()
        btn_bar.setContentsMargins(12, 8, 12, 8)
        self.btn_clear = QPushButton("Limpar Cache SQLite")
        self.btn_clear.setFixedWidth(130)
        self.btn_clear.setProperty("kind", "outline")
        self.btn_clear.setStyleSheet(
            "QPushButton { background: #FEE2E2; color: #B91C1C; border: 1px solid #FECACA; "
            "border-radius: 8px; padding: 6px 12px; font-size: 12px; font-weight: 600; }"
            "QPushButton:hover { background: #FECACA; }"
        )
        self.btn_clear.clicked.connect(self.clear_cache_requested.emit)
        btn_bar.addWidget(self.btn_clear)
        btn_bar.addStretch(1)
        layout.addLayout(btn_bar)

    # ------------------------------------------------------------------ #
    # Controle da gaveta
    # ------------------------------------------------------------------ #

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self.setFixedHeight(180 if self._expanded else 0)
        self.toggle_btn.setText("Logs v" if self._expanded else "Logs ^")

    def expand(self) -> None:
        if not self._expanded:
            self.toggle()

    def collapse(self) -> None:
        if self._expanded:
            self.toggle()

    # ------------------------------------------------------------------ #
    # Logs e cache
    # ------------------------------------------------------------------ #

    def append_log(self, text: str) -> None:
        self.log_view.append(text)

    def clear_logs(self) -> None:
        self.log_view.clear()

    def refresh_cache_stats(self) -> None:
        """Ler estado do cache SQLite e exibir no cache_view."""
        lines = [f"Caminho: {CACHE_DB_PATH}"]
        if CACHE_DB_PATH.exists():
            tamanho_kb = CACHE_DB_PATH.stat().st_size / 1024
            lines.append(f"Tamanho: {tamanho_kb:.1f} KB")
            try:
                conn = sqlite3.connect(str(CACHE_DB_PATH))
                try:
                    cur = conn.execute("SELECT COUNT(*) FROM processed_files")
                    registros = cur.fetchone()[0]
                finally:
                    conn.close()
                lines.append(f"Registros: {registros}")
            except sqlite3.Error as exc:
                lines.append(f"Erro ao ler cache: {exc}")
        else:
            lines.append("Tamanho: 0 KB")
            lines.append("Registros: 0 (cache não inicializado)")
        self.cache_view.setPlainText("\n".join(lines))

    # ------------------------------------------------------------------ #
    # Tema
    # ------------------------------------------------------------------ #

    def _apply_theme(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            f"QWidget {{ background-color: {tokens.bg_canvas}; color: {tokens.text_primary}; }}"
        )
