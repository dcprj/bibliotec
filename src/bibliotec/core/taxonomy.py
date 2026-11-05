"""Carrega e valida a taxonomia CAPES/CNPq (taxonomy_capes.json)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_RESOURCES_DIR = Path(__file__).parent / "resources"
_TAXONOMY_PATH = _RESOURCES_DIR / "taxonomy_capes.json"

_taxonomy_cache: Optional[dict] = None


def _load_taxonomy() -> dict:
    global _taxonomy_cache
    if _taxonomy_cache is None:
        with open(_TAXONOMY_PATH, "r", encoding="utf-8") as fh:
            _taxonomy_cache = json.load(fh)
    return _taxonomy_cache


def get_taxonomy_version() -> str:
    """Retornar a versão do catálogo CAPES/CNPq."""
    return _load_taxonomy().get("version", "capes-cnpq-v1")


def get_grandes_areas() -> list[str]:
    """Retornar a lista de Grandes Áreas oficiais."""
    return list(_load_taxonomy().get("areas", {}).keys())


def get_areas_basicas(grande_area: str) -> list[str]:
    """Retornar as Áreas Básicas de uma Grande Área específica."""
    areas = _load_taxonomy().get("areas", {})
    return areas.get(grande_area, [])


def _build_area_to_grande_area() -> dict[str, str]:
    """Mapear cada Área Básica para sua Grande Área pai."""
    mapping: dict[str, str] = {}
    for grande_area, areas_basicas in _load_taxonomy().get("areas", {}).items():
        for area_basica in areas_basicas:
            mapping[area_basica] = grande_area
    return mapping


def validate_or_repair_pair(
    grande_area: str,
    area_basica: str,
) -> Optional[tuple[str, str]]:
    """Validar ou reparar o par (grande_area, area_basica).

    Se a area_basica existir em outra Grande Área, corrige a grande_area pai.
    Retorna None caso nenhuma das duas exista no catálogo.
    """
    taxonomy = _load_taxonomy()
    areas = taxonomy.get("areas", {})
    area_to_grande = _build_area_to_grande_area()

    # Grande Área e Área Básica já consistentes
    if grande_area in areas and area_basica in areas.get(grande_area, []):
        return (grande_area, area_basica)

    # Grande Área inválida, mas Área Básica existe em outro pai -> reparar
    if area_basica in area_to_grande:
        correta = area_to_grande[area_basica]
        return (correta, area_basica)

    # Nenhuma das duas existe
    return None


def format_taxonomy_for_prompt() -> str:
    """Formatar o catálogo CAPES/CNPq para inclusão no prompt do LLM."""
    lines = ["Catálogo CAPES/CNPq (Grandes Áreas e Áreas Básicas válidas):"]
    for grande_area, areas_basicas in _load_taxonomy().get("areas", {}).items():
        areas_str = "; ".join(areas_basicas)
        lines.append(f"- {grande_area}: {areas_str}")
    return "\n".join(lines)
