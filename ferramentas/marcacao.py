"""marcacao.py — a marcação simples dos textos da página inicial, nos dois sentidos."""

from __future__ import annotations

import html
import re


_LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
_FORTE = re.compile(r"\*\*(.+?)\*\*", re.S)
_OBRA = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", re.S)


def para_html(texto: str, classe_link: str | None = None) -> str:
    """A marcação simples → o HTML que vai para a página."""
    if not texto:
        return ""

    def link(m: re.Match[str]) -> str:
        classe = f'class="{classe_link}" ' if classe_link else ""
        return f'<a {classe}href="{m.group(2)}">{m.group(1)}</a>'

    s = _FORTE.sub(r"<strong>\1</strong>", texto)
    s = _OBRA.sub(r"<cite>\1</cite>", s)
    return _LINK.sub(link, s)


_TAG_CITE = re.compile(r"<cite\b[^>]*>(.*?)</cite>", re.S | re.I)
_TAG_FORTE = re.compile(r"<(?:strong|b)\b[^>]*>(.*?)</(?:strong|b)>", re.S | re.I)
_TAG_LINK = re.compile(r'<a\b[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', re.S | re.I)
_TAG_EM = re.compile(r"<(?:em|i)\b[^>]*>(.*?)</(?:em|i)>", re.S | re.I)


def de_html(marcado: str) -> str:
    """O HTML antigo → a marcação simples. Para migrar e para conferir."""
    if not marcado:
        return ""
    s = _TAG_LINK.sub(lambda m: f"[{m.group(2)}]({m.group(1)})", marcado)
    s = _TAG_FORTE.sub(r"**\1**", s)
    s = _TAG_CITE.sub(r"*\1*", s)
    s = _TAG_EM.sub(r"*\1*", s)
    return s


def tem_tag(texto: str) -> bool:
    """Sobrou HTML no texto? Usado pela varredura."""
    return bool(re.search(r"</?[a-z][\w-]*[\s>]", texto or "", re.I))


def escapar(texto: str) -> str:
    """Escapa o que não é marcação, para o texto do autor nunca virar HTML."""
    return html.escape(texto, quote=False)
