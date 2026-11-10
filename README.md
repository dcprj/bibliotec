<p align="center">
  <img src="logo_e_icone/Logo.png?v=2" alt="Tomus Logo" width="560">
</p>

# Tomus — Organizador Acadêmico de PDFs

[![Licença MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-blue.svg)](LICENSE)
[![Plataformas](https://img.shields.io/badge/Plataformas-macOS-green.svg)](#como-baixar-e-instalar)
[![100% Gratuito](https://img.shields.io/badge/Software-100%25%20Gratuito-orange.svg)](#-apoie-o-projeto-doação-voluntária)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python/)

O **Tomus** é uma aplicação desktop acadêmica livre e gratuita projetada para automatizar a triagem, enriquecimento bibliográfico, padronização de nomes e catalogação temática de acervos de PDFs.

Ele organiza seus documentos diretamente em seu computador conforme a taxonomia oficial de áreas do conhecimento da **CAPES/CNPq** e gera arquivos de metadados complementares (`.md`) com fichamento e referências completas estritamente formatadas segundo a norma **ABNT NBR 6023**.

```
<Destino>/<Grande Área>/<Área Básica>/<Tipo>/<Autor> - <Título> - <Subtítulo> - <Ano>.pdf
```

---

## 📥 Como Baixar e Instalar

Você não precisa instalar Python nem configurar ambientes complexos para usar o Tomus. Baixe o instalador pronto para macOS na seção de **[Releases](https://github.com/dcprj/tomus/releases)**:

| Sistema Operacional | Formato do Pacote | Link de Download Direto |
| :--- | :--- | :--- |
| **macOS** (Apple Silicon / Intel) | `.dmg` (Arrastar para `/Applications`) | [Baixar Tomus para macOS (.dmg)](https://github.com/dcprj/tomus/releases/latest) |

---

### 🍎 1. Instalação no macOS

1. Baixe o arquivo oficial `Tomus-1.1.2-macOS.dmg` (ou versão mais recente).
2. Dê duplo clique no arquivo `.dmg` baixado para abri-lo.
3. Arraste o ícone do aplicativo para a pasta **Applications (Aplicativos)**.

> [!IMPORTANT]
> **Primeira Execução no macOS (Aviso do Apple Gatekeeper):**  
> Como o Tomus é distribuído de forma independente e gratuita (sem certificado pago da Apple Developer ID de US$ 99/ano), o macOS exibirá na primeira abertura um aviso de *"desenvolvedor não identificado"*:
> * **Método 1 (Mais Simples):** Abra o Finder, vá até a pasta **Aplicativos**, clique com o **botão direito** (ou pressione `Control` + clique) no ícone do Tomus e selecione **Abrir**. Na janela de confirmação, clique em **Abrir**. Essa confirmação só precisa ser feita uma única vez!
> * **Método 2 (Via Terminal):** Se preferir liberar o aplicativo permanentemente via linha de comando:
>   ```bash
>   xattr -cr /Applications/Tomus.app
>   ```

---

### 💻 2. Instalação via Python / Terminal (Desenvolvedores)

Se você é desenvolvedor ou prefere executar o Tomus via ambiente Python:

```bash
# Clonar o repositório
git clone https://github.com/dcprj/tomus.git
cd tomus

# Criar e ativar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependências
pip install -e ".[dev]"

# Iniciar a interface gráfica (Desktop GUI)
tomus-gui
# ou:
tomus gui
```

---

## 🚀 Como Obter Chaves de API Gratuitas

O Tomus funciona localmente com simulação e extração heurística, mas alcança precisão catalográfica máxima quando conectado a modelos de linguagem (LLMs). Você pode obter chaves com **cotas 100% gratuitas** diretamente nos provedores:

1. **Google Gemini (Recomendado — Gratuito):**
   * Acesse o [Google AI Studio](https://aistudio.google.com/).
   * Faça login com sua conta Google e clique em **"Create API Key"**.
   * Cota gratuita generosa para catalogação de bibliotecas inteiras.
2. **Groq (Llama 3.3 70B — Ultrarrápido e Gratuito):**
   * Crie sua conta em [Groq Console](https://console.groq.com/).
   * Gere uma chave em **API Keys**.
3. **DeepSeek (Alta Precisão com Custo Mínimo / Bônus Gratuito):**
   * Acesse a [DeepSeek Platform](https://platform.deepseek.com/).
   * Crie sua chave em **API Keys**.
4. **NVIDIA NIM (Nemotron — Gratuito com créditos iniciais):**
   * Obtenha em [NVIDIA Build](https://build.nvidia.com/).

No Tomus, basta clicar no botão **Preferências** (ícone de engrenagem) na barra superior e colar sua chave na aba **Credenciais e Chaves de API**. A chave é gravada exclusivamente no disco local da sua máquina.

---

## ☕ Apoie o Projeto (Doação Voluntária)

O **Tomus** é uma iniciativa independente, de código aberto e **100% gratuita**. Ele foi concebido para fortalecer a pesquisa científica e poupar semanas de trabalho manual repetitivo de pesquisadores, estudantes e instituições.

Se o Tomus foi útil para sua dissertação, tese ou organização bibliográfica e você deseja demonstrar sua gratidão e incentivar a manutenção e novas funcionalidades, você pode fazer uma **contribuição espontânea de qualquer valor**:

* **Chave Pix (Brasil):** `dpinheiro+tomus@gmail.com`
* **Código-fonte no GitHub:** [Repositório Oficial dcprj/tomus](https://github.com/dcprj/tomus)

> [!NOTE]
> **Esclarecimento Jurídico (Doação Pura):**  
> Toda contribuição financeira voluntária configura estritamente **Doação Pura e Simples**, nos termos do **Art. 538 do Código Civil Brasileiro** (Lei Federal nº 10.406/2002). A doação não constitui contraprestação mercantil, compra de software, contratação de serviços ou suporte comercial com SLA. Todos os usuários têm acesso irrestrito às mesmas versões e recursos do Tomus sem distinção.

---

## 🔒 Privacidade, Transparência e Proteção de Dados (LGPD & GDPR)

O Tomus adota uma política de **Transparência Técnica e Ética Integral** sobre como os seus documentos são manipulados:

* **Arquivos PDF 100% no seu Disco Local:** O arquivo binário do PDF integral, seus capítulos completos e dados brutos de pesquisa **nunca saem do seu computador** nem são enviados para servidores em nuvem. A extração inicial e o OCR (via Apple Vision no macOS) rodam exclusivamente no processador e na memória do seu Mac.
* **Envio Estrito de Dados de Catalogação para a IA:** Para determinar a área do conhecimento na taxonomia CAPES e formatar a citação ABNT NBR 6023, o Tomus extrai um **recorte textual reduzido** (amostra das primeiras e últimas páginas, como folha de rosto, sumário e ficha catalográfica) e o submete via HTTPS/TLS diretamente à API do provedor de IA configurado por você (Google Gemini, Claude, DeepSeek, Groq ou NVIDIA NIM).
* **Modelo BYOK (Bring Your Own Key):** Suas chaves de autenticação de API residem no seu computador (com permissão `0600`) e a comunicação é ponto a ponto direta com o provedor escolhido. O Tomus **não possui servidores intermediários** e **não realiza nenhuma telemetria** ou coleta de dados analíticos.
* **Controlador dos Dados:** Perante a Lei Geral de Proteção de Dados (LGPD - Lei nº 13.709/2018), o usuário atua como único Controlador dos documentos e conteúdos que submeter ao processamento.

---

## ⚠️ Isenção de Responsabilidade e Política de Backup

> [!WARNING]
> **AVISO MANDATÓRIO DE SEGURANÇA (BACKUP):**  
> O Tomus executa operações de leitura, cópia, movimentação e renomeação em massa de arquivos digitais no sistema de arquivos local. Embora o aplicativo incorpore mecanismos rigorosos de salvaguarda (como sanitização de caracteres proibidos pelo sistema operacional, validação criptográfica de integridade SHA-256 e modo de simulação prévia `--dry-run`), o software é disponibilizado **"no estado em que se encontra" (*as-is*)**, sem garantias de qualquer natureza.  
> 
> **É responsabilidade exclusiva e indelegável do usuário manter cópias de segurança (backup) completas e atualizadas de seus acervos antes de processar pastas em lote.** Os desenvolvedores e colaboradores do Tomus ficam expressamente isentos de qualquer responsabilidade civil por eventuais perdas, exclusões ou corrupções de arquivos decorrentes de interrupções de energia, falhas físicas de hardware, permissões do sistema operacional ou interpretações automatizadas dos modelos de linguagem.

---

## ⚖️ Licença

Este projeto é software livre distribuído sob os termos da **[Licença MIT](LICENSE)** combinada com os Termos Complementares de Jurisdição Brasileira e Isenção de Responsabilidade. Consulte o arquivo [LICENSE](LICENSE) e o parecer jurídico detalhado em [`docs/legal_distribution_framework.md`](docs/legal_distribution_framework.md).

*Marcas citadas (CAPES, CNPq, Google, Anthropic, DeepSeek, Groq, NVIDIA, OpenAlex) pertencem aos seus respectivos titulares e são mencionadas exclusivamente com finalidade de identificação e interoperabilidade técnica (Uso Nominativo e Justo, Art. 132 da LPI).*
