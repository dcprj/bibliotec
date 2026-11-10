"""Classificador LLM com protocolo extensível e provedores múltiplos (Item 18).

Declara o Protocol LLMProvider, aplica short-circuit antes da chamada de rede
quando o texto alfanumérico útil for < 50 caracteres e não houver
ExternalMetadata (confidence_score = 0.0), implementa múltiplos provedores
(Gemini, NVIDIA, DeepSeek, Claude, Groq, GitHub Models) com saída estruturada,
retry em HTTP 429/503, validação de par (grande_area, area_basica) via
validate_or_repair_pair forçando confidence_score = 0.0 quando retornar None, e
aplica o teto min(score, 0.50) quando o título for vazio/genérico sem autor
identável.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from tomus.core.models import ExternalMetadata, LLMClassificationOutput
from tomus.core.prompts import (
    build_context_payload,
    build_system_prompt,
    is_generic_title,
)
from tomus.core.taxonomy import validate_or_repair_pair

# Limite de texto alfanumérico útil abaixo do qual ocorre short-circuit.
MIN_USEFUL_CHARS = 50

# Teto de confiança quando o título é vazio/genérico sem autor identificável.
GENERIC_TITLE_CONFIDENCE_CAP = 0.50

# Limiar de confiança para organização automática.
CONFIDENCE_MIN = 0.70

def _alphanumeric_count(text: str) -> int:
    """Contar caracteres alfanuméricos úteis em um texto."""
    return sum(1 for ch in text if ch.isalnum())


def _is_retryable_http(exc: BaseException) -> bool:
    """Verificar se uma exceção do google-genai é um erro HTTP retryable (429/503)."""
    code = getattr(exc, "code", None)
    if code is None:
        response = getattr(exc, "response", None)
        if response is not None:
            code = getattr(response, "status_code", None)
    try:
        return int(code) in (429, 503)
    except (TypeError, ValueError):
        return False


def _retry_on_retryable_http():
    """Decorador de retry para erros HTTP retryable (429 e 503)."""
    return retry(
        retry=retry_if_exception(_is_retryable_http),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )


def _is_generic_openai_retryable(exc: BaseException) -> bool:
    """Verificar se uma exceção httpx é transitória (429/503/529 ou falha de transporte/timeout)."""
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 503, 529)
    return False


def _strip_markdown_json(text: str) -> str:
    """Remover eventuais blocos markdown (```json ... ```) da resposta."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
    if text.endswith("```"):
        text = text.rsplit("\n", 1)[0] if "\n" in text else text
    text = text.strip()
    if text.startswith("json"):
        text = text[4:].strip()
    return text


@dataclass
class ClassificationResult:
    """Resultado da classificação de um documento."""

    grande_area: str
    area_basica: str
    tipo: str
    authors: list[str]
    title: str
    subtitle: str
    year: int | None
    confidence_score: float
    reasoning: str
    used_ocr: bool = False
    provider_name: str = ""
    model_name: str = ""
    publisher: str | None = None
    city: str | None = None
    edition: str | None = None
    journal_name: str | None = None
    volume: str | None = None
    number: str | None = None
    pages: str | None = None
    doi: str | None = None
    isbn: str | None = None


def _check_short_circuit(
    sampled_text: str,
    cip_text: str,
    external_metadata: ExternalMetadata | None,
    used_ocr: bool,
    provider_name: str = "",
    model_name: str = "",
) -> ClassificationResult | None:
    """Retornar ClassificationResult de short-circuit se texto útil < 50 chars e sem metadados externos."""
    useful_chars = _alphanumeric_count(sampled_text) + _alphanumeric_count(cip_text)
    has_external = external_metadata is not None and bool(
        external_metadata.title or external_metadata.authors
    )
    if useful_chars < MIN_USEFUL_CHARS and not has_external:
        return ClassificationResult(
            grande_area="",
            area_basica="",
            tipo="Outros",
            authors=[],
            title="",
            subtitle="",
            year=None,
            confidence_score=0.0,
            reasoning=(
                "Texto alfanumérico útil inferior a 50 caracteres e sem "
                "metadados externos; classificação não realizada."
            ),
            used_ocr=used_ocr,
            provider_name=provider_name,
            model_name=model_name,
        )
    return None


