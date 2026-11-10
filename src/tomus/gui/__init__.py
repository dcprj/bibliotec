"""Pacote da interface gráfica desktop do Tomus (PySide6 / Qt6 Fusion).

Exporta ``launch_gui()`` e ``main()`` (implementados em :mod:`tomus.gui.app`).

Este pacote obedece ao manifesto Anti-AI-Slop da especificação
``docs/designs/gui_spec.md``: zero emojis crus, zero gradientes neon roxo/rosa,
alta densidade informacional e ícones vetoriais SVG monocromáticos puros.
"""

from __future__ import annotations

from tomus.gui.theme import (
    EDITORIAL_PAPER_THEME,
    TECHNICAL_GRAPHITE_THEME,
    ThemeTokens,
    active_theme_for_scheme,
    generate_qss,
    status_colors,
)

__all__ = [
    "EDITORIAL_PAPER_THEME",
    "TECHNICAL_GRAPHITE_THEME",
    "ThemeTokens",
    "active_theme_for_scheme",
    "generate_qss",
    "status_colors",
]
