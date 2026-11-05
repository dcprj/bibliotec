"""Orquestrador do pipeline de 5 estágios do BiblioTEC (Item 22).

Conecta: Scanner -> FileCache -> Extrator -> Enriquecedor -> LLM -> Organizer.
Executa sequencialmente por padrão (workers=1) ou paraleliza apenas as etapas
de rede (enriquecimento e classificação LLM) quando workers>1, protegendo o OCR
e a finalização (cache + organizer) com um lock no orquestrador.

Emite PipelineEvent para a UI e calcula ExecutionSummary com verificação do
teto de 20% para revisao_manual/.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

from bibliotec.core.cache import FileCache
from bibliotec.core.config import AppConfig
from bibliotec.core.models import (
    ExecutionSummary,
    ExtractedDocument,
    FileManifestEntry,
    LLMClassificationOutput,
    PipelineEvent,
    ProcessStatus,
)
from bibliotec.core.scanner import scan_directory, ScannedFile
from bibliotec.core.taxonomy import get_taxonomy_version
from bibliotec.storage.organizer import LibraryOrganizer

try:  # Item 16 (enrichers) pertence ao Lince; import tolerante.
    from bibliotec.core.enrichers import enrich_document_metadata  # type: ignore
except Exception:  # pragma: no cover - enriquecedor ainda não implementado pelo Lince

    def enrich_document_metadata(  # type: ignore[no-redef]
        doc: ExtractedDocument, config: AppConfig
    ) -> list:
        return []

from bibliotec.extractors import extract_document_content  # Item 12 (Lince)
from bibliotec.core.llm import (
    ClassificationResult,
    GeminiProvider,
    LLMProvider,
    MockLLMProvider,
)

EventCallback = Callable[[PipelineEvent], None]


def _emit(callback: EventCallback | None, stage: str, source_path: Path,
          status: str, message: str,
          total_files: int | None = None,
          completed_files: int | None = None) -> None:
    if callback is None:
        return
    try:
        callback(PipelineEvent(
            stage=stage,
            source_path=str(source_path),
            status=status,
            message=message,
            total_files=total_files,
            completed_files=completed_count[0] if completed_count else None,
        ))
    except Exception:
        pass


def _classification_to_dict(result: ClassificationResult) -> dict[str, Any]:
    return {
        "grande_area": result.grande_area,
        "area_basica": result.area_basica,
        "tipo": result.tipo,
        "authors": result.authors,
        "title": result.title,
        "subtitle": result.subtitle,
        "year": result.year,
        "confidence_score": result.confidence_score,
        "reasoning": result.reasoning,
    }


def _process_one(
    scanned: ScannedFile,
    config: AppConfig,
    target_dir: Path,
    provider: LLMProvider,
    cache: FileCache,
    organizer: LibraryOrganizer,
    taxonomy_version: str,
    model_name: str,
    emit: EventCallback,
    finalize_lock: threading.RLock,
    completed_count: list[int] | None = None,
    completed_count_lock: threading.Lock | None = None,
    total_files: int | None = None,
) -> FileManifestEntry | None:
    """Processar um único PDF válido através dos 5 estágios.

    O lock (finalize_lock) protege apenas a leitura/escrita do cache e a
    materialização no organizador (etapas que envolvem SQLite e sistema de
    arquivos). Enriquecimento e classificação LLM (chamadas de rede) ocorrem
    fora do lock para permitir paralelismo quando workers > 1.
    """
    source_path = scanned.path
    sha256 = scanned.sha256

    def _emit_terminal(stage: str, status: str, message: str) -> None:
        """Emitir evento terminal de conclusão com incremento thread-safe do contador."""
        comp = None
        if completed_count is not None and completed_count_lock is not None:
            with completed_count_lock:
                completed_count[0] += 1
                comp = completed_count[0]
        _emit(emit, stage, source_path, status, message,
              completed_files=comp, total_files=total_files)

    _emit(emit, "scanner", source_path, "started", "Iniciando processamento",
          completed_files=completed_count[0] if completed_count else None,
          total_files=total_files)

    # Short-circuit: PDF sem assinatura %PDF- (arquivo .pdf corrompido/inválido).
    if not scanned.is_valid_pdf:
        with finalize_lock:
            organizer.add_error(
                source_path,
                sha256,
                "Assinatura %PDF- ausente ou arquivo corrompido",
            )
        _emit_terminal("pipeline", "error", "PDF inválido -> revisao_manual")
        return organizer.entries[-1]

    # --- Cache hit (leitura serializada no lock) ---
    with finalize_lock:
        cached = cache.get(sha256, taxonomy_version, model_name)
    if cached is not None:
        _emit(emit, "cache", source_path, "hit", "Reutilizando classificação em cache",
              completed_files=completed_count[0] if completed_count else None,
              total_files=total_files)
        classification = cached
        used_ocr = bool(cached.get("used_ocr", False))
        confidence = float(classification.get("confidence_score", 0.0))
        if confidence >= config.general.confidence_min:
            filename = _organizer_filename(classification)
            with finalize_lock:
                organizer.add_organized(
                    source_path=source_path,
                    grande_area=classification.get("grande_area", ""),
                    area_basica=classification.get("area_basica", ""),
                    tipo=classification.get("tipo", "Outros"),
                    filename=filename,
                    sha256=sha256,
                    used_ocr=used_ocr,
                    classification=classification,
                )
            _emit_terminal("pipeline", "organized", "Cache hit aprovado")
            return organizer.entries[-1]
        with finalize_lock:
            organizer.add_manual_review(
                source_path=source_path,
                sha256=sha256,
                reason=f"Cache hit abaixo do limiar ({confidence:.2f})",
                used_ocr=used_ocr,
                classification=classification,
            )
        _emit_terminal("pipeline", "manual_review", "Cache hit abaixo do limiar")
        return organizer.entries[-1]

    # --- Stage 2: Extração (inclui OCR seletivo — serializado via lock) ---
    _emit(emit, "extractor", source_path, "started", "Extraindo conteúdo do PDF",
          completed_files=completed_count[0] if completed_count else None, total_files=total_files)
    try:
        # A extração (e o OCR seletivo dentro dela) é protegida pelo lock
        # para evitar concorrência no Docling/PyMuPDF.
        with finalize_lock:
            doc: ExtractedDocument = extract_document_content(source_path, sha256)
    except Exception as exc:
        _emit(emit, "extractor", source_path, "error", f"Falha na extração: {exc}",
              completed_files=completed_count[0] if completed_count else None,
              total_files=total_files)
        with finalize_lock:
            organizer.add_error(source_path, sha256, f"Extração falhou: {exc}")
        _emit_terminal("organizer", "error", f"Extração falhou: {exc}")
        return organizer.entries[-1]

    _emit(emit, "extractor", source_path, "completed",
          f"Texto extraído ({len(doc.sampled_text)} chars, OCR={doc.used_ocr})",
          completed_files=completed_count[0] if completed_count else None, total_files=total_files)

    # --- Stage 3: Enriquecimento acadêmico (rede, FORA do lock) ---
    _emit(emit, "enricher", source_path, "started", "Enriquecendo metadados externos",
          completed_files=completed_count[0] if completed_count else None, total_files=total_files)
    try:
        external_list = enrich_document_metadata(doc, config)
    except Exception as exc:
        _emit(emit, "enricher", source_path, "error", f"Falha no enriquecimento: {exc}",
              completed_files=completed_count[0] if completed_count else None,
              total_files=total_files)
        external_list = []
    external_metadata = external_list[0] if external_list else None
    _emit(emit, "enricher", source_path, "completed",
          f"{len(external_list)} metadado(s) externo(s)",
          completed_files=completed_count[0] if completed_count else None, total_files=total_files)

    # --- Stage 4: Classificação LLM (rede, FORA do lock) ---
    _emit(emit, "llm", source_path, "started", "Classificando via LLM",
          completed_files=completed_count[0] if completed_count else None, total_files=total_files)
    try:
        result: ClassificationResult = provider.classify(
            sampled_text=doc.sampled_text,
            cip_text=doc.cip_text,
            external_metadata=external_metadata,
            used_ocr=doc.used_ocr,
        )
    except Exception as exc:
        _emit(emit, "llm", source_path, "error", f"Falha na classificação LLM: {exc}",
              completed_files=completed_count[0] if completed_count else None,
              total_files=total_files)
        with finalize_lock:
            organizer.add_error(source_path, sha256, f"LLM falhou: {exc}", used_ocr=doc.used_ocr)
        _emit_terminal("organizer", "error", f"LLM falhou: {exc}")
        return organizer.entries[-1]

    classification = _classification_to_dict(result)
    confidence = float(result.confidence_score)
    _emit(emit, "llm", source_path, "completed",
          f"confidence={confidence:.2f} tipo={result.tipo}",
          completed_files=completed_count[0] if completed_count else None, total_files=total_files)

    # --- Stage 5: Materialização + persistência em cache (dentro do lock) ---
    with finalize_lock:
        if confidence >= config.general.confidence_min:
            filename = _organizer_filename(classification)
            organizer.add_organized(
                source_path=source_path,
                grande_area=result.grande_area,
                area_basica=result.area_basica,
                tipo=result.tipo,
                filename=filename,
                sha256=sha256,
                used_ocr=doc.used_ocr,
                classification=classification,
            )
            # Persistir apenas classificações aprovadas no cache.
            cache.put(sha256, taxonomy_version, model_name, classification,
                      doc.used_ocr, confidence_min=config.general.confidence_min)
            _emit_terminal("organizer", "organized",
                  f"Arquivo organizado: {filename}")
        else:
            reason = result.reasoning or f"Confiança {confidence:.2f} abaixo do limiar"
            organizer.add_manual_review(
                source_path=source_path,
                sha256=sha256,
                reason=reason,
                used_ocr=doc.used_ocr,
                classification=classification,
            )
            _emit_terminal("organizer", "manual_review",
                  f"Enviado para revisao_manual ({reason})")

    return organizer.entries[-1]


def _organizer_filename(classification: dict[str, Any]) -> str:
    """Montar o nome de arquivo a partir da classificação (sem depender do namer aqui)."""
    from bibliotec.storage.namer import format_academic_filename

    authors = classification.get("authors") or []
    title = classification.get("title") or ""
    subtitle = classification.get("subtitle") or ""
    year = classification.get("year")
    return format_academic_filename(
        authors=authors, title=title, subtitle=subtitle, year=year,
    )


def run_pipeline(
    source_dir: Path,
    target_dir: Path,
    config: AppConfig,
    *,
    provider: LLMProvider | None = None,
    cache: FileCache | None = None,
    organizer: LibraryOrganizer | None = None,
    workers: int = 1,
    event_callback: EventCallback | None = None,
    use_cache: bool = True,
) -> ExecutionSummary:
    """Executar o pipeline completo de 5 estágios.

    Parâmetros:
        source_dir: diretório de origem com os PDFs brutos.
        target_dir: diretório de destino da biblioteca organizada.
        config: configuração ativa (AppConfig).
        provider: provedor LLM (padrão GeminiProvider se houver API key, senão Mock).
        cache: instância de FileCache (criada se None).
        organizer: instância de LibraryOrganizer (criada se None).
        workers: concorrência para etapas de rede (1 = sequencial).
        event_callback: callback para PipelineEvent.
        use_cache: se False, ignora o cache SQLite (--no-cache).
    """
    emit = event_callback
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)

    taxonomy_version = get_taxonomy_version()
    model_name = config.llm.model
    confidence_min = config.general.confidence_min

    if organizer is None:
        organizer = LibraryOrganizer(
            target_dir,
            file_operation=config.general.file_operation,
            dry_run=False,
        )

    # --- Stage 1: Scanner ---
    _emit(emit, "scanner", source_dir, "started", "Varredura do diretório de origem")
    try:
        scan_result = scan_directory(source_dir, target_dir,
                                     recursive=config.general.recursive)
    except Exception as exc:
        _emit(emit, "scanner", source_dir, "error", str(exc))
        return ExecutionSummary(total_scanned=0, error_count=1,
                                entries=[FileManifestEntry(
                                    source_path=str(source_dir),
                                    destination_path=None,
                                    sha256="",
                                    status=ProcessStatus.ERROR,
                                    error_message=str(exc),
                                )])

    # Registrar não-PDFs ignorados.
    for ignored in scan_result.ignored_non_pdf:
        organizer.add_ignored_non_pdf(ignored.path)
        _emit(emit, "scanner", ignored.path, "ignored", "Não é um PDF válido")

    valid_pdfs = scan_result.valid_pdfs
    _emit(emit, "scanner", source_dir, "completed",
          f"{len(valid_pdfs)} PDF(s) válido(s), {len(scan_result.ignored_non_pdf)} ignorado(s)",
          total_files=len(valid_pdfs))

    if not valid_pdfs:
        return organizer.finalize(total_scanned=len(scan_result.ignored_non_pdf))

    # --- Cache ---
    if cache is None:
        cache = FileCache(enabled=use_cache)

    # --- Provedor LLM ---
    if provider is None:
        api_key = config.api_keys.gemini_api_key
        if api_key:
            provider = GeminiProvider(api_key=api_key, model=model_name)
        else:
            provider = MockLLMProvider()

    # Lock serializando OCR (dentro do extrator) e persistência (cache+organizer).
    finalize_lock = threading.RLock()
    # Contador de arquivos concluídos (para o campo completed_files dos eventos).
    # Usamos list[int] mutável para compartilhar entre threads com lock.
    completed_count = [0]
    completed_count_lock = threading.Lock()

    def _emit_final(event: PipelineEvent) -> None:
        """Incrementar completed_count de forma thread-safe e emitir evento terminal."""
        with completed_count_lock:
            completed_count[0] += 1
            comp = completed_count[0]
        event.completed_files = comp
        event.total_files = total_scanned
        emit(event)

    def process_with_lock(scanned: ScannedFile) -> FileManifestEntry | None:
        return _process_one(
            scanned=scanned,
            config=config,
            target_dir=target_dir,
            provider=provider,
            cache=cache,
            organizer=organizer,
            taxonomy_version=taxonomy_version,
            model_name=model_name,
            emit=emit,
            finalize_lock=finalize_lock,
            completed_count=completed_count,
            completed_count_lock=completed_count_lock,
            total_files=total_scanned,
        )

    total_scanned = len(valid_pdfs)

    if workers > 1:
        # Paralelizar etapas de rede (enriquecimento + LLM); OCR e persistência
        # permanecem serializados pelo finalize_lock.
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = [pool.submit(process_with_lock, s) for s in valid_pdfs]
            for _ in as_completed(futures):
                pass
    else:
        for scanned in valid_pdfs:
            process_with_lock(scanned)

    # Erros do scanner (ex: arquivo não pôde ser lido).
    for err in scan_result.errors:
        organizer.entries.append(FileManifestEntry(
            source_path="", destination_path=None, sha256="",
            status=ProcessStatus.ERROR, error_message=err,
        ))
        organizer._error_count += 1  # type: ignore[attr-defined]

    summary = organizer.finalize(total_scanned=total_scanned)
    _emit(emit, "pipeline", target_dir, "completed",
          f"{summary.organized_count} organizado(s), {summary.manual_review_count} revisão manual")
    return summary
