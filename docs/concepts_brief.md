# Tomus: Organizador Acadêmico de PDFs

* **Author:** Dario
* **Date:** 2026-11-05

## Overview

Tomus é um aplicativo para organizar bibliotecas acadêmicas de arquivos PDF (livros, revistas científicas, artigos, teses/dissertações e outros materiais) a partir de uma pasta de entrada desorganizada para uma árvore de diretórios estruturada. O público-alvo são estudantes, pesquisadores e acadêmicos que acumulam centenas de PDFs com nomes inconsistentes, arquivos escaneados sem camada de texto e literatura sem identificadores formais (como TCCs e materiais de aula).

O sistema inicia como uma ferramenta de linha de comando (CLI) desacoplada de um motor central (`core`), preparada para receber uma interface gráfica (GUI) posteriormente. Para cada PDF válido, o aplicativo extrai o texto das páginas iniciais e finais (acionando OCR local via Docling apenas em um recorte de páginas quando o PDF é escaneado), consulta APIs acadêmicas (OpenAlex e Google Books) para validar metadados existentes, e utiliza um modelo de linguagem externo (Gemini API por padrão, com suporte a outros provedores via chave de API do usuário) restrito a um esquema estruturado para classificar o documento na Tabela de Áreas do Conhecimento da CAPES/CNPq nos níveis `<assunto>/<especificidade>/<tipo>`, padronizando também o nome do arquivo final.

## Analysis

A revisão multi-lente sobre a hipótese de trabalho e sobre o conjunto real de testes (`repositorio_de_pdfs_para_testes`, contendo ~115 arquivos e ~1,1 GB) identificou seis pontos críticos que moldam a arquitetura:

1. **Deriva de Taxonomia dentro da Tabela CAPES/CNPq (`egm-design`):**
   A tabela oficial da CAPES/CNPq possui quatro níveis hierárquicos (Grande Área, Área Básica, Subárea e Especialidade). Para evitar pulverização de pastas e deriva de nomes, o sistema mapeia `<assunto>` para a **Grande Área** (ex.: `Ciências Humanas`, `Ciências Sociais Aplicadas`) e `<especificidade>` para a **Área Básica** (ex.: `Psicologia`, `Comunicação`, `Administração`), carregando um dicionário canônico local (`taxonomy_capes.json`) com os pares válidos e validando a saída do LLM contra essa lista fechada via esquema tipado (Pydantic).
2. **Custo de Memória e Tempo do Docling em PDFs Grandes (`egm-codebase-details`):**
   A pasta de testes inclui livros escaneados de até 34 MB. Enviar um PDF escaneado de 300 páginas inteiro para o Docling causa alto consumo de memória e leva minutos por arquivo. O extrator deve primeiro inspecionar o PDF com uma biblioteca leve (`PyMuPDF`), extrair texto nativo das 10 primeiras e 5 últimas páginas (onde ficam capa, folha de rosto, sumário, ficha catalográfica ABNT/CIP e colofão) e, somente se a densidade de texto for insuficiente (menos de 200 caracteres úteis no total), recortar as 5 primeiras e 2 últimas páginas em memória para enviá-las ao OCR do Docling.
3. **Falsos Positivos em Buscas por Título no OpenAlex e Google Books (`egm-implementation-readiness`):**
   Quando o PDF possui DOI ou ISBN válido (verificado por dígito verificador), a consulta ao OpenAlex ou Google Books retorna o registro exato. Porém, em TCCs, slides de aula ou apostilas sem DOI/ISBN, buscar apenas pelo título extraído frequentemente retorna obras homônimas incorretas. O enriquecimento externo só deve aceitar resultados buscados por título/autor quando a similaridade textual (ex.: `rapidfuzz`) entre o título extraído do PDF e o título retornado pela API atingir um limiar mínimo; caso contrário, a classificação deve basear-se apenas no texto extraído do próprio PDF (incluindo a Ficha Catalográfica, quando presente).
