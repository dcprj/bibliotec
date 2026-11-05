"""Testes unitários para src/bibliotec/core/config.py.

Valida a geração do arquivo config.toml local e a leitura por AppConfig()
respeitando a precedência das fontes de configuração.
"""

from __future__ import annotations

import os

import pytest

from bibliotec.core.config import AppConfig, init_config_file


def test_init_config_file_local_creates_bibliotec_toml(tmp_path, monkeypatch):
    """init_config_file(local=True) cria ./bibliotec.toml com permissão 0600."""
    monkeypatch.chdir(tmp_path)
    target = init_config_file(local=True)

    assert target == tmp_path / "bibliotec.toml"
    assert target.exists()

    # Permissão restrita (apenas o dono lê/escreve)
    mode = os.stat(target).st_mode & 0o777
    assert mode == 0o600

    # Conteúdo contém as seções esperadas
    content = target.read_text(encoding="utf-8")
    assert "[general]" in content
    assert "[llm]" in content
    assert "[api_keys]" in content
    assert "gemini_api_key" in content


def test_app_config_reads_local_toml_without_validation_error(tmp_path, monkeypatch):
    """AppConfig() não falha com ValidationError quando ./bibliotec.toml existe."""
    monkeypatch.chdir(tmp_path)
    init_config_file(local=True)

    # Não deve levantar ValidationError
    config = AppConfig()

    assert config.general.recursive is True
    assert config.general.file_operation == "copy"
    assert config.general.confidence_min == 0.70
    assert config.general.workers == 1
    assert config.general.use_cache is True
    assert config.llm.provider == "gemini"
    assert config.llm.model == "gemini-2.5-flash"
    assert config.api_keys.gemini_api_key == ""
    assert config.api_keys.google_books_api_key == ""
    assert config.api_keys.openalex_polite_email == ""


def test_app_config_reads_env_variables(tmp_path, monkeypatch):
    """Variáveis de ambiente diretas são lidas por ApiKeysConfig via AppConfig."""
    monkeypatch.chdir(tmp_path)
    init_config_file(local=True)

    # BIBLIOTEC_* deve ser lido (sem GEMINI_API_KEY definido)
    monkeypatch.setenv("BIBLIOTEC_GEMINI_API_KEY", "env-gemini-key-1234")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    config = AppConfig()

    assert config.api_keys.gemini_api_key == "env-gemini-key-1234"


def test_app_config_ignores_extra_keys(tmp_path, monkeypatch):
    """AppConfig() não rejeita chaves extras no TOML (extra='ignore')."""
    monkeypatch.chdir(tmp_path)
    toml_path = tmp_path / "bibliotec.toml"
    toml_path.write_text(
        """
[general]
recursive = true
file_operation = "copy"
confidence_min = 0.70
workers = 1
use_cache = true

[llm]
provider = "gemini"
model = "gemini-2.5-flash"

[api_keys]
gemini_api_key = ""
google_books_api_key = ""
openalex_polite_email = ""
chave_inexistente = "deve ser ignorada"
""",
        encoding="utf-8",
    )

    # Não deve levantar ValidationError por causa da chave extra
    config = AppConfig()
    assert config.general.recursive is True
