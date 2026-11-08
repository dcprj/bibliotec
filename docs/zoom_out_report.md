# Relatório de Auditoria Arquitetural — Stage 5 (Initial Zoom Out Review)

**Documento Auditado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md) (linhas 1–324)  
**Estado de Referência do Código:** `v0.4.0` ([CHANGELOG.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/CHANGELOG.md), [pyproject.toml](file:///Users/dario/Projetos-de-aplicativos/bibliotec/pyproject.toml))

---

## Visão Geral de Alto Nível (Simplicidade, YAGNI e Separação de Altitude)

A arquitetura conceitual descrita no `FeatureRange` (linhas 1–213) e no `DetailedRange` (linhas 214–324) mantém um isolamento claro entre o motor central (`bibliotec.core`, `bibliotec.extractors`, `bibliotec.storage`) e a camada de apresentação (`bibliotec.cli`), requisito necessário antes de iniciar a fase de interface gráfica (GUI).

Contudo, o documento de design permanece congelado no estado inicial do MVP (`v0.0.3`/`v0.1.0`) e apresenta divergências arquiteturais em relação ao sistema real implementado na `v0.4.0`, além de oportunidades de simplificação e eliminação de duplicação no código antes de acoplar uma GUI.

---

## Achados de Auditoria (Findings)

### 1. Divergência Arquitetural: Ecossistema Multi-Provedor e Cadeia de Fallback Omitidos no Design
* **Severity:** Blocker
* **Affected Scope:** `## Overview` (linha 29), `## Goals` (linha 41), `## Non-Goals` (linha 46), `### 2. Core Pipeline Stages - Stage 4` (linha 95), `### 4. User Configuration File` (linhas 137, 156–168), `### 5. CLI Contract` (linhas 173–190) e `## Detailed Implementation` — Item 6 (linhas 238–240) e Item 18 (linhas 286–288).
* **Simplicity Rationale:** O documento declara como *Non-Goal* o suporte a múltiplos provedores de LLM e descreve apenas o `GeminiProvider` (`gemini-2.5-flash`). Na implementação `v0.4.0`, [src/bibliotec/core/llm.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py) implementa 6 provedores (`GeminiProvider`, `NvidiaProvider`, `DeepSeekProvider`, `ClaudeProvider`, `GroqProvider`, `GitHubModelsProvider`), orquestrados por [`FallbackLLMDispatcher`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L1059-L1172) e pela fábrica [`create_provider_chain`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L1175-L1309), com `fallback_chain = ["groq", "nvidia", "deepseek"]` e modelo padrão `gemini-3.5-flash` em [`LLMConfig`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/config.py#L72-L94). Antes de avançar para a fase de GUI (que exporá seleção de provedor, status de fallback e configuração de chaves), o documento de design precisa refletir essa arquitetura multi-provedor.

### 2. Violação DRY nos Adaptadores de LLM (`llm.py` com 1.309 linhas)
* **Severity:** Major
* **Affected Scope:** `### 2. Core Pipeline Stages - Stage 4` (linhas 93–108) e `## Detailed Implementation` — Item 18 ([src/bibliotec/core/llm.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py), linhas 286–288).
* **Simplicity Rationale:** Em [src/bibliotec/core/llm.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py), quatro classes (`NvidiaProvider`, `DeepSeekProvider`, `GroqProvider`, `GitHubModelsProvider`) utilizam o protocolo OpenAI-compatível (`POST /chat/completions` via `httpx`), e todas as 6 classes de provedores repetem ~75 linhas idênticas de pré-validação (*short-circuit* `< 50` chars), montagem de prompt, limpeza de markdown JSON, validação de taxonomia (`validate_or_repair_pair`) e trava de título genérico (`min(confidence, 0.50)`). Isso expandiu `llm.py` para 1.309 linhas. O design na seção de Stage 4 e no Item 18 deve prever a centralização das travas determinísticas pré e pós-LLM em um único ponto (ou adaptador OpenAI-compatível parametrizado), evitando manter 6 cópias da mesma regra de negócio.

### 3. Comportamento de Materialização (`companion.py` e pasta `duplicatas/`) Ausente da Especificação
* **Severity:** Major
* **Affected Scope:** `### 2. Core Pipeline Stages - Stage 5` (linhas 109–119) e `## Detailed Implementation` — Itens 19 a 21 (linhas 290–300).
* **Simplicity Rationale:** O design afirma na linha 117 que *"duplicatas exatas são ignoradas (`duplicate_skipped`)"* e não menciona arquivos `.md` companheiros. Na implementação `v0.4.0`:
  1. O módulo [src/bibliotec/storage/companion.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/companion.py) gera um arquivo Markdown companheiro (`<nome>.md`) com *front matter* YAML e referência ABNT NBR 6023 ao lado de cada PDF organizado ([`LibraryOrganizer.add_organized`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L256-L268)).
  2. Duplicatas exatas (`duplicate_skipped`) são copiadas/movidas fisicamente para `<TARGET_DIR>/duplicatas/` acompanhadas de um `.md` companheiro explicativo apontando para a obra canônica ([`LibraryOrganizer.add_organized`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L220-L250)).
  3. O diagnóstico tipado de arquivos não-PDF (`.webloc`, `.url`, `.epub`, etc. — entrega `[DIAG-06]` da `v0.4.0`) em [`LibraryOrganizer.add_ignored_non_pdf`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/storage/organizer.py#L327-L363) e a seção dedicada em `relatorio_revisao.md` não constam no design.  
  Como a futura GUI exibirá o resultado da biblioteca, duplicatas e arquivos companheiros, o Stage 5 e o `DetailedRange` precisam documentar `companion.py`, o diretório `duplicatas/` e o diagnóstico de não-PDFs.

### 4. Módulos de Infraestrutura e Ergonomia de CLI da `v0.4.0` Omitidos (`logging.py`, `session.py`, `resume`, `cache`)
* **Severity:** Major
* **Affected Scope:** `### 3. Domain Entities & Data Contracts` (linhas 120–130), `### 5. CLI Contract` (linhas 170–190) e `## Detailed Implementation` (linhas 214–324).
* **Simplicity Rationale:** Quatro capacidades já implementadas e necessárias para reuso na futura GUI estão ausentes do documento:
  1. **Persistência e retomada de sessão:** [src/bibliotec/core/session.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/session.py) (`SessionState`, `.bibliotec_session.json`) e o comando `bibliotec resume` em [src/bibliotec/cli/main.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/cli/main.py#L628-L661).
  2. **Logging estruturado silencioso:** [src/bibliotec/core/logging.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/logging.py) (`setup_logging`, redirecionamento para `bibliotec.log` e silenciamento de loggers ruidosos como `RapidOCR`/`docling`/`torch`).
  3. **Gestão de cache e ergonomia na CLI:** O grupo de subcomandos `bibliotec cache {clean,clear,status,path}` ([src/bibliotec/cli/main.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/cli/main.py#L667-L715)) e a invocação direta na raiz `bibliotec -o <origem> -d <destino> [--provider/-p] [--verbose/-v]` (com `organize` marcado como `hidden=True`).
  4. **Contrato de `PipelineEvent`:** Em [`PipelineEvent`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/models.py#L110-L119), os campos `total_files`, `completed_files` e `timestamp` foram adicionados para alimentar barras de progresso determinísticas (e serão consumidos pela GUI), mas a tabela da Seção 3 (linha 129) lista apenas `stage`, `source_path`, `status`, `message`.

### 5. Queda de Altitude (Weeds) no `DetailedRange` (Linhas 214–324) vs. Contratos de Alto Nível
* **Severity:** Nit
* **Affected Scope:** `## Detailed Implementation` (linhas 218–324, Itens 4, 10, 11, 13, 15, 18 e 20).
* **Simplicity Rationale:** Vários itens do `DetailedRange` incluem detalhes micro-implementacionais (expressões regulares literais `r"\b10\.\d{4,9}/..."`, queries DDL SQL completas `CREATE TABLE IF NOT EXISTS...`, chamadas internas `a.split(",")[0].strip()`, ou a constante `__version__ = "0.1.0"` na linha 231 quando o pacote já está na `0.4.0`). O `DetailedRange` deve focar nas responsabilidades do módulo, suas interfaces públicas e invariantes de domínio, atualizando a versão para `0.4.0` e incluindo os arquivos adicionados (`src/bibliotec/core/logging.py`, `src/bibliotec/core/session.py`, `src/bibliotec/storage/companion.py` e os novos arquivos de teste).

### 6. Duplicação de Contratos de Saída (`ClassificationResult` vs. `LLMClassificationOutput`)
* **Severity:** Nit
* **Affected Scope:** `### 3. Domain Entities & Data Contracts` (linha 126) e `## Detailed Implementation` — Itens 7, 18 e 22.
* **Simplicity Rationale:** O design especifica apenas o modelo Pydantic [`LLMClassificationOutput`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/models.py#L70-L81), mas [src/bibliotec/core/llm.py](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/llm.py#L106-L120) declara uma `@dataclass` paralela `ClassificationResult` com os mesmos 9 campos (acrescentando apenas `used_ocr: bool`), exigindo conversão manual para `dict` em [`_classification_to_dict`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/src/bibliotec/core/pipeline.py#L72-L83). Documentar essa distinção ou unificar em torno do modelo Pydantic de domínio evita estruturas redundantes quando a GUI consumir os resultados do pipeline.
