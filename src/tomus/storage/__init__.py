"""Camada de armazenamento e organização de arquivos (Itens 19 a 21).

Exporta o formatador de nomes (format_academic_filename) e o
materializador de diretórios (LibraryOrganizer).
"""

from tomus.storage.companion import generate_companion_markdown
from tomus.storage.namer import format_academic_filename
from tomus.storage.organizer import LibraryOrganizer

__all__ = [
    "format_academic_filename",
    "LibraryOrganizer",
    "generate_companion_markdown",
]
