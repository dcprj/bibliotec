"""Scanner de diretório de origem do Tomus (Stage 1).

Resolve source_dir e target_dir, rejeita source_dir == target_dir, exclui a
subárvore de target_dir, executa varredura recursiva ou plana, ignora ocultos
e não-PDFs (ignorados como ignored_non_pdf), valida a assinatura %PDF- nos
primeiros 1024 bytes e calcula SHA-256 em blocos de 64 KB.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Assinatura binária PDF nos primeiros bytes
PDF_SIGNATURE = b"%PDF-"
# Quantidade de bytes lidos para verificar a assinatura
PDF_SIGNATURE_BYTES = 1024
# Tamanho do bloco para leitura do SHA-256 (64 KB)
HASH_BLOCK_SIZE = 64 * 1024


@dataclass
class ScannedFile:
    """Resultado da varredura de um único arquivo."""

    path: Path
    sha256: str
    file_size_bytes: int
    is_valid_pdf: bool
    is_hidden: bool
    is_ignored_non_pdf: bool


@dataclass
class ScanResult:
    """Resultado completo da varredura do diretório de origem."""

    source_dir: Path
    target_dir: Path
    valid_pdfs: list[ScannedFile]
    ignored_non_pdf: list[ScannedFile]
    errors: list[str]


def _is_hidden(path: Path, source_dir: Path | None = None) -> bool:
    """Verificar se um arquivo ou diretório é oculto (começa com ponto).

    Quando source_dir é fornecido, considera apenas as partes relativas a ele,
    evitando ignorar arquivos por causa de pastas ocultas acima de source_dir
    no caminho absoluto.
    """
    if source_dir is not None:
        try:
            partes = path.relative_to(source_dir).parts
        except ValueError:
            partes = path.parts
    else:
        partes = path.parts
    return any(part.startswith(".") for part in partes)


def _compute_sha256(path: Path) -> str:
    """Calcular SHA-256 do arquivo em blocos de 64 KB."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(HASH_BLOCK_SIZE), b""):
            h.update(chunk)
    return h.hexdigest()


def _validate_pdf_signature(path: Path) -> bool:
    """Validar a assinatura %PDF- nos primeiros 1024 bytes do arquivo."""
    try:
        with open(path, "rb") as fh:
            header = fh.read(PDF_SIGNATURE_BYTES)
        return PDF_SIGNATURE in header
    except OSError:
        return False


def _is_within(path: Path, parent: Path) -> bool:
    """Verificar se path está contido dentro de parent (subárvore)."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def scan_directory(
    source_dir: Path,
    target_dir: Path,
    recursive: bool = True,
) -> ScanResult:
    """Varredura do diretório de origem.

    Resolve caminhos absolutos, rejeita source_dir == target_dir, exclui a
    subárvore de target_dir, filtra ocultos e não-PDFs, valida a assinatura
    PDF e calcula SHA-256.
    """
    source_dir = source_dir.resolve()
    target_dir = target_dir.resolve()

    if source_dir == target_dir:
        raise ValueError("source_dir e target_dir não podem ser o mesmo diretório")

    if not source_dir.exists():
        raise FileNotFoundError(f"Diretório de origem não encontrado: {source_dir}")

    valid_pdfs: list[ScannedFile] = []
    ignored_non_pdf: list[ScannedFile] = []
    errors: list[str] = []

    # Iterar sobre entradas do diretório de origem
    if recursive:
        iterator = source_dir.rglob("*")
    else:
        iterator = source_dir.iterdir()

    for entry in iterator:
        # Excluir diretórios e arquivos ocultos
        if _is_hidden(entry, source_dir):
            continue

        # Excluir a subárvore de target_dir caso esteja dentro de source_dir
        if target_dir != source_dir and _is_within(entry, target_dir):
            continue

        # Apenas arquivos regulares
        if not entry.is_file():
            continue

        # Filtrar extensão .pdf
        if entry.suffix.lower() != ".pdf":
            ignored_non_pdf.append(
                ScannedFile(
                    path=entry,
                    sha256="",
                    file_size_bytes=entry.stat().st_size,
                    is_valid_pdf=False,
                    is_hidden=_is_hidden(entry, source_dir),
                    is_ignored_non_pdf=True,
                )
            )
            continue

        # Calcular SHA-256 e validar assinatura
        try:
            file_size = entry.stat().st_size
            sha256 = _compute_sha256(entry)
            is_valid_pdf = _validate_pdf_signature(entry)
        except OSError as exc:
            errors.append(f"Erro ao processar {entry}: {exc}")
            continue

        valid_pdfs.append(
            ScannedFile(
                path=entry,
                sha256=sha256,
                file_size_bytes=file_size,
                is_valid_pdf=is_valid_pdf,
                is_hidden=False,
                is_ignored_non_pdf=False,
            )
        )

    return ScanResult(
        source_dir=source_dir,
        target_dir=target_dir,
        valid_pdfs=valid_pdfs,
        ignored_non_pdf=ignored_non_pdf,
        errors=errors,
    )
