"""Testes para o módulo de sessão (src/bibliotec/core/session.py).

Cobre: save, load, clear, recuperação tolerante de arquivos corrompidos
e inexistentes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bibliotec.core.session import (
    SESSION_FILE,
    SessionState,
    save_session,
    load_session,
    clear_session,
)


def test_session_state_campos_padrao():
    """SessionState deve preencher valores padrão corretamente."""
    state = SessionState(source_dir="/origem", target_dir="/destino")
    assert state.source_dir == "/origem"
    assert state.target_dir == "/destino"
    assert state.recursive is True
    assert state.move is False
    assert state.dry_run is False
    assert state.provider == "gemini"
    assert state.model is None
    assert state.confidence_min == 0.70
    assert state.workers == 1
    assert state.no_cache is False
    assert state.created_at  # não vazio


def test_session_state_todos_campos():
    """SessionState deve aceitar todos os campos explicitamente."""
    state = SessionState(
        source_dir="/origem",
        target_dir="/destino",
        recursive=False,
        move=True,
        dry_run=True,
        provider="gemini",
        model="gemini-3.8-flash",
        confidence_min=0.85,
        workers=4,
        no_cache=True,
    )
    assert state.recursive is False
    assert state.move is True
    assert state.dry_run is True
    assert state.model == "gemini-3.8-flash"
    assert state.confidence_min == 0.85
    assert state.workers == 4
    assert state.no_cache is True


def test_save_e_load_roundtrip(tmp_path: Path):
    """save_session seguido de load_session deve retornar o mesmo estado."""
    session_path = tmp_path / ".bibliotec_session.json"
    estado_original = SessionState(
        source_dir="/origem",
        target_dir="/destino",
        recursive=False,
        move=True,
        confidence_min=0.80,
        workers=2,
    )

    save_session(estado_original, path=session_path)
    assert session_path.exists()

    estado_carregado = load_session(path=session_path)
    assert estado_carregado is not None
    assert estado_carregado.source_dir == "/origem"
    assert estado_carregado.target_dir == "/destino"
    assert estado_carregado.recursive is False
    assert estado_carregado.move is True
    assert estado_carregado.confidence_min == 0.80
    assert estado_carregado.workers == 2


def test_load_session_arquivo_inexistente_retorna_none(tmp_path: Path):
    """load_session deve retornar None quando o arquivo não existe."""
    session_path = tmp_path / "nao_existe.json"
    assert load_session(path=session_path) is None


def test_load_session_arquivo_corrompido_retorna_none(tmp_path: Path):
    """load_session deve retornar None quando o arquivo JSON está corrompido."""
    session_path = tmp_path / ".bibliotec_session.json"
    session_path.write_text("{json corrompido!!!", encoding="utf-8")
    assert load_session(path=session_path) is None


def test_load_session_arquivo_invalido_retorna_none(tmp_path: Path):
    """load_session deve retornar None quando o JSON não é um SessionState válido."""
    session_path = tmp_path / ".bibliotec_session.json"
    session_path.write_text('{"source_dir": 123}', encoding="utf-8")  # source_dir deve ser str
    assert load_session(path=session_path) is None


def test_clear_session_remove_arquivo(tmp_path: Path):
    """clear_session deve remover o arquivo de sessão."""
    session_path = tmp_path / ".bibliotec_session.json"
    estado = SessionState(source_dir="/o", target_dir="/d")
    save_session(estado, path=session_path)
    assert session_path.exists()

    clear_session(path=session_path)
    assert not session_path.exists()


def test_clear_session_tolerante_arquivo_inexistente(tmp_path: Path):
    """clear_session não deve lançar exceção se o arquivo já não existe."""
    session_path = tmp_path / "nao_existe.json"
    # Não deve levantar FileNotFoundError.
    clear_session(path=session_path)


def test_session_file_constante():
    """SESSION_FILE deve apontar para .bibliotec_session.json."""
    assert SESSION_FILE == Path(".bibliotec_session.json")
    assert SESSION_FILE.name == ".bibliotec_session.json"


def test_save_session_cria_diretorio_pai(tmp_path: Path):
    """save_session deve criar o diretório pai se não existir."""
    session_path = tmp_path / "sub" / "dir" / ".bibliotec_session.json"
    estado = SessionState(source_dir="/o", target_dir="/d")
    save_session(estado, path=session_path)
    assert session_path.exists()
    estado2 = load_session(path=session_path)
    assert estado2 is not None
    assert estado2.source_dir == "/o"


def test_session_state_model_dump_roundtrip(tmp_path: Path):
    """model_dump(mode='json') seguido de SessionState(**data) deve ser consistente."""
    session_path = tmp_path / ".bibliotec_session.json"
    estado = SessionState(
        source_dir="/a",
        target_dir="/b",
        model="gemini-3.5-flash",
        confidence_min=0.60,
    )
    save_session(estado, path=session_path)

    # Ler o JSON bruto e verificar campos.
    import json
    bruto = json.loads(session_path.read_text(encoding="utf-8"))
    assert bruto["source_dir"] == "/a"
    assert bruto["target_dir"] == "/b"
    assert bruto["model"] == "gemini-3.5-flash"
    assert bruto["confidence_min"] == 0.60
    assert "created_at" in bruto
