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
    assert dlg.tabs.tabText(0) == "Credenciais e Chaves de API"
    assert dlg.tabs.tabText(1) == "Provedores LLM && Fallback"
    assert dlg.tabs.tabText(2) == "Pipeline, OCR && Cache"
    dlg.close()


def test_preferences_dialog_save_and_reactivity(tmp_path, monkeypatch):
    """Garante que PreferencesDialog salva in-place e atualiza labels reativos."""
    from bibliotec.gui.widgets.preferences_dialog import PreferencesDialog

    monkeypatch.chdir(tmp_path)
    qapp = get_qapp()
    cfg = AppConfig()
    cfg_file = tmp_path / "config.toml"
    dlg = PreferencesDialog(cfg, config_path=cfg_file)

    # Label inicial deve ser não configurado se vazio
    dlg._fields["gemini_api_key"].setText("")
    assert "Não configurado" in dlg._env_labels["gemini_api_key"].text()

    # Digitar chave deve atualizar reativamente para configurado
    dlg._fields["gemini_api_key"].setText("AIzaSyTestKey123")
    assert "Configurado" in dlg._env_labels["gemini_api_key"].text()

    # Alterar provedor e modelo
    dlg.cmb_primary.setCurrentText("groq")
    dlg.edit_model.setText("llama-3.3-70b-versatile")
    dlg.chk_nvidia.setChecked(False)

    dlg._save()

    # Validar persistência in-place no objeto cfg
    assert cfg.api_keys.gemini_api_key == "AIzaSyTestKey123"
    assert cfg.llm.provider == "groq"
    assert cfg.llm.model == "llama-3.3-70b-versatile"
    assert "nvidia" not in cfg.llm.fallback_chain

    # Validar persistência no arquivo TOML
    assert dlg._config_path.exists()
    content = dlg._config_path.read_text(encoding="utf-8")
    assert "AIzaSyTestKey123" in content
    assert "groq" in content
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
