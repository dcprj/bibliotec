"""Testes da Etapa 2 da Passagem 2 — componentes da GUI do Tomus.

Valida:
* DocumentTableModel (8 colunas, upsert a partir de PipelineEvent, replace_all);
* PipelineWorker (criação, sinais, cancelamento cooperativo);
* Geração de QSS (cores dos tokens, sem gradientes/neon);
* Instanciação dos widgets principais (toolbar, sidebar, tabela, inspetor,
  status bar, gaveta, diálogo de preferências) em modo offscreen.

Execução alvo:

    QT_QPA_PLATFORM=offscreen pytest -m 'not slow' tests/test_gui_components.py
"""

from __future__ import annotations

import os as _os

_os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import threading

import pytest
from PySide6.QtWidgets import QApplication

from tomus.core.config import AppConfig
from tomus.core.models import (
    ExecutionSummary,
    FileManifestEntry,
    PipelineEvent,
    ProcessStatus,
)
from tomus.gui.models import DocumentTableModel
from tomus.gui.theme import EDITORIAL_PAPER_THEME, generate_qss
from tomus.gui.worker import ManualTriageService, PipelineWorker

__all__ = []


# --------------------------------------------------------------------------- #
# Fixture QApplication
# --------------------------------------------------------------------------- #

_QAPP = None


@pytest.fixture(scope="session")
def qapp():
    global _QAPP
    if _QAPP is None:
        _QAPP = QApplication.instance() or QApplication([])
    return _QAPP


# --------------------------------------------------------------------------- #
# DocumentTableModel
# --------------------------------------------------------------------------- #

def test_model_tem_8_colunas(qapp):
    model = DocumentTableModel()
    assert model.columnCount() == 8
    assert model.rowCount() == 0


def test_model_upsert_from_event_atualiza_status(qapp):
    """PipelineEvent terminal atualiza o status da linha (sem classification)."""
    model = DocumentTableModel()
    event = PipelineEvent(
        stage="organizer",
        source_path="/tmp/teste.pdf",
        status=ProcessStatus.ORGANIZED.value,
        message="Arquivo organizado",
    )
    model.upsert_from_event(event)
    assert model.rowCount() == 1
    row = model.row(0)
    assert row is not None
    assert row.source_path == "/tmp/teste.pdf"
    assert row.status == ProcessStatus.ORGANIZED.value
    assert row.stage == "organizer"
    assert row.message == "Arquivo organizado"


def test_model_upsert_event_scanner_completed_nao_insere(qapp):
    model = DocumentTableModel()
    event = PipelineEvent(
        stage="scanner",
        source_path="/tmp",
        status="completed",
        message="3 PDF(s) válido(s)",
        total_files=3,
    )
    model.upsert_from_event(event)
    assert model.rowCount() == 0


def test_model_upsert_event_scanner_started_diretorio_origem_nao_insere(qapp, tmp_path):
    """Eventos de ciclo de vida do scanner sobre pastas (ex: origem) não devem virar itens na grade."""
    model = DocumentTableModel()
    event = PipelineEvent(
        stage="scanner",
        source_path=str(tmp_path),
        status="started",
        message="Varredura do diretório de origem",
    )
    model.upsert_from_event(event)
    assert model.rowCount() == 0


def test_model_upsert_event_pipeline_completed_diretorio_destino_nao_insere(qapp, tmp_path):
    """Evento final do pipeline com target_dir não deve ser inserido na grade."""
    model = DocumentTableModel()
    event = PipelineEvent(
        stage="pipeline",
        source_path=str(tmp_path),
        status="completed",
        message="24 organizado(s), 1 revisão manual",
    )
    model.upsert_from_event(event)
    assert model.rowCount() == 0


def test_model_upsert_event_em_processamento_tem_status_processing(qapp):
    """Enquanto o pipeline processa, o status inicial é 'processing' e não 'organized' prematuro."""
    model = DocumentTableModel()
    event = PipelineEvent(
        stage="extractor",
        source_path="/tmp/livro_em_processamento.pdf",
        status="started",
        message="Extraindo conteúdo do PDF",
    )
    model.upsert_from_event(event)
    assert model.rowCount() == 1
    row = model.row(0)
    assert row is not None
    assert row.status == "processing"


def test_model_replace_all(qapp):
    model = DocumentTableModel()
    entries = [
        FileManifestEntry(
            source_path="/tmp/a.pdf",
            destination_path="/tmp/dst/a.pdf",
            sha256="sha-a",
            status=ProcessStatus.ORGANIZED,
        ),
        FileManifestEntry(
            source_path="/tmp/b.pdf",
            destination_path=None,
            sha256="sha-b",
            status=ProcessStatus.ERROR,
            error_message="PDF corrompido",
        ),
    ]
    model.replace_all(entries)
    assert model.rowCount() == 2
    model.clear()
    assert model.rowCount() == 0


