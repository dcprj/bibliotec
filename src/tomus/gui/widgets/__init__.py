"""Widgets da bancada de 3 painéis do Tomus (Seção 3.2 do gui_spec.md).

Exporta todos os componentes da interface:
``OperationalToolbar``, ``SessionResumeBanner``, ``CapesSidebarPanel``,
``DocumentTablePanel``, ``DocumentInspectorPanel``, ``ABNTReferenceCard``,
``ManualTriageBox``, ``TelemetryStatusBar``, ``LogCacheDrawer`` e
``PreferencesDialog``.
"""

from __future__ import annotations

from tomus.gui.widgets.document_table import DocumentTablePanel
from tomus.gui.widgets.inspector import (
    ABNTReferenceCard,
    DocumentInspectorPanel,
    ManualTriageBox,
)
from tomus.gui.widgets.preferences_dialog import PreferencesDialog
from tomus.gui.widgets.sidebar import CapesSidebarPanel
from tomus.gui.widgets.status_drawer import LogCacheDrawer, TelemetryStatusBar
from tomus.gui.widgets.toolbar import OperationalToolbar, SessionResumeBanner

__all__ = [
    "OperationalToolbar",
    "SessionResumeBanner",
    "CapesSidebarPanel",
    "DocumentTablePanel",
    "ABNTReferenceCard",
    "DocumentInspectorPanel",
    "ManualTriageBox",
    "TelemetryStatusBar",
    "LogCacheDrawer",
    "PreferencesDialog",
]
