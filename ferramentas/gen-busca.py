#!/usr/bin/env python3
"""gen-busca.py — o índice de busca dos textos e dos episódios."""

from __future__ import annotations

import html as libhtml
import json
import re
import sys
from pathlib import Path

from conteudo import ler_colecao

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"

RESUMO = 240

ROTULOS = {"diario": "diário", "coluna": "coluna", "textos": "textos", "outros": "outros"}


def texto_puro(md: str) -> str:
    """O corpo em Markdown → texto corrido, para o resumo e para a busca."""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", md)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[*_`>#-]", " ", s)
    s = libhtml.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    itens = []

    for texto in ler_colecao("textos"):
        if texto.get("publicado") is False:
            continue
        corpo = texto_puro(texto.get("body") or "")
        itens.append({
            "t": texto["titulo"],
            "d": texto["data"],
            "c": ROTULOS.get(texto.get("categoria"), "outros"),
            "s": texto["slug"],
            "r": corpo[:RESUMO],
        })

    itens.sort(key=lambda i: i["d"], reverse=True)

    episodios = []
    arquivo = SITE / "assets/data/episodios.json"
    if arquivo.exists():
        for ep in json.loads(arquivo.read_text(encoding="utf-8"))["episodios"]:
            rotulo = ep.get("rotulo") or ""
            episodios.append({
                "t": ep["nome"],
                "d": ep["publicado_em"],
                "c": "episódio",
                "s": ep["youtube_id"],
                "r": f"{rotulo} do abcpod." if rotulo else "episódio do abcpod.",
            })
        episodios.sort(key=lambda i: i["d"], reverse=True)

    destino = SITE / "assets/data/busca.json"
    destino.write_text(
        json.dumps({"textos": itens, "episodios": episodios}, ensure_ascii=False,
                   separators=(",", ":")),
        encoding="utf-8",
    )

    peso = destino.stat().st_size
    print(f"{len(itens)} textos e {len(episodios)} episódios no índice")
    print(f"{destino.relative_to(SITE)} — {peso / 1024:.0f} KB")
    print("baixado uma vez, e só quando alguém usa a busca")
    return 0


if __name__ == "__main__":
    sys.exit(main())
