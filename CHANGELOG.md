# Changelog do Tomus

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adota versionamento semântico ([Semantic Versioning](https://semver.org/lang/pt-BR/)).

## [1.1.2] - 2026-11-10

### Corrigido
- **Renomeação integral para `tomus`**: todos os pacotes, módulos e caminhos de importação renomeados de `bibliotec` para `tomus` (src/, pyproject.toml, CLI, imports internos).
- **Redação de segredos em logs (`src/tomus/core/logging.py`)**: `RedactingFilter` mascara chaves de API e tokens (`key=`, `sk-`, `nvapi-`, `gsk-`, `token=`) em todas as mensagens gravadas em `tomus.log`.
- **Path Traversal e Catálogo de Destino no QtWebChannel (`src/tomus/gui/bridge.py`)**: função `_is_safe_path()` valida containment do caminho resolvido em `source_dir`, `target_dir` e pastas do usuário, bloqueando `..`, dotfiles e diretórios sensíveis.
- **Sanitização de exceções LLM (`src/tomus/core/llm.py`, `src/tomus/core/pipeline.py`)**: `_sanitize_error_message()` aplica máscara regex a chaves de API antes de injetar em `reasoning` ou `error_message`.
- **Sanitização em `runJavaScript` (`src/tomus/gui/bridge.py`)**: payloads serializados com `json.dumps(..., ensure_ascii=False)`, sem risco de escape de string JS.
- **Prevenção de XSS em link DOI (`src/tomus/gui/web/app.js`)**: DOI validado para apenas protocolos seguros (`https://`, `http://`, `10.`); protocolos inseguros (`javascript:`, `data:`) renderizados como texto puro.
- **Silenciar logs de console JS (`src/tomus/gui/main_window.py`)**: `javaScriptConsoleMessage` imprime apenas com `verbose=True`.
- **Avisos de segurança na CLI (`src/tomus/cli/main.py`)**: flags `--api-key` e `--google-books-key` incluem aviso recomendando variáveis de ambiente.

### Adicionado
- **Identidade visual TOMUS v1.1.2**: ícones oficiais (`icon.ico` com 7 resoluções 16px–256px, `icon.icns` Retina, `icon.png` com transparência alfa), logotipo horizontal 1014x334, emblema isolado 28x28/44x44 na toolbar e modal Sobre.
- **Suporte completo a RapidOCR + ONNXRuntime no Windows**: DLLs do onnxruntime embarcadas via `binaries=binaries` no PyInstaller spec.
- **Landing Page oficial (`docs/index.html`)**: redesign editorial studio-grade com seção de créditos celebrando a parceria entre Dario e o enxame de agentes de IA.
- **README focado em macOS**: instruções de instalação atualizadas para o ecossistema Apple Silicon e Intel.

### Alterado
- **Versão**: 1.1.1 → 1.1.2 em pyproject.toml, Inno Setup, PyInstaller spec, badge da GUI web e docs/index.html.

---

## [1.0.1] - 2026-11-09

### Corrigido — Vulnerabilidades de Segurança (Relatório de Auditoria Sentinela)

#### CRT-02 — Vazamento de chaves de API em logs (`src/tomus/core/logging.py`)
- Adicionado `RedactingFilter` que faz regex replace mascarando chaves de API e tokens (`key=...`, `sk-...`, `nvapi-...`, `gsk-...`, `token=...`) em todas as mensagens de log gravadas no arquivo `tomus.log`.
- Definido nível `WARNING` para o logger `httpx`, impedindo que URLs completas com query params (incluindo `key=`) sejam gravadas em nível INFO.

#### ALT-01 e ALT-02 — Path Traversal e Catálogo de Destino no QtWebChannel (`src/tomus/gui/bridge.py`)
- Implementada função `_is_safe_path(p, allowed_roots)` que verifica containment do caminho resolvido em `source_dir`, `target_dir` e pastas do usuário, bloqueando `..`, dotfiles e diretórios sensíveis (`.ssh`, `.gnupg`, `.aws`, `.bashrc`, `/etc`, etc.).
- `revealPath()` e `openPdf()` agora validam o caminho com `_is_safe_path()` antes de abrir ou revelar; arquivos fora das pastas autorizadas são rejeitados com aviso de log.

#### MED-01 — Vazamento de chaves em exceções (`src/tomus/core/llm.py`, `src/tomus/core/pipeline.py`)
- Adicionada função `_sanitize_error_message()` que aplica máscara (regex) a chaves de API e tokens em mensagens de erro antes de injetá-las em `reasoning` ou `error_message`.
- Todas as chamadas `f"Falha na chamada ao LLM {exc}"` agora usam `_sanitize_error_message(str(exc))`.

#### MED-02 — Sanitização em `runJavaScript` (`src/tomus/gui/bridge.py`)
- Todos os payloads enviados para `web_view.page().runJavaScript` agora usam `json.dumps(..., ensure_ascii=False)`, garantindo serialização segura e sem risco de escape de string JS.

#### MED-03 — Prevenção de XSS em link DOI (`src/tomus/gui/web/app.js`)
- Na função `buildAbntCitation()`, o DOI é validado: apenas links que começam com `https://`, `http://` ou `10.` são renderizados como `<a>`; protocolos inseguros (`javascript:`, `data:`) são renderizados como texto puro sem tag `<a>`.

#### MED-04 — Silenciar logs de console JS no terminal (`src/tomus/gui/main_window.py`)
- `javaScriptConsoleMessage` agora imprime no stdout apenas quando `verbose=True` (desativado por padrão).

#### BAI-01 — Avisos de segurança na CLI (`src/tomus/cli/main.py`)
- As flags `--api-key` e `--google-books-key` agora incluem aviso no help recomendando o uso de variáveis de ambiente (`TOMUS_GEMINI_API_KEY`, `TOMUS_GOOGLE_BOOKS_API_KEY`).

---

## [1.0.0] - 2026-11-07

### Added
- **Desktop GUI Multiplataforma (`tomus.gui`)**: Bancada de trabalho de 3 painéis com identidade visual *Editorial Academic Workbench* inspirada em Zotero 7 e Things 3 (100% Anti-AI-Slop, sem emojis e sem gradientes neon).
  - Paletas semânticas *Editorial Paper* (Light) e *Technical Graphite* (Dark) com tokens imutáveis e renderização determinística via motor Qt6 `Fusion` + QSS.
  - Grade de documentos virtualizada a 60fps (`QTableView` + `QAbstractTableModel`) com 8 colunas de alta densidade e busca textual instantânea.
  - Inspetor documental com renderização tipográfica da referência **ABNT NBR 6023**, cópia rápida de citação e da ficha Markdown (`.md`) companheira.
  - Triagem manual assistida (`ManualTriageBox`) permitindo aprovar e mover documentos de `revisao_manual/` para a árvore temática CAPES/CNPq com atualização do cache SQLite.
  - Barra de telemetria ao vivo com monitor do teto de revisão manual (meta $\le 20\%$) e gaveta expansível para logs e inspeção do cache.
  - Subcomando `tomus gui` na CLI e script executável `tomus-gui`.
  - Suíte de 46 testes automatizados de interface rodando em modo offscreen (`test_gui_base.py` e `test_gui_components.py`).

## [0.4.0] - 2026-11-06

### Entregas da Sprint v0.4.0

#### [SCH-01] Schema JSON explícito para Provedores OpenAI-Compatíveis (`src/tomus/core/prompts.py`, `src/tomus/core/llm.py`)
* Prompt de sistema atualizado com especificação JSON formal completa para todos os campos (`title`, `subtitle`, `year`, `authors`, `grande_area`, `area_basica`, `tipo`, `confidence_score`, `reasoning`).
* Elevação da acurácia e riqueza de nomenclatura de arquivos gerados por DeepSeek, NVIDIA NIM, Groq e GitHub Models para o mesmo nível editorial do Gemini.
* Proteção contra respostas vazias ou nulas (`choice.message.content is None`) em todos os adaptadores HTTP.

#### [DIAG-06] Diagnósticos Detalhados e Notificação de Atalhos Ignorados (`src/tomus/storage/organizer.py`, `src/tomus/cli/main.py`)
* Diagnóstico tipado automático de arquivos não-PDF no scanner e organizador, diferenciando atalhos de internet do macOS (`.webloc`), Windows (`.url`), e-books (`.epub`, `.mobi`), documentos de escritório e mídias.
* Geração da seção `## Arquivos Não-PDF e Atalhos Ignorados` no relatório `revisao_manual/relatorio_revisao.md`, com caminho de origem e diagnóstico detalhado de cada item ignorado.
* Notificação contextual amigável na saída de console da CLI (`_print_summary`) discriminando atalhos macOS e arquivos não suportados.

#### [REV-07] Consolidação Arquitetural Pré-GUI (`organizer.py`, `enrichers.py`, `llm.py`, `pipeline.py`, `docs/designs/tomus.md`)
* Resolução de colisão por SHA-256 (`_resolve_collision`) estendida para `revisao_manual/` (`add_manual_review` e `add_error`), prevenindo sobrescrita de arquivos homônimos de subpastas distintas e evitando re-hashing desnecessário em disco.
* Correção do cabeçalho `User-Agent` (`mailto:` do Polite Pool) nas buscas por título e DOI do OpenAlex, filtro de retry para erros transitórios e extração de candidatos distintos de título/autor em `enrichers.py`.
* Inclusão de `provider_name` e `model_name` efetivos em `ClassificationResult`, persistência do modelo efetivo no cache SQLite sob fallback e suporte a `cancel_event: threading.Event | None` e `dry_run` diretamente em `run_pipeline` para acoplamento da Desktop GUI (`v1.0.0`).
* Sincronização integral da especificação de design (`docs/designs/tomus.md`) com a arquitetura `v0.4.0`.

---

## [0.3.0] - 2026-11-06

### Entregas da Sprint v0.3.0

#### [CLI-10] Novos provedores LLM: Groq e GitHub Models (`src/tomus/core/llm.py`, `src/tomus/cli/main.py`)
* `create_provider_chain()` expande suporte para provedores `"groq"` e `"github"`.
  * `"groq"`: instancia `GroqProvider` (API Groq /chat/completions), resolve `groq_api_key` via CLI > env > config.
  * `"github"`: instancia `GitHubModelsProvider` (API GitHub Models /chat/completions), resolve `github_token` via CLI > env > config.
* Flag `--provider` / `-p` na CLI aceita: `gemini`, `nvidia`, `deepseek`, `claude`, `groq`, `github`.
* `config show` exibe `api_keys.groq_api_key` e `api_keys.github_token` (mascarados).

#### [TST-11] Testes de Groq e GitHub Models (`tests/test_multi_provider.py`)
* Instanciação de `GroqProvider` e `GitHubModelsProvider`.
* Mock de chamada com sucesso para Groq (formato OpenAI) e GitHub Models (formato OpenAI).
* `FallbackLLMDispatcher`: falha no primário Groq → chaveamento automático para GitHub Models.

---

## [0.2.0] - 2026-11-06

### Entregas da Sprint v0.2.0

#### [FAL-04] Múltiplos provedores LLM com fallback automático (`src/tomus/core/llm.py`)
* `FallbackLLMDispatcher`: implementa o protocolo `LLMProvider` com cadeia ordenada de provedores.
  Tenta o primário; em caso de exceção ou resultado com reasoning 'Falha na chamada ao LLM',
  loga warning no logger `tomus.llm` e despacha para o próximo da cadeia.
* `create_provider_chain()`: fábrica que monta a cadeia a partir da `AppConfig` e flags CLI.
  Suporta provedores: `gemini`, `nvidia`, `deepseek`, `claude`.
  Resolução de chave: CLI > variável de ambiente > config.toml.
  Se o provedor primário não tiver chave, o primeiro com chave válida torna-se primário efetivo.
* Novos provedores: `DeepSeekProvider` (API DeepSeek /chat/completions) e
  `ClaudeProvider` (API Anthropic /messages), ambos com retry em 429/503/529 e
  travas determinísticas de confiança idênticas aos demais provedores.

#### [CLI-04] Novos provedores na CLI e `config show` expandido (`src/tomus/cli/main.py`)
* Flag `--provider` / `-p` aceita: `gemini`, `nvidia`, `deepseek`, `claude`.
* `_build_provider` agora usa `create_provider_chain()` para montar a cadeia com fallback.
* `config show` exibe: `llm.default_provider`, `llm.fallback_chain`,
  `api_keys.deepseek_api_key` e `api_keys.claude_api_key` (mascarados).
* Erro amigável quando nenhum provedor tem chave de API configurada.

#### [TST-05] Testes de múltiplos provedores (`tests/test_multi_provider.py`)
* Instanciação de `DeepSeekProvider` e `ClaudeProvider`.
* Mock de chamada com sucesso para DeepSeek (formato OpenAI) e Claude (formato Anthropic).
* `FallbackLLMDispatcher`: falha no primário (exceção / erro de rede) → chaveamento para o fallback.
* `FallbackLLMDispatcher`: primário retorna erro de rede → fallback responde com sucesso.
* `FallbackLLMDispatcher`: todos falham → retorna último erro.

---

## [0.1.0] - 2026-11-05

### Entregas da Release Minor v0.1.0

#### [LOG-01] Sistema de Logs Profissional (`src/tomus/core/logging.py`)
* Configuração de logging estruturado que redireciona logs detalhados para arquivo
  (`tomus.log`), mantendo o terminal 100% limpo para a barra de progresso do Rich.
* `setup_logging(verbose=verbose)`: quando `verbose=True`, anexa um StreamHandler ao console;
  caso contrário, apenas o arquivo de log recebe as mensagens.
* Silenciamento defensivo de loggers de terceiros (RapidOCR, docling, transformers, torch,
  urllib3, httpx, fitz) e variáveis de ambiente (GLOG_minloglevel, TORCH_CPP_LOG_LEVEL,
  TOKENIZERS_PARALLELISM, HF_HUB_DISABLE_PROGRESS_BARS).

#### [RES-02] Persistência de Sessão para Retomada (`src/tomus/core/session.py`)
* `SessionState` (Pydantic BaseModel): serializa estado de execução (source_dir, target_dir,
  recursive, move, dry_run, provider, model, confidence_min, workers, no_cache, created_at).
* `save_session(state)`: grava o estado em `.tomus_session.json`.
* `load_session()`: carrega o estado salvo, retornando None se o arquivo não existir ou
  estiver corrompido.
* `clear_session()`: remove o arquivo de sessão com tolerância a arquivo ausente.
* Novo comando CLI `./tomus resume` para retomada automática da execução interrompida.

#### [LLM-03] Provedor NVIDIA NIM (`src/tomus/core/llm.py`)
* `NvidiaProvider`: chama a API NVIDIA NIM em `POST /chat/completions` via httpx, com retry
  em 429/503, strip de blocos markdown JSON e travas determinísticas de confiança idênticas
  às do GeminiProvider (short-circuit < 50 chars, teto 0.50 para título genérico).
* Modelo padrão: `meta/llama-3.2-90b-vision-instruct`.
* Resolução de chave: flag CLI `--api-key` > env `TOMUS_NVIDIA_API_KEY` / `NVIDIA_API_KEY`
  > config `nvidia_api_key`.

#### [CLI-04] Integração CLI + Pipeline para release v0.1.0 (`src/tomus/cli/main.py`)
* Novas flags globais: `--verbose` / `-v` e `--provider` / `-p` (gemini ou nvidia).
* `setup_logging(verbose=verbose)` chamado no início de `_executar_organize`.
* `_build_provider` agora aceita parâmetro `provider`; suporte a NVIDIA com resolução de chave
  e erro amigável quando ausente.
* Sessão e Retomada: `save_session(SessionState(...))` no início de `_executar_organize`;
  `clear_session()` após conclusão bem-sucedida.
* Subcomando `organize` ocultado do `--help` raiz (`hidden=True`).
* Comando `tomus resume` adicionado.
* Barra de progresso Rich reescrita com `rich.console.Group` + `rich.live.Live`:
  barra consolidada no topo e linha de status do arquivo abaixo.
* Comando `tomus cache` com subcomandos `clean`/`clear`, `status` e `path`.
* Remoção do resquício `progress.update(task, description="Concluído")` do bloco `finally`.
* Bump de versão para **0.1.0** em `pyproject.toml` e `src/tomus/__init__.py`.

---

## [0.0.6] - 2026-11-04

### Adicionado
* **Arquivo companheiro (.md)**: `src/tomus/storage/companion.py` com funções
  `format_abnt_author`, `format_abnt_authors`, `format_abnt_reference`,
  `generate_companion_markdown` e `generate_duplicate_companion_markdown`.
* **Gerenciamento de duplicatas**: `LibraryOrganizer` encaminha duplicatas para
  `target_dir/duplicatas/` com resolução de colisão de nomes, `.md` companheiro e
  suporte a `move` (limpa a origem) e `copy`.
* **Comando `tomus cache`**: subcomandos `clean`/`clear`, `status` e `path` para
  gerenciar o banco SQLite `~/.cache/tomus/state.db`.
* **Barra de progresso Rich**: reescrita com `Group(prog_bar, status_prog)` e `Live`,
  com barra consolidada no topo e linha de status do arquivo abaixo.

### Alterado
* `src/tomus/storage/organizer.py`: integração do arquivo companheiro na etapa
  `add_organized` (quando `status == ORGANIZED` e não `dry_run`).

---

## [0.0.5] - 2026-11-03

### Corrigido
* **Modelo Gemini**: padrão atualizado para `gemini-3.8-flash` em `config.py`, `llm.py`
  e `tomus.toml`.
* **Fallback inteligente**: `GeminiProvider._call_gemini` tenta cadeia de modelos
  (`gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.5-flash`, `gemini-3.1-flash-lite`)
  quando o modelo atual retorna HTTP 404 NOT_FOUND.
* **Poluição do cache SQLite**: `FileCache` aceita `db_path`; nunca lê/grava resultados
  com `reasoning == 'mock'` no cache real (~/.cache/tomus/state.db); 113 entradas
  mock removidas; testes usam `db_path=tmp_path/'state.db'`.
* **CLI sem chave**: levanta erro amigável + `typer.Exit(1)` em vez de usar
  `MockLLMProvider` silenciosamente.
* **Colisão de nomes em `--dry-run`**: `LibraryOrganizer._planned_destinations`
  detecta colisões contra arquivos planejados na mesma execução, funcionando em
  modo dry-run.
* **Ambiente virtual Python 3.12**: `.venv` criado na raiz; `./tomus` re-executa
  com `.venv/bin/python` se existir.
* **Silenciamento de avisos**: `HF_HUB_DISABLE_PROGRESS_BARS=1`,
  `TOKENIZERS_PARALLELISM=false`, filtros para `google.*`, `fitz.*`, urllib3 OpenSSL,
  `SwigPy`/`swigvarlink`, `Redirects are currently not supported`, `UserWarning` do torch.
* **Bug da barra de progresso**: corrigido `NameError` no `_emit` (variável
  `completed_count` inexistente no escopo) que congelava a barra em `0/?`; eventos
  `duplicate_skipped` agora avançam a barra; `on_event` removido do callback.

---

## [0.0.4] - 2026-11-02

### Adicionado
* **Ergonomia da CLI**: `tomus -o <origem> -d <destino> [--dry-run]` executa o
  organize automaticamente sem precisar do subcomando.
* **Opções curtas**: `--origem/-o/--source` e `--destino/-d/--target` tanto no callback
  raiz quanto no subcomando `organize`.
* **Script executável `./tomus`**: adiciona `src/` ao `sys.path` automaticamente e
  chama `tomus.cli.main:main`; usa `.venv/bin/python` se existir.
* **Testes de ergonomia**: `tests/test_cli_ergonomia.py` com `typer.testing.CliRunner`
  cobrindo `-o/-d`, `--origem/--destino`, posições, opções source/target, precedência
  e casos de erro.

### Alterado
* `src/tomus/cli/main.py`: refatorado para extrair lógica comum em
  `_executar_organize`, evitando duplicação entre callback raiz e `organize`.

---

## [0.0.3] - 2026-11-01

### Adicionado (Itens 17 a 27 — Fase 2/3)
* **`src/tomus/core/prompts.py`**: prompt de sistema e payload contextual com
  truncamento de `sampled_text` a 15.000 caracteres priorizando `cip_text`; regras dos
  5 tipos documentais; autores no formato `'Sobrenome, Nome'`; catálogo fechado via
  `format_taxonomy_for_prompt`.
* **`src/tomus/core/llm.py`**: `Protocol LLMProvider`; short-circuit < 50 chars
  sem metadado externo (`confidence_score = 0.0`); `GeminiProvider` com
  `google-genai` (`response_mime_type='application/json'`,
  `response_schema=LLMClassificationOutput`); retry em HTTP 429; validação via
  `validate_or_repair_pair` forçando `confidence_score = 0.0` se retornar `None`;
  teto `min(score, 0.50)` quando título for vazio/genérico sem autor.
* **`src/tomus/storage/__init__.py`**: exporta `format_academic_filename` e
  `LibraryOrganizer`.
* **`src/tomus/storage/namer.py`**: `<autor> - <titulo> - <subtitulo> - <ano>.pdf`
  com 1/2/3+ autores; omissão de subtítulo vazio; `s.d.` quando `year` for `None`;
  normalização Unicode NFC; sanitização de proibidos; truncamento progressivo em
  fronteira de palavra garantindo ≤ 240 bytes UTF-8.
* **`src/tomus/storage/organizer.py`**: árvore temática
  `<Grande Área>/<Área Básica>/<Tipo>/<nome>.pdf`; `revisao_manual/` preservando nome
  original; `shutil.copy2` ou move seguro; `dry_run` sem pastas temáticas nem cópias;
  colisão por SHA-256 (`duplicate_skipped` ou sufixo ` (2).pdf`); gravação de
  `manifest.json` e `revisao_manual/relatorio_revisao.md`.
* **`src/tomus/core/pipeline.py`**: orquestrador de 5 estágios
  (scan → cache → extrator → enriquecer → LLM → organizador); `workers=1` padrão ou
  rede paralela com lock no OCR + finalização; `ExecutionSummary` com teto de 20%
  para `revisao_manual/`; emissão de `PipelineEvent`.
* **`src/tomus/cli/__init__.py`** e **`src/tomus/cli/main.py`**: Typer+Rich
  com comandos `organize`, `config init [--local]`, `config show`, `config path`.
* **Testes**: `tests/test_namer.py`, `tests/test_taxonomy_and_identifiers.py`,
  `tests/test_pipeline_integration.py` (31 testes não-slow).

### Alterado
* `src/tomus/core/__init__.py`: exporta novos módulos (prompts, llm).

---

## [0.0.2] - 2026-10-29

### Adicionado (Itens 12 a 16 — Fase 1, implementados pelo agente Lince)
* **`src/tomus/extractors/__init__.py`**: `extract_document_content(path, sha256)`.
* **`src/tomus/extractors/identifiers.py`**: extração de DOI por regex estrita,
  ISBN validado via `python-stdnum`, detecção de Ficha Catalográfica CIP.
* **`src/tomus/extractors/native_pdf.py`**: extração nativa via PyMuPDF das 10
  primeiras e 5 últimas páginas; decisão de necessidade de OCR.
* **`src/tomus/extractors/ocr_docling.py`**: fallback de OCR seletivo via Docling
  com recorte de páginas sem texto (máximo 8 páginas).
* **`src/tomus/core/enrichers.py`**: consultas HTTP para OpenAlex e Google Books
  com `httpx` + `tenacity` (retry 3 tentativas, timeout 8s); validação de similaridade
  `rapidfuzz.fuzz.token_set_ratio >= 88.0`.

---

## [0.0.1] - 2026-10-27

### Adicionado (Fase 1 — Itens 1 a 11)
* **`pyproject.toml`**: metadados do pacote, dependências, ponto de entrada
  `tomus = "tomus.cli.main:app"`.
* **`src/tomus/__init__.py`**: `__version__ = "0.1.0"`.
* **`src/tomus/core/__init__.py`**: exporta entidades de domínio.
* **`src/tomus/core/config.py`**: `AppConfig` com `pydantic-settings`, fontes TOML
  aninhadas, ordem de precedência (CLI > env > local TOML > global TOML), geração de
  template TOML com permissão `0600`.
* **`src/tomus/core/models.py`**: enums (`DocumentType`, `ProcessStatus`,
  `FileOperation`) e modelos Pydantic (`ExtractedDocument`, `ExternalMetadata`,
  `LLMClassificationOutput`, `FileManifestEntry`, `ExecutionSummary`, `PipelineEvent`).
* **`src/tomus/core/resources/taxonomy_capes.json`**: 9 Grandes Áreas e Áreas
  Básicas da CAPES/CNPq.
* **`src/tomus/core/taxonomy.py`**: carregamento da taxonomia,
  `validate_or_repair_pair`, `format_taxonomy_for_prompt`.
* **`src/tomus/core/scanner.py`**: varredura recursiva/plana, validação de
  assinatura `%PDF-`, SHA-256, exclusão da subárvore do destino.
* **`src/tomus/core/cache.py`**: cache SQLite em `~/.cache/tomus/state.db`
  (modo WAL), persistência apenas de classificações aprovadas.
* **`.gitignore`**: ignora ambientes virtuais, caches, chaves de API, bancos SQLite.
* **`README.md`**: documentação de instalação, configuração e uso.
