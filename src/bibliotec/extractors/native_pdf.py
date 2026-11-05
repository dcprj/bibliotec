"""Extração nativa de PDF via PyMuPDF (Item 14).

Lê metadados internos e extrai texto das 10 primeiras e 5 últimas páginas (sem
duplicar páginas em PDFs curtos), avaliando caracteres alfanuméricos por página
e sinalizando necessidade de OCR quando mais da metade das páginas inspecionadas
tiver menos de 30 caracteres alfanuméricos úteis.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

# Limiares (Item 14).
_ALPHANUM_THRESHOLD = 30
_FIRST_PAGES = 10
_LAST_PAGES = 5


def _alphanum_count(text: str) -> int:
    """Contar caracteres alfanuméricos úteis de uma página."""
    return sum(1 for ch in text if ch.isalnum())


def extract_native_pdf(path: Path) -> dict[str, Any]:
    """Extrair metadados e texto amostrado de um PDF nativo.

    Retorna um dicionário com:
      - ``metadata``: metadados internos do PDF (dict);
      - ``total_pages``: número total de páginas;
      - ``sampled_text``: texto das 10 primeiras e 5 últimas páginas;
      - ``file_size_bytes``: tamanho do arquivo em bytes;
      - ``needs_ocr``: True quando mais da metade das páginas inspecionadas tem
        menos de 30 caracteres alfanuméricos.
    """
    file_size_bytes = path.stat().st_size if path.exists() else 0

    doc = fitz.open(str(path))
    try:
        metadata: dict[str, Any] = dict(doc.metadata or {})
        total_pages = doc.page_count

        # Páginas a inspecionar: 10 primeiras e 5 últimas, sem duplicar em
        # documentos curtos.
        first = list(range(0, min(_FIRST_PAGES, total_pages)))
        last_start = max(total_pages - _LAST_PAGES, _FIRST_PAGES)
        last = list(range(last_start, total_pages))
        inspected = sorted(set(first + last))

        parts: list[str] = []
        low_count_pages = 0

        for idx in inspected:
            page = doc[idx]
            page_text = page.get_text() or ""
            parts.append(page_text)
            if _alphanum_count(page_text) < _ALPHANUM_THRESHOLD:
                low_count_pages += 1

        sampled_text = "\n".join(parts)

        needs_ocr = False
        if inspected:
            needs_ocr = low_count_pages > len(inspected) / 2

        return {
            "metadata": metadata,
            "total_pages": total_pages,
            "sampled_text": sampled_text,
            "file_size_bytes": file_size_bytes,
            "needs_ocr": needs_ocr,
            "inspected_pages": inspected,
        }
    finally:
        doc.close()
