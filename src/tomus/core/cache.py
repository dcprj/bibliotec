"""Cache SQLite local do Tomus (Stage 1 / idempotência).

Banco em ~/.cache/tomus/state.db em modo WAL com a tabela
processed_files indexada por (sha256, taxonomy_version, model_name),
persistindo apenas resultados com confidence_score >= confidence_min
e suportando invalidação via --no-cache.

Nunca lê nem grava resultados de provedores mock (reasoning == 'mock')
no cache real (~/.cache/tomus/state.db), a menos que um db_path
explícito de teste seja injetado.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path.home() / ".cache" / "tomus"
CACHE_DB_PATH = CACHE_DIR / "state.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS processed_files (
    sha256 TEXT NOT NULL,
    taxonomy_version TEXT NOT NULL,
    model_name TEXT NOT NULL,
    classification_json TEXT NOT NULL,
    used_ocr INTEGER NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (sha256, taxonomy_version, model_name)
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    """Abrir conexão SQLite em modo WAL, criando diretório e tabela se necessário."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # check_same_thread=False permite uso da mesma conexão em worker threads
    # (acesso serializado pelo finalize_lock em pipeline.py).
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def _is_mock(classification: dict[str, Any]) -> bool:
    """Verificar se uma classificação veio de um provedor mock."""
    return str(classification.get("reasoning", "")) == "mock"


class FileCache:
    """Gerenciar cache local de classificações já aprovadas.

    Quando ``db_path`` não é fornecido, usa o cache real
    (~/.cache/tomus/state.db). Nesse caso, nunca lê nem grava resultados
    com ``reasoning == 'mock'`` (provedor MockLLMProvider), evitando poluir o
    cache real com dados de teste.
    """

    def __init__(self, enabled: bool = True, db_path: Path | None = None) -> None:
        self.enabled = enabled
        self.db_path = db_path or CACHE_DB_PATH
        self._conn: Optional[sqlite3.Connection] = None
        # Indica se este é o cache real (sem db_path explícito de teste).
        self._is_real_cache = db_path is None

    def _ensure_conn(self) -> None:
        if self._conn is None and self.enabled:
            self._conn = _connect(self.db_path)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "FileCache":
        self._ensure_conn()
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def get(
        self,
        sha256: str,
        taxonomy_version: str,
        model_name: str,
    ) -> Optional[dict[str, Any]]:
        """Buscar classificação em cache pela chave composta.

        No cache real, ignora entradas com reasoning == 'mock'.
        """
        if not self.enabled:
            return None
        self._ensure_conn()
        if self._conn is None:
            return None
        cur = self._conn.execute(
            """
            SELECT classification_json, used_ocr
            FROM processed_files
            WHERE sha256 = ? AND taxonomy_version = ? AND model_name = ?
            """,
            (sha256, taxonomy_version, model_name),
        )
        row = cur.fetchone()
        if row is None:
            return None
        classification_json, used_ocr = row
        try:
            data = json.loads(classification_json)
        except json.JSONDecodeError:
            return None
        data["used_ocr"] = bool(used_ocr)
        # No cache real, nunca retornar dados de mock.
        if self._is_real_cache and _is_mock(data):
            return None
        return data

    def put(
        self,
        sha256: str,
        taxonomy_version: str,
        model_name: str,
        classification: dict[str, Any],
        used_ocr: bool,
        confidence_min: float = 0.70,
    ) -> None:
        """Persistir classificação apenas se confidence_score >= confidence_min.

        No cache real, nunca grava resultados com reasoning == 'mock'.
        """
        if not self.enabled:
            return
        confidence = float(classification.get("confidence_score", 0.0))
        if confidence < confidence_min:
            return
        # No cache real, nunca gravar dados de mock.
        if self._is_real_cache and _is_mock(classification):
            return
        self._ensure_conn()
        if self._conn is None:
            return
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            """
            INSERT INTO processed_files
                (sha256, taxonomy_version, model_name, classification_json, used_ocr, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(sha256, taxonomy_version, model_name) DO UPDATE SET
                classification_json = excluded.classification_json,
                used_ocr = excluded.used_ocr,
                updated_at = excluded.updated_at
            """,
            (
                sha256,
                taxonomy_version,
                model_name,
                json.dumps(classification, ensure_ascii=False),
                int(used_ocr),
                now,
            ),
        )
        self._conn.commit()

    def clear(self) -> None:
        """Limpar todas as entradas do cache (suporte a --no-cache invalidação)."""
        if not self.enabled:
            return
        self._ensure_conn()
        if self._conn is None:
            return
        self._conn.execute("DELETE FROM processed_files")
        self._conn.commit()

    def count(self) -> int:
        """Retorna o número total de entradas registradas no cache SQLite."""
        if not self.enabled or not self.db_path.exists():
            return 0
        try:
            self._ensure_conn()
            if self._conn is not None:
                cursor = self._conn.execute("SELECT COUNT(*) FROM processed_files")
                row = cursor.fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0
        return 0
