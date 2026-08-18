#!/usr/bin/env python3
"""gen-escrita.py — grava assets/data/escrita.json e injeta a seção "Escrita" no"""

import html
import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request

from PIL import Image

import leitor
from conteudo import ler_colecao

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "publicar"
BASTIDORES = RAIZ.parent / "bastidores"
ROTULOS = {"diario": "diário", "coluna": "coluna", "textos": "textos", "outros": "outros"}

SOURCE_CAPAS = BASTIDORES / "originais/escrita"
IMG_CAPAS = RAIZ / "assets/img/escrita"
LARGURAS_CAPA = (480, 960)
QUALIDADE_WEBP = 95
QUALIDADE_JPEG = 95

MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]

CATEGORIAS_HOME = ["diario", "coluna", "textos"]

RESERVA = {
    "total": 577,
    "categorias": [
        ("diario", "diário", 196),
        ("coluna", "coluna", 108),
        ("textos", "textos", 235),
        ("outros", "outros", 38),
    ],
    "recentes": [
        ("dia 193/365.", "2026-08-05", "dia-193-365", "diário", None),
        ("o que precisa morrer em você.", "2026-04-04", "o-que-precisa-morrer-em-voce", "coluna", None),
        ("brasilidades.", "2026-03-05", "brasilidades", "textos", None),
    ],
}

MARCA_INICIO = "<!-- ESCRITA:INICIO (gerado por ferramentas/gen-escrita.py) -->"
MARCA_FIM = "<!-- ESCRITA:FIM -->"

LEITOR_INICIO = "<!-- LEITOR:INICIO (gerado por ferramentas/gen-escrita.py) -->"
LEITOR_FIM = "<!-- LEITOR:FIM -->"

CAPA = re.compile(r'<img[^>]+src="([^"]+)"|!\[[^\]]*\]\(([^)\s]+)\)', re.IGNORECASE)

SETA = (
    '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M6 3.25 10.75 8 6 12.75" /></svg>'
)


def data_curta(iso):
    """2026-08-04 → '04 ago 2026'. Mês abreviado evita ambiguidade de formato."""
    ano, mes, dia = iso.split("-")
    return f"{dia} {MESES[int(mes) - 1]} {ano}"


def capa(texto):
    """O endereço da capa do texto, ou None."""
    escolhida = (texto.get("capa") or "").strip()
    if escolhida:
        return escolhida.split("?")[0]
    m = CAPA.search(texto.get("body") or "")
    if not m:
        return None
    return (m.group(1) or m.group(2)).split("?")[0]


def carrega():
    """(total, categorias, recentes) a partir de conteudo/textos/."""
    try:
        textos = ler_colecao("textos")
    except FileNotFoundError:
        return RESERVA["total"], RESERVA["categorias"], RESERVA["recentes"]

    conhecidas = [(g, r) for g, r in ROTULOS.items()]
    agrupados = {slug: [] for slug, _ in conhecidas}
    for texto in textos:
        if texto.get("publicado") is False:
            continue
        slug = texto.get("categoria")
        agrupados.setdefault(slug if slug in agrupados else "outros", []).append(texto)

    categorias = [(slug, rotulo, len(agrupados[slug])) for slug, rotulo in conhecidas]

    escolhidos = []
    for slug, rotulo in conhecidas:
        if slug not in CATEGORIAS_HOME:
            continue
        posts = sorted(agrupados[slug], key=lambda p: p["data"], reverse=True)
        if not posts:
            continue
        p = posts[0]
        escolhidos.append(
            (p["titulo"], p["data"], p["slug"], rotulo, capa(p))
        )

    escolhidos.sort(key=lambda p: p[1], reverse=True)

    return sum(c[2] for c in categorias), categorias, escolhidos


def dimensoes(caminho):
    """(largura, altura) em pixels, com Pillow."""
    with Image.open(caminho) as imagem:
        return imagem.size


def baixa_original(url, slug):
    """Original em bastidores/originais/escrita/<slug>.<ext>. Já baixado, não rebaixa."""
    ext = pathlib.Path(url.split("?")[0]).suffix.lower() or ".png"
    destino = SOURCE_CAPAS / f"{slug}{ext}"
    if destino.exists():
        return destino

    if not url.startswith(("http://", "https://")):
        local = RAIZ / url.lstrip('/')
        if local.exists():
            return local
        raise SystemExit(
            f"erro: a capa de '{slug}' aponta para {url}, que não existe.\n"
            f"       Rode ferramentas/gerar-capas.py antes deste."
        )

    SOURCE_CAPAS.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as resposta:
        dados = resposta.read()
    with tempfile.NamedTemporaryFile(dir=SOURCE_CAPAS, delete=False) as tmp:
        tmp.write(dados)
        parcial = pathlib.Path(tmp.name)
    parcial.replace(destino)
    return destino


def deriva(origem, slug):
    """Gera os .webp e o .jpg de reserva. Devolve as dimensões do maior."""
    IMG_CAPAS.mkdir(parents=True, exist_ok=True)
    maior = max(LARGURAS_CAPA)

    with Image.open(origem) as imagem:
        imagem.load()
        if imagem.mode not in ("RGB", "RGBA"):
            imagem = imagem.convert("RGB")

        for largura in LARGURAS_CAPA:
            escala = min(1, largura / max(imagem.width, imagem.height))
            tamanho = (round(imagem.width * escala), round(imagem.height * escala))
            imagem.resize(tamanho, Image.LANCZOS).save(
                IMG_CAPAS / f"{slug}-{largura}.webp", "WEBP", quality=QUALIDADE_WEBP
            )

        escala = min(1, maior / max(imagem.width, imagem.height))
        tamanho = (round(imagem.width * escala), round(imagem.height * escala))
        reserva = imagem.resize(tamanho, Image.LANCZOS)
        if reserva.mode == "RGBA":
            reserva = reserva.convert("RGB")
        reserva.save(IMG_CAPAS / f"{slug}-{maior}.jpg", "JPEG", quality=QUALIDADE_JPEG)

    return dimensoes(IMG_CAPAS / f"{slug}-{maior}.jpg")


