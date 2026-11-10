"""Execução assíncrona do pipeline e serviço de triagem manual (Seção 5.4 item 1).

Implementa:
* ``PipelineWorker(QThread)`` — executa ``run_pipeline`` em background sem
  bloquear a Event Loop do Qt, comunicando-se via sinais Qt thread-safe
  (``event_received``, ``pipeline_finished``, ``pipeline_failed``) com
  cancelamento cooperativo seguro via ``cancel_event.set()``.
* ``ManualTriageService`` — aprova e materializa um item de revisão manual na
  árvore temática CAPES/CNPq, gera o ``.md`` companheiro ABNT, persiste no
  cache SQLite (confidence 1.0, modelo ``manual_human_review``) e atualiza
  ``manifest.json`` + ``relatorio_revisao.md``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from tomus.core.cache import FileCache
from tomus.core.config import AppConfig
from tomus.core.models import (
    DocumentType,
    ExecutionSummary,
    FileManifestEntry,
    PipelineEvent,
    ProcessStatus,
)
from tomus.core.pipeline import run_pipeline
from tomus.core.taxonomy import get_taxonomy_version, validate_or_repair_pair
from tomus.storage.companion import generate_companion_markdown
from tomus.storage.namer import format_academic_filename
from tomus.storage.organizer import (
    DUPLICATAS_DIR,
    MANIFEST_FILENAME,
    RELATORIO_FILENAME,
    REVISAO_DIR,
)

__all__ = ["PipelineWorker", "ManualTriageService"]


# --------------------------------------------------------------------------- #
# PipelineWorker — execução assíncrona do pipeline de 5 estágios
# --------------------------------------------------------------------------- #


class PipelineWorker(QThread):
    """Executa ``run_pipeline`` em background sem bloquear a UI.

    Os sinais são emitidos com ``Qt.ConnectionType.QueuedConnection``
    (padrão para sinais entre threads no PySide6), garantindo comunicação
    thread-safe entre a worker thread e a thread principal da GUI.
    """

    event_received = Signal(object)          # PipelineEvent
    pipeline_finished = Signal(object, bool)  # (ExecutionSummary, was_cancelled)
    pipeline_failed = Signal(str)            # mensagem de erro inesperado

    def __init__(
        self,
        source_dir: Path | str,
        target_dir: Path | str,
        config: AppConfig,
        *,
        dry_run: bool = False,
        use_cache: bool = True,
        workers: int = 1,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.config = config
        self.dry_run = dry_run
        self.use_cache = use_cache
        self.workers = workers
        self.cancel_event = threading.Event()

    def request_cancel(self) -> None:
        """Acionar cancelamento cooperativo seguro no orquestrador."""
        self.cancel_event.set()

    def run(self) -> None:
        try:
            summary = run_pipeline(
                source_dir=self.source_dir,
                target_dir=self.target_dir,
                config=self.config,
                workers=self.workers,
                event_callback=self._handle_pipeline_event,
                use_cache=self.use_cache,
                dry_run=self.dry_run,
                cancel_event=self.cancel_event,
            )
            self.pipeline_finished.emit(summary, self.cancel_event.is_set())
        except Exception as exc:  # pragma: no cover - erro inesperado do orquestrador
            self.pipeline_failed.emit(str(exc))

    def _handle_pipeline_event(self, event: PipelineEvent) -> None:
        self.event_received.emit(event)


# --------------------------------------------------------------------------- #
# ManualTriageService — triagem manual assistida
# --------------------------------------------------------------------------- #


class ManualTriageService(QObject):
    """Aprovar e materializar um item de revisão manual na tomusa temática.

    O serviço move/copia o arquivo de ``revisao_manual/`` para a pasta temática
    correta ``<Grande Área>/<Área Básica>/<Tipo>/``, gera o ``.md`` companheiro
    ABNT NBR 6023, grava a classificação revisada no cache SQLite
    (``confidence_score = 1.0``, ``model_name = "manual_human_review"``) e
    atualiza ``manifest.json`` e ``relatorio_revisao.md``.
    """

    triage_completed = Signal(object)  # FileManifestEntry atualizado (organizado)

    def __init__(
        self,
        target_dir: Path | str,
        config: AppConfig,
        cache: FileCache | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.target_dir = Path(target_dir).resolve()
        self.config = config
        self.cache = cache or FileCache(enabled=True)

    # ------------------------------------------------------------------ #
    # API pública
    # ------------------------------------------------------------------ #

    def approve_and_materialize(
        self,
        entry: FileManifestEntry,
        grande_area: str,
        area_basica: str,
        tipo: str,
        title: str,
        subtitle: str,
        authors: list[str],
        year: int | None,
    ) -> FileManifestEntry:
        """Aprovar classificação manual e materializar o item na tomusa."""
        # Validar/reparar o par CAPES/CNPq.
        par = validate_or_repair_pair(grande_area, area_basica)
        if par is None:
            raise ValueError(
                f"Par CAPES/CNPq inválido: {grande_area} / {area_basica}"
            )
        grande_area, area_basica = par

        # Nome padronizado do arquivo de destino.
        filename = format_academic_filename(
            authors=authors,
            title=title,
            subtitle=subtitle,
            year=year,
        )

        sha256 = entry.sha256 or self._compute_sha256(Path(entry.source_path))

        classification: dict[str, Any] = {
            "grande_area": grande_area,
            "area_basica": area_basica,
            "tipo": tipo,
            "authors": authors,
            "title": title,
            "subtitle": subtitle,
            "year": year,
            "confidence_score": 1.0,
            "reasoning": "manual_human_review",
        }

        source_path = Path(entry.source_path)

        # Destino na árvore temática com resolução de colisão.
        dest_dir = self.target_dir / grande_area / area_basica / tipo
        dest_dir.mkdir(parents=True, exist_ok=True)
        nome_final, _colisao = _resolve_collision(
            dest_dir, filename, source_path, src_sha256=sha256
        )
        dest_path = dest_dir / nome_final

        # Copiar o PDF (modo seguro: cópia, nunca remoção do original por aqui).
        shutil.copy2(source_path, dest_path)

        # Arquivo companheiro .md ABNT NBR 6023.
        companion_path = dest_path.with_suffix(".md")
        companion_path.write_text(
            generate_companion_markdown(
                destination_path=companion_path,
                source_path=source_path,
                sha256=sha256,
                classification=classification,
                used_ocr=bool(entry.used_ocr),
            ),
            encoding="utf-8",
        )

        # Persistir no cache SQLite (confidence 1.0, revisão humana).
        taxonomy_version = get_taxonomy_version()
        self.cache.put(
            sha256,
            taxonomy_version,
            "manual_human_review",
            classification,
            bool(entry.used_ocr),
            confidence_min=0.0,
        )

        # Atualizar manifest.json e relatorio_revisao.md.
        self._update_manifest_and_relatorio(
            source_path=source_path,
            dest_path=dest_path,
            sha256=sha256,
            classification=classification,
            used_ocr=bool(entry.used_ocr),
        )

        entry_out = FileManifestEntry(
            source_path=str(source_path),
            destination_path=str(dest_path),
            sha256=sha256,
            status=ProcessStatus.ORGANIZED,
            used_ocr=bool(entry.used_ocr),
            classification=classification,
        )
        self.triage_completed.emit(entry_out)
        return entry_out

    # ------------------------------------------------------------------ #
    # Helpers internos
    # ------------------------------------------------------------------ #

    @staticmethod
    def _compute_sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(64 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def _update_manifest_and_relatorio(
        self,
        *,
        source_path: Path,
        dest_path: Path,
        sha256: str,
        classification: dict[str, Any],
        used_ocr: bool,
    ) -> None:
        """Atualizar manifest.json e relatorio_revisao.md após triagem manual."""
        manifest_path = self.target_dir / MANIFEST_FILENAME

        # Carregar entradas existentes (se houver).
        entries: list[dict[str, Any]] = []
        generated_at = ""
        totals = {
            "total_scanned": 0,
            "organized_count": 0,
            "manual_review_count": 0,
            "duplicate_skipped_count": 0,
            "ignored_non_pdf_count": 0,
            "error_count": 0,
        }
        if manifest_path.exists():
            try:
                data = json.loads(manifest_path.read_text(encoding="utf-8"))
                entries = data.get("entries", [])
                generated_at = data.get("generated_at", "")
                for key in totals:
                    totals[key] = data.get(key, 0)
            except (json.JSONDecodeError, OSError):
                entries = []

        # Remover entrada antiga deste source_path (se já estava listada).
        entries = [e for e in entries if e.get("source_path") != str(source_path)]

        # Adicionar a nova entrada organizada.
        new_entry: dict[str, Any] = {
            "source_path": str(source_path),
            "destination_path": str(dest_path),
            "sha256": sha256,
            "status": ProcessStatus.ORGANIZED.value,
            "used_ocr": used_ocr,
            "classification": classification,
        }
        entries.append(new_entry)

        # Recalcular contadores.
        organized = sum(1 for e in entries if e.get("status") == ProcessStatus.ORGANIZED.value)
        manual = sum(1 for e in entries if e.get("status") == ProcessStatus.MANUAL_REVIEW.value)
        duplicate = sum(1 for e in entries if e.get("status") == ProcessStatus.DUPLICATE_SKIPPED.value)
        ignored = sum(1 for e in entries if e.get("status") == ProcessStatus.IGNORED_NON_PDF.value)
        errors = sum(1 for e in entries if e.get("status") == ProcessStatus.ERROR.value)
        total = len(entries)
        manual_ratio = (manual / total) if total else 0.0

        payload = {
            "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
            "total_scanned": total,
            "organized_count": organized,
            "manual_review_count": manual,
            "duplicate_skipped_count": duplicate,
            "ignored_non_pdf_count": ignored,
            "error_count": errors,
            "manual_review_ratio": round(manual_ratio, 4),
            "exceeded_manual_review_ceiling": manual_ratio > 0.20,
            "entries": entries,
        }
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Atualizar relatorio_revisao.md (remover este item dos pendentes).
        relatorio_path = self.target_dir / REVISAO_DIR / RELATORIO_FILENAME
        if relatorio_path.exists():
            lines = relatorio_path.read_text(encoding="utf-8").splitlines()
            # Manter apenas linhas que não referenciam este source_path como pendente.
            filtered: list[str] = []
            skip_next = False
            for line in lines:
                if skip_next:
                    skip_next = False
                    continue
                if str(source_path) in line and "→" in line:
                    # Esta linha é uma entrada pendente; pular ela e a linha de motivo.
                    skip_next = True
                    continue
                filtered.append(line)
            relatorio_path.write_text("\n".join(filtered), encoding="utf-8")

    def _resolve_collision(
        self,
        dest_dir: Path,
        filename: str,
        src_path: Path,
        *,
        src_sha256: str | None = None,
    ) -> tuple[str, str]:
        """Resolver colisão de nome no destino (mesma lógica do organizer)."""
        from tomus.storage.organizer import _resolve_collision

        return _resolve_collision(
            dest_dir, filename, src_path, None, src_sha256=src_sha256
        )
