---
name: desktop-ui-craft
description: >-
  Diretrizes de UX/UI de estúdio para aplicações desktop utilitárias e acadêmicas
  (macOS, Windows e Linux) com rigor anti-IA (Anti-AI-Slop). Use sempre que for
  projetar, especificar, estilizar ou revisar a interface gráfica (GUI) do BiblioTEC.
---

# Desktop UI Craft & Anti-AI-Slop Design System

Esta skill define o padrão de design de interfaces desktop para o **BiblioTEC**, garantindo uma estética autoral, funcional, editorial e livre de clichês visuais gerados por IA ("AI slop"), com ergonomia nativa no **macOS** e portabilidade limpa para **Windows** e **Linux**.

---

## 1. Calibração Anti-AI-Slop (O que é ESTRITAMENTE PROIBIDO)

Interfaces geradas por IA sofrem de convergência distribucional e parecem "templates genéricos de SaaS". Ao projetar ou implementar a GUI do BiblioTEC, **NUNCA** utilize:

1. **Gradientes Neon / Roxo-Rosa ("AI Glow"):** Proibido usar fundos ou botões com gradientes `purple-to-pink`, `indigo-to-cyan` ou sombras brilhantes coloridas.
2. **Emojis Crus como Ícones de Interface:** Nunca use emojis (`📂`, `🚀`, `✨`, `⚙️`, `✅`) em botões, abas, árvore de diretórios ou barras laterais. Utilize exclusivamente ícones vetoriais monocromáticos consistentes (traço uniforme de `1.5px` ou `1.75px`, estilo Lucide / SF Symbols / Phosphor) ou símbolos tipográficos geométricos limpos.
3. **Síndrome de Landing Page ("SaaS Hero"):** Aplicativos desktop utilitários não têm "Hero Section" centralizada com frases promocionais, subtítulos em caixa-alta espaçada (*tracked-out ALL-CAPS eyebrows*) ou cartões arredondados gigantes (`border-radius > 12px`) flutuando no vazio.
4. **Baixa Densidade de Informação:** Não desperdice a área útil da janela desktop com paddings exagerados (`32px+` dentro de tabelas/listas). Pesquisadores lidam com centenas de títulos longos, autores e áreas CAPES/CNPq; a tabela/árvore de documentos deve priorizar legibilidade e alta densidade informacional.
5. ** Botões com Setas Forçadas (`→`) ou Pílulas Decorativas Aleatórias:** Use badges semânticos discretos apenas para estados reais do pipeline (`Organizado`, `Revisão Manual`, `Duplicata`, `Cache Hit`, `OCR`).

---

## 2. Identidade Visual do BiblioTEC: "Editorial Academic Workbench"

Inspirada em ferramentas de precisão como **Zotero 7**, **Things 3**, **Linear** e **Panic Nova**:

* **Conceito:** Uma bancada de catalogação acadêmica silenciosa, precisa e tátil. A interface deve transmitir a sobriedade de uma biblioteca universitária e a eficiência de uma ferramenta de engenharia.
* **Paleta de Cores Intencional (Papel & Tinta Acadêmica / Grafite Técnico):**
  * **Modo Claro (Editorial Paper):**
    * Superfície Base (Janela/Sidebar): `#F6F5F1` (Alabastro quente sutil, descansa a vista na leitura de metadados)
    * Superfície Principal (Área de Dados/Tabela): `#FFFFFF`
    * Superfície Elevada / Hover: `#EFECE6`
    * Bordas de Divisão (Hairline `1px`): `#E2DFD7`
    * Texto Primário (Tinta): `#18181B`
    * Texto Secundário / Metadados: `#52525B`
    * Acento Primário (Azul Oxford / Acadêmico): `#1E3A5F` (hover `#162B47`)
  * **Modo Escuro (Technical Graphite):**
    * Superfície Base (Sidebar): `#141517`
    * Superfície Principal (Área de Dados): `#1B1C1F`
    * Superfície Elevada / Input: `#232529`
    * Bordas de Divisão (Hairline `1px`): `#2E3036`
    * Texto Primário: `#F4F4F6`
    * Texto Secundário: `#9CA3AF`
    * Acento Primário (Azul Ardósia Luminoso): `#4A7BB0`
  * **Cores Semânticas de Status (Sóbrias):**
    * `Organizado`: Verde Botânico (`#15803D` claro / `#4ADE80` escuro)
    * `Revisão Manual`: Âmbar Editorial (`#B45309` claro / `#FBBF24` escuro)
    * `Duplicata`: Azul Petróleo (`#0369A1` claro / `#38BDF8` escuro)
    * `Erro`: Carmim (`#B91C1C` claro / `#F87171` escuro)