4. **Regras de Formatação de Nomes de Arquivo e Limite de 255 Bytes (`egm-comprehension`):**
   O padrão `<autor> - <titulo> - <subtitulo se houver> - <ano>.pdf` falha se não houver regras determinísticas para casos comuns na literatura acadêmica:
   * **Múltiplos autores:** Documentos com muitos coautores geram nomes longos demais. A regra deve padronizar 1 autor como `Sobrenome, Nome`, 2 autores como `Sobrenome1; Sobrenome2` e 3 ou mais como `Sobrenome1 et al.`.
   * **Campos ausentes:** Se não houver subtítulo, o separador correspondente deve ser omitido (`<autor> - <titulo> - <ano>.pdf`). Se o ano não for identificado, usar `s.d.`.
   * **Limite do sistema de arquivos:** No macOS (APFS) e Linux, cada nome de arquivo tem limite estrito de 255 bytes em UTF-8 (caracteres acentuados ocupam mais de 1 byte). O formatador deve remover caracteres ilegais (`/ : \ ? * " < > |`) e truncar primeiro o subtítulo e depois o título para garantir que o nome final nunca ultrapasse 240 bytes.
   * **Colisões:** Se dois arquivos distintos gerarem o mesmo nome no destino, verificar o hash SHA-256; se o conteúdo for idêntico, registrar como duplicata e não sobrescrever; se o conteúdo for diferente, acrescentar sufixo incremental ` (2).pdf`.
5. **Calibração da Meta de 80% de Acerto vs. Pasta `revisao_manual` (`egm-zoom-out`):**
   Excluir irrestritamente os arquivos de `revisao_manual` do cálculo de acerto permite que o sistema atinja 100% de precisão aparente enviando quase todos os arquivos duvidosos para revisão manual. A métrica de sucesso deve exigir: (a) precisão mínima de 80% sobre os arquivos classificados automaticamente e (b) teto máximo de arquivos válidos enviados para `revisao_manual` (ex.: máximo de 15% a 20% do lote), acompanhado de um manifesto explicando o motivo de cada envio para revisão.
6. **Idempotência, Cache por Hash e Separação Core/CLI (`egm-structural`):**
   Processar centenas de PDFs envolve chamadas de rede e OCR. Para evitar retrabalho e gasto duplicado de tokens quando uma execução é interrompida ou repetida, o sistema deve manter um cache local SQLite indexado pelo hash SHA-256 do arquivo. Além disso, toda a lógica de extração, enriquecimento, classificação e movimentação deve residir em um pacote `core` independente de interface, emitindo eventos estruturados que hoje alimentam a CLI e futuramente alimentarão a GUI.

## Goals vs. Non-Goals

* **In-Scope Goals:**
  * Ler recursivamente ou linearmente uma pasta de origem, validar arquivos PDF reais (extensão `.pdf` e cabeçalho `%PDF-`) e ignorar outros formatos (como `.webloc` e `.DS_Store`).
  * Extrair texto nativo das páginas iniciais e finais com detecção prioritária de Ficha Catalográfica (CIP/CDD/CDU) e acionar OCR local via Docling apenas em subconjunto de páginas quando o PDF for escaneado.
  * Extrair DOI/ISBN e consultar OpenAlex e Google Books com timeout, retry e validação de similaridade textual para evitar falsos positivos.
  * Classificar cada PDF usando LLM via interface plugável (implementação inicial com Gemini API via Structured Outputs) dentro da taxonomia fechada CAPES/CNPq (`<assunto>/<especificidade>/<tipo>`, onde `<tipo>` é `Livro`, `Revista Científica`, `Artigo`, `Tese_Dissertacao` ou `Outros`).
  * Copiar os arquivos por padrão (ou mover, mediante parâmetro explícito) para a pasta de destino, renomeando-os para `<autor> - <titulo> - <subtitulo> - <ano>.pdf` dentro do limite de 240 bytes em UTF-8.
  * Enviar arquivos com baixa confiança para a pasta `revisao_manual/` junto com um relatório/manifesto auditável (`manifest.json` / `relatorio.csv`) e suportar modo de simulação (`--dry-run`).
  * Atingir no mínimo 80% de acerto na classificação dos PDFs válidos da pasta `repositorio_de_pdfs_para_testes`.