# --------------------------------------------------------------------------- #
# PipelineWorker
# --------------------------------------------------------------------------- #

def test_worker_criacao_e_cancelamento(qapp):
    config = AppConfig()
    worker = PipelineWorker(
        source_dir="/tmp/src",
        target_dir="/tmp/dst",
        config=config,
    )
    assert isinstance(worker.cancel_event, threading.Event)
    assert not worker.cancel_event.is_set()
    worker.request_cancel()
    assert worker.cancel_event.is_set()


def test_worker_sinais_existem(qapp):
    worker = PipelineWorker(
        source_dir="/tmp/src",
        target_dir="/tmp/dst",
        config=AppConfig(),
    )
    assert hasattr(worker, "event_received")
    assert hasattr(worker, "pipeline_finished")
    assert hasattr(worker, "pipeline_failed")


# --------------------------------------------------------------------------- #
# QSS
# --------------------------------------------------------------------------- #

def test_qss_contem_tokens_do_tema():
    qss = generate_qss(EDITORIAL_PAPER_THEME)
    assert "#F8F9FA" in qss  # bg_canvas
    assert "#FFFFFF" in qss  # bg_surface
    assert "#1E3A8A" in qss  # accent_primary / border_focus
    assert "gradient" not in qss.lower()


# --------------------------------------------------------------------------- #
# Widgets — instanciação em offscreen
# --------------------------------------------------------------------------- #

def test_toolbar_instancia(qapp):
    from tomus.gui.widgets.toolbar import OperationalToolbar

    toolbar = OperationalToolbar()
    assert toolbar.provider_key() == "gemini"
    assert toolbar.file_operation() == "copy"
    assert toolbar.dry_run() is False
    assert toolbar.recursive() is True


def test_sidebar_instancia(qapp):
    from tomus.gui.widgets.sidebar import CapesSidebarPanel

    sidebar = CapesSidebarPanel()
    sidebar.set_counters({"total": 10, "organized": 7, "error": 1})
    areas = {
        "Ciências Humanas": {"Psicologia": ["Livro", "Artigo"]},
        "Ciências Exatas": {"Ciência da Computação": ["Artigo"]},
    }
    sidebar.populate_tree(areas)
    assert sidebar.tree.topLevelItemCount() == 2


def test_document_table_panel_instancia(qapp):
    from tomus.gui.widgets.document_table import DocumentTablePanel

    panel = DocumentTablePanel()
    panel.clear()
    assert panel.table.model().rowCount() == 0


def test_inspector_instancia(qapp):
    from tomus.gui.widgets.inspector import DocumentInspectorPanel

    inspector = DocumentInspectorPanel()
    inspector.show_entry(None)
    assert inspector._current_entry is None


def test_status_bar_instancia(qapp):
    from tomus.gui.widgets.status_drawer import TelemetryStatusBar

    bar = TelemetryStatusBar()
    bar.set_progress(50, 100)
    bar.set_stage("llm")
    bar.set_manual_review(0.10, False)
    assert bar.progress.value() == 50


def test_log_drawer_instancia(qapp):
    from tomus.gui.widgets.status_drawer import LogCacheDrawer

    drawer = LogCacheDrawer()
    drawer.append_log("teste de log")
    drawer.refresh_cache_stats()
    assert drawer.height() == 0  # colapsada por padrão


def test_preferences_dialog_instancia(qapp):
    from tomus.gui.widgets.preferences_dialog import PreferencesDialog

    dlg = PreferencesDialog(AppConfig())
    assert dlg is not None
    dlg.reject()


# --------------------------------------------------------------------------- #
# ManualTriageService (instanciação e validação de par inválido)
# --------------------------------------------------------------------------- #

def test_triage_service_instancia(qapp, tmp_path):
    service = ManualTriageService(tmp_path, AppConfig())
    assert service is not None
    assert service.target_dir == tmp_path.resolve()


def test_triage_service_par_invalido(qapp, tmp_path):
    service = ManualTriageService(tmp_path, AppConfig())
    entry = FileManifestEntry(
        source_path="/tmp/x.pdf",
        sha256="abc",
        status=ProcessStatus.MANUAL_REVIEW,
    )
    with pytest.raises(ValueError):
        service.approve_and_materialize(
            entry,
            grande_area="Área Inexistente",
            area_basica="Também Inexistente",
            tipo="Livro",
            title="T",
            subtitle="",
            authors=["A, B"],
            year=2020,
        )
