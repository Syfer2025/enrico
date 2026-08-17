"""moldura.py — o cabeçalho e o rodapé do site, lidos de um lugar só."""

from __future__ import annotations

import re
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
FONTE = PROJETO / "publicar/index.html"


def _pedaco(s: str, inicio: str, fim: str) -> str:
    i = s.index(inicio)
    f = s.index(fim) + len(fim)
    return s[i:f]


def cabecalho(atual: str | None = None) -> str:
    """O cabeçalho do site. `atual` é o href do item de menu desta página."""
    s = FONTE.read_text(encoding="utf-8")
    html = _pedaco(s, '<header class="site-header"', "</header>")

    html = html.replace(' aria-current="page"', "")

    if atual:
        html = re.sub(
            rf'(<a class="site-nav__link" href="{re.escape(atual)}")',
            r'\1 aria-current="page"',
            html,
            count=1,
        )
    return html


def rodape() -> str:
    """O rodapé do site, igual em todas as páginas."""
    s = FONTE.read_text(encoding="utf-8")
    return _pedaco(s, '<footer class="site-footer"', "</footer>")
