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
- **Status:** Concluído / Resolvido (v1.0.0)
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
   - `src/bibliotec/gui/resources/bibliotec_icon.png`: Bitmap oficial 256x256 injetado no `app.setWindowIcon` e `window.setWindowIcon`.
2. **Logo e Web GUI:**
   - Cópias em `src/bibliotec/gui/resources/` e `src/bibliotec/gui/web/logo.png`.
   - Pendência ao retomar: finalizar inserção do elemento `<img>` na toolbar e no modal "Sobre o BiblioTEC".

---

### [FEAT-UI-01] Substituição do Ícone Padrão do Python por Ícone Personalizado do BiblioTEC

- **Prioridade:** Média / Alta (Polimento de Produto)
- **Status:** Concluído / Resolvido (v1.0.1)
- **Escopo:** macOS (.app / Dock), Windows (.exe / Taskbar / Inno Setup)
- **Data do Relato:** 2026-11-08
- **Responsáveis:** Prisma (UX/UI) & Atlas (Foundation)

#### 1. Objetivo
Substituir o ícone genérico padrão do Python (exibido atualmente no Dock do macOS, na barra de tarefas do Windows e nos binários empacotados) por uma identidade visual exclusiva e personalizada do **BiblioTEC** (*Editorial Academic Workbench*), remetendo a organização acadêmica, catalogação e rigor tipográfico.

#### 2. Requisitos de Entrega
1. **Arte e Formatos Multiplataforma:**
   - **macOS (`.icns`):** Arquivo multi-resolução com camadas de 16x16 até 1024x1024 (Retina @2x), integrado em `Contents/Resources/icon.icns` do `.app`.
   - **Windows (`.ico`):** Arquivo contendo resoluções de 16x16, 32x32, 48x48, 64x64, 128x128 e 256x256 incorporado ao `BiblioTEC.exe` e ao instalador Inno Setup (`SetupIconFile`).
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

### [FEAT-PKG-03] Empacotamento Oficial Multiplataforma (macOS .dmg e Windows .exe)

- **Prioridade:** Alta (Lançamento Oficial v1.0.0)
- **Status:** Concluído / Resolvido (v1.0.0)
- **Escopo:** `.github/workflows/release.yml`, `packaging/windows_installer.iss`, GitHub Releases
- **Data do Relato:** 2026-11-08
- **Responsável:** Farol (Release & GitOps Manager) & Atlas (Foundation Engineer)

#### 1. Diretriz Estratégica de Lançamento
Conforme decisão de produto, o lançamento inicial foca na estabilização dos dois maiores ecossistemas desktop acadêmicos:
1. **macOS**: Imagem DMG com suporte a Apple Silicon / Intel e atalho Finder para `/Applications`.
2. **Windows**: Instalador `.exe` profissional com assistente moderno Inno Setup, criação de atalhos e desinstalador limpo.

#### 2. Requisitos de Entrega
1. **Compilação do Instalador Windows:**
   - Executar o workflow de CI em runner Windows (`windows-latest`).
   - Gerar o bundle via PyInstaller e compilar o instalador Inno Setup (`packaging/windows_installer.iss`).
   - Validar que o instalador crie atalhos no Menu Iniciar, Área de Trabalho e suporte desinstalação limpa.
   - Gerar o arquivo final `BiblioTEC_Setup_v1.0.0_Windows_x64.exe`.
2. **Compilação do Instalador macOS:**
   - Executar o workflow de CI em runner macOS (`macos-latest`).
   - Gerar o bundle via PyInstaller e compilar a imagem DMG com Finder layout (`packaging/build_macos.sh`).
   - Gerar o arquivo final `BiblioTEC-1.0.0-macOS.dmg`.
3. **Publicação Consolidada na Seção Assets:**
   - Anexar ambos os arquivos (`.dmg` e `.exe`) à página de releases do repositório `dcprj/bibliotec`.
   - Garantir que ambos os instaladores oficiais (macOS e Windows) apareçam listados com seus hashes SHA-256 e tamanhos.

---

## 🔑 Guia de APIs e Credenciais: Google Books API Key

