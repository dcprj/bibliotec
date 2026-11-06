"""Gerador de arquivo companheiro (.md) para cada PDF organizado.

Conforme a especificação, gera um arquivo Markdown com front matter YAML e
referência bibliográfica no estilo ABNT NBR 6023 ao lado de cada PDF
organizado na árvore temática.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _sobrenome_maiusculo(autor: str) -> str:
    """Extrair o sobrenome e colocá-lo em maiúsculas, preservando o restante.

    Aceita 'Sobrenome, Nome' (formato do BiblioTEC) ou 'Nome Sobrenome'.
    """
    autor = autor.strip()
    if not autor:
        return ""
    if "," in autor:
        partes = autor.split(",", 1)
        sobrenome = partes[0].strip()
        nome = partes[1].strip()
        return f"{sobrenome.upper()}, {nome}"
    # Formato 'Nome Sobrenome': a última palavra é o sobrenome.
    partes = autor.split()
    if len(partes) == 1:
        return partes[0].upper()
    sobrenome = partes[-1].upper()
    nome = " ".join(partes[:-1])
    return f"{sobrenome}, {nome}"


def format_abnt_author(author: str) -> str:
    """Converter um único autor para o formato ABNT.

    * 'Márcio Borges Moreira' -> 'MOREIRA, Márcio Borges'
    * 'Moreira, M. B.' -> 'MOREIRA, M. B.' (preserva/ajusta)
    """
    return _sobrenome_maiusculo(author)


def format_abnt_authors(authors: list[str]) -> str:
    """Formatar lista de autores segundo ABNT NBR 6023.

    * 1 autor: 'SILVA, João.'
    * 2 autores: 'SILVA, João; SANTOS, Maria.'
    * 3 autores: 'SILVA, João; SANTOS, Maria; OLIVEIRA, Pedro.'
    * Mais de 3 autores: 'SILVA, João et al.'
    * Sem autor: inicia pelo título (retorna string vazia).
    """
    if not authors:
        return ""
    autores_formatados = [_sobrenome_maiusculo(a) for a in authors if a.strip()]
    if not autores_formatados:
        return ""
    if len(autores_formatados) == 1:
        return f"{autores_formatados[0]}."
    if len(autores_formatados) == 2:
        return f"{autores_formatados[0]}; {autores_formatados[1]}."
    if len(autores_formatados) == 3:
        return f"{autores_formatados[0]}; {autores_formatados[1]}; {autores_formatados[2]}."
    return f"{autores_formatados[0]} et al."


def _primeira_palavra_maiuscula(titulo: str) -> str:
    """Deixar a primeira palavra do título em caixa alta."""
    titulo = titulo.strip()
    if not titulo:
        return ""
    match = re.match(r"^(\S+)(.*)$", titulo)
    if not match:
        return titulo
    primeira, resto = match.group(1), match.group(2)
    return primeira.upper() + resto


def format_abnt_reference(classification: dict[str, Any]) -> str:
    """Gerar referência bibliográfica completa segundo ABNT NBR 6023 em Markdown.

    Exemplo: MOREIRA, M. B.; MEDEIROS, C. A. **Princípios Básicos de Análise do Comportamento**. 2007.
    """
    authors = classification.get("authors") or []
    title = classification.get("title") or ""
    subtitle = classification.get("subtitle") or ""
    year = classification.get("year")
    doi = classification.get("doi")
    isbn = classification.get("isbn")

    autores_texto = format_abnt_authors(authors)

    # Título em itálico (Markdown: **titulo**).
    titulo_italico = f"**{title}**"
    if subtitle:
        titulo_italico = f"**{title}**: {subtitle}"

    partes: list[str] = []
    if autores_texto:
        partes.append(autores_texto)
        partes.append(titulo_italico)
    else:
        # Sem autor: inicia pelo título com a primeira palavra em caixa alta.
        partes.append(_primeira_palavra_maiuscula(titulo_italico))

    if year is not None:
        partes.append(str(year))

    referencia = ". ".join(partes)
    if not referencia.endswith("."):
        referencia += "."

    # DOI e ISBN.
    if doi:
        referencia += f" Disponível em: https://doi.org/{doi}."
    if isbn:
        referencia += f" ISBN {isbn}."

    return referencia


def generate_companion_markdown(
    destination_path: Path,
    source_path: Path,
    sha256: str,
    classification: dict[str, Any],
    used_ocr: bool = False,
) -> str:
    """Gerar o conteúdo Markdown completo do arquivo companheiro.

    Inclui front matter YAML e corpo com título, referência ABNT e metadados.
    """
    authors = classification.get("authors") or []
    title = classification.get("title") or ""
    subtitle = classification.get("subtitle") or ""
    year = classification.get("year")
    grande_area = classification.get("grande_area", "")
    area_basica = classification.get("area_basica", "")
    tipo = classification.get("tipo", "")
    doi = classification.get("doi")
    isbn = classification.get("isbn")
    confidence_score = classification.get("confidence_score", 0.0)

    now = datetime.now()
    organized_at = now.strftime("%Y-%m-%d %H:%M:%S")
    data_amigavel = now.strftime("%d/%m/%Y às %H:%M:%S")

    # Front matter YAML.
    lines: list[str] = []
    lines.append("---")
    lines.append(f"title: {title!r}")
    if subtitle:
        lines.append(f"subtitle: {subtitle!r}")
    if authors:
        lines.append("authors:")
        for a in authors:
            lines.append(f"  - {a!r}")
    if year is not None:
        lines.append(f"year: {year}")
    lines.append(f"grande_area: {grande_area!r}")
    lines.append(f"area_basica: {area_basica!r}")
    lines.append(f"tipo: {tipo!r}")
    if doi:
        lines.append(f"doi: {doi!r}")
    if isbn:
        lines.append(f"isbn: {isbn!r}")
    lines.append(f"sha256: {sha256}")
    lines.append(f"confidence_score: {confidence_score}")
    lines.append(f"used_ocr: {str(used_ocr).lower()}")
    lines.append(f"source_file: {source_path.name}")
    lines.append(f"organized_at: {organized_at!r}")
    lines.append("---")
    lines.append("")

    # Corpo Markdown.
    lines.append(f"# {title}")
    lines.append("")
    referencia = format_abnt_reference(classification)
    lines.append("## Referência Bibliográfica (ABNT NBR 6023)")
    lines.append("")
    lines.append(referencia)
    lines.append("")
    lines.append("## Metadados do Arquivo")
    lines.append("")
    lines.append(f"- **Área Temática:** {grande_area} / {area_basica}")
    lines.append(f"- **Tipo de Documento:** {tipo}")
    lines.append(f"- **Arquivo Original:** {source_path.name}")
    lines.append(f"- **SHA-256:** {sha256}")
    lines.append(f"- **Organizado em:** {data_amigavel}")

    return "\n".join(lines) + "\n"


def generate_duplicate_companion_markdown(
    duplicate_source: Path,
    canonical_dest: Path,
    sha256: str,
) -> str:
    """Gerar arquivo companheiro .md para uma duplicata detectada.

    Front Matter YAML com status='duplicata' e corpo explicando que o arquivo
    é idêntico à obra canônica, informando o caminho do PDF canônico e do seu
    .md companheiro.
    """
    now = datetime.now()
    detected_at = now.strftime("%Y-%m-%d %H:%M:%S")
    data_detectada = now.strftime("%d/%m/%Y às %H:%M:%S")
    # Caminho canônico: relativo se possível, absoluto caso contrário.
    try:
        canonical_rel = canonical_dest.resolve().relative_to(Path.cwd().resolve())
        canonical_path = str(canonical_rel)
    except ValueError:
        canonical_path = str(canonical_dest.resolve())
    canonical_md = str(Path(canonical_path).with_suffix(".md"))

    lines: list[str] = []
    lines.append("---")
    lines.append(f"status: 'duplicata'")
    lines.append(f"original_filename: {duplicate_source.name!r}")
    lines.append(f"sha256: {sha256}")
    lines.append(f"canonical_path: {canonical_path!r}")
    lines.append(f"detected_at: {detected_at!r}")
    lines.append("---")
    lines.append("")

    lines.append(f"# {duplicate_source.name}")
    lines.append("")
    lines.append("## Arquivo Duplicado Detectado")
    lines.append("")
    lines.append(f"- **Detectado em:** {data_detectada}")
    lines.append("")
    lines.append(
        "Este arquivo é uma **duplicata exata** (mesmo SHA-256) de uma obra "
        "já organizada na árvore temática. Por não haver conteúdo novo, ele não "
        "foi copiado novamente."
    )
    lines.append("")
    lines.append("### Informações da Duplicata")
    lines.append("")
    lines.append(f"- **Arquivo duplicado:** {duplicate_source.name}")
    lines.append(f"- **SHA-256:** {sha256}")
    lines.append(f"- **Detectado em:** {detected_at}")
    lines.append("")
    lines.append("### Obra Canônica")
    lines.append("")
    lines.append(f"- **PDF canônico:** {canonical_path}")
    lines.append(f"- **Companheiro canônico:** {canonical_md}")
    lines.append("")
    lines.append("> Ambos os arquivos compartilham o mesmo conteúdo binário; "
    "apenas o primeiro foi mantido na árvore temática.")

    return "\n".join(lines) + "\n"
