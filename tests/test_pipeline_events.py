"""Teste de integração validando propagação ponta a ponta dos eventos de pipeline com total_files.

Garante que o NameError em _emit foi resolvido e que a barra de progresso
não fica congelada em '0/?' ao usar múltiplos workers.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
import pytest

from bibliotec.core.cache import FileCache
from bibliotec.core.config import AppConfig
from bibliotec.core.models import PipelineEvent, ProcessStatus
from bibliotec.core.pipeline import run_pipeline
from bibliotec.core.llm import ClassificationResult, MockLLMProvider


def _criar_pdf(caminho: Path, texto: str = "Título de teste Autor Silva, João 2020") -> str:
    """Criar um PDF sintético de uma página e retornar seu SHA-256."""
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto)
    doc.save(str(caminho))
    doc.close()
    import hashlib
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def test_pipeline_events_propagation_with_total_files(tmp_path: Path):
    """Validar que eventos de pipeline incluem total_files e não travam em 0/?."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()

    for i in range(5):
        _criar_pdf(source / f"doc_{i}.pdf")

    cfg = AppConfig()
    events: list[PipelineEvent] = []

    def callback(event: PipelineEvent) -> None:
        events.append(event)

    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=4,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
        event_callback=callback,
    )

    # Todos os PDFs processados sem erro.
    assert summary.total_scanned == 5
    assert summary.error_count == 0
    assert summary.organized_count + summary.manual_review_count == 5

    # Eventos de scanner devem incluir total_files.
    scanner_events = [e for e in events if e.stage == "scanner"]
    assert len(scanner_events) > 0
    completed_events = [e for e in scanner_events if e.status == "completed"]
    assert len(completed_events) == 1
    assert completed_events[0].total_files == 5, (
        f"Esperado total_files=5, obtido {completed_events[0].total_files}"
    )

    # Eventos de pipeline/organizer terminal devem ter completed_files preenchido.
    terminal_events = [
        e for e in events
        if e.stage in ("pipeline", "organizer")
        and e.status in ("organized", "manual_review", "error")
    ]
    if terminal_events:
        for ev in terminal_events:
            assert ev.completed_files is not None, (
                f"Evento {e.stage}/{ev.status} não tem completed_files preenchido"
            )
            assert ev.total_files == 5, (
                f"Evento {ev.stage}/{ev.status} tem total_files={ev.total_files}, esperado 5"
            )

    # Verificar que o progresso avançou (completed_files > 0 em algum evento terminal).
    assert any(ev.completed_files and ev.completed_files > 0 for ev in terminal_events), (
        "Nenhum evento terminal reportou progresso (completed_files > 0)"
    )
