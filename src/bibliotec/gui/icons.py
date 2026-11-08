"""Renderizador de ícones vetoriais SVG em memória — BiblioTEC GUI.

Implementa o **Sistema de Ícones Vetoriais Embutidos** da seção 2.3 da
especificação ``docs/designs/gui_spec.md``:

* Nenhum arquivo externo ``.png`` nem emoji é utilizado.
* Primitivas SVG puras com viewBox ``0 0 24 24``, traço ``1.5px``,
  ``stroke-linecap="round"``, ``stroke-linejoin="round"`` e sem preenchimento
  pesado (``fill="none"``).
* Renderização em memória via ``QSvgRenderer`` + ``QPainter`` sobre
  ``QPixmap`` com ``devicePixelRatio`` nativo (suporte Retina ``@2x`` / ``@3x``).
* A cor de cada ícone é parametrizada pela cor de texto/acento do tema ativo.
"""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

__all__ = [
    "ICON_NAMES",
    "render_icon",
    "render_pixmap",
    "svg_for",
]


# --------------------------------------------------------------------------- #
# Primitivas SVG vetoriais (viewBox 0 0 24 24, traço 1.5px, sem preenchimento)
# --------------------------------------------------------------------------- #

_SVG: Final[dict[str, str]] = {
    # folder-input: Pasta com seta de entrada (Origem).
    "folder-input": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M2 21V8a2 2 0 0 1 2-2h6l2 2h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/>'
        '<path d="M12 8l-3 3 3 3"/>'
        "</svg>"
    ),
    # folder-output: Pasta com marcador de árvore (Destino).
    "folder-output": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M2 21V8a2 2 0 0 1 2-2h6l2 2h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/>'
        '<path d="M22 11h-4l-3 3 3 3h4"/>'
        "</svg>"
    ),
    # play-run: Triângulo geométrico técnico (Organizar Acervo).
    "play-run": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<polygon points="8 5 19 12 8 19"/>'
        "</svg>"
    ),
    # stop-square: Quadrado sólido interno (Interromper / Cancelar lote).
    "stop-square": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="8" y="8" width="8" height="8" rx="1"/>'
        "</svg>"
    ),
    # rotate-ccw: Seta circular anti-horária (Retomar Sessão).
    "rotate-ccw": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M1 12a9 9 0 1 0 9-9 9.7 9.7 0 0 0-0.74 2.91L10 4"/>'
        "</svg>"
    ),
    # sliders-settings: Três trilhos horizontais com seletores (Preferências).
    "sliders-settings": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<line x1="12" y1="7" x2="18" y2="7"/>'
        '<line x1="6" y1="12" x2="18" y2="12"/>'
        '<line x1="6" y1="17" x2="14" y2="17"/>'
        '<circle cx="12" cy="7" r="1" fill="currentColor"/>'
        '<circle cx="18" cy="12" r="1" fill="currentColor"/>'
        '<circle cx="14" cy="17" r="1" fill="currentColor"/>'
        "</svg>"
    ),
    # database-cache: Cilindro técnico discreto (Cache SQLite).
    "database-cache": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M5 17h14c0 2.21 3.582 4 8 4s8-1.79 8-4-3.582-4-8-4H5c-4.418 0-8 1.79-8 4s3.582 4 8 4z"/>'
        '<ellipse cx="12" cy="13" rx="8" ry="2"/>'
        "</svg>"
    ),
    # check-circle: Círculo com marca de verificação (Status: Organizado).
    "check-circle": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M8 12l2 2 4-4"/>'
        "</svg>"
    ),
    # alert-triangle: Triângulo com ponto de exclamação (Revisão Manual / Teto > 20%).
    "alert-triangle": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
        "</svg>"
    ),
    # copy-layers: Dois retângulos sobrepostos (Duplicata / Copiar Citação ABNT).
    "copy-layers": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="8" y="8" width="10" height="10" rx="1" ry="1"/>'
        '<rect x="3" y="3" width="10" height="10" rx="1" ry="1"/>'
        "</svg>"
    ),
    # file-slash: Folha com traço diagonal (Ignorado Não-PDF).
    "file-slash": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14 2v6h6"/>'
        '<path d="M17 22H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8l6 6z"/>'
        '<path d="M22 22l-20-20"/>'
        "</svg>"
    ),
    # x-octagon: Octógono com X (Status: Erro).
    "x-octagon": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M14.75 2H9.25a1 1 0 0 0-.84 1.55L6 4.68V7.32a1 1 0 0 0 .84 1.55l3.75 1.5L6.92 17.32a1 1 0 0 0 .84 1.55h5.5a1 1 0 0 0 .84-1.55L18 10.68V8.04a1 1 0 0 0-.84-1.55l-3.75-1.5L14.09 4.68A1 1 0 0 0 13.25 3.15z"/>'
        '<path d="m15 7 3 3M15 10l-3-3"/>'
        "</svg>"
    ),
    # external-link: Caixa com seta diagonal superior direita (Abrir PDF).
    "external-link": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M13 2H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>'
        '<polyline points="18 15 21 12 18 9"/>'
        '<path d="M18 15h-6a2 2 0 0 1-2-2V6"/>'
        "</svg>"
    ),
    # folder-reveal: Lupa sobre pasta (Mostrar no Finder / Explorer).
    "folder-reveal": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M2 21V8a2 2 0 0 1 2-2h6l2 2h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2z"/>'
        '<circle cx="17" cy="17" r="3"/>'
        '<path d="M20 20l1.5 1.5"/>'
        "</svg>"
    ),
    # scan-ocr: Moldura de foco com linhas de texto internas (OCR Docling).
    "scan-ocr": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="3" y="5" width="18" height="14" rx="1"/>'
        '<path d="M7 9h4M7 12h5M12 12h3M7 15h3M10 15h2M16 15h2"/>'
        "</svg>"
    ),
    # cpu-provider: Chip geométrico (Provedor LLM ativo / Fallback).
    "cpu-provider": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<rect x="5" y="5" width="14" height="14" rx="2" ry="2"/>'
        '<line x1="9" y1="9" x2="9" y2="9.01"/>'
        '<line x1="15" y1="9" x2="15" y2="9.01"/>'
        '<line x1="9" y1="15" x2="9" y2="15.01"/>'
        '<line x1="15" y1="15" x2="15" y2="15.01"/>'
        "</svg>"
    ),
    # catalog-empty: Catálogo com folha (Empty State: nenhum documento selecionado).
    "catalog-empty": (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="currentColor" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M12 2v20M2 12h20"/>'
        '<rect x="3" y="3" width="7" height="7" rx="1"/>'
        '<rect x="14" y="3" width="7" height="7" rx="1"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1"/>'
        '<rect x="14" y="14" width="7" height="7" rx="1"/>'
        "</svg>"
    ),
}

