"""Testes de ergonomia da CLI (raiz -o/-d e organize com posições/opções).

Usa typer.testing.CliRunner para simular invocações diretas do terminal,
mockando _executar_organize para não processar PDFs reais.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from bibliotec.cli.main import app

runner = CliRunner()


def _origem_destino() -> tuple[Path, Path]:
    return Path("/tmp/bib_origem"), Path("/tmp/bib_destino")


def test_raiz_curto_o_d_dry_run_chama_organize():
    """bibliotec -o <origem> -d <destino> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("bibliotec.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["-o", str(origem), "-d", str(destino), "--dry-run", "--no-cache"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino
    assert kwargs["dry_run"] is True
    assert kwargs["no_cache"] is True


def test_raiz_longo_origem_destino_dry_run_chama_organize():
    """bibliotec --origem <origem> --destino <destino> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("bibliotec.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["--origem", str(origem), "--destino", str(destino), "--dry-run"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino
    assert kwargs["dry_run"] is True


def test_raiz_sem_subcomando_sem_opcoes_exibe_help():
    """bibliotec (sem nada) exibe o help."""
    result = runner.invoke(app, [])
    # O Typer pode sair com código 0 ou 2 quando nenhum argumento é passado;
    # o importante é que o help seja exibido.
    assert result.exit_code in (0, 2)
    assert "Organizador Acadêmico" in result.output or "Usage:" in result.output


def test_raiz_somente_origem_erro():
    """bibliotec -o <origem> (sem -d) exibe erro e sai com código != 0."""
    origem, _ = _origem_destino()
    result = runner.invoke(app, ["-o", str(origem)])
    assert result.exit_code != 0
    assert "necessário informar" in result.output


def test_raiz_somente_destino_erro():
    """bibliotec -d <destino> (sem -o) exibe erro e sai com código != 0."""
    _, destino = _origem_destino()
    result = runner.invoke(app, ["-d", str(destino)])
    assert result.exit_code != 0
    assert "necessário informar" in result.output


def test_organize_posicionais_chama_organize():
    """bibliotec organize <ORIGEM> <DESTINO> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("bibliotec.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["organize", str(origem), str(destino), "--dry-run"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino


def test_organize_opcoes_o_d_chama_organize():
    """bibliotec organize -o <origem> -d <destino> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("bibliotec.cli.main._executar_organize") as mock_exec:
        result = runner.invoke(app, ["organize", "-o", str(origem), "-d", str(destino), "--dry-run"])
    assert result.exit_code == 0, result.output
    mock_exec.assert_called_once()
    kwargs = mock_exec.call_args.kwargs
    assert kwargs["source_dir"] == origem
    assert kwargs["target_dir"] == destino


def test_organize_opcoes_source_target_chama_organize():
    """bibliotec organize --source <origem> --target <destino> --dry-run executa organize."""
    origem, destino = _origem_destino()
    with patch("bibliotec.cli.main._executar_organize") as mock_exec:
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
    with patch("bibliotec.cli.main._executar_organize") as mock_exec:
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
    """bibliotec organize -o <origem> (sem destino) exibe erro."""
    origem, _ = _origem_destino()
    result = runner.invoke(app, ["organize", "-o", str(origem)])
    assert result.exit_code != 0
    assert "necessário informar" in result.output


def test_organize_sem_nada_erro():
    """bibliotec organize (sem origem nem destino) exibe erro."""
    result = runner.invoke(app, ["organize"])
    assert result.exit_code != 0
    assert "necessário informar" in result.output


def test_flags_adicionais_sao_repassadas():
    """--move, --workers, --confidence-min, --model são repassados ao organize."""
    origem, destino = _origem_destino()
    with patch("bibliotec.cli.main._executar_organize") as mock_exec:
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
