"""Extração de identificadores (DOI, ISBN) e detecção de Ficha Catalográfica (Item 13).

Localiza candidatos a DOI por expressão regular estrita (limpando pontuação
terminal) e candidatos a ISBN-10/ISBN-13 validando matematicamente o dígito
verificador via ``python-stdnum`` (``stdnum.isbn.is_valid``). Detecta também
páginas de Ficha Catalográfica CIP por marcadores ABNT.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

from stdnum import isbn as _isbn

# Expressão regular estrita para DOI (Item 13).
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b")

# Pontuação terminal que pode ser capturada indevidamente pela regex.
_TERMINAL_PUNCT = ".,;:!?)]}»’\"'"


def _clean_doi(candidate: str) -> str:
    """Remove pontuação terminal de um candidato a DOI."""
    cleaned = candidate
    while cleaned and cleaned[-1] in _TERMINAL_PUNCT:
        cleaned = cleaned[:-1]
    return cleaned


def extract_doi(text: str) -> Optional[str]:
    """Extrair o primeiro DOI válido de ``text``, ou ``None``."""
    for match in DOI_RE.finditer(text):
        candidate = _clean_doi(match.group(0))
        if candidate:
            return candidate
    return None


def extract_isbn(text: str) -> Optional[str]:
    """Extrair o primeiro ISBN-10/ISBN-13 válido de ``text``, ou ``None``.

    A validação do dígito verificador é feita por ``python-stdnum``
    (``stdnum.isbn.is_valid``), rejeitando números arbitrários.
    """
    # Candidatos a ISBN: sequências de dígitos, hífens e espaços, com opcional
    # sufixo 'X' (dígito verificador do ISBN-10).
    for match in re.finditer(r"\b[\d][\d\- ]{8,}[\dXx]\b", text):
        candidate = match.group(0).replace("-", "").replace(" ", "")
        if _isbn.is_valid(candidate):
            return candidate
    return None


def extract_identifiers(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extrair DOI e ISBN de ``text``.

    Retorna uma tupla ``(detected_doi, detected_isbn)``.
    """
    return extract_doi(text), extract_isbn(text)


# Marcadores de Ficha Catalográfica CIP (Item 13).
CIP_MARKERS = (
    "Ficha catalográfica",
    "Dados Internacionais de Catalogação",
    "CDD",
    "CDU",
    "Tomusári",
)


def detect_cip_page(text: str) -> str:
    """Detectar o trecho de Ficha Catalográfica de ``text``.

    Retorna o conteúdo da página/trecho que contiver qualquer marcador CIP, ou
    uma string vazia quando não houver marcador.
    """
    if not text:
        return ""

    # Trabalha linha a linha para isolar o bloco da ficha catalográfica.
    lines = text.splitlines()
    cip_lines: list[str] = []
    in_cip = False

    for line in lines:
        stripped = line.strip()
        if any(marker.lower() in stripped.lower() for marker in CIP_MARKERS):
            in_cip = True
        if in_cip:
            cip_lines.append(line)
            # Encerra o bloco quando encontrar uma linha vazia dupla ou um
            # novo marcador de seção distante (heurística simples).
            if stripped == "" and cip_lines:
                break

    return "\n".join(cip_lines).strip()
