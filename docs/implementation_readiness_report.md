# Relatório de Prontidão de Implementação — Stage 9 (`implementation_readiness_report.md`)

**Arquivo Auditado:** [`docs/designs/bibliotec.md`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L211-L321)  
**Escopo Auditado:** `DetailedRange: 211..321` (com leitura contextual de `1..210`)  
**Revisores:** `egm-implementation-readiness`, `egm-codebase-details`, `egm-style`

---

## Resumo Executivo

* **3 Blockers:**
  1. **Módulo `stdnum.doi.is_valid` inexistente (`egm-codebase-details`):** A biblioteca `python-stdnum` possui `stdnum.isbn.is_valid` (e `stdnum.issn`), mas **não possui `stdnum.doi`** (pois o padrão DOI ISO 26324 não tem dígito verificador matemático). Tentar importar `stdnum.doi` causará `ModuleNotFoundError`.
  2. **Esquema SQL (`DDL`), caminho físico e política de persistência do `state.db` ausentes (`egm-implementation-readiness` & `egm-codebase-details`):** O Item 11 (`cache.py`) não especifica o caminho padrão (`~/.cache/bibliotec/state.db`), as colunas exatas do `CREATE TABLE processed_files` nem a regra de só persistir classificações com `confidence_score >= confidence_min`.
  3. **Contratos de dados incompletos para `ExecutionSummary`, `PipelineEvent` e parsing de `authors` (`egm-implementation-readiness`):** Os modelos `ExecutionSummary` e `PipelineEvent` são citados no Item 7 sem definição de campos, e a regra de extração do sobrenome em `namer.py` a partir de `authors: list[str]` precisa ser explicitada.
* **4 Majors (`egm-implementation-readiness`):**
  4. Formato de `taxonomy_capes.json`, cálculo de `taxonomy_version` e fallback para `revisao_manual/` quando o par `(grande_area, area_basica)` for irreparável.
  5. Condição booleana exata para "título/autor genéricos" e *short-circuit* quando texto $< 50$ caracteres sem metadado externo em `llm.py`.
  6. Mapeamento entre as tabelas TOML (`[general]`, `[llm]`, `[api_keys]`) e variáveis de ambiente (`AliasChoices`) no `pydantic-settings` em `config.py`.
  7. Regras explícitas de materialização para `revisao_manual/` (preservar `source_path.name`), modo `--dry-run` (não criar pastas temáticas nem copiar PDFs) e exclusão de `<TARGET_DIR>` na varredura recursiva de `scanner.py`.
* **5 Nits (`egm-codebase-details` & `egm-style`):**
  8. Uso do wrapper `DocumentStream(name=..., stream=bytes_io)` de `docling.datamodel.base_models` ao passar `io.BytesIO` para `DocumentConverter.convert()`.
  9–12. Ajustes de calibração textual no `DetailedRange` (substituir `"Prova matematicamente"`, `"enxuto sem hierarquias... desnecessárias"`, `"sem risco de"` e detalhar `cli/__init__.py`).

---

## Apontamentos Detalhados

