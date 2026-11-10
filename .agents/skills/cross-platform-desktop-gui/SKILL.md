---
name: cross-platform-desktop-gui
description: >-
  Guia de engenharia para construção de interfaces desktop multiplataforma em Python
  (macOS primordialmente) integradas ao motor tomus.core (threads, sinais,
  cancelamento cooperativo, diálogos nativos e empacotamento).
---

# Engenharia de GUI Desktop para o Tomus

Esta skill orienta a arquitetura técnica do pacote `src/tomus/gui/` sobre o motor `tomus.core` (`v1.1.0`), garantindo responsividade da thread principal (UI a 60fps), segurança de concorrência e foco primordial no **macOS**.

---

## 1. Contratos de Integração com `tomus.core`

A GUI nunca deve bloquear a *Main Event Loop* durante a varredura, OCR ou chamadas de rede (OpenAlex, Google Books, LLMs):

1. **Worker Thread Dedicada + Cancelamento Cooperativo:**
   * Execute `run_pipeline(...)` em uma thread de background (`QThread` / `threading.Thread`) passando:
     * `event_callback`: função que converte cada `PipelineEvent` (`stage`, `source_path`, `status`, `message`, `total_files`, `completed_files`, `timestamp`) em um sinal thread-safe para a thread de UI.
     * `cancel_event`: instância de `threading.Event()`. Quando o usuário clica em **Interromper**, a GUI chama `cancel_event.set()`, interrompendo o lote de forma limpa sem corromper o banco SQLite (`~/.cache/tomus/state.db`) nem deixar arquivos truncados.
2. **Gerenciamento de Configuração e Credenciais (`AppConfig`):**
   * A tela/modal de **Preferências e Chaves de API** deve ler e gravar `~/.config/tomus/config.toml` (mantendo permissão `0600` em sistemas POSIX) usando os modelos de `tomus.core.config` (`GeneralConfig`, `LLMConfig`, `ApiKeysConfig`) e exibir o status de cada provedor da cadeia (`gemini`, `groq`, `nvidia`, `deepseek`, `claude`, `github`).
3. **Retomada de Sessão (`tomus.core.session`):**
   * Ao iniciar a GUI, verifique `load_session()`. Se houver uma sessão interrompida pendente, exiba um banner discreto na barra superior permitindo retomar com 1 clique ou descartar a sessão.
4. **Inspeção de Cache (`tomus.core.cache`):**
   * Exiba estatísticas do cache SQLite (`~/.cache/tomus/state.db`: quantidade de obras indexadas e tamanho em disco) com botão para limpeza segura (`FileCache.clear()`).

---

## 2. Integração com o Sistema Operacional (macOS)

1. **Integração com o macOS:**
   * **Abrir PDF no leitor padrão:** `QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))`
   * **Revelar arquivo no Finder:** `subprocess.Popen(["open", "-R", str(path)])`
2. **Ponto de Entrada CLI & Desktop:**
   * Subcomando `tomus gui` em `src/tomus/cli/main.py` e script `[project.gui-scripts]` (`tomus-gui = "tomus.gui.app:main"`) no `pyproject.toml`.
