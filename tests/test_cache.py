"""Testes para o cache SQLite do Tomus (src/tomus/core/cache.py).

Cobre: conexão WAL, get/put com confidence_min, persistência seletiva,
--no-cache, invalidação e múltiplas entradas com chave composta.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tomus.core.cache import FileCache, CACHE_DB_PATH


class _FakeClassification(dict):
    """Wrapper para facilitar construção de classificações de teste."""
    def __init__(self, confidence_score: float = 0.9, used_ocr: bool = False,
                 grande_area: str = "Ciências Humanas", **kwargs):
        super().__init__(
            confidence_score=confidence_score,
            used_ocr=used_ocr,
            grande_area=grande_area,
            **kwargs,
        )


# --------------------------------------------------------------------------- #
# Testes de conexão e schema
# --------------------------------------------------------------------------- #
def test_cache_conexao_wal_cria_tabela(tmp_path: Path):
    """A conexão deve abrir em modo WAL e criar a tabela processed_files."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)
    cache._ensure_conn()
    assert cache._conn is not None

    # Verificar modo WAL.
    cur = cache._conn.execute("PRAGMA journal_mode")
    modo = cur.fetchone()[0].lower()
    assert modo == "wal"

    # Verificar tabela.
    cur = cache._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='processed_files'"
    )
    assert cur.fetchone() is not None
    cache.close()


def test_cache_schema_tem_chave_composta(tmp_path: Path):
    """A tabela deve ter PRIMARY KEY (sha256, taxonomy_version, model_name)."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)
    cache._ensure_conn()
    cur = cache._conn.execute(
        "PRAGMA table_info(processed_files)"
    )
    colunas = {row[1]: row for row in cur.fetchall()}
    assert "sha256" in colunas
    assert "taxonomy_version" in colunas
    assert "model_name" in colunas
    # Verificar SQL da criação para a chave composta.
    cur = cache._conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='processed_files'"
    )
    sql = cur.fetchone()[0]
    assert "PRIMARY KEY (sha256, taxonomy_version, model_name)" in sql
    cache.close()


# --------------------------------------------------------------------------- #
# Testes de get/put
# --------------------------------------------------------------------------- #
def test_cache_put_e_get_roundtrip(tmp_path: Path):
    """put seguido de get deve retornar os mesmos dados."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)

    classificacao = _FakeClassification(confidence_score=0.90, used_ocr=False)
    cache.put("aaa111", "capes-cnpq-v1", "gemini-3.8-flash", classificacao, False)

    resultado = cache.get("aaa111", "capes-cnpq-v1", "gemini-3.8-flash")
    assert resultado is not None
    assert resultado["confidence_score"] == 0.90
    assert resultado["used_ocr"] is False
    assert resultado["grande_area"] == "Ciências Humanas"
    cache.close()


def test_cache_get_nao_encontrado_retorna_none(tmp_path: Path):
    """get com chave inexistente deve retornar None."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)
    assert cache.get("inexistente", "capes-cnpq-v1", "gemini-3.8-flash") is None
    cache.close()


def test_cache_chave_composta_distingue_modelos(tmp_path: Path):
    """Mesmo sha256 com modelos diferentes deve ser entradas distintas."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)

    cache.put("sha1", "capes-cnpq-v1", "modelo-A", _FakeClassification(0.90), False,
              confidence_min=0.0)
    cache.put("sha1", "capes-cnpq-v1", "modelo-B", _FakeClassification(0.80), False,
              confidence_min=0.0)

    a = cache.get("sha1", "capes-cnpq-v1", "modelo-A")
    b = cache.get("sha1", "capes-cnpq-v1", "modelo-B")
    assert a is not None and a["confidence_score"] == 0.90
    assert b is not None and b["confidence_score"] == 0.80
    cache.close()


def test_cache_chave_composta_distingue_taxonomy(tmp_path: Path):
    """Mesmo sha256 com taxonomy_version diferente deve ser distinta."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)

    cache.put("sha1", "capes-cnpq-v1", "modelo-X", _FakeClassification(0.90), False,
              confidence_min=0.0)
    cache.put("sha1", "capes-cnpq-v2", "modelo-X", _FakeClassification(0.80), False,
              confidence_min=0.0)

    a = cache.get("sha1", "capes-cnpq-v1", "modelo-X")
    b = cache.get("sha1", "capes-cnpq-v2", "modelo-X")
    assert a is not None and a["confidence_score"] == 0.90
    assert b is not None and b["confidence_score"] == 0.80
    cache.close()


# --------------------------------------------------------------------------- #
# Testes de confidence_min (persistência seletiva)
# --------------------------------------------------------------------------- #
def test_cache_nao_persiste_abaixo_do_confidence_min(tmp_path: Path):
    """Classificações abaixo do confidence_min não devem ser persistidas."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)

    # 0.50 < 0.70 (default) -> não persistir.
    cache.put("sha-baixo", "capes-cnpq-v1", "modelo-Z",
              _FakeClassification(confidence_score=0.50), False)
    assert cache.get("sha-baixo", "capes-cnpq-v1", "modelo-Z") is None

    # 0.90 >= 0.70 -> persistir.
    cache.put("sha-alto", "capes-cnpq-v1", "modelo-Z",
              _FakeClassification(confidence_score=0.90), False)
    assert cache.get("sha-alto", "capes-cnpq-v1", "modelo-Z") is not None
    cache.close()


