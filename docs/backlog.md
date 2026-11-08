# Backlog do BiblioTEC

Este documento registra itens de melhoria contínua, débitos técnicos, ideias futuras e bugs reportados para tratamento em sprints posteriores.

---

## 📌 Bugs Identificados em Pacotes / Distribuição

### [BUG-PKG-01] Crash `SIGABRT` (`QMessageLogger::fatal`) ao inicializar `QWebEnginePage` no bundle macOS (.app)

- **Prioridade:** Média (Próxima Sprint de Empacotamento)
- **Status:** Aberto / Mapeado
- **Ambiente:** macOS 14+ / Apple Silicon (ARM64), pacote congelado via PyInstaller (`BiblioTEC.app`).
- **Data do Relato:** 2026-11-08

#### 1. Sintoma e Log de Falha
Ao iniciar o binário congelado `BiblioTEC.app` (fora do interpretador Python direto do `.venv`), o aplicativo aborta imediatamente na inicialização:
```text
Exception Type:    EXC_CRASH (SIGABRT)
Termination Reason: Namespace SIGNAL, Code 6, Abort trap: 6
Application Specific Information: abort() called

Thread 0 Crashed (Dispatch queue: com.apple.main-thread):
0  libsystem_kernel.dylib   __pthread_kill + 8
1  libsystem_pthread.dylib  pthread_kill + 296
2  libsystem_c.dylib        abort + 148
3  QtCore                   QMessageLogger::fatal(char const*, ...) const + 96
4  QtWebEngineCore          QtWebEngineCore::WebContentsAdapter::WebContentsAdapter() + 96
5  QtWebEngineCore          QWebEnginePagePrivate::QWebEnginePagePrivate(...) + 68
6  QtWebEngineCore          QWebEnginePage::QWebEnginePage(QObject*) + 52
7  QtWebEngineCore.abi3.so  Sbk_QWebEnginePage_Init(...) + 1144
```

#### 2. Causa Raiz Técnica
1. **Localização do `QtWebEngineProcess` e Recursos do Chromium:**  
   No empacotamento com PyInstaller no macOS, o motor Chromium do `QtWebEngineCore` exige o executável auxiliar `QtWebEngineProcess.app` e os arquivos `.pak` (`qtwebengine_resources.pak`, `icudtl.dat`, pastas `locales/`). Quando o bundle `.app` não resolve a árvore padrão do Framework Qt, o `QWebEnginePage` invoca `QMessageLogger::fatal()` gerando um `abort()`.
2. **Chromium Sandbox Confinement:**  
   Em bundles não assinados ou sem Hardened Runtime e entitlements de JIT (`com.apple.security.cs.allow-jit`, `com.apple.security.cs.allow-unsigned-executable-memory`), o sandbox padrão do Chromium pode disparar violação de integridade de processo no macOS Sonoma/Sequoia.

#### 3. Plano de Correção Mapeado
1. **Configuração Defensiva de Ambiente em `src/bibliotec/gui/app.py`:**
   - Injetar flags de desativação de sandbox antes da criação do `QApplication`:
     ```python
     import os, sys
     if getattr(sys, "frozen", False):
         os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")
         # Apontar QTWEBENGINE_PROCESS_PATH se necessário
         process_path = os.path.join(sys._MEIPASS, "PySide6", "Qt", "lib", "QtWebEngineCore.framework", "Helpers", "QtWebEngineProcess.app", "Contents", "MacOS", "QtWebEngineProcess")
         if os.path.exists(process_path):
             os.environ["QTWEBENGINE_PROCESS_PATH"] = process_path
     ```
2. **Ajuste no `packaging/pyinstaller.spec`:**
   - Garantir coleta explícita de `QtWebEngineProcess.app` e arquivos de recursos `.pak` via `collect_data_files('PySide6')` ou hook customizado.
3. **Mecanismo de Resiliência / Fallback Gracioso:**
   - Proteger a instanciação do `QWebEngineView` com bloco `try/except`. Se o motor WebEngine falhar no ambiente congelado do usuário, alternar automaticamente para a bancada nativa pura (`QtWidgets.QTableView` + `QSplitter` nativo já implementada em `document_table.py` e `inspector.py`).
