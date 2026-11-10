# Framework Jurídico e Regulatório de Distribuição: Tomus
**Parecer Jurídico, Termos de Licenciamento, Diretrizes de Privacidade (LGPD/GDPR) e Minutas Oficiais**

---

## 1. PARECER JURÍDICO FUNDAMENTADO

### 1.1. Natureza Jurídica do Software e Regime de Direitos Autorais
O **Tomus** é uma aplicação desktop multiplataforma desenvolvida para auxílio à pesquisa acadêmica, cujo escopo tecnológico compreende a organização, extração de metadados, classificação temática (tabelas CAPES/CNPq) e renomeação de arquivos PDF em sistemas de arquivos locais.

Sob a ótica do ordenamento jurídico brasileiro:
1. **Regime Legal Aplicável**: O software enquadra-se como programa de computador regido pela **Lei Federal nº 9.609/1998 (Lei do Software)** e, subsidiariamente, pela **Lei Federal nº 9.610/1998 (Lei de Direitos Autorais)**. A proteção aos direitos autorais sobre o código-fonte independe de registro ou homologação formal junto ao INPI (art. 2º, § 3º, da Lei 9.609/1998), embora a autoria moral e patrimonial original permaneça com os seus criadores/mantenedores.
2. **Modelo de Disponibilização (Open Source / Freeware)**: O software é distribuído de forma 100% gratuita, sem restrições de cobrança de licenciamento ou assinaturas de acesso (*royalty-free*).
3. **Compatibilidade com a Licença MIT**: A licença MIT é universalmente consolidada no ecossistema de software livre e permissivo. Permite livre execução, cópia, modificação, fusão e redistribuição, condicionada apenas à preservação do aviso de direitos autorais (*copyright notice*) e à expressa aceitação da cláusula de isenção total de garantias e responsabilidade civil (*as-is* clause).

---

### 1.2. Inaplicabilidade do Código de Defesa do Consumidor (CDC) e Nexo Causal
Uma das preocupações jurídicas cardeais na disponibilização de utilitários locais de manipulação em massa de arquivos (*file renaming*, movimentação de pastas e criação de arquivos *companion*) reside no risco de litígios por alegada corrupção ou perda de arquivos digitais.

1. **Ausência de Relação de Consumo (Lei nº 8.078/1990 - CDC)**:
   - O fornecimento do software é gratuito, benevolente e desprovido de finalidade mercantil ou remuneração direta/indireta compulsória. 
   - A jurisprudência consolidada do Superior Tribunal de Justiça (STJ) condiciona a caracterização de fornecedor à habitualidade lucrativa e remuneração (art. 3º, § 2º, do CDC). A mera disponibilização de código aberto e binários executáveis em regime *freeware* afasta a incidência do microssistema consumerista.
2. **Regime Geral de Responsabilidade Civil (Código Civil Brasileiro, Lei nº 10.406/2002)**:
   - A matéria rege-se pelos arts. 186, 393 e 927 do Código Civil. Não havendo ato ilícito ou dolo imputável aos desenvolvedores, e diante da aceitação contratual de utilização "no estado em que se encontra" (*as is*), inexiste dever de indenizar danos emergentes ou lucros cessantes decorrentes do mau uso do programa, travamentos operacionais ou incompatibilidade de sistemas de arquivos.
3. **Dever de Mitigação de Danos pelo Próprio Titular (*Duty to Mitigate the Loss*)**:
   - Pelo princípio da boa-fé objetiva (art. 422 do CC), incumbe ao usuário que manipula acervos digitais adotar cautelas preliminares essenciais, notadamente a execução prévia de cópias de segurança integrais (*backups*). A negligência do usuário ao autorizar movimentações ou renomeações automáticas em lote sem cópia de salvaguarda configura culpa exclusiva da vítima (art. 945 do CC) e/ou fortuito externo decorrente de falha física de hardware ou de permissões do sistema operacional.

---

### 1.3. Conformidade com a LGPD (Lei nº 13.709/2018) e GDPR: Arquitetura *Privacy-by-Design*
O Tomus foi concebido sob o rigoroso paradigma de **Privacidade desde a Concepção e por Padrão (*Privacy by Design & by Default*)**:

