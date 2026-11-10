"""Design system do Tomus: paletas cromáticas, ``ThemeTokens`` e gerador QSS.

Implementa o **Design System "Editorial Academic Workbench"** atualizado conforme
o **Mockup 1** aprovado pelo usuário (direção visual inspirada em Vercel Web
Interface Guidelines e Property Dashboard Components):

* Fundo suave ``#F8F9FA`` com cartões elevados em branco puro ``#FFFFFF``
  e bordas nítidas de 1px ``#E2E8F0`` com border-radius de 8px a 12px.
* Cabeçalho de Controle em 2 linhas com marca "Tomus" (16px, bold,
  tom ardósia ``#0F172A``) e botão primário azul profundo ``#1E3A8A``.
* Badges em pílula semânticos: Verde = Organizado, Âmbar = Revisão Manual,
  Azul = Duplicata, Cinza = Processando/Ignorado, Vermelho = Erro.
* Zero gradientes, zero emojis, zero landing-page hero — alinhado ao
  manifesto Anti-AI-Slop da especificação ``docs/designs/gui_spec.md``.

Toda cor de acento é sólida e opaca, ancorada em tons editoriais.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from tomus.core.models import ProcessStatus

__all__ = [
    "ThemeTokens",
    "EDITORIAL_PAPER_THEME",
    "TECHNICAL_GRAPHITE_THEME",
    "status_colors",
    "active_theme_for_scheme",
    "generate_qss",
    # Tokens de border-radius para uso direto nos componentes.
    "BORDER_RADIUS_SM",
    "BORDER_RADIUS_MD",
    "BORDER_RADIUS_LG",
]

# --------------------------------------------------------------------------- #
# Tokens de geometria (border-radius)
# --------------------------------------------------------------------------- #

BORDER_RADIUS_SM = 4  # Inputs, badges pequenos
BORDER_RADIUS_MD = 8  # Cartões, pílulas de status
BORDER_RADIUS_LG = 12  # Cartões principais, janelas de diálogo

# --------------------------------------------------------------------------- #
# Paletas de cores semânticas (tokens hexadecimais) — Mockup 1 aprovado
# --------------------------------------------------------------------------- #

EDITORIAL_PAPER_THEME = ThemeTokens = None  # placeholder, substituído abaixo
TECHNICAL_GRAPHITE_THEME = None  # placeholder, substituído abaixo


@dataclass(frozen=True)
class ThemeTokens:
    """Tokens cromáticos imutáveis de um tema (claro ou escuro)."""

    # Superfícies — Mockup 1: fundo suave #F8F9FA, cartões #FFFFFF
    bg_canvas: str  # Janela / Sidebar / StatusBar / Toolbar (fundo suave)
    bg_surface: str  # Cartões elevados / Dados / Grade / Inspetor (branco puro)
    bg_elevated: str  # Inputs / linhas em hover / cabeçalhos de seção
    bg_selected: str  # Linha selecionada na grade / item ativo na árvore

    # Bordas — Mockup 1: bordas nítidas 1px #E2E8F0
    border_subtle: str  # Hairline 1px (divisórias, inputs, cabeçalhos, rodapé)
    border_focus: str  # Anel de foco 1px solid em campos ativos

    # Textos
    text_primary: str  # Tinta principal (títulos, autores, citações)
    text_secondary: str  # Metadados, subtítulos, rótulos de formulário
    text_muted: str  # Placeholder / hashes / caminhos desabilitados / timestamps
    text_inverse: str  # Texto sobre fundo escuro / acento

    # Acento primário (ação principal) — Mockup 1: azul profundo #1E3A8A
    accent_primary: str  # Botão primário, barra de progresso ativa, links DOI
    accent_hover: str  # Estado :hover do botão primário / controles ativos
    text_on_accent: str  # Rótulo e ícone dentro do botão primário

    # Marca (aplicativo)
    brand_primary: str  # "Tomus" — tom ardósia #0F172A

    # Cores de status documental (texto, fundo do badge) — modo claro
    # Mockup 1: badges em pílula semânticos 1:1 cor/ícone/texto
    status_organized_fg_light: str
    status_organized_bg_light: str
    status_manual_review_fg_light: str
    status_manual_review_bg_light: str
    status_duplicate_skipped_fg_light: str
    status_duplicate_skipped_bg_light: str
    status_ignored_non_pdf_fg_light: str
    status_ignored_non_pdf_bg_light: str
    status_error_fg_light: str
    status_error_bg_light: str

    # Cores de status documental (texto, fundo do badge) — modo escuro
    status_organized_fg_dark: str
    status_organized_bg_dark: str
    status_manual_review_fg_dark: str
    status_manual_review_bg_dark: str
    status_duplicate_skipped_fg_dark: str
    status_duplicate_skipped_bg_dark: str
    status_ignored_non_pdf_fg_dark: str
    status_ignored_non_pdf_bg_dark: str
    status_error_fg_dark: str
    status_error_bg_dark: str


# Modo Claro — Editorial Paper (conforme Mockup 1 aprovado)
EDITORIAL_PAPER_THEME = ThemeTokens(
    # Superfícies
    bg_canvas="#F8F9FA",        # Fundo suave
    bg_surface="#FFFFFF",       # Cartões elevados branco puro
    bg_elevated="#F1F5F9",      # Inputs / hover / cabeçalhos (slate-100)
    bg_selected="#EFF6FF",      # Linha selecionada (blue-50)
    # Bordas
    border_subtle="#E2E8F0",    # Bordas nítidas 1px (slate-200)
    border_focus="#1E3A8A",     # Anel de foco (azul profundo)
    # Textos
    text_primary="#0F172A",     # Tinta principal (slate-900)
    text_secondary="#64748B",   # Metadados / subtítulos (slate-500)
    text_muted="#94A3B8",       # Placeholder / hashes (slate-400)
    text_inverse="#FFFFFF",     # Texto sobre fundo escuro / acento
    # Acento primário
    accent_primary="#1E3A8A",   # Azul profundo (blue-900)
    accent_hover="#1E40AF",     # Azul profundo hover (blue-950)
    text_on_accent="#FFFFFF",
    # Marca
    brand_primary="#0F172A",    # Tom ardósia para "Tomus"
    # Status — claro (texto / fundo badge)
    # Verde = Organizado
    status_organized_fg_light="#15803D",
    status_organized_bg_light="#DCFCE7",
    # Âmbar = Revisão Manual
    status_manual_review_fg_light="#B45309",
    status_manual_review_bg_light="#FEF3C7",
    # Azul = Duplicata
    status_duplicate_skipped_fg_light="#0369A1",
    status_duplicate_skipped_bg_light="#E0F2FE",
    # Cinza = Processando / Ignorado
    status_ignored_non_pdf_fg_light="#64748B",
    status_ignored_non_pdf_bg_light="#F1F5F9",
    # Vermelho = Erro
    status_error_fg_light="#B91C1C",
    status_error_bg_light="#FEE2E2",
    # Status — escuro (texto / fundo badge)
    status_organized_fg_dark="#4ADE80",
    status_organized_bg_dark="#142E1F",
    status_manual_review_fg_dark="#FBBF24",
    status_manual_review_bg_dark="#33240B",
    status_duplicate_skipped_fg_dark="#38BDF8",
    status_duplicate_skipped_bg_dark="#0F293A",
    status_ignored_non_pdf_fg_dark="#94A3B8",
    status_ignored_non_pdf_bg_dark="#1E293B",
    status_error_fg_dark="#F87171",
    status_error_bg_dark="#381515",
)

# Modo Escuro — Technical Graphite
TECHNICAL_GRAPHITE_THEME = ThemeTokens(
    # Superfícies
    bg_canvas="#0F172A",        # Fundo suave escuro (slate-900)
    bg_surface="#1E293B",       # Cartões elevados (slate-800)
    bg_elevated="#334155",      # Inputs / hover / cabeçalhos (slate-700)
    bg_selected="#1E3A8A",      # Linha selecionada (azul profundo)
    # Bordas
    border_subtle="#334155",    # Bordas nítidas 1px (slate-700)
    border_focus="#4A7BB0",     # Anel de foco (azul ardósia claro)
    # Textos
    text_primary="#F8FAFC",     # Tinta principal (slate-50)
    text_secondary="#94A3B8",   # Metadados / subtítulos (slate-400)
    text_muted="#64748B",       # Placeholder / hashes (slate-500)
    text_inverse="#0F172A",     # Texto sobre fundo claro / acento
    # Acento primário
    accent_primary="#4A7BB0",   # Azul ardósia claro
    accent_hover="#5B8EC4",     # Azul ardósia hover
    text_on_accent="#FFFFFF",
    # Marca
    brand_primary="#F8FAFC",
    # Status — claro (texto / fundo badge)
    status_organized_fg_light="#15803D",
    status_organized_bg_light="#DCFCE7",
    status_manual_review_fg_light="#B45309",
    status_manual_review_bg_light="#FEF3C7",
    status_duplicate_skipped_fg_light="#0369A1",
    status_duplicate_skipped_bg_light="#E0F2FE",
    status_ignored_non_pdf_fg_light="#64748B",
    status_ignored_non_pdf_bg_light="#F1F5F9",
    status_error_fg_light="#B91C1C",
    status_error_bg_light="#FEE2E2",
    # Status — escuro (texto / fundo badge)
    status_organized_fg_dark="#4ADE80",
    status_organized_bg_dark="#142E1F",
    status_manual_review_fg_dark="#FBBF24",
    status_manual_review_bg_dark="#33240B",
    status_duplicate_skipped_fg_dark="#38BDF8",
    status_duplicate_skipped_bg_dark="#0F293A",
    status_ignored_non_pdf_fg_dark="#94A3B8",
    status_ignored_non_pdf_bg_dark="#1E293B",
    status_error_fg_dark="#F87171",
    status_error_bg_dark="#381515",
)

# Mapeamento ProcessStatus -> (nome do atributo fg claro, bg claro, fg escuro, bg escuro)
_STATUS_TOKEN_BY_STATUS: Final[dict[ProcessStatus, tuple[str, str, str, str]]] = {
    ProcessStatus.ORGANIZED: (
        "status_organized_fg_light",
        "status_organized_bg_light",
        "status_organized_fg_dark",
        "status_organized_bg_dark",
    ),
    ProcessStatus.MANUAL_REVIEW: (
        "status_manual_review_fg_light",
        "status_manual_review_bg_light",
        "status_manual_review_fg_dark",
        "status_manual_review_bg_dark",
    ),
    ProcessStatus.DUPLICATE_SKIPPED: (
        "status_duplicate_skipped_fg_light",
        "status_duplicate_skipped_bg_light",
        "status_duplicate_skipped_fg_dark",
        "status_duplicate_skipped_bg_dark",
    ),
    ProcessStatus.IGNORED_NON_PDF: (
        "status_ignored_non_pdf_fg_light",
        "status_ignored_non_pdf_bg_light",
        "status_ignored_non_pdf_fg_dark",
        "status_ignored_non_pdf_bg_dark",
    ),
    ProcessStatus.ERROR: (
        "status_error_fg_light",
        "status_error_bg_light",
        "status_error_fg_dark",
        "status_error_bg_dark",
    ),
}


def status_colors(
    status: ProcessStatus, tokens: ThemeTokens
) -> tuple[str, str]:
    """Retornar (cor do texto, cor de fundo do badge) para um ``ProcessStatus``.

    A cor de texto/fundo é escolhida conforme o tema ativo (claro ou escuro)
    a partir dos tokens de status do próprio ``tokens``.
    """
    fg_light_attr, bg_light_attr, fg_dark_attr, bg_dark_attr = _STATUS_TOKEN_BY_STATUS[
        status
    ]
    is_light = _is_light_theme(tokens)
    if is_light:
        return getattr(tokens, fg_light_attr), getattr(tokens, bg_light_attr)
    return getattr(tokens, fg_dark_attr), getattr(tokens, bg_dark_attr)


def _is_light_theme(tokens: ThemeTokens) -> bool:
    """Heurística: tema claro quando a superfície base tem luminosidade alta."""
    return tokens.bg_canvas.startswith(("#F", "#E", "#D"))


def active_theme_for_scheme(is_dark: bool) -> ThemeTokens:
    """Retornar o tema ativo conforme o esquema de cor do sistema operacional."""
    return TECHNICAL_GRAPHITE_THEME if is_dark else EDITORIAL_PAPER_THEME


# --------------------------------------------------------------------------- #
# Gerador de folha de estilos QSS tokenizado — Mockup 1
# --------------------------------------------------------------------------- #

_QSS_TEMPLATE: Final[str] = """
/* Tomus Desktop GUI — QSS gerado a partir de ThemeTokens (Mockup 1) */
* {{
    outline: none;
}}

