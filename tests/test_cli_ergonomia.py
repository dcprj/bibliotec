"""Testes de ergonomia da CLI (raiz -o/-d e organize com posições/opções).

Usa typer.testing.CliRunner para simular invocações diretas do terminal,
mockando _executar_organize para não processar PDFs reais.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import shutil

from typer.testing import CliRunner

from tomus.cli.main import app
from tomus.core.cache import FileCache
from tomus.core.config import AppConfig
from tomus.core.pipeline import run_pipeline
from tomus.core.llm import MockLLMProvider

runner = CliRunner()


def _origem_destino() -> tuple[Path, Path]:
    return Path("/tmp/bib_origem"), Path("/tmp/bib_destino")


def _criar_pdf(caminho: Path, texto: str = "Título de teste Autor Silva, João 2020") -> None:
    """Criar um PDF sintético de uma página."""
    import fitz  # PyMuPDF

    doc = fitz.open()
    pagina = doc.new_page()
    pagina.insert_text((72, 72), texto)
    doc.save(str(caminho))
    doc.close()


def test_raiz_curto_o_d_dry_run_chama_organize():
    """tomus -o <origem> -d <destino> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("tomus.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["-o", str(origem), "-d", str(destino), "--dry-run", "--no-cache"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino
    assert kwargs["dry_run"] is True
    assert kwargs["no_cache"] is True


def test_raiz_longo_origem_destino_dry_run_chama_organize():
    """tomus --origem <origem> --destino <destino> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("tomus.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["--origem", str(origem), "--destino", str(destino), "--dry-run"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino
    assert kwargs["dry_run"] is True


def test_raiz_sem_subcomando_sem_opcoes_exibe_help():
    """tomus (sem nada) exibe o help."""
    result = runner.invoke(app, [])
    # O Typer pode sair com código 0 ou 2 quando nenhum argumento é passado;
    # o importante é que o help seja exibido.
    assert result.exit_code in (0, 2)
    assert "Organizador Acadêmico" in result.output or "Usage:" in result.output


def test_raiz_somente_origem_erro():
    """tomus -o <origem> (sem -d) exibe erro e sai com código != 0."""
    origem, _ = _origem_destino()
    result = runner.invoke(app, ["-o", str(origem)])
    assert result.exit_code != 0
    assert "necessário informar" in result.output


def test_raiz_somente_destino_erro():
    """tomus -d <destino> (sem -o) exibe erro e sai com código != 0."""
    _, destino = _origem_destino()
    result = runner.invoke(app, ["-d", str(destino)])
    assert result.exit_code != 0
    assert "necessário informar" in result.output


def test_organize_posicionais_chama_organize():
    """tomus organize <ORIGEM> <DESTINO> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("tomus.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["organize", str(origem), str(destino), "--dry-run"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino


def test_organize_opcoes_o_d_chama_organize():
    """tomus organize -o <origem> -d <destino> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("tomus.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["organize", "-o", str(origem), "-d", str(destino), "--dry-run"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino


def test_organize_opcoes_source_target_chama_organize():
    """tomus organize --source <origem> --target <destino> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("tomus.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["organize", "--source", str(origem), "--target", str(destino), "--dry-run"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino


def test_organize_opcoes_precedem_posicionais():
    """Quando opções e posicionais são passados, as opções vencem."""
    origem_opt, destino_opt = _origem_destino()
    origem_pos = Path("/tmp/pos_origem")
    destino_pos = Path("/tmp/pos_destino")
    with patch("tomus.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(
            app,
            ["organize", "--origem", str(origem_opt), "--destino", str(destino_opt),
             str(origem_pos), str(destino_pos), "--dry-run"],
        )
    assert result.exit_code == 0, result.output
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem_opt
    assert kwargs["target_dir"] == destino_opt


def test_organize_falta_destino_erro():
    """tomus organize -o <origem> (sem destino) exibe erro."""
    origem, _ = _origem_destino()
    result = runner.invoke(app, ["organize", "-o", str(origem)])
    assert result.exit_code != 0
    assert "necessário informar" in result.output


def test_organize_sem_nada_erro():
    """tomus organize (sem origem nem destino) exibe erro."""
    result = runner.invoke(app, ["organize"])
    assert result.exit_code != 0
    assert "necessário informar" in result.output


def test_flags_adicionais_sao_repassadas():
    """--move, --workers, --confidence-min, --model são repassados ao organize."""
    origem, destino = _origem_destino()
    with patch("tomus.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(
            app,
            ["-o", str(origem), "-d", str(destino), "--move", "--workers", "4",
             "--confidence-min", "0.8", "--model", "gemini-2.5-pro", "--dry-run"],
        )
    assert result.exit_code == 0, result.output
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["workers"] == 4
    assert kwargs["confidence_min"] == 0.8
    assert kwargs["model"] == "gemini-2.5-pro"


def test_emit_with_progress_nao_levanta_nameerror_e_avanca_progresso(tmp_path: Path):
    """Validar que emit_with_progress (dentro de run_pipeline) não levanta NameError
    e que eventos terminais (incluindo duplicate_skipped) são recebidos pelo callback."""
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()

    # Dois PDFs idênticos -> um organizado, um duplicate_skipped.
    _criar_pdf(source / "a.pdf")
    import shutil
    shutil.copy2(source / "a.pdf", source / "b.pdf")

    cfg = AppConfig()
    eventos_recebidos: list = []

    def callback(event):
        eventos_recebidos.append(event)

    summary = run_pipeline(
        source_dir=source,
        target_dir=target,
        config=cfg,
        provider=MockLLMProvider(),
        workers=1,
        cache=FileCache(enabled=False),  # desabilitar cache para forçar _resolve_collision
        event_callback=callback,
    )

    # Nenhum NameError deve ter sido levantado (se houvesse, run_pipeline falharia).
    assert summary.total_scanned == 2

    # Devem existir eventos terminais.
    statuses_terminais = {
        e.status for e in eventos_recebidos
        if e.status in ("organized", "manual_review", "error", "duplicate_skipped")
    }
    assert len(statuses_terminais) >= 1, (
        "Nenhum evento terminal foi emitido pelo callback"
    )

    # Se houver duplicate_skipped, ele também deve contar como terminal.
    if summary.duplicate_skipped_count > 0:
        assert "duplicate_skipped" in statuses_terminais
