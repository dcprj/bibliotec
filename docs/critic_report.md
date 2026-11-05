# Relatório Consolidado de Revisão Crítica — Stage 7 (`critic_report.md`)

**Arquivo Alvo:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L1-L210)  
**Escopo Auditado:** `FeatureRange: 1..210`  
**Revisores:** `egm-design`, `egm-structural`, `egm-style`

---

## Resumo Executivo

* **`egm-structural`:** 0 apontamentos (todas as seções obrigatórias, hierarquia de cabeçalhos `H1 -> H2 -> H3 -> H4`, tabelas, blocos de código e diagrama Mermaid estão em conformidade com o padrão `feature-spec-standard`).
* **`egm-design`:** 5 apontamentos **Major** e 2 **Nit** focados em casos de borda reais da operação (folhas de rosto digitais em PDFs escaneados enganando o limiar global de 200 caracteres, exclusão de `TARGET_DIR` na varredura recursiva, política de cache para falhas transitórias, orçamento de tokens no `sampled_text` e preservação do nome original em `revisao_manual/`).
* **`egm-style`:** 4 apontamentos **Nit** de precisão terminológica e concisão textual.

---

## Apontamentos de Design & Arquitetura (`egm-design`)

### 1. [Major] Premissa Frágil no Gatilho Global de OCR (< 200 caracteres) Diante de PDFs Escaneados com Capa/Marca d'Água Digital
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L62-L65), [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L80-L84) (`Stage 2: Extração Seletiva de Texto e Fallback de OCR`)
* **Descrição e Recomendação:**
  * **Falha:** PDFs escaneados baixados de portais acadêmicos (JSTOR, SciELO, ResearchGate, BDTD) frequentemente possuem uma primeira página digital injetada pelo portal ou marcas d'água/rodapés selecionáveis em todas as páginas. Isso faz a soma das 15 páginas ultrapassar 200 caracteres, impedindo o acionamento do OCR nas páginas reais da obra. Além disso, reduzir a janela inicial de 10 páginas (nativo) para 5 páginas (OCR) pode perder a Ficha Catalográfica (CIP) ou o resumo em livros e teses com dedicatória/agradecimentos.
  * **Recomendação:** Avaliar a densidade textual **por página** (ex.: considerar escaneado se mais da metade das páginas inspecionadas tiver `< 30` caracteres úteis, ignorando linhas repetidas de rodapé entre páginas) e submeter ao OCR as páginas sem camada de texto dentro das **8 primeiras e 2 últimas páginas** (limitando o buffer enviado ao Docling a no máximo 8 páginas).

### 2. [Major] Risco de Reprocessamento Recursivo quando `TARGET_DIR` Está Contido em `SOURCE_DIR`
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L75-L77) (`Stage 1: Scanner`) e [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L171-L179) (`CLI Contract`)
* **Descrição e Recomendação:**
  * **Falha:** Como a varredura padrão é recursiva (`--recursive`), se o usuário indicar um `<TARGET_DIR>` dentro de `<SOURCE_DIR>` (ex.: `bibliotec organize ./acervo ./acervo/organizado`), o scanner varrerá também a pasta de saída e `revisao_manual/`.
  * **Recomendação:** Especificar no Stage 1 que o Scanner resolve os caminhos absolutos (`realpath`) de `SOURCE_DIR` e `TARGET_DIR`, rejeita execuções onde `SOURCE_DIR == TARGET_DIR` e exclui automaticamente a subárvore de `TARGET_DIR` caso ela esteja dentro de `SOURCE_DIR`.

### 3. [Major] Indefinição do Ciclo de Vida, Localização e Política de Cache para Falhas / Baixa Confiança (`state.db`)
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L61-L70), [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L78-L79) (`Stage 1: Cache de Idempotência`)
* **Descrição e Recomendação:**
  * **Falha:** (1) O caminho físico padrão de `state.db` não está fixado na especificação; (2) Se um arquivo cair em `revisao_manual/` (`confidence_score < 0.70`) devido a falha temporária de rede nas APIs externas e esse resultado for gravado no cache, novas execuções continuarão enviando-o para `revisao_manual/` sem tentar reclassificar; (3) A chave do cache não inclui o nome do modelo (`llm.model`).
  * **Recomendação:** Fixar o caminho padrão em `~/.cache/bibliotec/state.db`, compor a chave de cache com `(sha256, taxonomy_version, model_name)` e persistir no cache apenas classificações concluídas com `confidence_score >= confidence_min` (deixando arquivos de `revisao_manual/` elegíveis para nova tentativa em execuções futuras).