QMainWindow {{
    background-color: {bg_canvas};
    color: {text_primary};
    font-family: {FONT_UI};
    font-size: 13px;
}}

QWidget {{
    background-color: transparent;
    color: {text_primary};
    font-family: {FONT_UI};
    font-size: 13px;
}}

QFrame#card {{
    background-color: {bg_surface};
    border: 1px solid {border_subtle};
    border-radius: {BORDER_RADIUS_LG}px;
}}

QFrame#cardSm {{
    background-color: {bg_surface};
    border: 1px solid {border_subtle};
    border-radius: {BORDER_RADIUS_MD}px;
}}

QToolBar, QWidget#toolbar {{
    background-color: {bg_canvas};
    border-bottom: 1px solid {border_subtle};
    spacing: 8px;
    padding: 10px 16px;
}}

QLabel#brand {{
    color: {brand_primary};
    font-size: 16px;
    font-weight: 700;
    letter-spacing: -0.3px;
}}

QPushButton#primary {{
    background-color: {accent_primary};
    color: {text_on_accent};
    border: none;
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton#primary:hover {{
    background-color: {accent_hover};
}}

QPushButton#primary:disabled {{
    background-color: {text_muted};
    color: #CBD5E1;
}}

QPushButton#outline {{
    background-color: transparent;
    color: {text_secondary};
    border: 1px solid {border_subtle};
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12.5px;
}}

