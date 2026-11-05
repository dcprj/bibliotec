"""OCR seletivo de páginas escaneadas via Docling (Item 15).

Recebe o caminho de um PDF escaneado, recorta via PyMuPDF
(``doc.insert_pdf``) as páginas sem texto dentro da janela das 8 primeiras e 2
últimas páginas (máximo de 8 páginas) em um ``io.BytesIO``, encapsula-o em
``DocumentStream(name=f"{path.stem}_slice.pdf", stream=buf)`` e executa uma
instância singleton/lazy do ``DocumentConverter`` do Docling.

Trata exceções ou ausência do modelo com fallback seguro (retorna texto vazio)
sem quebrar o processo.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

# Janela de inspeção para OCR seletivo (Item 15).
_OCR_FIRST_PAGES = 8
_OCR_LAST_PAGES = 2
_OCR_MAX_PAGES = 8

_CONVERTER: Optional[object] = None


def _get_converter():
    """Retornar uma instância singleton/lazy do ``DocumentConverter`` do Docling.

    Retorna ``None`` quando o Docling não estiver disponível ou não puder ser
    instanciado (fallback seguro).
    """
    global _CONVERTER
    if _CONVERTER is not None:
        return _CONVERTER
    try:
        from docling.document_converter import DocumentConverter  # type: ignore

        _CONVERTER = DocumentConverter()
        return _CONVERTER
    except Exception:
        _CONVERTER = None
        return None


def _pages_without_text(doc: fitz.Document) -> list[int]:
    """Listar índices de páginas sem texto selecionável."""
    empty_pages: list[int] = []
    for idx in range(doc.page_count):
        text = doc[idx].get_text() or ""
        if sum(1 for ch in text if ch.isalnum()) == 0:
            empty_pages.append(idx)
    return empty_pages


def _build_slice_pdf(path: Path, pages: list[int]) -> Optional[bytes]:
    """Recortar as ``pages`` indicadas para um novo PDF em memória (bytes).

    Usa ``doc.insert_pdf`` para copiar apenas as páginas selecionadas.
    Retorna ``None`` em caso de falha.
    """
    try:
        src = fitz.open(str(path))
        try:
            out = fitz.open()  # documento vazio
            for idx in pages:
                out.insert_pdf(src, from_page=idx, to_page=idx)
            buf = io.BytesIO()
            out.save(buf, deflate=True)
            return buf.getvalue()
        finally:
            src.close()
            out.close()
    except Exception:
        return None


def ocr_scanned_pages(path: Path) -> str:
    """Executar OCR seletivo nas páginas sem texto do ``path``.

    Retorna o texto extraído pelo Docling, ou uma string vazia quando o Docling
    não estiver disponível, não houver páginas para OCR ou ocorrer qualquer
    exceção (fallback seguro).
    """
    try:
        doc = fitz.open(str(path))
    except Exception:
        return ""

    try:
        total_pages = doc.page_count

        # Janela: 8 primeiras e 2 últimas páginas, sem duplicar.
        first = list(range(0, min(_OCR_FIRST_PAGES, total_pages)))
        last_start = max(total_pages - _OCR_LAST_PAGES, _OCR_FIRST_PAGES)
        last = list(range(last_start, total_pages))
        window = sorted(set(first + last))

        # Apenas páginas sem texto dentro da janela.
        empty_in_window = [idx for idx in window if idx in _pages_without_text(doc)]

        if not empty_in_window:
            return ""

        # Limitar a no máximo 8 páginas.
        selected = empty_in_window[:_OCR_MAX_PAGES]

        pdf_bytes = _build_slice_pdf(path, selected)
        if pdf_bytes is None:
            return ""

        converter = _get_converter()
        if converter is None:
            return ""

        from docling.datamodel.base_models import DocumentStream  # type: ignore

        buf = io.BytesIO(pdf_bytes)
        stream = DocumentStream(name=f"{path.stem}_slice.pdf", stream=buf)

        result = converter.convert(source=stream)
        extracted_text = ""
        if result is not None and hasattr(result, "document"):
            doc_obj = result.document
            if hasattr(doc_obj, "export_to_text"):
                extracted_text = doc_obj.export_to_text() or ""
            elif hasattr(doc_obj, "text"):
                extracted_text = doc_obj.text or ""
        return extracted_text
    except Exception:
        return ""
    finally:
        try:
            doc.close()
        except Exception:
            pass