1. **Inexistência de Infraestrutura de Nuvem Intermediária**:
   - Os mantenedores do Tomus **não** possuem, operam ou intermedeiam servidores de retaguarda (*backend servers*), banco de dados em nuvem ou serviços de telemetria/rastreamento de uso.
   - Nenhuma informação pessoal, conteúdo de PDF, caminho de diretório ou chave de API transita por servidores pertencentes aos autores do software.
2. **Operação Estritamente Local no Endpoint do Usuário**:
   - A leitura dos arquivos PDF, a análise morfológica, a criação de arquivos de metadados `.md` e a reorganização de pastas ocorrem em memória e em disco local na máquina do usuário.
3. **Credenciais de Acesso a APIs de Terceiros (LLMs e Bases Bibliográficas)**:
   - Todas as chaves secretas de API (Google Gemini, Anthropic Claude, OpenAI, DeepSeek, Groq, NVIDIA NIM, OpenAlex, Google Books) são inseridas voluntariamente pelo usuário e armazenadas de forma restrita e local no equipamento (ex.: arquivos locais de configuração ou chaveiro do sistema operacional).
   - O software opera como mero agente/cliente HTTP automatizado.
4. **Papéis Jurídicos perante a LGPD**:
   - **Usuário**: Atua como **Controlador dos Dados** (art. 5º, VI, da LGPD) em relação aos documentos PDF que escolhe processar e aos trechos enviados aos provedores de IA. O usuário é o exclusivo responsável por avaliar se os documentos contêm dados pessoais protegidos ou informações confidenciais antes de submetê-los a serviços de IA remotos.
   - **Provedores de Nuvem/LLM de Terceiros (OpenAI, Google, Anthropic, etc.)**: Atuam como Operadores/Processadores terceirizados sob os termos contratuais e políticas de privacidade independentes contratadas pelo próprio usuário ao criar suas chaves de API.
   - **Desenvolvedores do Tomus**: Não realizam operações de tratamento de dados pessoais (*data processing*), não tendo acesso nem custódia a quaisquer informações ou metadados processados pela ferramenta.

---

### 1.4. Natureza Jurídica das Contribuições Espontâneas (Doações Voluntárias)
Para viabilizar a sustentabilidade do projeto sem transmudar a relação em comércio eletrônico:

1. **Enquadramento no Artigo 538 do Código Civil Brasileiro**:
   - As contribuições financeiras (via chave Pix, plataformas de apoio voluntário, GitHub Sponsors, Apoia.se, etc.) configuram **Doação Pura e Simples**, realizada por mera liberalidade do doador como forma de reconhecimento e incentivo ao projeto de código aberto.
2. **Inexistência de Vínculo Contratual Sinalagmático**:
   - A doação **não** confere ao doador:
     - Direito a suporte técnico dedicado ou níveis de serviço garantidos (SLA);
     - Customizações de código sob demanda;
     - Acesso a versões restritas ou exclusivas (o software permanece indistintamente 100% público e gratuito para todos);
     - Direito a reembolso ou compensação financeira por insatisfação operacional.
3. **Afastamento do Risco Tributário de Prestação de Serviço**:
   - Caracterizada a doação civil desvinculada de venda de licenças ou prestação onerosa de serviços de informática (ausência de hipótese de incidência de ISSQN ou ICMS sobre mercadoria digital).

---

### 1.5. Propriedade Intelectual e Uso Nominativo de Marcas de Terceiros
O Tomus faz referência a tabelas de classificação e interfaces de programação de terceiros:
1. **Tabelas de Áreas do Conhecimento CAPES/CNPq**:
   - O uso das nomenclaturas das Grandes Áreas, Áreas e Subáreas da Coordenação de Aperfeiçoamento de Pessoal de Nível Superior (CAPES) e do Conselho Nacional de Desenvolvimento Científico e Tecnológico (CNPq) possui finalidade estritamente catalográfica, taxonômica e educacional, correspondendo a dados e classificações científicas de domínio e interesse público brasileiro.
2. **Marcas e APIs de LLMs (Google, Anthropic, OpenAI, DeepSeek, Groq, NVIDIA) e Fontes Bibliográficas (OpenAlex, CrossRef, Google Books)**:
   - A referência a tais nomes é feita sob a égide do **Uso Nominativo e Justo de Marcas (*Nominative Fair Use*)**, em consonância com o **Artigo 132, incisos II e IV, da Lei de Propriedade Industrial (Lei Federal nº 9.279/1996 - LPI)**, o qual assegura que o titular de marca não pode impedir o uso de sua marca por terceiros para indicar a destinação ou compatibilidade técnica do produto, contanto que não gere falsa confusão de origem ou patrocínio direto.
   - O Tomus declara expressamente não possuir afiliação institucional, patrocínio ou chancela oficial por parte de nenhuma das corporações ou fundações citadas.

