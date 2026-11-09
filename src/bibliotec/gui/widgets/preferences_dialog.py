"""Modal de Preferências e Chaves de API (Seção 3.3 do gui_spec.md).

Lê e grava ``~/.config/bibliotec/config.toml`` (ou ``./bibliotec.toml``)
preservando permissão restrita ``0600``. Respeita a precedência
``ENV > Local TOML > Global TOML``.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from bibliotec.core.config import (
    ApiKeysConfig,
    AppConfig,
    CONFIG_FILE_MODE,
    GLOBAL_CONFIG_PATH,
    LOCAL_CONFIG_FILENAME,
    GeneralConfig,
    LLMConfig,
    mask_key,
)

__all__ = ["PreferencesDialog"]

_CHECKMARK_PATH = str(Path(__file__).parent.parent / "resources" / "checkmark.svg").replace("\\", "/")

_PREFERENCES_STYLE = f"""
QDialog {{
    background-color: #FFFFFF;
    color: #0F172A;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}}
QTabWidget::pane {{
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    background-color: #FFFFFF;
    top: -1px;
}}
QTabBar::tab {{
    background: #F8FAFC;
    color: #64748B;
    border: 1px solid #E2E8F0;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 4px;
    font-weight: 500;
}}
QTabBar::tab:selected {{
    background: #FFFFFF;
    color: #1E3A8A;
    border-bottom: 2px solid #1E3A8A;
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background: #F1F5F9;
    color: #0F172A;
}}
QLabel {{
    color: #0F172A;
    font-size: 13px;
}}
QLineEdit {{
    background-color: #F8FAFC;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border: 1px solid #1E3A8A;
    background-color: #FFFFFF;
}}
QComboBox {{
    background-color: #F8FAFC;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #E2E8F0;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
    background-color: #F1F5F9;
}}
QComboBox QAbstractItemView {{
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
    outline: none;
    padding: 4px;
}}
QComboBox QAbstractItemView::item {{
    min-height: 28px;
    padding: 6px 10px;
    color: #0F172A;
    background-color: #FFFFFF;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: #1E3A8A;
    color: #FFFFFF;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: #F1F5F9;
    color: #0F172A;
}}
QCheckBox {{
    color: #0F172A;
    font-size: 13px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #94A3B8;
    border-radius: 4px;
    background-color: #FFFFFF;
}}
QCheckBox::indicator:checked {{
    background-color: #1E3A8A;
    border: 1px solid #1E3A8A;
    image: url({_CHECKMARK_PATH});
}}
QCheckBox::indicator:hover {{
    border: 1px solid #1E3A8A;
}}
QPushButton {{
    background-color: #F1F5F9;
    color: #1E293B;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: #E2E8F0;
}}
QPushButton:checked {{
    background-color: #1E3A8A;
    color: #FFFFFF;
    border-color: #1E3A8A;
}}
"""

API_KEY_FIELDS = [
    ("gemini_api_key", "Google Gemini API Key", ["BIBLIOTEC_GEMINI_API_KEY", "GEMINI_API_KEY"]),
    ("groq_api_key", "Groq Cloud API Key", ["BIBLIOTEC_GROQ_API_KEY", "GROQ_API_KEY"]),
    ("nvidia_api_key", "NVIDIA NIM API Key", ["BIBLIOTEC_NVIDIA_API_KEY", "NVIDIA_API_KEY"]),
    ("deepseek_api_key", "DeepSeek API Key", ["BIBLIOTEC_DEEPSEEK_API_KEY", "DEEPSEEK_API_KEY"]),
    ("claude_api_key", "Anthropic Claude API Key", ["BIBLIOTEC_CLAUDE_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_API_KEY"]),
    ("github_token", "GitHub Models Token", ["BIBLIOTEC_GITHUB_TOKEN", "GITHUB_TOKEN", "GH_TOKEN"]),
]

ENRICHMENT_FIELDS = [
    ("openalex_polite_email", "OpenAlex Polite Email", []),
    ("google_books_api_key", "Google Books API Key", ["BIBLIOTEC_GOOGLE_BOOKS_API_KEY", "GOOGLE_BOOKS_API_KEY"]),
]


def _env_active(env_names: list[str]) -> bool:
    return any(os.environ.get(env) for env in env_names)


class PreferencesDialog(QDialog):
    """Diálogo modal de edição do config.toml e chaves de API."""

    def __init__(self, config: AppConfig, parent=None, config_path: Path | None = None) -> None:
        super().__init__(parent)
        self._config = config

        if config_path is not None:
            self._config_path = Path(config_path)
        else:
            local = Path.cwd() / LOCAL_CONFIG_FILENAME
            global_path = Path.home() / ".config" / "bibliotec" / "config.toml"
            self._config_path = local if local.exists() else global_path

        self.setWindowTitle("Preferências e Credenciais — BiblioTEC")
        self.setModal(True)
        self.resize(840, 580)
        self.setStyleSheet(_PREFERENCES_STYLE)

        self._fields: dict[str, QLineEdit] = {}
        self._env_labels: dict[str, QLabel] = {}

        self._build_ui()
        self._load_config_into_ui()

    # ------------------------------------------------------------------ #
    # Construção da UI
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._tab_credentials(), "Credenciais e Chaves de API")
        self.tabs.addTab(self._tab_fallback(), "Provedores LLM & Fallback".replace("&", "&&"))
        self.tabs.addTab(self._tab_pipeline(), "Pipeline, OCR & Cache".replace("&", "&&"))
        layout.addWidget(self.tabs)

        self.path_lbl = QLabel()
        self.path_lbl.setStyleSheet("color: #64748B; font-size: 11px; font-family: monospace; padding-top: 4px;")
        layout.addWidget(self.path_lbl)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        self.btn_save = btns.button(QDialogButtonBox.StandardButton.Save)
        self.btn_save.setText("Salvar Configuração")
        self.btn_save.setStyleSheet(
            "QPushButton { background-color: #1E3A8A; color: #FFFFFF; border: none; "
            "border-radius: 6px; padding: 8px 20px; font-weight: 600; font-size: 13px; }"
            "QPushButton:hover { background-color: #172554; }"
        )
        self.btn_cancel = btns.button(QDialogButtonBox.StandardButton.Cancel)
        self.btn_cancel.setText("Cancelar")
        self.btn_cancel.setStyleSheet(
            "QPushButton { background-color: #FFFFFF; color: #475569; border: 1px solid #CBD5E1; "
            "border-radius: 6px; padding: 8px 16px; font-weight: 500; font-size: 13px; }"
            "QPushButton:hover { background-color: #F1F5F9; color: #0F172A; }"
        )
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _tab_credentials(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_lbl = QLabel("Credenciais dos provedores de classificação (Stage 4)")
        header_lbl.setStyleSheet("font-weight: 600; color: #0F172A; font-size: 13px;")
        layout.addWidget(header_lbl)

        form = QFormLayout()
        form.setSpacing(10)
        for field_name, label, env_names in API_KEY_FIELDS:
            row = QHBoxLayout()
            row.setSpacing(8)
            edit = QLineEdit()
            edit.setPlaceholderText("Cole sua chave aqui...")
            edit.setEchoMode(QLineEdit.EchoMode.Password)
            edit.setFixedWidth(260)
            reveal = QPushButton("Mostrar")
            reveal.setFixedWidth(76)
            reveal.setCheckable(True)
            reveal.toggled.connect(
                lambda checked, e=edit, b=reveal: (
                    e.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password),
                    b.setText("Ocultar" if checked else "Mostrar"),
                )
            )
            env_lbl = QLabel("(Não configurado)")
            env_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic;")
            env_lbl.setMinimumWidth(190)

            def _on_change(_text, e=edit, l=env_lbl, ev=env_names):
                if _env_active(ev):
                    l.setText("(Ativo via Variável de Ambiente)")
                    l.setStyleSheet("color: #0284C7; font-size: 11px; font-weight: 500;")
                elif e.text().strip():
                    l.setText("✓ Configurado")
                    l.setStyleSheet("color: #16A34A; font-size: 11px; font-weight: 600;")
                else:
                    l.setText("(Não configurado)")
                    l.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic;")

            edit.textChanged.connect(_on_change)

            row.addWidget(edit)
            row.addWidget(reveal)
            row.addSpacing(10)
            row.addWidget(env_lbl)
            row.addStretch(1)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: 500; color: #1E293B;")
            form.addRow(lbl, row)
            self._fields[field_name] = edit
            self._env_labels[field_name] = env_lbl

        layout.addLayout(form)
        layout.addSpacing(8)

        header_enrich = QLabel("Serviços de enriquecimento acadêmico (Stage 3 — OpenAlex & Google Books)")
        header_enrich.setStyleSheet("font-weight: 600; color: #0F172A; font-size: 13px;")
        layout.addWidget(header_enrich)

        form_enrich = QFormLayout()
        form_enrich.setSpacing(10)
        for field_name, label, env_names in ENRICHMENT_FIELDS:
            edit = QLineEdit()
            edit.setFixedWidth(260)
            if "key" in field_name:
                edit.setPlaceholderText("Cole sua chave aqui...")
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            else:
                edit.setPlaceholderText("pesquisador@instituicao.edu.br")

            env_lbl = QLabel("(Não configurado)")
            env_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic;")
            env_lbl.setMinimumWidth(190)

            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(edit)

            if "key" in field_name:
                reveal = QPushButton("Mostrar")
                reveal.setFixedWidth(76)
                reveal.setCheckable(True)
                reveal.toggled.connect(
                    lambda checked, e=edit, b=reveal: (
                        e.setEchoMode(QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password),
                        b.setText("Ocultar" if checked else "Mostrar"),
                    )
                )
                row.addWidget(reveal)
            else:
                spacer = QWidget()
                spacer.setFixedWidth(76)
                row.addWidget(spacer)

            def _on_enrich_change(_text, e=edit, l=env_lbl, ev=env_names, fn=field_name):
                if _env_active(ev):
                    l.setText("(Ativo via Variável de Ambiente)")
                    l.setStyleSheet("color: #0284C7; font-size: 11px; font-weight: 500;")
                elif e.text().strip():
                    if fn == "openalex_polite_email":
                        l.setText("✓ Polite Pool Ativo (10 req/s)")
                    else:
                        l.setText("✓ Configurado")
                    l.setStyleSheet("color: #16A34A; font-size: 11px; font-weight: 600;")
                else:
                    l.setText("(Não configurado)")
                    l.setStyleSheet("color: #94A3B8; font-size: 11px; font-style: italic;")

            edit.textChanged.connect(_on_enrich_change)

            row.addSpacing(10)
            row.addWidget(env_lbl)
            row.addStretch(1)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: 500; color: #1E293B;")
            form_enrich.addRow(lbl, row)
            self._fields[field_name] = edit
            self._env_labels[field_name] = env_lbl

        layout.addLayout(form_enrich)
        layout.addStretch(1)
        return widget

    def _tab_fallback(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header1 = QLabel("Cadeia de fallback automático (FallbackLLMDispatcher)")
        header1.setStyleSheet("font-weight: 600; color: #0F172A; font-size: 13px;")
        layout.addWidget(header1)

        self.chk_groq = QCheckBox("groq (openai/gpt-oss-20b)", self)
        self.chk_groq.setChecked(True)
        self.chk_nvidia = QCheckBox("nvidia", self)
        self.chk_nvidia.setChecked(True)
        self.chk_deepseek = QCheckBox("deepseek", self)
        self.chk_deepseek.setChecked(True)
        fallback_lay = QHBoxLayout()
        lbl_prim = QLabel("Provedor Primário:")
        lbl_prim.setStyleSheet("font-weight: 500; color: #1E293B;")
        fallback_lay.addWidget(lbl_prim)
        self.cmb_primary = QComboBox(self)
        self.cmb_primary.addItems(["gemini", "groq", "nvidia", "deepseek", "claude", "github"])
        if self.cmb_primary.view():
            self.cmb_primary.view().setStyleSheet(
                "background-color: #FFFFFF; color: #0F172A; selection-background-color: #1E3A8A; selection-color: #FFFFFF;"
            )
        self.cmb_primary.setFixedWidth(130)
        fallback_lay.addWidget(self.cmb_primary)
        fallback_lay.addSpacing(16)
        lbl_mod = QLabel("Modelo Padrão:")
        lbl_mod.setStyleSheet("font-weight: 500; color: #1E293B;")
        fallback_lay.addWidget(lbl_mod)
        self.edit_model = QLineEdit("gemini-3.5-flash")
        self.edit_model.setFixedWidth(240)
        fallback_lay.addWidget(self.edit_model)
        fallback_lay.addStretch(1)
        layout.addLayout(fallback_lay)

        def _on_provider_change(prov: str) -> None:
            defaults = {
                "gemini": "gemini-3.5-flash",
                "groq": "llama-3.3-70b-versatile",
                "nvidia": "nvidia/llama-3.1-nemotron-70b-instruct",
                "deepseek": "deepseek-flash",
                "claude": "claude-3-5-sonnet-latest",
                "github": "gpt-4o",
            }
            if prov in defaults:
                self.edit_model.setText(defaults[prov])

        self.cmb_primary.currentTextChanged.connect(_on_provider_change)

        layout.addSpacing(6)
        lbl_ord = QLabel("Ordem de Fallback:")
        lbl_ord.setStyleSheet("font-weight: 500; color: #1E293B;")
        layout.addWidget(lbl_ord)
        fb_row = QHBoxLayout()
        fb_row.addWidget(self.chk_groq)
        fb_row.addWidget(self.chk_nvidia)
        fb_row.addWidget(self.chk_deepseek)
        fb_row.addStretch(1)
        layout.addLayout(fb_row)

        desc = QLabel(
            "Quando o provedor primário esgota sua cota (HTTP 429) ou sofre timeout, "
            "o BiblioTEC tenta sequencialmente os provedores habilitados acima."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #64748B; font-size: 12px; line-height: 1.4;")
        layout.addWidget(desc)

        layout.addStretch(1)
        return widget

    def _tab_pipeline(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header2 = QLabel("Limiar de qualidade e concorrência (Stage 1 a Stage 5)")
        header2.setStyleSheet("font-weight: 600; color: #0F172A; font-size: 13px;")
        layout.addWidget(header2)

        form = QFormLayout()
        form.setSpacing(10)
        self.edit_conf = QLineEdit("0.70")
        self.edit_conf.setFixedWidth(70)
        lbl_conf = QLabel("Confiança Mínima (confidence_min):")
        lbl_conf.setStyleSheet("font-weight: 500; color: #1E293B;")
        form.addRow(lbl_conf, self.edit_conf)
        self.edit_workers = QLineEdit("1")
        self.edit_workers.setFixedWidth(70)
        lbl_work = QLabel("Workers de Rede:")
        lbl_work.setStyleSheet("font-weight: 500; color: #1E293B;")
        form.addRow(lbl_work, self.edit_workers)
        layout.addLayout(form)

        layout.addSpacing(14)
        header3 = QLabel("Cache Local de Classificação (Stage 1)")
        header3.setStyleSheet("font-weight: 600; color: #0F172A; font-size: 13px;")
        layout.addWidget(header3)

        self.chk_use_cache = QCheckBox("Utilizar Cache Local SQLite (evita reprocessamento de PDFs já classificados)", self)
        self.chk_use_cache.setChecked(self._config.general.use_cache)
        layout.addWidget(self.chk_use_cache)

        layout.addStretch(1)
        return widget

    # ------------------------------------------------------------------ #
    # Carregar / Salvar
    # ------------------------------------------------------------------ #

    def _load_config_into_ui(self) -> None:
        modo = " (Permissão 0600 Segura)" if self._config_path.exists() else ""
        self.path_lbl.setText(f"ARQUIVO DE CONFIGURAÇÃO ATIVO: {self._config_path}{modo}")

        for field_name, _label, _env in API_KEY_FIELDS:
            value = getattr(self._config.api_keys, field_name, "")
            if field_name in self._fields:
                self._fields[field_name].setText(value)

        for field_name, _label, _env in ENRICHMENT_FIELDS:
            value = getattr(self._config.api_keys, field_name, "")
            if field_name in self._fields:
                self._fields[field_name].setText(value)

        curr_provider = self._config.llm.provider or "gemini"
        idx = self.cmb_primary.findText(curr_provider)
        if idx >= 0:
            self.cmb_primary.setCurrentIndex(idx)
        else:
            self.cmb_primary.setCurrentText(curr_provider)

        self.edit_model.setText(self._config.llm.model or "gemini-3.5-flash")

        fb = self._config.llm.fallback_chain or []
        self.chk_groq.setChecked("groq" in fb)
        self.chk_nvidia.setChecked("nvidia" in fb)
        self.chk_deepseek.setChecked("deepseek" in fb)

        self.edit_conf.setText(f"{self._config.general.confidence_min:.2f}")
        self.edit_workers.setText(str(self._config.general.workers))
        self.chk_use_cache.setChecked(self._config.general.use_cache)

    def _save(self) -> None:
        """Serializar as seções em config.toml com permissão 0600 e atualizar self._config in-place."""
        import tomli_w

        api_updates = {}
        for field_name, edit in self._fields.items():
            val = edit.text().strip()
            if hasattr(self._config.api_keys, field_name):
                setattr(self._config.api_keys, field_name, val)
                api_updates[field_name] = val

        try:
            conf = float(self.edit_conf.text())
        except ValueError:
            conf = 0.70
        try:
            workers = int(self.edit_workers.text())
        except ValueError:
            workers = 1

        use_cache = self.chk_use_cache.isChecked()
        self._config.general.use_cache = use_cache
        self._config.general.confidence_min = conf
        self._config.general.workers = workers

        primary_prov = self.cmb_primary.currentText()
        model_name = self.edit_model.text().strip() or "gemini-3.5-flash"
        fallback = []
        if self.chk_groq.isChecked():
            fallback.append("groq")
        if self.chk_nvidia.isChecked():
            fallback.append("nvidia")
        if self.chk_deepseek.isChecked():
            fallback.append("deepseek")

        self._config.llm.provider = primary_prov
        self._config.llm.model = model_name
        self._config.llm.fallback_chain = fallback

        new_config = AppConfig(
            general=GeneralConfig(
                **{
                    **self._config.general.model_dump(),
                    "confidence_min": conf,
                    "workers": workers,
                    "use_cache": use_cache,
                }
            ),
            llm=LLMConfig(
                provider=primary_prov,
                default_provider=primary_prov,
                model=model_name,
                fallback_chain=fallback,
                providers=self._config.llm.providers,
            ),
            api_keys=ApiKeysConfig(
                **{**self._config.api_keys.model_dump(), **api_updates}
            ),
        )

        config_dir = self._config_path.parent
        config_dir.mkdir(parents=True, exist_ok=True)
        toml_data = {
            "general": {
                "recursive": new_config.general.recursive,
                "file_operation": new_config.general.file_operation,
                "confidence_min": new_config.general.confidence_min,
                "workers": new_config.general.workers,
                "use_cache": new_config.general.use_cache,
            },
            "llm": {
                "provider": new_config.llm.provider,
                "default_provider": new_config.llm.provider,
                "fallback_chain": new_config.llm.fallback_chain,
                "model": new_config.llm.model,
            },
            "api_keys": {k: v for k, v in new_config.api_keys.model_dump().items() if v},
        }
        text = tomli_w.dumps(toml_data)
        self._config_path.write_text(text, encoding="utf-8")
        try:
            os.chmod(self._config_path, CONFIG_FILE_MODE)
        except OSError:
            pass

        self.accept()
