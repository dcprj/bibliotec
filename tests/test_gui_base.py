"""Testes unitários da Etapa 1 da Passagem 2 — pacote base ``src/tomus/gui/``.

Valida:
* as cores hexadecimais dos temas Editorial Paper e Technical Graphite
  (seção 2.1 do ``docs/designs/gui_spec.md``);
* a ausência absoluta de emojis Unicode nos módulos GUI (Anti-AI-Slop);
* a geração de folha de estilo QSS (cores dos tokens, zero gradientes,
  zero cores neon roxo/rosa);
* o renderizador de ícones SVG em memória (viewBox 0 0 24 24, traço 1.5px,
  sem arquivos externos, suporte Retina via devicePixelRatio);
* a abstração multiplataforma ``os_integration`` (mock de subprocess).

Execução alvo (conforme gui_spec.md seção 6):

    QT_QPA_PLATFORM=offscreen pytest -m 'not slow' tests/test_gui_base.py
"""

from __future__ import annotations

import os as _os
import re
import sys
from pathlib import Path

# Garantir offscreen ANTES de qualquer import de PySide6 (ícones precisam de QApplication).
_os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from tomus.core.models import ProcessStatus
from tomus.gui.theme import (
    EDITORIAL_PAPER_THEME,
    TECHNICAL_GRAPHITE_THEME,
    ThemeTokens,
    active_theme_for_scheme,
    generate_qss,
    status_colors,
)
from tomus.gui.icons import ICON_NAMES, render_icon, render_pixmap, svg_for

# --------------------------------------------------------------------------- #
# Fixture QApplication (necessária para QIcon/QPixmap/QSvgRenderer em offscreen)
# --------------------------------------------------------------------------- #

_QAPP: "_QAppHolder" = None  # type: ignore[name-defined]


class _QAppHolder:
    def __init__(self) -> None:
        from PySide6.QtWidgets import QApplication

        self.app = QApplication.instance() or QApplication([])


@pytest.fixture(scope="session")
def qapp() -> _QAppHolder:
    global _QAPP
    if _QAPP is None:
        _QAPP = _QAppHolder()
    return _QAPP


# --------------------------------------------------------------------------- #
# Helpers de detecção de emoji (Anti-AI-Slop: zero emojis crus na interface)
# --------------------------------------------------------------------------- #

_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # símbolos e pictogramas
    "\U0001F680-\U0001F6FF"  # transporte e mapas
    "\U0001F1E0-\U0001F1FF"  # bandeiras
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+"
)

_GUI_MODULE_FILES = [
    "src/tomus/gui/__init__.py",
    "src/tomus/gui/theme.py",
    "src/tomus/gui/icons.py",
    "src/tomus/gui/os_integration.py",
]


def _module_source_lines(project_root: str) -> list[tuple[str, int, str]]:
    """Ler os fontes dos módulos GUI (caminho, número da linha, conteúdo)."""
    out: list[tuple[str, int, str]] = []
    for rel in _GUI_MODULE_FILES:
        abs_path = _os.path.join(project_root, rel)
        with open(abs_path, encoding="utf-8") as fh:
            for idx, line in enumerate(fh, start=1):
                out.append((rel, idx, line))
    return out


# --------------------------------------------------------------------------- #
# Testes: paletas de cores (Seção 2.1)
# --------------------------------------------------------------------------- #

_EDITORIAL_PAPER = {
    "bg_canvas": "#F8F9FA",
    "bg_surface": "#FFFFFF",
    "bg_elevated": "#F1F5F9",
    "bg_selected": "#EFF6FF",
    "border_subtle": "#E2E8F0",
    "border_focus": "#1E3A8A",
    "text_primary": "#0F172A",
    "text_secondary": "#64748B",
    "text_muted": "#94A3B8",
    "text_inverse": "#FFFFFF",
    "accent_primary": "#1E3A8A",
    "accent_hover": "#1E40AF",
    "text_on_accent": "#FFFFFF",
    "brand_primary": "#0F172A",
    "status_organized_fg_light": "#15803D",
    "status_organized_bg_light": "#DCFCE7",
    "status_manual_review_fg_light": "#B45309",
    "status_manual_review_bg_light": "#FEF3C7",
    "status_duplicate_skipped_fg_light": "#0369A1",
    "status_duplicate_skipped_bg_light": "#E0F2FE",
    "status_ignored_non_pdf_fg_light": "#64748B",
    "status_ignored_non_pdf_bg_light": "#F1F5F9",
    "status_error_fg_light": "#B91C1C",
    "status_error_bg_light": "#FEE2E2",
    "status_organized_fg_dark": "#4ADE80",
    "status_organized_bg_dark": "#142E1F",
    "status_manual_review_fg_dark": "#FBBF24",
    "status_manual_review_bg_dark": "#33240B",
    "status_duplicate_skipped_fg_dark": "#38BDF8",
    "status_duplicate_skipped_bg_dark": "#0F293A",
    "status_ignored_non_pdf_fg_dark": "#94A3B8",
    "status_ignored_non_pdf_bg_dark": "#1E293B",
    "status_error_fg_dark": "#F87171",
    "status_error_bg_dark": "#381515",
}

