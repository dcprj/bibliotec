---
name: web-design-guidelines
description: Mais de 50 diretrizes rigorosas de design de interface inspiradas nas Web Interface Guidelines da Vercel Labs adaptadas para UI desktop. Cobre alinhamento ótico, truncamento inteligente, micro-espaçamentos, prevenção de layout shifts, feedback visual instantâneo e estados vazios impecáveis.
---

# Web & Desktop Interface Guidelines (Vercel-Grade Quality)

Este documento dita os padrões inegociáveis de acabamento de layout, tipografia, contraste e ergonomia para interfaces de software profissional.

---

## 1. Regras de Espaçamento e Layout

1. **Prevenção de Truncamento Cego de Rótulos:** Nenhum botão, checkbox ou etiqueta pode ter largura fixa menor do que o comprimento intrínseco de seu texto (`sizeHint`). Rótulos como *"Recursivo"* e *"Simulação (Dry-Run)"* devem ter margem de respiro garantida.
2. **Distribuição em Camadas (Toolbar Multi-Linhas):** Agrupamentos com funções distintas não devem ser forçados na mesma linha horizontal quando o espaço for menor que 1400px.
   - Entradas de diretório e botão de ação primária residem na **Linha de Ação Principal**.
   - Parâmetros auxiliares (provedor, flags, configurações) residem na **Linha de Controle Secundário**.
3. **Alinhamento e Respiro de Campos de Caminho:** Campos de seleção de arquivo/pasta devem ter altura ergonômica mínima de `32px`, cantos com raio sutil (`4px` a `6px`), fonte monoespaçada legível (`12px`) e botão de procurar com largura confortável (`90px` a `100px`).

---

## 2. Tabelas e Exibição de Dados em Massa

1. **Modo Stretch Obrigatório no Título:** A coluna do nome do documento/obra deve sempre ser configurada com `ResizeMode.Stretch` para consumir todo o espaço horizontal livre da janela, evitando que o usuário precise rolar horizontalmente para ler os títulos.
2. **Identidade Visual Inicial na Grade:** Nenhuma linha adicionada à grade pode exibir travessões vazios (`—`) durante o processamento. Enquanto o título acadêmico não for descoberto pelo LLM, a coluna deve exibir o nome do arquivo original (`doc.source_path.name`) em peso regular ou texto secundário.
3. **Badges de Status Não-Intrusivos:**
   - Devem ter cantos arredondados contidos (`4px`), altura de `22px`, margem interna de `4px 8px`.
   - Cores de fundo dessaturadas (*tint*) com texto em contraste escuro de alta legibilidade.
   - O ícone vetorial deve ter alinhamento ótico perfeito com o centro vertical do texto.

---

## 3. Painel de Detalhes e Empty State de Estúdio

1. **Estrutura do Empty State:**
   - Um contêiner vertical centralizado com espaçamento de `12px`.
   - Ícone vetorial da biblioteca ou catálogo em tom suave (`#A1A1AA` claro / `#52525B` escuro) em `48x48px`.
   - Título descritivo em peso `600 SemiBold` (*"Nenhum documento selecionado"*).
   - Parágrafo de instrução em `12px` cor secundária (*"Selecione uma obra na grade ao lado para inspecionar a citação ABNT NBR 6023, metadados acadêmicos ou realizar triagem manual."*).
2. **Auto-Seleção Pós-Execução:**
   - Se a grade possui itens ao finalizar ou ao interromper o lote, a linha 0 deve ser automaticamente ativada (`setCurrentIndex(proxy.index(0, 0))`), eliminando a sensação de tela "morta".
