# Relatório de Revisão Crítica (Stage 7 — Critic Review)

* **Arquivo Auditado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L1-L213)
* **Escopo (`FeatureRange`):** Linhas 1–213
* **Padrão de Referência:** `feature-spec-standard` (auditado contra o codebase `v0.4.0`)
* **Personas Revisoras:** Design Critic (`egm-design`), Structural Architect (`egm-structural`) e Technical Copy Editor (`egm-style`)

---

## Resumo Executivo

A revisão crítica das linhas `1–213` de [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L1-L213) consolidou **10 achados deduplicados** (**2 Blockers**, **6 Majors** e **2 Nits**):

1. **Descompasso entre Especificação (`v0.1.0`) e Implementação Real (`v0.4.0`):** O documento ainda declara múltiplos provedores de LLM como *Non-Goal* e omite o hub de 6 provedores (`FallbackLLMDispatcher`), os arquivos companheiros `.md` com citação ABNT, a pasta `duplicatas/`, o diagnóstico tipado de arquivos não-PDF (`.webloc`, `.url`, `.epub`) e os novos contratos de `config.toml` e da CLI (`bibliotec resume`, `bibliotec cache`, invocação raiz `-o/-d`).
2. **Vulnerabilidades Arquiteturais e Prontidão para GUI (`v1.0.0`):** A auditoria cruzada com o código identificou falhas que devem ser endereçadas e especificadas antes da construção da GUI: ausência de resolução de colisão em `revisao_manual/` (risco de perda de arquivo com `--move`), mutação de disco em `--dry-run`, chaveamento de cache SQLite com `model_name` estático sob fallback, perda do cabeçalho do Polite Pool do OpenAlex na busca por título, ausência de `cancel_event` cooperativo em `run_pipeline` e acoplamento a `Path.cwd()` em `session.py` e `logging.py`.

---

## 🔴 Achados Bloqueantes (Blockers)

