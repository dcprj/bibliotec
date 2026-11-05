"""Enriquecimento acadêmico externo via OpenAlex e Google Books (Item 16).

Implementa consultas HTTP com ``httpx`` + ``tenacity`` (3 tentativas, backoff
exponencial, timeout de 8s) para:

* OpenAlex API: busca exata por DOI ou busca por título com similaridade
  ``rapidfuzz.fuzz.token_set_ratio >= 88.0``, incluindo ``mailto:`` no
  ``User-Agent`` quando ``openalex_polite_email`` estiver configurado.
* Google Books API: busca por ISBN validado ou título/autor com rapidfuzz >= 88.0
  e ``&key=`` opcional.

Retorna ``list[ExternalMetadata]`` e expõe
:func:`enrich_document_metadata`.
"""

from __future__ import annotations

from typing import Optional

import httpx
from rapidfuzz import fuzz
from tenacity import retry, stop_after_attempt, wait_exponential

from bibliotec.core.config import AppConfig
from bibliotec.core.models import ExtractedDocument, ExternalMetadata

# Limiar de similaridade para buscas por título/autor (Item 16).
_SIMILARITY_THRESHOLD = 88.0

# Timeouts e retry (Item 16).
_REQUEST_TIMEOUT = 8.0
_RETRY_ATTEMPTS = 3

_USER_AGENT = "BiblioTEC/0.1.0 (https://github.com/dario/bibliotec)"


# ---------------------------------------------------------------------------
# Cliente HTTP com retry (tenacity)
# ---------------------------------------------------------------------------


def _retryable() -> httpx.Client:
    """Criar um cliente httpx com timeout de 8s."""
    return httpx.Client(timeout=_REQUEST_TIMEOUT, headers={"User-Agent": _USER_AGENT})


