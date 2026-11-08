"""Abstração multiplataforma de integração com o sistema operacional.

Implementa a seção 5.4 (item 2) da especificação ``docs/designs/gui_spec.md``:
``os_integration.py`` encapsula todas as interações dependentes de sistema
operacional usando ``sys.platform`` e ``pathlib.Path``, sem jamais concatenar
strings com ``/`` manualmente.

Suporta macOS (``darwin``), Windows (``win32``) e Linux (``linux`` /
Wayland/X11 — GNOME/KDE).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

__all__ = [
    "open_file_in_os",
    "reveal_in_file_manager",
    "secure_chmod_600",
]


def _resolve(path: Path | str) -> Path:
    """Resolver o caminho para um Path absoluto, levantando se não existir."""
    p = Path(path)
    return p.resolve(strict=False)


def open_file_in_os(path: Path | str) -> None:
    """Abrir um arquivo (PDF / Markdown / etc.) no aplicativo padrão do SO.

    * macOS: ``subprocess.Popen(["open", str(path)])``
    * Windows: ``os.startfile(str(path))``
    * Linux: ``subprocess.Popen(["xdg-open", str(path)])``

    :param path: caminho do arquivo a abrir.
    :raises FileNotFoundError: se o caminho não existir no disco.
    :raises OSError: se o comando do SO não estiver disponível.
    """
    p = _resolve(path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")

    if sys.platform == "darwin":
        subprocess.Popen(["open", str(p)])
    elif sys.platform == "win32":
        os.startfile(str(p))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(p)])


def reveal_in_file_manager(path: Path | str) -> None:
    """Revelar (selecionar) um arquivo na pasta do gerenciador de arquivos.

    * macOS: ``subprocess.Popen(["open", "-R", str(path)])``
    * Windows: ``subprocess.Popen(["explorer", f"/select,{path}"])``
    * Linux: ``subprocess.Popen(["xdg-open", str(path.parent)])``

    :param path: caminho do arquivo a revelar.
    :raises FileNotFoundError: se o caminho não existir no disco.
    :raises OSError: se o comando do SO não estiver disponível.
    """
    p = _resolve(path)
    if not p.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {p}")

    if sys.platform == "darwin":
        subprocess.Popen(["open", "-R", str(p)])
    elif sys.platform == "win32":
        subprocess.Popen(["explorer", f"/select,{p}"])
    else:
        # xdg-open abre o diretório pai quando o alvo não é um diretório.
        subprocess.Popen(["xdg-open", str(p.parent)])


def secure_chmod_600(path: Path | str) -> None:
    """Aplicar permissão restrita ``0600`` (apenas o dono lê/escreve).

    Usado para o arquivo de configuração ``config.toml`` (``CONFIG_FILE_MODE``
    do :mod:`bibliotec.core.config`). Em sistemas POSIX (macOS/Linux) aplica
    ``os.chmod(path, 0o600)``; no Windows a operação é ignorada com segurança
    via ``try/except OSError``, pois ACLs POSIX não se aplicam.

    :param path: caminho do arquivo a proteger.
    """
    if sys.platform == "win32":
        return
    try:
        os.chmod(path, 0o600)
    except OSError:
        # Permissão não aplicável (sistema de arquivos sem suporte a ACL POSIX
        # ou usuário sem privilégios): ignorar com segurança.
        pass
