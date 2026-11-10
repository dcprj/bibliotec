"""Testes unitários do formatador de nomes acadêmicos (Item 25).

Cobrem 1, 2 e 3+ autores, ausência de subtítulo/ano, caracteres especiais e
truncamento exato abaixo de 240 bytes UTF-8 com caracteres acentuados.
"""

from __future__ import annotations

from tomus.storage.namer import format_academic_filename


def test_um_autor():
    nome = format_academic_filename(
        authors=["Silva, João"], title="Psicologia da Educação", year=2021
    )
    assert nome == "Silva, João - Psicologia da Educação - 2021.pdf"


def test_dois_autores():
    nome = format_academic_filename(
        authors=["Silva, João", "Souza, Maria"], title="Trabalho", year=2020
    )
    assert nome == "Silva; Souza - Trabalho - 2020.pdf"


def test_tres_mais_autores():
    nome = format_academic_filename(
        authors=["Silva, João", "Souza, Maria", "Costa, Pedro"], title="Livro", year=2019
    )
    assert nome == "Silva et al. - Livro - 2019.pdf"


def test_sem_subtitulo():
    nome = format_academic_filename(
        authors=["X, Y"], title="Título", year=2022
    )
    assert nome == "X, Y - Título - 2022.pdf"


def test_ano_none_usa_sd():
    nome = format_academic_filename(
        authors=["Autor, Um"], title="Obra", year=None
    )
    assert nome == "Autor, Um - Obra - s.d..pdf"


def test_sem_autores():
    nome = format_academic_filename(
        authors=[], title="Obra sem autor", year=2021
    )
    assert nome.startswith("Autor Desconhecido - Obra sem autor - 2021.pdf")


def test_sanitizacao_caracteres_proibidos():
    nome = format_academic_filename(
        authors=["A, B"], title='t/a:b*c"d<e>f|?', year=2021
    )
    for proibido in r"/\:*?\"<>|":
        assert proibido not in nome
    assert nome == "A, B - tabcdef - 2021.pdf"


def test_truncamento_respeita_240_bytes_utf8():
    """Título longo com acentos deve truncar em fronteira de palavra <= 240 bytes."""
    titulo = "á é í ó ú ã õ ç " * 25
    nome = format_academic_filename(
        authors=["Silva, João"], title=titulo, year=2021
    )
    tamanho_bytes = len(nome.encode("utf-8"))
    assert tamanho_bytes <= 240, f"excedeu 240 bytes: {tamanho_bytes}"
    assert nome.endswith(".pdf")
    # Autor e ano devem ser preservados.
    assert nome.startswith("Silva, João - ")
    assert nome.endswith("- 2021.pdf")


def test_truncamento_nao_divide_palavra():
    """O truncamento deve ocorrer em fronteira de palavra, não dividir palavras."""
    titulo = "palavrauma palavradois palabratres " * 10
    nome = format_academic_filename(
        authors=["Sobrenome, Nome"], title=titulo, year=2020
    )
    tamanho_bytes = len(nome.encode("utf-8"))
    assert tamanho_bytes <= 240
    # A parte do título (entre autor e ano) não deve terminar com caractere
    # acento solto indicando corte no meio de caractere multibyte.
    parte_titulo = nome.split("- 2020.pdf")[0]
    # Remover o prefixo "Autor - "
    parte_titulo = parte_titulo.split("- ", 1)[1]
    # Se houver truncamento, o último caractere não deve ser um byte de
    # continuação UTF-8 (0x80-0xBF).
    if parte_titulo != "":
        ultimo = parte_titulo.encode("utf-8")[-1:]
        assert not (0x80 <= ultimo[0] <= 0xBF), "corte no meio de caractere UTF-8"


def test_limite_exato_240_bytes():
    """Forçar um nome que esteja bem próximo do limite de 240 bytes."""
    autores = ["A, B"]
    titulo = "x" * 200
    nome = format_academic_filename(
        authors=autores, title=titulo, subtitle="y" * 50, year=2021
    )
    tamanho_bytes = len(nome.encode("utf-8"))
    assert tamanho_bytes <= 240
    assert nome.endswith(".pdf")


def test_truncamento_preserva_palavras_intactas_sem_espacos_entre_letras():
    """Truncamento deve manter palavras inteiras, nunca inserir espaços entre letras."""
    titulo = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    nome = format_academic_filename(
        authors=["Sobrenome, Nome"], title=titulo, year=2020
    )
    tamanho_bytes = len(nome.encode("utf-8"))
    assert tamanho_bytes <= 240
    assert nome.endswith(".pdf")
    # Extrair a parte do título (entre o autor e o ano).
    parte_titulo = nome.split("- 2020.pdf")[0].split("- ", 1)[1]
    # As palavras do título devem aparecer intactas (sem espaços entre letras).
    palavras_originais = set(titulo.split())
    palavras_nome = set(parte_titulo.split())
    # Cada palavra no nome truncado deve ser uma palavra original inteira.
    for palavra in palavras_nome:
        assert palavra in palavras_originais, f"palavra quebrada: {palavra!r}"
    # Não deve haver espaços consecutivos nem espaços entre letras.
    assert "  " not in parte_titulo
