"""Testes unitários para o WebBridge e MainWindow baseada em WebEngine."""

import json
from pathlib import Path

from PySide6.QtWidgets import QApplication

from bibliotec.core.config import AppConfig
from bibliotec.gui.bridge import WebBridge
from bibliotec.gui.main_window import BiblioTECMainWindow

_QAPP = None


def get_qapp():
    global _QAPP
    if _QAPP is None:
        _QAPP = QApplication.instance() or QApplication([])
    return _QAPP


def test_web_bridge_initial_state():
    qapp = get_qapp()
    cfg = AppConfig()
    bridge = WebBridge(cfg)
    bridge.source_dir = "/tmp/origem"
    bridge.target_dir = "/tmp/destino"

    raw = bridge.getInitialState()
    data = json.loads(raw)
    assert data["source"] == "/tmp/origem"
    assert data["target"] == "/tmp/destino"
    assert "provider" in data
    assert "hasKey" in data


def test_web_bridge_slots_exist():
    qapp = get_qapp()
    cfg = AppConfig()
    bridge = WebBridge(cfg)

    assert hasattr(bridge, "browseSource")
    assert hasattr(bridge, "browseTarget")
    assert hasattr(bridge, "startOrganize")
    assert hasattr(bridge, "cancelPipeline")
    assert hasattr(bridge, "openPdf")
    assert hasattr(bridge, "revealPath")
    assert hasattr(bridge, "openExternalUrl")
    assert hasattr(bridge, "approveManualTriage")
    assert hasattr(bridge, "checkProviderKey")
    assert hasattr(bridge, "openCacheDialog")
    assert hasattr(bridge, "openPreferences")


def test_web_bridge_check_provider_key():
    qapp = get_qapp()
    cfg = AppConfig()
    bridge = WebBridge(cfg)

    # Provider sem chave deve retornar False
    cfg.api_keys.claude_api_key = ""
    assert bridge.checkProviderKey("claude") is False

    # Provider com chave deve retornar True
    cfg.api_keys.claude_api_key = "sk-ant-test-key"
    assert bridge.checkProviderKey("claude") is True

    cfg.api_keys.github_token = ""
    assert bridge.checkProviderKey("github") is False

    cfg.api_keys.github_token = "ghp_test"
    assert bridge.checkProviderKey("github") is True


def test_web_bridge_cache_module_accessible():
    """Garante que bibliotec.core.cache é importado sem erros no slot de cache."""
    from bibliotec.core.cache import FileCache

    cache = FileCache(enabled=True)
    count = cache.count()
    assert isinstance(count, int)
    assert count >= 0
    cache.close()


def test_preferences_dialog_light_styling():
    """Garante que PreferencesDialog tem estilo claro explícito e componentes legíveis."""
    from bibliotec.gui.widgets.preferences_dialog import PreferencesDialog

    qapp = get_qapp()
    cfg = AppConfig()
    dlg = PreferencesDialog(cfg)

    assert "#FFFFFF" in dlg.styleSheet()
    assert "#1E3A8A" in dlg.styleSheet()
    assert dlg.tabs.count() == 3
    dlg.close()


def test_main_window_web_view_instancia():
    qapp = get_qapp()
    cfg = AppConfig()
    win = BiblioTECMainWindow(cfg, source_dir="/tmp/origem", target_dir="/tmp/destino")
    assert win.web_view is not None
    assert win.bridge is not None
    assert win.bridge.source_dir == "/tmp/origem"
    assert win.bridge.target_dir == "/tmp/destino"


def test_web_bridge_pipeline_event_with_destination_and_sha256():
    """Garante que PipelineEvent carrega destination_path e sha256 para os botões do Inspetor."""
    from bibliotec.core.models import PipelineEvent

    ev = PipelineEvent(
        stage="organizer",
        source_path="/tmp/origem/doc.pdf",
        destination_path="/tmp/destino/Ciências Humanas/Sociologia/Artigo/doc.pdf",
        sha256="abc1234567890abcdef1234567890abcdef1234567890abcdef1234567890abc",
        status="organized",
        message="Arquivo organizado",
    )
    dumped = ev.model_dump()
    assert dumped["destination_path"] == "/tmp/destino/Ciências Humanas/Sociologia/Artigo/doc.pdf"
    assert dumped["sha256"].startswith("abc1234")
