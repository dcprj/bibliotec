"""Formatador de nomes acadêmicos de arquivo (Item 20).

Compõe '<autor> - <titulo> - <subtitulo> - <ano>.pdf' com suporte a 1, 2 ou
3+ autores, omissão de subtítulo vazio, 's.d.' quando o ano for None,
normalização Unicode NFC, sanitização de caracteres proibidos e truncamento
progressivo em fronteira de palavra garantindo len(filename.encode('utf-8'))
<= 240 bytes (abaixo do limite de 255 bytes do sistema de arquivos).
"""

from __future__ import annotations

import unicodedata

# Caracteres proibidos em nomes de arquivo (Windows / POSIX portátil).
_PROHIBITED_CHARS = set(r'/\:*?"<>|')
# Separador entre campos do nome acadêmico.
_FIELD_SEP = " - "
# Sufixo incremental para resolução de colisão.
_COLLISION_SUFFIX = " (2)"
# Limite máximo de bytes UTF-8 do nome do arquivo (extensão .pdf incluída).
MAX_BYTES = 240


def _sanitize(value: str) -> str:
    """Remover caracteres proibidos e colapsar espaços em branco."""
    sanitized = "".join(ch for ch in value if ch not in _PROHIBITED_CHARS)
    return " ".join(sanitized.split())


def _truncate_word_boundary(text: str, max_bytes: int) -> str:
    """Truncar 'text' em fronteira de palavra respeitando um orçamento de bytes.

    Itera palavra por palavra acumulando-as separadas por espaço, de modo que
    nunca insira espaços entre letras de uma mesma palavra. Retorna o maior
    prefixo cujo tamanho em bytes UTF-8 não exceda 'max_bytes'. Se mesmo a
    primeira palavra sozinha exceder o orçamento, truncar por caracteres sem
    quebrar sequências multibyte UTF-8.
    """
    if max_bytes <= 0:
        return ""

    palavras = text.split()
    if not palavras:
        return ""

    resultado = ""
    for palavra in palavras:
        candidato = (resultado + " " + palavra).strip()
        if len(candidato.encode("utf-8")) > max_bytes:
            break
        resultado = candidato

    if resultado:
        return resultado

    # Primeira palavra sozinha excede o orçamento: truncar por caracteres,
    # respeitando fronteiras UTF-8 (não cortar dentro de sequência multibyte).
    codificado = palavras[0].encode("utf-8")
    if len(codificado) <= max_bytes:
        return palavras[0]
    corte = codificado[:max_bytes]
    # Recuar até encontrar o início de um caractere UTF-8 (byte não 0x80-0xBF).
    while corte and (corte[-1] & 0xC0) == 0x80:
        corte = corte[:-1]
    return corte.decode("utf-8", errors="ignore")


def format_academic_filename(
    *,
    authors: list[str],
    title: str,
    subtitle: str = "",
    year: int | str | None = None,
    ext: str = ".pdf",
) -> str:
    """Formatar o nome acadêmico do arquivo.

    Regras:
      * 1 autor: authors[0] ('Sobrenome, Nome').
      * 2 autores: 'Sobrenome1; Sobrenome2'.
      * 3+ autores: 'Sobrenome1 et al.'.
      * subtítulo vazio é omitido (e o separador associado).
      * ano None -> 's.d.'.
      * normalização Unicode NFC.
      * sanitização de '/ \\ : * ? " < > |'.
      * truncamento progressivo primeiro do subtítulo e depois do título,
        em fronteira de palavra, preservando <autor> e <ano>.
      * len(filename.encode('utf-8')) <= 240 bytes.
    """
    from bibliotec.core.prompts import format_authors_for_filename

    autor = format_authors_for_filename(list(authors))
    autor = _sanitize(autor)

    titulo = _sanitize(title or "")
    subtitulo = _sanitize(subtitle or "")

    if year is None:
        ano = "s.d."
    else:
        ano = str(year)

    # Extensão conta no orçamento de bytes.
    ext_bytes = len(ext.encode("utf-8"))

    # Orçamento disponível para os campos variáveis (autor, títulos, ano e
    # separadores ' - ' entre eles).
    def build(subt: str) -> str:
        partes = [autor, titulo]
        if subt:
            partes.append(subt)
        partes.append(ano)
        return _FIELD_SEP.join(partes) + ext

    # Orçamento de bytes para os campos variáveis (sem a extensão).
    budget = MAX_BYTES - ext_bytes

    # Montar com subtítulo completo se couber.
    nome = build(subtitulo)
    if len(nome.encode("utf-8")) <= MAX_BYTES:
        return unicodedata.normalize("NFC", nome)

    # Truncar progressivamente: primeiro o subtítulo.
    variavel_fixo = len((_FIELD_SEP.join([autor, titulo, ano])).encode("utf-8"))
    if subtitulo:
        # espaço para o subtítulo = budget - (autor + separador + título +
        # separador + ano), mais o separador extra antes do subtítulo.
        # Calcular diretamente: tentar encaixar subtítulo no restante.
        prefixo = _FIELD_SEP.join([autor, titulo]) + _FIELD_SEP
        prefixo_bytes = len(prefixo.encode("utf-8"))
        ano_com_sep = _FIELD_SEP + ano
        ano_bytes = len(ano_com_sep.encode("utf-8"))
        sub_budget = budget - prefixo_bytes - ano_bytes
        subt_trunc = _truncate_word_boundary(subtitulo, sub_budget)
        if subt_trunc:
            nome = build(subt_trunc)
            if len(nome.encode("utf-8")) <= MAX_BYTES:
                return unicodedata.normalize("NFC", nome)
        # Subtítulo não coube de forma útil; omiti-lo.
        subt_trunc = ""

    # Sem subtítulo útil: truncar o título, preservando autor e ano.
    prefixo_autor = autor + _FIELD_SEP
    sufixo_ano = _FIELD_SEP + ano
    prefixo_bytes = len(prefixo_autor.encode("utf-8"))
    sufixo_bytes = len(sufixo_ano.encode("utf-8"))
    titulo_budget = budget - prefixo_bytes - sufixo_bytes
    titulo_trunc = _truncate_word_boundary(titulo, titulo_budget)
    nome = prefixo_autor + titulo_trunc + sufixo_ano + ext
    nome = unicodedata.normalize("NFC", nome)

    # Garantia final de segurança: se ainda exceder (casos extremos com
    # autor/ano longos), truncar brutalmente o título até caber.
    if len(nome.encode("utf-8")) > MAX_BYTES:
        while titulo_trunc and len(nome.encode("utf-8")) > MAX_BYTES:
            titulo_trunc = titulo_trunc[:-1]
            nome = prefixo_autor + titulo_trunc + sufixo_ano + ext
            nome = unicodedata.normalize("NFC", nome)

    return nome