@retry(
    stop=stop_after_attempt(_RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _get_json(client: httpx.Client, url: str, params: dict) -> dict:
    """GET JSON com retry de 3 tentativas e backoff exponencial."""
    resp = client.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# OpenAlex
# ---------------------------------------------------------------------------


def _openalex_user_agent(email: Optional[str]) -> str:
    """Montar o User-Agent com mailto quando o e-mail polite estiver configurado."""
    if email:
        return f"{_USER_AGENT} (mailto:{email})"
    return _USER_AGENT


def _query_openalex_by_doi(client: httpx.Client, doi: str, email: Optional[str]) -> list[ExternalMetadata]:
    """Busca exata por DOI na OpenAlex."""
    url = f"https://api.openalex.org/works/https://doi.org/{doi}"
    headers = {"User-Agent": _openalex_user_agent(email)}
    resp = client.get(url, headers=headers)
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    data = resp.json()
    return [_openalex_to_metadata(data, score=1.0)]


def _query_openalex_by_title(client: httpx.Client, title: str, email: Optional[str]) -> list[ExternalMetadata]:
    """Busca por título na OpenAlex, filtrando por similaridade >= 88.0."""
    url = "https://api.openalex.org/works"
    headers = {"User-Agent": _openalex_user_agent(email)}
    params = {"search": title, "per-page": 10}
    data = _get_json(client, url, params)
    results = data.get("results", []) or []
    metadata: list[ExternalMetadata] = []
    for item in results:
        api_title = item.get("title") or ""
        score = fuzz.token_set_ratio(title, api_title)
        if score >= _SIMILARITY_THRESHOLD:
            metadata.append(_openalex_to_metadata(item, score=score / 100.0))
    return metadata


def _openalex_to_metadata(item: dict, score: float) -> ExternalMetadata:
    """Converter um item da OpenAlex em :class:`ExternalMetadata`."""
    authors = []
    for authorship in (item.get("authorships") or []):
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)
    publication_year = item.get("publication_year")
    concepts = []
    for concept in (item.get("concepts") or []):
        name = concept.get("display_name")
        if name:
            concepts.append(name)
    return ExternalMetadata(
        source="openalex",
        title=item.get("title") or "",
        subtitle="",
        authors=authors,
        publication_year=publication_year,
        document_type_hint=item.get("type"),
        concepts=concepts,
        match_score=score,
    )


# ---------------------------------------------------------------------------
# Google Books
# ---------------------------------------------------------------------------


def _query_google_books_by_isbn(client: httpx.Client, isbn: str, api_key: Optional[str]) -> list[ExternalMetadata]:
    """Busca exata por ISBN na Google Books."""
    url = "https://www.googleapis.com/books/v1/volumes"
    params: dict = {"q": f"isbn:{isbn}"}
    if api_key:
        params["key"] = api_key
    data = _get_json(client, url, params)
    items = data.get("items") or []
    return [_google_books_to_metadata(item, score=1.0) for item in items]


def _query_google_books_by_title_author(
    client: httpx.Client, title: str, author: Optional[str], api_key: Optional[str]
) -> list[ExternalMetadata]:
    """Busca por título/autor na Google Books, filtrando por similaridade >= 88.0."""
    url = "https://www.googleapis.com/books/v1/volumes"
    query = title if not author else f"{title} {author}"
    params: dict = {"q": query, "maxResults": 10}
    if api_key:
        params["key"] = api_key
    data = _get_json(client, url, params)
    items = data.get("items") or []
    metadata: list[ExternalMetadata] = []
    for item in items:
        volume_info = item.get("volumeInfo") or {}
        api_title = volume_info.get("title") or ""
        score = fuzz.token_set_ratio(title, api_title)
        if score >= _SIMILARITY_THRESHOLD:
            metadata.append(_google_books_to_metadata(item, score=score / 100.0))
    return metadata


def _google_books_to_metadata(item: dict, score: float) -> ExternalMetadata:
    """Converter um item da Google Books em :class:`ExternalMetadata`."""
    volume_info = item.get("volumeInfo") or {}
    authors = list(volume_info.get("authors") or [])
    pub_date = volume_info.get("publishedDate")
    publication_year: Optional[int] = None
    if pub_date:
        try:
            publication_year = int(str(pub_date)[:4])
        except ValueError:
            publication_year = None
    return ExternalMetadata(
        source="google_books",
        title=volume_info.get("title") or "",
        subtitle=volume_info.get("subtitle") or "",
        authors=authors,
        publication_year=publication_year,
        document_type_hint=volume_info.get("printType"),
        concepts=list(volume_info.get("categories") or []),
        match_score=score,
    )


# ---------------------------------------------------------------------------
# Orquestrador de enriquecimento
# ---------------------------------------------------------------------------


def enrich_document_metadata(
    doc: ExtractedDocument, config: AppConfig
) -> list[ExternalMetadata]:
    """Enriquecer um :class:`ExtractedDocument` com metadados externos.

    Consulta OpenAlex por DOI (exato) ou título, e Google Books por ISBN
    (exato) ou título/autor, retornando uma lista de
    :class:`ExternalMetadata` válidos (similaridade >= 88.0 para buscas
    textuais).
    """
    email = config.api_keys.openalex_polite_email or None
    google_key = config.api_keys.google_books_api_key or None

    results: list[ExternalMetadata] = []

    with _retryable() as client:
        # OpenAlex: busca exata por DOI, senão por título.
        if doc.detected_doi:
            try:
                results.extend(_query_openalex_by_doi(client, doc.detected_doi, email))
            except Exception:
                pass
        elif doc.sampled_text:
            # Extrair um título candidato (primeira linha não vazia) para busca.
            title_candidate = next(
                (line.strip() for line in doc.sampled_text.splitlines() if line.strip()),
                "",
            )
            if title_candidate:
                try:
                    results.extend(
                        _query_openalex_by_title(client, title_candidate, email)
                    )
                except Exception:
                    pass

        # Google Books: busca exata por ISBN, senão por título/autor.
        if doc.detected_isbn:
            try:
                results.extend(_query_google_books_by_isbn(client, doc.detected_isbn, google_key))
            except Exception:
                pass
        else:
            title_candidate = next(
                (line.strip() for line in doc.sampled_text.splitlines() if line.strip()),
                "",
            )
            author_candidate = doc.sampled_text.splitlines()[0].strip() if doc.sampled_text else None
            if title_candidate:
                try:
                    results.extend(
                        _query_google_books_by_title_author(
                            client, title_candidate, author_candidate, google_key
                        )
                    )
                except Exception:
                    pass

    return results
