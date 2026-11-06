"""Configuração do BiblioTEC usando pydantic-settings com fontes TOML aninhadas.

Ordem de precedência (maior para menor):
    1. init_settings (flags da CLI passadas diretamente ao construtor)
    2. env_settings (variáveis de ambiente)
    3. local_toml_settings (./bibliotec.toml)
    4. global_toml_settings (~/.config/bibliotec/config.toml)
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, ConfigDict, Field, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    TomlConfigSettingsSource,
)

# Caminho global do arquivo de configuração do usuário
GLOBAL_CONFIG_DIR = Path.home() / ".config" / "bibliotec"
GLOBAL_CONFIG_PATH = GLOBAL_CONFIG_DIR / "config.toml"

# Nome do arquivo de configuração local no diretório corrente
LOCAL_CONFIG_FILENAME = "bibliotec.toml"

# Permissão restrita para o arquivo de configuração gerado (apenas o dono lê/escreve)
CONFIG_FILE_MODE = 0o600


class GeneralConfig(BaseSettings):
    """Seção [general] do config.toml."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    recursive: bool = Field(
        default=True,
        description="Varredura recursiva da pasta de origem (true) ou plano (false).",
    )
    file_operation: str = Field(
        default="copy",
        description='Operação padrão: "copy" (copiar) ou "move" (mover).',
    )
    confidence_min: float = Field(
        default=0.70,
        ge=0.0,
        le=1.0,
        description="Limiar mínimo de confiança (0.0 a 1.0) para organização automática.",
    )
    workers: int = Field(
        default=1,
        ge=1,
        description="Número de workers para chamadas de rede (1 = sequencial).",
    )
    use_cache: bool = Field(
        default=True,
        description="Ativar cache local SQLite por SHA-256.",
    )

    @field_validator("file_operation")
    @classmethod
    def _validate_file_operation(cls, value: str) -> str:
        if value not in ("copy", "move"):
            raise ValueError('file_operation deve ser "copy" ou "move"')
        return value


class LLMConfig(BaseSettings):
    """Seção [llm] do config.toml."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    provider: str = Field(
        default="gemini",
        validation_alias=AliasChoices("provider", "default_provider"),
        description="Provedor de classificação padrão (MVP implementa 'gemini').",
    )
    fallback_chain: list[str] = Field(
        default_factory=lambda: ["groq", "nvidia", "deepseek"],
        description="Cadeia de fallback de provedores quando o padrão falha.",
    )
    model: str = Field(
        default="gemini-3.5-flash",
        description="Modelo padrão do provedor.",
    )
    providers: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Configurações específicas por provedor (ex: providers.deepseek.model).",
    )


class ApiKeysConfig(BaseSettings):
    """Seção [api_keys] do config.toml."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("gemini_api_key", "BIBLIOTEC_GEMINI_API_KEY", "GEMINI_API_KEY"),
        description="Chave de API do provedor de LLM (Gemini).",
    )
    google_books_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "google_books_api_key", "BIBLIOTEC_GOOGLE_BOOKS_API_KEY", "GOOGLE_BOOKS_API_KEY"
        ),
        description="Chave de API do Google Books.",
    )
    openalex_polite_email: str = Field(
        default="",
        validation_alias=AliasChoices(
            "openalex_polite_email", "BIBLIOTEC_OPENALEX_POLITE_EMAIL", "OPENALEX_POLITE_EMAIL"
        ),
        description="E-mail opcional para uso do Polite Pool do OpenAlex.",
    )
    nvidia_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "nvidia_api_key", "BIBLIOTEC_NVIDIA_API_KEY", "NVIDIA_API_KEY"
        ),
        description="Chave de API da NVIDIA (NVIDIA NIM / build.nvidia.com).",
    )
    deepseek_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "deepseek_api_key", "BIBLIOTEC_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"
        ),
        description="Chave de API do DeepSeek.",
    )
    claude_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "claude_api_key", "BIBLIOTEC_CLAUDE_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_API_KEY"
        ),
        description="Chave de API da Anthropic Claude.",
    )
    groq_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "groq_api_key", "BIBLIOTEC_GROQ_API_KEY", "GROQ_API_KEY"
        ),
        description="Chave de API da Groq.",
    )
    github_token: str = Field(
        default="",
        validation_alias=AliasChoices(
            "github_token", "BIBLIOTEC_GITHUB_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"
        ),
        description="Token de acesso do GitHub (API REST).",
    )