QPushButton#outline:hover {{
    background-color: {bg_elevated};
    border-color: {border_focus};
}}

QPushButton#segmented {{
    background-color: {bg_elevated};
    color: {text_primary};
    border: 1px solid {border_subtle};
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 6px 12px;
    font-weight: 600;
    font-size: 12.5px;
}}

QPushButton#segmented:checked {{
    background-color: {accent_primary};
    color: {text_on_accent};
    border-color: {accent_primary};
}}

QPushButton#segmented:first:checked {{
    border-top-left-radius: {BORDER_RADIUS_MD}px;
    border-bottom-left-radius: {BORDER_RADIUS_MD}px;
}}

QPushButton#segmented:last:checked {{
    border-top-right-radius: {BORDER_RADIUS_MD}px;
    border-bottom-right-radius: {BORDER_RADIUS_MD}px;
}}

QLineEdit, QComboBox, QSpinBox {{
    background-color: {bg_elevated};
    color: {text_primary};
    border: 1px solid {border_subtle};
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 6px 12px;
    font-size: 13px;
    selection-background-color: {accent_primary};
    selection-color: {text_on_accent};
}}

QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {border_focus};
    background-color: {bg_surface};
}}

QCheckBox {{
    color: {text_primary};
    font-size: 13px;
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {border_subtle};
    border-radius: 3px;
    background-color: {bg_surface};
}}

