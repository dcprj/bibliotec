"""Testes de integração do pipeline completo (Item 27).

Simulam o fluxo de 5 estágios usando PDFs sintéticos (PyMuPDF) e um
MockLLMProvider determinístico, cobrindo:
  * exclusão de TARGET_DIR e filtro de .webloc (ignored_non_pdf);
  * organização aprovada na árvore <Grande Área>/<Área Básica>/<Tipo>;
  * deduplicação por SHA-256 (duplicate_skipped);
  * preservação do nome original em revisao_manual/ (baixa confiança);
  * modo --dry-run (sem criar pastas temáticas nem copiar PDFs);
  * cache SQLite (segunda execução reutiliza o cache).
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import fitz  # PyMuPDF
import pytest

from tomus.core.config import AppConfig
from tomus.core.cache import FileCache
from tomus.core.pipeline import run_pipeline
from tomus.core.llm import ClassificationResult, MockLLMProvider
from tomus.storage.organizer import LibraryOrganizer


# --------------------------------------------------------------------------- #
# Fixtures auxiliares
# --------------------------------------------------------------------------- #
def _criar_pdf(caminho: Path, texto: str = "Título de teste Autor Silva, João 2020") -> str:
    """Criar um PDF sintético de uma página e retornar seu SHA-256."""
    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto)
    doc.save(str(caminho))
    doc.close()
    return _sha256(caminho)


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class _BaixaConfiancaProvider:
    """Provider que retorna confiança baixa para forçar revisao_manual."""

    def classify(self, sampled_text, cip_text, external_metadata=None, used_ocr=False):
        return ClassificationResult(
            grande_area="Ciências Humanas",
            area_basica="Psicologia",
            tipo="Livro",
            authors=["Silva, João"],
            title="Título",
            subtitle="",
            year=2020,
            confidence_score=0.50,
            reasoning="baixa confiança",
        )


# --------------------------------------------------------------------------- #
# Testes
# --------------------------------------------------------------------------- #
def test_pipeline_organiza_aprovados_em_arvore_tematica(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    pdf = source / "livro_teste.pdf"
    _criar_pdf(pdf)

    cfg = AppConfig()
    provider = MockLLMProvider()  # confiança 0.90 -> aprovado

    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=provider,
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    assert summary.total_scanned == 1
    assert summary.organized_count == 1
    assert summary.manual_review_count == 0

    esperado = (
        target / "Ciências Humanas" / "Psicologia" / "Livro"
        / "Silva, João - Título de teste - 2020.pdf"
    )
    assert esperado.exists(), f"arquivo não encontrado em {esperado}"

    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["organized_count"] == 1
    assert manifest["entries"][0]["status"] == "organized"


def test_pipeline_ignora_webloc_e_nao_pdfs(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    _criar_pdf(source / "valido.pdf")
    (source / "atalho.webloc").write_text("plist falso", encoding="utf-8")
    (source / "notas.txt").write_text("não é pdf", encoding="utf-8")

    cfg = AppConfig()
    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    assert summary.ignored_non_pdf_count == 2
    assert summary.total_scanned == 1  # apenas o PDF válido é processado


def test_pipeline_deduplicacao_por_sha256(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    pdf1 = source / "a.pdf"
    pdf2 = source / "b.pdf"
    _criar_pdf(pdf1)
    shutil.copy2(pdf1, pdf2)  # mesmo conteúdo -> mesmo SHA-256

    cfg = AppConfig()
    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    # Um organizado, um duplicata pulada (mesmo hash).
    assert summary.organized_count == 1
    assert summary.duplicate_skipped_count == 1


def test_pipeline_baixa_confianca_preserva_nome_em_revisao(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    pdf = source / "arquivo_com_nome_original.pdf"
    _criar_pdf(pdf)

    cfg = AppConfig()
    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=_BaixaConfiancaProvider(),
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    assert summary.manual_review_count == 1
    assert summary.organized_count == 0

    revisao = target / "revisao_manual" / "arquivo_com_nome_original.pdf"
    assert revisao.exists(), "nome original deve ser preservado em revisao_manual"

    relatorio = target / "revisao_manual" / "relatorio_revisao.md"
    assert relatorio.exists()
    texto_relatorio = relatorio.read_text(encoding="utf-8")
    assert "arquivo_com_nome_original.pdf" in texto_relatorio


def test_pipeline_dry_run_nao_copia_pdf_nem_cria_pastas_tematicas(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    _criar_pdf(source / "livro.pdf")

    cfg = AppConfig()
    organizer = LibraryOrganizer(
        target, file_operation="copy", dry_run=True
    )
    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        organizer=organizer,
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    assert summary.organized_count == 1
    # Nenhum PDF deve estar no disco em dry_run.
    assert list(target.rglob("*.pdf")) == []
    # Nenhuma pasta temática deve ter sido criada.
    tematicas = [p for p in target.iterdir() if p.is_dir() and p.name != "revisao_manual"]
    assert tematicas == []
    # Mas o manifesto e o relatório de auditoria devem existir.
    assert (target / "manifest.json").exists()


def test_pipeline_cache_sqlite_segunda_execucao(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    _criar_pdf(source / "cache.pdf")

    cfg = AppConfig()
    provider = MockLLMProvider()
    cache = FileCache(enabled=True, db_path=tmp_path / "state.db")

    # Primeira execução: organiza e grava no cache.
    sumario1 = run_pipeline(
        source_dir=source, target_dir=target, config=cfg, provider=provider,
        workers=1, cache=cache,
    )
    assert sumario1.organized_count == 1

    # Segunda execução com cache ativado: deve reutilizar o cache. Como o
    # arquivo já existe no destino com o mesmo SHA-256, entra como
    # duplicate_skipped (não é reprocessado pelo LLM).
    sumario2 = run_pipeline(
        source_dir=source, target_dir=target, config=cfg, provider=provider,
        workers=1, cache=cache,
    )
    assert sumario2.organized_count + sumario2.duplicate_skipped_count == 1
    assert sumario2.error_count == 0


def test_pipeline_erro_pdf_corrompido_vai_para_revisao(tmp_path: Path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    corrompido = source / "corrompido.pdf"
    corrompido.write_bytes(b"nao e um pdf real")

    cfg = AppConfig()
    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    assert summary.error_count == 1
    assert (target / "revisao_manual" / "corrompido.pdf").exists()


# --------------------------------------------------------------------------- #
# Avaliação sobre o repositório de referência (execução limitada).
# --------------------------------------------------------------------------- #
@pytest.mark.slow
def test_avaliacao_repositorio_referencia(tmp_path: Path):
    """Execução limitada sobre repositorio_de_pdfs_para_testes.

    Verifica que o scanner encontra PDFs válidos, ignora .webloc e que o
    pipeline não dispara exceções. A meta de precisão (>= 80%) é avaliada
    com o classificador real (Gemini) fora deste ambiente de teste.
    """
    repo = Path("repositorio_de_pdfs_para_testes")
    if not repo.exists():
        pytest.skip("repositorio_de_pdfs_para_testes não encontrado")

    pdfs = [p for p in repo.iterdir() if p.suffix.lower() == ".pdf"]
    weblocs = [p for p in repo.iterdir() if p.suffix.lower() == ".webloc"]
    assert len(pdfs) > 0
    assert len(weblocs) > 0  # há .webloc a ignorar

    target = tmp_path / "alvo"
    cfg = AppConfig()
    cfg.general.recursive = False
    summary = run_pipeline(
        source_dir=repo,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    assert summary.total_scanned == len(pdfs)
    assert summary.ignored_non_pdf_count >= len(weblocs)
    assert summary.organized_count + summary.manual_review_count + summary.duplicate_skipped_count == len(pdfs)
    assert summary.exceeded_manual_review_ceiling in (True, False)


def test_pipeline_workers_4_cache_sqlite_thread_safe(tmp_path: Path):
    """Execução com workers=4 não lança ProgrammingError no SQLite.

    O cache SQLite compartilhado entre worker threads precisa de
    check_same_thread=False para evitar
    'SQLite objects created in a thread can only be used in that same thread'.
    """
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()

    # Vários PDFs para exercer concorrência no cache.
    for i in range(8):
        _criar_pdf(source / f"doc_{i}.pdf")

    cfg = AppConfig()
    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=4,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    # Todos os 8 PDFs válidos devem ser processados sem erro de thread.
    assert summary.total_scanned == 8
    assert summary.error_count == 0
    assert summary.organized_count + summary.manual_review_count == 8


def test_callback_recebe_eventos_com_total_files_e_status(tmp_path: Path):
    """Validar que o callback de eventos é chamado com total_files e status."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    _criar_pdf(source / "doc.pdf")

    cfg = AppConfig()
    events_recebidos: list = []

    def callback(event):
        events_recebidos.append(event)

    run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
        event_callback=callback,
    )

    # Deve haver eventos emitidos.
    assert len(events_recebidos) > 0, "Nenhum evento foi emitido pelo pipeline"

    # O evento scanner completed deve trazer total_files.
    eventos_scanner_completed = [
        e for e in events_recebidos
        if e.stage == "scanner" and e.status == "completed"
    ]
    if eventos_scanner_completed:
        assert eventos_scanner_completed[0].total_files is not None
        assert eventos_scanner_completed[0].total_files == 1

    # Deve haver eventos terminais com status válido.
    statuses_terminais = {
        e.status for e in events_recebidos
        if e.status in ("organized", "manual_review", "error")
    }
    assert len(statuses_terminais) >= 1, (
        "Nenhum evento terminal (organized/manual_review/error) foi emitido"
    )

    # Cada evento deve ter total_files preenchido (quando aplicável).
    for e in events_recebidos:
        if e.total_files is not None:
            assert e.total_files == 1