_TECHNICAL_GRAPHITE = dict(_EDITORIAL_PAPER)
_TECHNICAL_GRAPHITE.update(
    {
        "bg_canvas": "#0F172A",
        "bg_surface": "#1E293B",
        "bg_elevated": "#334155",
        "bg_selected": "#1E3A8A",
        "border_subtle": "#334155",
        "border_focus": "#4A7BB0",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "text_muted": "#64748B",
        "text_inverse": "#0F172A",
        "accent_primary": "#4A7BB0",
        "accent_hover": "#5B8EC4",
        "brand_primary": "#F8FAFC",
    }
)


def test_theme_tokens_sao_imutaveis():
    """ThemeTokens deve ser um dataclass frozen (não permite atribuição)."""
    t = EDITORIAL_PAPER_THEME
    assert isinstance(t, ThemeTokens)
    with pytest.raises(Exception):
        t.bg_canvas = "#000000"  # type: ignore[misc]


def test_editorial_paper_tema_tem_cores_esperadas():
    """Tema claro (Editorial Paper) deve ter todos os tokens hexadecimais do spec."""
    t = EDITORIAL_PAPER_THEME
    for attr, esperado in _EDITORIAL_PAPER.items():
        assert getattr(t, attr) == esperado, f"{attr}: esperado {esperado}"


def test_technical_graphite_tema_tem_cores_esperadas():
    """Tema escuro (Technical Graphite) deve ter todos os tokens hexadecimais do spec."""
    t = TECHNICAL_GRAPHITE_THEME
    for attr, esperado in _TECHNICAL_GRAPHITE.items():
        assert getattr(t, attr) == esperado, f"{attr}: esperado {esperado}"


def test_todas_cores_sao_hex_validas():
    """Todo token de cor deve ser uma string hexadecimal #RRGGBB."""
    hex_re = re.compile(r"^#[0-9A-Fa-f]{6}$")
    for tema in (EDITORIAL_PAPER_THEME, TECHNICAL_GRAPHITE_THEME):
        for campo in tema.__dataclass_fields__:
            valor = getattr(tema, campo)
            assert isinstance(valor, str) and hex_re.match(valor), (
                f"{tema.__name__}.{campo} não é hex válido: {valor!r}"
            )


def test_active_theme_for_scheme():
    """Seleção de tema conforme esquema do sistema operacional."""
    assert active_theme_for_scheme(is_dark=False) is EDITORIAL_PAPER_THEME
    assert active_theme_for_scheme(is_dark=True) is TECHNICAL_GRAPHITE_THEME


# --------------------------------------------------------------------------- #
# Testes: cores de status por ProcessStatus
# --------------------------------------------------------------------------- #

_PARAMETRIZADO_STATUS = [
    (ProcessStatus.ORGANIZED, "#15803D", "#DCFCE7", "#4ADE80", "#142E1F"),
    (ProcessStatus.MANUAL_REVIEW, "#B45309", "#FEF3C7", "#FBBF24", "#33240B"),
    (ProcessStatus.DUPLICATE_SKIPPED, "#0369A1", "#E0F2FE", "#38BDF8", "#0F293A"),
    (ProcessStatus.IGNORED_NON_PDF, "#64748B", "#F1F5F9", "#94A3B8", "#1E293B"),
    (ProcessStatus.ERROR, "#B91C1C", "#FEE2E2", "#F87171", "#381515"),
]


