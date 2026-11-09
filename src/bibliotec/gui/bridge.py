"""Ponte de comunicação bidirecional (QWebChannel) entre Python e o frontend Web.

Permite que a interface HTML5/CSS moderna invoque métodos do motor
e receba eventos de streaming de processamento em tempo real.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget

from bibliotec.core.config import AppConfig
from bibliotec.core.models import FileManifestEntry, PipelineEvent, ProcessStatus
from bibliotec.gui.worker import ManualTriageService, PipelineWorker


class WebBridge(QObject):
    """Ponte QWebChannel exposta ao JavaScript como ``window.backend``."""

    pipelineEvent = Signal(str)
    pipelineFinished = Signal(str)
    sourceChanged = Signal(str)
    targetChanged = Signal(str)
    keyStatusChanged = Signal(bool)

    def __init__(
        self,
        config: AppConfig,
        parent_widget: QWidget | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.config = config
        self.parent_widget = parent_widget
        self.source_dir = ""
        self.target_dir = ""
        self.worker: PipelineWorker | None = None
        self.triage_service: ManualTriageService | None = None

    # ------------------------------------------------------------------ #
    # Estado inicial & Validação de Chaves
    # ------------------------------------------------------------------ #

    @Slot(str, result=bool)
    def checkProviderKey(self, provider: str) -> bool:
        """Verifica se o provedor especificado possui chave configurada (TOML ou ENV)."""
        import os

        prov = (provider or "").strip().lower()
        if prov == "gemini":
            return bool(
                self.config.api_keys.gemini_api_key
                or os.getenv("BIBLIOTEC_GEMINI_API_KEY")
                or os.getenv("GEMINI_API_KEY")
            )
        elif prov == "groq":
            return bool(
                self.config.api_keys.groq_api_key
                or os.getenv("BIBLIOTEC_GROQ_API_KEY")
                or os.getenv("GROQ_API_KEY")
            )
        elif prov == "nvidia":
            return bool(
                self.config.api_keys.nvidia_api_key
                or os.getenv("BIBLIOTEC_NVIDIA_API_KEY")
                or os.getenv("NVIDIA_API_KEY")
            )
        elif prov == "deepseek":
            return bool(
                self.config.api_keys.deepseek_api_key
                or os.getenv("BIBLIOTEC_DEEPSEEK_API_KEY")
                or os.getenv("DEEPSEEK_API_KEY")
            )
        elif prov == "claude":
            return bool(
                self.config.api_keys.claude_api_key
                or os.getenv("BIBLIOTEC_CLAUDE_API_KEY")
                or os.getenv("CLAUDE_API_KEY")
                or os.getenv("ANTHROPIC_API_KEY")
            )
        elif prov == "github":
            return bool(
                self.config.api_keys.github_token
                or os.getenv("BIBLIOTEC_GITHUB_TOKEN")
                or os.getenv("GITHUB_TOKEN")
                or os.getenv("GH_TOKEN")
            )
        return False

    @Slot(result=str)
    def getInitialState(self) -> str:
        initial_provider = self.config.llm.provider or "gemini"
        has_key = self.checkProviderKey(initial_provider)
        return json.dumps({
            "source": self.source_dir,
            "target": self.target_dir,
            "provider": initial_provider,
            "hasKey": bool(has_key),
        })

    # ------------------------------------------------------------------ #
    # Seleção de Pastas
    # ------------------------------------------------------------------ #

    @Slot(result=str)
    def browseSource(self) -> str:
        path = QFileDialog.getExistingDirectory(
            self.parent_widget,
            "Selecionar Diretório de Origem dos PDFs",
            self.source_dir or str(Path.home()),
        )
        if path:
            self.source_dir = path
            self.sourceChanged.emit(path)
        return path or ""

    @Slot(result=str)
    def browseTarget(self) -> str:
        path = QFileDialog.getExistingDirectory(
            self.parent_widget,
            "Selecionar Diretório de Destino da Biblioteca",
            self.target_dir or str(Path.home()),
        )
        if path:
            self.target_dir = path
            self.targetChanged.emit(path)
        return path or ""

    # ------------------------------------------------------------------ #
    # Pipeline & Execução
    # ------------------------------------------------------------------ #

    @Slot(str)
    def startOrganize(self, params_json: str) -> None:
        try:
            params = json.loads(params_json)
        except Exception:
            params = {}

        source = Path(params.get("source_dir", self.source_dir))
        target = Path(params.get("target_dir", self.target_dir))
        provider_name = params.get("provider", "gemini")
        file_operation = params.get("file_operation", "copy")
        recursive = bool(params.get("recursive", True))
        dry_run = bool(params.get("dry_run", False))

        self.source_dir = str(source)
        self.target_dir = str(target)

        # Clonar configuração e atualizar parâmetros
        cfg = AppConfig(**self.config.model_dump())
        cfg.general.file_operation = file_operation
        cfg.general.recursive = recursive
        cfg.llm.provider = provider_name

        model_defaults = {
            "gemini": "gemini-3.5-flash",
            "groq": "llama-3.3-70b-versatile",
            "nvidia": "nvidia/llama-3.1-nemotron-70b-instruct",
            "deepseek": "deepseek-flash",
            "claude": "claude-3-5-sonnet-latest",
            "github": "gpt-4o",
        }
        if provider_name in model_defaults:
            cfg.llm.model = model_defaults[provider_name]

        self.triage_service = ManualTriageService(target, cfg)

        workers = max(1, int(cfg.general.workers))
        use_cache = bool(cfg.general.use_cache)

        self.worker = PipelineWorker(
            source_dir=source,
            target_dir=target,
            config=cfg,
            dry_run=dry_run,
            use_cache=use_cache,
            workers=workers,
            parent=self,
        )
        self.worker.event_received.connect(self._on_worker_event)
        self.worker.pipeline_finished.connect(self._on_worker_finished)
        self.worker.pipeline_failed.connect(self._on_worker_failed)
        self.worker.start()

    @Slot()
    def cancelPipeline(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.worker.request_cancel()

    def _on_worker_event(self, event: PipelineEvent) -> None:
        try:
            payload = event.model_dump()
            payload_json = json.dumps(payload)
            self.pipelineEvent.emit(payload_json)

            # Invocação direta no V8 do Chromium para entrega imediata garantida
            if self.parent_widget and hasattr(self.parent_widget, "web_view"):
                js = f"if (window.handlePipelineEvent) {{ window.handlePipelineEvent({payload_json}); }}"
                self.parent_widget.web_view.page().runJavaScript(js)
        except Exception as exc:
            print(f"[WebBridge] Erro em _on_worker_event: {exc}", file=sys.stderr)

    def _on_worker_finished(self, summary: Any, was_cancelled: bool) -> None:
        try:
            data = {
                "total_scanned": summary.total_scanned,
                "organized_count": summary.organized_count,
                "manual_review_count": summary.manual_review_count,
                "duplicate_skipped_count": summary.duplicate_skipped_count,
                "ignored_non_pdf_count": summary.ignored_non_pdf_count,
                "error_count": summary.error_count,
                "manual_review_ratio": summary.manual_review_ratio,
                "exceeded_manual_review_ceiling": summary.exceeded_manual_review_ceiling,
                "was_cancelled": was_cancelled,
            }
            data_json = json.dumps(data)
            self.pipelineFinished.emit(data_json)

            if self.parent_widget and hasattr(self.parent_widget, "web_view"):
                js = f"if (window.handlePipelineFinished) {{ window.handlePipelineFinished({data_json}); }}"
                self.parent_widget.web_view.page().runJavaScript(js)
        except Exception as exc:
            print(f"[WebBridge] Erro em _on_worker_finished: {exc}", file=sys.stderr)

    def _on_worker_failed(self, error_msg: str) -> None:
        try:
            data = {
                "error": error_msg,
                "was_cancelled": False,
            }
            data_json = json.dumps(data)
            self.pipelineFinished.emit(data_json)

            if self.parent_widget and hasattr(self.parent_widget, "web_view"):
                js = f"if (window.handlePipelineFinished) {{ window.handlePipelineFinished({data_json}); }}"
                self.parent_widget.web_view.page().runJavaScript(js)
        except Exception as exc:
            print(f"[WebBridge] Erro em _on_worker_failed: {exc}", file=sys.stderr)

    # ------------------------------------------------------------------ #
    # Ações Contextuais de Arquivos (Nativas macOS / Multiplataforma)
    # ------------------------------------------------------------------ #

    @Slot(str)
    def openPdf(self, path: str) -> None:
        if not path:
            return
        p = Path(path)
        if not p.exists():
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.resolve())))

    @Slot(str)
    def revealPath(self, path: str) -> None:
        if not path:
            return
        p = Path(path).resolve()
        target = p if p.exists() else p.parent
        if sys.platform == "darwin":
            subprocess.run(["open", "-R", str(p if p.exists() else target)])
        elif sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{p}"])
        else:
            subprocess.run(["xdg-open", str(target)])

    @Slot(str)
    def openExternalUrl(self, url: str) -> None:
        """Abrir link ou documentação externa no navegador padrão do sistema."""
        if not url:
            return
        QDesktopServices.openUrl(QUrl(url))

    # ------------------------------------------------------------------ #
    # Triagem Manual Assistida
    # ------------------------------------------------------------------ #

    @Slot(str, result=bool)
    def approveManualTriage(self, triage_json: str) -> bool:
        if not self.triage_service:
            return False
        try:
            data = json.loads(triage_json)
            entry = FileManifestEntry(
                source_path=data["source_path"],
                destination_path=None,
                sha256="",
                status=ProcessStatus.MANUAL_REVIEW,
            )
            updated = self.triage_service.approve_and_materialize(
                entry=entry,
                grande_area=data["grande_area"],
                area_basica=data["area_basica"],
                tipo=data.get("tipo", "Outros"),
                title=data["title"],
                subtitle=data.get("subtitle", ""),
                authors=data.get("authors", []),
                year=data.get("year"),
            )
            # Notificar o frontend com evento de atualização
            event = PipelineEvent(
                stage="organizer",
                source_path=updated.source_path,
                destination_path=updated.destination_path,
                sha256=updated.sha256,
                status=ProcessStatus.ORGANIZED.value,
                message=f"Aprovado manualmente: {Path(updated.destination_path or '').name}",
                classification=updated.classification,
            )
            self._on_worker_event(event)
            return True
        except Exception as exc:
            print(f"[WebBridge] Erro na triagem manual: {exc}")
            return False

    # ------------------------------------------------------------------ #
    # Preferências & Cache
    # ------------------------------------------------------------------ #

    @Slot()
    def openPreferences(self) -> None:
        from bibliotec.gui.widgets.preferences_dialog import PreferencesDialog

        dlg = PreferencesDialog(self.config, parent=self.parent_widget)
        if dlg.exec():
            # Recarregar AppConfig a partir do disco para sincronização total
            from bibliotec.core.config import AppConfig

            self.config = AppConfig()

            # Atualizar status da chave para o provedor selecionado
            current_provider = self.config.llm.provider or "gemini"
            has_key = self.checkProviderKey(current_provider)
            self.keyStatusChanged.emit(bool(has_key))

    @Slot()
    def openCacheDialog(self) -> None:
        try:
            from bibliotec.core.cache import FileCache

            cache = FileCache(enabled=True)
            total = cache.count()
            db_path = str(cache.db_path)

            box = QMessageBox(self.parent_widget)
            box.setWindowTitle("Gerenciamento de Cache — BiblioTEC")
            box.setIcon(QMessageBox.Icon.Information)
            box.setText(f"Entradas ativas no cache SQLite: {total}\nLocalização: {db_path}")

            btn_clear = box.addButton("Esvaziar Cache", QMessageBox.ButtonRole.DestructiveRole)
            btn_close = box.addButton("Fechar", QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(btn_close)

            box.setStyleSheet("""
                QMessageBox {
                    background-color: #FFFFFF;
                }
                QLabel {
                    color: #0F172A;
                    font-size: 13px;
                    background-color: transparent;
                }
                QPushButton {
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-size: 13px;
                    font-weight: 500;
                }
            """)
            btn_clear.setStyleSheet("background-color: #DC2626; color: #FFFFFF; border: none; font-weight: 600; padding: 6px 14px;")
            btn_close.setStyleSheet("background-color: #1E3A8A; color: #FFFFFF; border: none; font-weight: 600; padding: 6px 18px;")

            box.exec()

            if box.clickedButton() == btn_clear:
                confirm = QMessageBox(self.parent_widget)
                confirm.setWindowTitle("Confirmar Limpeza")
                confirm.setIcon(QMessageBox.Icon.Warning)
                confirm.setText(f"Deseja realmente apagar todas as {total} entradas salvas no cache?\n\nIsso forçará a reclassificação completa de todos os PDFs em futuras execuções.")
                btn_yes = confirm.addButton("Sim, Esvaziar", QMessageBox.ButtonRole.YesRole)
                btn_no = confirm.addButton("Cancelar", QMessageBox.ButtonRole.NoRole)
                confirm.setDefaultButton(btn_no)
                confirm.setStyleSheet("QMessageBox { background-color: #FFFFFF; } QLabel { color: #0F172A; font-size: 13px; }")
                btn_yes.setStyleSheet("background-color: #DC2626; color: #FFFFFF; border: none; border-radius: 6px; padding: 6px 14px; font-weight: 600;")
                btn_no.setStyleSheet("background-color: #F1F5F9; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 14px; font-weight: 500;")
                confirm.exec()
                if confirm.clickedButton() == btn_yes:
                    cache.clear()
                    success_box = QMessageBox(self.parent_widget)
                    success_box.setWindowTitle("Cache Limpo")
                    success_box.setIcon(QMessageBox.Icon.Information)
                    success_box.setText("O cache foi esvaziado com sucesso.")
                    success_box.setStyleSheet("QMessageBox { background-color: #FFFFFF; } QLabel { color: #0F172A; }")
                    success_box.exec()
            cache.close()
        except Exception as exc:
            print(f"[WebBridge] Erro ao abrir diálogo de cache: {exc}", file=sys.stderr)
            box = QMessageBox(self.parent_widget)
            box.setWindowTitle("Aviso de Cache")
            box.setIcon(QMessageBox.Icon.Warning)
            box.setText(f"Não foi possível gerenciar o cache:\n{exc}")
            box.setStyleSheet("QMessageBox { background-color: #FFFFFF; } QLabel { color: #0F172A; }")
            box.exec()