* **Tipografia e Hierarquia:**
  * **UI & Tabelas:** Fonte sans-serif nativa de alta legibilidade multiplataforma (`SF Pro Text` no macOS, `Segoe UI Variable` no Windows, `Inter` / `Cantarell` no Linux) com `tabular-nums` para contadores, anos, porcentagens e scores de confiança.
  * **Caminhos de Arquivo, Hashes SHA-256 e Logs:** Fonte monoespaçada técnica (`SF Mono`, `JetBrains Mono`, `Cascadia Mono`).
  * **Visualizador de Referência ABNT NBR 6023:** Renderização limpa com destaque tipográfico real (autores em CAIXA ALTA, título em **negrito**, ano e área temática).

---

## 3. Arquitetura de Layout Desktop (3 Painéis + Barra de Comando)

Em vez de múltiplas janelas soltas ou abas confusas, adote um layout de **bancada única (Workbench)** redimensionável (`QSplitter` / Split-View):

1. **Barra Superior Enxuta (Toolbar de Operação):**
   * Seletores compactos de **Pasta de Origem** e **Pasta de Destino** (com suporte a *Drag & Drop* de pastas diretamente na janela).
   * Seletor rápido de **Provedor Primário** (`Gemini`, `Groq`, `NVIDIA`, `DeepSeek`, `Claude`, `GitHub`) com indicador visual de status da chave/fallback.
   * Toggles diretos e claros: `Copiar / Mover`, `Recursivo`, `Simulação (Dry-Run)`.
   * Botão de ação principal (`Organizar Acervo` / `Interromper` via `cancel_event` / `Retomar Sessão` quando `.bibliotec_session.json` existir).
2. **Painel Central Dividido (Master-Detail):**
   * **Esquerda — Navegador de Filtro / Áreas CAPES:** Filtro rápido por status (`Todos`, `Organizados`, `Revisão Manual`, `Duplicatas`, `Ignorados Não-PDF`) e árvore colapsável das Grandes Áreas e Áreas Básicas da CAPES/CNPq geradas no lote.
   * **Centro — Grade de Documentos de Alta Densidade:** Tabela virtualizada com colunas redimensionáveis (`Status`, `Título / Obra`, `Autor(es)`, `Ano`, `Grande Área / Área Básica`, `Tipo`, `Confiança`, `OCR`).
   * **Direita — Inspetor de Obra & Ficha ABNT (Collapsible Inspector):** Ao selecionar um PDF na grade, exibe:
     * A referência **ABNT NBR 6023** pronta para copiar com 1 clique (`Copiar Citação ABNT`);
     * Os metadados extraídos (`DOI`, `ISBN`, `SHA-256`, justificativa do LLM `reasoning`, provedor/modelo utilizado);
     * Botões de ação rápida: `Abrir PDF`, `Mostrar na Pasta` (Finder / Explorer / Nautilus) e, para itens em `revisao_manual/`, detalhes do motivo para triagem rápida.
3. **Rodapé de Telemetria em Tempo Real (Status Bar & Drawer de Progresso):**
   * Barra de progresso precisa alimentada por `PipelineEvent` (`completed_files / total_files`, contador `Restam: N`, estágio atual `Scanner -> Extrator/OCR -> OpenAlex/Google Books -> LLM -> Materialização`).
   * Indicador do teto de qualidade (`Taxa de Revisão Manual: X%` com alerta se `> 20%`).
   * Gaveta expansível opcional para inspeção de `bibliotec.log` e gerenciamento do cache SQLite (`bibliotec cache status/clean`).

---

## 4. Portabilidade Multiplataforma (macOS $\rightarrow$ Windows & Linux)

1. **Zero Dependência de APIs Exclusivas da Apple na Camada de UI:**
   * Para abrir arquivos ou revelar no gerenciador de arquivos do sistema, encapsule a chamada por SO (`open -R` no macOS, `explorer /select,` no Windows, `xdg-open` no Linux).
   * Use `pathlib.Path` em toda a interface; nunca concatene caminhos com `/` manualmente.
2. **Atalhos de Teclado Adaptativos:**
   * Use abstrações de atalho padrão (`QKeySequence.StandardKey` ou equivalente) que mapeiam automaticamente `Cmd` no macOS para `Ctrl` no Windows/Linux.
3. **Geometria, DPI e Fontes:**
   * Suporte completo a telas Retina / High-DPI sem tamanhos fixos em pixels que quebrem em escalas de 125%/150% no Windows/Linux.

---

## 5. Fluxo de Trabalho em Duas Passagens (Two-Pass Workflow)

Antes de escrever o código final da GUI:
1. **Passagem 1 — Especificação Visual e Tokens (`docs/designs/gui_spec.md`):** Defina a estrutura exata de componentes, paleta de cores hexadecimal, tipografia, wireframes ASCII da janela principal e do modal de configurações (`config.toml` / chaves de API), e o mapeamento de eventos de `bibliotec.core`.
2. **Passagem 2 — Auditoria Anti-Slop e Implementação Modular (`src/bibliotec/gui/`):** Audite o plano contra a lista de proibições da Seção 1 e implemente o pacote `bibliotec.gui` desacoplado, testável e integrado ao `run_pipeline`.
