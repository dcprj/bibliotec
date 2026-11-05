# Initial Zoom Out Review (`zoom_out_report.md`)

**Target File:** [`docs/designs/bibliotec.md`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md)  
**Reviewed Ranges:** Feature Architecture (`1..286`) & Detailed Implementation (`287..421`)  
**Reviewer Role:** Skeptical Architect (Zoom Out Goldfish)

---

## Executive Summary

O documento apresenta uma visão clara do problema de negócio, boas restrições de escopo (`Non-Goals`) e decisões arquiteturais acertadas para o domínio — em especial o uso de catálogo fechado da CAPES/CNPq e o recorte seletivo de páginas antes de acionar o OCR local. 

Contudo, sob a ótica do padrão **Zoom Out** (simplicidade, YAGNI, reuso e separação entre arquitetura e detalhes de implementação), o projeto sofre de **sobre-engenharia em abstrações prematuras (múltiplos provedores de LLM e hierarquias de classes para clientes HTTP)**, **otimização prematura de concorrência (`workers = 4` conflitando com OCR pesado e SQLite)**, **reinvenção de roda em validação de ISBN/configuração** e **queda de altitude (weeds)** na seção de arquitetura.

---

## Findings

### 1. [Major] Violação de YAGNI e Inconsistência no Suporte Multi-Provedor de LLM no MVP
* **Severity:** Major
* **Affected Scope:** Overview (L29), Technical Plan — Stage 4 (L99–101), User Configuration (L224–235), CLI Contract (L256), Detailed Implementation — `pyproject.toml` (L292) e `src/bibliotec/llm/openai_provider.py` (L383–385).
* **Simplicity Rationale:**
  * O objetivo central do MVP (L32, L37) é validar o motor de classificação via CLI atingindo $\ge 80\%$ de precisão no conjunto de testes usando `Gemini API` (`gemini-2.5-flash`).
  * Apesar disso, o design exige empacotar três SDKs pesados (`google-genai`, `openai`, `anthropic` na L292), expor chaves para todos eles no `config.toml` (L232–234) e criar [`src/bibliotec/llm/openai_provider.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L383-L385), cuja descrição chega a misturar dois SDKs incompatíveis no mesmo arquivo (*"Implementa `OpenAIProvider` usando Structured Outputs (`beta.chat.completions.parse`) e `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`"* — a API da Anthropic não utiliza `beta.chat.completions.parse`).
  * **Recomendação:** Mantenha o protocolo `LLMProvider` como ponto de extensão arquitetural, mas implemente **apenas o `GeminiProvider`** no MVP (ou utilize uma camada única baseada em endpoint compatível com OpenAI / `litellm` se múltiplos provedores forem estritamente necessários agora). Remova `anthropic` (e `openai`, se não for requisito imediato de lançamento) das dependências obrigatórias do `pyproject.toml`.

---

### 2. [Major] Otimização Prematura e Risco Arquitetural: Pool de Concorrência (`workers = 4`) Acoplado ao Docling OCR e SQLite
* **Severity:** Major
* **Affected Scope:** Technical Plan — Stage 1 (L77) & Stage 2 (L83), User Configuration (L219–220), CLI Contract (L262), Detailed Implementation — [`src/bibliotec/core/pipeline.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L399-L401) e [`src/bibliotec/core/cache.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L331-L333).
* **Simplicity Rationale:**
  * Definir `workers = 4` como padrão para o pipeline inteiro significa que até 4 documentos escaneados podem instanciar e executar o `DocumentConverter` do Docling simultaneamente. O Docling carrega modelos pesados de visão/layout e já paraleliza operações internamente na CPU/GPU; 4 instâncias concorrentes causarão contenção severa de memória RAM/CPU.
  * Além disso, 4 workers paralelos gravando no mesmo banco SQLite (`state.db`) e disparando requisições simultâneas para a API gratuita/padrão do Gemini e Google Books aumentarão a incidência de `sqlite3.OperationalError: database is locked` e erros `HTTP 429`.
  * **Recomendação:** Simplifique o MVP para execução sequencial por padrão (`workers = 1`) ou restrinja a concorrência exclusivamente às chamadas HTTP de enriquecimento/LLM (mantendo o Docling OCR e a escrita no SQLite estritamente serializados).

---

### 3. [Major] Queda de Altitude ("Weeds") na Seção de Arquitetura (`FeatureRange: 1..286`)
* **Severity:** Major
* **Affected Scope:** Technical Plan — Stage 2 (L80–83), Stage 3 (L86–95), Stage 5 (L128–137) e Section 3: Data Models (L143–197).
* **Simplicity Rationale:**
  * A seção de arquitetura de alto nível desce repetidamente para detalhes de implementação de baixo nível que pertencem ao código ou à especificação detalhada:
    1. **Bloco literal de código Python (L145–197):** 53 linhas de código Pydantic (`ExtractedDocument`, `ExternalMetadata`, `LLMClassificationOutput`, etc.) duplicando o que já está descrito em prosa nos estágios e novamente em `src/bibliotec/core/models.py` (L315–317).
    2. **Detalhes de stdlib e regex (L83, L87, L90–93, L130, L134):** Menções explícitas a `io.BytesIO`, `shutil.copy2`, `len(nome.encode("utf-8"))`, `rapidfuzz.fuzz.token_set_ratio`, expressões regulares literais (`10.\d{4,9}/[-._;()/:A-Z0-9]+`) e URLs completas de endpoints REST.
  * **Recomendação:** Substitua o código Python literal das linhas 145–197 por uma tabela concisa de contratos/entidades de domínio ou diagrama de dados, e mova detalhes de chamadas de biblioteca padrão (`io.BytesIO`, `shutil.copy2`, regexes exatas) para a seção `Detailed Implementation`.

---

### 4. [Nit] Reinvenção da Roda em Validação de ISBN/DOI e Resolução de Configuração
* **Severity:** Nit
* **Affected Scope:** Technical Plan — Stage 3 (L86–88), Section 4 (L203–208), Detailed Implementation — [`src/bibliotec/extractors/identifiers.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L339-L341) e [`src/bibliotec/core/config.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L311-L313).
* **Simplicity Rationale:**
  * **Validação matemática manual de ISBN (L88, L340):** Implementar regexes próprias e cálculo manual de dígito verificador módulo 11 (com tratamento de `'X'`) e módulo 10 reinventa funcionalidade já resolvida por bibliotecas leves e testadas como `python-stdnum` (`stdnum.isbn`, `stdnum.doi`) ou `isbnlib`.
  * **Resolução manual de precedência de configuração (L203–207, L312):** Codificar manualmente a fusão em 4 níveis (CLI flags $\rightarrow$ variáveis de ambiente $\rightarrow$ `./bibliotec.toml` $\rightarrow$ `~/.config/bibliotec/config.toml`) em `config.py` reimplementa o que `pydantic-settings` (com `TomlConfigSettingsSource`) já oferece nativamente no ecossistema Pydantic v2.

---

### 5. [Nit] Fragmentação Excessiva de Módulos e Classes Abstratas Desnecessárias (`DetailedRange: 287..421`)
* **Severity:** Nit
* **Affected Scope:** Detailed Implementation — [`src/bibliotec/enrichers/__init__.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L351-L353), [`src/bibliotec/enrichers/base.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L355-L357), [`src/bibliotec/enrichers/openalex.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L359-L361), [`src/bibliotec/enrichers/google_books.py`](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L363-L365).
* **Simplicity Rationale:**
  * O plano propõe criar **33 arquivos** divididos em 6 subpacotes para uma ferramenta CLI greenfield.
  * Em especial, o subpacote `bibliotec.enrichers` cria 4 arquivos (`__init__.py`, `base.py`, `openalex.py`, `google_books.py`) com uma classe abstrata em `base.py` e um `MetadataEnricherService` apenas para encapsular duas chamadas HTTP GET (uma para OpenAlex e outra para Google Books) que possuem contratos de entrada distintos (DOI vs. ISBN).
  * **Recomendação:** Elimine a classe base abstrata `enrichers/base.py` e consolide os clientes de enriquecimento em funções diretas (ou em um único módulo `src/bibliotec/core/enrichers.py`), reduzindo o boilerplate de pacotes `__init__.py` vazios.
