"""Fixtures compartilhadas para a suíte de testes do BiblioTEC."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Diretório raiz do repositório BiblioTEC."""
    return Path(__file__).resolve().parents[1]
