---
name: cross-platform-desktop-gui
description: >-
  Guia de engenharia para construção de interfaces desktop multiplataforma em Python
  (macOS, Windows e Linux) integradas ao motor bibliotec.core (threads, sinais,
  cancelamento cooperativo, diálogos nativos e empacotamento).
---

# Engenharia de GUI Desktop Multiplataforma para o BiblioTEC

Esta skill orienta a arquitetura técnica do pacote `src/bibliotec/gui/` sobre o motor `bibliotec.core` (`v0.4.0`), garantindo responsividade da thread principal (UI a 60fps), segurança de concorrência e portabilidade entre **macOS**, **Windows** e **Linux**.

---

## 1. Contratos de Integração com `bibliotec.core`

A GUI nunca deve bloquear a *Main Event Loop* durante a varredura, OCR (Docling) ou chamadas de rede (OpenAlex, Google Books, LLMs):

1. **Worker Thread Dedicada + Cancelamento Cooperativo:**
   * Execute `run_pipeline(...)` em uma thread de background (`QThread` / `threading.Thread`) passando:
     * `event_callback`: função que converte cada `PipelineEvent` (`stage`, `source_path`, `status`, `message`, `total_files`, `completed_files`, `timestamp`) em um sinal thread-safe para a thread de UI.
     * `cancel_event`: instância de `threading.Event()`. Quando o usuário clica em **Interromper**, a GUI chama `cancel_event.set()`, interrompendo o lote de forma limpa sem corromper o banco SQLite (`~/.cache/bibliotec/state.db`) nem deixar arquivos truncados.
2. **Gerenciamento de Configuração e Credenciais (`AppConfig`):**
   * A tela/modal de **Preferências e Chaves de API** deve ler e gravar `~/.config/bibliotec/config.toml` (mantendo permissão `0600` em sistemas POSIX) usando os modelos de `bibliotec.core.config` (`GeneralConfig`, `LLMConfig`, `ApiKeysConfig`) e exibir o status de cada provedor da cadeia (`gemini`, `groq`, `nvidia`, `deepseek`, `claude`, `github`).
3. **Retomada de Sessão (`bibliotec.core.session`):**
   * Ao iniciar a GUI, verifique `load_session()`. Se houver uma sessão interrompida pendente, exiba um banner discreto na barra superior permitindo retomar com 1 clique ou descartar a sessão.
4. **Inspeção de Cache (`bibliotec.core.cache`):**
   * Exiba estatísticas do cache SQLite (`~/.cache/bibliotec/state.db`: quantidade de obras indexadas e tamanho em disco) com botão para limpeza segura (`FileCache.clear()`).

---

## 2. Regras de Portabilidade (macOS, Windows e Linux)

1. **Integração com o Sistema Operacional (`os_integration.py`):**
   * **Abrir PDF no leitor padrão:**
     * macOS: `subprocess.Popen(["open", str(path)])` (ou `QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))`)
     * Windows: `os.startfile(str(path))` (ou `QDesktopServices`)
     * Linux: `subprocess.Popen(["xdg-open", str(path)])`
   * **Revelar arquivo na pasta (Finder / Explorer / File Manager):**
     * macOS: `subprocess.Popen(["open", "-R", str(path)])`
     * Windows: `subprocess.Popen(["explorer", f"/select,{Path(path).resolve()}"])`
     * Linux: abrir o diretório pai via `xdg-open str(path.parent)`
2. **Estilo Visual Unificado e Independente de Tema Bugado do SO:**
   * Utilize um sistema de tokens de estilo explícito (ex.: `QApplication.setStyle("Fusion")` + folha de estilos QSS parametrizada por tokens de tema Claro/Escuro) para garantir que a interface tenha exatamente a mesma precisão tipográfica, bordas finas de `1px` e espaçamento no macOS, no Windows 11 e no Linux (GNOME/KDE), sem depender de widgets legados de aparência datada.
3. **Ponto de Entrada CLI & Desktop:**
   * Adicione o subcomando `bibliotec gui` em `src/bibliotec/cli/main.py` e o script `[project.gui-scripts]` (`bibliotec-gui = "bibliotec.gui.app:main"`) no `pyproject.toml`.
