# Intermediate Zoom Out Review — Stage 8 (`intermediate_zoom_out_report.md`)

**Arquivo Auditado:** [`docs/designs/bibliotec.md`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md) (Linhas `1..321`, sendo `FeatureRange: 1..210` e `DetailedRange: 211..321`)  
**Padrão Aplicado:** `zoom-out-standard` (Simplicidade, Altitude, YAGNI e Reuso)  
**Revisor:** Skeptical Architect (Zoom Out Goldfish)

---

## 1. Verificação de Integridade das Correções do Stage 5 (`zoom_out_report.md`)

Todas as **5 correções** exigidas na revisão inicial de Zoom Out (Stage 5) foram devidamente aplicadas e permanecem íntegras em [`docs/designs/bibliotec.md`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md):

1. **Remoção de Multi-Provedor Prematuro (YAGNI):** O suporte a `openai` e `anthropic` no MVP foi movido para [`Non-Goals`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L46) e removido de [`pyproject.toml`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L216), [`config.toml`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L153-L165) e da lista de arquivos, mantendo apenas o protocolo `LLMProvider` e a implementação `GeminiProvider` em [`src/bibliotec/core/llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L283-L285).
2. **Execução Sequencial Padrão (`workers = 1`):** A configuração padrão foi reduzida para `workers = 1` ([L84](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L84), [L149](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L149), [L186](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L186), [L300](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L300)), evitando contenção de RAM/CPU no Docling OCR e locks no SQLite.
3. **Correção de Altitude (`FeatureRange: 1..210`):** O bloco literal de 53 linhas de código Python foi substituído por uma tabela de alto nível em [`3. Domain Entities & Data Contracts`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L119-L127), e os detalhes de stdlib/regex foram transferidos para [`Detailed Implementation`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L211-L321).
4. **Reuso de Bibliotecas (`python-stdnum` e `pydantic-settings`):** A validação matemática de ISBN/DOI agora delega para `python-stdnum` ([L216](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L216), [L264](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L264)) e a resolução de precedência de configuração usa `pydantic-settings` com `TomlConfigSettingsSource` ([L130](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L130), [L236](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L236)).
5. **Desfragmentação de Módulos:** O antigo subpacote `enrichers/` (4 arquivos com classe base abstrata) foi consolidado em um único módulo enxuto [`src/bibliotec/core/enrichers.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L275-L277), reduzindo o plano de 33 para 27 arquivos.

---

## 2. Apontamentos Remanescentes de Simplicidade e Guardrails para o Stage 9

Não há **nenhum Blocker ou Major** remanescente sob a ótica do `zoom-out-standard`. Abaixo estão **2 apontamentos Nit** (um sobre concorrência híbrida residual no documento atual e um guardrail de simplicidade para a aplicação das correções dos críticos do Stage 7 no Stage 9):

### 1. [Nit] Complexidade Residual na Concorrência Híbrida (`workers > 1`) com Locks Manuais Multi-Estágio
* **Severity:** Nit
* **Affected Scope:** Technical Plan — Stage 2 ([L84](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L84)), CLI Contract ([L186](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L186)), Detailed Implementation — [`src/bibliotec/core/cache.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L255-L257) e [`src/bibliotec/core/pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L299-L301).
* **Simplicity Rationale:**
  * Embora o padrão tenha sido acertadamente mudado para `workers = 1`, o design ainda mantém a flag `--workers INT` propondo um modelo híbrido complexo quando `workers > 1`: paralelizar apenas os estágios de rede (Stage 3 e Stage 4) enquanto sincroniza via `threading.Lock` o Stage 1/5 (SQLite `state.db`), o Stage 2 (singleton do Docling OCR) e, conforme apontado no item 6 do [`critic_report.md`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/critic_report.md#L49-L51), também a resolução de colisão e escrita em disco no Stage 5.
  * Para lotes locais de 100 a 500 PDFs apoiados por cache SQLite por `SHA-256`, manter múltiplos locks coordenando threads entre estágios síncronos adiciona complexidade de sincronização com ganho marginal no MVP.
  * **Recomendação para o Stage 9:** Se mantiver `--workers` no MVP, isole a concorrência de forma simples (por exemplo, pré-extraindo sequencialmente ou protegendo o bloco de persistência final `cache + organizer` com um único lock de finalização no `pipeline.py`), sem espalhar primitivas de sincronização por múltiplos módulos.

### 2. [Nit] Guardrail contra Sobre-Engenharia ao Incorporar o Apontamento 1 do `critic_report.md` (Detecção de PDF Escaneado)
* **Severity:** Nit
* **Affected Scope:** Technical Plan — Stage 2 ([L80-L84](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L80-L84)) e Detailed Implementation — [`src/bibliotec/extractors/native_pdf.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L267-L270).
* **Simplicity Rationale:**
  * O Apontamento 1 do [`critic_report.md`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/critic_report.md#L19-L23) identifica um problema real de domínio (uma folha de rosto digital de portal como JSTOR/SciELO pode ter $> 200$ caracteres e mascarar um PDF cujas páginas seguintes são imagens escaneadas), mas sugere simultaneamente *"ignorar linhas repetidas de rodapé entre páginas"*.
  * Implementar algoritmos de detecção/deduplicação de cabeçalhos e rodapés entre páginas introduziria heurísticas frágeis e desnecessárias no extrator nativo.
  * **Recomendação para o Stage 9:** Ao aplicar as correções do `critic_report.md` no Stage 9, adote **apenas a regra simples por página** (considerar o documento como escaneado quando mais da metade das páginas inspecionadas tiver menos de 30 caracteres alfanuméricos úteis, enviando as páginas sem texto dentro da janela de até 8 páginas para o Docling) e **não** adicione algoritmos de detecção de rodapé. As demais correções do [`critic_report.md`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/critic_report.md) (exclusão de `TARGET_DIR` via `Path.resolve()`, caminho `~/.cache/bibliotec/state.db` cacheando apenas `confidence_score >= confidence_min`, limite `sampled_text[:15000]` e preservação do nome original em `revisao_manual/`) são simples, diretas e preservam integralmente a altitude do documento.
