"""Testes para o módulo de arquivo companheiro (.md) do BiblioTEC.

Cobre: formatação de autores ABNT NBR 6023, referência bibliográfica,
front matter YAML, geração de markdown e integração com LibraryOrganizer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bibliotec.storage.companion import (
    format_abnt_authors,
    format_abnt_author,
    format_abnt_reference,
    generate_companion_markdown,
)
from bibliotec.storage.organizer import LibraryOrganizer
from bibliotec.storage.namer import format_academic_filename


# --------------------------------------------------------------------------- #
# Testes unitários: formatação de autores (ABNT NBR 6023)
# --------------------------------------------------------------------------- #
def test_abnt_author_uma_palavra():
    """Autor com uma única palavra fica em maiúsculas."""
    assert format_abnt_author("Machado") == "MACHADO"


def test_abnt_author_nome_sobrenome():
    """'Nome Sobrenome' vira 'SOBRENOME, Nome'."""
    assert format_abnt_author("Márcio Borges Moreira") == "MOREIRA, Márcio Borges"


def test_abnt_author_sobrenome_nome():
    """'Sobrenome, Nome' preserva o formato com sobrenome maiúsculo."""
    assert format_abnt_author("Moreira, M. B.") == "MOREIRA, M. B."


def test_abnt_authors_um_autor():
    """Um autor recebe ponto final."""
    assert format_abnt_authors(["SILVA, João"]) == "SILVA, João."


def test_abnt_authors_dois_autores():
    """Dois autores separados por ponto e vírgula."""
    assert format_abnt_authors(["SILVA, João", "SANTOS, Maria"]) == (
        "SILVA, João; SANTOS, Maria."
    )


def test_abnt_authors_tres_autores():
    """Três autores todos listados."""
    assert format_abnt_authors(["SILVA, João", "SANTOS, Maria", "OLIVEIRA, Pedro"]) == (
        "SILVA, João; SANTOS, Maria; OLIVEIRA, Pedro."
    )


def test_abnt_authors_mais_de_tres():
    """Mais de três autores usa 'et al.'."""
    assert format_abnt_authors(
        ["SILVA, João", "SANTOS, Maria", "OLIVEIRA, Pedro", "COSTA, Ana"]
    ) == "SILVA, João et al."


def test_abnt_authors_sem_autores():
    """Lista vazia retorna string vazia."""
    assert format_abnt_authors([]) == ""


# --------------------------------------------------------------------------- #
# Testes unitários: referência bibliográfica ABNT NBR 6023
# --------------------------------------------------------------------------- #
def test_abnt_reference_completa():
    """Referência com autores, título e ano."""
    classificacao = {
        "authors": ["MOREIRA, M. B.", "MEDEIROS, C. A."],
        "title": "Princípios Básicos de Análise do Comportamento",
        "year": 2007,
    }
    ref = format_abnt_reference(classificacao)
    assert ref.startswith("MOREIRA, M. B.; MEDEIROS, C. A.")
    assert "**Princípios Básicos de Análise do Comportamento**" in ref
    assert ref.endswith("2007.")


def test_abnt_reference_com_subtitulo():
    """Referência com subtítulo separado por dois pontos."""
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Título do Trabalho",
        "subtitle": "uma abordagem comportamental",
        "year": 2020,
    }
    ref = format_abnt_reference(classificacao)
    assert "**Título do Trabalho**: uma abordagem comportamental" in ref


def test_abnt_reference_com_doi():
    """Referência com DOI inclui 'Disponível em: https://doi.org/...'."""
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Título",
        "year": 2021,
        "doi": "10.1234/abc",
    }
    ref = format_abnt_reference(classificacao)
    assert "Disponível em: https://doi.org/10.1234/abc." in ref


def test_abnt_reference_com_isbn():
    """Referência com ISBN inclui 'ISBN ...'."""
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Título",
        "year": 2021,
        "isbn": "978-85-123456-7-8",
    }
    ref = format_abnt_reference(classificacao)
    assert "ISBN 978-85-123456-7-8." in ref


def test_abnt_reference_sem_autor():
    """Sem autor, inicia pelo título com primeira palavra em caixa alta."""
    classificacao = {
        "authors": [],
        "title": "estudos sobre comportamento",
        "year": 2019,
    }
    ref = format_abnt_reference(classificacao)
    assert ref.startswith("**ESTUDOS sobre comportamento**")
    assert ref.endswith("2019.")


# --------------------------------------------------------------------------- #
# Testes unitários: front matter YAML e corpo do markdown
# --------------------------------------------------------------------------- #
def test_companion_front_matter_yaml():
    """O front matter deve começar e terminar com '---'."""
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Título de Teste",
        "year": 2020,
        "grande_area": "Ciências Humanas",
        "area_basica": "Psicologia",
        "tipo": "Livro",
        "confidence_score": 0.90,
    }
    md = generate_companion_markdown(
        destination_path=Path("/x/teste.md"),
        source_path=Path("/orig/teste.pdf"),
        sha256="abc123",
        classification=classificacao,
    )
    assert md.startswith("---\n")
    assert "title: 'Título de Teste'" in md
    assert "authors:" in md
    assert "  - 'SILVA, João'" in md
    assert "year: 2020" in md
    assert "grande_area: 'Ciências Humanas'" in md
    assert "area_basica: 'Psicologia'" in md
    assert "tipo: 'Livro'" in md
    assert "sha256: abc123" in md
    assert "confidence_score: 0.9" in md
    assert "used_ocr: false" in md
    assert "source_file: teste.pdf" in md
    assert "organized_at:" in md
    assert md.count("---") == 2  # abertura e fechamento


def test_companion_com_subtitulo_doi_isbn():
    """Front matter inclui subtítulo, DOI e ISBN quando presentes."""
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Título",
        "subtitle": "subtítulo de teste",
        "year": 2021,
        "grande_area": "Ciências Exatas",
        "area_basica": "Computação",
        "tipo": "Artigo",
        "doi": "10.1234/xyz",
        "isbn": "978-85-000000-0-0",
        "confidence_score": 0.85,
    }
    md = generate_companion_markdown(
        destination_path=Path("/x/teste.md"),
        source_path=Path("/orig/teste.pdf"),
        sha256="def456",
        classification=classificacao,
        used_ocr=True,
    )
    assert "subtitle: 'subtítulo de teste'" in md
    assert "doi: '10.1234/xyz'" in md
    assert "isbn: '978-85-000000-0-0'" in md
    assert "used_ocr: true" in md
    assert "confidence_score: 0.85" in md


def test_companor_corpo_markdown():
    """O corpo do markdown deve ter título, referência e metadados."""
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Título do Documento",
        "year": 2020,
        "grande_area": "Ciências Humanas",
        "area_basica": "Psicologia",
        "tipo": "Livro",
        "confidence_score": 0.90,
    }
    md = generate_companion_markdown(
        destination_path=Path("/x/teste.md"),
        source_path=Path("/orig/teste.pdf"),
        sha256="abc123",
        classification=classificacao,
    )
    assert "# Título do Documento" in md
    assert "## Referência Bibliográfica (ABNT NBR 6023)" in md
    assert "## Metadados do Arquivo" in md
    assert "**Área Temática:** Ciências Humanas / Psicologia" in md
    assert "**Tipo de Documento:** Livro" in md
    assert "**Arquivo Original:** teste.pdf" in md
    assert "**SHA-256:** abc123" in md


# --------------------------------------------------------------------------- #
# Teste de integração: organizer gera arquivo companheiro
# --------------------------------------------------------------------------- #
def test_organizer_gera_arquivo_companheiro(tmp_path: Path):
    """LibraryOrganizer deve gerar arquivo .md ao lado do PDF organizado."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "livro_teste.pdf").write_bytes(b"%PDF-1.4 falso")

    organizer = LibraryOrganizer(target, file_operation="copy", dry_run=False)
    nome = format_academic_filename(
        authors=["SILVA, João"], title="Livro de Teste", year=2020
    )
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Livro de Teste",
        "year": 2020,
        "grande_area": "Ciências Humanas",
        "area_basica": "Psicologia",
        "tipo": "Livro",
        "confidence_score": 0.90,
    }

    entry = organizer.add_organized(
        source_path=source / "livro_teste.pdf",
        grande_area="Ciências Humanas",
        area_basica="Psicologia",
        tipo="Livro",
        filename=nome,
        sha256="abc123",
        used_ocr=False,
        classification=classificacao,
    )

    # O arquivo companheiro deve existir ao lado do PDF.
    companion_path = Path(entry.destination_path).with_suffix(".md")
    assert companion_path.exists(), f"arquivo companheiro não encontrado: {companion_path}"
    conteudo = companion_path.read_text(encoding="utf-8")
    assert "# Livro de Teste" in conteudo
    assert "## Referência Bibliográfica (ABNT NBR 6023)" in conteudo


