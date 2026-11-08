# Backlog do BiblioTEC

Este documento registra itens de melhoria contínua, débitos técnicos, ideias futuras e bugs reportados para tratamento em sprints posteriores.

---

## 📌 Bugs Identificados em Pacotes / Distribuição

### [BUG-PKG-01] Crash `SIGABRT` (`QMessageLogger::fatal`) ao inicializar `QWebEnginePage` no bundle macOS (.app)

- **Prioridade:** Média (Próxima Sprint de Empacotamento)
- **Status:** Concluído / Resolvido (v1.0.1)
- **Ambiente:** macOS 14+ / Apple Silicon (ARM64), pacote congelado via PyInstaller (`BiblioTEC.app`).
- **Data do Relato:** 2026-11-08
- **Responsável:** Prisma (BiblioTEC UX/UI & Desktop GUI Architect)

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

---

## 🎨 Identidade Visual e Experiência Desktop

### [FEAT-BRAND-01] Aplicação da Identidade Visual Oficial (Logo e Ícone de /logo_e_icone)

- **Prioridade:** Alta (Identidade Oficial do Aplicativo)
- **Status:** Em andamento / Pré-configurado (Pausado para atualização de SO)
- **Escopo:** `logo_e_icone/`, `packaging/icons/`, `src/bibliotec/gui/resources/`, `src/bibliotec/gui/web/`
- **Data do Relato:** 2026-11-08
- **Responsável:** Prisma (UX/UI) & Chefe

#### 1. Diagnóstico e Fontes Oficiais
Foram disponibilizadas as artes oficiais em alta resolução:
- `/Users/dario/Projetos-de-aplicativos/bibliotec/logo_e_icone/icone.png` (1254 x 1254 px)
- `/Users/dario/Projetos-de-aplicativos/bibliotec/logo_e_icone/Logo.png` (1774 x 887 px)

#### 2. Entregas Pré-processadas
1. **Ícones Multiplataforma:**
   - `packaging/icons/icon.icns`: Pacote Apple Silicon / Retina multi-camada (16x16 até 1024x1024) com transparência de cantos gerado via `iconutil`.
   - `packaging/icons/icon.ico`: Pacote multi-resolução para Windows (16, 32, 48, 64, 128, 256) integrado no instalador Inno Setup (`packaging/windows_installer.iss`).
   - `packaging/icons/icon.png`: Resolução 512x512 para o AppImage e menu `.desktop` Linux.
   - `src/bibliotec/gui/resources/bibliotec_icon.png`: Bitmap oficial 256x256 injetado no `app.setWindowIcon` e `window.setWindowIcon`.
2. **Logo e Web GUI:**
   - Cópias em `src/bibliotec/gui/resources/` e `src/bibliotec/gui/web/logo.png`.
   - Pendência ao retomar: finalizar inserção do elemento `<img>` na toolbar e no modal "Sobre o BiblioTEC".

---

### [FEAT-UI-01] Substituição do Ícone Padrão do Python por Ícone Personalizado do BiblioTEC

- **Prioridade:** Média / Alta (Polimento de Produto)
- **Status:** Concluído / Resolvido (v1.0.1)
- **Escopo:** macOS (.app / Dock), Windows (.exe / Taskbar / Inno Setup), Linux (.AppImage / Desktop Menu)
- **Data do Relato:** 2026-11-08
- **Responsáveis:** Prisma (UX/UI) & Atlas (Foundation)

#### 1. Objetivo
Substituir o ícone genérico padrão do Python (exibido atualmente no Dock do macOS, na barra de tarefas do Windows e nos binários empacotados) por uma identidade visual exclusiva e personalizada do **BiblioTEC** (*Editorial Academic Workbench*), remetendo a organização acadêmica, catalogação e rigor tipográfico.

#### 2. Requisitos de Entrega
1. **Arte e Formatos Multiplataforma:**
   - **macOS (`.icns`):** Arquivo multi-resolução com camadas de 16x16 até 1024x1024 (Retina @2x), integrado em `Contents/Resources/icon.icns` do `.app`.
   - **Windows (`.ico`):** Arquivo contendo resoluções de 16x16, 32x32, 48x48, 64x64, 128x128 e 256x256 incorporado ao `BiblioTEC.exe` e ao instalador Inno Setup (`SetupIconFile`).
   - **Linux (`.png` e `.svg`):** Ícone vetorial e bitmap 512x512 instalado em `usr/share/icons/hicolor/512x512/apps/bibliotec.png` no `AppDir` do AppImage.
2. **Runtime do Aplicativo (`src/bibliotec/gui/app.py`):**
   - Configurar `app.setWindowIcon(QIcon(icon_path))` no `QApplication` e em `MainWindow` para que janelas secundárias e diálogos modais herdem o ícone oficial.
   - Definir `AppUserModelID` no Windows (`ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID`) para garantir que o Windows agrupe a janela corretamente na barra de tarefas com o ícone customizado.