### 1. Para que a chave é necessária no BiblioTEC
1. **Enriquecimento Bibliográfico Oficial:** O extrator `metadata_google_books.py` consulta o catálogo mundial do Google Books para enriquecer livros e e-books com metadados canônicos (título padronizado, nomes completos dos autores, editora, cidade, ano de publicação exato, sinopse e categorização temática), além de validar e formatar o ISBN-13.
2. **Prevenção de Rate Limiting (HTTP 429):** Requisições anônimas (sem chave) compartilham um pool restrito de cotas baseado em IP público. Em varreduras de pastas com dezenas de PDFs acadêmicos, requisições repetidas sem chave sofrem bloqueio temporário (erro `429 Too Many Requests`). A chave pessoal garante requisições dedicadas e sem bloqueio.
3. **Cota Diária Gratuita:** O Google Cloud oferece gratuitamente uma cota de 1.000 requisições por dia por projeto, o que cobre com folga qualquer biblioteca pessoal ou acadêmica.

### 2. Passo a Passo para Gerar a Chave no Google Cloud Console
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/) com a sua conta Google.
2. Selecione ou crie um projeto (ex.: `BiblioTEC`).
3. No menu de navegação lateral (☰), vá em **APIs e Serviços** > **Biblioteca**.
4. No campo de busca, pesquise por **Books API** (ou **Google Books API**) e clique em **Ativar** (Enable).
5. Após ativada, vá em **APIs e Serviços** > **Credenciais**.
6. Clique no botão superior **+ Criar Credenciais** e selecione **Chave de API**.
7. *(Boa prática de segurança)*: Clique nos três pontinhos ao lado da chave criada e selecione **Editar chave**:
   - Em **Restrições de API**, marque **Restringir chave** e selecione exclusivamente a **Books API**.
   - Salve a configuração.
8. Copie a chave gerada (iniciada por `AIzaSy...`).
9. **Configuração no BiblioTEC:**
   - **Interface Gráfica (Recomendado):** Abra o modal **Preferências (⚙️)** > aba **Chaves de API** > preencha o campo **Google Books API Key** e salve.
   - **Arquivo Local:** Adicione em `bibliotec.toml`: `google_books_api_key = "AIzaSy..."`.
   - **Variável de Ambiente:** Exporte `export BIBLIOTEC_GOOGLE_BOOKS_API_KEY="AIzaSy..."`.

---

## 🌐 Presença Web e Distribuição: Landing Page no GitHub Pages [FEAT-WEB-01]

- **Prioridade:** Média (Pós-v1.0.1)
- **Status:** Planejado
- **Responsáveis:** Prisma (UX/UI Designer) & Farol (GitOps)
- **Hospedagem:** Gratuita via GitHub Pages (`https://dcprj.github.io/bibliotec/`)

### 1. Escopo e Objetivos
1. **Página Estática Leve e Responsiva:** Desenvolvida em HTML5/CSS3 moderno na pasta `docs/` ou branch dedicada, sem dependências de frameworks pesados.
2. **Hero Section:**
   - Logotipo oficial e identidade visual do BiblioTEC.
   - Slogan acadêmico voltado a pesquisadores e estudantes de pós-graduação.
   - Botões de download inteligentes que direcionam para os assets oficiais da última release:
     - `BiblioTEC_Setup_v{VERSION}_Windows_x64.exe`
     - `BiblioTEC-{VERSION}-macOS.dmg`
3. **Showcase Visual:**
   - Demonstração da taxonomia curricular CAPES/CNPq.
   - Extração de metadados canônicos via DOI/Crossref e Google Books.
   - Resgate de documentos escaneados antigos via Docling OCR.
   - Geração de companion markdown (.md) com referências ABNT NBR 6023.
   - Garantia de privacidade 100% local (sem envio de documentos acadêmicos para a nuvem).
4. **Instruções de Instalação e FAQ:** Requisitos para macOS (Apple Silicon / Intel) e Windows 10/11.

---

## 🏛️ Governança de Engenharia: Modelo de Pull Requests & Code Review [GOV-01]

- **Prioridade:** Alta (Para as próximas sprints v1.0.2 e v1.1.0)
- **Status:** Planejado
- **Responsáveis:** Farol (Release Manager), Sentinela (AppSec) e Chefe (Arquiteto)

### 1. Regras de Proteção de Branch (`main`)
- Bloqueio de commits diretos na branch principal.
- Exigência de Pull Request aprovado e esteira de CI/CD 100% verde antes de qualquer merge.

