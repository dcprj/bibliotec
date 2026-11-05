"""CLI do BiblioTEC com Typer + Rich (Item 24).

Comandos:
  bibliotec organize [--origem/-o <SOURCE>] [--destino/-d <TARGET>] [OPTIONS]
  bibliotec organize <SOURCE_DIR> <TARGET_DIR] [OPTIONS]
  bibliotec config init [--local]
  bibliotec config show
  bibliotec config path

Quando nenhum subcomando for informado mas --origem/-o e --destino/-d forem
passados diretamente (ex: `bibliotec -o ... -d ... --dry-run`), o organize
é executado automaticamente.
"""

from __future__ import annotations

import warnings

# Silenciar avisos de bibliotecas externas antes de qualquer outro import.
warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\..*")
warnings.filterwarnings("ignore", category=FutureWarning, module=r"fitz.*")
warnings.filterwarnings(
    "ignore", message=r".*urllib3 v2 only supports OpenSSL.*"
)
warnings.filterwarnings(
    "ignore", category=DeprecationWarning, message=r".*SwigPy.*|.*swigvarlink.*"
)

import os

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    MofNCompleteColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from typer import Context, Option

from bibliotec.core.config import (
    AppConfig,
    GLOBAL_CONFIG_PATH,
    LOCAL_CONFIG_FILENAME,
    init_config_file,
    generate_config_template,
    mask_key,
)
from bibliotec.core.models import ProcessStatus
from bibliotec.core.pipeline import run_pipeline
from bibliotec.core.cache import CACHE_DB_PATH, FileCache
from bibliotec.core.llm import GeminiProvider, MockLLMProvider
from bibliotec.core.scanner import scan_directory
from bibliotec.storage.organizer import LibraryOrganizer
from bibliotec.core.taxonomy import get_taxonomy_version

app = typer.Typer(
    name="bibliotec",
    help="Organizador Acadêmico de PDFs baseado na taxonomia CAPES/CNPq.",
    no_args_is_help=True,
    invoke_without_command=True,
)
console = Console()