---

## 2. MINUTA CONTRATUAL: ARQUIVO OFICIAL `LICENSE`

*Abaixo consta a minuta recomendada para o arquivo `LICENSE` na raiz do repositório, combinando a consagrada Licença MIT em inglês com adendo legal de termos complementares em português.*

```text
MIT License

Copyright (c) 2026 Tomus Contributors and Maintainers.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

================================================================================
TERMOS COMPLEMENTARES E CONDIÇÕES DE USO (BRASIL / JURISDIÇÃO LOCAL)
================================================================================

1. NATUREZA DA DISTRIBUIÇÃO E GRATUIDADE
O Tomus é um programa de computador distribuído no modelo de código aberto
e utilitário freeware (100% gratuito), regido pela Lei Federal nº 9.609/1998
(Lei do Software) e Lei Federal nº 9.610/1998 (Direitos Autorais). Não há
qualquer cobrança compulsória para o seu uso ou instalação.

2. CLÁUSULA DE ISENÇÃO DE RESPONSABILIDADE CIVIL POR ARQUIVOS LOCAIS
O SOFTWARE FOI CONCEBIDO PARA REALIZAR OPERAÇÕES DE LEITURA, CLASSIFICAÇÃO,
RENOMEAÇÃO E ORGANIZAÇÃO DE ARQUIVOS DIGITAIS DIRETAMENTE NO DISPOSITIVO LOCAL
DO USUÁRIO. EM NENHUMA HIPÓTESE OS AUTORES, COLABORADORES OU DISTRIBUIDORES
DO TOMUS SERÃO RESPONSÁVEIS POR:
(I) QUAISQUER DANOS DIRETOS, INDIRETOS, INCIDENTAIS OU EMERGENTES,
(II) CORRUPÇÃO, PERDA, APAGAMENTO INVOLUNTÁRIO OU RENOMEAÇÃO IMPRÓPRIA DE
     DOCUMENTOS OU DIRETÓRIOS,
(III) PERDA DE DADOS DE PESQUISA, DISSERTAÇÕES, TESES OU ACERVOS BIBLIOGRÁFICOS,
(IV) INCOMPATIBILIDADES COM SISTEMAS DE ARQUIVOS (NTFS, APFS, EXT4 ETC.).
É DEVER EXCLUSIVO DO USUÁRIO MANTER CÓPIAS DE SEGURANÇA (BACKUP) COMPLETAS E
ATUALIZADAS DE SEUS ARQUIVOS ANTES DE INICIAR QUALQUER PROCESSO EM LOTE.

3. PRIVACIDADE E PROTEÇÃO DE DADOS (LGPD - LEI Nº 13.709/2018)
O Tomus opera exclusivamente no dispositivo local do usuário. Não há coleta,
telemetria ou tráfego de dados para servidores dos desenvolvedores. O usuário
é qualificado como único Controlador perante a LGPD em relação aos dados
contidos nos arquivos manipulados e às requisições enviadas por meio de suas
chaves de API pessoais para serviços de terceiros.

4. CONTRIBUIÇÕES ESPONTÂNEAS (DOAÇÃO PURA - ART. 538 DO CÓDIGO CIVIL)
Quaisquer transferências financeiras voluntárias remetidas aos desenvolvedores
(via Pix, plataformas de apoio ou financiamento coletivo) configuram Doação
Pura por mera liberalidade e apreço. Tais atos de mecenato não ensejam relação
de consumo, não conferem direitos a suporte técnico com SLA garantido, não
garantem pedidos de funcionalidades exclusivas e não são passíveis de estorno.
================================================================================
```

---

## 3. CLÁUSULAS DE ISENÇÃO DE RESPONSABILIDADE CIVIL E DIRETRIZES DE BACKUP
*(Para inclusão na documentação técnica, instaladores e manual do usuário)*

### Declaração de Operação Local e Segurança do Acervo