def _finalize_classification(
    output: LLMClassificationOutput,
    used_ocr: bool,
    provider_name: str = "",
    model_name: str = "",
) -> ClassificationResult:
    """Aplicar validação/reparo CAPES e trava determinística de título genérico."""
    reparado = validate_or_repair_pair(output.grande_area, output.area_basica)
    tipo_str = output.tipo.value if hasattr(output.tipo, "value") else str(output.tipo)
    if reparado is None:
        return ClassificationResult(
            grande_area=output.grande_area,
            area_basica=output.area_basica,
            tipo=tipo_str,
            authors=list(output.authors),
            title=output.title,
            subtitle=output.subtitle,
            year=output.year,
            publisher=output.publisher,
            city=output.city,
            edition=output.edition,
            journal_name=output.journal_name,
            volume=output.volume,
            number=output.number,
            pages=output.pages,
            doi=output.doi,
            isbn=output.isbn,
            confidence_score=0.0,
            reasoning=(
                f"{output.reasoning} Par (grande_area, area_basica) irreparável "
                f"contra o catálogo CAPES/CNPq."
            ),
            used_ocr=used_ocr,
            provider_name=provider_name,
            model_name=model_name,
        )
    grande_area, area_basica = reparado

    confidence = float(output.confidence_score)
    title = output.title or ""
    has_authors = bool(output.authors)
    if is_generic_title(title) and not has_authors:
        confidence = min(confidence, GENERIC_TITLE_CONFIDENCE_CAP)

    return ClassificationResult(
        grande_area=grande_area,
        area_basica=area_basica,
        tipo=tipo_str,
        authors=list(output.authors),
        title=title,
        subtitle=output.subtitle,
        year=output.year,
        publisher=output.publisher,
        city=output.city,
        edition=output.edition,
        journal_name=output.journal_name,
        volume=output.volume,
        number=output.number,
        pages=output.pages,
        doi=output.doi,
        isbn=output.isbn,
        confidence_score=confidence,
        reasoning=output.reasoning,
        used_ocr=used_ocr,
        provider_name=provider_name,
        model_name=model_name,
    )