# --------------------------------------------------------------------------- #
# Helpers de configuração
# --------------------------------------------------------------------------- #
def _load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Carregar a configuração ativa respeitando a ordem de precedência."""
    if config_path is not None:
        try:
            import tomllib  # Python 3.11+
        except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
            import tomli as tomllib  # type: ignore[no-redef]

        with open(config_path, "rb") as fh:
            data = tomllib.load(fh)
        general = data.get("general", {})
        llm = data.get("llm", {})
        api_keys = data.get("api_keys", {})
        return AppConfig(
            general=general if general else None,
            llm=llm if llm else None,
            api_keys=api_keys if api_keys else None,
        )
    return AppConfig()


def _resolve_api_key(config: AppConfig, cli_key: Optional[str]) -> str:
    """Resolver a chave do Gemini: flag CLI > env > config."""
    if cli_key:
        return cli_key
    env_key = os.environ.get("BIBLIOTEC_GEMINI_API_KEY") or os.environ.get(
        "GEMINI_API_KEY", ""
    )
    if env_key:
        return env_key
    return config.api_keys.gemini_api_key


def _build_provider(config: AppConfig, api_key: Optional[str],
                    model: Optional[str]) -> object | None:
    resolved_key = _resolve_api_key(config, api_key)
    resolved_model = model or config.llm.model
    if resolved_key:
        return GeminiProvider(api_key=resolved_key, model=resolved_model)
    # Sem chave de API: não usar MockLLMProvider silenciosamente na CLI real.
    return None


def _aplicar_overrides(
    cfg: AppConfig,
    *,
    recursive: Optional[bool] = None,
    move: Optional[bool] = None,
    confidence_min: Optional[float] = None,
    workers: int = 1,
    no_cache: bool = False,
    model: Optional[str] = None,
    google_books_key: Optional[str] = None,
) -> AppConfig:
    """Aplicar overrides de flags de CLI (maior precedência) sobre a config."""
    from bibliotec.core.config import GeneralConfig, LLMConfig, ApiKeysConfig

    general_kwargs: dict = {}
    if recursive is not None:
        general_kwargs["recursive"] = recursive
    file_operation = cfg.general.file_operation
    if move is not None:
        file_operation = "move" if move else "copy"
    general_kwargs["file_operation"] = file_operation
    if confidence_min is not None:
        general_kwargs["confidence_min"] = confidence_min
    general_kwargs["workers"] = workers
    general_kwargs["use_cache"] = not no_cache

    llm_kwargs: dict = {}
    if model is not None:
        llm_kwargs["model"] = model

    api_keys_kwargs: dict = {}
    if google_books_key is not None:
        api_keys_kwargs["google_books_api_key"] = google_books_key

    return AppConfig(
        general=GeneralConfig(**{**cfg.general.model_dump(), **general_kwargs}),
        llm=LLMConfig(**{**cfg.llm.model_dump(), **llm_kwargs}),
        api_keys=ApiKeysConfig(**{**cfg.api_keys.model_dump(), **api_keys_kwargs}),
    )


def _executar_organize(
    *,
    source_dir: Path,
    target_dir: Path,
    config: Optional[Path] = None,
    recursive: Optional[bool] = None,
    move: Optional[bool] = None,
    dry_run: bool = False,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    google_books_key: Optional[str] = None,
    confidence_min: Optional[float] = None,
    no_cache: bool = False,
    workers: int = 1,
) -> None:
    """Executar o pipeline de organização (comum a organize e ao callback raiz)."""
    cfg = _load_config(config)
    cfg = _aplicar_overrides(
        cfg,
        recursive=recursive,
        move=move,
        confidence_min=confidence_min,
        workers=workers,
        no_cache=no_cache,
        model=model,
        google_books_key=google_books_key,
    )

    provider = _build_provider(cfg, api_key, model)
    if provider is None:
        console.print("[red]Erro:[/red] Nenhuma chave de API do Gemini configurada.")
        console.print(
            "Defina gemini_api_key no bibliotec.toml (ou ~/.config/bibliotec/config.toml) "
            "ou passe --api-key na linha de comando."
        )
        raise typer.Exit(code=1)

    target_dir = target_dir.resolve()
    organizer = LibraryOrganizer(
        target_dir,
        file_operation=cfg.general.file_operation,
        dry_run=dry_run,
    )
    cache = FileCache(enabled=cfg.general.use_cache)

    events = []

    total_files_var: list[int] = [0]  # mutable para capturar do evento scanner
    completed_files_var: list[int] = [0]

    # Barra de progresso consolidada no topo.
    prog_bar = Progress(
        TextColumn("[bold blue]{task.fields[top_desc]}", justify="left"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TextColumn("• Restam: [bold yellow]{task.fields[remaining]}[/bold yellow]"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        transient=False,
    )
    # Linha de status do arquivo atual abaixo da barra.
    status_prog = Progress(
        TextColumn("  ↳ [dim]{task.description}[/dim]", justify="left"),
        transient=False,
    )
    group = Group(prog_bar, status_prog)

    task_geral = prog_bar.add_task(
        "Progresso Geral", total=None, remaining=0, top_desc="Iniciando pipeline...",
    )
    task_status = status_prog.add_task("Status do arquivo atual", start=False)

    with Live(group, console=console, refresh_per_second=10, transient=False):

        def emit_with_progress(event):
            events.append(event)
            # Capturar total de PDFs quando o scanner terminar.
            if event.stage == "scanner" and event.status == "completed" and event.total_files:
                total_files_var[0] = event.total_files or 0
                prog_bar.update(
                    task_geral,
                    total=event.total_files,
                    remaining=event.total_files,
                )
            # Eventos de início (started): atualizar status abaixo.
            if event.status == "started":
                status_prog.update(
                    task_status,
                    description=f"{event.stage}: {Path(event.source_path).name}",
                )
                return
            # Eventos terminais: avançar barra geral e atualizar status.
            if event.status in ("organized", "manual_review", "error", "duplicate_skipped"):
                prog_bar.advance(task_geral, 1)
                comp = int(prog_bar.tasks[task_geral].completed)
                tot = int(prog_bar.tasks[task_geral].total or 0)
                rem = max(0, tot - comp)
                prog_bar.update(
                    task_geral,
                    remaining=rem,
                    top_desc=f"{event.stage}: {Path(event.source_path).name} - {event.status}",
                )
                status_prog.update(
                    task_status,
                    description=f"{event.stage}: {Path(event.source_path).name} - {event.status}",
                )

        try:
            summary = run_pipeline(
                source_dir=source_dir,
                target_dir=target_dir,
                config=cfg,
                provider=provider,
                cache=cache,
                organizer=organizer,
                workers=cfg.general.workers,
                event_callback=emit_with_progress,
                use_cache=cfg.general.use_cache,
            )
        finally:
            cache.close()
            progress.update(task, description="Concluído")

    _print_summary(summary, dry_run)


def _print_summary(summary, dry_run: bool) -> None:
    console.print()
    table = Table(title="Resultado da Organização", show_lines=True)
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", justify="right", style="magenta")
    table.add_row("Total escaneado", str(summary.total_scanned))
    table.add_row("Organizados", str(summary.organized_count))
    table.add_row("Revisão manual", str(summary.manual_review_count))
    table.add_row("Duplicatas puladas", str(summary.duplicate_skipped_count))
    table.add_row("Não-PDFs ignorados", str(summary.ignored_non_pdf_count))
    table.add_row("Erros", str(summary.error_count))
    table.add_row("Taxa revisão manual", f"{summary.manual_review_ratio:.1%}")
    teto = ("EXCEDEU o teto de 20%"
            if summary.exceeded_manual_review_ceiling else "dentro do teto (20%)")
    table.add_row("Teto revisão manual", teto)
    console.print(table)
    console.print()
    if dry_run:
        console.print("[yellow]Modo dry-run: nenhum PDF foi copiado/movido e "
                      "nenhuma pasta temática criada.[/yellow]")
    console.print(f"Manifesto gravado em: {summary.entries and 'manifest.json'}")


# --------------------------------------------------------------------------- #
# Callback raiz: permite 'bibliotec -o ... -d ... [--dry-run]' sem subcomando.
# --------------------------------------------------------------------------- #
@app.callback(invoke_without_command=True)
def _root_callback(
    ctx: Context,
    origem: Optional[Path] = Option(
        None, "--origem", "-o", "--source",
        help="Diretório de origem com PDFs.",
    ),
    destino: Optional[Path] = Option(
        None, "--destino", "-d", "--target",
        help="Diretório de destino da biblioteca.",
    ),
    config: Optional[Path] = Option(
        None, "--config", help="Caminho para um config.toml customizado.",
    ),
    recursive: Optional[bool] = Option(
        None, "--recursive/--flat",
        help="Varredura recursiva (padrão) ou apenas nível raiz.",
    ),
    move: Optional[bool] = Option(
        None, "--move/--copy",
        help="Mover arquivos em vez de copiar (padrão: copiar).",
    ),
    dry_run: bool = Option(
        False, "--dry-run",
        help="Extrair e classificar sem copiar/mover arquivos.",
    ),
    model: Optional[str] = Option(
        None, "--model", help="Nome do modelo Gemini.",
    ),
    api_key: Optional[str] = Option(
        None, "--api-key", help="Chave de API do Gemini.",
    ),
    google_books_key: Optional[str] = Option(
        None, "--google-books-key", help="Chave de API do Google Books.",
    ),
    confidence_min: Optional[float] = Option(
        None, "--confidence-min",
        help="Limiar mínimo para organização automática (padrão: 0.70).",
    ),
    no_cache: bool = Option(
        False, "--no-cache", help="Ignorar o cache SQLite local.",
    ),
    workers: int = Option(
        1, "--workers", help="Concorrência para chamadas de rede (padrão: 1).",
    ),
) -> None:
    """Ponto de entrada único do BiblioTEC.

    Se nenhum subcomando for informado mas --origem/-o e --destino/-d forem
    passados, executa organize automaticamente. Caso contrário, exibe o help.
    """
    # Quando um subcomando é invocado, o callback ainda roda; delegamos para ele.
    if ctx.invoked_subcommand is not None:
        return

    if origem is None and destino is None:
        # Nenhum subcomando e nenhuma opção de origem/destino: exibir help.
        console.print(ctx.get_help())
        raise typer.Exit(code=0)

    if origem is None or destino is None:
        console.print("[red]Erro:[/red] É necessário informar --origem/-o e "
                      "--destino/-d (ou usar 'bibliotec organize <origem> <destino>').")
        raise typer.Exit(code=2)

    _executar_organize(
        source_dir=origem,
        target_dir=destino,
        config=config,
        recursive=recursive,
        move=move,
        dry_run=dry_run,
        model=model,
        api_key=api_key,
        google_books_key=google_books_key,
        confidence_min=confidence_min,
        no_cache=no_cache,
        workers=workers,
    )


# --------------------------------------------------------------------------- #
# Comando: organize
# --------------------------------------------------------------------------- #
@app.command("organize")
def organize(
    source_dir: Optional[Path] = Option(
        None, "--origem", "-o", "--source",
        help="Diretório de origem com PDFs.",
    ),
    target_dir: Optional[Path] = Option(
        None, "--destino", "-d", "--target",
        help="Diretório de destino da biblioteca.",
    ),
    pos_source: Optional[Path] = typer.Argument(
        None, help="Diretório de origem com PDFs (posicional).",
    ),
    pos_target: Optional[Path] = typer.Argument(
        None, help="Diretório de destino da biblioteca (posicional).",
    ),
    config: Optional[Path] = Option(
        None, "--config", help="Caminho para um config.toml customizado.",
    ),
    recursive: Optional[bool] = Option(
        None, "--recursive/--flat",
        help="Varredura recursiva (padrão) ou apenas nível raiz.",
    ),
    move: Optional[bool] = Option(
        None, "--move/--copy",
        help="Mover arquivos em vez de copiar (padrão: copiar).",
    ),
    dry_run: bool = Option(
        False, "--dry-run",
        help="Extrair e classificar sem copiar/mover arquivos.",
    ),
    model: Optional[str] = Option(
        None, "--model", help="Nome do modelo Gemini.",
    ),
    api_key: Optional[str] = Option(
        None, "--api-key", help="Chave de API do Gemini.",
    ),
    google_books_key: Optional[str] = Option(
        None, "--google-books-key", help="Chave de API do Google Books.",
    ),
    confidence_min: Optional[float] = Option(
        None, "--confidence-min",
        help="Limiar mínimo para organização automática (padrão: 0.70).",
    ),
    no_cache: bool = Option(
        False, "--no-cache", help="Ignorar o cache SQLite local.",
    ),
    workers: int = Option(
        1, "--workers", help="Concorrência para chamadas de rede (padrão: 1).",
    ),
) -> None:
    """Organizar uma biblioteca de PDFs (5 estágios).

    A origem e o destino podem ser informados como argumentos posicionais
    (`bibliotec organize <ORIGEM> <DESTINO>`) ou via opções
    (`--origem/-o` / `--destino/-d`). Se faltar algum dos dois, exibe erro.
    """
    # Resolver origem e destino: opções têm precedência sobre posicionais.
    origem = source_dir if source_dir is not None else pos_source
    destino = target_dir if target_dir is not None else pos_target

    if origem is None or destino is None:
        console.print("[red]Erro:[/red] É necessário informar --origem/-o e "
                      "--destino/-d (ou passar como argumentos posicionais).")
        raise typer.Exit(code=2)

    _executar_organize(
        source_dir=origem,
        target_dir=destino,
        config=config,
        recursive=recursive,
        move=move,
        dry_run=dry_run,
        model=model,
        api_key=api_key,
        google_books_key=google_books_key,
        confidence_min=confidence_min,
        no_cache=no_cache,
        workers=workers,
    )


# --------------------------------------------------------------------------- #
# Grupo: config
# --------------------------------------------------------------------------- #
config_app = typer.Typer(help="Gerenciar o arquivo de configuração config.toml.")
app.add_typer(config_app, name="config")


@config_app.command("init")
def config_init(
    local: bool = Option(
        False, "--local",
        help="Gravar ./bibliotec.toml no diretório corrente (padrão: ~/.config/bibliotec/config.toml).",
    ),
) -> None:
    """Criar o arquivo config.toml comentado."""
    target = init_config_file(local=local)
    console.print(f"[green]Configuração gravada em:[/green] {target}")
    console.print("Edite o arquivo e preencha as chaves de API (permissão 0600 aplicada).")


@config_app.command("show")
def config_show(
    config: Optional[Path] = Option(
        None, "--config", help="Caminho para um config.toml customizado.",
    ),
) -> None:
    """Exibir a configuração ativa (mascarando as chaves de API)."""
    cfg = _load_config(config)
    table = Table(title="Configuração Ativa do BiblioTEC")
    table.add_column("Seção.Campo", style="cyan")
    table.add_column("Valor", style="magenta")
    g = cfg.general
    table.add_row("general.recursive", str(g.recursive))
    table.add_row("general.file_operation", g.file_operation)
    table.add_row("general.confidence_min", str(g.confidence_min))
    table.add_row("general.workers", str(g.workers))
    table.add_row("general.use_cache", str(g.use_cache))
    table.add_row("llm.provider", cfg.llm.provider)
    table.add_row("llm.model", cfg.llm.model)
    table.add_row("api_keys.gemini_api_key", mask_key(cfg.api_keys.gemini_api_key) or "(não definida)")
    table.add_row("api_keys.google_books_api_key", mask_key(cfg.api_keys.google_books_api_key) or "(não definida)")
    table.add_row("api_keys.openalex_polite_email", cfg.api_keys.openalex_polite_email or "(não definida)")
    console.print(table)


@config_app.command("path")
def config_path(
    config: Optional[Path] = Option(
        None, "--config", help="Caminho para um config.toml customizado.",
    ),
) -> None:
    """Exibir o caminho do arquivo de configuração carregado."""
    if config is not None:
        console.print(str(config.resolve()))
        return
    # Determinar qual arquivo seria carregado (local tem precedência sobre global).
    local = Path.cwd() / LOCAL_CONFIG_FILENAME
    if local.exists():
        console.print(str(local.resolve()))
    elif GLOBAL_CONFIG_PATH.exists():
        console.print(str(GLOBAL_CONFIG_PATH))
    else:
        console.print(str(GLOBAL_CONFIG_PATH))


# --------------------------------------------------------------------------- #
# Grupo: cache
# --------------------------------------------------------------------------- #
cache_app = typer.Typer(help="Gerenciar o cache SQLite local (~/.cache/bibliotec/state.db).")
app.add_typer(cache_app, name="cache")


@cache_app.command("clean")
@cache_app.command("clear")
def cache_clean() -> None:
    """Remover o banco de dados SQLite do cache local."""
    if CACHE_DB_PATH.exists():
        # Remover state.db e arquivos auxiliares (WAL, SHM).
        removed = []
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(CACHE_DB_PATH) + suffix)
            if p.exists():
                p.unlink()
                removed.append(p.name)
        if removed:
            console.print(f"[green]Cache limpo:[/green] {', '.join(removed)} removido(s) de {CACHE_DB_PATH}")
        else:
            console.print(f"[yellow]Cache já estava vazio:[/yellow] {CACHE_DB_PATH}")
    else:
        console.print(f"[yellow]Nenhum cache encontrado em:[/yellow] {CACHE_DB_PATH}")


@cache_app.command("status")
def cache_status() -> None:
    """Exibir informações sobre o cache SQLite local."""
    if CACHE_DB_PATH.exists():
        tamanho_kb = CACHE_DB_PATH.stat().st_size / 1024
        # Contar registros na tabela processed_files.
        import sqlite3
        conn = sqlite3.connect(str(CACHE_DB_PATH))
        try:
            cur = conn.execute("SELECT COUNT(*) FROM processed_files")
            registros = cur.fetchone()[0]
        finally:
            conn.close()
        console.print(f"[blue]Caminho:[/blue] {CACHE_DB_PATH}")
        console.print(f"[blue]Tamanho:[/blue] {tamanho_kb:.1f} KB")
        console.print(f"[blue]Registros:[/blue] {registros}")
    else:
        console.print(f"[yellow]Nenhum cache encontrado em:[/yellow] {CACHE_DB_PATH}")


@cache_app.command("path")
def cache_path() -> None:
    """Imprimir o caminho absoluto do banco de dados do cache."""
    console.print(str(CACHE_DB_PATH))


def main() -> None:
    """Ponto de entrada da CLI."""
    app()


if __name__ == "__main__":
    main()
