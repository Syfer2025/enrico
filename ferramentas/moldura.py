"""moldura.py — o cabeçalho, o rodapé e o convite da newsletter, lidos de um"""

from __future__ import annotations

import re
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
FONTE = PROJETO / "publicar/index.html"


def _pedaco(s: str, inicio: str, fim: str) -> str:
    i = s.index(inicio)
    f = s.index(fim) + len(fim)
    return s[i:f]


def _ancoras_para_o_index(html: str) -> str:
    """Faz as âncoras da home apontarem para a home."""
    return re.sub(r'href="#([\w-]+)"', r'href="index.html#\1"', html)


def cabecalho(atual: str | None = None) -> str:
    """O cabeçalho do site. `atual` é o href do item de menu desta página."""
    s = FONTE.read_text(encoding="utf-8")
    html = _pedaco(s, '<header class="site-header"', "</header>")

    html = html.replace(' aria-current="page"', "")

    if atual:
        html = _ancoras_para_o_index(html)
        html = re.sub(
            rf'(<a class="site-nav__link" href="{re.escape(atual)}")',
            r'\1 aria-current="page"',
            html,
            count=1,
        )
    return html


def convite() -> str:
    """A seção da newsletter, copiada da home."""
    s = FONTE.read_text(encoding="utf-8")
    return _pedaco(s, "<!-- CONVITE:INICIO", "<!-- CONVITE:FIM -->")


def rodape() -> str:
    """O rodapé do site, igual em todas as páginas."""
    s = FONTE.read_text(encoding="utf-8")
    return _ancoras_para_o_index(_pedaco(s, '<footer class="site-footer"', "</footer>"))
