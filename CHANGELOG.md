# Changelog do BiblioTEC

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adota [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.0.5] - 2026-11-05

### Corrigido

- **src/bibliotec/cli/main.py**: removida chamada a `on_event` inexistente que
  travava a barra de progresso visual.
- **src/bibliotec/core/scanner.py**: conformidade com ISO 32000-1 § 7.5.2 na
  detecção de `%PDF-` dentro dos primeiros 1024 bytes. Leitores conformes
  aceitam até 1024 bytes de dados arbitrários prévios (ex: cabeçalhos
  HTTP/multipart de repositórios institucionais), então a verificação agora
  busca a assinatura em qualquer posição do cabeçalho lido, não apenas no
  início.

### Adicionado

- **src/bibliotec/core/pipeline.py**: suporte a avanço de barra de progresso
  em eventos `duplicate_skipped`, garantindo que o contador de progresso
  avance corretamente também para arquivos duplicados pulados.

## [0.0.4] - 2026-11-05

### Adicionado

- **src/bibliotec/storage/companion.py**: geração automática de arquivo
  companheiro (.md) ao lado do PDF organizado, contendo Front Matter YAML
  completo (título, subtítulo, autores, ano, grande área, área básica, tipo,
  DOI, ISBN, SHA-256, confidence_score, used_ocr, source_file, organized_at)
  e referência bibliográfica formatada segundo a ABNT NBR 6023.
- **src/bibliotec/storage/organizer.py**: integração para materializar o
  arquivo companheiro juntamente com o PDF no destino (arquivo `.md` com o
  mesmo nome base do PDF, gerado apenas quando não for `--dry-run`).
- **src/bibliotec/storage/__init__.py**: exporta `generate_companion_markdown`
  como parte da API pública da camada de armazenamento.
- **tests/test_companion.py**: 18 testes unitários e de integração para o
  módulo companheiro (formato de autores ABNT, referência bibliográfica,
  front matter YAML, geração de markdown, integração com organizer).

## [0.0.3] - 2026-11-05

### Corrigido

- **src/bibliotec/core/pipeline.py**: resolvido `NameError` em `_emit` que
  impedia o envio de eventos para a CLI e congelava a barra de progresso
  visual em `'0/?'` (`total_scanned` agora é definido antes de qualquer uso
  em closures de emissão de eventos).

### Modificado

- **src/bibliotec/__init__.py**: suprimidas mensagens de terminal e barras de
  progresso do HuggingFace/PyTorch/Docling (`HF_HUB_DISABLE_PROGRESS_BARS=1`,
  `TOKENIZERS_PARALLELISM=false` e filtros de warnings do `torch`).

### Adicionado

- **tests/test_pipeline_events.py**: teste unitário/integração validando a
  propagação ponta a ponta dos eventos de pipeline com `total_files`.

## [0.0.2] - 2026-11-05

### Modificado

- **src/bibliotec/core/llm.py**: cadeia de fallback atualizada para modelos
  ativos da Google (`gemini-3.8-flash`, `gemini-3.7-flash`,
  `gemini-3.5-flash`, `gemini-3.1-flash-lite`).

### Corrigido

- **src/bibliotec/core/pipeline.py** e **src/bibliotec/cli/main.py**:
  contagem atômica thread-safe na barra de progresso da CLI com múltiplos
  workers (`completed_count` incrementado apenas ao final de cada PDF, via
  `list[int]` mutável + `threading.Lock`, garantindo `progress.advance`
  chamado exatamente 1 vez por PDF concluído).

### Removido

- **src/bibliotec/core/llm.py**: modelos legados descontinuados da Google
  (`gemini-2.5-pro`) removidos da cadeia de fallback.

## [0.0.1] - 2026-11-05

### Adicionado

- **pyproject.toml**: pacote `bibliotec`, Python >= 3.11, build hatchling,
  entrypoint `bibliotec = bibliotec.cli.main:app`, dependências de produção
  (`pymupdf`, `docling`, `httpx`, `tenacity`, `rapidfuzz`, `python-stdnum`,
  `pydantic`, `pydantic-settings`, `google-genai`, `typer`, `rich`, `tomli-w`)
  e de desenvolvimento (`pytest`, `respx`, `ruff`).
- **.gitignore**: ignora ambientes virtuais (`.venv/`), caches Python
  (`__pycache__/`, `.pytest_cache/`, `.ruff_cache/`), arquivos de sistema
  (`.DS_Store`), bancos SQLite locais (`*.db`), arquivo de configuração local
  com chaves de API (`bibliotec.toml`) e o repositório de PDFs de teste
  (`repositorio_de_pdfs_para_testes/`, ~1.1 GB).
- **README.md**: documenta instalação, configuração inicial via
  `bibliotec config init`, estrutura do `config.toml`, exemplos de uso de
  `bibliotec organize` (incluindo `--dry-run`, `--move`, `--flat`) e a
  arquitetura em 5 estágios.
- **src/bibliotec/__init__.py**: define `__version__ = "0.0.1"` e expõe a API
  pública de alto nível do pacote.
- **src/bibliotec/core/__init__.py**: exporta as entidades principais do
  domínio e o orquestrador do pipeline, mantendo a fronteira limpa entre o
  motor central (`core`) e a camada de interface (`cli`, futura `gui`).
- **src/bibliotec/core/config.py**: `AppConfig(BaseSettings)` composto pelos
  submodelos `GeneralConfig`, `LLMConfig` e `ApiKeysConfig` usando
  `pydantic-settings`, `TomlConfigSettingsSource` e `AliasChoices`
  (`BIBLIOTEC_GEMINI_API_KEY` > `GEMINI_API_KEY`, etc.) com precedência
  `init -> env -> ./bibliotec.toml -> ~/.config/bibliotec/config.toml`.
  Inclui geração de template TOML comentado com permissão `0600`
  (`os.chmod`) e mascaramento de chaves de API (`mask_key`).
