"""Materializador de diretórios da biblioteca (Item 21).

Organiza arquivos aprovados em
<TARGET_DIR>/<Grande Área>/<Área Básica>/<Tipo>/<nome_formatado>.pdf e
arquivos de baixa confiança/erro em
<TARGET_DIR>/revisao_manual/<source_path.name> (preservando o nome original).

Suporta cópia (shutil.copy2) ou movimentação segura, modo dry_run (sem criar
pastas temáticas nem copiar/mover PDFs), resolução de colisão por SHA-256
(duplicate_skipped ou sufixo ' (2).pdf') e gravação de manifest.json e
revisao_manual/relatorio_revisao.md.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bibliotec.core.models import (
    ExecutionSummary,
    FileManifestEntry,
    ProcessStatus,
)

from bibliotec.storage.companion import generate_companion_markdown

REVISAO_DIR = "revisao_manual"
MANIFEST_FILENAME = "manifest.json"
RELATORIO_FILENAME = "relatorio_revisao.md"
COLLISION_SUFFIX = " (2)"


def _compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _destinations_equal(src: Path, dst: Path) -> bool:
    """Verificar se dois caminhos apontam para o mesmo arquivo."""
    try:
        return src.resolve() == dst.resolve()
    except OSError:
        return False


def _resolve_collision(
    dest_dir: Path,
    filename: str,
    src_path: Path,
    planned_destinations: dict[Path, str] | None = None,
) -> tuple[str, str]:
    """Resolver colisão de nome no destino.

    Detecta colisões tanto contra arquivos existentes no disco quanto contra
    arquivos já planejados na mesma execução (``planned_destinations``),
    permitindo funcionar corretamente em modo --dry-run (nenhum arquivo é
    escrito no disco).

    Retorna (nome_final, status_extra) onde status_extra é:
      - 'duplicate_skipped' se já existir arquivo com mesmo SHA-256;
      - nome com sufixo incremental ' (2).pdf' se o conteúdo for distinto.
    """
    dest_path = dest_dir / filename

    # Verificar contra arquivos já planejados nesta execução (dry-run).
    if planned_destinations is not None and dest_path in planned_destinations:
        planned_hash = planned_destinations[dest_path]
        src_hash = _compute_sha256(src_path)
        if planned_hash == src_hash:
            return filename, ProcessStatus.DUPLICATE_SKIPPED.value

    if not dest_path.exists():
        return filename, ""

    try:
        dst_hash = _compute_sha256(dest_path)
    except OSError:
        dst_hash = ""
    src_hash = _compute_sha256(src_path)

    if dst_hash == src_hash:
        return filename, ProcessStatus.DUPLICATE_SKIPPED.value

    # Conteúdo distinto: sufixo incremental ' (2).pdf', ' (3).pdf', etc.
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 2
    while True:
        candidate = f"{stem} ({counter}){suffix}"
        candidate_path = dest_dir / candidate
        # Verificar tanto no disco quanto nos planejados.
        disk_exists = candidate_path.exists()
        planned_hash = None
        if planned_destinations is not None:
            planned_hash = planned_destinations.get(candidate_path)
        if not disk_exists and planned_hash is None:
            return candidate, ""
        # Se já existe no disco ou foi planejado, verificar se é duplicata.
        candidate_hash = None
        if disk_exists:
            try:
                candidate_hash = _compute_sha256(candidate_path)
            except OSError:
                pass
        if candidate_hash is None and planned_hash is not None:
            candidate_hash = planned_hash
        if candidate_hash == src_hash:
            return candidate, ProcessStatus.DUPLICATE_SKIPPED.value
        counter += 1


class LibraryOrganizer:
    """Materializar a organização física dos arquivos classificados."""

    def __init__(
        self,
        target_dir: Path,
        *,
        file_operation: str = "copy",
        dry_run: bool = False,
    ) -> None:
        self.target_dir = Path(target_dir).resolve()
        self.file_operation = file_operation
        self.dry_run = dry_run
        self.entries: list[FileManifestEntry] = []
        self._organized_count = 0
        self._manual_review_count = 0
        self._duplicate_skipped_count = 0
        self._ignored_non_pdf_count = 0
        self._error_count = 0
        # Mapeia destination_path -> sha256 para detectar colisões/duplicatas
        # na mesma execução, inclusive em --dry-run (sem arquivos no disco).
        self._planned_destinations: dict[Path, str] = {}

    # ------------------------------------------------------------------ #
    # Operações de sistema de arquivos
    # ------------------------------------------------------------------ #
    def _materialize(
        self,
        source_path: Path,
        destination_path: Path,
        sha256: str,
        status: ProcessStatus,
    ) -> bool:
        """Copiar/mover o arquivo para o destino (ou apenas registrar no dry-run).

        Retorna True se a operação foi realizada (ou simulada) com sucesso.
        """
        if self.dry_run:
            # No dry-run não cria pastas temáticas nem copia/move PDFs.
            return True

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        if _destinations_equal(source_path, destination_path):
            return True

        if self.file_operation == "move":
            # Movimentação segura: copiar e, só então, remover o original.
            shutil.copy2(source_path, destination_path)
            try:
                source_path.unlink()
            except OSError:
                pass
        else:
            shutil.copy2(source_path, destination_path)
        return True

    def _materialize_dry(self, source_path: Path, destination_path: Path) -> bool:
        """Registro sem cópia (usado para duplicatas exatas puladas)."""
        if self.dry_run:
            return True
        # Duplicata exata: nada a gravar, o arquivo já existe no destino.
        return True

    # ------------------------------------------------------------------ #
    # Entradas de manifesto
    # ------------------------------------------------------------------ #
    def add_organized(
        self,
        source_path: Path,
        grande_area: str,
        area_basica: str,
        tipo: str,
        filename: str,
        sha256: str,
        used_ocr: bool = False,
        classification: dict[str, Any] | None = None,
        duplicate: bool = False,
    ) -> FileManifestEntry:
        """Registrar um arquivo organizado na árvore temática."""
        dest_dir = self.target_dir / grande_area / area_basica / tipo
        nome_final, colisao_status = _resolve_collision(
            dest_dir, filename, source_path, self._planned_destinations
        )
        destination_path = dest_dir / nome_final

        # Registrar o destino planejado (inclui em dry-run) para detecção de
        # colisões contra arquivos da mesma execução.
        self._planned_destinations[destination_path] = sha256

        if colisao_status == ProcessStatus.DUPLICATE_SKIPPED.value:
            status = ProcessStatus.DUPLICATE_SKIPPED
            self._duplicate_skipped_count += 1
            # Não copiar/mover: duplicata exata já está no destino.
            self._materialize_dry(source_path, destination_path)
        else:
            status = ProcessStatus.ORGANIZED
            self._organized_count += 1
            self._materialize(source_path, destination_path, sha256, status)
            # Gerar arquivo companheiro (.md) apenas quando não for dry_run.
            if not self.dry_run and classification:
                companion_path = destination_path.with_suffix(".md")
                companion_content = generate_companion_markdown(
                    destination_path=companion_path,
                    source_path=source_path,
                    sha256=sha256,
                    classification=classification,
                    used_ocr=used_ocr,
                )
                companion_path.write_text(
                    companion_content, encoding="utf-8"
                )

        entry = FileManifestEntry(
            source_path=str(source_path),
            destination_path=str(destination_path),
            sha256=sha256,
            status=status,
            used_ocr=used_ocr,
            classification=classification,
        )
        self.entries.append(entry)
        return entry

    def add_manual_review(
        self,
        source_path: Path,
        sha256: str,
        reason: str,
        used_ocr: bool = False,
        classification: dict[str, Any] | None = None,
    ) -> FileManifestEntry:
        """Registrar arquivo enviado para revisao_manual preservando o nome original."""
        destination_path = self.target_dir / REVISAO_DIR / source_path.name
        entry = FileManifestEntry(
            source_path=str(source_path),
            destination_path=str(destination_path),
            sha256=sha256,
            status=ProcessStatus.MANUAL_REVIEW,
            used_ocr=used_ocr,
            classification=classification,
            error_message=reason,
        )
        self.entries.append(entry)
        self._manual_review_count += 1
        self._materialize(source_path, destination_path, sha256, ProcessStatus.MANUAL_REVIEW)
        return entry

    def add_error(
        self,
        source_path: Path,
        sha256: str,
        error_message: str,
        used_ocr: bool = False,
    ) -> FileManifestEntry:
        """Registrar um erro (arquivo corrompido etc.) em revisao_manual."""
        destination_path = self.target_dir / REVISAO_DIR / source_path.name
        entry = FileManifestEntry(
            source_path=str(source_path),
            destination_path=str(destination_path),
            sha256=sha256,
            status=ProcessStatus.ERROR,
            used_ocr=used_ocr,
            error_message=error_message,
        )
        self.entries.append(entry)
        self._error_count += 1
        self._materialize(source_path, destination_path, sha256, ProcessStatus.ERROR)
        return entry

    def add_ignored_non_pdf(self, source_path: Path) -> FileManifestEntry:
        """Registrar arquivo não-PDF ignorado."""
        entry = FileManifestEntry(
            source_path=str(source_path),
            destination_path=None,
            sha256="",
            status=ProcessStatus.IGNORED_NON_PDF,
        )
        self.entries.append(entry)
        self._ignored_non_pdf_count += 1
        return entry

    # ------------------------------------------------------------------ #
    # Manifesto e relatório
    # ------------------------------------------------------------------ #
    def build_summary(self, total_scanned: int) -> ExecutionSummary:
        manual_review_ratio = (
            self._manual_review_count / total_scanned if total_scanned else 0.0
        )
        return ExecutionSummary(
            total_scanned=total_scanned,
            organized_count=self._organized_count,
            manual_review_count=self._manual_review_count,
            duplicate_skipped_count=self._duplicate_skipped_count,
            ignored_non_pdf_count=self._ignored_non_pdf_count,
            error_count=self._error_count,
            manual_review_ratio=manual_review_ratio,
            exceeded_manual_review_ceiling=manual_review_ratio > 0.20,
            entries=list(self.entries),
        )

    def write_manifest(self, summary: ExecutionSummary) -> Path:
        """Gravar manifest.json no diretório de destino."""
        manifest_path = self.target_dir / MANIFEST_FILENAME
        if not self.dry_run:
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_scanned": summary.total_scanned,
            "organized_count": summary.organized_count,
            "manual_review_count": summary.manual_review_count,
            "duplicate_skipped_count": summary.duplicate_skipped_count,
            "ignored_non_pdf_count": summary.ignored_non_pdf_count,
            "error_count": summary.error_count,
            "manual_review_ratio": round(summary.manual_review_ratio, 4),
            "exceeded_manual_review_ceiling": summary.exceeded_manual_review_ceiling,
            "entries": [
                entry.model_dump(mode="json") for entry in summary.entries
            ],
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return manifest_path

    def write_relatorio_revisao(self, summary: ExecutionSummary) -> Path:
        """Gravar revisao_manual/relatorio_revisao.md com as pendências."""
        relatorio_dir = self.target_dir / REVISAO_DIR
        relatorio_path = relatorio_dir / RELATORIO_FILENAME
        relatorio_dir.mkdir(parents=True, exist_ok=True)

        pendentes = [
            e
            for e in summary.entries
            if e.status
            in (ProcessStatus.MANUAL_REVIEW, ProcessStatus.ERROR)
        ]

        lines: list[str] = []
        lines.append("# Relatório de Revisão Manual")
        lines.append("")
        lines.append(
            f"Gerado em: {datetime.now(timezone.utc).isoformat()}\n"
        )
        lines.append(f"Total de arquivos pendentes: {len(pendentes)}\n")
        if summary.exceeded_manual_review_ceiling:
            lines.append(
                f"⚠️  ATENÇÃO: taxa de revisão manual "
                f"({summary.manual_review_ratio:.1%}) excede o teto de 20%."
            )
        lines.append("")

        if not pendentes:
            lines.append("Nenhum arquivo requer revisão manual.\n")
        else:
            lines.append("## Arquivos para revisão\n")
            for entry in pendentes:
                motivo = entry.error_message or "confiança abaixo do limiar"
                lines.append(f"- `{entry.source_path}` → `{entry.destination_path}`")
                lines.append(f"  - Status: {entry.status.value}")
                lines.append(f"  - Motivo: {motivo}")
                lines.append("")

        relatorio_path.write_text("\n".join(lines), encoding="utf-8")
        return relatorio_path

    def finalize(self, total_scanned: int) -> ExecutionSummary:
        """Montar o resumo e gravar manifest.json e relatório de revisão."""
        summary = self.build_summary(total_scanned)
        self.write_manifest(summary)
        self.write_relatorio_revisao(summary)
        return summary