@pytest.mark.parametrize(
    "status,fg_light,bg_light,fg_dark,bg_dark", _PARAMETRIZADO_STATUS
)
def test_status_colors_por_processo(status, fg_light, bg_light, fg_dark, bg_dark):
    """status_colors deve retornar (texto, fundo) do badge conforme o tema."""
    fg, bg = status_colors(status, EDITORIAL_PAPER_THEME)
    assert (fg, bg) == (fg_light, bg_light)
    fg, bg = status_colors(status, TECHNICAL_GRAPHITE_THEME)
    assert (fg, bg) == (fg_dark, bg_dark)


# --------------------------------------------------------------------------- #
# Testes: geração de QSS
# --------------------------------------------------------------------------- #

def test_qss_contem_cores_dos_tokens():
    """O QSS gerado deve referenciar as cores hexadecimais dos tokens ativos."""
    qss_claro = generate_qss(EDITORIAL_PAPER_THEME)
    qss_escuro = generate_qss(TECHNICAL_GRAPHITE_THEME)

    assert "#F8F9FA" in qss_claro
    assert "#0F172A" in qss_escuro
    assert "#1E3A8A" in qss_claro
    assert "#4A7BB0" in qss_escuro
    assert "#FFFFFF" in qss_claro and "#FFFFFF" in qss_escuro

    # Mesmo QSS para temas diferentes não deve conter a cor do outro tema
    # nas superfícies base (auditoria de não-vazamento de paleta).
    assert "#1E293B" not in qss_claro.replace("#142E1F", "")
    assert "#F8F9FA" not in qss_escuro.replace("#142E1F", "")


def test_qss_sem_gradientes_ou_cores_neon():
    """Anti-AI-Slop: QSS não deve conter gradientes lineares/radiais nem cores neon."""
    qss = generate_qss(EDITORIAL_PAPER_THEME)
    qss_lower = qss.lower()

    assert "gradient" not in qss_lower
    assert "linear-gradient" not in qss_lower
    assert "radial-gradient" not in qss_lower

    # Cores neon proibidas (roxo-rosa / AI Glow)
    proibidas = ["#ff00ff", "#bf00ff", "#ff00de", "#a855f7", "#d946ef"]
    for proibida in proibidas:
        assert proibida not in qss_lower, f"Cor neon proibida no QSS: {proibida}"


def test_qss_sem_emojis():
    """Anti-AI-Slop: QSS gerado não deve conter caracteres emoji."""
    qss = generate_qss(EDITORIAL_PAPER_THEME)
    assert not _EMOJI_RE.search(qss)


# --------------------------------------------------------------------------- #
# Testes: ausência de emojis nos fontes GUI (Anti-AI-Slop)
# --------------------------------------------------------------------------- #

def test_modulos_gui_sem_emojis(project_root):
    """Nenhum módulo do pacote gui deve conter emojis Unicode crus."""
    for rel, linha_num, linha in _module_source_lines(project_root):
        assert not _EMOJI_RE.search(linha), (
            f"Emoji proibido em {rel}:{linha_num}: {linha.rstrip()!r}"
        )


def _linhas_fora_de_docstring(
    project_root: Path,
) -> list[tuple[str, int, str]]:
    """Ler fontes dos módulos GUI ignorando linhas dentro de docstrings."""
    resultado: list[tuple[str, int, str]] = []
    # Agrupar linhas por arquivo para resetar o estado do docstring a cada arquivo.
    linhas_por_arquivo: dict[str, list[tuple[int, str]]] = {}
    for rel, linha_num, linha in _module_source_lines(project_root):
        linhas_por_arquivo.setdefault(rel, []).append((linha_num, linha))

    for rel in sorted(linhas_por_arquivo):
        dentro_docstring = False
        for linha_num, linha in linhas_por_arquivo[rel]:
            if '"""' in linha:
                dentro_docstring = not dentro_docstring
                continue
            if dentro_docstring:
                continue
            resultado.append((rel, linha_num, linha))
    return resultado


