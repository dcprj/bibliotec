# Relatório Consolidado de Revisão e Resolução (`/egm:egm-review` — Goldfish Review Report)

* **Documento Alvo:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md)
* **Versão do Codebase:** `v0.4.0`
* **Data da Consolidação:** `2026-11-06`
* **Relatórios por Etapa:**
  * Stage 5 (Initial Zoom Out): [zoom_out_report.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/zoom_out_report.md)
  * Stage 6 (Comprehension Test): [comprehension_report.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/comprehension_report.md)
  * Stage 7 (Critic Review — `1..213`): [critic_report.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/critic_report.md)
  * Stage 8 (Intermediate Zoom Out — `1..324`): [intermediate_zoom_out_report.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/intermediate_zoom_out_report.md)
  * Stage 9 (Implementation Readiness — `214..324`): [implementation_readiness_report.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/implementation_readiness_report.md)

---

## 1. Resumo das Resoluções Aplicadas no Código (`v0.4.0`)

| ID | Achado Consolidado | Módulos Alterados | Resolução Aplicada |
| :--- | :--- | :--- | :--- |
| **`CRIT-03` / `ZOUT-05`** | Sobrescrita silenciosa de arquivos homônimos vindos de subpastas diferentes em `revisao_manual/` e recálculo desnecessário de SHA-256 em `_resolve_collision`. | [`src/bibliotec/storage/organizer.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L57-L355) | `_resolve_collision` agora recebe `src_sha256` opcional (evitando re-hashing de disco) e é chamado também em `add_manual_review` e `add_error`, atribuindo sufixo incremental ` (2).pdf` para arquivos distintos e prevenindo perda de dados. |
| **`CRIT-04` / `ZOUT-04`** | Chave de cache SQLite com `model_name` estático sob fallback e ausência de suporte a `[llm.providers.<nome>].model` em `create_provider_chain`. | [`src/bibliotec/core/llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L93-L1309), [`src/bibliotec/core/pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/pipeline.py#L248-L250) | `ClassificationResult` passou a incluir `provider_name` e `model_name` efetivos; `pipeline.py` persiste no SQLite usando o modelo efetivo que classificou a obra; `create_provider_chain` respeita `[llm.providers.<nome>].model`. |
| **`CRIT-05` / `CRIT-09` / `IMPL-02`** | Cabeçalho `mailto:` do Polite Pool do OpenAlex omitido na busca por título, busca por DOI sem `@retry`, query duplicada título/autor e `_USER_AGENT` fixo em `0.1.0`. | [`src/bibliotec/core/enrichers.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/enrichers.py#L18-L278) | `_get_json` agora aceita `headers` e filtra erros transitórios (`429`, `5xx`, `TimeoutException`, `TransportError`); `_query_openalex_by_title` e `_query_openalex_by_doi` enviam o cabeçalho `User-Agent` com `mailto:` e `__version__`; `_extract_title_author_candidates` extrai candidatos distintos. |
| **`CRIT-05` / `ZOUT-03`** | Código duplicado de pré/pós-validação em `llm.py`, constantes duplicadas `_GENERIC_TITLES` e mutação concorrente de `self._model` em `GeminiProvider`. | [`src/bibliotec/core/llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L42-L295) | Removidas constantes mortas duplicadas; extraídas as funções `_check_short_circuit` e `_finalize_classification`; ampliado `_is_generic_openai_retryable` para cobrir `TimeoutException`, `TransportError` e HTTP `529`; eliminada a mutação não sincronizada de `self._model` entre threads. |
| **`CRIT-06` / `ZOUT-02` / `IMPL-04`** | Prontidão da fronteira `bibliotec.core` para a Desktop GUI (`v1.0.0`): ausência de `cancel_event`, `dry_run` e `create_provider_chain` em `run_pipeline` e exportações em `core/__init__.py`. | [`src/bibliotec/core/pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/pipeline.py#L280-L435), [`src/bibliotec/core/__init__.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/__init__.py#L32-L87) | `run_pipeline` agora aceita `dry_run: bool = False` e `cancel_event: threading.Event | None = None`, aciona `create_provider_chain(config)` automaticamente quando há chaves configuradas e `core/__init__.py` exporta todos os provedores e `create_provider_chain`. |

---

## 2. Resumo das Resoluções Aplicadas na Documentação ([bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md))

1. **Alinhamento Arquitetural (`FeatureRange` `1..213`):**
   * Atualizados `Overview`, `Goals`, `Non-Goals`, diagrama Mermaid (`flowchart TD`), `Stage 1` a `Stage 5` para refletir o hub de 6 provedores (`gemini`, `groq`, `nvidia`, `deepseek`, `claude`, `github`), o `FallbackLLMDispatcher`, os arquivos companheiros `.md` ABNT NBR 6023, a pasta `duplicatas/` e o diagnóstico tipado de arquivos não-PDF (`[DIAG-06]`).
   * Completada a tabela da Seção 3 (`Domain Entities & Data Contracts`) com `ClassificationResult`, `SessionState` e os campos `total_files`, `completed_files` e `timestamp` de `PipelineEvent`.
   * Atualizadas as Seções 4 (`config.toml` e regras de precedência) e 5 (`CLI Contract`) com todas as 8 chaves de API, `fallback_chain`, invocação direta na raiz (`bibliotec -o ... -d ...`), `bibliotec resume` e `bibliotec cache {clean,clear,status,path}`.
2. **Alinhamento de Implementação (`DetailedRange` `214..End`):**
   * Substituídos os marcadores obsoletos `(Criar)` por `(Implementado — v0.4.0)` no presente do indicativo.
   * Adicionados os módulos `src/bibliotec/core/logging.py`, `src/bibliotec/core/session.py`, `src/bibliotec/storage/companion.py`, `CHANGELOG.md` e todas as suítes de teste de `tests/`.
