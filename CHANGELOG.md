# Changelog do BiblioTEC

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adota versionamento semântico ([Semantic Versioning](https://semver.org/lang/pt-BR/)).

## [0.2.0] - 2026-11-06

### Entregas da Sprint v0.2.0

#### [FAL-04] Múltiplos provedores LLM com fallback automático (`src/bibliotec/core/llm.py`)
* `FallbackLLMDispatcher`: implementa o protocolo `LLMProvider` com cadeia ordenada de provedores.
  Tenta o primário; em caso de exceção ou resultado com reasoning 'Falha na chamada ao LLM',
  loga warning no logger `bibliotec.llm` e despacha para o próximo da cadeia.
* `create_provider_chain()`: fábrica que monta a cadeia a partir da `AppConfig` e flags CLI.
  Suporta provedores: `gemini`, `nvidia`, `deepseek`, `claude`.
  Resolução de chave: CLI > variável de ambiente > config.toml.
  Se o provedor primário não tiver chave, o primeiro com chave válida torna-se primário efetivo.
* Novos provedores: `DeepSeekProvider` (API DeepSeek /chat/completions) e
  `ClaudeProvider` (API Anthropic /messages), ambos com retry em 429/503/529 e
  travas determinísticas de confiança idênticas aos demais provedores.

#### [CLI-04] Novos provedores na CLI e `config show` expandido (`src/bibliotec/cli/main.py`)
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

#### [LOG-01] Sistema de Logs Profissional (`src/bibliotec/core/logging.py`)
* Configuração de logging estruturado que redireciona logs detalhados para arquivo
  (`bibliotec.log`), mantendo o terminal 100% limpo para a barra de progresso do Rich.
* `setup_logging(verbose=verbose)`: quando `verbose=True`, anexa um StreamHandler ao console;
  caso contrário, apenas o arquivo de log recebe as mensagens.
* Silenciamento defensivo de loggers de terceiros (RapidOCR, docling, transformers, torch,
  urllib3, httpx, fitz) e variáveis de ambiente (GLOG_minloglevel, TORCH_CPP_LOG_LEVEL,
  TOKENIZERS_PARALLELISM, HF_HUB_DISABLE_PROGRESS_BARS).

#### [RES-02] Persistência de Sessão para Retomada (`src/bibliotec/core/session.py`)
* `SessionState` (Pydantic BaseModel): serializa estado de execução (source_dir, target_dir,
  recursive, move, dry_run, provider, model, confidence_min, workers, no_cache, created_at).
* `save_session(state)`: grava o estado em `.bibliotec_session.json`.
* `load_session()`: carrega o estado salvo, retornando None se o arquivo não existir ou
  estiver corrompido.
* `clear_session()`: remove o arquivo de sessão com tolerância a arquivo ausente.
* Novo comando CLI `./bibliotec resume` para retomada automática da execução interrompida.

#### [LLM-03] Provedor NVIDIA NIM (`src/bibliotec/core/llm.py`)
* `NvidiaProvider`: chama a API NVIDIA NIM em `POST /chat/completions` via httpx, com retry
  em 429/503, strip de blocos markdown JSON e travas determinísticas de confiança idênticas
  às do GeminiProvider (short-circuit < 50 chars, teto 0.50 para título genérico).
* Modelo padrão: `meta/llama-3.2-90b-vision-instruct`.
* Resolução de chave: flag CLI `--api-key` > env `BIBLIOTEC_NVIDIA_API_KEY` / `NVIDIA_API_KEY`
  > config `nvidia_api_key`.

#### [CLI-04] Integração CLI + Pipeline para release v0.1.0 (`src/bibliotec/cli/main.py`)
* Novas flags globais: `--verbose` / `-v` e `--provider` / `-p` (gemini ou nvidia).
* `setup_logging(verbose=verbose)` chamado no início de `_executar_organize`.
* `_build_provider` agora aceita parâmetro `provider`; suporte a NVIDIA com resolução de chave
  e erro amigável quando ausente.
* Sessão e Retomada: `save_session(SessionState(...))` no início de `_executar_organize`;
  `clear_session()` após conclusão bem-sucedida.
* Subcomando `organize` ocultado do `--help` raiz (`hidden=True`).
* Comando `bibliotec resume` adicionado.
* Barra de progresso Rich reescrita com `rich.console.Group` + `rich.live.Live`:
  barra consolidada no topo e linha de status do arquivo abaixo.
* Comando `bibliotec cache` com subcomandos `clean`/`clear`, `status` e `path`.
* Remoção do resquício `progress.update(task, description="Concluído")` do bloco `finally`.
* Bump de versão para **0.1.0** em `pyproject.toml` e `src/bibliotec/__init__.py`.

---

## [0.0.6] - 2026-11-04

### Adicionado
* **Arquivo companheiro (.md)**: `src/bibliotec/storage/companion.py` com funções
  `format_abnt_author`, `format_abnt_authors`, `format_abnt_reference`,
  `generate_companion_markdown` e `generate_duplicate_companion_markdown`.
* **Gerenciamento de duplicatas**: `LibraryOrganizer` encaminha duplicatas para
  `target_dir/duplicatas/` com resolução de colisão de nomes, `.md` companheiro e
  suporte a `move` (limpa a origem) e `copy`.
* **Comando `bibliotec cache`**: subcomandos `clean`/`clear`, `status` e `path` para
  gerenciar o banco SQLite `~/.cache/bibliotec/state.db`.
* **Barra de progresso Rich**: reescrita com `Group(prog_bar, status_prog)` e `Live`,
  com barra consolidada no topo e linha de status do arquivo abaixo.

### Alterado
* `src/bibliotec/storage/organizer.py`: integração do arquivo companheiro na etapa
  `add_organized` (quando `status == ORGANIZED` e não `dry_run`).

---

## [0.0.5] - 2026-11-03

### Corrigido
* **Modelo Gemini**: padrão atualizado para `gemini-3.8-flash` em `config.py`, `llm.py`
  e `bibliotec.toml`.
* **Fallback inteligente**: `GeminiProvider._call_gemini` tenta cadeia de modelos
  (`gemini-3.8-flash`, `gemini-3.7-flash`, `gemini-3.5-flash`, `gemini-3.1-flash-lite`)
  quando o modelo atual retorna HTTP 404 NOT_FOUND.
* **Poluição do cache SQLite**: `FileCache` aceita `db_path`; nunca lê/grava resultados
  com `reasoning == 'mock'` no cache real (~/.cache/bibliotec/state.db); 113 entradas
  mock removidas; testes usam `db_path=tmp_path/'state.db'`.
* **CLI sem chave**: levanta erro amigável + `typer.Exit(1)` em vez de usar
  `MockLLMProvider` silenciosamente.
* **Colisão de nomes em `--dry-run`**: `LibraryOrganizer._planned_destinations`
  detecta colisões contra arquivos planejados na mesma execução, funcionando em
  modo dry-run.
* **Ambiente virtual Python 3.12**: `.venv` criado na raiz; `./bibliotec` re-executa
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
* **Ergonomia da CLI**: `bibliotec -o <origem> -d <destino> [--dry-run]` executa o
  organize automaticamente sem precisar do subcomando.
* **Opções curtas**: `--origem/-o/--source` e `--destino/-d/--target` tanto no callback
  raiz quanto no subcomando `organize`.
* **Script executável `./bibliotec`**: adiciona `src/` ao `sys.path` automaticamente e
  chama `bibliotec.cli.main:main`; usa `.venv/bin/python` se existir.
* **Testes de ergonomia**: `tests/test_cli_ergonomia.py` com `typer.testing.CliRunner`
  cobrindo `-o/-d`, `--origem/--destino`, posições, opções source/target, precedência
  e casos de erro.

### Alterado
* `src/bibliotec/cli/main.py`: refatorado para extrair lógica comum em
  `_executar_organize`, evitando duplicação entre callback raiz e `organize`.

---

## [0.0.3] - 2026-11-01

### Adicionado (Itens 17 a 27 — Fase 2/3)
* **`src/bibliotec/core/prompts.py`**: prompt de sistema e payload contextual com
  truncamento de `sampled_text` a 15.000 caracteres priorizando `cip_text`; regras dos
  5 tipos documentais; autores no formato `'Sobrenome, Nome'`; catálogo fechado via
  `format_taxonomy_for_prompt`.
* **`src/bibliotec/core/llm.py`**: `Protocol LLMProvider`; short-circuit < 50 chars
  sem metadado externo (`confidence_score = 0.0`); `GeminiProvider` com
  `google-genai` (`response_mime_type='application/json'`,
  `response_schema=LLMClassificationOutput`); retry em HTTP 429; validação via
  `validate_or_repair_pair` forçando `confidence_score = 0.0` se retornar `None`;
  teto `min(score, 0.50)` quando título for vazio/genérico sem autor.
* **`src/bibliotec/storage/__init__.py`**: exporta `format_academic_filename` e
  `LibraryOrganizer`.
* **`src/bibliotec/storage/namer.py`**: `<autor> - <titulo> - <subtitulo> - <ano>.pdf`
  com 1/2/3+ autores; omissão de subtítulo vazio; `s.d.` quando `year` for `None`;
  normalização Unicode NFC; sanitização de proibidos; truncamento progressivo em
  fronteira de palavra garantindo ≤ 240 bytes UTF-8.
* **`src/bibliotec/storage/organizer.py`**: árvore temática
  `<Grande Área>/<Área Básica>/<Tipo>/<nome>.pdf`; `revisao_manual/` preservando nome
  original; `shutil.copy2` ou move seguro; `dry_run` sem pastas temáticas nem cópias;
  colisão por SHA-256 (`duplicate_skipped` ou sufixo ` (2).pdf`); gravação de
  `manifest.json` e `revisao_manual/relatorio_revisao.md`.
* **`src/bibliotec/core/pipeline.py`**: orquestrador de 5 estágios
  (scan → cache → extrator → enriquecer → LLM → organizador); `workers=1` padrão ou
  rede paralela com lock no OCR + finalização; `ExecutionSummary` com teto de 20%
  para `revisao_manual/`; emissão de `PipelineEvent`.
* **`src/bibliotec/cli/__init__.py`** e **`src/bibliotec/cli/main.py`**: Typer+Rich
  com comandos `organize`, `config init [--local]`, `config show`, `config path`.
* **Testes**: `tests/test_namer.py`, `tests/test_taxonomy_and_identifiers.py`,
  `tests/test_pipeline_integration.py` (31 testes não-slow).

### Alterado
* `src/bibliotec/core/__init__.py`: exporta novos módulos (prompts, llm).

---

## [0.0.2] - 2026-10-29

### Adicionado (Itens 12 a 16 — Fase 1, implementados pelo agente Lince)
* **`src/bibliotec/extractors/__init__.py`**: `extract_document_content(path, sha256)`.
* **`src/bibliotec/extractors/identifiers.py`**: extração de DOI por regex estrita,
  ISBN validado via `python-stdnum`, detecção de Ficha Catalográfica CIP.
* **`src/bibliotec/extractors/native_pdf.py`**: extração nativa via PyMuPDF das 10
  primeiras e 5 últimas páginas; decisão de necessidade de OCR.
* **`src/bibliotec/extractors/ocr_docling.py`**: fallback de OCR seletivo via Docling
  com recorte de páginas sem texto (máximo 8 páginas).
* **`src/bibliotec/core/enrichers.py`**: consultas HTTP para OpenAlex e Google Books
  com `httpx` + `tenacity` (retry 3 tentativas, timeout 8s); validação de similaridade
  `rapidfuzz.fuzz.token_set_ratio >= 88.0`.

---

## [0.0.1] - 2026-10-27

### Adicionado (Fase 1 — Itens 1 a 11)
* **`pyproject.toml`**: metadados do pacote, dependências, ponto de entrada
  `bibliotec = "bibliotec.cli.main:app"`.
* **`src/bibliotec/__init__.py`**: `__version__ = "0.1.0"`.
* **`src/bibliotec/core/__init__.py`**: exporta entidades de domínio.
* **`src/bibliotec/core/config.py`**: `AppConfig` com `pydantic-settings`, fontes TOML
  aninhadas, ordem de precedência (CLI > env > local TOML > global TOML), geração de
  template TOML com permissão `0600`.
* **`src/bibliotec/core/models.py`**: enums (`DocumentType`, `ProcessStatus`,
  `FileOperation`) e modelos Pydantic (`ExtractedDocument`, `ExternalMetadata`,
  `LLMClassificationOutput`, `FileManifestEntry`, `ExecutionSummary`, `PipelineEvent`).
* **`src/bibliotec/core/resources/taxonomy_capes.json`**: 9 Grandes Áreas e Áreas
  Básicas da CAPES/CNPq.
* **`src/bibliotec/core/taxonomy.py`**: carregamento da taxonomia,
  `validate_or_repair_pair`, `format_taxonomy_for_prompt`.
* **`src/bibliotec/core/scanner.py`**: varredura recursiva/plana, validação de
  assinatura `%PDF-`, SHA-256, exclusão da subárvore do destino.
* **`src/bibliotec/core/cache.py`**: cache SQLite em `~/.cache/bibliotec/state.db`
  (modo WAL), persistência apenas de classificações aprovadas.
* **`.gitignore`**: ignora ambientes virtuais, caches, chaves de API, bancos SQLite.
* **`README.md`**: documentação de instalação, configuração e uso.
