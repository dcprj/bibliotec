"""Testes de taxonomia e identificadores (Item 26).

Validam a integridade de taxonomy_capes.json, o reparo automático de
Grande Área, a extração de DOI por regex, a validação de ISBN via
stdnum.isbn.is_valid (rejeitando falsos números como 531581939) e a
detecção de Ficha Catalográfica.
"""

from __future__ import annotations

from tomus.core.taxonomy import (
    get_taxonomy_version,
    get_grandes_areas,
    get_areas_basicas,
    validate_or_repair_pair,
)
from tomus.extractors.identifiers import (
    extract_doi,
    extract_isbn,
    detect_cip_page,
)


def test_taxonomy_version():
    assert get_taxonomy_version() == "capes-cnpq-v1"


def test_taxonomy_has_nove_grandes_areas():
    grandes = get_grandes_areas()
    assert len(grandes) == 9
    assert "Ciências Humanas" in grandes
    assert "Ciências Exatas e da Terra" in grandes


def test_cada_grande_area_tem_areas_basicas_nao_vazias():
    for grande in get_grandes_areas():
        basicas = get_areas_basicas(grande)
        assert len(basicas) > 0, f"{grande} sem áreas básicas"
        for basica in basicas:
            assert "/" not in basica


def test_validate_or_repair_pair_consistente():
    assert validate_or_repair_pair("Ciências Humanas", "Psicologia") == (
        "Ciências Humanas",
        "Psicologia",
    )
    assert validate_or_repair_pair("Engenharias", "Engenharia Civil") == (
        "Engenharias",
        "Engenharia Civil",
    )


def test_validate_or_repair_pair_repara_grande_area():
    # Psicologia pertence a Ciências Humanas; grande_area informada errada.
    assert validate_or_repair_pair("Ciências Exatas e da Terra", "Psicologia") == (
        "Ciências Humanas",
        "Psicologia",
    )


def test_validate_or_repair_pair_ambos_invalidos_retorna_none():
    assert validate_or_repair_pair("Não Existe", "Também Não Existe") is None


def test_extract_doi_valido():
    texto = "DOI: 10.1037/arc0000014 e mais texto"
    assert extract_doi(texto) == "10.1037/arc0000014"


def test_extract_doi_limpa_pontuacao_terminal():
    texto = "https://doi.org/10.1000/xyz123."
    assert extract_doi(texto) == "10.1000/xyz123"


def test_extract_doi_nao_encontrado():
    assert extract_doi("não há doi aqui") is None


def test_extract_isbn_valido_isbn13():
    texto = "ISBN 978-85-363-1234-7"
    # 9788536312347 é um ISBN-13 válido (dígito verificador = 7).
    assert extract_isbn(texto) == "9788536312347"


def test_extract_isbn_rejeita_numero_arbitrario():
    # 531581939 é um número arbitrário (não ISBN válido).
    assert extract_isbn("531581939") is None


def test_extract_isbn_nao_encontrado():
    assert extract_isbn("não há isbn aqui") is None


def test_detect_cip_page():
    texto = """
    Sumário
    ...
    Ficha catalográfica
    Silva, João.
    Título da obra / João Silva. -- São Paulo : Editora, 2021.
    CDD 150.19
    """
    cip = detect_cip_page(texto)
    assert "Ficha catalográfica" in cip
    assert "CDD" in cip


def test_detect_cip_page_sem_marcador():
    assert detect_cip_page("apenas texto comum sem ficha") == ""