@runtime_checkable
class LLMProvider(Protocol):
    """Protocolo de classificação de documentos por modelo de linguagem."""

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar um documento e retornar o resultado estruturado."""
        ...


class GeminiProvider:
    """Provedor Gemini usando google-genai com saída estruturada."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash",
        max_sampled_chars: int = 15_000,
    ) -> None:
        from google.genai import Client
        from google.genai import types as genai_types

        self._client = Client(api_key=api_key)
        self._model = model
        self._max_sampled_chars = max_sampled_chars
        self._types = genai_types
        self._fallback_models = ["gemini-3.5-flash", "gemini-3.1-flash-lite"]

    def _is_404(self, exc: BaseException) -> bool:
        """Verificar se uma exceção do google-genai é um erro HTTP 404 (NOT_FOUND)."""
        code = getattr(exc, "code", None)
        try:
            return int(code) == 404
        except (TypeError, ValueError):
            return False

    @retry(
        retry=retry_if_exception(_is_retryable_http),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_gemini(
        self,
        system_prompt: str,
        context_payload: str,
    ) -> LLMClassificationOutput:
        """Chamar a API Gemini com saída estruturada e retry HTTP 429/503, com fallback em HTTP 404."""
        config = self._types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=LLMClassificationOutput,
            temperature=0.1,
        )
        ultimo_erro: Exception | None = None
        modelos_a_tentar = [self._model] + [
            m for m in self._fallback_models if m != self._model
        ]
        for modelo in modelos_a_tentar:
            try:
                response = self._client.models.generate_content(
                    model=modelo,
                    contents=context_payload,
                    config=config,
                )
                parsed = response.parsed
                if parsed is None:
                    raise ValueError("Resposta do Gemini não pôde ser interpretada como JSON")
                if not isinstance(parsed, LLMClassificationOutput):
                    parsed = LLMClassificationOutput.model_validate(parsed)
                return parsed
            except Exception as exc:
                ultimo_erro = exc
                if self._is_404(exc):
                    continue
                if _is_retryable_http(exc):
                    continue
                raise
        raise ultimo_erro or RuntimeError("Falha ao chamar a API Gemini")

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar via Gemini aplicando travas determinísticas de confiança."""
        short = _check_short_circuit(
            sampled_text, cip_text, external_metadata, used_ocr, "gemini", self._model
        )
        if short is not None:
            return short

        system_prompt = build_system_prompt()
        context_payload = build_context_payload(sampled_text, cip_text, external_metadata)

        try:
            output = self._call_gemini(system_prompt, context_payload)
        except Exception as exc:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=f"Falha na chamada ao LLM: {exc}",
                used_ocr=used_ocr,
                provider_name="gemini",
                model_name=self._model,
            )

        return _finalize_classification(output, used_ocr, "gemini", self._model)


class MockLLMProvider:
    """Provedor de teste determinístico (não requer rede)."""

    def __init__(self, result: ClassificationResult | None = None) -> None:
        self._result = result or ClassificationResult(
            grande_area="Ciências Humanas",
            area_basica="Psicologia",
            tipo="Livro",
            authors=["Silva, João"],
            title="Título de teste",
            subtitle="",
            year=2020,
            confidence_score=0.90,
            reasoning="mock",
        )

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        return self._result


class NvidiaProvider:
    """Provedor NVIDIA NIM usando httpx diretamente."""

    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/nemotron-3.5-lightning-30b-a3b",
        base_url: str = "https://integrate.api.nvidia.com/v1",
        max_sampled_chars: int = 15_000,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        self._model = model
        self._max_sampled_chars = max_sampled_chars

    @retry(
        retry=retry_if_exception(_is_generic_openai_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_nvidia(self, system_prompt: str, context_payload: str) -> str:
        """Chamar a API NVIDIA NIM /chat/completions com retry em 429/503."""
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    + "\n\nResponda APENAS com um objeto JSON válido estritamente no schema solicitado, sem marcação markdown adicional.",
                },
                {"role": "user", "content": context_payload},
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
        }
        resp = self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        msg = choice.get("message", {})
        content = msg.get("content")
        if not content or not str(content).strip():
            reasoning = msg.get("reasoning_content")
            if reasoning and "{" in reasoning and "}" in reasoning:
                content = reasoning
            else:
                raise ValueError("Resposta do LLM NVIDIA veio vazia")
        return str(content)

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar via NVIDIA NIM aplicando travas determinísticas de confiança."""
        useful_chars = _alphanumeric_count(sampled_text) + _alphanumeric_count(cip_text)
        has_external = external_metadata is not None and bool(
            external_metadata.title or external_metadata.authors
        )
        if useful_chars < MIN_USEFUL_CHARS and not has_external:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=(
                    "Texto alfanumérico útil inferior a 50 caracteres e sem "
                    "metadados externos; classificação não realizada."
                ),
                used_ocr=used_ocr,
            )

        system_prompt = build_system_prompt()
        context_payload = build_context_payload(sampled_text, cip_text, external_metadata)

        try:
            content = self._call_nvidia(system_prompt, context_payload)
        except Exception as exc:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=f"Falha na chamada ao LLM NVIDIA: {exc}",
                used_ocr=used_ocr,
            )

        json_text = _strip_markdown_json(content)
        try:
            output = LLMClassificationOutput.model_validate_json(json_text)
        except Exception:
            output = LLMClassificationOutput.model_validate(json.loads(json_text))

        return _finalize_classification(output, used_ocr, "nvidia", self._model)