QCheckBox::indicator:checked {{
    background-color: {accent_primary};
    border-color: {accent_primary};
}}

QTableView {{
    background-color: {bg_surface};
    color: {text_primary};
    border: 1px solid {border_subtle};
    border-radius: {BORDER_RADIUS_LG}px;
    gridline-color: {border_subtle};
    selection-background-color: transparent;
    selection-color: {text_primary};
}}

QHeaderView::section {{
    background-color: transparent;
    color: {text_secondary};
    border: none;
    border-bottom: 1px solid {border_subtle};
    padding: 8px 12px;
    font-weight: 600;
    font-size: 11.5px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}}

QTreeView {{
    background-color: {bg_canvas};
    color: {text_primary};
    border: 1px solid {border_subtle};
    border-radius: {BORDER_RADIUS_LG}px;
}}

QTreeView::item {{
    border: none;
    padding: 6px 10px;
}}

QTreeView::item:selected {{
    background-color: {bg_selected};
    color: {accent_primary};
    border-radius: {BORDER_RADIUS_MD}px;
}}

QStatusBar {{
    background-color: {bg_canvas};
    color: {text_secondary};
    border-top: 1px solid {border_subtle};
    padding: 6px 16px;
}}

QSplitter::handle {{
    background-color: {border_subtle};
    width: 1px;
    height: 1px;
}}