### 4. [Major] Ausência de Orçamento de Tokens e Limite de Payload em `sampled_text` para o Stage 4 (LLM)
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L81-L83), [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L93-L98), [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L123-L125)
* **Descrição e Recomendação:**
  * **Falha:** 15 páginas de texto denso podem somar até 75.000 caracteres por PDF sem limite explícito no prompt.
  * **Recomendação:** Definir um teto de truncamento para `sampled_text` antes do envio ao LLM (ex.: máximo de **15.000 caracteres** por documento, preservando integralmente `cip_text`, metadados nativos e as primeiras páginas).

### 5. [Major] Comportamento de Nomeação e Colisão na Pasta `revisao_manual/` Não Especificado
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L107), [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L109-L117) (`Stage 5: Materialização`)
* **Descrição e Recomendação:**
  * **Falha:** O Stage 5 não explicita se arquivos enviados para `revisao_manual/` mantêm seu nome original ou se usam o nome padronizado, e como resolver colisões quando dois arquivos de subpastas diferentes têm o mesmo nome original (ex.: `aula1/artigo.pdf` e `aula2/artigo.pdf`).
  * **Recomendação:** Explicitar que arquivos roteados para `revisao_manual/` **preservam seu nome de arquivo original**, aplicando a mesma verificação de `SHA-256` e sufixo incremental ` (2).pdf` caso haja colisão de nomes na pasta `revisao_manual/`.

### 6. [Nit] Sincronização da Materialização (Stage 5) Quando `workers > 1`
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L84-L85), [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L116)
* **Descrição e Recomendação:** Incluir o Stage 5 (verificação de colisão e cópia/movimentação no disco) na seção protegida por lock junto ao SQLite quando `workers > 1`, evitando condição de corrida (*TOCTOU*) ao gerar sufixos ` (2).pdf`.

### 7. [Nit] Precedência entre Variáveis de Ambiente e Mapeamento Completo em `config.toml`
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L134)
* **Descrição e Recomendação:** Explicitar que `BIBLIOTEC_GEMINI_API_KEY` tem precedência sobre `GEMINI_API_KEY`, e listar `BIBLIOTEC_OPENALEX_POLITE_EMAIL` para o campo `openalex_polite_email`.

---

## Apontamentos de Estilo & Precisão Editorial (`egm-style`)

### 8. [Nit] Calibração do Limite de 240 Bytes em `Goals` e `Stage 5`
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L39) e [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L113)
* **Descrição e Recomendação:** Na linha 39, substituir `"regras claras"` por `"regras determinísticas"` e mencionar já em `Goals` o truncamento em **240 bytes UTF-8** (abaixo do limite de 255 bytes do SO). Na linha 113, substituir `"para garantir que o nome final nunca exceda 240 bytes"` por `"limitando o nome final a 240 bytes"`.

### 9. [Nit] Redundância de Sinônimos no Stage 2
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L83)
* **Descrição e Recomendação:** Simplificar `"digitalizado/escaneado"` para `"escaneado"` e remover a repetição `"apenas ... exclusivamente"` na mesma frase.

### 10. [Nit] Explicitação do Valor de Timeout no Stage 3
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L91)
* **Descrição e Recomendação:** Substituir o adjetivo subjetivo `"timeout curto"` por `"timeout de 8 segundos"`.

### 11. [Nit] Padronização de Caixa do Status `duplicate_skipped`
* **Escopo Afetado:** [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L116) e [bibliotec.md](file:///Users/dario/Projetos-de-aplicativos/bibliotec/docs/designs/bibliotec.md#L126)
* **Descrição e Recomendação:** Padronizar `duplicate_skipped` em minúsculas na linha 116 (assim como `IGNORED_NON_PDF` na seção Detailed Implementation para `ignored_non_pdf`) para coincidir com a tabela de contratos da linha 126.