class DeepSeekProvider:
    """Provedor DeepSeek usando httpx diretamente.

    Chama a API DeepSeek em POST /chat/completions e aplica travas
    determinísticas de confiança idênticas às do NvidiaProvider.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "deepseek-flash",
        base_url: str = "https://api.deepseek.com/v1",
        max_sampled_chars: int = 15_000,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        self._model = model
        self._max_sampled_chars = max_sampled_chars

    @retry(
        retry=retry_if_exception(_is_generic_openai_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_deepseek(self, system_prompt: str, context_payload: str) -> str:
        """Chamar a API DeepSeek /chat/completions com retry em 429/503."""
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    + "\n\nResponda APENAS com um objeto JSON válido estritamente no schema solicitado, sem marcação markdown adicional.",
                },
                {"role": "user", "content": context_payload},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        }
        resp = self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content")
        if not content or not str(content).strip():
            raise ValueError("Resposta do LLM DeepSeek veio vazia")
        return str(content)

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar via DeepSeek aplicando travas determinísticas de confiança."""
        useful_chars = _alphanumeric_count(sampled_text) + _alphanumeric_count(cip_text)
        has_external = external_metadata is not None and bool(
            external_metadata.title or external_metadata.authors
        )
        if useful_chars < MIN_USEFUL_CHARS and not has_external:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=(
                    "Texto alfanumérico útil inferior a 50 caracteres e sem "
                    "metadados externos; classificação não realizada."
                ),
                used_ocr=used_ocr,
            )

        system_prompt = build_system_prompt()
        context_payload = build_context_payload(sampled_text, cip_text, external_metadata)

        try:
            content = self._call_deepseek(system_prompt, context_payload)
        except Exception as exc:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=f"Falha na chamada ao LLM DeepSeek: {exc}",
                used_ocr=used_ocr,
            )

        json_text = _strip_markdown_json(content)
        try:
            output = LLMClassificationOutput.model_validate_json(json_text)
        except Exception:
            output = LLMClassificationOutput.model_validate(json.loads(json_text))

        return _finalize_classification(output, used_ocr, "deepseek", self._model)

class ClaudeProvider:
    """Provedor Anthropic Claude usando httpx diretamente."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-20241022",
        base_url: str = "https://api.anthropic.com/v1",
        max_sampled_chars: int = 15_000,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            timeout=60.0,
        )
        self._model = model
        self._max_sampled_chars = max_sampled_chars

    @retry(
        retry=retry_if_exception(_is_generic_openai_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_claude(self, system_prompt: str, context_payload: str) -> str:
        """Chamar a API Anthropic /messages com retry em 429/529/503."""
        payload = {
            "model": self._model,
            "max_tokens": 2048,
            "system": system_prompt
            + "\nResponda APENAS com um objeto JSON válido estritamente no schema solicitado, sem marcação markdown adicional.",
            "messages": [{"role": "user", "content": context_payload}],
        }
        resp = self._client.post("/messages", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar via Anthropic Claude aplicando travas determinísticas de confiança."""
        useful_chars = _alphanumeric_count(sampled_text) + _alphanumeric_count(cip_text)
        has_external = external_metadata is not None and bool(
            external_metadata.title or external_metadata.authors
        )
        if useful_chars < MIN_USEFUL_CHARS and not has_external:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=(
                    "Texto alfanumérico útil inferior a 50 caracteres e sem "
                    "metadados externos; classificação não realizada."
                ),
                used_ocr=used_ocr,
            )

        system_prompt = build_system_prompt()
        context_payload = build_context_payload(sampled_text, cip_text, external_metadata)

        try:
            content = self._call_claude(system_prompt, context_payload)
        except Exception as exc:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=f"Falha na chamada ao LLM Claude: {exc}",
                used_ocr=used_ocr,
            )

        json_text = _strip_markdown_json(content)
        try:
            output = LLMClassificationOutput.model_validate_json(json_text)
        except Exception:
            output = LLMClassificationOutput.model_validate(json.loads(json_text))

        return _finalize_classification(output, used_ocr, "claude", self._model)


class GroqProvider:
    """Provedor Groq (OpenAI-compatível) usando httpx diretamente.

    Chama a API Groq em POST /chat/completions e aplica travas
    determinísticas de confiança idênticas às dos demais provedores.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-oss-20b",
        base_url: str = "https://api.groq.com/openai/v1",
        max_sampled_chars: int = 15_000,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        self._model = model
        self._max_sampled_chars = max_sampled_chars

    @retry(
        retry=retry_if_exception(_is_generic_openai_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_groq(self, system_prompt: str, context_payload: str) -> str:
        """Chamar a API Groq /chat/completions com retry em 429/503."""
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    + "\n\nResponda APENAS com um objeto JSON válido estritamente no schema solicitado, sem marcação markdown adicional.",
                },
                {"role": "user", "content": context_payload},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"},
        }
        resp = self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content")
        if not content or not str(content).strip():
            raise ValueError("Resposta do LLM Groq veio vazia")
        return str(content)

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar via Groq aplicando travas determinísticas de confiança."""
        useful_chars = _alphanumeric_count(sampled_text) + _alphanumeric_count(cip_text)
        has_external = external_metadata is not None and bool(
            external_metadata.title or external_metadata.authors
        )
        if useful_chars < MIN_USEFUL_CHARS and not has_external:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=(
                    "Texto alfanumérico útil inferior a 50 caracteres e sem "
                    "metadados externos; classificação não realizada."
                ),
                used_ocr=used_ocr,
            )

        system_prompt = build_system_prompt()
        context_payload = build_context_payload(sampled_text, cip_text, external_metadata)

        try:
            content = self._call_groq(system_prompt, context_payload)
        except Exception as exc:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=f"Falha na chamada ao LLM Groq: {exc}",
                used_ocr=used_ocr,
            )

        json_text = _strip_markdown_json(content)
        try:
            output = LLMClassificationOutput.model_validate_json(json_text)
        except Exception:
            output = LLMClassificationOutput.model_validate(json.loads(json_text))

        return _finalize_classification(output, used_ocr, "groq", self._model)