3. **Scripts de Empacotamento (`packaging/`):**
   - No `packaging/pyinstaller.spec`: adicionar parâmetro `icon='assets/icons/bibliotec.icns'` no bloco `BNDL` (macOS) e `icon='assets/icons/bibliotec.ico'` no bloco `EXE` (Windows).
   - No `packaging/windows_installer.iss`: configurar `SetupIconFile=..\assets\icons\bibliotec.ico` e `UninstallDisplayIcon={app}\BiblioTEC.exe`.

---

## 📦 Empacotamento e Distribuição macOS

### [FEAT-PKG-02] Janela DMG Profissional no macOS com Atalho "Arrastar para Aplicativos" (Drag-to-Applications)

- **Prioridade:** Média (Polimento da Experiência macOS)
- **Status:** Concluído / Resolvido (v1.0.1)
- **Escopo:** `packaging/build_macos.sh`, `.github/workflows/release.yml`
- **Data do Relato:** 2026-11-08
- **Responsável:** Atlas (BiblioTEC Foundation Engineer)

#### 1. Objetivo
Ao montar e abrir o arquivo `BiblioTEC-1.0.0-macOS.dmg`, o Finder deve abrir automaticamente uma janela limpa e customizada contendo:
- O ícone do aplicativo **`BiblioTEC.app`** à esquerda.
- Um atalho simbólico nativo para a pasta **`Applications` (Aplicativos)** à direita.
- (Opcional) Fundo ilustrativo com seta discreta e texto instrucional orientando a arrastar o aplicativo para instalar.

#### 2. Requisitos Técnicos
1. **Estrutura do Volume DMG:**
   - Criar link simbólico `ln -s /Applications "${DMG_TEMP_DIR}/Applications"` no diretório base da imagem.
2. **Posicionamento e Propriedades do Finder:**
   - Utilizar ferramenta automatizada como `create-dmg` ou script AppleScript / `dmgbuild` para configurar:
     - Dimensão da janela (ex.: 540x380 px).
     - Tamanho dos ícones (ex.: 100px ou 128px).
     - Coordenadas exatas dos ícones (ex.: `BiblioTEC.app` em `(140, 190)` e `Applications` em `(400, 190)`).
     - Ocultação da barra lateral e barra de status do Finder no volume montado.
3. **Automação no CI/CD e Script Local:**
   - Atualizar `packaging/build_macos.sh` para suportar `create-dmg` (instalável via Homebrew ou GitHub Actions `brew install create-dmg`).
   - Atualizar a etapa `build-macos` no `.github/workflows/release.yml` para gerar o `.dmg` com o layout padronizado.

---

## 📦 Distribuição Multiplataforma e Assets no GitHub Releases

### [FEAT-PKG-03] Revisão e Empacotamento Completo dos Assets de Windows (.exe) e Linux (.AppImage) no GitHub Releases

- **Prioridade:** Alta (Completude do Catálogo de Lançamento)
- **Status:** Aberto / Mapeado
- **Escopo:** `.github/workflows/release.yml`, `packaging/windows_installer.iss`, `packaging/build_linux_appimage.sh`, GitHub Releases
- **Data do Relato:** 2026-11-08
- **Responsável:** Farol (Release & GitOps Manager) & Atlas (Foundation Engineer)

#### 1. Sintoma e Diagnóstico
Na página oficial de releases ([https://github.com/dcprj/bibliotec/releases](https://github.com/dcprj/bibliotec/releases)), apenas o pacote para macOS (`BiblioTEC-1.0.0-macOS.dmg`) está disponível na seção de **Assets** para download.
Os instaladores de Windows (`BiblioTEC_Setup_v1.0.0_Windows_x64.exe`) e Linux (`BiblioTEC-1.0.0-x86_64.AppImage`) ainda não foram compilados e anexados à release.

#### 2. Requisitos de Entrega
1. **Compilação do Instalador Windows:**
   - Executar o workflow de CI em runner Windows (`windows-latest`).
   - Gerar o bundle via PyInstaller e compilar o instalador Inno Setup (`packaging/windows_installer.iss`).
   - Validar que o instalador crie atalhos no Menu Iniciar, Área de Trabalho e suporte desinstalação limpa.
   - Gerar o arquivo final `BiblioTEC_Setup_v1.0.0_Windows_x64.exe` (ou v1.0.1).
2. **Compilação do Executável Linux AppImage:**
   - Executar o workflow de CI em runner Linux (`ubuntu-22.04`).
   - Configurar `appimagetool` com as bibliotecas essenciais (`fuse`, `libfuse2`, Qt6 dependencies).
   - Gerar o arquivo universal portátil `BiblioTEC-1.0.0-x86_64.AppImage` (ou v1.0.1).
3. **Publicação Consolidada na Seção Assets:**
   - Anexar ambos os arquivos (`.exe` e `.AppImage`) à página de releases do repositório `dcprj/bibliotec`.
   - Garantir que todos os 3 instaladores (macOS, Windows, Linux) apareçam listados com seus hashes SHA-256 e tamanhos.