> ### ⚠️ AVISO MANDATÓRIO DE CÓPIA DE SEGURANÇA (BACKUP)
> 
> O **Tomus** executa tarefas profundas de organização em disco, incluindo:
> 1. Renomeação padronizada de arquivos `.pdf`;
> 2. Criação de árvores de diretórios baseadas nas áreas da CAPES/CNPq;
> 3. Geração de arquivos complementares `.md` (companion files) contendo referências ABNT NBR 6023 e fichamentos.
>
> Embora o software incorpore rotinas estritas de segurança (como verificação de integridade antes da renomeação, sanitização de caracteres proibidos pelo sistema operacional e modo de simulação/visualização prévia):
> 
> * **A realização prévia de backup é de responsabilidade estrita e indelegável do usuário.**
> * **Recomenda-se enfaticamente testar o processamento primeiramente em uma pasta de amostra reduzida** antes de aplicar a renomeação a tomusas acadêmicas massivas.
> * Os desenvolvedores, colaboradores e instituições associadas ao Tomus **ficam isentos de toda e qualquer responsabilidade civil ou patrimonial** decorrente de interrupções de energia, falhas de disco, permissões concorrentes de acesso, substituição acidental de arquivos ou comportamento inadequado gerado por interpretações automatizadas de modelos de inteligência artificial.

---

## 4. POLÍTICA DE PRIVACIDADE E CONFORMIDADE COM LGPD/GDPR

### 4.1. Fundamentos e Filosofia "Zero Telemetria"
* **Sem Rastreadores (No Trackers)**: O Tomus não possui SDKs de analytics (Google Analytics, Sentry, Mixpanel, etc.).
* **Sem Servidores Proprietários**: O software não se comunica com nenhum servidor pertencente aos criadores do Tomus. Nenhuma chamada HTTP "home" é realizada para verificar licença ou registrar uso.
* **Execução Local (On-Device Processing)**: A extração do texto dos PDFs é realizada integralmente no processador e na memória do computador do usuário por tomusas nativas de código aberto.

### 4.2. Fluxo de Dados e Credenciais de APIs Externas
1. **Credenciais Pessoais (BYOK - Bring Your Own Key)**:
   - Para utilizar os recursos de inteligência artificial ou consulta bibliográfica avançada, o usuário fornece diretamente as suas próprias chaves de autenticação (*API Keys*).
   - O armazenamento das chaves é realizado localmente nos arquivos de configuração do usuário no diretório de perfil (`~/.tomus/` ou `AppData` no Windows).
2. **Comunicação Direta com Provedores Terceirizados**:
   - Ao disparar o enriquecimento semântico, o Tomus estabelece uma conexão TLS/HTTPS direta e exclusiva entre a máquina do usuário e os servidores da empresa provedora contratada pelo usuário (ex.: Google Vertex/AI Studio, Anthropic Cloud, DeepSeek, Groq Cloud, NVIDIA Cloud, OpenAlex API).
   - O usuário deve observar e acatar as respectivas políticas de privacidade e termos de serviço de cada fornecedor que decidir integrar.
3. **Resumo de Papéis Regulatórios (LGPD)**:
   | Elemento | Papel Jurídico | Responsabilidade |
   | :--- | :--- | :--- |
   | **Usuário** | Controlador de Dados | Titular das escolhas de arquivos, chaves de API e consentimento de envio. |
   | **APIs Externas (Google, OpenAI, etc.)** | Operadores Terceirizados | Processamento dos prompts e dados conforme seus respectivos termos de serviço. |
   | **Mantenedores do Tomus** | Criadores de Código Aberto | Isentos de custódia; sem acesso a dados, credenciais ou acervos. |

---

## 5. TERMO DE GRATIFICAÇÃO ESPONTÂNEA E DOAÇÃO VOLUNTÁRIA

*Texto a ser divulgado na seção de apoio do repositório, documentação e botão "Apoiar o Projeto":*