class GitHubModelsProvider:
    """Provedor GitHub Models usando httpx diretamente.

    Chama a API GitHub Models em POST /chat/completions e aplica travas
    determinísticas de confiança idênticas às dos demais provedores.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "https://models.github.ai/inference",
        max_sampled_chars: int = 15_000,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )
        self._model = model
        self._max_sampled_chars = max_sampled_chars

    @retry(
        retry=retry_if_exception(_is_generic_openai_retryable),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_github_models(self, system_prompt: str, context_payload: str) -> str:
        """Chamar a API GitHub Models /chat/completions com retry em 429/503."""
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    + "\n\nResponda APENAS com um objeto JSON válido estritamente no schema solicitado, sem marcação markdown adicional.",
                },
                {"role": "user", "content": context_payload},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
            "response_format": {"type": "json_object"},
        }
        resp = self._client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = resp.json()
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content")
        if not content or not str(content).strip():
            raise ValueError("Resposta do LLM GitHub Models veio vazia")
        return str(content)

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar via GitHub Models aplicando travas determinísticas de confiança."""
        useful_chars = _alphanumeric_count(sampled_text) + _alphanumeric_count(cip_text)
        has_external = external_metadata is not None and bool(
            external_metadata.title or external_metadata.authors
        )
        if useful_chars < MIN_USEFUL_CHARS and not has_external:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=(
                    "Texto alfanumérico útil inferior a 50 caracteres e sem "
                    "metadados externos; classificação não realizada."
                ),
                used_ocr=used_ocr,
            )

        system_prompt = build_system_prompt()
        context_payload = build_context_payload(sampled_text, cip_text, external_metadata)

        try:
            content = self._call_github_models(system_prompt, context_payload)
        except Exception as exc:
            return ClassificationResult(
                grande_area="",
                area_basica="",
                tipo="Outros",
                authors=[],
                title="",
                subtitle="",
                year=None,
                confidence_score=0.0,
                reasoning=f"Falha na chamada ao LLM GitHub Models: {exc}",
                used_ocr=used_ocr,
            )

        json_text = _strip_markdown_json(content)
        try:
            output = LLMClassificationOutput.model_validate_json(json_text)
        except Exception:
            output = LLMClassificationOutput.model_validate(json.loads(json_text))

        return _finalize_classification(output, used_ocr, "github", self._model)


# --------------------------------------------------------------------------- #
# FallbackLLMDispatcher e fábrica de cadeia de provedores
# --------------------------------------------------------------------------- #
import logging  # noqa: E402

_llm_logger = logging.getLogger("tomus.llm")


