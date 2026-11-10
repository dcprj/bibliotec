# Relatório de Prontidão de Implementação (Stage 9 — Implementation Readiness Test)

* **Arquivo Auditado:** [tomus.md](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L214-L324)
* **Escopo (`DetailedRange`):** Linhas 214–324 (`## Detailed Implementation`)
* **Base de Código de Referência:** `v0.4.0` ([CHANGELOG.md](file:///Users/dario/Projetos-de-aplicativos/tomus/CHANGELOG.md), [pyproject.toml](file:///Users/dario/Projetos-de-aplicativos/tomus/pyproject.toml))
* **Personas Revisoras:** Pragmatic Tech Lead (`egm-implementation-readiness`), Pedantic Codebase Auditor (`egm-codebase-details`) e Technical Copy Editor (`egm-style`)

---

## Resumo Executivo

A auditoria detalhada das linhas `214–324` de [tomus.md](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L214-L324) consolidou **10 achados deduplicados** (**3 Blockers**, **4 Majors** e **3 Nits**):

1. **Omissão de 3 Módulos de Produção da `v0.4.0`:** A lista unificada de arquivos (`Itens 1–27`) não inclui [`src/tomus/core/logging.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/logging.py), [`src/tomus/core/session.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/session.py) e [`src/tomus/storage/companion.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/companion.py), nem as suítes de teste adicionadas entre a `v0.1.0` e a `v0.4.0`.
2. **Descompasso entre Contratos Especificados e Módulos Reais:** Os Itens 4 (`__init__.py`), 5 (`core/__init__.py`), 6 (`config.py`), 17 (`prompts.py`), 18 (`llm.py`), 21 (`organizer.py`), 22 (`pipeline.py`) e 24 (`cli/main.py`) descrevem assinaturas e comportamentos da `v0.1.0` e trazem o rótulo `(Criar)` no tempo futuro.
3. **Prontidão da Fronteira `tomus.core` para a Desktop GUI `v1.0.0`:** A especificação e a fronteira do `core` precisam consolidar os campos de progresso de `PipelineEvent` (`total_files`, `completed_files`, `timestamp`), a exportação de `run_pipeline` e `create_provider_chain` em `core/__init__.py` e o desacoplamento do carregamento de configuração/provedores hoje residente em `cli/main.py`.

---

## 🔴 Achados Bloqueantes (Blockers)

### 1. [IMPL-01] Omissão Completa de Três Módulos de Produção da `v0.4.0` (`logging.py`, `session.py`, `companion.py`)
* **Severidade:** Blocker
* **Fontes:** `egm-implementation-readiness` (#1), `egm-codebase-details` (#1), `egm-style` (#1)
* **Escopo Afetado:** [tomus.md](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L216-L324) vs. [`src/tomus/core/logging.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/logging.py#L1-L98), [`src/tomus/core/session.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/session.py#L1-L62) e [`src/tomus/storage/companion.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/companion.py#L1-L255)
* **Descrição e Orientação Técnica:**
  A seção `## Detailed Implementation` omite três módulos que integram o fluxo de produção da `v0.4.0`:
  1. **[`src/tomus/core/logging.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/logging.py) (`[LOG-01]`):** Implementa `setup_logging(log_file="tomus.log", verbose=False, level=logging.INFO)` e `get_logger(name)`, define variáveis de ambiente defensivas (`GLOG_minloglevel="2"`, `TORCH_CPP_LOG_LEVEL="ERROR"`, `TOKENIZERS_PARALLELISM="false"`, `HF_HUB_DISABLE_PROGRESS_BARS="1"`), redireciona logs de tomusas de terceiros (`_THIRD_PARTY_LOGGERS`: `RapidOCR`, `docling`, `docling_core`, `transformers`, `torch`, `urllib3`, `httpx`, `fitz`) para arquivo e só anexa `StreamHandler` ao console quando `verbose=True`.
  2. **[`src/tomus/core/session.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/session.py) (`[RES-02]`):** Define `SESSION_FILE = Path(".tomus_session.json")`, o modelo Pydantic `SessionState` (`source_dir`, `target_dir`, `recursive`, `move`, `dry_run`, `provider`, `model`, `confidence_min`, `workers`, `no_cache`, `created_at`) e as funções `save_session`, `load_session` e `clear_session`.
  3. **[`src/tomus/storage/companion.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/companion.py) (`[CMP-01]`, `[CMP-02]`):** Implementa `format_abnt_author`, `format_abnt_authors`, `format_abnt_reference`, `generate_companion_markdown` (gera `.md` com Front Matter YAML, timestamp local humanizado `DD/MM/YYYY HH:MM:SS` e referência ABNT NBR 6023 ao lado de cada PDF organizado) e `generate_duplicate_companion_markdown` (gera `.md` na pasta `duplicatas/` apontando para a obra canônica).
* **Ação Recomendada:** Incluir `logging.py`, `session.py` e `companion.py` na lista unificada com suas assinaturas e responsabilidades.

---

### 2. [IMPL-02] Rótulos `(Criar)` no Tempo Futuro e Divergências em `src/tomus/__init__.py` e `src/tomus/core/__init__.py`
* **Severidade:** Blocker
* **Fontes:** `egm-style` (#1, #2), `egm-codebase-details` (#2, #3), `egm-implementation-readiness` (#4, #8)
* **Escopo Afetado:** Introdução ([L216](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L216)), Item 4 ([L230–L232](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L230-L232)), Item 5 ([L234–L236](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L234-L236)) e todos os 27 itens ([L218–L324](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L218-L324))
* **Descrição e Orientação Técnica:**
  1. **Marcadores `(Criar)` e tempo futuro:** Todos os 27 itens estão rotulados como `(Criar)` e descritos no futuro, embora já estejam implementados na `v0.4.0`.
  2. **Item 4 (`src/tomus/__init__.py`):** O documento afirma que o módulo define `__version__ = "0.1.0"`, expõe a API pública de alto nível e centraliza a versão usada no cabeçalho `User-Agent`. Na realidade, [`src/tomus/__init__.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/__init__.py#L1-L20) define `__version__ = "0.4.0"`, configura variáveis de ambiente (`HF_HUB_DISABLE_PROGRESS_BARS`, `TOKENIZERS_PARALLELISM`) e filtros `warnings.filterwarnings`, enquanto [`enrichers.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/enrichers.py#L34) declara `_USER_AGENT` como string literal.
  3. **Item 5 (`src/tomus/core/__init__.py`):** O documento afirma que `core/__init__.py` exporta o orquestrador do pipeline, mas [`src/tomus/core/__init__.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/__init__.py#L39-L73) **não exporta `run_pipeline`** (nem os novos provedores e `create_provider_chain`), enquanto exporta os símbolos de `logging.py` e `session.py`.
* **Ação Recomendada:** Calibrar o tempo verbal e os rótulos da seção para o estado `v0.4.0`, atualizar a versão para `0.4.0` no Item 4 e alinhar as exportações de `src/tomus/core/__init__.py` no Item 5.

---

### 3. [IMPL-03] Especificação Incompleta de `src/tomus/core/llm.py` e `src/tomus/storage/organizer.py`
* **Severidade:** Blocker
* **Fontes:** `egm-implementation-readiness` (#2, #3), `egm-codebase-details` (#4, #6), `egm-style` (#3)
* **Escopo Afetado:** Item 18 ([L286–L288](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L286-L288)) e Item 21 ([L298–L300](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L298-L300)) vs. [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1-L1309) e [`organizer.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/organizer.py#L1-L470)
* **Descrição e Orientação Técnica:**
  1. **Em `src/tomus/core/llm.py` (Item 18):** O texto documenta apenas `GeminiProvider`. Na `v0.4.0`, o módulo implementa o dataclass `ClassificationResult`, 6 provedores de produção (`GeminiProvider` com modelo `gemini-3.5-flash` e fallback 404, `NvidiaProvider` com `nvidia/nemotron-3.5-lightning-30b-a3b` e fallback `reasoning_content`, `DeepSeekProvider` com `deepseek-flash`, `ClaudeProvider` com `claude-3-5-haiku-20241022`, `GroqProvider` com `openai/gpt-oss-20b`, `GitHubModelsProvider` com `gpt-4o`), `MockLLMProvider`, o despachante [`FallbackLLMDispatcher`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1059-L1172) e a fábrica [`create_provider_chain`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1175-L1309).
  2. **Em `src/tomus/storage/organizer.py` (Item 21):** O texto omite:
     * A cópia/movimentação física de duplicatas exatas (`duplicate_skipped`) para `<TARGET_DIR>/duplicatas/<nome>` acompanhada de `.md` companheiro (`generate_duplicate_companion_markdown`);
     * A geração de `<destination_path>.md` ao lado de cada PDF aprovado na árvore temática (`generate_companion_markdown`);
     * O dicionário em memória `_planned_destinations: dict[Path, str]` para detecção de colisões durante `--dry-run`;
     * O método `add_ignored_non_pdf` e a seção `## Arquivos Não-PDF e Atalhos Ignorados` em `revisao_manual/relatorio_revisao.md` (`[DIAG-06]`).
* **Ação Recomendada:** Atualizar integralmente os Itens 18 e 21 com todos os componentes e contratos da `v0.4.0`.

---

## 🟡 Achados Principais (Majors)

### 4. [IMPL-04] Lacunas na Fronteira `tomus.core` (`models.py` e `pipeline.py`) para a Desktop GUI `v1.0.0`
* **Severidade:** Major
* **Fontes:** `egm-implementation-readiness` (#4)
* **Escopo Afetado:** Item 7 ([L242–L244](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L242-L244)) e Item 22 ([L302–L304](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L302-L304)) vs. [`models.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/models.py#L110-L119) e [`pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/pipeline.py#L280-L419)
* **Descrição e Orientação Técnica:**
  1. **Campos de progresso em `PipelineEvent` (Item 7):** `PipelineEvent` inclui `total_files: int | None = None`, `completed_files: int | None = None` e `timestamp: str` (ISO-8601), atualizados de forma thread-safe em `pipeline.py` para alimentar barras de progresso na CLI e na futura GUI.
  2. **Injeção padrão de provedor e `dry_run` em `run_pipeline` (Item 22):** Quando `provider is None`, [`run_pipeline`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/pipeline.py#L354-L359) verifica apenas `config.api_keys.gemini_api_key` em vez de chamar `create_provider_chain(config)`, e fixa `dry_run=False` ao instanciar `LibraryOrganizer` internamente, forçando a CLI (e a futura GUI) a construir `LibraryOrganizer` e `create_provider_chain` manualmente fora de `run_pipeline`.
* **Ação Recomendada:** Documentar os campos completos de `PipelineEvent` no Item 7 e padronizar `run_pipeline` no Item 22 para utilizar `create_provider_chain(config)` por padrão e expor suporte a `dry_run` / `cancel_event`.

---

### 5. [IMPL-05] Especificação Desatualizada de `src/tomus/core/config.py` (`FilteredTomlSettingsSource` e Configurações Multi-Provedor)
* **Severidade:** Major
* **Fontes:** `egm-implementation-readiness` (#5), `egm-codebase-details` (#5), `egm-style` (#3)
* **Escopo Afetado:** Item 6 ([L238–L240](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L238-L240)) vs. [`src/tomus/core/config.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/config.py#L72-L227)
* **Descrição e Orientação Técnica:**
  O Item 6 menciona apenas 3 chaves de API e `TomlConfigSettingsSource`. Na `v0.4.0`, `config.py` implementa:
  1. `FilteredTomlSettingsSource` (`LocalTomlSettingsSource` e `GlobalTomlSettingsSource`), que filtra strings vazias (`""`) via `_remove_empty_strings` para que valores em branco no template TOML não anulem variáveis de ambiente ou padrões.
  2. `LLMConfig` com `provider` (`AliasChoices("provider", "default_provider")`), `fallback_chain = ["groq", "nvidia", "deepseek"]`, `model = "gemini-3.5-flash"` e `providers: dict[str, dict[str, Any]]`.
  3. `ApiKeysConfig` com 8 chaves e seus respectivos `AliasChoices` (`gemini_api_key`, `google_books_api_key`, `openalex_polite_email`, `nvidia_api_key`, `deepseek_api_key`, `claude_api_key`, `groq_api_key` e `github_token`).
* **Ação Recomendada:** Atualizar o Item 6 com `FilteredTomlSettingsSource`, os campos de `LLMConfig` e todas as 8 chaves de `ApiKeysConfig`.

---

### 6. [IMPL-06] Especificação Desatualizada de `src/tomus/cli/main.py` (Callback Raiz `-o/-d`, `resume`, `cache` e Diagnóstico de Atalhos)
* **Severidade:** Major
* **Fontes:** `egm-implementation-readiness` (#6), `egm-codebase-details` (#7), `egm-style` (#3)
* **Escopo Afetado:** Item 24 ([L310–L312](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L310-L312)) vs. [`src/tomus/cli/main.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py#L1-L723)
* **Descrição e Orientação Técnica:**
  O Item 24 documenta apenas `organize` e `config (init|show|path)`. Na `v0.4.0`, `cli/main.py` inclui:
  1. Callback raiz `_root_callback` para invocação direta `tomus -o <origem> -d <destino> [OPTIONS]` e subcomando `organize` com `hidden=True`.
  2. Comando `tomus resume` (retomada via `.tomus_session.json`) e subgrupo `tomus cache {clean, clear, status, path}`.
  3. Flags `--origem/-o/--source`, `--destino/-d/--target`, `--provider/-p` e `--verbose/-v`.
  4. Painel duplo `rich.live.Live` + `rich.console.Group(prog_bar, status_prog)` e aviso pós-execução para atalhos `.webloc` e arquivos não-PDF ignorados em `_print_summary`.
* **Ação Recomendada:** Atualizar o Item 24 contemplando todos os comandos, opções e componentes visuais da CLI `v0.4.0`.

---

### 7. [IMPL-07] Schema JSON Explícito em `prompts.py` e Proteção Anti-Mock em `cache.py`
* **Severidade:** Major
* **Fontes:** `egm-implementation-readiness` (#7), `egm-codebase-details` (#8, #9), `egm-style` (#3)
* **Escopo Afetado:** Item 11 ([L258–L260](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L258-L260)) e Item 17 ([L282–L284](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L282-L284)) vs. [`cache.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/cache.py#L49-L144) e [`prompts.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/prompts.py#L48-L162)
* **Descrição e Orientação Técnica:**
  1. **Item 11 (`src/tomus/core/cache.py`):** Além do modo WAL e da chave `(sha256, taxonomy_version, model_name)`, `FileCache(enabled=True, db_path=None)` usa `check_same_thread=False`, expõe `clear()` e bloqueia a leitura/gravação de entradas com `reasoning == "mock"` (`_is_mock`) quando opera no banco real (`db_path is None`), evitando poluição do cache do usuário por testes automatizados.
  2. **Item 17 (`src/tomus/core/prompts.py`):** `build_system_prompt()` incorpora o bloco formal `Formato JSON obrigatório` com os 9 campos do schema (`[SCH-01]`), e o módulo também exporta `is_generic_title(title: str) -> bool` e `format_authors_for_filename(authors: list[str]) -> str`.
* **Ação Recomendada:** Atualizar os Itens 11 e 17 com esses contratos.

---

## 🟢 Ajustes Menores e Editoriais (Nits)

### 8. [IMPL-08] Assinaturas de `taxonomy.py` e Exportações de `storage/__init__.py`
* **Severidade:** Nit
* **Fontes:** `egm-codebase-details` (#10, #11), `egm-implementation-readiness` (#3)
* **Escopo Afetado:** Item 9 ([L250–L252](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L250-L252)) e Item 19 ([L290–L292](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L290-L292))
* **Descrição e Orientação Técnica:**
  1. No Item 9 (`src/tomus/core/taxonomy.py`), explicitar a assinatura `get_areas_basicas(grande_area: str) -> list[str]` (com argumento obrigatório) e o nome exato da função `format_taxonomy_for_prompt() -> str`.
  2. No Item 19 (`src/tomus/storage/__init__.py`), incluir `generate_companion_markdown` ao lado de `format_academic_filename` e `LibraryOrganizer`.

---

### 9. [IMPL-09] Cobertura das Novas Suítes de Teste (`test_multi_provider.py`, `test_cli_ergonomia.py`) e `pyproject.toml`
* **Severidade:** Nit
* **Fontes:** `egm-implementation-readiness` (#8), `egm-style` (#4)
* **Escopo Afetado:** Item 1 ([L218–L220](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L218-L220)) e Itens 25–27 ([L314–L324](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L314-L324))
* **Descrição e Orientação Técnica:**
  1. No Item 1 (`pyproject.toml`), mencionar a seção `[tool.pytest.ini_options]` com o marcador `slow` e a lista `filterwarnings`.
  2. Após o Item 27, listar as suítes de teste adicionadas até a `v0.4.0` (`tests/test_multi_provider.py`, `tests/test_cli_ergonomia.py`, etc.) e o arquivo `CHANGELOG.md`.

---

### 10. [IMPL-10] Precisão Terminológica e Eliminação de Metáforas nos Itens 5, 8, 11, 22 e 24
* **Severidade:** Nit
* **Fontes:** `egm-style` (#5)
* **Escopo Afetado:** Linhas 236, 248, 260, 304 e 312 de [tomus.md](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L236-L312)
* **Descrição e Orientação Técnica:**
  Substituir expressões figuradas ou promocionais por termos técnicos diretos:
  * L236: substituir *"fronteira limpa"* por *"Isola o pacote `core` de dependências da camada de apresentação (`typer`, `rich`)"*;
  * L260: substituir *"sem cristalizar no cache"* por *"sem persistir no cache"*;
  * L304: substituir *"todo o fluxo de ponta a ponta"* por *"a execução sequencial e concorrente dos 5 estágios"*;
  * L312: substituir *"Entrega a interface operacional do MVP permitindo uso imediato no terminal"* por *"Expõe os comandos da CLI, o controle de sessão e a exibição de progresso no terminal"*.
