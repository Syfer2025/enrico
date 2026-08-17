#!/usr/bin/env python3
"""conferir-html.py — compara duas versões de uma página ignorando espaçamento."""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path


class Eventos(HTMLParser):
    """Transforma o HTML numa lista de eventos comparáveis."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.itens: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        pares = " ".join(f"{k}={v!r}" for k, v in sorted(attrs))
        self.itens.append(f"<{tag} {pares}>")

    def handle_endtag(self, tag: str) -> None:
        self.itens.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        texto = re.sub(r"\s+", " ", data).strip()
        if texto:
            self.itens.append(texto)

    def handle_comment(self, data: str) -> None:
        self.itens.append(f"<!--{re.sub(r's+', ' ', data).strip()}-->")


def eventos(caminho: Path) -> list[str]:
    p = Eventos()
    p.feed(caminho.read_text(encoding="utf-8"))
    return p.itens


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[-1])
        return 2

    antes, depois = (Path(a) for a in sys.argv[1:3])
    a, d = eventos(antes), eventos(depois)

    if a == d:
        print(f"IDÊNTICO na renderização — {len(a)} elementos conferidos")
        print(f"  ({antes.name} e {depois.name} diferem só em espaçamento)")
        return 0

    print(f"DIFERENÇA: {len(a)} elementos antes, {len(d)} depois\n")
    mostradas = 0
    for i in range(max(len(a), len(d))):
        va = a[i] if i < len(a) else "(acabou)"
        vd = d[i] if i < len(d) else "(acabou)"
        if va != vd:
            print(f"  posição {i}:")
            print(f"    antes : {va[:150]}")
            print(f"    depois: {vd[:150]}")
            mostradas += 1
            if mostradas == 10:
                print("\n  (mostrando as 10 primeiras)")
                break
    return 1


if __name__ == "__main__":
    sys.exit(main())