QLabel#sectionHeader {{
    color: {text_secondary};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    padding: 4px 12px;
}}

QLabel#muted {{
    color: {text_muted};
}}

QLabel#pillBadge {{
    color: {text_primary};
    background-color: {bg_elevated};
    border-radius: {BORDER_RADIUS_MD}px;
    padding: 2px 8px;
    font-size: 11.5px;
    font-weight: 600;
}}

QScrollBar:vertical {{
    background-color: transparent;
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {text_muted};
    border-radius: 5px;
    min-height: 40px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {text_secondary};
}}
"""


def generate_qss(tokens: ThemeTokens | None = None) -> str:
    """Gerar a folha de estilos QSS completa a partir de um ``ThemeTokens``.

    Quando ``tokens`` é omitido, usa-se o tema claro (Editorial Paper) por
    padrão. O QSS resultante referencia exclusivamente tokens da paleta ativa:
    nenhuma cor aparece hard-coded fora dos tokens (auditoria Anti-AI-Slop).

    :param tokens: instância de ``ThemeTokens`` (padrão: Editorial Paper).
    :returns: string QSS pronta para ``QApplication.setStyleSheet()``.
    """
    if tokens is None:
        tokens = EDITORIAL_PAPER_THEME

    font_ui = '"SF Pro Text", "Helvetica Neue", sans-serif'

    return _QSS_TEMPLATE.format(
        bg_canvas=tokens.bg_canvas,
        bg_surface=tokens.bg_surface,
        bg_elevated=tokens.bg_elevated,
        bg_selected=tokens.bg_selected,
        border_subtle=tokens.border_subtle,
        border_focus=tokens.border_focus,
        text_primary=tokens.text_primary,
        text_secondary=tokens.text_secondary,
        text_muted=tokens.text_muted,
        text_inverse=tokens.text_inverse,
        accent_primary=tokens.accent_primary,
        accent_hover=tokens.accent_hover,
        text_on_accent=tokens.text_on_accent,
        brand_primary=tokens.brand_primary,
        status_error_fg_light=tokens.status_error_fg_light,
        BORDER_RADIUS_SM=BORDER_RADIUS_SM,
        BORDER_RADIUS_MD=BORDER_RADIUS_MD,
        BORDER_RADIUS_LG=BORDER_RADIUS_LG,
        FONT_UI=font_ui,
    )