```markdown
### ☕ Apoie o Tomus (Doação Voluntária)

O Tomus é uma iniciativa de código aberto, concebida para fortalecer a pesquisa científica e facilitar a vida de estudantes, professores e pesquisadores no Brasil e no mundo. O aplicativo é e sempre será **100% gratuito e livre**.

Se o Tomus economizou suas horas de organização acadêmica e você deseja expressar sua gratidão e incentivar o desenvolvimento contínuo de novas funcionalidades, sinta-se à vontade para fazer uma contribuição espontânea:

* **Chave Pix (Brasil)**: `dpinheiro+tomus@gmail.com`
* **Apoio Coletivo / Internacional**: `[link-github-sponsors-ou-apoia-se]`

#### Esclarecimento Jurídico sobre a Doação:
1. **Natureza Jurídica**: Qualquer contribuição financeira voluntária configura estritamente **Doação Pura e Simples**, nos termos do art. 538 da Lei Federal nº 10.406/2002 (Código Civil Brasileiro).
2. **Ausência de Relação Comercial**: A doação voluntária não constitui compra de licença, pagamento por serviços, antecipação de mensalidade ou contratação de software sob encomenda.
3. **Sem Contraprestação Compulsória**: A doação não obriga os desenvolvedores a prestar suporte técnico personalizado, atendimento com Acordo de Nível de Serviço (SLA), correções sob demanda ou implementação de funcionalidades específicas para o doador.
4. **Igualdade de Recursos**: Todos os usuários do Tomus usufruem do mesmo software e das mesmas ferramentas, independentemente de terem realizado ou não qualquer doação.
```

---

## 6. DECLARAÇÃO DE MARCAS E PROPRIEDADE INTELECTUAL DE TERCEIROS

* **CAPES & CNPq**: Os nomes Coordenação de Aperfeiçoamento de Pessoal de Nível Superior (CAPES) e Conselho Nacional de Desenvolvimento Científico e Tecnológico (CNPq), bem como suas respectivas Árvores do Conhecimento e Tabelas de Áreas, pertencem às fundações e agências governamentais brasileiras a eles associadas. Seu uso nesta ferramenta tem caráter estritamente funcional e acadêmico de classificação bibliográfica.
* **APIs de Terceiros e Modelos de Linguagem**: Anthropic®, Claude®, Google®, Google Gemini®, OpenAI®, ChatGPT®, DeepSeek®, Groq®, NVIDIA® e OpenAlex® são marcas registradas de seus respectivos titulares de direitos proprietários. A menção a tais entidades tem o propósito único de permitir a interoperabilidade e a configuração de endpoints pelo usuário final (*Uso Nominativo e Justo*, art. 132 da Lei nº 9.279/1996). O Tomus não representa, não é patrocinado e não mantém vínculo societário com nenhuma das organizações supramencionadas.
* **Normas ABNT**: A referência à norma técnica ABNT NBR 6023 (Informação e documentação — Referências — Elaboração) tem propósito de conformidade técnica e padronização científica de citações bibliográficas.

---

## 7. CONTEÚDO PRONTO PARA O MODAL "SOBRE O TOMUS" (ABOUT DIALOG)

Abaixo constam as duas versões padronizadas para o diálogo `AboutDialog` da interface gráfica PySide6/Qt:

### 7.1. Versão Formatada para Interface Gráfica (Rich Text / HTML / PySide6)