def test_organizer_dry_run_nao_gera_companheiro(tmp_path: Path):
    """Em modo dry_run não deve gerar arquivo companheiro (.md)."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "livro_teste.pdf").write_bytes(b"%PDF-1.4 falso")

    organizer = LibraryOrganizer(target, file_operation="copy", dry_run=True)
    nome = format_academic_filename(
        authors=["SILVA, João"], title="Livro de Teste", year=2020
    )
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Livro de Teste",
        "year": 2020,
        "grande_area": "Ciências Humanas",
        "area_basica": "Psicologia",
        "tipo": "Livro",
        "confidence_score": 0.90,
    }

    organizer.add_organized(
        source_path=source / "livro_teste.pdf",
        grande_area="Ciências Humanas",
        area_basica="Psicologia",
        tipo="Livro",
        filename=nome,
        sha256="abc123",
        used_ocr=False,
        classification=classificacao,
    )

    # Em dry_run não deve haver arquivo .md no destino.
    md_files = list(target.rglob("*.md"))
    assert md_files == [], f"arquivos .md não esperados em dry_run: {md_files}"


# --------------------------------------------------------------------------- #
# Teste de integração: organizer lida com duplicatas
# --------------------------------------------------------------------------- #
def test_organizer_duplicata_vai_para_pasta_duplicatas_com_md(tmp_path: Path):
    """Duplicata exata deve ir para duplicatas/ com .md companheiro."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    # Dois arquivos com mesmo conteúdo (mesmo SHA-256).
    (source / "a.pdf").write_bytes(b"%PDF-1.4 conteudo igual")
    (source / "b.pdf").write_bytes(b"%PDF-1.4 conteudo igual")

    organizer = LibraryOrganizer(target, file_operation="copy", dry_run=False)
    nome = format_academic_filename(
        authors=["SILVA, João"], title="Livro Duplicado", year=2020
    )
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Livro Duplicado",
        "year": 2020,
        "grande_area": "Ciências Humanas",
        "area_basica": "Psicologia",
        "tipo": "Livro",
        "confidence_score": 0.90,
    }

    # Primeiro arquivo organizado normalmente.
    entry1 = organizer.add_organized(
        source_path=source / "a.pdf",
        grande_area="Ciências Humanas",
        area_basica="Psicologia",
        tipo="Livro",
        filename=nome,
        sha256="abc123",
        used_ocr=False,
        classification=classificacao,
    )

    # Segundo arquivo (mesmo SHA-256) é duplicata.
    entry2 = organizer.add_organized(
        source_path=source / "b.pdf",
        grande_area="Ciências Humanas",
        area_basica="Psicologia",
        tipo="Livro",
        filename=nome,
        sha256="abc123",
        used_ocr=False,
        classification=classificacao,
    )

    # A duplicata deve ir para duplicatas/ com nome original.
    assert entry2.status.value == "duplicate_skipped"
    duplicatas_dir = target / "duplicatas"
    assert duplicatas_dir.exists(), "pasta duplicatas/ deve existir"
    # O .md companheiro da duplicata deve existir.
    md_dup = list(duplicatas_dir.glob("*.md"))
    assert len(md_dup) == 1, f"esperava 1 .md em duplicatas/, achei: {md_dup}"
    conteudo_md = md_dup[0].read_text(encoding="utf-8")
    assert "status: 'duplicata'" in conteudo_md
    assert "b.pdf" in conteudo_md
    assert "abc123" in conteudo_md


