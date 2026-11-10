"""Persistência de Sessão para Retomada (Item [RES-02]).

Permite salvar o estado de uma execução em disco para que, em caso de
interrupção (Ctrl+C, fechamento de janela, queda de energia), o comando
``./tomus resume`` possa retomar exatamente de onde parou.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

SESSION_FILE = Path(".tomus_session.json")


class SessionState(BaseModel):
    """Estado de uma execução do Tomus, serializável em JSON."""

    source_dir: str
    target_dir: str
    recursive: bool = True
    move: bool = False
    dry_run: bool = False
    provider: str = "gemini"
    model: Optional[str] = None
    confidence_min: float = 0.70
    workers: int = 1
    no_cache: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def save_session(state: SessionState, path: Path = SESSION_FILE) -> None:
    """Salvar o estado da sessão em arquivo JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = state.model_dump(mode="json")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_session(path: Path = SESSION_FILE) -> Optional[SessionState]:
    """Carregar o estado da sessão do arquivo JSON.

    Retorna None se o arquivo não existir ou for inválido (corrompido).
    """
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState(**data)
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        return None


def clear_session(path: Path = SESSION_FILE) -> None:
    """Remover o arquivo de sessão com tolerância se já não existir."""
    try:
        path.unlink()
    except FileNotFoundError:
        pass