def test_cache_confidence_min_customizado(tmp_path: Path):
    """O confidence_min pode ser sobrescrito por chamada."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)

    # 0.60 >= 0.50 (custom) -> persistir.
    cache.put("sha", "capes-cnpq-v1", "modelo",
              _FakeClassification(confidence_score=0.60), False,
              confidence_min=0.50)
    assert cache.get("sha", "capes-cnpq-v1", "modelo") is not None

    # 0.60 < 0.70 (default) -> não persistir.
    cache.put("sha2", "capes-cnpq-v1", "modelo",
              _FakeClassification(confidence_score=0.60), False,
              confidence_min=0.70)
    assert cache.get("sha2", "capes-cnpq-v1", "modelo") is None
    cache.close()


# --------------------------------------------------------------------------- #
# Testes de --no-cache (enabled=False)
# --------------------------------------------------------------------------- #
def test_cache_desabilitado_nao_persiste_nem_ler(tmp_path: Path):
    """com enabled=True, mas --no-cache (enabled=False) não grava nem lê."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=False, db_path=db_path)

    cache.put("sha", "capes-cnpq-v1", "modelo",
              _FakeClassification(confidence_score=0.90), False)
    assert cache.get("sha", "capes-cnpq-v1", "modelo") is None
    cache.close()


# --------------------------------------------------------------------------- #
# Testes de invalidação (clear)
# --------------------------------------------------------------------------- #
def test_cache_clear_remove_todos_os_registros(tmp_path: Path):
    """clear deve remover todos os registros da tabela."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)

    cache.put("sha1", "capes-cnpq-v1", "modelo-A", _FakeClassification(0.9), False)
    cache.put("sha2", "capes-cnpq-v1", "modelo-B", _FakeClassification(0.8), False)
    assert cache.get("sha1", "capes-cnpq-v1", "modelo-A") is not None
    assert cache.get("sha2", "capes-cnpq-v1", "modelo-B") is not None

    cache.clear()
    assert cache.get("sha1", "capes-cnpq-v1", "modelo-A") is None
    assert cache.get("sha2", "capes-cnpq-v1", "modelo-B") is None
    cache.close()


# --------------------------------------------------------------------------- #
# Testes de upsert (sobrescrever entrada existente)
# --------------------------------------------------------------------------- #
def test_cache_upsert_sobrescreve_entrada_existente(tmp_path: Path):
    """put com mesma chave composta deve sobrescrever a entrada anterior."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)

    cache.put("sha", "capes-cnpq-v1", "modelo",
              _FakeClassification(confidence_score=0.50), False)
    cache.put("sha", "capes-cnpq-v1", "modelo",
              _FakeClassification(confidence_score=0.90), False)

    resultado = cache.get("sha", "capes-cnpq-v1", "modelo")
    assert resultado is not None
    assert resultado["confidence_score"] == 0.90
    cache.close()


# --------------------------------------------------------------------------- #
# Testes de used_ocr
# --------------------------------------------------------------------------- #
def test_cache_preserva_used_ocr(tmp_path: Path):
    """O campo used_ocr deve ser preservado no roundtrip."""
    db_path = tmp_path / "state.db"
    cache = FileCache(enabled=True, db_path=db_path)

    cache.put("sha", "capes-cnpq-v1", "modelo",
              _FakeClassification(confidence_score=0.90, used_ocr=True), True)
    resultado = cache.get("sha", "capes-cnpq-v1", "modelo")
    assert resultado is not None
    assert resultado["used_ocr"] is True
    cache.close()


# --------------------------------------------------------------------------- #
# Teste de contexto gerenciador (with)
# --------------------------------------------------------------------------- #
def test_cache_contexto_gerenciador(tmp_path: Path):
    """FileCache deve funcionar como gerenciador de contexto."""
    db_path = tmp_path / "state.db"
    with FileCache(enabled=True, db_path=db_path) as cache:
        cache.put("sha", "capes-cnpq-v1", "modelo",
                  _FakeClassification(confidence_score=0.90), False)
        resultado = cache.get("sha", "capes-cnpq-v1", "modelo")
        assert resultado is not None
        assert resultado["confidence_score"] == 0.90
    # Após sair do contexto, a conexão deve estar fechada.
    assert cache._conn is None
