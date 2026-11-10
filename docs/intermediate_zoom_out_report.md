# Relatório de Revisão Intermediária Zoom Out (Stage 8 — Intermediate Zoom Out Review)

* **Arquivo Auditado:** [tomus.md](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L1-L324) (linhas 1–324, `FeatureRange` `1..213` + `DetailedRange` `214..324`)
* **Relatórios Anteriores Inspecionados:** [zoom_out_report.md](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/zoom_out_report.md), [critic_report.md](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/critic_report.md)
* **Base de Código de Referência:** `v0.4.0` ([CHANGELOG.md](file:///Users/dario/Projetos-de-aplicativos/tomus/CHANGELOG.md), [pyproject.toml](file:///Users/dario/Projetos-de-aplicativos/tomus/pyproject.toml))
* **Persona Revisora:** Skeptical Architect (`egm-zoom-out`)

---

## Avaliação Geral de Alto Nível (Coesão `1..213` vs. `214..324` e Prontidão para a GUI `v1.0.0`)

A divisão arquitetural do sistema em três pacotes de domínio independentes de interface (`tomus.core`, `tomus.extractors`, `tomus.storage`) e um pacote de apresentação (`tomus.cli`) é sólida e enxuta. Contudo, a auditoria integrada do documento completo (`1..324`) contra o código `v0.4.0` identifica **6 achados** (**2 Blockers**, **3 Majors** e **1 Nit**) centrados em três eixos antes do início da Desktop GUI (`v1.0.0`):

1. **Ruptura de Coesão entre `FeatureRange` (`1..213`), `DetailedRange` (`214..324`) e o Código `v0.4.0`:** Ambos os intervalos do documento ainda descrevem o estado `v0.0.1`/`v0.1.0` (todos os 27 itens do `DetailedRange` estão rotulados como `(Criar)` e omitem os módulos `companion.py`, `logging.py` e `session.py`, bem como o hub de 6 provedores de LLM e os novos comandos da CLI).
2. **Vazamento de Orquestração para a Camada CLI ([`cli/main.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py#L88-L264)):** A montagem da cadeia de provedores (`create_provider_chain`), o carregamento/override de `config.toml` e o ciclo de vida de sessão (`save_session`/`clear_session`) estão acoplados a funções privadas da CLI (`_executar_organize`), enquanto [`run_pipeline`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/pipeline.py#L353-L360) ainda instancia apenas `GeminiProvider` ou `MockLLMProvider`.
3. **Duplicação Massiva em [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py) (1.309 linhas):** Os 6 provedores repetem a mesma lógica de negócio pré/pós-chamada e 4 provedores repetem o mesmo cliente REST OpenAI-compatível.

---

## 🔴 Achados Bloqueantes (Blockers)

### 1. [ZOUT-01] Desalinhamento Integral entre `FeatureRange` (`1..213`), `DetailedRange` (`214..324`) e a Arquitetura Real `v0.4.0`
* **Severidade:** Blocker
* **Escopo Afetado:**
  * `FeatureRange`: `## Overview` ([L29–L31](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L29-L31)), `## Goals` ([L41](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L41)), `## Non-Goals` ([L46](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L46)), `### 1. System Architecture` ([L57–L71](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L57-L71)), `#### Stage 4` ([L95](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L95)), `#### Stage 5` ([L114–L118](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L114-L118)), `### 3. Domain Entities` ([L120–L130](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L120-L130)), `### 4. User Configuration File` ([L131–L168](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L131-L168)) e `### 5. CLI Contract` ([L170–L190](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L170-L190)).
  * `DetailedRange`: `## Detailed Implementation` ([L214–L324](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L214-L324) — especialmente Itens 4, 6, 7, 17, 18, 19, 21, 22, 24 e ausência de itens para `logging.py`, `session.py` e `companion.py`).
* **Racional de Simplicidade e Coesão:**
  Para que o documento sirva como fonte única de verdade antes da GUI `v1.0.0`, o `FeatureRange` (`1..213`) e o `DetailedRange` (`214..324`) precisam estar 100% coesos entre si e com o código `v0.4.0`:
  1. **Módulos da `v0.4.0` ausentes no `DetailedRange` (`214..324`):** O inventário de arquivos termina no Item 27 e omite três módulos de produção já existentes no repositório:
     * [src/tomus/storage/companion.py](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/companion.py) (geração de arquivos `.md` companheiros com *front matter* YAML, data humanizada e referência ABNT NBR 6023 para obras canônicas e duplicatas);
     * [src/tomus/core/logging.py](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/logging.py) (`setup_logging`, redirecionamento para arquivo de log e silenciamento de loggers ruidosos como `RapidOCR`, `docling`, `torch`);
     * [src/tomus/core/session.py](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/session.py) (`SessionState`, `save_session`, `load_session`, `clear_session`).
  2. **Itens desatualizados no `DetailedRange`:**
     * **Item 4 ([L230–L232](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L230-L232)):** Menciona `__version__ = "0.1.0"`, enquanto [pyproject.toml](file:///Users/dario/Projetos-de-aplicativos/tomus/pyproject.toml#L7) está em `0.4.0`.
     * **Item 6 ([L238–L240](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L238-L240)):** Descreve apenas 3 variáveis de ambiente em [`config.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/config.py), omitindo `fallback_chain`, `default_provider`, `providers`, as chaves/aliases dos 5 provedores adicionais (`nvidia`, `deepseek`, `claude`, `groq`, `github`) e a classe `FilteredTomlSettingsSource`.
     * **Item 17 ([L282–L284](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L282-L284)):** Omite o schema JSON explícito unificado (`[SCH-01]`) incluído em [`prompts.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/prompts.py#L48-L87) para nivelar provedores OpenAI-compatíveis ao Gemini.
     * **Item 18 ([L286–L288](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L286-L288)):** Descreve apenas `GeminiProvider`, omitindo `NvidiaProvider`, `DeepSeekProvider`, `ClaudeProvider`, `GroqProvider`, `GitHubModelsProvider`, [`FallbackLLMDispatcher`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1059-L1172) e [`create_provider_chain`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1175-L1309).
     * **Item 21 ([L298–L300](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L298-L300)):** Afirma que duplicatas são apenas ignoradas (`duplicate_skipped`), omitindo a materialização física em `<TARGET_DIR>/duplicatas/`, a geração dos `.md` companheiros e o diagnóstico tipado de não-PDFs (`[DIAG-06]`) em [`organizer.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/organizer.py#L213-L363).
     * **Item 24 ([L310–L312](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L310-L312)):** Omite a invocação raiz (`tomus -o <origem> -d <destino>`), o comando `tomus resume`, o subgrupo `tomus cache {clean,clear,status,path}` e as flags `--provider/-p` e `--verbose/-v` em [`cli/main.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py).

---

### 2. [ZOUT-02] Lógica de Orquestração e Fábrica de Provedores Presa na CLI em vez de Reutilizável no `core` (Bloqueio de Reuso para a GUI `v1.0.0`)
* **Severidade:** Blocker
* **Escopo Afetado:** `### 1. System Architecture & Data Flow` ([L55](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L55)), `## Detailed Implementation` — Item 22 ([L302–L304](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L302-L304)) e Item 24 ([L310–L312](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L310-L312)) vs. [`src/tomus/core/pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/pipeline.py#L353-L360) e [`src/tomus/cli/main.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py#L88-L264).
* **Racional de Simplicidade e Reuso:**
  O objetivo arquitetural declarado na linha 55 é que `tomus.core` execute todo o pipeline sem acoplamento com terminal, permitindo que a futura GUI consuma a mesma API pública. Porém, na implementação atual:
  1. Em [`run_pipeline`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/pipeline.py#L354-L359), quando `provider is None`, o orquestrador **não** chama [`create_provider_chain(config)`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1175): ele instancia diretamente `GeminiProvider(api_key=config.api_keys.gemini_api_key)` ou cai silenciosamente em `MockLLMProvider()`.
  2. O carregamento de `config.toml` customizado ([`_load_config`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py#L88-L106)), a aplicação de overrides ([`_aplicar_overrides`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py#L136-L174)), a construção da cadeia de provedores ([`_build_provider`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py#L121-L133)) e a persistência de sessão (`save_session`/`clear_session`) estão implementados dentro de [`src/tomus/cli/main.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py#L177-L319).
  3. Se a Desktop GUI (`v1.0.0`) chamar `run_pipeline` diretamente, terá de reimplementar toda essa colagem que hoje mora em `cli/main.py`.
* **Recomendação:** Mover `_load_config` / `_aplicar_overrides` para [`core/config.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/config.py) e fazer [`run_pipeline`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/pipeline.py) usar `create_provider_chain(config)` por padrão (além de aceitar `cancel_event: threading.Event | None = None` para cancelamento cooperativo na GUI).

---

## 🟡 Achados Principais (Majors)

### 3. [ZOUT-03] Violação Severa de DRY e Complexidade Acidental em [`src/tomus/core/llm.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py) (1.309 Linhas)
* **Severidade:** Major
* **Escopo Afetado:** `#### Stage 4: Classificação via LLM` ([L93–L108](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L93-L108)) e `## Detailed Implementation` — Item 18 ([L286–L288](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L286-L288)) vs. [`src/tomus/core/llm.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1-L1309).
* **Racional de Simplicidade:**
  [`src/tomus/core/llm.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py) cresceu para **1.309 linhas** porque:
  1. **Quatro classes quase idênticas (`NvidiaProvider`, `DeepSeekProvider`, `GroqProvider`, `GitHubModelsProvider`):** Todas fazem exatamente a mesma requisição `POST /chat/completions` via `httpx`, mudando apenas `base_url`, `default_model`, cabeçalhos extras e o fallback de `reasoning_content` (usado por modelos de raciocínio como NVIDIA Nemotron/DeepSeek). Uma única classe base ou adaptador parametrizado `OpenAICompatibleProvider` substituiria mais de 600 linhas duplicadas.
  2. **Seis cópias do pipeline de validação (`classify`):** A pré-validação de *short-circuit* (`_alphanumeric_count < 50` sem metadados externos), a montagem de `build_system_prompt()`/`build_context_payload()`, o reparo de taxonomia (`validate_or_repair_pair`) e a trava pós-LLM de título genérico (`min(confidence, 0.50)`) estão copiados e colados dentro do método `classify()` de cada um dos 6 provedores.
  3. **Duplicação de constantes entre módulos:** `_GENERIC_PREFIXES` e `_GENERIC_TITLES` estão definidos em [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L42-L55) **e** também em [`prompts.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/prompts.py#L20-L27) (`GENERIC_TITLES`, `GENERIC_TITLE_PREFIXES`), sendo que `llm.py` já importa `is_generic_title` de `prompts.py`, tornando as constantes em `llm.py` código morto.
* **Recomendação:** Documentar no Stage 4 e no Item 18 que as travas determinísticas pré e pós-LLM são executadas de forma centralizada e que provedores REST OpenAI-compatíveis compartilham a mesma infraestrutura HTTP.

---

### 4. [ZOUT-04] Duplicação na Resolução de Chaves de API entre `AppConfig` (`pydantic-settings`) e `create_provider_chain`
* **Severidade:** Major
* **Escopo Afetado:** `### 4. User Configuration File (config.toml) & Precedence Rules` ([L135–L140](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L135-L140)) e `## Detailed Implementation` — Item 6 ([L238–L240](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L238-L240)) e Item 18 ([L286–L288](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L286-L288)) vs. [`config.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/config.py#L96-L155) e [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1197-L1250).
* **Racional de Simplicidade:**
  [`ApiKeysConfig`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/config.py#L96-L155) já declara `AliasChoices` no Pydantic para resolver variáveis de ambiente com precedência sobre o `config.toml` (graças a `FilteredTomlSettingsSource`). Ainda assim, [`create_provider_chain`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L1197-L1250) (e [`_resolve_api_key`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/cli/main.py#L109-L119) em `cli/main.py`) reimplementa manualmente a leitura de `os.environ.get(...)` com tuplas `chave_env` duplicadas. Além disso, `create_provider_chain` ignora o dicionário `config.llm.providers` definido em [`LLMConfig.providers`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/config.py#L90-L93) (que permite configurar `providers.<nome>.model` no `config.toml`, conforme linhas 266–276 de `config.py`).
* **Recomendação:** Centralizar a resolução de chaves e modelos por provedor em métodos de [`AppConfig`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/config.py) (respeitando `llm.providers.<nome>.model`) e remover a leitura redundante de `os.environ` em `llm.py` e `cli/main.py`.

---

### 5. [ZOUT-05] Inconsistências de Segurança de Dados e Fronteira Desktop (`revisao_manual/`, `--dry-run`, `Path.cwd()` e Chave de Cache)
* **Severidade:** Major
* **Escopo Afetado:** `#### Stage 1` ([L78](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L78)), `#### Stage 5` ([L114–L118](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L114-L118)) e `## Detailed Implementation` — Itens 11, 21 e 22 ([L258–L260, L298–L304](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L258-L260)).
* **Racional de Simplicidade:**
  Confirmando na perspectiva de arquitetura global os pontos levantados no `critic_report.md` (`CRIT-03`, `CRIT-04`, `CRIT-06`), estas falhas afetam diretamente tanto o `FeatureRange` quanto o `DetailedRange`:
  1. **Reuso de `_resolve_collision` em `revisao_manual/` ([`organizer.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/organizer.py#L281-L325)):** `_resolve_collision` já existe no mesmo arquivo e já recebe `planned_destinations`, mas não é reutilizado em `add_manual_review` nem em `add_error`, permitindo sobrescrita de arquivos homônimos vindos de subpastas distintas. Além disso, `_resolve_collision` recalcula `_compute_sha256(src_path)` do disco em vez de reutilizar o `sha256` já calculado pelo Scanner no Stage 1.
  2. **Caminhos relativos ao CWD em [`session.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/session.py#L17), [`logging.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/logging.py#L30) e [`companion.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/companion.py#L213):** Gravar `.tomus_session.json` e `tomus.log` em `Path.cwd()` falha em aplicativos desktop empacotados (`.app`/`.exe`), onde o diretório de trabalho padrão é somente-leitura. Ambos devem residir em `~/.cache/tomus/` (reutilizando `CACHE_DIR` já definido em [`cache.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/cache.py#L21)). Já em [`generate_duplicate_companion_markdown`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/storage/companion.py#L213), o caminho relativo deve ser calculado em relação a `target_dir` (raiz da biblioteca) e não a `Path.cwd()`.
  3. **Rastreabilidade do modelo efetivo no Cache e no Manifesto ([`llm.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L106-L120), [`pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/pipeline.py#L138-L249)):** Incluir `provider_name` e `model_name` efetivos no resultado da classificação evita indexar o cache com o modelo primário quando um provedor de fallback respondeu.

---

## 🟢 Ajustes Menores e Editoriais (Nits)

### 6. [ZOUT-06] Queda de Altitude (Weeds) no `DetailedRange` (`214..324`) e Rótulos `(Criar)` Obsoletos
* **Severidade:** Nit
* **Escopo Afetado:** `## Detailed Implementation` ([L214–L324](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L214-L324) — todos os 27 itens).
* **Racional de Simplicidade:**
  1. **Status dos arquivos:** Todos os itens de `## Detailed Implementation` estão marcados como `(Criar)` e o texto introdutório ([L216](file:///Users/dario/Projetos-de-aplicativos/tomus/docs/designs/tomus.md#L216)) diz *"todos os arquivos que serão criados"*, embora o sistema já esteja implementado na `v0.4.0`. O cabeçalho e os itens devem refletir a arquitetura implementada (`v0.4.0`) e os ajustes planejados.
  2. **Excesso de detalhes de implementação (Weeds):** Itens como o 11 (DDL SQL literal completo na linha 259), 13 (expressão regular literal na linha 267), 18 (lista literal de strings genéricas na linha 287) e 20 (`a.split(",")[0].strip()` na linha 295) descem ao nível de código-fonte linha a linha em vez de descrever responsabilidades, interfaces públicas e invariantes de cada módulo.
  3. **Unificação de `ClassificationResult` e `LLMClassificationOutput`:** Avaliar no Item 7 e Item 18 a simplificação entre [`LLMClassificationOutput`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/models.py#L70-L81) e [`ClassificationResult`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/llm.py#L106-L120) (ou documentar explicitamente `ClassificationResult` e `SessionState` na tabela da Seção 3, conforme `CRIT-08`), eliminando conversões manuais em [`_classification_to_dict`](file:///Users/dario/Projetos-de-aplicativos/tomus/src/tomus/core/pipeline.py#L72-L83).