- **src/bibliotec/core/models.py**: enumeradores `DocumentType`,
  `ProcessStatus`, `FileOperation` e modelos Pydantic
  `ExtractedDocument`, `ExternalMetadata`, `LLMClassificationOutput`,
  `FileManifestEntry`, `ExecutionSummary`, `PipelineEvent` conforme a Seção 3
  do design, fornecendo contratos de dados tipados e o
  `response_schema` exigido pelo Structured Outputs do Gemini.
- **src/bibliotec/core/resources/taxonomy_capes.json**: dicionário canônico
  oficial `{"version": "capes-cnpq-v1", "areas": {...}}` com as 9 Grandes
  Áreas da CAPES/CNPq e suas Áreas Básicas em português, sem barras `/`
  nos nomes. Fonte única de verdade para validação de pastas e
  `taxonomy_version` usada na chave do cache.
- **src/bibliotec/core/taxonomy.py**: `get_taxonomy_version()`,
  `get_grandes_areas()`, `get_areas_basicas()`,
  `validate_or_repair_pair(grande_area, area_basica) -> tuple[str, str] |
  None` (repara a `grande_area` pai quando a `area_basica` existe em outra
  Grande Área; retorna `None` quando ambas são inválidas) e
  `format_taxonomy_for_prompt()`.
- **src/bibliotec/core/scanner.py**: resolve `source_dir` e `target_dir`,
  rejeita `source_dir == target_dir`, exclui a subárvore de `target_dir`,
  varredura recursiva (padrão) ou plana (`--flat`), ignora ocultos e
  não-PDFs (`ignored_non_pdf`), valida a assinatura `%PDF-` nos primeiros
  1024 bytes e calcula SHA-256 em blocos de 64 KB.
- **src/bibliotec/core/cache.py**: banco SQLite em
  `~/.cache/bibliotec/state.db` em modo WAL (`PRAGMA journal_mode=WAL`) com
  tabela `processed_files` indexada por `(sha256, taxonomy_version,
  model_name)`, persistindo apenas resultados com
  `confidence_score >= confidence_min` e suportando invalidação via
  `--no-cache`. Usa `check_same_thread=False` para uso seguro em worker
  threads com `--workers > 1` (acesso serializado pelo `finalize_lock` do
  pipeline).
- **src/bibliotec/core/llm.py**: `Protocol LLMProvider` e `GeminiProvider`
  usando o SDK `google-genai` com saída estruturada
  (`response_mime_type="application/json"`,
  `response_schema=LLMClassificationOutput`), retry em HTTP 429 e 503
  (`wait_exponential`, `stop_after_attempt(4)`), cadeia de fallback de
  modelos (`gemini-3.8-flash`, `gemini-3-flash-preview`,
  `gemini-2.5-pro`) em 404 ou 503, short-circuit quando texto útil < 50
  caracteres sem metadado externo (`confidence_score = 0.0`), teto
  `min(score, 0.50)` para títulos genéricos sem autor, e validação do par
  `(grande_area, area_basica)` via `validate_or_repair_pair`.
- **bibliotec.example.toml**: modelo limpo de configuração (sem chaves
  reais) para copiar e preencher com os próprios valores do usuário.
- **CHANGELOG.md**: este arquivo, no padrão Keep a Changelog.
- **tests/test_config.py**: testes unitários para `init_config_file()`,
  leitura de `./bibliotec.toml` sem `ValidationError`, variáveis de
  ambiente diretas e `extra='ignore'` para chaves desconhecidas.
- **tests/test_namer.py**: testes unitários de formatação de nomes de
  arquivo (1, 2 e 3+ autores, ausência de subtítulo/ano, caracteres
  especiais, truncamento abaixo de 240 bytes UTF-8).
- **tests/test_taxonomy_and_identifiers.py**: testes de integridade da
  taxonomia, reparo automático de Grande Área, extração de DOI por regex,
  validação de ISBN via `python-stdnum` e detecção de Ficha Catalográfica.
- **tests/test_pipeline_integration.py**: testes de integração do pipeline
  completo (árvore temática, ignorar `.webloc`/não-PDFs, deduplicação por
  SHA-256, baixa confiança -> `revisao_manual/`, modo `--dry-run`, cache
  SQLite, PDF corrompido, execução com `workers=4`).

### Alterado

- Versão do pacote ajustada de `0.1.0` para `0.0.1` (primeira versão
  oficial, conforme diretrizes de versionamento).

### Corrigido

- `ApiKeysConfig` agora inclui o nome do próprio campo em cada
  `AliasChoices` (ex: `gemini_api_key`, `BIBLIOTEC_GEMINI_API_KEY`,
  `GEMINI_API_KEY`) para que o TOML seja lido sem `extra_forbidden`.
- `model_config = ConfigDict(populate_by_name=True, extra="ignore")`
  adicionado a `GeneralConfig`, `LLMConfig`, `ApiKeysConfig` e
  `AppConfig`.
- Removido `env_nested_delimiter="__"` do `AppConfig` para que variáveis
  de ambiente diretas (`BIBLIOTEC_GEMINI_API_KEY`) sejam lidas corretamente.
- `FilteredTomlSettingsSource` ignora strings vazias (`""`) no TOML,
  permitindo que variáveis de ambiente preencham campos deixados vazios no
  arquivo de configuração.
- `sqlite3.connect(..., check_same_thread=False)` no cache SQLite para
  evitar `ProgrammingError` com `--workers > 1`.
