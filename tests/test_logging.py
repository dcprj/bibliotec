"""Testes para o módulo de logging (src/tomus/core/logging.py).

Cobre: setup_logging, redirecionamento para arquivo, comportamento
verbose=True/False e neutralização do logger do RapidOCR.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from tomus.core.logging import setup_logging, get_logger, _THIRD_PARTY_LOGGERS


def _apenas_stream_handlers_nao_arquivo(handlers):
    """Retornar handlers StreamHandler que NÃO são FileHandler (console de verdade)."""
    return [
        h for h in handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    ]


def test_setup_logging_cria_arquivo_log(tmp_path: Path):
    """setup_logging deve criar o arquivo de log especificado."""
    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=False, level=logging.INFO)

    assert log_file.exists()

    # Gravar uma mensagem para garantir conteúdo no arquivo.
    logger = logging.getLogger("tomus.teste_criacao")
    logger.info("mensagem de verificacao de criacao de arquivo")

    assert log_file.stat().st_size > 0  # agora deve ter conteúdo

    # Conteúdo deve conter a formatação esperada.
    texto = log_file.read_text(encoding="utf-8")
    assert "%(asctime)s" not in texto  # já foi renderizado pelo Formatter
    assert "[" in texto  # colchetes de levelname e name


def test_setup_logging_terminal_limpo_quando_verbose_false(tmp_path: Path, monkeypatch):
    """Com verbose=False, nenhum handler de console (StreamHandler não-arquivo) deve ser adicionado ao root."""
    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=False, level=logging.INFO)

    root_logger = logging.getLogger()
    console_handlers = _apenas_stream_handlers_nao_arquivo(root_logger.handlers)
    # Não deve haver StreamHandler de console (terminal limpo para Rich).
    assert console_handlers == []


def test_setup_logging_stream_handler_quando_verbose_true(tmp_path: Path, monkeypatch):
    """Com verbose=True, um StreamHandler de console deve ser adicionado ao root."""
    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=True, level=logging.DEBUG)

    root_logger = logging.getLogger()
    console_handlers = _apenas_stream_handlers_nao_arquivo(root_logger.handlers)
    assert len(console_handlers) == 1


def test_setup_logging_formato_arquivo(tmp_path: Path):
    """O arquivo de log deve usar a formatação %(asctime)s [%(levelname)s] [%(name)s] %(message)s."""
    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=False, level=logging.DEBUG)

    logger = logging.getLogger("tomus.teste")
    logger.debug("mensagem de teste de formato")

    texto = log_file.read_text(encoding="utf-8")
    assert "mensagem de teste de formato" in texto
    assert "[DEBUG]" in texto
    assert "[tomus.teste]" in texto


def test_setup_logging_nivel_filtra_mensagens(tmp_path: Path):
    """Mensagens abaixo do nível configurado não devem aparecer no arquivo."""
    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=False, level=logging.ERROR)

    logger = logging.getLogger("tomus.teste_nivel")
    logger.debug("debug deve ser ignorado")
    logger.info("info deve ser ignorado")
    logger.error("erro deve aparecer")

    texto = log_file.read_text(encoding="utf-8")
    assert "debug deve ser ignorado" not in texto
    assert "info deve ser ignorado" not in texto
    assert "erro deve aparecer" in texto


def test_setup_logging_silencia_terceiros(tmp_path: Path, monkeypatch):
    """Loggers de terceiros (exceto RapidOCR especial) devem ter propagate=True."""
    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=False, level=logging.WARNING)

    for nome in _THIRD_PARTY_LOGGERS:
        if nome == "RapidOCR":
            continue  # RapidOCR é tratado separadamente (propagate=False)
        logger = logging.getLogger(nome)
        assert logger.propagate is True, f"{nome} deve ter propagate=True"


def test_setup_logging_rapidocr_handlers_limpos(tmp_path: Path, monkeypatch):
    """O logger RapidOCR deve ter seus handlers limpos e o FileHandler anexado."""
    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=False, level=logging.INFO)

    rapidocr_logger = logging.getLogger("RapidOCR")
    # Não deve haver StreamHandler de console (não-arquivo).
    console_handlers = _apenas_stream_handlers_nao_arquivo(rapidocr_logger.handlers)
    assert console_handlers == []
    # Deve ter pelo menos um FileHandler.
    file_handlers = [
        h for h in rapidocr_logger.handlers if isinstance(h, logging.FileHandler)
    ]
    assert len(file_handlers) >= 1
    # propagate deve ser False para evitar dupla gravação.
    assert rapidocr_logger.propagate is False


def test_get_logger_retorna_logger_nomeado():
    """get_logger deve retornar um logger nomeado dentro de tomus."""
    logger = get_logger("meu_modulo")
    assert logger.name == "tomus.meu_modulo"
    assert isinstance(logger, logging.Logger)


def test_variaveis_ambiente_definidas(tmp_path: Path, monkeypatch):
    """As variáveis de ambiente defensivas devem ser definidas."""
    # Limpar antes para garantir que o teste valide a definição.
    for var in ("GLOG_minloglevel", "TORCH_CPP_LOG_LEVEL", "TOKENIZERS_PARALLELISM", "HF_HUB_DISABLE_PROGRESS_BARS"):
        monkeypatch.delenv(var, raising=False)

    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=False, level=logging.INFO)

    assert os.environ["GLOG_minloglevel"] == "2"
    assert os.environ["TORCH_CPP_LOG_LEVEL"] == "ERROR"
    assert os.environ["TOKENIZERS_PARALLELISM"] == "false"
    assert os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] == "1"


def test_setup_logging_idempotente(tmp_path: Path):
    """Chamar setup_logging duas vezes não deve duplicar handlers."""
    log_file = tmp_path / "tomus.log"
    setup_logging(log_file=log_file, verbose=False, level=logging.INFO)
    setup_logging(log_file=log_file, verbose=False, level=logging.INFO)

    root_logger = logging.getLogger()
    file_handlers = [
        h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
        and Path(h.baseFilename).resolve() == log_file.resolve()
    ]
    assert len(file_handlers) == 1