def test_modulos_gui_sem_carregamento_arquivo_imagem_externo(project_root):
    """Ícones não devem carregar arquivos .png/.jpg externos (somente SVG em memória).

    A detecção foca em chamadas reais de leitura/construção de imagem
    (QPixmap/QIcon/QImage/QMovie com caminho literal, ou open() de imagem),
    ignorando menções em docstrings/comentários.
    """
    proibidos = re.compile(r"\.(png|jpg|jpeg|gif|bmp|ico)\b", re.IGNORECASE)
    carregamento_imagem = re.compile(
        r"\b(QPixmap|QIcon|QImage|QMovie|open)\s*\(.*"
        r"\.(png|jpg|jpeg|gif|bmp|ico)\b",
        re.IGNORECASE,
    )
    for rel, linha_num, linha in _linhas_fora_de_docstring(project_root):
        # Pular linhas que contenham """ (resto de docstring não balanceado).
        if '"""' in linha:
            continue
        assert not carregamento_imagem.search(linha), (
            f"Carregamento de imagem externa em {rel}:{linha_num}: {linha.rstrip()!r}"
        )
        assert not proibidos.search(linha.split("#")[0]), (
            f"Extensão de imagem externa em {rel}:{linha_num}: {linha.rstrip()!r}"
        )


# --------------------------------------------------------------------------- #
# Testes: ícones SVG em memória (Seção 2.3)
# --------------------------------------------------------------------------- #

_ESPERADO_ICONES = (
    "alert-triangle",
    "catalog-empty",
    "check-circle",
    "copy-layers",
    "cpu-provider",
    "database-cache",
    "external-link",
    "file-slash",
    "folder-input",
    "folder-output",
    "folder-reveal",
    "play-run",
    "rotate-ccw",
    "scan-ocr",
    "sliders-settings",
    "stop-square",
    "x-octagon",
)


def test_icon_names_correspondem_ao_spec():
    """ICON_NAMES deve conter exatamente os 16 ícones da especificação."""
    assert sorted(ICON_NAMES) == sorted(_ESPERADO_ICONES)


def test_svg_primitivas_tem_atributos_obrigatorios():
    """Cada SVG deve ter viewBox 0 0 24 24, stroke-width 1.5, linecap/join round, fill none."""
    for nome in ICON_NAMES:
        svg = svg_for(nome)
        assert 'viewBox="0 0 24 24"' in svg, f"{nome}: viewBox ausente"
        assert 'stroke-width="1.5"' in svg, f"{nome}: stroke-width ausente"
        assert 'stroke-linecap="round"' in svg, f"{nome}: stroke-linecap ausente"
        assert 'stroke-linejoin="round"' in svg, f"{nome}: stroke-linejoin ausente"
        assert 'fill="none"' in svg, f"{nome}: fill='none' ausente"
        assert 'stroke="currentColor"' in svg, f"{nome}: currentColor ausente"


def test_svg_desconhecido_leva_keyerror():
    """svg_for deve levantar KeyError para nome inexistente."""
    with pytest.raises(KeyError):
        svg_for("icone-inexistente")


def test_render_pixmap_retorna_qpixmap(qapp):
    """render_pixmap deve retornar QPixmap com devicePixelRatio configurado."""
    pixmap = render_pixmap("play-run", color="#1E3A5F", size_px=24, dpr=1.0)
    assert not pixmap.isNull()
    assert pixmap.devicePixelRatioF() == 1.0
    assert pixmap.size().width() == 24
    assert pixmap.size().height() == 24


def test_render_pixmap_retina_dpr(qapp):
    """Suporte Retina @2x/@3x: dpr 2.0 deve dobrar os pixels físicos."""
    pixmap_1x = render_pixmap("check-circle", dpr=1.0)
    pixmap_2x = render_pixmap("check-circle", dpr=2.0)
    assert pixmap_2x.size().width() == pixmap_1x.size().width() * 2
    assert pixmap_2x.devicePixelRatioF() == 2.0


def test_render_icon_retorna_qicon_nao_vazio(qapp):
    """render_icon deve retornar QIcon com pelo menos um pixmap disponível."""
    icon = render_icon("folder-input", color="#4A7BB0", size_px=20)
    assert not icon.isNull()
    tamanhos = [p for p in icon.availableSizes()]
    assert any(t.width() == 20 and t.height() == 20 for t in tamanhos)


# --------------------------------------------------------------------------- #
# Testes: os_integration (abstração multiplataforma)
# --------------------------------------------------------------------------- #