### 2. Mapeamento de Responsabilidades (`.github/CODEOWNERS`)
- `src/bibliotec/gui/`: Revisão obrigatória de Prisma (UX/UI).
- `src/bibliotec/core/`: Revisão obrigatória de Atlas (Foundation).
- `src/bibliotec/extractors/`: Revisão obrigatória de Lince (Extractors).
- `src/bibliotec/cli/`: Revisão obrigatória de Forja (Pipeline & CLI).
- `packaging/`, `.github/workflows/`: Revisão obrigatória de Farol (Release Manager).
- Todo o código / credenciais / segurança: Gatekeeper Sentinela (AppSec).

### 3. Template de PR Padronizado (`.github/pull_request_template.md`)
- Checklist de testes unitários executados.
- Checklist de segurança da informação (ausência de chaves, sanitização de entradas e caminhos).
- Evidências gráficas para alterações de interface.

---

## 🏛️ Rebranding Oficial para TOMUS [BRAND-01]

- **Prioridade:** Alta (Alvo da versão v1.1.0)
- **Status:** Aprovado pela Direção (Dario)
- **Responsáveis:** Prisma (UX/UI Designer) & Atlas (Foundation)
- **Novo Nome Oficial:** **Tomus — Organizador Acadêmico de PDFs**
- **Conceito & Etimologia:** Do latim *tomus* (volume encadernado, seção de um compêndio ou enciclopédia do saber).
- **Identidade Visual Aprovada:** Opção 1 — Neoclássico Editorial
  - **Paleta:** Fundo Navy Slate (`#0f172a`), filetes em ouro acetinado e iluminação azul etéreo.
  - **Emblema:** Tomo encadernado clássico com páginas organizadas formando a letra **"T"**.
  - **Arquivos de Referência:**
    - Ícone: `docs/designs/tomus_branding/tomus_app_icon.jpg`
    - Banner: `docs/designs/tomus_branding/tomus_horizontal_logo.jpg`
- **Etapas de Execução para v1.1.0:**
  1. Criação dos pacotes de ícones vetoriais: `icon.icns` (macOS Retina) e `icon.ico` (Windows multi-resolução 16-256px).
  2. Atualização dos cabeçalhos, títulos da janela e logo no WebView da GUI.
  3. Atualização do `README.md` e metadados de empacotamento.
  4. Lançamento da Landing Page no GitHub Pages já ostentando a nova marca **Tomus**.

---

## 🔑 Validação Ativa de Chaves de API no Salvamento [FEAT-AUTH-02]

- **Prioridade:** Alta (UX & Resiliência - Sprint v1.1.0/v1.2.0)
- **Status:** Planejado
- **Responsáveis:** Prisma (UX/UI) & Atlas (Foundation)
- **Origem:** Demanda de Produto (Dario)

### 1. Problema Identificado
Atualmente, a aplicação grava qualquer string inserida nos campos de chave de API no arquivo de configuração sem validação imediata. Se a chave estiver expirada, digitada incorretamente ou for um token inválido (como tokens OAuth em vez de API Keys), o usuário só descobre a falha muito tempo depois, durante a execução de um lote de PDFs, gerando erros HTTP 401/403 ou paradas inesperadas.

### 2. Requisitos de Entrega
1. **Health Check Ativo no Salvamento:**
   - Ao clicar no botão **"Salvar"** no modal de Preferências (ou via comando `config set`), disparar uma verificação assíncrona leve para cada chave informada:
     - **Google Gemini:** Consulta rápida de modelos disponíveis ou teste mínimo de conexão.
     - **Google Books:** Consulta leve com a chave fornecida (`q=isbn:0000000000&key=...`).
     - **Provedores Alternativos (Groq, DeepSeek, NVIDIA):** Ping leve de autenticação (`/models`).
2. **Feedback Visual Imediato na Interface:**
   - **Chave Válida:** Indicador visual verde (badge "Ativa e Validada").
   - **Chave Inválida / Não Autorizada (HTTP 401/403):** Alerta claro e contextualizado (ex.: *"Chave da Google Books recusada pelo Google Cloud. Verifique se a Books API foi ativada nas credenciais do seu projeto"*), permitindo correção imediata.
3. **Não-Bloqueio Gracioso:**
   - Se o usuário estiver temporariamente offline no momento de salvar, informar que a chave foi gravada mas não pôde ser testada por ausência de conexão.







