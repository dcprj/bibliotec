# BiblioTEC v1.0.0 — Lançamento Oficial (macOS & Windows)

O **BiblioTEC** é uma aplicação desktop acadêmica livre e 100% gratuita projetada para automatizar a triagem, enriquecimento bibliográfico, padronização de nomes e catalogação temática de acervos de PDFs conforme a taxonomia oficial **CAPES/CNPq** e normas **ABNT NBR 6023**.

---

## 📥 Pacotes Oficiais Disponíveis para Download

| Sistema Operacional | Arquivo | Tamanho | Checksum (SHA-256) |
| :--- | :--- | :--- | :--- |
| **macOS** (Apple Silicon / Intel) | [`BiblioTEC-1.0.0-macOS.dmg`](https://github.com/dcprj/bibliotec/releases/download/v1.0.0/BiblioTEC-1.0.0-macOS.dmg) | ~514 MB | `f1d6edbd9cf0bd033589f181a093009107856648e686019cbf38337b808f8ad0` |
| **Windows** (10 / 11 64-bit) | [`BiblioTEC_Setup_v1.0.0_Windows_x64.exe`](https://github.com/dcprj/bibliotec/releases/download/v1.0.0/BiblioTEC_Setup_v1.0.0_Windows_x64.exe) | ~366 MB | `bb6cd9bcaa6d79bdc5402dea5224954fdbfb1b5b2b57d2204219baeda5410dc3` |

---

## 🛠️ Instruções de Instalação

### 🍎 macOS
1. Baixe o arquivo `BiblioTEC-1.0.0-macOS.dmg`.
2. Dê um duplo clique para montar o volume e arraste o **BiblioTEC.app** para a pasta **Applications (Aplicativos)**.
3. **Primeira Abertura (macOS Gatekeeper):**
   - Como o BiblioTEC é um projeto de código aberto sem assinatura paga da Apple ($99/ano), o macOS exibirá um aviso de segurança.
   - Abra o **Ajustes do Sistema > Privacidade e Segurança** e clique em **"Abrir Mesmo Assim"**;
   - *Ou alternativamente, no Terminal:*
     ```bash
     xattr -cr /Applications/BiblioTEC.app
     ```

### 🪟 Windows
1. Baixe o executável `BiblioTEC_Setup_v1.0.0_Windows_x64.exe`.
2. Execute o instalador e siga o assistente moderno passo a passo.
3. Se o aviso do Windows SmartScreen for exibido ("O Windows protegeu o seu computador"), clique em **"Mais informações"** e em seguida em **"Executar assim mesmo"**.
4. O assistente criará automaticamente atalhos na Área de Trabalho e no Menu Iniciar com o ícone oficial da aplicação.

---

## ✨ Destaques da Versão v1.0.0
- **Identidade Visual Oficial:** Novo logotipo oficial integrado na interface gráfica desktop (WebEngine/HTML5) e ícones dedicados em alta definição para Dock e Barra de Tarefas.
- **Triagem Inteligente Local:** Modelos de inteligência artificial locais e remotos (OpenAI, Gemini, Groq, Ollama, DeepSeek, Claude) com fallback resiliente.
- **Enriquecimento e Metadados:** Extração direta de títulos, autores, resumos e geração de referências no formato ABNT NBR 6023.
- **Cache Local SQLite:** Evita reprocessamento de arquivos já catalogados e economiza chamadas de API.
- **Privacidade por Design (Zero-Telemetry):** Processamento estritamente local; chaves de API e arquivos não saem da sua máquina.

---

## ☕ Apoie o Projeto (Doação Voluntária)
O BiblioTEC é livre e gratuito. Se o utilitário ajudou a acelerar sua pesquisa acadêmica e você deseja incentivar o desenvolvimento contínuo, considere fazer uma contribuição espontânea via **Pix**:

**Chave Pix:** `dpinheiro+bibliotec@gmail.com`  
*(Contribuição voluntária sob Art. 538 do Código Civil Brasileiro — Doação Pura e Simples).*
