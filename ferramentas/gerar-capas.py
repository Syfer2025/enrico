#!/usr/bin/env python3
"""gerar-capas.py — cria as versões responsivas das capas dos textos."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from PIL import Image

from conteudo import ler_colecao

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"
DESTINO = SITE / "assets/img/acervo/capas"

LARGURAS = (160, 320, 640, 960)
QUALIDADE = 82

PRIMEIRA_IMAGEM = re.compile(r'<img[^>]+src="([^"]+)"|!\[[^\]]*\]\(([^)\s]+)\)')


def main() -> int:
    refazer = "--refazer" in sys.argv
    textos = ler_colecao("textos")

    if refazer and DESTINO.exists():
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True, exist_ok=True)

    com_capa = sem_capa = 0
    faltando: list[str] = []
    gerados = aproveitados = 0
    esperados: set[str] = set()

    for texto in textos:
        escolhida = texto.get("capa") or ""
        if escolhida and "/acervo/capas/" not in escolhida:
            caminho = escolhida.lstrip("/")
        else:
            achado = PRIMEIRA_IMAGEM.search(texto.get("body") or "")
            if not achado:
                sem_capa += 1
                continue
            caminho = achado.group(1) or achado.group(2)

        origem = SITE / caminho.lstrip('/')
        if not origem.exists():
            faltando.append(f"{texto['slug']} → {caminho}")
            sem_capa += 1
            continue

        try:
            with Image.open(origem) as imagem:
                imagem.load()
                if imagem.mode not in ("RGB", "RGBA"):
                    imagem = imagem.convert("RGB")
                for largura in LARGURAS:
                    if largura > imagem.width:
                        continue
                    destino = DESTINO / f"{texto['slug']}-{largura}.webp"
                    esperados.add(destino.name)
                    if (
                        not refazer
                        and destino.exists()
                        and destino.stat().st_mtime >= origem.stat().st_mtime
                    ):
                        aproveitados += 1
                        continue
                    altura = round(imagem.height * largura / imagem.width)
                    imagem.resize((largura, altura), Image.LANCZOS).save(
                        destino, "WEBP", quality=QUALIDADE, method=5
                    )
                    gerados += 1
        except Exception as erro:
            faltando.append(f"{texto['slug']} → {type(erro).__name__}: {erro}")
            sem_capa += 1
            continue

        com_capa += 1

    orfas = 0
    for arquivo in DESTINO.glob("*.webp"):
        if arquivo.name not in esperados:
            arquivo.unlink()
            orfas += 1

    peso = sum(p.stat().st_size for p in DESTINO.iterdir())
    print(f"{com_capa} textos com capa, {sem_capa} sem (viram quadrado com a inicial)")
    print(f"  {gerados} gerada(s), {aproveitados} já estava(m) pronta(s)"
          + (f", {orfas} órfã(s) removida(s)" if orfas else ""))
    print(f"  {peso / 1_048_576:.1f} MB em {DESTINO.relative_to(SITE)}/")
    if faltando:
        print(f"\n{len(faltando)} não deram certo:")
        for f in faltando[:10]:
            print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
