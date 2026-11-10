"""Entidades de domínio e contratos de dados do Tomus (Seção 3 do design)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class DocumentType(str, Enum):
    """Tipos documentais fechados do Tomus."""

    LIVRO = "Livro"
    REVISTA_CIENTIFICA = "Revista Científica"
    ARTIGO = "Artigo"
    TESE_DISSERTACAO = "Tese_Dissertacao"
    OUTROS = "Outros"


class ProcessStatus(str, Enum):
    """Status de processamento de um arquivo no manifesto."""

    ORGANIZED = "organized"
    MANUAL_REVIEW = "manual_review"
    DUPLICATE_SKIPPED = "duplicate_skipped"
    IGNORED_NON_PDF = "ignored_non_pdf"
    ERROR = "error"


class FileOperation(str, Enum):
    """Operação de sistema de arquivos."""

    COPY = "copy"
    MOVE = "move"


class ExtractedDocument(BaseModel):
    """Resultado da leitura local do PDF (Stage 1 e Stage 2)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_path: Path
    sha256: str
    file_size_bytes: int
    total_pages: int
    used_ocr: bool = False
    native_metadata: dict[str, Any] = Field(default_factory=dict)
    sampled_text: str = ""
    cip_text: str = ""
    detected_doi: Optional[str] = None
    detected_isbn: Optional[str] = None


class ExternalMetadata(BaseModel):
    """Metadados recuperados e validados do OpenAlex ou Google Books (Stage 3)."""

    source: str  # "openalex" | "google_books"
    title: str = ""
    subtitle: str = ""
    authors: list[str] = Field(default_factory=list)
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    city: Optional[str] = None
    edition: Optional[str] = None
    journal_name: Optional[str] = None
    volume: Optional[str] = None
    number: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    document_type_hint: Optional[str] = None
    concepts: list[str] = Field(default_factory=list)
    match_score: float = 0.0


class LLMClassificationOutput(BaseModel):
    """Contrato de saída estruturada do LLM validado contra a tabela CAPES/CNPq (Stage 4)."""

    grande_area: str
    area_basica: str
    tipo: DocumentType
    authors: list[str] = Field(default_factory=list)
    title: str = ""
    subtitle: str = ""
    year: Optional[int] = None
    publisher: Optional[str] = None
    city: Optional[str] = None
    edition: Optional[str] = None
    journal_name: Optional[str] = None
    volume: Optional[str] = None
    number: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str = ""


class FileManifestEntry(BaseModel):
    """Registro individual auditável gravado em manifest.json (Stage 5)."""

    source_path: str
    destination_path: Optional[str] = None
    sha256: str
    status: ProcessStatus
    used_ocr: bool = False
    classification: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None


class ExecutionSummary(BaseModel):
    """Envelope raiz gravado em manifest.json e exibido ao final da CLI."""

    total_scanned: int = 0
    organized_count: int = 0
    manual_review_count: int = 0
    duplicate_skipped_count: int = 0
    ignored_non_pdf_count: int = 0
    error_count: int = 0
    manual_review_ratio: float = 0.0
    exceeded_manual_review_ceiling: bool = False
    entries: list[FileManifestEntry] = Field(default_factory=list)


class PipelineEvent(BaseModel):
    """Evento emitido pelo orquestrador para atualizar a interface (CLI/futura GUI)."""

    stage: str
    source_path: str
    destination_path: Optional[str] = None
    sha256: Optional[str] = None
    status: str
    message: str
    total_files: int | None = None
    completed_files: int | None = None
    classification: dict[str, Any] | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
