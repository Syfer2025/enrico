#!/usr/bin/env python3
"""quebrar-acervo.py — parte o acervo num arquivo por texto."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "publicar"
ORIGEM = RAIZ.parent / "bastidores/acervo-completo.json"
DESTINO = RAIZ / "assets/data/textos"


def main() -> int:
    if not ORIGEM.exists():
        print(f"erro: {ORIGEM.relative_to(RAIZ)} não existe")
        return 1

    dados = json.loads(ORIGEM.read_text(encoding="utf-8"))

    if DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)

    escritos = 0
    maior = 0
    vistos: set[str] = set()

    for grupo in dados["grupos"]:
        for post in grupo["posts"]:
            slug = post["slug"]
            if slug in vistos:
                print(f"  aviso: slug repetido, mantido o primeiro — {slug}")
                continue
            vistos.add(slug)

            texto = {
                "slug": slug,
                "titulo": post["titulo"],
                "data": post["data"],
                "url": post["url"],
                "categoria": grupo["rotulo"],
                "conteudo": post["conteudo"],
            }
            arquivo = DESTINO / f"{slug}.json"
            arquivo.write_text(
                json.dumps(texto, ensure_ascii=False), encoding="utf-8"
            )
            escritos += 1
            maior = max(maior, arquivo.stat().st_size)

    antes = ORIGEM.stat().st_size
    soma = sum(p.stat().st_size for p in DESTINO.iterdir())
    print(f"{escritos} textos em {DESTINO.relative_to(RAIZ)}/")
    print(f"  antes : 1 arquivo de {antes / 1024:.0f} KB baixado para abrir 1 texto")
    print(f"  agora : o maior texto tem {maior / 1024:.0f} KB (soma {soma / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
