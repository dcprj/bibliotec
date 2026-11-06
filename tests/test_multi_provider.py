"""Testes de múltiplos provedores LLM (Sprint v0.2.0 - FAL-04 e TST-05).

Valida:
  * Instanciação de DeepSeekProvider e ClaudeProvider.
  * Mock de chamada com sucesso para DeepSeek e Claude.
  * FallbackLLMDispatcher: falha no provedor primário -> chaveamento automático para o fallback.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from bibliotec.core.llm import (
    ClaudeProvider,
    DeepSeekProvider,
    FallbackLLMDispatcher,
    GitHubModelsProvider,
    GroqProvider,
    NvidiaProvider,
    ClassificationResult,
    ExternalMetadata,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _classification_payload(**overrides):
    payload = {
        "grande_area": "Ciências Humanas",
        "area_basica": "Psicologia",
        "tipo": "Livro",
        "authors": ["Silva, João"],
        "title": "Psicologia Social",
        "subtitle": "Uma introdução",
        "year": 2021,
        "confidence_score": 0.92,
        "reasoning": "Classificação de teste",
    }
    payload.update(overrides)
    return payload


def _mock_success_openai(route, payload):
    """Mock no formato OpenAI (DeepSeek): choices[0].message.content."""
    route.mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
        )
    )


def _mock_success_claude(route, payload):
    """Mock no formato Anthropic (Claude): content[0].text."""
    route.mock(
        return_value=httpx.Response(
            200,
            json={"content": [{"text": json.dumps(payload)}]},
        )
    )


# --------------------------------------------------------------------------- #
# 1. Instanciação de DeepSeekProvider e ClaudeProvider
# --------------------------------------------------------------------------- #
def test_deepseek_provider_instancia():
    provider = DeepSeekProvider(api_key="test-key", model="deepseek-flash")
    assert provider is not None
    assert provider._model == "deepseek-flash"


def test_claude_provider_instancia():
    provider = ClaudeProvider(api_key="test-key", model="claude-3-5-haiku-20241022")
    assert provider is not None
    assert provider._model == "claude-3-5-haiku-20241022"


# --------------------------------------------------------------------------- #
# 2. Mock de chamada com sucesso para DeepSeek e Claude
# --------------------------------------------------------------------------- #
@respx.mock
def test_deepseek_chamada_sucesso():
    payload = _classification_payload()
    route = respx.post("https://api.deepseek.com/v1/chat/completions")
    _mock_success_openai(route, payload)

    provider = DeepSeekProvider(api_key="test-key")
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.grande_area == "Ciências Humanas"
    assert result.area_basica == "Psicologia"
    assert result.tipo == "Livro"
    assert result.title == "Psicologia Social"


@respx.mock
def test_claude_chamada_sucesso():
    payload = _classification_payload()
    route = respx.post("https://api.anthropic.com/v1/messages")
    _mock_success_claude(route, payload)

    provider = ClaudeProvider(api_key="test-key")
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.grande_area == "Ciências Humanas"
    assert result.area_basica == "Psicologia"
    assert result.tipo == "Livro"
    assert result.title == "Psicologia Social"


# --------------------------------------------------------------------------- #
# 2b. Instanciação de GroqProvider e GitHubModelsProvider
# --------------------------------------------------------------------------- #
def test_groq_provider_instancia():
    provider = GroqProvider(api_key="test-key", model="openai/gpt-oss-120b")
    assert provider is not None
    assert provider._model == "openai/gpt-oss-120b"


def test_github_models_provider_instancia():
    provider = GitHubModelsProvider(api_key="test-key", model="openai/gpt-4o")
    assert provider is not None
    assert provider._model == "openai/gpt-4o"


# --------------------------------------------------------------------------- #
# 2c. Mock de chamada com sucesso para Groq e GitHub Models
# --------------------------------------------------------------------------- #
@respx.mock
def test_groq_chamada_sucesso():
    payload = _classification_payload()
    route = respx.post("https://api.groq.com/openai/v1/chat/completions")
    _mock_success_openai(route, payload)

    provider = GroqProvider(api_key="test-key")
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.grande_area == "Ciências Humanas"
    assert result.area_basica == "Psicologia"
    assert result.tipo == "Livro"
    assert result.title == "Psicologia Social"


@respx.mock
def test_github_models_chamada_sucesso():
    payload = _classification_payload()
    route = respx.post("https://models.github.ai/inference/chat/completions")
    _mock_success_openai(route, payload)

    provider = GitHubModelsProvider(api_key="test-key")
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.grande_area == "Ciências Humanas"
    assert result.area_basica == "Psicologia"
    assert result.tipo == "Livro"
    assert result.title == "Psicologia Social"


# --------------------------------------------------------------------------- #
# 3. FallbackLLMDispatcher: falha no primário -> chaveamento para o fallback
# --------------------------------------------------------------------------- #
@respx.mock
def test_fallback_dispatcher_primario_falha_secundario_sucesso():
    """Provedor primário lança exceção; fallback responde com sucesso."""
    payload = _classification_payload(reasoning="Classificação via fallback.")

    # Primário: sempre falha com 429.
    rota_primario = respx.post("https://api.deepseek.com/v1/chat/completions")
    rota_primario.mock(side_effect=httpx.ConnectError("conexão recusada"))

    # Secundário: responde com sucesso.
    rota_fallback = respx.post("https://api.anthropic.com/v1/messages")
    _mock_success_claude(rota_fallback, payload)

    primario = DeepSeekProvider(api_key="test-key")
    fallback = ClaudeProvider(api_key="test-key")

    dispatcher = FallbackLLMDispatcher([("deepseek", primario), ("claude", fallback)])

    assert dispatcher.primary_name == "deepseek"
    assert dispatcher.provider_names == ["deepseek", "claude"]

    result = dispatcher.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.grande_area == "Ciências Humanas"
    assert result.title == "Psicologia Social"


@respx.mock
def test_fallback_dispatcher_todos_falham_retorna_ultimo_erro():
    """Todos os provedores falham; dispatcher retorna o último erro."""
    # Primário: falha com exceção.
    rota_primario = respx.post("https://api.deepseek.com/v1/chat/completions")
    rota_primario.mock(side_effect=httpx.ConnectError("conexão recusada"))

    # Secundário: também falha com exceção.
    rota_fallback = respx.post("https://api.anthropic.com/v1/messages")
    rota_fallback.mock(side_effect=httpx.ConnectError("timeout"))

    primario = DeepSeekProvider(api_key="test-key")
    fallback = ClaudeProvider(api_key="test-key")

    dispatcher = FallbackLLMDispatcher([("deepseek", primario), ("claude", fallback)])

    result = dispatcher.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.0
    assert "Falha na chamada ao LLM" in result.reasoning


@respx.mock
def test_fallback_dispatcher_primario_retorna_erro_rede_secundario_sucesso():
    """Provedor primário retorna resultado com 'Falha na chamada ao LLM'; fallback responde."""
    erro_payload = _classification_payload(
        reasoning="Falha na chamada ao LLM DeepSeek: timeout",
        confidence_score=0.0,
    )
    rota_primario = respx.post("https://api.deepseek.com/v1/chat/completions")
    _mock_success_openai(rota_primario, erro_payload)

    ok_payload = _classification_payload(reasoning="Classificação via Claude fallback.")
    rota_fallback = respx.post("https://api.anthropic.com/v1/messages")
    _mock_success_claude(rota_fallback, ok_payload)

    primario = DeepSeekProvider(api_key="test-key")
    fallback = ClaudeProvider(api_key="test-key")

    dispatcher = FallbackLLMDispatcher([("deepseek", primario), ("claude", fallback)])

    result = dispatcher.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.reasoning == "Classificação via Claude fallback."


@respx.mock
def test_fallback_dispatcher_groq_falha_github_sucesso():
    """Provedor primário Groq falha; GitHub Models responde com sucesso."""
    erro_payload = _classification_payload(
        reasoning="Falha na chamada ao LLM Groq: timeout",
        confidence_score=0.0,
    )
    rota_primario = respx.post("https://api.groq.com/openai/v1/chat/completions")
    _mock_success_openai(rota_primario, erro_payload)

    ok_payload = _classification_payload(reasoning="Classificação via GitHub Models fallback.")
    rota_fallback = respx.post("https://models.github.ai/inference/chat/completions")
    _mock_success_openai(rota_fallback, ok_payload)

    primario = GroqProvider(api_key="test-key")
    fallback = GitHubModelsProvider(api_key="test-key")

    dispatcher = FallbackLLMDispatcher([("groq", primario), ("github", fallback)])

    assert dispatcher.primary_name == "groq"
    assert dispatcher.provider_names == ["groq", "github"]

    result = dispatcher.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.reasoning == "Classificação via GitHub Models fallback."