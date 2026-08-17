#!/usr/bin/env python3
"""gerar-marca.py — a imagem de prévia dos links e o favicon."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"

OG = (1200, 630)


def carregar_hero() -> Image.Image:
    """A foto do hero, na maior versão disponível."""
    for caminho in (
        SITE / "assets/img/hero/enrico-hero-2880.jpg",
        SITE / "assets/img/hero/enrico-hero-1440.jpg",
        PROJETO / "bastidores/originais/hero",
    ):
        if caminho.is_file():
            return Image.open(caminho).convert("RGB")
        if caminho.is_dir():
            for arquivo in sorted(caminho.iterdir()):
                if arquivo.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    return Image.open(arquivo).convert("RGB")
    raise SystemExit("erro: não achei a foto do hero")


def recortar(imagem: Image.Image, alvo: tuple[int, int]) -> Image.Image:
    """Recorta pelo centro na proporção pedida, sem distorcer."""
    largura, altura = alvo
    escala = max(largura / imagem.width, altura / imagem.height)
    novo = (round(imagem.width * escala), round(imagem.height * escala))
    imagem = imagem.resize(novo, Image.LANCZOS)
    esquerda = (imagem.width - largura) // 2
    topo = max(0, (imagem.height - altura) // 3)
    return imagem.crop((esquerda, topo, esquerda + largura, topo + altura))


def imagem_de_previa() -> Path:
    base = recortar(carregar_hero(), OG)

    veu = Image.new("L", OG, 0)
    desenho = ImageDraw.Draw(veu)
    for x in range(OG[0]):
        opacidade = max(0, int(210 * (1 - x / (OG[0] * 0.62))))
        desenho.line([(x, 0), (x, OG[1])], fill=opacidade)
    escuro = Image.new("RGB", OG, (8, 9, 12))
    base = Image.composite(escuro, base, veu)

    logo = Image.open(SITE / "assets/img/brand/logo-enrico-branco-1600.png").convert("RGBA")
    largura_logo = 520
    logo = logo.resize(
        (largura_logo, round(logo.height * largura_logo / logo.width)), Image.LANCZOS
    )
    base.paste(logo, (72, (OG[1] - logo.height) // 2), logo)

    destino = SITE / "assets/img/og/capa.jpg"
    destino.parent.mkdir(parents=True, exist_ok=True)
    base.save(destino, "JPEG", quality=88, optimize=True, progressive=True)
    return destino


def favicons() -> list[Path]:
    """Ícones a partir do logo, sobre o quase-preto do site."""
    logo = Image.open(SITE / "assets/img/brand/logo-enrico-branco-1600.png").convert("RGBA")
    feitos = []

    for lado, nome in ((512, "icone-512.png"), (180, "apple-touch-icon.png")):
        tela = Image.new("RGBA", (lado, lado), (8, 9, 12, 255))
        largura = round(lado * 0.76)
        peca = logo.resize((largura, round(logo.height * largura / logo.width)), Image.LANCZOS)
        tela.paste(peca, ((lado - peca.width) // 2, (lado - peca.height) // 2), peca)
        caminho = SITE / nome
        tela.convert("RGB").save(caminho, "PNG", optimize=True)
        feitos.append(caminho)

    base = Image.open(SITE / "icone-512.png")
    ico = SITE / "favicon.ico"
    base.save(ico, sizes=[(16, 16), (32, 32), (48, 48)])
    feitos.append(ico)
    return feitos


def main() -> int:
    previa = imagem_de_previa()
    print(f"prévia de link  {previa.relative_to(SITE)}  "
          f"{OG[0]}×{OG[1]}  {previa.stat().st_size / 1024:.0f} KB")
    for caminho in favicons():
        print(f"ícone           {caminho.relative_to(SITE)}  "
              f"{caminho.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
