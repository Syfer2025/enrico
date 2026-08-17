#!/usr/bin/env python3
"""texto.py — transforma o texto escrito no painel em HTML para o site."""

from __future__ import annotations

import re
from pathlib import Path

import markdown as _markdown
from PIL import Image

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"

_conversor = _markdown.Markdown(extensions=["extra", "sane_lists"])

_medidas: dict[str, tuple[int, int]] = {}


def _dimensoes(caminho: str) -> tuple[int, int] | None:
    """Medidas reais do arquivo, em cache — são milhares de consultas."""
    if caminho not in _medidas:
        arquivo = SITE / caminho.lstrip("/")
        if not arquivo.exists() or arquivo.suffix.lower() == ".svg":
            return None
        try:
            with Image.open(arquivo) as imagem:
                _medidas[caminho] = imagem.size
        except Exception:
            return None
    return _medidas.get(caminho)


def _arrumar_imagem(tag: str) -> str:
    """<img src=x> → a marcação completa que o site espera, com as medidas."""
    src = re.search(r'src="([^"]+)"', tag)
    if not src:
        return tag
    caminho = src.group(1)

    if caminho.startswith("/") and not caminho.startswith("//"):
        caminho = caminho.lstrip("/")

    atributos = [f'src="{caminho}"']
    alt = re.search(r'alt="([^"]*)"', tag)
    atributos.append(f'alt="{alt.group(1) if alt else ""}"')

    medidas = _dimensoes(caminho)
    if medidas:
        atributos.append(f'width="{medidas[0]}"')
        atributos.append(f'height="{medidas[1]}"')
    atributos += ['loading="lazy"', 'decoding="async"']

    return f'<figure class="esc-item__media"><img {" ".join(atributos)}></figure>'


def figura(caminho: str, alt: str = "") -> str:
    """A marcação de uma foto avulsa, igual à das fotos do texto."""
    if not caminho:
        return ""
    escapado = alt.replace('"', "&quot;")
    return _arrumar_imagem(f'<img src="{caminho}" alt="{escapado}">')


def para_html(texto: str) -> str:
    """O texto do painel → o HTML que vai para a página."""
    if not texto:
        return ""
    _conversor.reset()
    html = _conversor.convert(texto)

    html = re.sub(r"<img[^>]*>", lambda m: _arrumar_imagem(m.group(0)), html)

    def _soltar(m: re.Match[str]) -> str:
        antes, figura, depois = m.group(1).strip(), m.group(2), m.group(3).strip()
        partes = []
        if antes:
            partes.append(f"<p>{antes}</p>")
        partes.append(figura)
        if depois:
            partes.append(f"<p>{depois}</p>")
        return "\n".join(partes)

    sem_p = r"(?:(?!</?p\b).)*?"
    html = re.sub(
        rf"<p>({sem_p})(<figure\b.*?</figure>)({sem_p})</p>",
        _soltar, html, flags=re.S,
    )

    def link(m: re.Match[str]) -> str:
        tag, href = m.group(0), m.group(1)
        if href.startswith("http") and "enricopierro.com.br" not in href:
            return tag[:-1] + ' target="_blank" rel="noopener">'
        return tag

    return re.sub(r'<a href="([^"]+)">', link, html)