class AppConfig(BaseSettings):
    """Configuração principal do BiblioTEC.

    Composto pelos submodelos general: GeneralConfig, llm: LLMConfig e
    api_keys: ApiKeysConfig.
    """

    general: GeneralConfig = Field(default_factory=GeneralConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    api_keys: ApiKeysConfig = Field(default_factory=ApiKeysConfig)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        local_toml = LocalTomlSettingsSource(settings_cls)
        global_toml = GlobalTomlSettingsSource(settings_cls)
        return (
            init_settings,
            env_settings,
            local_toml,
            global_toml,
        )


class FilteredTomlSettingsSource(TomlConfigSettingsSource):
    """TomlConfigSettingsSource que ignora valores vazios (strings vazias) para que
    variáveis de ambiente possam preencher os campos (respeitando a precedência
    env > TOML).
    """

    def __call__(self) -> dict[str, Any]:
        data = super().__call__()
        return self._remove_empty_strings(data)

    @staticmethod
    def _remove_empty_strings(data: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, dict):
                nested = FilteredTomlSettingsSource._remove_empty_strings(value)
                if nested:
                    result[key] = nested
            elif value != "":
                result[key] = value
        return result


class LocalTomlSettingsSource(FilteredTomlSettingsSource):
    """Fonte TOML local: ./bibliotec.toml."""

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        super().__init__(settings_cls, toml_file=LOCAL_CONFIG_FILENAME)


class GlobalTomlSettingsSource(FilteredTomlSettingsSource):
    """Fonte TOML global: ~/.config/bibliotec/config.toml."""

    def __init__(self, settings_cls: type[BaseSettings]) -> None:
        super().__init__(settings_cls, toml_file=str(GLOBAL_CONFIG_PATH))


def mask_key(value: str) -> str:
    """Mascarar uma chave de API para exibição segura."""
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return f"****{value[-4:]}"


def generate_config_template() -> str:
    """Gerar o template TOML comentado para config.toml."""
    return """# Arquivo de configuração do BiblioTEC (~/.config/bibliotec/config.toml)
# Ou ./bibliotec.toml para configuração local do diretório corrente

[general]
# Modo de varredura da pasta de origem: true = recursivo (padrão), false = plano
recursive = true
# Operação padrão nos arquivos: "copy" (copiar) ou "move" (mover)
file_operation = "copy"
# Limiar mínimo de confiança (0.0 a 1.0) para organizar automaticamente
confidence_min = 0.70
# Número de workers (1 = execução sequencial padrão segura para OCR e SQLite)
workers = 1
# Ativar cache local SQLite por SHA-256 (~/.cache/bibliotec/state.db)
use_cache = true

[llm]
# Provedor de classificação (MVP implementa "gemini")
provider = "gemini"
# Alias para provider (retrocompatibilidade)
default_provider = "gemini"
# Cadeia de fallback de provedores quando o padrão falha
fallback_chain = ["groq", "nvidia", "deepseek"]
# Modelo padrão do provedor
model = "gemini-3.5-flash"

# Configurações específicas por provedor (exemplo comentado)
#[llm.providers.gemini]
#model = "gemini-3.5-flash"

#[llm.providers.groq]
#model = "openai/gpt-oss-20b"

#[llm.providers.nvidia]
#model = "nvidia/nemotron-3.5-lightning-30b-a3b"

#[llm.providers.deepseek]
#model = "deepseek-flash"

[api_keys]
# Chaves de API do provedor de LLM e serviços de busca acadêmica
gemini_api_key = ""
google_books_api_key = ""
# E-mail opcional para uso do Polite Pool do OpenAlex (até 10 req/s)
openalex_polite_email = ""
# Chave da API da NVIDIA (NVIDIA NIM / build.nvidia.com)
nvidia_api_key = ""
# Chave de API do DeepSeek
deepseek_api_key = ""
# Chave de API da Anthropic Claude (também aceita ANTHROPIC_API_KEY via env)
claude_api_key = ""
# Chave de API da Groq
groq_api_key = ""
# Token de acesso do GitHub (também aceita GITHUB_TOKEN / GH_TOKEN via env)
github_token = ""
"""


def init_config_file(local: bool = False) -> Path:
    """Criar o arquivo config.toml comentado com permissão 0600.

    Quando local=True, escreve ./bibliotec.toml; caso contrário,
    escreve ~/.config/bibliotec/config.toml.
    """
    if local:
        target = Path.cwd() / LOCAL_CONFIG_FILENAME
    else:
        GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        target = GLOBAL_CONFIG_PATH

    content = generate_config_template()
    target.write_text(content, encoding="utf-8")
    os.chmod(target, CONFIG_FILE_MODE)
    return target
