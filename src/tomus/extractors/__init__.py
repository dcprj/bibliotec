"""Extração de conteúdo de PDFs do Tomus (Itens 12 a 15).

Expõe a função coordenadora :func:`extract_document_content` que decide entre
texto nativo (PyMuPDF) e fallback de OCR (Docling) e extrai identificadores
(DOI, ISBN e Ficha Catalográfica CIP).
"""

from __future__ import annotations

from pathlib import Path

from .native_pdf import extract_native_pdf
from .ocr_docling import ocr_scanned_pages
from .identifiers import extract_identifiers, detect_cip_page


def extract_document_content(path: Path, sha256: str) -> "ExtractedDocument":
    """Ler um PDF e retornar um :class:`ExtractedDocument` populado.

    Coordena:
      1. extração nativa via PyMuPDF (metadados + texto das primeiras e últimas
         páginas) e decisão de necessidade de OCR;
      2. fallback de OCR seletivo via Docling quando o documento é escaneado;
      3. extração de identificadores (DOI, ISBN, detecção de CIP) sobre o texto
         amostrado.
    """
    # Importação lazy para evitar importação circular com tomus.core
    # (que importa pipeline -> extractors).
    from tomus.core.models import ExtractedDocument  # noqa: PLC0415

    native = extract_native_pdf(path)

    text = native["sampled_text"]
    used_ocr = False

    if native["needs_ocr"]:
        ocr_text = ocr_scanned_pages(path)
        if ocr_text:
            text = ocr_text
            used_ocr = True

    sampled_text = text or ""
    cip_text = ""
    detected_doi = None
    detected_isbn = None

    if sampled_text:
        cip_text = detect_cip_page(sampled_text)
        doi, isbn_val = extract_identifiers(sampled_text)
        detected_doi = doi
        detected_isbn = isbn_val

    return ExtractedDocument(
        source_path=path,
        sha256=sha256,
        file_size_bytes=native["file_size_bytes"],
        total_pages=native["total_pages"],
        used_ocr=used_ocr,
        native_metadata=native["metadata"],
        sampled_text=sampled_text,
        cip_text=cip_text,
        detected_doi=detected_doi,
        detected_isbn=detected_isbn,
    )
