"""Testes unitários do provedor NVIDIA NIM (tarefa [LLM-03]).

Mocka httpx com respx para evitar chamadas de rede reais. Cobrem:
  * classificação bem-sucedida com parsing JSON e validação CAPES/CNPq;
  * short-circuit para texto curto sem metadados;
  * retry em HTTP 429 e falha de rede;
  * reparo de grande_area / area_basica inválida;
  * teto de confiança para título genérico.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from bibliotec.core.llm import NvidiaProvider
from bibliotec.core.models import ExternalMetadata

BASE_URL = "https://integrate.api.nvidia.com/v1"


def _make_provider(api_key="test-key", model="meta/llama-3.2-90b-vision-instruct"):
    return NvidiaProvider(api_key=api_key, model=model)


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


def _mock_success(route, payload):
    route.mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": json.dumps(payload)}}]},
        )
    )


# ---------------------------------------------------------------------------
# 1. Classificação bem-sucedida
# ---------------------------------------------------------------------------


@respx.mock
def test_classificacao_sucesso_json_e_validacao_capes():
    payload = _classification_payload()
    route = respx.post(f"{BASE_URL}/chat/completions")
    _mock_success(route, payload)

    provider = _make_provider()
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para "
        "classificação do documento acadêmico sobre psicologia.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.grande_area == "Ciências Humanas"
    assert result.area_basica == "Psicologia"
    assert result.tipo == "Livro"
    assert result.authors == ["Silva, João"]
    assert result.title == "Psicologia Social"
    assert result.subtitle == "Uma introdução"
    assert result.year == 2021
    assert result.reasoning == "Classificação de teste"


# ---------------------------------------------------------------------------
# 2. Short-circuit texto curto sem metadados
# ---------------------------------------------------------------------------


def test_short_circuito_texto_curto_sem_metadados():
    provider = _make_provider()
    result = provider.classify(
        sampled_text="oi",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.0
    assert result.grande_area == ""
    assert result.area_basica == ""
    assert result.tipo == "Outros"
    assert "inferior a 50 caracteres" in result.reasoning


# ---------------------------------------------------------------------------
# 3. Retry em HTTP 429 e falha de rede
# ---------------------------------------------------------------------------


@respx.mock
def test_retry_em_429_then_sucesso():
    payload = _classification_payload()
    route = respx.post(f"{BASE_URL}/chat/completions")
    route.mock(
        side_effect=[
            httpx.Response(429, json={"error": "rate limited"}),
            httpx.Response(
                200,
                json={"choices": [{"message": {"content": json.dumps(payload)}}]},
            ),
        ]
    )

    provider = _make_provider()
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.grande_area == "Ciências Humanas"


@respx.mock
def test_falha_de_rede_retorna_confianca_zero():
    route = respx.post(f"{BASE_URL}/chat/completions")
    route.mock(side_effect=httpx.ConnectError("falha de conexão com a NVIDIA"))

    provider = _make_provider()
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.0
    assert "Falha na chamada ao LLM NVIDIA" in result.reasoning
    assert result.tipo == "Outros"


# ---------------------------------------------------------------------------
# 4. Reparo de grande_area / area_basica inválida
# ---------------------------------------------------------------------------


@respx.mock
def test_reparo_grande_area_invalida():
    # Psicologia pertence a Ciências Humanas; informe grande_area errada.
    payload = _classification_payload(grande_area="Engenharias")
    route = respx.post(f"{BASE_URL}/chat/completions")
    _mock_success(route, payload)

    provider = _make_provider()
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.grande_area == "Ciências Humanas"  # reparado automaticamente
    assert result.area_basica == "Psicologia"


@respx.mock
def test_par_irreparavel_forca_confianca_zero():
    payload = _classification_payload(
        grande_area="Não Existe", area_basica="Também Não Existe"
    )
    route = respx.post(f"{BASE_URL}/chat/completions")
    _mock_success(route, payload)

    provider = _make_provider()
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.0
    assert "irreparável" in result.reasoning


# ---------------------------------------------------------------------------
# 5. Teto de confiança para título genérico
# ---------------------------------------------------------------------------


@respx.mock
def test_teto_confianca_titulo_generico_sem_autor():
    payload = _classification_payload(
        title="sem título", confidence_score=0.90, authors=[]
    )
    route = respx.post(f"{BASE_URL}/chat/completions")
    _mock_success(route, payload)

    provider = _make_provider()
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.50


@respx.mock
def test_sem_teto_quando_titulo_generico_tem_autor():
    payload = _classification_payload(
        title="sem título", confidence_score=0.90, authors=["Silva, João"]
    )
    route = respx.post(f"{BASE_URL}/chat/completions")
    _mock_success(route, payload)

    provider = _make_provider()
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.90  # não aplica teto: há autor


# ---------------------------------------------------------------------------
# 6. Conteúdo JSON envolvido em markdown
# ---------------------------------------------------------------------------


@respx.mock
def test_resposta_embrulhada_em_markdown_json():
    payload = _classification_payload()
    markdown_content = "```json\n" + json.dumps(payload) + "\n```"
    route = respx.post(f"{BASE_URL}/chat/completions")
    route.mock(
        return_value=httpx.Response(
            200,
            json={"choices": [{"message": {"content": markdown_content}}]},
        )
    )

    provider = _make_provider()
    result = provider.classify(
        sampled_text="Texto de amostra com conteúdo suficiente para classificação.",
        cip_text="",
        external_metadata=None,
    )

    assert result.confidence_score == 0.92
    assert result.title == "Psicologia Social"


# ---------------------------------------------------------------------------
# 7. Cumpre o protocolo LLMProvider
# ---------------------------------------------------------------------------


def test_cumpre_protocolo_llm_provider():
    from bibliotec.core.llm import LLMProvider

    provider = _make_provider()
    assert isinstance(provider, LLMProvider)


@respx.mock
def test_usar_external_metadata_evita_short_circuito():
    """Texto curto, mas com metadados externos -> não short-circuita."""
    route = respx.post(f"{BASE_URL}/chat/completions")
    payload = _classification_payload()
    _mock_success(route, payload)

    provider = _make_provider()
    ext = ExternalMetadata(
        source="openalex",
        title="Psicologia Social",
        authors=["Silva, João"],
        match_score=0.95,
    )
    result = provider.classify(
        sampled_text="oi",
        cip_text="",
        external_metadata=ext,
    )

    # Chamou a API (não short-circuitou) e obteve classificação válida.
    assert result.confidence_score == 0.92
    assert result.title == "Psicologia Social"
