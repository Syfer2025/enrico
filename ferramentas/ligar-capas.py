#!/usr/bin/env python3
"""ligar-capas.py — dá a cada texto um campo `capa` apontando para a sua imagem."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from conteudo import CONTEUDO, escrever, ler_colecao

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"

PRIMEIRA_IMAGEM = re.compile(r'<img[^>]+src="([^"]+)"')

LARGURA_MINIATURA = 320

ORDEM = ["titulo", "data", "categoria", "publicado", "capa", "url_original"]


def main() -> int:
    forcar = "--forcar" in sys.argv
    pasta = CONTEUDO / "textos"

    com_capa = sem_capa = ja_tinha = 0

    for texto in ler_colecao("textos"):
        if texto.get("capa") and not forcar:
            ja_tinha += 1
            continue

        slug = texto["slug"]
        capa = None

        miniatura = SITE / f"assets/img/acervo/capas/{slug}-{LARGURA_MINIATURA}.webp"
        if miniatura.exists():
            capa = f"/assets/img/acervo/capas/{slug}-{LARGURA_MINIATURA}.webp"
        else:
            achado = PRIMEIRA_IMAGEM.search(texto.get("body") or "")
            if achado and (SITE / achado.group(1)).exists():
                capa = "/" + achado.group(1)

        if not capa:
            sem_capa += 1
            continue

        campos = {c: texto.get(c) for c in ORDEM if c != "capa"}
        campos["capa"] = capa
        campos = {c: campos.get(c) for c in ORDEM}

        escrever(pasta / f"{slug}.md", campos, texto.get("body", ""))
        com_capa += 1

    print(f"{com_capa} textos ganharam campo de capa")
    if ja_tinha:
        print(f"{ja_tinha} já tinham (use --forcar para refazer)")
    print(f"{sem_capa} sem imagem — na lista aparecem só com o título, como antes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