def prepara_capa(url, slug):
    """Capa local pronta para a marcação, ou None se não der para gerar."""
    if not url:
        return None
    try:
        largura, altura = deriva(baixa_original(url, slug), slug)
    except (urllib.error.URLError, OSError) as erro:
        print(f"  aviso: não consegui preparar a capa de {slug} ({erro})")
        return None
    return {"slug": slug, "largura": largura, "altura": altura}


SIZES_CAPA = "(width >= 1440px) 400px, (width >= 880px) 30vw, 100vw"


def thumb(url, local):
    if local:
        s = local["slug"]
        maior = max(LARGURAS_CAPA)
        fontes = ", ".join(
            f"assets/img/escrita/{s}-{w}.webp {w}w" for w in LARGURAS_CAPA
        )
        return (
            '<span class="writing-post__thumb">'
            "<picture>"
            f'<source type="image/webp" srcset="{fontes}" sizes="{SIZES_CAPA}" />'
            f'<img src="assets/img/escrita/{s}-{maior}.jpg" '
            f'width="{local["largura"]}" height="{local["altura"]}" '
            'alt="" loading="lazy" decoding="async" />'
            "</picture>"
            "</span>"
        )

    if not url:
        return (
            '<span class="writing-post__thumb writing-post__thumb--tipo" '
            'aria-hidden="true"></span>'
        )

    print(f"  aviso: sem capa preparada, cartão tipográfico ({url})")
    return (
        '<span class="writing-post__thumb writing-post__thumb--tipo" '
        'aria-hidden="true"></span>'
    )


def item(titulo, iso, slug, categoria, url_capa, local):
    e = html.escape
    return f'''      <li class="writing-post">
        <a class="writing-post__link" href="escrita.html#{slug}"
           data-slug="{e(slug)}" data-titulo="{e(titulo)}">
          {thumb(url_capa, local)}
          <span class="writing-post__body">
            <span class="t-eyebrow writing-post__cat">{e(categoria)}</span>
            <span class="writing-post__title">{e(titulo)}</span>
            <time class="t-footnote writing-post__date tabular" datetime="{iso}">{data_curta(iso)}</time>
          </span>
        </a>
      </li>'''


def bloco(total, recentes):
    itens = "\n".join(item(*p) for p in recentes)
    return f'''{MARCA_INICIO}
      <section class="writing" id="escrita" aria-labelledby="escrita-titulo"
               data-module="esc-leitor" data-src="assets/data/textos">
        <div class="container">
          <div class="writing__head">
            <p class="t-eyebrow writing__eyebrow">escrita</p>
            <h2 class="t-display-2 writing__title" id="escrita-titulo">
              os últimos textos
            </h2>
            <p class="writing__standfirst">
              {total} publicações abertas para leitura em
              <a class="writing__link" href="escrita.html">a escrita</a>: a
              coluna da semana, o acervo de textos e o diário.
            </p>
          </div>

          <ul class="writing-list" aria-label="Os {len(recentes)} textos mais recentes publicados">
{itens}
          </ul>

          <a class="writing__all" href="escrita.html">
            <span>ver todas as {total} publicações</span>
            {SETA}
          </a>
        </div>
      </section>
      {MARCA_FIM}'''


def dados(total, categorias, recentes):
    return {
        "fonte": "bastidores/acervo-completo.json",
        "arquivo": "escrita.html",
        "total": total,
        "criterio": "o texto mais recente de cada categoria principal (diário, coluna, textos)",
        "categorias": [
            {"slug": s, "rotulo": r, "total": t, "url": f"escrita.html#esc-{s}"}
            for s, r, t in categorias
        ],
        "recentes": [
            {
                "titulo": t,
                "data": d,
                "slug": s,
                "categoria": c,
                "url": f"escrita.html#{s}",
                "capa": url_capa,
            }
            for t, d, s, c, url_capa, _local in recentes
        ],
    }


if __name__ == "__main__":
    total, categorias, recentes = carrega()

    recentes = [(*p, prepara_capa(p[4], p[2])) for p in recentes]

    arquivo = RAIZ / "assets/data/escrita.json"
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(
        json.dumps(dados(total, categorias, recentes), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    idx = RAIZ / "index.html"
    s = idx.read_text(encoding="utf-8")
    if MARCA_INICIO not in s:
        raise SystemExit(
            f"marcador {MARCA_INICIO} não encontrado no index.html — "
            "cole os dois marcadores no lugar onde a seção deve entrar."
        )
    i, f = s.index(MARCA_INICIO), s.index(MARCA_FIM) + len(MARCA_FIM)
    s = s[:i] + bloco(total, recentes) + s[f:]

    if LEITOR_INICIO not in s:
        raise SystemExit(
            f"marcador {LEITOR_INICIO} não encontrado no index.html — "
            "cole os dois marcadores no fim do <body>, onde a janela deve entrar."
        )
    i, f = s.index(LEITOR_INICIO), s.index(LEITOR_FIM) + len(LEITOR_FIM)
    s = s[:i] + LEITOR_INICIO + "\n" + leitor.MARCACAO + "\n    " + LEITOR_FIM + s[f:]

    idx.write_text(s, encoding="utf-8")

    print(
        f"{len(recentes)} textos mais recentes de {total} "
        "-> assets/data/escrita.json e index.html"
    )
