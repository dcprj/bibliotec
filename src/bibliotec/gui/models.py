"""Modelos de dados da grade de documentos (Seção 3.2 item C do gui_spec.md).

Implementa:
* ``DocumentTableModel(QAbstractTableModel)`` — modelo virtualizado de 8
  colunas com renderização a 60fps para lotes de 5.000+ arquivos.
* ``DocumentFilterProxyModel(QSortFilterProxyModel)`` — busca textual
  instantânea (debounce 120ms na view) + filtro por status e área CAPES/CNPq.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    QSortFilterProxyModel,
    QAbstractTableModel,
)

from bibliotec.core.models import FileManifestEntry, ProcessStatus

__all__ = ["DocumentTableModel", "DocumentFilterProxyModel"]

# --------------------------------------------------------------------------- #
# Definição das 8 colunas da grade (conforme Seção 3.2 item C)
# --------------------------------------------------------------------------- #

_COL_STATUS = 0
_COL_TITLE = 1
_COL_AUTHORS = 2
_COL_YEAR = 3
_COL_AREA = 4
_COL_TYPE = 5
_COL_CONFIDENCE = 6
_COL_FLAGS = 7

_COLUMN_HEADERS = [
    "Status",
    "Título / Arquivo",
    "Autor(es)",
    "Ano",
    "Grande Área / Área Básica",
    "Tipo",
    "Confiança",
    "Flags",
]

# Larguras iniciais das colunas (pixels). A coluna Título é flexível (estica).
_COLUMN_WIDTHS = [118, 260, 180, 56, 210, 110, 72, 64]


class _DocumentRow:
    """Representação enxuta de uma linha da grade (um documento do lote)."""

    __slots__ = (
        "source_path",
        "destination_path",
        "sha256",
        "status",
        "title",
        "subtitle",
        "authors",
        "year",
        "grande_area",
        "area_basica",
        "tipo",
        "confidence",
        "used_ocr",
        "from_cache",
        "error_message",
        "stage",
        "message",
    )

    def __init__(self, entry: FileManifestEntry | None = None) -> None:
        self.source_path = ""
        self.destination_path = ""
        self.sha256 = ""
        self.status: str = "processing"
        self.title = ""
        self.subtitle = ""
        self.authors: list[str] = []
        self.year: int | None = None
        self.grande_area = ""
        self.area_basica = ""
        self.tipo = ""
        self.confidence: float = 0.0
        self.used_ocr = False
        self.from_cache = False
        self.error_message = ""
        self.stage = ""
        self.message = ""

        if entry is not None:
            self._from_entry(entry)

    def _from_entry(self, entry: FileManifestEntry) -> None:
        self.source_path = entry.source_path
        self.destination_path = entry.destination_path or ""
        self.sha256 = entry.sha256
        self.status = entry.status.value if isinstance(entry.status, ProcessStatus) else str(entry.status)
        self.error_message = entry.error_message or ""
        classification = entry.classification or {}
        self.title = classification.get("title", "") or ""
        self.subtitle = classification.get("subtitle", "") or ""
        self.authors = list(classification.get("authors") or [])
        self.year = classification.get("year")
        self.grande_area = classification.get("grande_area", "") or ""
        self.area_basica = classification.get("area_basica", "") or ""
        self.tipo = str(classification.get("tipo", "") or "")
        self.confidence = float(classification.get("confidence_score", 0.0) or 0.0)
        self.used_ocr = bool(classification.get("used_ocr", False))

    @property
    def display_title(self) -> str:
        """Título acadêmico ou nome do arquivo original enquanto não classificado."""
        if self.title:
            return self.title
        return Path(self.source_path).name if self.source_path else ""

    @property
    def display_authors(self) -> str:
        if self.authors:
            return "; ".join(self.authors)
        return "—"

    @property
    def display_year(self) -> str:
        if self.year is not None:
            return str(self.year)
        return "s.d."

    @property
    def display_area(self) -> str:
        if self.grande_area and self.area_basica:
            return f"{self.grande_area} › {self.area_basica}"
        if self.grande_area:
            return self.grande_area
        return "—"

    @property
    def display_confidence(self) -> str:
        if self.confidence > 0:
            return f"{self.confidence:.2f}"
        return "—"

    @property
    def is_processing(self) -> bool:
        return self.status not in {
            ProcessStatus.ORGANIZED.value,
            ProcessStatus.MANUAL_REVIEW.value,
            ProcessStatus.DUPLICATE_SKIPPED.value,
            ProcessStatus.IGNORED_NON_PDF.value,
            ProcessStatus.ERROR.value,
        }

    @property
    def flags(self) -> list[str]:
        flags: list[str] = []
        if self.used_ocr:
            flags.append("OCR")
        if self.from_cache:
            flags.append("CACHE")
        return flags


# --------------------------------------------------------------------------- #
# DocumentTableModel
# --------------------------------------------------------------------------- #


class DocumentTableModel(QAbstractTableModel):
    """Modelo virtualizado da grade de documentos (8 colunas, 60fps).

    Armazena linhas como objetos ``_DocumentRow`` leves. A view solicita apenas
    as células visíveis via ``data()``, mantendo rolagem fluida mesmo com
    lotes de 5.000+ arquivos (arquitetura Model/View do Qt 6).
    """

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._rows: list[_DocumentRow] = []

    # -- Qt model API ------------------------------------------------------- #

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(_COLUMN_HEADERS)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(_COLUMN_HEADERS):
                return _COLUMN_HEADERS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        if row < 0 or row >= len(self._rows):
            return None
        doc = self._rows[row]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_value(doc, col)
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return self._alignment(col)
        if role == Qt.ItemDataRole.UserRole:
            return doc
        return None

    def _display_value(self, doc: _DocumentRow, col: int) -> Any:
        if col == _COL_STATUS:
            return doc.status
        if col == _COL_TITLE:
            return doc.display_title
        if col == _COL_AUTHORS:
            return doc.display_authors
        if col == _COL_YEAR:
            return doc.display_year
        if col == _COL_AREA:
            return doc.display_area
        if col == _COL_TYPE:
            return doc.tipo or "—"
        if col == _COL_CONFIDENCE:
            return doc.display_confidence
        if col == _COL_FLAGS:
            return ", ".join(doc.flags) if doc.flags else ""
        return None

    def _alignment(self, col: int) -> Any:
        if col in (_COL_YEAR, _COL_CONFIDENCE):
            return int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        if col == _COL_FLAGS:
            return int(Qt.AlignmentFlag.AlignCenter)
        return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    # -- API de atualização a partir de eventos do pipeline ----------------- #

    def upsert_from_event(self, event: Any) -> None:
        """Inserir ou atualizar uma linha a partir de um ``PipelineEvent``.

        O ``source_path`` do evento é a chave de identidade. Quando o evento é
        terminal (status em estados finais), preenche todos os campos.
        Eventos de conclusão do scanner ou de ciclo de vida de diretórios não
        representam um documento individual e são ignorados.
        """
        stage = getattr(event, "stage", "")
        status = getattr(event, "status", "")
        message = getattr(event, "message", "")
        source_path = getattr(event, "source_path", "")

        if not source_path:
            return

        # Ignorar eventos de ciclo de vida / resumo que operam no nível de
        # diretório ou lote global (e não em documentos individuais).
        if stage == "scanner" and (
            status == "completed"
            or message.startswith("Varredura")
            or "PDF(s)" in message
        ):
            return
        if stage == "pipeline" and status == "completed":
            return

        # Diretórios nunca devem entrar na grade de documentos individuais.
        try:
            if Path(source_path).is_dir():
                return
        except OSError:
            pass

        # Encontrar linha existente pelo source_path.
        row_idx = self._find_row(source_path)
        doc = self._rows[row_idx] if row_idx is not None else _DocumentRow()
        if row_idx is None:
            doc.source_path = source_path
            self.beginInsertRows(QModelIndex(), len(self._rows), len(self._rows))
            self._rows.append(doc)
            self.endInsertRows()
            row_idx = len(self._rows) - 1

        doc.stage = stage
        doc.message = message

        # Propagar classification (título parcial ou completo) quando presente
        # no evento, mesmo que o status ainda não seja terminal.
        classification = getattr(event, "classification", None) or {}
        if classification:
            doc.title = classification.get("title", "") or doc.title
            doc.subtitle = classification.get("subtitle", "") or doc.subtitle
            doc.authors = list(classification.get("authors") or [])
            doc.year = classification.get("year")
            doc.grande_area = classification.get("grande_area", "") or ""
            doc.area_basica = classification.get("area_basica", "") or ""
            doc.tipo = str(classification.get("tipo", "") or "")
            doc.confidence = float(classification.get("confidence_score", 0.0) or 0.0)
            doc.used_ocr = bool(classification.get("used_ocr", False))
            doc.from_cache = stage == "cache"

        # Atualizar o status apenas quando o evento traz um estado terminal.
        if status in {
            ProcessStatus.ORGANIZED.value,
            ProcessStatus.MANUAL_REVIEW.value,
            ProcessStatus.DUPLICATE_SKIPPED.value,
            ProcessStatus.IGNORED_NON_PDF.value,
            ProcessStatus.ERROR.value,
        }:
            doc.status = status
        elif status == "ignored":
            doc.status = ProcessStatus.IGNORED_NON_PDF.value

        self.dataChanged.emit(
            self.index(row_idx, 0), self.index(row_idx, self.columnCount() - 1)
        )

    def _find_row(self, source_path: str) -> int | None:
        for i, doc in enumerate(self._rows):
            if doc.source_path == source_path:
                return i
        return None

    def replace_all(self, entries: list[FileManifestEntry]) -> None:
        """Substituir todo o conteúdo da grade (usa beginResetModel)."""
        self.beginResetModel()
        self._rows = [
            _DocumentRow(e)
            for e in entries
            if e.source_path and not Path(e.source_path).is_dir()
        ]
        self.endResetModel()

    def clear(self) -> None:
        self.beginResetModel()
        self._rows = []
        self.endResetModel()

    def row(self, index: int) -> _DocumentRow | None:
        if 0 <= index < len(self._rows):
            return self._rows[index]
        return None

    def entries(self) -> list[_DocumentRow]:
        return list(self._rows)


# --------------------------------------------------------------------------- #
# DocumentFilterProxyModel
# --------------------------------------------------------------------------- #


class DocumentFilterProxyModel(QSortFilterProxyModel):
    """Proxy de filtros para a grade de documentos.

    Suporta:
    * Busca textual instantânea sobre título, autor, ano, DOI, ISBN e nome
      original do arquivo (case-insensitive, contém).
    * Filtro por status documental (ProcessStatus).
    * Filtro por Grande Área / Área Básica CAPES/CNPq.
    """

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._search_text = ""
        self._status_filter: set[str] | None = None  # None = todos
        self._area_filter: str | None = None  # None = todas

    # -- Filtros ------------------------------------------------------------ #

    def set_search_text(self, text: str) -> None:
        self._search_text = text.strip().lower()
        self.invalidateFilter()

    def set_status_filter(self, statuses: set[str] | None) -> None:
        self._status_filter = statuses
        self.invalidateFilter()

    def set_area_filter(self, area: str | None) -> None:
        self._area_filter = area
        self.invalidateFilter()

    # -- QSortFilterProxyModel API ------------------------------------------ #

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        model = self.sourceModel()
        if not isinstance(model, DocumentTableModel):
            return True
        doc = model.row(source_row)
        if doc is None:
            return False

        # Filtro por status.
        if self._status_filter is not None and doc.status not in self._status_filter:
            return False

        # Filtro por área CAPES/CNPq.
        if self._area_filter is not None:
            if self._area_filter != doc.grande_area and self._area_filter != doc.area_basica:
                return False

        # Busca textual.
        if self._search_text:
            haystack = " ".join(
                [
                    doc.display_title,
                    doc.display_authors,
                    doc.display_year,
                    doc.display_area,
                    doc.tipo,
                    doc.sha256,
                    Path(doc.source_path).name,
                ]
            ).lower()
            if self._search_text not in haystack:
                return False

        return True


class PathLike(str):
    """Marcador de tipo para caminhos de arquivo (evita ambiguidade)."""
    pass