def test_organizer_duplicata_move_limpa_origem(tmp_path: Path):
    """Com file_operation='move', a duplicata é movida e a origem limpa."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    (source / "a.pdf").write_bytes(b"%PDF-1.4 conteudo igual")
    (source / "b.pdf").write_bytes(b"%PDF-1.4 conteudo igual")

    organizer = LibraryOrganizer(target, file_operation="move", dry_run=False)
    nome = format_academic_filename(
        authors=["SILVA, João"], title="Livro Movido", year=2020
    )
    classificacao = {
        "authors": ["SILVA, João"],
        "title": "Livro Movido",
        "year": 2020,
        "grande_area": "Ciências Humanas",
        "area_basica": "Psicologia",
        "tipo": "Livro",
        "confidence_score": 0.90,
    }

    organizer.add_organized(
        source_path=source / "a.pdf",
        grande_area="Ciências Humanas",
        area_basica="Psicologia",
        tipo="Livro",
        filename=nome,
        sha256="abc456",
        used_ocr=False,
        classification=classificacao,
    )
    entry2 = organizer.add_organized(
        source_path=source / "b.pdf",
        grande_area="Ciências Humanas",
        area_basica="Psicologia",
        tipo="Livro",
        filename=nome,
        sha256="abc456",
        used_ocr=False,
        classification=classificacao,
    )

    # O arquivo b.pdf deve ter sido movido para duplicatas/ e removido da origem.
    assert not (source / "b.pdf").exists(), "b.pdf deve ser removido da origem em move"
    duplicatas_dir = target / "duplicatas"
    assert (duplicatas_dir / "b.pdf").exists(), "b.pdf deve estar em duplicatas/"
    assert entry2.status.value == "duplicate_skipped"


def test_generate_duplicate_companion_markdown():
    """generate_duplicate_companion_markdown deve gerar front matter YAML correto."""
    from bibliotec.storage.companion import generate_duplicate_companion_markdown

    md = generate_duplicate_companion_markdown(
        duplicate_source=Path("/source/b.pdf"),
        canonical_dest=Path("/target/Ciências Humanas/Psicologia/Livro/a.pdf"),
        sha256="abc123",
    )
    assert "status: 'duplicata'" in md
    assert "original_filename: 'b.pdf'" in md
    assert "sha256: abc123" in md
    assert "canonical_path:" in md
    assert "detected_at:" in md
    assert "## Arquivo Duplicado Detectado" in md
    assert "b.pdf" in md


def test_organizer_ignored_non_pdf_diagnostics(tmp_path: Path):
    """[DIAG-06] Não-PDFs e atalhos .webloc devem ter diagnóstico detalhado em relatorio_revisao.md."""
    target = tmp_path / "target"
    organizer = LibraryOrganizer(target, file_operation="copy", dry_run=False)

    e1 = organizer.add_ignored_non_pdf(Path("/origem/artigo.webloc"))
    assert "Atalho de internet macOS (.webloc)" in e1.error_message

    e2 = organizer.add_ignored_non_pdf(Path("/origem/livro.epub"))
    assert "E-book não-PDF (.epub)" in e2.error_message

    summary = organizer.finalize(total_scanned=2)
    assert summary.ignored_non_pdf_count == 2

    relatorio_md = target / "revisao_manual" / "relatorio_revisao.md"
    assert relatorio_md.exists()
    conteudo = relatorio_md.read_text(encoding="utf-8")
    assert "## Arquivos Não-PDF e Atalhos Ignorados" in conteudo
    assert "artigo.webloc" in conteudo
    assert "Atalho de internet macOS (.webloc)" in conteudo
    assert "livro.epub" in conteudo
    assert "E-book não-PDF (.epub)" in conteudo
