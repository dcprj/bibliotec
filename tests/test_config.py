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
    assert config.llm.model == "gemini-3.5-flash"
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
model = "gemini-3.5-flash"

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


def test_llm_config_default_provider_alias(tmp_path, monkeypatch):
    """default_provider é um alias para provider (retrocompatibilidade)."""
    monkeypatch.chdir(tmp_path)
    toml_path = tmp_path / "bibliotec.toml"
    toml_path.write_text(
        """
[llm]
default_provider = "nvidia"
model = "nemotron-3.5-super-vl-120b-a12b"
fallback_chain = ["groq", "nvidia", "deepseek"]

[api_keys]
gemini_api_key = ""
google_books_api_key = ""
openalex_polite_email = ""
nvidia_api_key = ""
deepseek_api_key = ""
claude_api_key = ""
""",
        encoding="utf-8",
    )
    config = AppConfig()
    assert config.llm.provider == "nvidia"
    # default_provider é um validation_alias: mapeia para provider na leitura do TOML
    assert config.llm.fallback_chain == ["groq", "nvidia", "deepseek"]
    assert config.llm.model == "nemotron-3.5-super-vl-120b-a12b"


def test_llm_config_providers_dict(tmp_path, monkeypatch):
    """providers aceita dicionário de configurações específicas por provedor."""
    monkeypatch.chdir(tmp_path)
    toml_path = tmp_path / "bibliotec.toml"
    toml_path.write_text(
        """
[llm]
provider = "gemini"
model = "gemini-3.5-flash"
fallback_chain = ["groq", "nvidia", "deepseek"]

[llm.providers.deepseek]
model = "deepseek-flash"
base_url = "https://api.deepseek.com"
max_tokens = 4096

[llm.providers.nvidia]
model = "nemotron-3.5-super-vl-120b-a12b"
base_url = "https://integrate.api.nvidia.com/v1"
max_tokens = 4096

[api_keys]
gemini_api_key = ""
google_books_api_key = ""
openalex_polite_email = ""
nvidia_api_key = ""
deepseek_api_key = ""
claude_api_key = ""
""",
        encoding="utf-8",
    )
    config = AppConfig()
    assert config.llm.providers["deepseek"]["model"] == "deepseek-flash"
    assert config.llm.providers["deepseek"]["base_url"] == "https://api.deepseek.com"
    assert config.llm.providers["deepseek"]["max_tokens"] == 4096
    assert config.llm.providers["nvidia"]["model"] == "nemotron-3.5-super-vl-120b-a12b"
    assert config.llm.providers["nvidia"]["base_url"] == "https://integrate.api.nvidia.com/v1"


def test_api_keys_deepseek_and_claude_env(tmp_path, monkeypatch):
    """Variáveis de ambiente diretas são lidas para deepseek e claude."""
    monkeypatch.chdir(tmp_path)
    init_config_file(local=True)

    monkeypatch.setenv("BIBLIOTEC_DEEPSEEK_API_KEY", "ds-key-1234")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "claude-key-5678")

    config = AppConfig()
    assert config.api_keys.deepseek_api_key == "ds-key-1234"
    assert config.api_keys.claude_api_key == "claude-key-5678"


def test_mask_key_mascarar_novas_chaves():
    """mask_key deve mascarar corretamente as novas chaves de API."""
    from bibliotec.core.config import mask_key

    # Chave vazia
    assert mask_key("") == ""

    # Chave curta (<= 4 caracteres)
    assert mask_key("abc") == "****"

    # Chave longa (mostra apenas os últimos 4)
    assert mask_key("sk-1234567890abcdef") == "****cdef"
    assert mask_key("nvapi-abcdef1234567890") == "****7890"
    assert mask_key("sk-ant-1234567890abcdef") == "****cdef"


def test_template_contem_novas_secoes():
    """O template gerado deve conter as novas seções e chaves."""
    from bibliotec.core.config import generate_config_template

    template = generate_config_template()
    assert "default_provider" in template
    assert "fallback_chain" in template
    assert "deepseek_api_key" in template
    assert "claude_api_key" in template
    assert "nvidia_api_key" in template
    # Seções de provedor comentadas
    assert "providers.deepseek" in template
    assert "providers.nvidia" in template
    assert "providers.groq" in template


def test_llm_config_valores_padrao():
    """LLMConfig deve ter valores padrão corretos."""
    from bibliotec.core.config import LLMConfig

    config = LLMConfig()
    assert config.provider == "gemini"
    # default_provider é um validation_alias: acessível apenas na leitura do TOML/env
    assert config.fallback_chain == ["groq", "nvidia", "deepseek"]
    assert config.model == "gemini-3.5-flash"
    assert config.providers == {}