```html
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.5; color: #2c3e50;">
    <h2 style="margin: 0; padding-bottom: 4px; color: #1a365d; font-size: 20px;">Tomus</h2>
    <p style="margin: 0 0 12px 0; font-size: 12px; color: #718096; font-weight: 500;">
        Organizador e Catalogador de Acervos Acadêmicos • Versão 1.0.0
    </p>

    <div style="background-color: #f7fafc; border-left: 4px solid #3182ce; padding: 10px 14px; margin-bottom: 14px; border-radius: 2px;">
        <p style="margin: 0; font-size: 12px; color: #2d3748;">
            O <strong>Tomus</strong> é um software livre, aberto e 100% gratuito, desenvolvido para auxiliar pesquisadores na renomeação, enriquecimento de metadados (ABNT NBR 6023) e classificação temática (CAPES/CNPq) de seus arquivos acadêmicos.
        </p>
    </div>

    <h4 style="margin: 12px 0 4px 0; font-size: 13px; color: #2d3748;">Privacidade e Operação Local</h4>
    <p style="margin: 0 0 10px 0; font-size: 11px; color: #4a5568;">
        <strong>Privacy-by-Design:</strong> Todos os seus arquivos PDF e dados de pesquisa são processados localmente em sua máquina. O Tomus não envia telemetria e não possui servidores em nuvem. As chaves de API fornecidas são salvas exclusivamente em seu dispositivo e comunicam-se diretamente com os provedores escolhidos por você.
    </p>

    <h4 style="margin: 12px 0 4px 0; font-size: 13px; color: #2d3748;">Isenção de Responsabilidade & Backup</h4>
    <p style="margin: 0 0 10px 0; font-size: 11px; color: #4a5568;">
        Distribuído sob a <strong>Licença MIT</strong> "no estado em que se encontra" (<em>as is</em>), sem garantias de qualquer natureza. O usuário é o exclusivo responsável por manter cópias de segurança (backup) atualizadas de seus arquivos antes de realizar qualquer operação de renomeação em lote.
    </p>

    <h4 style="margin: 12px 0 4px 0; font-size: 13px; color: #2d3748;">Apoio Espontâneo ao Projeto</h4>
    <p style="margin: 0 0 12px 0; font-size: 11px; color: #4a5568;">
        O Tomus é mantido de forma independente. Contribuições voluntárias são enquadradas como Doação Pura (Art. 538 do Código Civil), desprovidas de encargo ou finalidade mercantil.
    </p>

    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 12px 0;" />

    <p style="margin: 0; font-size: 10px; color: #a0aec0; text-align: center;">
        © 2026 Tomus Contributors • Código sob Licença MIT.<br/>
        Marcas registradas (CAPES, CNPq, Google, Anthropic, DeepSeek, Groq, NVIDIA, OpenAlex) pertencem aos seus respectivos titulares.
    </p>
</div>
```

### 7.2. Bloco em Python / PySide6 para Conexão Imediata na UI

```python
"""
Módulo de Diálogo 'Sobre o Tomus' com ancoragem jurídica e conformidade LGPD.
"""
from PySide6.QtWidgets import QMessageBox, QWidget


def show_about_dialog(parent: QWidget = None) -> None:
    """Exibe o diálogo modal 'Sobre' juridicamente estruturado."""
    about_text = """
    <h3>Tomus 1.0.0</h3>
    <p><b>Organizador e Catalogador Acadêmico Inteligente</b></p>
    <p>Software livre e 100% gratuito sob os termos da <b>Licença MIT</b>.</p>
    
    <p><b>Privacidade &amp; Segurança (LGPD):</b><br>
    O Tomus opera exclusivamente no seu dispositivo local. Não coletamos telemetria 
    nem intermediamos seus arquivos em servidores externos. Suas chaves de API são armazenadas 
    de forma estritamente local.</p>
    
    <p><b>Aviso Legal de Backup:</b><br>
    O software é disponibilizado <i>'as is'</i> (no estado em que se encontra). Mantenha sempre 
    uma cópia de segurança (backup) dos seus arquivos e pastas antes de executar renomeações em lote.</p>
    
    <p><b>Doações Voluntárias:</b><br>
    Contribuições financeiras espontâneas caracterizam Doação Pura (Art. 538 do Código Civil) 
    para incentivo à pesquisa aberta, sem contraprestação mercantil ou SLA de suporte.</p>
    
    <hr>
    <p style='font-size: 9pt; color: #666;'>
    As marcas citadas (CAPES, CNPq, Anthropic, Google, DeepSeek, OpenAI, Groq, NVIDIA, OpenAlex) 
    são utilizadas com propósitos de interoperabilidade técnica e pertencem aos seus titulares.
    </p>
    """
    QMessageBox.about(parent, "Sobre o Tomus", about_text)
```

---

## 8. SÍNTESE E RECOMENDAÇÕES FINAIS PARA DEPLOY

1. **Arquivo `LICENSE`**: Salvar o conteúdo do Item 2 como `LICENSE` na raiz do projeto.
2. **Repositório GitHub/GitLab**: Criar um arquivo `SECURITY.md` ou referenciar a seção de Privacidade no `README.md`.
3. **Instaladores (PyInstaller / DMG / Inno Setup)**: Exibir o resumo dos termos e a recomendação expressa de backup na tela de aceite da instalação.
4. **Primeira Execução do App (First Run Modal / Onboarding)**: Apresentar um pequeno aviso na primeira vez que o usuário selecionar uma pasta com PDFs:
   *"Lembrete de Segurança: Certifique-se de possuir backup dos seus documentos antes de renomeá-los em lote."* com opção "Entendi".