class FallbackLLMDispatcher:
    """Despachante de provedores LLM com fallback automático.

    Implementa o protocolo :class:`LLMProvider`. Recebe uma cadeia ordenada de
    tuplas ``(nome_provedor, instancia_provedor)``. O primeiro é o provedor
    primário; os demais são fallbacks tentados em ordem quando o anterior
    falha (exceção ou resultado com reasoning contendo 'Falha na chamada ao
    LLM').

    Quando todos os provedores falham, retorna o último resultado de falha.
    """

    def __init__(self, providers: list[tuple[str, object]]) -> None:
        if not providers:
            raise ValueError("FallbackLLMDispatcher requer pelo menos um provedor.")
        self._providers: list[tuple[str, object]] = providers

    @property
    def primary_name(self) -> str:
        """Retornar o nome do provedor primário."""
        return self._providers[0][0]

    @property
    def provider_names(self) -> list[str]:
        """Retornar a lista ordenada de nomes dos provedores na cadeia."""
        return [nome for nome, _ in self._providers]

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar tentando os provedores em ordem até obter sucesso.

        Se um provedor levantar exceção ou retornar resultado com
        reasoning contendo 'Falha na chamada ao LLM', loga um warning e
        tenta o próximo da cadeia.
        """
        ultimo_resultado: ClassificationResult | None = None
        ultimo_erro: str | None = None

        for indice, (nome, provedor) in enumerate(self._providers):
            try:
                resultado = provedor.classify(
                    sampled_text=sampled_text,
                    cip_text=cip_text,
                    external_metadata=external_metadata,
                    used_ocr=used_ocr,
                )
            except Exception as exc:
                ultimo_erro = str(exc)
                proximo = (
                    self._providers[indice + 1][0]
                    if indice + 1 < len(self._providers)
                    else "nenhum (último)"
                )
                _llm_logger.warning(
                    "Provedor %s falhou: %s. Tentando fallback para %s...",
                    nome,
                    exc,
                    proximo,
                )
                ultimo_resultado = ClassificationResult(
                    grande_area="",
                    area_basica="",
                    tipo="Outros",
                    authors=[],
                    title="",
                    subtitle="",
                    year=None,
                    confidence_score=0.0,
                    reasoning=f"Falha na chamada ao LLM {nome}: {exc}",
                    used_ocr=used_ocr,
                )
                continue

            # Resultado de erro de rede/API: reasoning começa com
            # 'Falha na chamada ao LLM ...' -> tenta o próximo provedor.
            if resultado.reasoning.startswith("Falha na chamada ao LLM"):
                ultimo_erro = resultado.reasoning
                proximo = (
                    self._providers[indice + 1][0]
                    if indice + 1 < len(self._providers)
                    else "nenhum (último)"
                )
                _llm_logger.warning(
                    "Provedor %s falhou: %s. Tentando fallback para %s...",
                    nome,
                    resultado.reasoning,
                    proximo,
                )
                ultimo_resultado = resultado
                continue

            # Sucesso: preenche provider/model efetivos se ausentes e retorna.
            if not resultado.provider_name:
                resultado.provider_name = nome
            if not resultado.model_name:
                resultado.model_name = str(getattr(provedor, "_model", ""))
            return resultado

        # Todos os provedores falharam: retornar o último resultado de erro.
        if ultimo_resultado is not None:
            return ultimo_resultado
        return ClassificationResult(
            grande_area="",
            area_basica="",
            tipo="Outros",
            authors=[],
            title="",
            subtitle="",
            year=None,
            confidence_score=0.0,
            reasoning=f"Falha na chamada ao LLM: {ultimo_erro or 'provedor desconhecido'}",
            used_ocr=used_ocr,
        )


def create_provider_chain(
    config: AppConfig,
    *,
    cli_provider: str | None = None,
    cli_model: str | None = None,
    cli_api_key: str | None = None,
) -> LLMProvider:
    """Criar uma cadeia de provedores LLM com fallback automático.

    Parâmetros:
        config: configuração ativa (AppConfig).
        cli_provider: provedor solicitado via CLI (sobrescreve config).
        cli_model: modelo solicitado via CLI (sobrescreve config).
        cli_api_key: chave de API via CLI (sobrescreve config e env).

    A cadeia usa o provedor especificado pelo usuário como primário e inclui
    como fallback os demais provedores que tiverem chave de API configurada.
    Se o primário não tiver chave, o primeiro com chave válida torna-se o
    primário efetivo.

    Suporta: "gemini", "nvidia", "deepseek", "claude", "groq", "github".
    """
    provedores_disponiveis: dict[str, dict[str, Any]] = {
        "gemini": {
            "classe": GeminiProvider,
            "chave": config.api_keys.gemini_api_key,
            "modelo_padrao": "gemini-3.5-flash",
            "chave_env": ("TOMUS_GEMINI_API_KEY", "GEMINI_API_KEY"),
        },
        "groq": {
            "classe": GroqProvider,
            "chave": config.api_keys.groq_api_key,
            "modelo_padrao": "openai/gpt-oss-20b",
            "chave_env": ("TOMUS_GROQ_API_KEY", "GROQ_API_KEY"),
        },
        "nvidia": {
            "classe": NvidiaProvider,
            "chave": config.api_keys.nvidia_api_key,
            "modelo_padrao": "nvidia/nemotron-3.5-lightning-30b-a3b",
            "chave_env": ("TOMUS_NVIDIA_API_KEY", "NVIDIA_API_KEY"),
        },
        "deepseek": {
            "classe": DeepSeekProvider,
            "chave": config.api_keys.deepseek_api_key,
            "modelo_padrao": "deepseek-flash",
            "chave_env": ("TOMUS_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"),
        },
        "claude": {
            "classe": ClaudeProvider,
            "chave": config.api_keys.claude_api_key,
            "modelo_padrao": "claude-3-5-haiku-20241022",
            "chave_env": (
                "TOMUS_CLAUDE_API_KEY",
                "CLAUDE_API_KEY",
                "ANTHROPIC_API_KEY",
            ),
        },
        "github": {
            "classe": GitHubModelsProvider,
            "chave": config.api_keys.github_token,
            "modelo_padrao": "gpt-4o",
            "chave_env": ("TOMUS_GITHUB_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"),
        },
    }

    def _resolver_chave(nome_provedor: str, cli_key: str | None) -> str | None:
        """Resolver a chave de API: CLI > env > config."""
        if cli_key:
            return cli_key
        info = provedores_disponiveis[nome_provedor]
        for env_var in info["chave_env"]:
            valor = os.environ.get(env_var, "")
            if valor:
                return valor
        return info["chave"] or None

    def _resolver_modelo(nome_provedor: str, cli_model_val: str | None) -> str:
        """Resolver o modelo: CLI > [llm.providers.<nome>].model > config.llm.model > padrão."""
        if cli_model_val:
            return cli_model_val
        prov_cfg = (config.llm.providers or {}).get(nome_provedor, {})
        if isinstance(prov_cfg, dict) and prov_cfg.get("model"):
            return str(prov_cfg["model"])
        if config.llm.provider == nome_provedor and config.llm.model:
            return config.llm.model
        return provedores_disponiveis[nome_provedor]["modelo_padrao"]

    # Determinar provedor primário: CLI > config.llm.provider > "gemini".
    provedor_solicitado = cli_provider or config.llm.provider or "gemini"
    if provedor_solicitado not in provedores_disponiveis:
        provedor_solicitado = "gemini"

    # Construir cadeia: começar com o solicitado, depois os demais com chave.
    cadeia: list[tuple[str, object]] = []
    nomes_vistos: set[str] = set()

    def _adicionar_provedor(
        nome: str, usar_cli_key: bool, usar_cli_model: bool
    ) -> None:
        if nome in nomes_vistos:
            return
        info = provedores_disponiveis[nome]
        chave = _resolver_chave(nome, cli_api_key if usar_cli_key else None)
        if not chave:
            return  # sem chave: não adicionar
        modelo = _resolver_modelo(nome, cli_model if usar_cli_model else None)
        instancia = info["classe"](api_key=chave, model=modelo)
        cadeia.append((nome, instancia))
        nomes_vistos.add(nome)

    # Primeiro: o provedor solicitado pelo usuário (se tiver chave).
    _adicionar_provedor(
        provedor_solicitado,
        usar_cli_key=(cli_provider is not None),
        usar_cli_model=(cli_model is not None),
    )

    # Depois: os demais da cadeia de fallback do config (se houver chave).
    for nome in config.llm.fallback_chain:
        if nome != provedor_solicitado:
            _adicionar_provedor(nome, usar_cli_key=False, usar_cli_model=False)

    # Se o solicitado não teve chave, garantir pelo menos um com chave.
    if not cadeia:
        for nome in ("gemini", "nvidia", "deepseek", "claude", "groq", "github"):
            _adicionar_provedor(nome, usar_cli_key=False, usar_cli_model=False)
            if cadeia:
                break

    if not cadeia:
        raise ValueError(
            "Nenhum provedor de LLM tem chave de API configurada. "
            "Defina gemini_api_key, nvidia_api_key, deepseek_api_key, "
            "claude_api_key, groq_api_key ou github_token no config.toml "
            "ou variáveis de ambiente."
        )

    return FallbackLLMDispatcher(cadeia)