### 1. [CRIT-01] Descompasso Arquitetural entre Especificação (MVP Monoprovedor) e Base de Código v0.4.0 (Hub Multi-Provedor e Artefatos do Stage 5)
* **Severidade:** Blocker
* **Fontes:** `egm-design` (#1), `egm-structural` (#5), `egm-style` (#1)
* **Escopo Afetado:** `## Overview` ([L29–L31](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L29-L31)), `## Goals` ([L41](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L41)), `## Non-Goals` ([L46](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L46)), `#### Stage 4` ([L95](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L95)) e `#### Stage 5` ([L114–L118](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L114-L118)) vs. [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L1059-L1309), [`prompts.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/prompts.py#L48-L87), [`companion.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/companion.py#L125-L255), [`organizer.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L213-L269)
* **Descrição e Racional:**
  O documento descreve uma arquitetura restrita ao provedor Gemini (`gemini-2.5-flash`) e declara em **Non-Goals** ([L46](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L46)) que *"Provedores adicionais de LLM não serão empacotados no MVP"*. Na versão `v0.4.0`, a arquitetura real inclui:
  1. **Hub de 6 Provedores e `FallbackLLMDispatcher`:** Suporte nativo a `gemini` (`gemini-3.5-flash` / fallback interno 404), `groq` (`openai/gpt-oss-20b`), `nvidia` (`nvidia/nemotron-3.5-lightning-30b-a3b` com extração de `reasoning_content`), `deepseek` (`deepseek-flash`), `claude` (`claude-sonnet-4-5`) e `github` (`gpt-5`), com cadeia de fallback configurável (`fallback_chain = ["groq", "nvidia", "deepseek"]`) e schema JSON explícito unificado no prompt de sistema (`[SCH-01]`).
  2. **Materialização de Duplicatas e Arquivos Companheiros (`.md`):** A linha 117 afirma que *"duplicatas exatas são ignoradas (`duplicate_skipped`)"*, mas [`LibraryOrganizer.add_organized`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L213-L269) encaminha duplicatas para `<TARGET_DIR>/duplicatas/` com resolução de colisão e gera arquivos companheiros `<nome_formatado>.md` contendo citação ABNT NBR 6023 tanto para PDFs organizados quanto para duplicatas.
  3. **Diagnóstico Tipado de Não-PDFs (`[DIAG-06]`):** Arquivos não-PDF (`.webloc`, `.url`, `.epub`, `.mobi`, etc.) recebem diagnóstico específico e são documentados na seção `## Arquivos Não-PDF e Atalhos Ignorados` dentro de `revisao_manual/relatorio_revisao.md`.
* **Recomendação:** Calibrar `## Overview`, `## Goals`, `## Non-Goals` (esclarecendo que o Non-Goal é não depender de SDKs proprietários pesados de terceiros, utilizando adaptadores REST via `httpx`), `#### Stage 4` e `#### Stage 5` para refletir a arquitetura `v0.4.0`.

---

### 2. [CRIT-02] Contratos de Configuração (`config.toml`) e da CLI (`bibliotec`) Defasados em Relação à v0.4.0
* **Severidade:** Blocker
* **Fontes:** `egm-structural` (#1, #2), `egm-style` (#2, #4), `egm-design` (#1)
* **Escopo Afetado:** `### 4. User Configuration File (config.toml) & Precedence Rules` ([L131–L168](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L131-L168)) e `### 5. CLI Contract (bibliotec)` ([L170–L190](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L170-L190)) vs. [`config.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/config.py#L72-L295) e [`main.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/cli/main.py#L367-L716)
* **Descrição e Racional:**
  Os blocos estruturais das Seções 4 e 5 divergem diretamente dos contratos implementados:
  1. **Precedência de Variáveis de Ambiente ([L137](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L137)):** Omite as cadeias `AliasChoices` dos 5 provedores adicionais (`BIBLIOTEC_NVIDIA_API_KEY` > `NVIDIA_API_KEY`, `BIBLIOTEC_DEEPSEEK_API_KEY` > `DEEPSEEK_API_KEY`, `BIBLIOTEC_CLAUDE_API_KEY` > `CLAUDE_API_KEY` > `ANTHROPIC_API_KEY`, `BIBLIOTEC_GROQ_API_KEY` > `GROQ_API_KEY`, `BIBLIOTEC_GITHUB_TOKEN` > `GITHUB_TOKEN` > `GH_TOKEN`).
  2. **Schema `config.toml` ([L146–L168](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L146-L168)):** A seção `[llm]` exibe `model = "gemini-2.5-flash"` e omite `default_provider = "gemini"`, `fallback_chain = ["groq", "nvidia", "deepseek"]` e as subseções `[llm.providers.<nome>]`. A seção `[api_keys]` omite `nvidia_api_key`, `deepseek_api_key`, `claude_api_key`, `groq_api_key` e `github_token`.
  3. **Topologia de Comandos da CLI ([L172–L190](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L172-L190)):** Omite a invocação direta na raiz (`bibliotec -o <SOURCE_DIR> -d <TARGET_DIR> [OPTIONS]`, sendo `organize` mantido como alias oculto `hidden=True`), o comando `bibliotec resume [--verbose / -v]`, o subgrupo `bibliotec cache {clean, clear, status, path}` e as flags `--origem / -o / --source`, `--destino / -d / --target`, `--provider / -p` e `--verbose / -v`.
* **Recomendação:** Atualizar integralmente os blocos das Seções 4 e 5 em [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L131-L190) em sincronia com [`config.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/config.py) e [`main.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/cli/main.py).

---

## 🟡 Achados Principais (Majors)

### 3. [CRIT-03] Sobrescrita Silenciosa em `revisao_manual/` e Mutação de Disco no Modo `--dry-run`
* **Severidade:** Major
* **Fontes:** `egm-design` (#2)
* **Escopo Afetado:** `#### Stage 5` ([L115–L118](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L115-L118)) e [`organizer.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L281-L325), [`organizer.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L384-L414)
* **Descrição e Racional:**
  1. **Colisão não tratada em `revisao_manual/`:** A especificação ([L117](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L117)) exige que tanto a árvore temática quanto `revisao_manual/` resolvam colisões de nome comparando SHA-256 e aplicando sufixo ` (2).pdf`. Contudo, [`LibraryOrganizer.add_manual_review`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L290) e [`LibraryOrganizer.add_error`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L313) gravam diretamente em `target_dir / REVISAO_DIR / source_path.name` **sem chamar `_resolve_collision`**. Em varreduras recursivas, dois PDFs distintos com nomes iguais em subpastas diferentes (ex.: `sub1/artigo.pdf` e `sub2/artigo.pdf`) encaminhados para `revisao_manual/` sobrescrevem-se silenciosamente (causando perda definitiva do primeiro arquivo quando `--move` está ativo).
  2. **Mutação de disco em `--dry-run`:** [`write_manifest`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L403) e [`write_relatorio_revisao`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L413) criam `target_dir` e `target_dir/revisao_manual/` em disco mesmo quando `dry_run=True`.
* **Recomendação:** Exigir e implementar `_resolve_collision` em `add_manual_review` e `add_error`, e especificar de forma explícita o comportamento de escrita de `manifest.json` e `relatorio_revisao.md` durante `--dry-run`.

---

### 4. [CRIT-04] Inconsistência da Chave de Cache SQLite (`model_name` Estático) sob Fallback Multi-Provedor
* **Severidade:** Major
* **Fontes:** `egm-design` (#3)
* **Escopo Afetado:** `#### Stage 1` ([L78](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L78)), [`pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/pipeline.py#L138-L249), [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L107-L120)
* **Descrição e Racional:**
  O cache SQLite indexa `processed_files` pela chave primária `(sha256, taxonomy_version, model_name)`. Em [`run_pipeline`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/pipeline.py#L310), `model_name` é lido estaticamente de `config.llm.model` antes da execução. Quando o `FallbackLLMDispatcher` chaveia para outro provedor em tempo de execução (ou quando o usuário passa `--provider groq` sem alterar `config.llm.model`), o resultado é persistido sob o `model_name` estático em vez do provedor/modelo que efetivamente realizou a classificação, e `ClassificationResult` não registra o provedor/modelo vencedor.
* **Recomendação:** Incluir `provider_name` e `model_name` efetivos em `ClassificationResult` e documentar no Stage 1 como o cache resolve hits e persiste classificações quando a cadeia de fallback entra em ação.

---

### 5. [CRIT-05] Falhas no Polite Pool do OpenAlex, Cobertura de Retry HTTP e Mutação Concorrente em `GeminiProvider`
* **Severidade:** Major
* **Fontes:** `egm-design` (#4)
* **Escopo Afetado:** `#### Stage 3` ([L84–L92](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L84-L92)), `#### Stage 4` ([L94–L107](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L94-L107)), [`enrichers.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/enrichers.py#L47-L95) e [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L76-L207)
* **Descrição e Racional:**
  1. **Polite Pool do OpenAlex ignorado na busca por título e busca por DOI sem `@retry`:** Em [`_query_openalex_by_title`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/enrichers.py#L86), o dicionário `headers` com `openalex_polite_email` é construído localmente mas **nunca é passado** para `_get_json(client, url, params)`. Já [`_query_openalex_by_doi`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/enrichers.py#L71-L80) chama `client.get` diretamente, contornando `_get_json` e o decorador `@retry`.
  2. **Filtros de exceção nos retries:** Em [`enrichers.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/enrichers.py#L47-L51), `@retry` repete inclusive erros cliente permanentes (HTTP 400/404). Em [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L86-L90), `_is_generic_openai_retryable` captura apenas `httpx.HTTPStatusError` (429/503), ignorando `httpx.TimeoutException`, `httpx.TransportError` e o status `529` (Anthropic Overloaded).
  3. **Conflito entre loop interno e `@retry` no `GeminiProvider`:** Em [`GeminiProvider._call_gemini`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L169-L207), erros 429/503 acionam `continue` para o próximo modelo da lista `_fallback_models` antes que o `tenacity` possa aplicar backoff no modelo atual, além de mutar `self._model` ([L193](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L193)) sem lock entre threads quando `workers > 1`.
* **Recomendação:** Documentar a política exata de retry e fallback nos Stages 3 e 4 e alinhar as implementações de `enrichers.py` e `llm.py`.

---

### 6. [CRIT-06] Prontidão da Fronteira `bibliotec.core` para a Futura GUI (`v1.0.0`)
* **Severidade:** Major
* **Fontes:** `egm-design` (#5)
* **Escopo Afetado:** `## Goals` ([L41](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L41)), `### 1. System Architecture` ([L55](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L55)), `### 3. Domain Entities` ([L129](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L129)) vs. [`pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/pipeline.py#L280-L419), [`session.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/session.py#L17), [`logging.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/logging.py#L30-L57)
* **Descrição e Racional:**
  Embora o design estabeleça como meta que `bibliotec.core` seja consumível diretamente por uma futura GUI sem acoplamento ao terminal, três pontos na fronteira atual impedem o uso seguro em um aplicativo desktop empacotado (`.app` / `.exe`):
  1. **Ausência de cancelamento cooperativo:** `run_pipeline` não recebe `cancel_event: threading.Event | None = None`, impedindo que o usuário interrompa ou pause uma execução em lote pela GUI sem encerrar o processo.
  2. **Escrita relativa em `Path.cwd()` e limpeza do `root_logger`:** `session.py` grava `.bibliotec_session.json` no diretório de trabalho atual (`Path(".bibliotec_session.json")`) e `logging.py` grava `bibliotec.log` no CWD além de remover todos os handlers do `root_logger` global. Em bundles macOS `.app`, o CWD padrão é somente-leitura, causando `PermissionError`.
* **Recomendação:** Especificar na Seção 1 e Seção 3 o suporte a `cancel_event` em `run_pipeline` e o armazenamento padrão de sessão e logs em diretórios de dados do usuário (`~/.cache/bibliotec/` ou `~/.local/share/bibliotec/`).

---

### 7. [CRIT-07] Diagrama Mermaid Desatualizado quanto ao Fluxo Multi-Provedor e Saídas do Stage 5
* **Severidade:** Major
* **Fontes:** `egm-structural` (#3), `egm-style` (#3)
* **Escopo Afetado:** `### 1. System Architecture & Data Flow` ([L57–L71](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L57-L71))
* **Descrição e Racional:**
  O fluxograma `flowchart TD` nas linhas 57–71 omite três elementos centrais da arquitetura `v0.4.0`:
  1. O nó `F` mencione apenas `"Stage 4: Classificador LLM (Protocolo LLMProvider / Gemini)"`, omitindo o `FallbackLLMDispatcher` e a cadeia multi-provedor.
  2. As saídas do nó `G["Stage 5: Materializacao e Namer"]` mostram apenas a árvore temática (`H`) e `revisao_manual/` (`I`), omitindo a geração dos arquivos companheiros `.md` ABNT e a pasta `duplicatas/`.
  3. O nó `X["Ignorado (Log no Manifesto)"]` omite que arquivos não-PDF e atalhos (`.webloc`, `.url`) também são reportados com diagnóstico em `revisao_manual/relatorio_revisao.md`.
* **Recomendação:** Atualizar os nós `F`, `G`, `H`, `I` e `X` (e adicionar o nó de `duplicatas/`) no diagrama Mermaid da Seção 1.

---

### 8. [CRIT-08] Tabela de Entidades de Domínio Incompleta (`### 3. Domain Entities & Data Contracts`)
* **Severidade:** Major
* **Fontes:** `egm-structural` (#4), `egm-design` (#5)
* **Escopo Afetado:** `### 3. Domain Entities & Data Contracts` ([L120–L130](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L120-L130)) vs. [`models.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/models.py#L110-L119), [`llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L106-L120), [`session.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/session.py#L20-L34)
* **Descrição e Racional:**
  1. A linha de `PipelineEvent` ([L129](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L129)) lista apenas `stage`, `source_path`, `status`, `message`, omitindo os campos `total_files`, `completed_files` e `timestamp` definidos em [`models.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/models.py#L110-L119).
  2. A tabela não documenta os contratos `ClassificationResult` (`src/bibliotec/core/llm.py`) e `SessionState` (`src/bibliotec/core/session.py`).
* **Recomendação:** Completar os campos de `PipelineEvent` e incluir `ClassificationResult` e `SessionState` na tabela da Seção 3.

---

## 🟢 Ajustes Menores e Editoriais (Nits)

### 9. [CRIT-09] Heurística de Busca por Título/Autor em `enrichers.py` e Re-hashing em `_resolve_collision`
* **Severidade:** Nit
* **Fontes:** `egm-design` (#6)
* **Escopo Afetado:** `#### Stage 3` ([L90](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L90)), [`enrichers.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/enrichers.py#L214-L243), [`organizer.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L79-L90)
* **Descrição e Racional:**
  1. Em [`enrichers.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/enrichers.py#L234-L238), quando não há ISBN, tanto `title_candidate` quanto `author_candidate` extraem a mesma primeira linha de `doc.sampled_text`, enviando uma query duplicada ao Google Books e ignorando `doc.native_metadata.get("title")`.
  2. Em [`_resolve_collision`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L79-L90), o SHA-256 do arquivo de origem é recalculado do disco embora já tenha sido computado no Stage 1.
* **Recomendação:** Priorizar `native_metadata["title"]` (quando não genérico) na busca textual do Stage 3 e reutilizar o `sha256` já calculado em `_resolve_collision`.

---

### 10. [CRIT-10] Metadados de Cabeçalho, Concatenação Bilíngue (`Rejected by author:`) e Ortografia no Mermaid
* **Severidade:** Nit
* **Fontes:** `egm-structural` (#6), `egm-style` (#5, #6)
* **Escopo Afetado:** Cabeçalho ([L3–L5](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L3-L5)), `### 1. System Architecture` ([L29](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L29), [L57–L71](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L57-L71)) e `## Alternatives Considered` ([L196, L200, L204, L208, L212](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L196))
* **Descrição e Racional:**
  1. O cabeçalho de metadados (linhas 3–5) traz `* **Date:** 2026-11-05` e não explicita `* **Version:** 0.4.0`.
  2. Nas linhas 196, 200, 204, 208 e 212, ocorre concatenação bilíngue na mesma frase (`* **Decisão:** Rejected by author: ...`).
  3. Na linha 29, o termo *"detrás de um protocolo extensível"* pode ser substituído por *"abstraído pelo protocolo `LLMProvider`"*, e os rótulos entre aspas do diagrama Mermaid (linhas 57–71) podem usar acentuação padrão em português (`"Diretório"`, `"Não-PDF"`, `"Materialização"`, `"Catalográfica"`, `"Confiança"`).
* **Recomendação:** Atualizar a data/versão no cabeçalho, padronizar o rótulo de decisão e restaurar a acentuação nos rótulos entre aspas do Mermaid.
