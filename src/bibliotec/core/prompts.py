"""Prompt de sistema e payload contextual do classificador LLM (Item 17).

Concentra as instruções de classificação e o controle de orçamento de tokens:
* texto amostrado (sampled_text) limitado a 15.000 caracteres, priorizando cip_text;
* regras dos 5 tipos documentais (Livro, Revista Científica, Artigo,
  Tese_Dissertacao, Outros);
* formatação de autores em 'Sobrenome, Nome';
* catálogo fechado da CAPES/CNPq via format_taxonomy_for_prompt.
"""

from __future__ import annotations

from bibliotec.core.models import ExternalMetadata
from bibliotec.core.taxonomy import format_taxonomy_for_prompt

# Tamanho máximo do texto amostrado enviado ao classificador (em caracteres).
MAX_SAMPLED_TEXT_CHARS = 15_000

# Valores genéricos de título que reduzem a confiança quando não há autor.
GENERIC_TITLES = {
    "sem título", "sem titulo", "untitled", "unknown", "desconhecido",
    "documento", "pdf", "artigo", "livro", "slide",
}

# Prefixos genéricos de exportação de escritório que reduzem a confiança.
GENERIC_TITLE_PREFIXES = ("microsoft powerpoint -", "microsoft word -")


def _truncate_sampled_text(sampled_text: str, cip_text: str) -> str:
    """Truncar sampled_text priorizando a integralidade de cip_text.

    A Ficha Catalográfica (CIP) é sempre preservada completa; o restante do
    texto amostrado é preenchido com o espaço restante dentro do limite de
    15.000 caracteres.
    """
    if len(sampled_text) <= MAX_SAMPLED_TEXT_CHARS:
        return sampled_text

    reserve = len(cip_text)
    budget = MAX_SAMPLED_TEXT_CHARS - reserve
    if budget <= 0:
        # Não há espaço para nada além do CIP; retornar o CIP sozinho.
        return cip_text[:MAX_SAMPLED_TEXT_CHARS]

    return sampled_text[:budget] + "\n..." + cip_text


def build_system_prompt() -> str:
    """Construir o prompt de sistema com regras de classificação fechadas e schema JSON explícito."""
    return (
        "Você é um classificador acadêmico especializado na tabela CAPES/CNPq.\n"
        "Sua tarefa é classificar um documento PDF com base no texto amostrado "
        "extraído (páginas iniciais e finais) e na Ficha Catalográfica (CIP) "
        "quando disponível.\n\n"
        "Regras obrigatórias de classificação e extração de metadados:\n"
        "1. Responda SOMENTE em JSON válido estritamente no esquema solicitado.\n"
        "2. 'grande_area' e 'area_basica' devem pertencer ao catálogo fechado "
        "CAPES/CNPq fornecido no contexto; não invente categorias.\n"
        "3. 'tipo' deve ser exatamente um dos cinco valores: Livro, "
        "Revista Científica, Artigo, Tese_Dissertacao ou Outros.\n"
        "4. 'authors' deve ser uma lista de strings no formato 'Sobrenome, Nome'. Se desconhecido ou institucional, use ['Autor Desconhecido'].\n"
        "5. 'title' deve ser o título principal da obra/documento em português ou idioma original (não deixe vazio se o título for identificável no texto ou CIP).\n"
        "6. 'subtitle' deve ser o subtítulo da obra se houver, ou string vazia (\"\") se ausente.\n"
        "7. 'year' deve ser o ano de publicação como número inteiro de 4 dígitos (ex: 2014) ou null se não puder ser determinado.\n"
        "8. 'confidence_score' deve estar entre 0.0 e 1.0 representando o grau de certeza na classificação temática.\n"
        "9. 'reasoning' deve justificar brevemente a escolha da Grande Área e Área Básica com base no texto analisado.\n\n"
        "Formato JSON obrigatório:\n"
        "{\n"
        '  "grande_area": "string (exata da tabela CAPES)",\n'
        '  "area_basica": "string (exata da tabela CAPES)",\n'
        '  "tipo": "Livro | Revista Científica | Artigo | Tese_Dissertacao | Outros",\n'
        '  "authors": ["Sobrenome, Nome"],\n'
        '  "title": "string (título completo)",\n'
        '  "subtitle": "string (subtítulo ou vazio)",\n'
        '  "year": 2024,\n'
        '  "confidence_score": 0.95,\n'
        '  "reasoning": "string (justificativa sucinta)"\n'
        "}\n\n"
        "Distinga os tipos documentais assim:\n"
        "- Livro: obra monográfica completa, livro-texto ou coletânea.\n"
        "- Revista Científica: edição ou fascículo completo de periódico com múltiplos artigos.\n"
        "- Artigo: artigo científico individual, ensaio acadêmico ou revisão de literatura avulsa.\n"
        "- Tese_Dissertacao: teses, dissertações, TCCs e monografias acadêmicas.\n"
        "- Outros: slides de aula, apostilas institucionais, cartilhas, relatórios ou ementas.\n\n"
        "Formate os autores sempre como 'Sobrenome, Nome'. Se o autor for uma instituição ou não for identificável, use 'Autor Desconhecido'."
    )