def test_open_file_in_os_darwin(monkeypatch, tmp_path):
    """macOS deve chamar ``open <caminho>``."""
    arquivo = tmp_path / "documento.pdf"
    arquivo.write_text("x")
    chamados: list[list[str]] = []

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr("subprocess.Popen", lambda cmd: chamados.append(cmd))

    from tomus.gui.os_integration import open_file_in_os

    open_file_in_os(arquivo)
    assert chamados == [["open", str(arquivo.resolve())]]


def test_reveal_in_file_manager_darwin(monkeypatch, tmp_path):
    """macOS deve chamar ``open -R <caminho>``."""
    arquivo = tmp_path / "documento.pdf"
    arquivo.write_text("x")
    chamados: list[list[str]] = []

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr("subprocess.Popen", lambda cmd: chamados.append(cmd))

    from tomus.gui.os_integration import reveal_in_file_manager

    reveal_in_file_manager(arquivo)
    assert chamados == [["open", "-R", str(arquivo.resolve())]]


def test_open_file_in_os_windows(monkeypatch, tmp_path):
    """Windows deve chamar ``os.startfile``."""
    arquivo = tmp_path / "documento.pdf"
    arquivo.write_text("x")
    chamados: list[str] = []

    monkeypatch.setattr(sys, "platform", "win32")

    def _fake_startfile(p: str) -> None:
        chamados.append(p)

    monkeypatch.setattr(_os, "startfile", _fake_startfile, raising=False)

    from tomus.gui.os_integration import open_file_in_os

    open_file_in_os(arquivo)
    assert chamados == [str(arquivo.resolve())]


def test_reveal_in_file_manager_windows(monkeypatch, tmp_path):
    """Windows deve chamar ``explorer /select,<caminho>``."""
    arquivo = tmp_path / "documento.pdf"
    arquivo.write_text("x")
    chamados: list[list[str]] = []

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("subprocess.Popen", lambda cmd: chamados.append(cmd))

    from tomus.gui.os_integration import reveal_in_file_manager

    reveal_in_file_manager(arquivo)
    assert chamados == [["explorer", f"/select,{arquivo.resolve()}"]]


def test_open_file_in_os_linux(monkeypatch, tmp_path):
    """Linux deve chamar ``xdg-open <caminho>``."""
    arquivo = tmp_path / "documento.pdf"
    arquivo.write_text("x")
    chamados: list[list[str]] = []

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr("subprocess.Popen", lambda cmd: chamados.append(cmd))

    from tomus.gui.os_integration import open_file_in_os

    open_file_in_os(arquivo)
    assert chamados == [["xdg-open", str(arquivo.resolve())]]


def test_open_file_in_os_arquivo_inexistente_leva_file_not_found():
    """open_file_in_os deve levantar FileNotFoundError para caminho ausente."""
    from tomus.gui.os_integration import open_file_in_os

    with pytest.raises(FileNotFoundError):
        open_file_in_os("/caminho/que/nao/existe.pdf")


def test_secure_chmod_600_aplica_0600(monkeypatch, tmp_path):
    """secure_chmod_600 deve aplicar os.chmod(path, 0o600) em POSIX."""
    arquivo = tmp_path / "config.toml"
    arquivo.write_text("x")
    chamados: list[int] = []

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr("os.chmod", lambda p, modo: chamados.append(modo))

    from tomus.gui.os_integration import secure_chmod_600

    secure_chmod_600(arquivo)
    assert chamados == [0o600]


def test_secure_chmod_600_windows_ignora(monkeypatch, tmp_path):
    """No Windows, secure_chmod_600 não chama os.chmod (ACL POSIX não se aplica)."""
    arquivo = tmp_path / "config.toml"
    arquivo.write_text("x")
    chamados: list[int] = []

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr("os.chmod", lambda p, modo: chamados.append(modo))

    from tomus.gui.os_integration import secure_chmod_600

    secure_chmod_600(arquivo)
    assert chamados == []


def test_reveal_in_file_manager_arquivo_inexistente_leva_file_not_found():
    """reveal_in_file_manager deve levantar FileNotFoundError para caminho ausente."""
    from tomus.gui.os_integration import reveal_in_file_manager

    with pytest.raises(FileNotFoundError):
        reveal_in_file_manager("/caminho/que/nao/existe.pdf")
