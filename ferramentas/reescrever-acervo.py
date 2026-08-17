#!/usr/bin/env python3
"""reescrever-acervo.py — troca no HTML e no JSON os endereços de terceiros pelos"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent / "publicar"
BASTIDORES = RAIZ.parent / "bastidores"
MAPA = BASTIDORES / "acervo-mapa.json"

PADRAO_URL = re.compile(r'https?://[^\s"\'<>)\\]+')
PADRAO_IMG = re.compile(r"\.(png|jpe?g|gif|webp|svg)(\?|$)", re.I)

_dimensoes: dict[str, tuple[int, int]] = {}


def dimensoes(caminho: str) -> tuple[int, int] | None:
    """Medidas reais do arquivo local, em cache — são milhares de consultas."""
    if caminho not in _dimensoes:
        arquivo = RAIZ / caminho
        if not arquivo.exists() or arquivo.suffix == ".svg":
            return None
        try:
            with Image.open(arquivo) as imagem:
                _dimensoes[caminho] = imagem.size
        except Exception:
            return None
    return _dimensoes[caminho]


def corrigir_medidas(tag: str, caminho: str) -> str:
    """Ajusta width/height da tag para o que o arquivo local realmente tem."""
    medidas = dimensoes(caminho)
    if not medidas:
        return tag
    largura, altura = medidas
    if 'width="' in tag:
        tag = re.sub(r'width="\d+"', f'width="{largura}"', tag, count=1)
    if 'height="' in tag:
        tag = re.sub(r'height="\d+"', f'height="{altura}"', tag, count=1)
    return tag


def main() -> int:
    if not MAPA.exists():
        print("erro: bastidores/acervo-mapa.json não existe — rode antes o baixar-acervo.py")
        return 1

    mapa: dict[str, str] = json.loads(MAPA.read_text(encoding="utf-8"))
    print(f"mapa com {len(mapa)} imagens locais\n")

    ordenadas = sorted(mapa, key=len, reverse=True)

    def tratar(html: str, medir_imagens: bool) -> tuple[str, int, int]:
        """Devolve (html tratado, quantas trocas, quantas <img> removidas)."""
        removidas = 0

        def limpar(match: re.Match[str]) -> str:
            nonlocal removidas
            tag = match.group(0)
            src = re.search(r'src="([^"]+)"', tag)
            if not src:
                return tag
            endereco = src.group(1)
            if not endereco.startswith("http") or endereco in mapa:
                return tag
            removidas += 1
            return ""

        html = re.sub(r"<img\b[^>]*>", limpar, html)
        html = re.sub(r"<figure[^>]*>\s*</figure>", "", html)

        trocadas = 0
        for url in ordenadas:
            if url in html:
                trocadas += html.count(url)
                html = html.replace(url, mapa[url])

        if medir_imagens:

            def medir(match: re.Match[str]) -> str:
                tag = match.group(0)
                src = re.search(r'src="(assets/img/acervo/[^"]+)"', tag)
                return corrigir_medidas(tag, src.group(1)) if src else tag

            html = re.sub(r"<img\b[^>]*>", medir, html)

        return html, trocadas, removidas

    arquivo = RAIZ / "escrita.html"
    texto = arquivo.read_text(encoding="utf-8")
    texto, trocadas, removidas = tratar(texto, medir_imagens=False)
    arquivo.write_text(texto, encoding="utf-8")
    sobrando = [u for u in PADRAO_URL.findall(texto) if PADRAO_IMG.search(u)]
    print("escrita.html")
    print(f"  {trocadas} endereços trocados por arquivo local")
    print(f"  {removidas} <img> de link morto removidas")
    print(f"  {len(sobrando)} urls de imagem externas restantes")

    arquivo = BASTIDORES / "acervo-completo.json"
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    trocadas = removidas = 0
    for grupo in dados["grupos"]:
        for post in grupo["posts"]:
            post["conteudo"], t, r = tratar(post["conteudo"], medir_imagens=True)
            trocadas += t
            removidas += r
    arquivo.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    cru = arquivo.read_text(encoding="utf-8")
    sobrando = [u for u in PADRAO_URL.findall(cru) if PADRAO_IMG.search(u)]
    print("bastidores/acervo-completo.json")
    print(f"  {trocadas} endereços trocados por arquivo local")
    print(f"  {removidas} <img> de link morto removidas")
    print(f"  {len(sobrando)} urls de imagem externas restantes (só em href de crédito)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
