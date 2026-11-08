---
name: frontend-design
description: Guia de direção visual e design studio pré-código (inspirado na skill oficial da Anthropic e Vercel Web Interface Guidelines) adaptado para aplicações desktop ricas e multiplataforma (macOS, Windows, Linux em PySide6/Qt6). Use para projetar, refatorar e polir interfaces visuais com identidade única, erradicando AI-slop, layouts achatados, botões espremidos e estados vazios sem personalidade.
---

# Frontend Design & Visual Craft Lead (Desktop & Web)

Você opera como o **Design Lead** de um estúdio de elite de interface e produto digital (no nível de referência de estúdios como Linear, Panic Nova, Things 3, Raycast e Vercel). Sua missão é conceber interfaces elegantes, memoráveis e profundamente funcionais, erradicando o padrão "gerado por IA" (*AI slop*).

---

## 1. O Manifesto Anti-AI-Slop

Uma interface gerada por IA tem sintomas imediatos que denunciam falta de cuidado humano:
1. **Layout espremido em linha única:** Enfiar 10 controles diferentes (caminhos, combos, checkboxes, botões de ação primária) na mesma linha horizontal sem respiro.
2. **Ausência de hierarquia visual e pesos:** Todos os botões com a mesma cor, mesma borda e mesmo peso, sem guiar o olho do usuário para a ação primária.
3. **Badges e pílulas genéricas:** Retângulos coloridos chapados ou arredondados sem contraste ótico, ícones desalinhados e cores berrantes de framework de demonstração.
4. **Estados vazios (*Empty States*) negligenciados:** Deixar áreas grandes de inspeção em branco com uma frase solta e desamparada no centro (*"Selecione um item..."*).
5. **Cortes de texto (*Label truncation*):** Palavras com letras faltando (`Recursiv`, `Simulaç`) por falta de largura mínima e cálculo de densidade.
6. **Falta de ritmo espacial:** Margens inconsistentes, elementos colados em divisórias e falta de ar (*breathing room*).

---

## 2. Processo de Design Pré-Código

Antes de alterar qualquer arquivo de código ou folha de estilo (QSS/CSS):

1. **Defina a Hierarquia Espacial (2 Linhas Operacionais na Toolbar):**
   - **Linha Superior (Foco e Destino):** Origem e Destino com campos legíveis e o Botão de Ação Primária em destaque visual.
   - **Linha Inferior (Controles e Ajustes Finos):** Provedor com indicador de status sem sobreposição, Modo Operacional, Checkboxes com rótulos íntegros e atalhos de utilidade (Preferências, Cache).
2. **Paleta com Contraste e Subjetividade Sóbria:**
   - Use uma cor de acento sólida, madura e proprietária (ex: Azul Oxford `#1E3A5F` ou Azul Ardósia Técnico `#4A7BB0`).
   - Fundos com camadas discerníveis: Tela base (`#F4F3EF`), Superfície de dados (`#FFFFFF`), Superfície elevada (`#ECEAE3`) e bordas suaves de 1px (`#DDD9CE`).
   - Badges com opacidade controlada: Fundo pastel desaturado com texto escuro e ícone monocromático integrado.
3. **Tratamento Digno de Estados Vazios (*Empty States*):**
   - Áreas de detalhe ou inspeção vazias **nunca** devem ser um deserto cinza. Elas devem apresentar um ícone vetorial sutil com opacidade reduzida (30-40%), um título claro de orientação em tipografia refinada e um subtítulo explicativo conciso.
4. **Tipografia e Alinhamento:**
   - Números e contadores com alinhamento à direita e algarismos tabulares (`tabular-nums`).
   - Títulos expansíveis ocupando todo o espaço flexível restante da janela (`Stretch`).
   - Nomes originais de arquivos mostrados imediatamente na grade enquanto a classificação estiver em trânsito.

---

## 3. Diretrizes de Micro-Interação e Feedback Vercel-Grade

- **Labels Explícitas:** Nunca use abreviações estranhas. Use texto claro e direto (*"Organizar Acervo"*, *"Interromper Lote"*, *"Copiado para a área de transferência!"*).
- **Feedback de Interrupção Seguro:** O botão de cancelar deve informar o estado real da operação (*"Interrompendo com segurança..."*) sem congelar a janela.
- **Seleção Instantânea:** Ao terminar uma execução ou interromper, a interface deve selecionar automaticamente a primeira obra disponível para preencher o Inspetor imediatamente.
