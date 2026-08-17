#!/usr/bin/env python3
"""gen-books.py — grava assets/data/livros.json e injeta o carrossel no index.html."""

import json
import pathlib
import html

from PIL import Image

from conteudo import ler_colecao

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "publicar"
CAPTURADO_EM = "2026-08-04"
LOJA = "https://www.amazon.com.br/stores/author/B0DVQCC67C"

def carregar_livros():
    livros = []
    for livro in ler_colecao("livros", ordenar_por="ordem"):
        slug = livro["slug"]
        capa = RAIZ / f"assets/img/books/{slug}-640.jpg"
        with Image.open(capa) as img:
            larg, alt = img.size
        livros.append((
            slug,
            livro["asin"],
            livro["titulo"],
            livro["subtitulo"],
            livro["nota"],
            livro["avaliacoes"],
            livro["body"],
            larg,
            alt,
        ))
    return livros


LIVROS = carregar_livros()

MARCA_INICIO = "<!-- CARROSSEL:INICIO (gerado por ferramentas/gen-books.py) -->"
MARCA_FIM = "<!-- CARROSSEL:FIM -->"


def json_dos_livros():
    return {
        "fonte": "Amazon.com.br — loja do autor, busca e páginas de produto",
        "capturado_em": CAPTURADO_EM,
        "aviso": "nota e avaliacoes envelhecem; sinopses sao recortes verbatim da Amazon",
        "livros": [
            {
                "slug": s, "asin": a, "titulo": t, "subtitulo": sub,
                "nota": nota, "avaliacoes": av, "sinopse": sin,
                "url": f"https://www.amazon.com.br/dp/{a}",
                "capa": f"assets/img/books/{s}-640.jpg",
            }
            for s, a, t, sub, nota, av, sin, _, _ in LIVROS
        ],
    }


def card(slug, asin, titulo, sub, nota, av, sinopse, larg, alt):
    e = html.escape
    subtitulo = (
        f'\n              <p class="t-footnote book-card__sub">{e(sub)}</p>' if sub else ""
    )

    if nota:
        pct = round(float(nota.replace(",", ".")) / 5 * 100, 1)
        plural = "avaliação" if av == 1 else "avaliações"
        avaliacao = f'''
              <p class="book-rating">
                <span class="book-rating__stars" style="--nota: {pct}%" aria-hidden="true"></span>
                <span class="book-rating__value tabular">{e(nota)}</span>
                <span class="book-rating__count tabular">({av})</span>
                <span class="visually-hidden">
                  {e(nota)} de 5 estrelas, {av} {plural} na Amazon
                </span>
              </p>'''
    else:
        avaliacao = '''
              <p class="book-rating">
                <span class="book-badge">Em Lançamento</span>
              </p>'''

    return f'''          <li class="book-card">
            <a class="book-card__cover" href="https://www.amazon.com.br/dp/{asin}"
               target="_blank" rel="noopener" tabindex="-1" aria-hidden="true">
              <span class="book-mockup">
                <picture>
                  <source
                    type="image/webp"
                    srcset="
                      assets/img/books/{slug}-320.webp 320w,
                      assets/img/books/{slug}-640.webp 640w
                    "
                    sizes="10rem"
                  />
                  <img
                    src="assets/img/books/{slug}-640.jpg"
                    alt=""
                    width="{larg}"
                    height="{alt}"
                    loading="lazy"
                    decoding="async"
                  />
                </picture>
              </span>
            </a>

            <div class="book-card__body">
              <h3 class="t-title-3 book-card__title">{html.escape(titulo)}</h3>{subtitulo}{avaliacao}
              <p class="t-footnote book-card__desc">{html.escape(sinopse)}</p>
              <a class="book-card__cta"
                 href="https://www.amazon.com.br/dp/{asin}" target="_blank" rel="noopener">
                Ver na Amazon<svg class="book-card__cta-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3.25 10.75 8 6 12.75" /></svg>
                <span class="visually-hidden">— {html.escape(titulo)}</span>
              </a>
            </div>
          </li>'''


def bloco_carrossel():
    cards = "\n\n".join(card(*l) for l in LIVROS)
    return f'''{MARCA_INICIO}
      <section class="book-carousel" data-module="book-carousel" aria-labelledby="livros-titulo">
        <div class="book-carousel__head">
          <div class="book-carousel__heading">
            <h2 class="book-carousel__title" id="livros-titulo">Livros</h2>
            <p class="t-footnote book-carousel__count">{len(LIVROS)} títulos</p>
          </div>
          <div class="book-carousel__nav">
            <button class="carousel-btn" type="button" data-dir="prev" aria-label="Livros anteriores">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75"
                   stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M10 3.25 5.25 8 10 12.75" />
              </svg>
            </button>
            <button class="carousel-btn" type="button" data-dir="next" aria-label="Próximos livros">
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75"
                   stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M6 3.25 10.75 8 6 12.75" />
              </svg>
            </button>
          </div>
        </div>

        <ul class="book-carousel__track" tabindex="0"
            aria-label="Livros de Enrico Pierro, lista horizontal">
{cards}
        </ul>
      </section>
      {MARCA_FIM}'''


if __name__ == "__main__":
    dados = RAIZ / "assets/data/livros.json"
    dados.parent.mkdir(parents=True, exist_ok=True)
    dados.write_text(
        json.dumps(json_dos_livros(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    idx = RAIZ / "index.html"
    s = idx.read_text(encoding="utf-8")
    i, f = s.index(MARCA_INICIO), s.index(MARCA_FIM) + len(MARCA_FIM)
    idx.write_text(s[:i] + bloco_carrossel() + s[f:], encoding="utf-8")

    print(f"{len(LIVROS)} livros -> assets/data/livros.json e index.html")
