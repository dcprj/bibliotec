# BiblioTEC: Organizador Acadêmico de PDFs

O BiblioTEC automatiza a triagem, classificação temática, padronização de nomes e organização física de bibliotecas acadêmicas de PDFs com base na tabela de áreas do conhecimento da CAPES/CNPq.

Estrutura de destino:

```
<Grande Área>/<Área Básica>/<Tipo>/<autor> - <titulo> - <subtitulo> - <ano>.pdf
```

Onde `<Tipo>` pertence ao conjunto fechado `{Livro, Revista Científica, Artigo, Tese_Dissertacao, Outros}`.

## Instalação

```bash
pip install .
```

Ou, para desenvolvimento:

```bash
pip install -e ".[dev]"
```

## Configuração inicial

Gere o arquivo de configuração global (com permissão `0600`):

```bash
bibliotec config init
```

Ou gere um arquivo local no diretório corrente:

```bash
bibliotec config init --local
```

Edite `~/.config/bibliotec/config.toml` (ou `./bibliotec.toml`) e preencha as chaves de API:

```toml
[api_keys]
gemini_api_key = "SUA_CHAVE_GEMINI"
google_books_api_key = ""
openalex_polite_email = "seu@email.com"
```

A ordem de precedência é: flags da CLI > variáveis de ambiente (`BIBLIOTEC_GEMINI_API_KEY` > `GEMINI_API_KEY`, etc.) > `./bibliotec.toml` > `~/.config/bibliotec/config.toml`.

## Uso

### Organizar uma biblioteca

```bash
bibliotec organize <SOURCE_DIR> <TARGET_DIR>
```

Opções de `bibliotec organize`:

| Opção | Descrição |
|-------|-----------|
| `--config PATH` | Caminho para um config.toml customizado |
| `--recursive / --flat` | Varre subpastas recursivamente (padrão) ou apenas nível raiz |
| `--move / --copy` | Mover arquivos em vez de copiar (padrão: `--copy`) |
| `--dry-run` | Extrai e classifica sem copiar/mover, grava apenas o manifesto |
| `--model TEXT` | Modelo Gemini (sobrescreve o config.toml) |
| `--api-key TEXT` | Chave de API do Gemini (sobrescreve config e env) |
| `--google-books-key TEXT` | Chave de API do Google Books |
| `--confidence-min FLOAT` | Limiar mínimo para organização automática (padrão: 0.70) |
| `--no-cache` | Ignora o cache SQLite local |
| `--workers INT` | Concorrência para chamadas de rede (padrão: 1) |

Exemplos:

```bash
# Execução padrão: cópia, recursiva, com cache
bibliotec organize ~/Downloads/pdfs ~/Biblioteca

# Modo simulação: não move nem copia nada
bibliotec organize ~/Downloads/pdfs ~/Biblioteca --dry-run

# Modo plano e move
bibliotec organize ~/Downloads/pdfs ~/Biblioteca --flat --move

# Sem cache
bibliotec organize ~/Downloads/pdfs ~/Biblioteca --no-cache
```

### Comandos de configuração

```bash
bibliotec config init [--local]
bibliotec config show
bibliotec config path
```

## Arquitetura (5 estágios)

1. **Scanner:** Valida a assinatura `%PDF-`, calcula SHA-256, ignora não-PDFs e exclui a subárvore do destino.
2. **Extrator:** Lê texto das 10 primeiras e 5 últimas páginas; aplica OCR seletivo via Docling quando necessário.
3. **Enriquecimento:** Consulta OpenAlex e Google Books por DOI/ISBN/título-autor.
4. **Classificação LLM:** Classifica via Gemini com saída estruturada, validada contra o catálogo fechado CAPES/CNPq.
5. **Materialização:** Renomeia, copia/move para a árvore temática e grava `manifest.json` e `revisao_manual/relatorio_revisao.md`.

Documentos com confiança `< 0.70` são encaminhados para `revisao_manual/`.

## Taxonomia

O catálogo oficial das 9 Grandes Áreas e suas Áreas Básicas da CAPES/CNPq fica em `src/bibliotec/core/resources/taxonomy_capes.json`.

## Licença

Projeto privado.