* **Out-of-Scope Non-Goals:**
  * Construção da interface gráfica (GUI) nesta primeira fase (o foco inicial é validar o motor e a barreira de classificação via CLI).
  * OCR de livros escaneados inteiros (página por página do início ao fim) ou indexação de busca de texto completo (full-text search) do conteúdo integral das obras.
  * Gerenciamento de citações em processadores de texto (Word/LaTeX) ou sincronização em nuvem proprietária ao estilo Zotero/Mendeley.
  * Edição ou regravação dos metadados internos binários (XMP/Info dict) dentro do arquivo PDF original.

## Alternatives Weighed

* **Zotero (com plugins ZotMoov/Attanger) ou Calibre:** Rejected by author: Embora extraiam metadados bibliográficos de artigos e livros, exigem manter um banco de dados próprio de gerenciador de referências e não classificam automaticamente os arquivos em uma árvore física estrita de Assunto/Especificidade/Tipo baseada na taxonomia acadêmica brasileira.
* **`llama-fs`:** Rejected by author: Gera árvores de diretórios dinamicamente via LLM a cada execução, provocando deriva de categorias (pastas inconsistentes a cada lote), não diferencia tipos acadêmicos com rigor e falha em PDFs escaneados sem camada de texto.
* **`organize-tool` (regras determinísticas em YAML):** Rejected by author: Opera apenas com regras fixas de metadados ou expressões regulares, sendo incapaz de inferir assunto e especificidade semântica de livros, artigos e teses sem que o próprio motor de classificação seja construído por fora.
* **Executar Docling OCR no PDF completo:** Rejected by author: Processar centenas de páginas escaneadas por arquivo inviabiliza o tempo de execução e o consumo de memória RAM quando apenas as páginas iniciais e finais contêm os metadados necessários para classificação.

## Key Decisions & Staging for Next Steps

1. **Mapeamento dos 2 níveis temáticos da CAPES/CNPq (Resolvido):** `<assunto>` corresponde à **Grande Área** da tabela CAPES/CNPq (9 categorias amplas, ex.: `Ciências Humanas`, `Ciências Sociais Aplicadas`) e `<especificidade>` corresponde à **Área Básica** oficial vinculada (ex.: `Psicologia`, `Comunicação`, `Administração`), validadas contra catálogo fechado.
2. **Validação de APIs Acadêmicas e Ficha Catalográfica (Resolvido):** Consultas ao OpenAlex e Google Books são aceitas mediante match exato de DOI/ISBN ou alta similaridade textual de título + autor (`rapidfuzz`). O extrator prioriza a detecção de Ficha Catalográfica (CIP/ABNT) nas 10 primeiras e 5 últimas páginas do PDF.
3. **Regras de desempate para `<tipo>` (Resolvido):** Os valores permitidos são `Livro`, `Revista Científica` (fascículo/edição completa), `Artigo` (artigo individual), `Tese_Dissertacao` (incluindo TCCs, monografias, dissertações e teses) e `Outros` (slides de aula, apostilas e relatórios).
4. **Política de renomeação, truncamento e múltiplos autores (Resolvido):** Padrão `<autor> - <titulo> - <subtitulo> - <ano>.pdf`, com `Sobrenome, Nome` (1 autor), `Sobrenome1; Sobrenome2` (2 autores) e `Sobrenome1 et al.` (3+ autores); omissão do separador quando não houver subtítulo; uso de `s.d.` quando o ano for desconhecido; e truncamento seguro em até 240 bytes UTF-8.
5. **Critério de sucesso e teto de `revisao_manual` (Resolvido):** Mínimo de 80% de acerto na classificação dos PDFs válidos da pasta `repositorio_de_pdfs_para_testes`, com teto máximo de 15% a 20% dos PDFs válidos enviados para `revisao_manual`.