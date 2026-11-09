"""Sistema de Logs Profissional do BiblioTEC (Item [LOG-01]).

Configura logging estruturado que redireciona logs detalhados para arquivo,
mantendo o terminal 100% limpo para a barra de progresso do Rich.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

# Loggers de terceiros a serem silenciados/redirecionados para arquivo.
_THIRD_PARTY_LOGGERS = (
    "RapidOCR",
    "docling",
    "docling_core",
    "transformers",
    "torch",
    "urllib3",
    "httpx",
    "fitz",
)

# Formato padrão para o arquivo de log.
_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"


def setup_logging(
    log_file: Path | str = "bibliotec.log",
    verbose: bool = False,
    level: int = logging.INFO,
) -> None:
    """Configurar o sistema de logs do BiblioTEC.

    Por padrão (verbose=False), logs detalhados vão para o arquivo
    ``bibliotec.log`` e o terminal fica 100% limpo para a barra de progresso
    do Rich. Quando verbose=True, um StreamHandler também é anexado ao console.

    Parâmetros:
        log_file: caminho do arquivo de log (padrão: bibliotec.log).
        verbose: se True, também exibe logs no console.
        level: nível de logging (padrão: logging.INFO).
    """
    # --- Variáveis de ambiente defensivas para silenciar terceiros -----------
    os.environ["GLOG_minloglevel"] = "2"
    os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

    # --- Root logger ---------------------------------------------------------
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remover handlers existentes do root (evita duplicação em recarregamento).
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # FileHandler sempre ativo -> arquivo de log.
    # Em caso de erro de permissão/disco (ex: diretório raiz '/', Program Files
    # protegido no Windows), fallback silencioso para NullHandler para garantir
    # que NENHUM erro de log impeça a inicialização da aplicação.
    log_path = Path(log_file)
    file_handler = None
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        root_logger.addHandler(file_handler)
    except Exception:
        # Fallback: adicionar NullHandler para não quebrar a aplicação.
        root_logger.addHandler(logging.NullHandler())
        # Tentar gravar aviso em stderr sem depender do sistema de logging.
        import sys as _sys
        _sys.stderr.write(
            f"[bibliotec] Aviso: não foi possível criar arquivo de log em "
            f"{log_path}. Logs serão ignorados.\n"
        )

    # StreamHandler apenas quando verbose=True.
    if verbose:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        root_logger.addHandler(stream_handler)

    # --- Silenciar loggers de terceiros --------------------------------------
    for name in _THIRD_PARTY_LOGGERS:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = True  # faz com que mensagens subam para o root

    # --- Caso especial: RapidOCR --------------------------------------------
    # O logger "RapidOCR" (em rapidocr.utils.log) adiciona seu próprio
    # console_handler e seta propagate=False. Precisamos limpar seus handlers
    # e anexar o FileHandler nele (ou forçar propagação).
    rapidocr_logger = logging.getLogger("RapidOCR")
    rapidocr_logger.setLevel(level)
    for handler in list(rapidocr_logger.handlers):
        rapidocr_logger.removeHandler(handler)
    if file_handler is not None:
        rapidocr_logger.addHandler(file_handler)
    rapidocr_logger.propagate = False  # evita dupla gravação via root

    # --- Log do próprio BiblioTEC -------------------------------------------
    biblio_logger = logging.getLogger("bibliotec")
    biblio_logger.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Retornar um logger nomeado do pacote bibliotec."""
    return logging.getLogger(f"bibliotec.{name}")
