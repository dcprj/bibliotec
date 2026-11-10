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

    Aceita 'Sobrenome, Nome' (formato do Tomus) ou 'Nome Sobrenome'.
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

    Exemplos:
    * Livro: CARNEIRO, Sueli. **Escritos de uma vida**. 1. ed. São Paulo: Pólen Livros, 2018. 288 p. ISBN 9786557826669.
    * Artigo: BULAMAH, Lucas Charafeddine; KUPERMANN, Daniel. A dupla volta da subjetivação em Winnicott. **Tempo Psicanalítico**, Rio de Janeiro, v. 54.1, p. 134-155, 2022. Disponível em: https://doi.org/...
    """
    authors = classification.get("authors") or []
    title = (classification.get("title") or "").strip()
    subtitle = (classification.get("subtitle") or "").strip()
    year = classification.get("year")
    edition = classification.get("edition")
    city = classification.get("city")
    publisher = classification.get("publisher")
    journal_name = classification.get("journal_name")
    volume = classification.get("volume")
    number = classification.get("number")
    pages = classification.get("pages")
    doi = classification.get("doi")
    isbn = classification.get("isbn")
    tipo = str(classification.get("tipo") or "")

    autores_texto = format_abnt_authors(authors).strip().rstrip(".")

    partes: list[str] = []
    if autores_texto:
        partes.append(autores_texto)

    # Formatação especializada por Tipo Documental
    if tipo == "Artigo" and journal_name:
        # Em artigos: Título do artigo é texto normal; Nome do periódico em negrito
        art_title = f"{title}: {subtitle}" if subtitle else title
        if not autores_texto:
            art_title = _primeira_palavra_maiuscula(art_title)
        partes.append(art_title.rstrip("."))

        # Detalhes do periódico: **Nome da Revista**, Local, v. X, n. Y, p. xx-yy, ano.
        j_parts = [f"**{journal_name}**"]
        if city:
            j_parts.append(city)
        if volume:
            v_str = f"v. {volume}" if not str(volume).lower().startswith("v.") else str(volume)
            j_parts.append(v_str)
        if number:
            n_str = f"n. {number}" if not str(number).lower().startswith("n.") else str(number)
            j_parts.append(n_str)
        if pages:
            p_str = f"p. {pages}" if not str(pages).lower().startswith("p.") else str(pages)
            j_parts.append(p_str)
        if year is not None:
            j_parts.append(str(year))

        partes.append(", ".join(j_parts))

    else:
        # Livro, Tese_Dissertacao, Revista Científica ou Outros: Título principal em negrito
        titulo_formatado = f"**{title}**"
        if subtitle:
            titulo_formatado = f"**{title}**: {subtitle}"

        if not autores_texto:
            titulo_formatado = _primeira_palavra_maiuscula(titulo_formatado)
        partes.append(titulo_formatado)

        if edition:
            ed_str = f"{str(edition).rstrip('.')}." if not str(edition).endswith("ed.") else str(edition)
            partes.append(ed_str)

        # Publicação: Cidade: Editora, Ano.
        imprint_parts: list[str] = []
        if city and publisher:
            imprint_parts.append(f"{city}: {publisher}")
        elif publisher:
            imprint_parts.append(f"[S.l.]: {publisher}")
        elif city:
            imprint_parts.append(f"{city}: [s.n.]")

        if year is not None:
            if imprint_parts:
                imprint_parts[0] += f", {year}"
            else:
                imprint_parts.append(str(year))

        if imprint_parts:
            partes.append(imprint_parts[0])

        if pages:
            p_str = f"{pages} p." if str(pages).isdigit() else str(pages)
            partes.append(p_str)

    # Limpeza de pontuação duplicada
    partes_limpas = [p.strip().rstrip(".") for p in partes if p and p.strip()]
    referencia = ". ".join(partes_limpas) + "."

    # DOI e ISBN
    if doi:
        doi_clean = str(doi).strip()
        doi_url = doi_clean if doi_clean.startswith("http") else f"https://doi.org/{doi_clean}"
        referencia += f" Disponível em: {doi_url}."
    if isbn:
        referencia += f" ISBN {str(isbn).strip()}."

    return referencia


def generate_companion_markdown(
    destination_path: Path,
    source_path: Path,
    sha256: str,
    classification: dict[str, Any],
    used_ocr: bool = False,
) -> str:
    """Gerar o conteúdo Markdown completo do arquivo companheiro.

    Inclui front matter YAML completo e corpo com título, referência ABNT e metadados.
    """
    authors = classification.get("authors") or []
    title = classification.get("title") or ""
    subtitle = classification.get("subtitle") or ""
    year = classification.get("year")
    publisher = classification.get("publisher")
    city = classification.get("city")
    edition = classification.get("edition")
    journal_name = classification.get("journal_name")
    volume = classification.get("volume")
    number = classification.get("number")
    pages = classification.get("pages")
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
    if publisher:
        lines.append(f"publisher: {publisher!r}")
    if city:
        lines.append(f"city: {city!r}")
    if edition:
        lines.append(f"edition: {edition!r}")
    if journal_name:
        lines.append(f"journal_name: {journal_name!r}")
    if volume:
        lines.append(f"volume: {str(volume)!r}")
    if number:
        lines.append(f"number: {str(number)!r}")
    if pages:
        lines.append(f"pages: {str(pages)!r}")
    if doi:
        lines.append(f"doi: {doi!r}")
    if isbn:
        lines.append(f"isbn: {isbn!r}")
    lines.append(f"grande_area: {grande_area!r}")
    lines.append(f"area_basica: {area_basica!r}")
    lines.append(f"tipo: {tipo!r}")
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
    if journal_name:
        lines.append(f"- **Periódico / Revista:** {journal_name}")
    if volume or number:
        vol_str = f"v. {volume}" if volume and not str(volume).lower().startswith("v.") else (volume or "")
        num_str = f"n. {number}" if number and not str(number).lower().startswith("n.") else (number or "")
        vol_num = ", ".join(filter(None, [vol_str, num_str]))
        lines.append(f"- **Volume / Fascículo:** {vol_num}")
    if publisher:
        lines.append(f"- **Editora / Publicador:** {publisher}")
    if city:
        lines.append(f"- **Local de Publicação:** {city}")
    if edition:
        lines.append(f"- **Edição:** {edition}")
    if pages:
        lines.append(f"- **Páginas:** {pages}")
    if doi:
        doi_clean = str(doi).strip()
        doi_url = doi_clean if doi_clean.startswith("http") else f"https://doi.org/{doi_clean}"
        lines.append(f"- **DOI:** {doi_url}")
    if isbn:
        lines.append(f"- **ISBN:** {isbn}")
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
