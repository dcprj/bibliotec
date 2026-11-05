"""Classificador LLM com protocolo extensível e provedor Gemini (Item 18).

Declara o Protocol LLMProvider, aplica short-circuit antes da chamada de rede
quando o texto alfanumérico útil for < 50 caracteres e não houver
ExternalMetadata (confidence_score = 0.0), implementa GeminiProvider usando
google-genai (response_mime_type='application/json',
response_schema=LLMClassificationOutput) com retry em HTTP 429, valida o par
(grande_area, area_basica) via validate_or_repair_pair forçando
confidence_score = 0.0 quando retornar None, e aplica o teto
min(score, 0.50) quando o título for vazio/genérico sem autor identificável.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from bibliotec.core.models import ExternalMetadata, LLMClassificationOutput
from bibliotec.core.prompts import (
    build_context_payload,
    build_system_prompt,
    is_generic_title,
)
from bibliotec.core.taxonomy import validate_or_repair_pair

# Limite de texto alfanumérico útil abaixo do qual ocorre short-circuit.
MIN_USEFUL_CHARS = 50

# Teto de confiança quando o título é vazio/genérico sem autor identificável.
GENERIC_TITLE_CONFIDENCE_CAP = 0.50

# Limiar de confiança para organização automática.
CONFIDENCE_MIN = 0.70

# Prefixos que indicam título genérico de exportação de escritório.
_GENERIC_PREFIXES = ("microsoft powerpoint -", "microsoft word -")
_GENERIC_TITLES = {
    "sem título", "sem titulo", "untitled", "unknown", "desconhecido",
    "documento", "pdf", "artigo", "livro", "slide",
}


def _alphanumeric_count(text: str) -> int:
    """Contar caracteres alfanuméricos úteis em um texto."""
    return sum(1 for ch in text if ch.isalnum())


def _is_retryable_http(exc: BaseException) -> bool:
    """Verificar se uma exceção do google-genai é um erro HTTP retryable.

    Retorna True para HTTP 429 (RESOURCE_EXHAUSTED - rate limit) e
    HTTP 503 (UNAVAILABLE - 'This model is currently experiencing high demand'),
    pois a API do Gemini retorna 503 em picos de demanda.
    """
    code = getattr(exc, "code", None)
    if code is None:
        # Tentar extrair do corpo da resposta quando disponível.
        response = getattr(exc, "response", None)
        if response is not None:
            code = getattr(response, "status_code", None)
    try:
        return int(code) in (429, 503)
    except (TypeError, ValueError):
        return False


def _retry_on_retryable_http():
    """Decorador de retry para erros HTTP retryable (429 e 503).

    Usa backoff exponencial (multiplier=1, min=2s, max=10s) com até 4 tentativas.
    """
    return retry(
        retry=retry_if_exception(_is_retryable_http),
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )


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
        model: str = "gemini-3.8-flash",
        max_sampled_chars: int = 15_000,
    ) -> None:
        from google.genai import Client
        from google.genai import types as genai_types

        self._client = Client(api_key=api_key)
        self._model = model
        self._max_sampled_chars = max_sampled_chars
        self._types = genai_types
        # Cadeia de fallback quando o modelo padrão retorna 404 NOT_FOUND
        # ou 503 UNAVAILABLE (alta demanda).
        self._fallback_models = ["gemini-3.8-flash", "gemini-3-flash-preview", "gemini-2.5-pro"]

    def _is_404(self, exc: BaseException) -> bool:
        """Verificar se uma exceção do google-genai é um erro HTTP 404 (NOT_FOUND)."""
        code = getattr(exc, "code", None)
        try:
            return int(code) == 404
        except (TypeError, ValueError):
            return False

    @_retry_on_retryable_http()
    def _call_gemini(
        self,
        system_prompt: str,
        context_payload: str,
    ) -> LLMClassificationOutput:
        """Chamar a API Gemini com saída estruturada, retry em HTTP 429/503 e
        fallback inteligente em HTTP 404 (NOT_FOUND) ou 503 (UNAVAILABLE).

        Se o modelo atual retornar 404, ou se todas as tentativas de retry
        (backoff exponencial) esgotarem com 503, tenta a cadeia de fallback
        (``self._fallback_models``) e atualiza ``self._model`` para o primeiro
        modelo que responder 200 OK.
        """
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
                # Sucesso: atualiza o modelo ativo para este.
                if modelo != self._model:
                    self._model = modelo
                parsed = response.parsed
                if parsed is None:
                    raise ValueError(
                        "Resposta do Gemini não pôde ser interpretada como JSON"
                    )
                if not isinstance(parsed, LLMClassificationOutput):
                    parsed = LLMClassificationOutput.model_validate(parsed)
                return parsed
            except Exception as exc:
                ultimo_erro = exc
                if self._is_404(exc):
                    # Tenta o próximo modelo da cadeia de fallback.
                    continue
                # 503 (ou outro não-404) após esgotar retry: tenta próximo modelo.
                if _is_retryable_http(exc):
                    continue
                # Erro não-retryable: propaga imediatamente.
                raise
        # Esgotou a cadeia de fallback sem sucesso.
        raise ultimo_erro or RuntimeError("Falha ao chamar a API Gemini")

    def classify(
        self,
        sampled_text: str,
        cip_text: str,
        external_metadata: ExternalMetadata | None,
        used_ocr: bool = False,
    ) -> ClassificationResult:
        """Classificar via Gemini aplicando travas determinísticas de confiança."""
        # Short-circuit: texto útil insuficiente e sem metadado externo.
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
            output = self._call_gemini(system_prompt, context_payload)
        except Exception as exc:  # falha de rede / API / parse
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
            )

        # Validar/reparar par (grande_area, area_basica) contra o catálogo.
        reparado = validate_or_repair_pair(output.grande_area, output.area_basica)
        if reparado is None:
            return ClassificationResult(
                grande_area=output.grande_area,
                area_basica=output.area_basica,
                tipo=output.tipo.value if hasattr(output.tipo, "value") else str(output.tipo),
                authors=list(output.authors),
                title=output.title,
                subtitle=output.subtitle,
                year=output.year,
                confidence_score=0.0,
                reasoning=(
                    f"{output.reasoning} Par (grande_area, area_basica) irreparável "
                    f"contra o catálogo CAPES/CNPq."
                ),
                used_ocr=used_ocr,
            )
        grande_area, area_basica = reparado

        # Teto de confiança para título vazio/genérico sem autor identificável.
        confidence = float(output.confidence_score)
        title = output.title or ""
        has_authors = bool(output.authors)
        if is_generic_title(title) and not has_authors:
            confidence = min(confidence, GENERIC_TITLE_CONFIDENCE_CAP)

        return ClassificationResult(
            grande_area=grande_area,
            area_basica=area_basica,
            tipo=output.tipo.value if hasattr(output.tipo, "value") else str(output.tipo),
            authors=list(output.authors),
            title=title,
            subtitle=output.subtitle,
            year=output.year,
            confidence_score=confidence,
            reasoning=output.reasoning,
            used_ocr=used_ocr,
        )


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