### 1. [Blocker] API Inexistente (`stdnum.doi.is_valid`) na Biblioteca `python-stdnum`
* **Revisor:** `egm-codebase-details`
* **Escopo Afetado:** Item 13 ([`src/bibliotec/extractors/identifiers.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L263-L265)) e Stage 3 ([linha 87](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L87)).
* **Descrição e Correção:**
  O padrão DOI (ISO 26324) não possui dígito verificador matemático e `python-stdnum` não possui o submódulo `stdnum.doi`.
  * **Correção:** Usar `stdnum.isbn.is_valid` (e `stdnum.isbn.format`) para validar o dígito verificador de ISBN-10/ISBN-13, e validar DOIs via expressão regular estrita (`r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b"`, com remoção de pontuação terminal `.` `,` `;` `)`).

### 2. [Blocker] Localização, Esquema SQL (`DDL`) e Política de Persistência do Cache SQLite (`state.db`)
* **Revisores:** `egm-implementation-readiness` & `egm-codebase-details`
* **Escopo Afetado:** Item 11 ([`src/bibliotec/core/cache.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L255-L257)) e Stage 1 ([linha 78](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L78)).
* **Descrição e Correção:**
  * **Correção:** Especificar:
    1. Caminho padrão: `~/.cache/bibliotec/state.db`.
    2. Esquema SQL: `CREATE TABLE IF NOT EXISTS processed_files (sha256 TEXT NOT NULL, taxonomy_version TEXT NOT NULL, model_name TEXT NOT NULL, classification_json TEXT NOT NULL, used_ocr INTEGER NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY (sha256, taxonomy_version, model_name))`.
    3. Política: Persistir no cache apenas classificações com `confidence_score >= confidence_min`, permitindo que documentos enviados para `revisao_manual/` sejam reavaliados em execuções futuras.

### 3. [Blocker] Contratos de `ExecutionSummary`, `PipelineEvent` e Parsing de `authors`
* **Revisor:** `egm-implementation-readiness`
* **Escopo Afetado:** Item 7 ([`src/bibliotec/core/models.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L239-L241)), Item 20 ([`src/bibliotec/storage/namer.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L291-L293)) e Seção 3 ([linhas 119-127](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L119-L127)).
* **Descrição e Correção:**
  * **Correção:**
    1. Adicionar `ExecutionSummary` (`total_scanned`, `organized_count`, `manual_review_count`, `duplicate_skipped_count`, `ignored_non_pdf_count`, `error_count`, `manual_review_ratio`, `exceeded_manual_review_ceiling`, `entries: list[FileManifestEntry]`) e `PipelineEvent` (`stage`, `source_path`, `status`, `message`) na tabela de contratos da Seção 3 e no Item 7.
    2. Especificar no Item 20 (`namer.py`) que cada string em `authors: list[str]` segue o formato `"Sobrenome, Nome"`: para 1 autor usa `authors[0]`; para 2 autores extrai o sobrenome antes da vírgula (`a.split(",")[0].strip()`) formando `f"{s1}; {s2}"`; para 3+ autores forma `f"{s1} et al."`.

### 4. [Major] Formato de `taxonomy_capes.json`, `taxonomy_version` e Fallback de Par Irreparável
* **Revisor:** `egm-implementation-readiness`
* **Escopo Afetado:** Item 8 ([`taxonomy_capes.json`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L243-L245)) e Item 9 ([`src/bibliotec/core/taxonomy.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L247-L249)).
* **Descrição e Correção:**
  * **Correção:** Definir que `taxonomy_capes.json` possui a estrutura `{"version": "capes-cnpq-v1", "areas": {"Grande Área": ["Área Básica", ...]}}` (sem caracteres `/` nos nomes de áreas), que `taxonomy_version` lê o campo `"version"`, e que `validate_or_repair_pair` retorna `None` (forçando `confidence_score = 0.0` e envio para `revisao_manual/`) caso nem `area_basica` nem `grande_area` constem no catálogo.

### 5. [Major] Condição Determinística de "Título/Autor Genéricos" e Short-Circuit em `llm.py`
* **Revisor:** `egm-implementation-readiness`
* **Escopo Afetado:** Item 18 ([`src/bibliotec/core/llm.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L283-L285)) e Stage 4 ([linha 106](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L106)).
* **Descrição e Correção:**
  * **Correção:**
    1. Se `len(alphanumeric_chars) < 50` e não houver `ExternalMetadata`, fazer *short-circuit* antes de chamar a API Gemini, retornando imediatamente `confidence_score = 0.0` com motivo `"Texto extraído insuficiente (< 50 caracteres) e sem metadados externos"`.
    2. Definir título genérico como string vazia, iniciando por `"microsoft powerpoint -"` / `"microsoft word -"`, ou pertencente a `{"sem título", "sem titulo", "untitled", "unknown", "desconhecido", "documento", "pdf", "artigo", "livro", "slide"}` (case-insensitive) quando `authors` estiver vazio ou contiver apenas `"Autor Desconhecido"`, aplicando `confidence_score = min(score, 0.50)`.
    3. Truncar `sampled_text` em no máximo `15.000` caracteres antes do envio ao Gemini (conforme também apontado no Stage 7).

### 6. [Major] Mapeamento de Seções TOML e `AliasChoices` de Variáveis de Ambiente em `config.py`
* **Revisor:** `egm-implementation-readiness`
* **Escopo Afetado:** Item 6 ([`src/bibliotec/core/config.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L235-L237)).
* **Descrição e Correção:**
  * **Correção:** Especificar que `AppConfig` agrupa os submodelos `general: GeneralConfig`, `llm: LLMConfig` e `api_keys: ApiKeysConfig`, resolvendo variáveis de ambiente via `AliasChoices` com precedência `BIBLIOTEC_GEMINI_API_KEY > GEMINI_API_KEY`, `BIBLIOTEC_GOOGLE_BOOKS_API_KEY > GOOGLE_BOOKS_API_KEY` e `BIBLIOTEC_OPENALEX_POLITE_EMAIL > OPENALEX_POLITE_EMAIL`.

### 7. [Major] Regras de `revisao_manual/`, `--dry-run`, Exclusão de `<TARGET_DIR>` e Densidade por Página
* **Revisores:** `egm-implementation-readiness` & `egm-design` (Stage 7)
* **Escopo Afetado:** Item 10 (`scanner.py`), Item 14 (`native_pdf.py`), Item 15 (`ocr_docling.py`) e Item 21 (`organizer.py`).
* **Descrição e Correção:**
  * **Correção:**
    1. Em `scanner.py`: Resolver `SOURCE_DIR.resolve()` e `TARGET_DIR.resolve()`, rejeitar `SOURCE_DIR == TARGET_DIR` e pular qualquer arquivo dentro da subárvore de `TARGET_DIR`.
    2. Em `native_pdf.py` e `ocr_docling.py`: Avaliar densidade por página (acionar OCR se mais da metade das páginas inspecionadas tiver `< 30` caracteres alfanuméricos úteis, recortando até 8 páginas sem texto dentre as 8 primeiras e 2 últimas páginas).
    3. Em `organizer.py`: Preservar `source_path.name` para arquivos enviados a `revisao_manual/` (com resolução de colisão por `SHA-256` / sufixo ` (2).pdf`); em modo `--dry-run`, não criar pastas temáticas nem copiar/mover PDFs, gravando apenas `manifest.json` e `relatorio_revisao.md`.

### 8. [Nit] Uso de `DocumentStream` no Docling (`ocr_docling.py`)
* **Revisores:** `egm-codebase-details` & `egm-implementation-readiness`
* **Escopo Afetado:** Item 15 ([`src/bibliotec/extractors/ocr_docling.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L271-L273)).
* **Descrição e Correção:** Encapsular o `io.BytesIO` em `DocumentStream(name=f"{path.stem}_slice.pdf", stream=buf)` (`from docling.datamodel.base_models import DocumentStream`) ao chamar `DocumentConverter.convert()`.

### 9–12. [Nit] Calibração de Estilo e Precisão Textual (`egm-style`)
* **Escopo Afetado:** Linhas 257, 269, 277, 297, 303–305, 313, 317.
* **Descrição e Correção:** Remover hipérboles (*"Prova matematicamente"*, *"sem risco de"*, *"em milissegundos"*, *"nunca sofra deriva"*, *"enxuto sem hierarquias... desnecessárias"*) e detalhar o papel de `src/bibliotec/cli/__init__.py`.