ICON_NAMES: Final[tuple[str, ...]] = tuple(sorted(_SVG.keys()))


def svg_for(name: str) -> str:
    """Retornar a string SVG bruta de um ícone pelo nome.

    :param name: nome do ícone (ex: ``"folder-input"``, ``"play-run"``).
    :raises KeyError: se o nome não existir em :data:`ICON_NAMES`.
    """
    if name not in _SVG:
        raise KeyError(f"Ícone desconhecido: {name!r}. Disponíveis: {ICON_NAMES}")
    return _SVG[name]


def render_pixmap(
    name: str,
    color: QColor | str | None = None,
    size_px: int = 24,
    dpr: float | None = None,
) -> QPixmap:
    """Renderizar um ícone SVG em um ``QPixmap`` com suporte Retina.

    O SVG é renderizado em memória via ``QSvgRenderer`` sobre um
    ``QPixmap`` cujo ``devicePixelRatio`` é ajustado para ``dpr`` (padrão:
    ``devicePixelRatio()`` da aplicação ou ``1.0``), garantindo nitidez em
    telas Retina (``@2x`` / ``@3x``) sem arquivos externos.

    :param name: nome do ícone (ver :data:`ICON_NAMES`).
    :param color: cor do traço (``QColor``, string hex ou ``None`` para usar
        a cor do texto da aplicação).
    :param size_px: tamanho base em pixels lógicos (padrão ``24``).
    :param dpr: device pixel ratio (padrão: ``QApplication.devicePixelRatio()``
        ou ``1.0`` quando não houver aplicação instanciada).
    :returns: ``QPixmap`` pronto para ser colocado em um ``QIcon``.
    """
    if dpr is None:
        app = QApplication.instance()
        dpr = app.devicePixelRatio() if app is not None else 1.0

    svg_bytes = svg_for(name).encode("utf-8")
    renderer = QSvgRenderer(svg_bytes)

    logical_size = size_px
    pixel_size = max(1, int(round(logical_size * dpr)))
    pixmap = QPixmap(pixel_size, pixel_size)
    pixmap.setDevicePixelRatio(dpr)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    # O QSvgRenderer escala o SVG para preencher o target_rect informado em
    # render(); não há setDefaultSize no PySide6 6.x — o rect do pixmap define
    # o tamanho de saída (físico, já considerando o devicePixelRatio).
    renderer.render(painter, QRectF(0, 0, pixel_size, pixel_size))

    if color is not None:
        qcolor = QColor(color) if isinstance(color, str) else color
        # Recolorir o ícone: o traço é renderizado em currentColor (preto);
        # SourceIn substitui apenas os pixels não-transparentes pela cor alvo.
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), qcolor)

    painter.end()
    return pixmap


def render_icon(
    name: str,
    color: QColor | str | None = None,
    size_px: int = 24,
    dpr: float | None = None,
) -> QIcon:
    """Retornar um ``QIcon`` a partir de um ícone SVG em memória.

    :param name: nome do ícone (ver :data:`ICON_NAMES`).
    :param color: cor do traço (``QColor``, string hex ou ``None`` para usar
        a cor do texto da aplicação).
    :param size_px: tamanho base em pixels lógicos (padrão ``24``).
    :param dpr: device pixel ratio (padrão: ``QApplication.devicePixelRatio()``
        ou ``1.0`` quando não houver aplicação instanciada).
    :returns: ``QIcon`` com o pixmap renderizado (Retina-aware via
        ``devicePixelRatio``).
    """
    pixmap = render_pixmap(name, color=color, size_px=size_px, dpr=dpr)
    icon = QIcon()
    icon.addPixmap(pixmap)
    return icon