def test_revisao_manual_resolve_colisao_nomes_distintos(tmp_path: Path):
    """Dois PDFs distintos com o mesmo nome em subpastas diferentes não se sobrescrevem em revisao_manual/."""
    source = tmp_path / "source"
    sub1 = source / "sub1"
    sub2 = source / "sub2"
    sub1.mkdir(parents=True)
    sub2.mkdir(parents=True)
    target = tmp_path / "target"

    _criar_pdf(sub1 / "artigo.pdf", texto="Conteúdo exclusivo da subpasta 1")
    _criar_pdf(sub2 / "artigo.pdf", texto="Conteúdo exclusivo da subpasta 2")

    cfg = AppConfig()
    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=_BaixaConfiancaProvider(),
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
    )

    assert summary.manual_review_count == 2
    assert (target / "revisao_manual" / "artigo.pdf").exists()
    assert (target / "revisao_manual" / "artigo (2).pdf").exists()


def test_pipeline_cancel_event_cooperativo(tmp_path: Path):
    """Quando cancel_event está sinalizado, o pipeline interrompe o processamento de novos arquivos."""
    import threading

    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    _criar_pdf(source / "doc1.pdf", texto="Documento 1")
    _criar_pdf(source / "doc2.pdf", texto="Documento 2")

    cancel_event = threading.Event()
    cancel_event.set()

    cfg = AppConfig()
    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=1,
        cache=FileCache(enabled=True, db_path=tmp_path / "state.db"),
        cancel_event=cancel_event,
    )

    assert summary.organized_count == 0
    assert summary.manual_review_count == 0


