"""Fixtures compartilhadas para a suíte de testes do Tomus."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Diretório raiz do repositório Tomus."""
    return Path(__file__).resolve().parents[1]