def build_context_payload(
    sampled_text: str,
    cip_text: str,
    external_metadata: ExternalMetadata | None = None,
) -> str:
    """Montar o payload contextual enviado ao LLM.

    O texto amostrado é truncado a no máximo 15.000 caracteres, priorizando a
    preservação integral de cip_text. Metadados externos (quando disponíveis)
    são incluídos para auxiliar a classificação.
    """
    lines: list[str] = []
    lines.append("### Contexto do documento")
    lines.append("")
    lines.append(format_taxonomy_for_prompt())
    lines.append("")

    texto_amostrado = _truncate_sampled_text(sampled_text, cip_text)

    if cip_text:
        lines.append("### Ficha Catalográfica (CIP) - prioridade integral")
        lines.append(cip_text)
        lines.append("")

    lines.append("### Texto amostrado (páginas iniciais e finais)")
    lines.append(texto_amostrado)
    lines.append("")

    if external_metadata is not None:
        lines.append("### Metadados externos (OpenAlex / Google Books)")
        lines.append(f"Título: {external_metadata.title or '(não informado)'}")
        lines.append(f"Subtítulo: {external_metadata.subtitle or '(não informado)'}")
        authors = ", ".join(external_metadata.authors) or "(não informado)"
        lines.append(f"Autores: {authors}")
        lines.append(f"Ano: {external_metadata.publication_year or '(não informado)'}")
        lines.append(f"Tipo sugerido: {external_metadata.document_type_hint or '(não informado)'}")
        lines.append(f"Pontuação da correspondência: {external_metadata.match_score}")
        lines.append("")

    return "\n".join(lines)


def is_generic_title(title: str) -> bool:
    """Verificar se um título é genérico/vazio sem autor identificável."""
    if not title or not title.strip():
        return True
    lowered = title.strip().lower()
    if lowered in GENERIC_TITLES:
        return True
    return any(lowered.startswith(prefix) for prefix in GENERIC_TITLE_PREFIXES)


def format_authors_for_filename(authors: list[str]) -> str:
    """Formatar lista de autores para composição do nome de arquivo.

    * 1 autor: 'Sobrenome, Nome' (usa authors[0] tal qual).
    * 2 autores: 'Sobrenome1; Sobrenome2' (sobrenome antes da vírgula de cada um).
    * 3+ autores: 'Sobrenome1 et al.'
    * lista vazia: 'Autor Desconhecido'.
    """
    if not authors:
        return "Autor Desconhecido"
    if len(authors) == 1:
        return authors[0].strip() or "Autor Desconhecido"
    if len(authors) == 2:
        sobrenomes = [a.split(",")[0].strip() for a in authors if a.strip()]
        sobrenomes = [s for s in sobrenomes if s]
        if len(sobrenomes) == 2:
            return f"{sobrenomes[0]}; {sobrenomes[1]}"
        if len(sobrenomes) == 1:
            return sobrenomes[0]
        return "Autor Desconhecido"
    primeiro_sobrenome = authors[0].split(",")[0].strip() if authors[0].strip() else ""
    return f"{primeiro_sobrenome} et al." if primeiro_sobrenome else "Autor Desconhecido"
