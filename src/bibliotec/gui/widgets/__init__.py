"""Widgets da bancada de 3 painéis do BiblioTEC (Seção 3.2 do gui_spec.md).

Exporta todos os componentes da interface:
``OperationalToolbar``, ``SessionResumeBanner``, ``CapesSidebarPanel``,
``DocumentTablePanel``, ``DocumentInspectorPanel``, ``ABNTReferenceCard``,
``ManualTriageBox``, ``TelemetryStatusBar``, ``LogCacheDrawer`` e
``PreferencesDialog``.
"""

from __future__ import annotations

from bibliotec.gui.widgets.document_table import DocumentTablePanel
from bibliotec.gui.widgets.inspector import (
    ABNTReferenceCard,
    DocumentInspectorPanel,
    ManualTriageBox,
)
from bibliotec.gui.widgets.preferences_dialog import PreferencesDialog
from bibliotec.gui.widgets.sidebar import CapesSidebarPanel
from bibliotec.gui.widgets.status_drawer import LogCacheDrawer, TelemetryStatusBar
from bibliotec.gui.widgets.toolbar import OperationalToolbar, SessionResumeBanner

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
