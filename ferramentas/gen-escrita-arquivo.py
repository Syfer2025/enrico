#!/usr/bin/env python3
"""gen-escrita-arquivo.py — gera a subpágina "a escrita" (escrita.html)."""

import html
import json
import pathlib
import shutil
import re
import sys
import time
import urllib.request
from html.parser import HTMLParser

from conteudo import escrever, ler_colecao
import leitor
from texto import figura, para_html

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "publicar"
PROJETO = RAIZ.parent
LIDO_EM = "2026-08-05"
SITE = "https://enricopierro.com.br"
API = "https://public-api.wordpress.com/rest/v1.1/sites/enricopierro.com.br/posts/"
FIELDS = "title,date,slug,URL,categories,content"
BASTIDORES = RAIZ.parent / "bastidores"
CACHE = BASTIDORES / ".cache-escrita.json"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]
MESES_LONGOS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

DESTAQUE = 6
ANTERIORES = 12

LIMITE_ANO = 48

ENQUADRAMENTO = {
    "centro": None,
    "topo": "50% 0%",
    "fundo": "50% 100%",
    "esquerda": "0% 50%",
    "direita": "100% 50%",
}

GRUPOS = [
    {
        "slug": "diario",
        "rotulo": "diário",
        "linha": "um texto por dia, numerado, ao longo de um ano inteiro.",
    },
    {
        "slug": "coluna",
        "rotulo": "coluna",
        "linha": "a coluna semanal, publicada em mais de 40 jornais e portais do país.",
    },
    {
        "slug": "textos",
        "rotulo": "textos",
        "linha": "o acervo aberto: prosa curta, cartas e poesia, do primeiro ao mais recente.",
    },
    {
        "slug": "outros",
        "rotulo": "outros",
        "linha": "o resto do acervo — cartas de domingo, desabafos e tudo o que não tem categoria.",
    },
]

PAYWALL = re.compile(
    r"subscribe to keep reading|become a paid subscriber", re.IGNORECASE
)

KEEP = {
    "p", "br", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote",
    "ul", "ol", "li", "em", "strong", "b", "i", "u", "a", "img",
    "figure", "figcaption", "div", "span", "code", "pre", "sup", "sub",
    "small", "s", "del",
}
DROP_SKIP = {"script", "style", "iframe", "noscript", "object", "embed", "form", "svg", "math"}
VOID = {"img", "br"}


def data_curta(iso):
    """2026-08-04 → '04 ago 2026'. Mês abreviado evita ambiguidade de formato."""
    ano, mes, dia = iso.split("-")
    return f"{dia} {MESES[int(mes) - 1]} {ano}"


def grupo(cats, slug):
    if "coluna" in cats:
        return "coluna"
    if "textos" in cats:
        return "textos"
    if "diario" in cats:
        return "diario"
    if slug.startswith("dia-"):
        return "diario"
    return "outros"


class Limpador(HTMLParser):
    """Reconstrói o HTML de blocos do WordPress sem classes, estilos e lixo."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag in DROP_SKIP:
            self.skip += 1
            return
        if tag not in KEEP:
            return
        a = dict(attrs)
        at = []
        emit = True
        if tag == "img":
            for k in ("src", "alt", "width", "height"):
                v = a.get(k)
                if v:
                    at.append((k, v))
            at.append(("loading", "lazy"))
            at.append(("decoding", "async"))
        elif tag == "a":
            href = (a.get("href") or "").strip()
            if href and href.startswith(("#", "https://", "http://", "mailto:")):
                at.append(("href", href))
                if href.startswith("http") and "enricopierro.com.br" not in href:
                    at.append(("target", "_blank"))
                    at.append(("rel", "noopener"))
            else:
                emit = False
        elif tag == "figure":
            at.append(("class", "esc-item__media"))
        if emit:
            self.stack.append(tag)
            self.out.append(
                "<" + tag
                + ("".join(f' {k}="{html.escape(v, quote=True)}"' for k, v in at) if at else "")
                + ">"
            )

    def handle_endtag(self, tag):
        if tag in DROP_SKIP:
            self.skip = max(0, self.skip - 1)
            return
        if tag not in KEEP or tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
            self.out.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def limpa(raw):
    """HTML bruto do WordPress → HTML limpo da página."""
    s = re.sub(r"<a\b[^>]*>\s*(<img\b[^>]*>)\s*</a>", r"\1", raw)
    p = Limpador()
    p.feed(s)
    out = "".join(p.out)
    out = re.sub(r"\s*\n\s*", "\n", out)
    out = re.sub(r"\n\s*\n\s*\n+", "\n\n", out)
    return out.strip()


def conteudo_limpo(raw):
    """Conteúdo para o card; posts de assinante (paywall do substack) não têm"""
    if PAYWALL.search(raw):
        return "<p>este texto é exclusivo para assinantes e fica no site original.</p>"
    return limpa(raw)


def _get(url, tentativas=4):
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception as exc:
            print(f"  (tentativa {i + 1} falhou: {exc})")
            time.sleep(2)
    return None


def busca(offline=False):
    """Retorna os posts da API (ou do cache). 100 por página."""
    if offline:
        if not CACHE.exists():
            raise SystemExit(f"--offline, mas não há cache em {CACHE}")
        posts = json.loads(CACHE.read_text(encoding="utf-8"))
        print(f"{len(posts)} posts do cache local")
        return posts

    posts = []
    page = 1
    while True:
        d = _get(f"{API}?number=100&page={page}&fields={FIELDS}")
        if not d or not d.get("posts"):
            print(f"  sem resposta na página {page}; parando")
            break
        posts += d["posts"]
        print(f"  página {page}: +{len(d['posts'])} (total {len(posts)})")
        if len(d["posts"]) < 100:
            break
        page += 1
        time.sleep(0.4)

    if not posts:
        if CACHE.exists():
            print("  busca falhou; usando o cache local")
            return json.loads(CACHE.read_text(encoding="utf-8"))
        raise SystemExit("não veio nada da API e não há cache")

    CACHE.write_text(json.dumps(posts, ensure_ascii=False), encoding="utf-8")
    print(f"  {len(posts)} posts salvos no cache")
    return posts


def monta(posts):
    """Posts da API → lista de grupos pronta para virar HTML e JSON."""
    agrupados = {g["slug"]: [] for g in GRUPOS}
    for p in posts:
        g = grupo(p.get("categories") or [], p.get("slug") or "")
        iso = (p.get("date") or "")[:10]
        agrupados[g].append(
            {
                "titulo": p.get("title") or "(sem título)",
                "data": iso,
                "slug": p.get("slug"),
                "url": p.get("URL") or f"{SITE}/{p.get('slug')}/",
                "conteudo": conteudo_limpo(p.get("content") or ""),
            }
        )

    grupos = []
    for g in GRUPOS:
        itens = agrupados[g["slug"]]
        itens.sort(key=lambda x: x["data"], reverse=True)
        grupos.append({**g, "total": len(itens), "posts": itens})
    return grupos


def seta():
    return (
        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<path d="M6 3.25 10.75 8 6 12.75" /></svg>'
    )


def estilo_de_foco(reg):
    """O object-position da capa, ou string vazia quando é o centro."""
    posicao = ENQUADRAMENTO.get(reg.get("enquadramento") or "centro")
    return f' style="object-position:{posicao}"' if posicao else ""


def linha_thumb(reg, sizes="4.5rem"):
    """Miniatura da linha. Sem imagem no post, um quadrado com a inicial."""
    slug = capa(reg)
    src, srcset = srcset_capa(slug, (160, 320)) if slug else (None, None)
    if not src:
        inicial = (reg["titulo"].strip()[:1] or "•").upper()
        return (
            '<span class="esc-row__thumb esc-row__thumb--tipo" aria-hidden="true">'
            f'<span class="esc-row__inicial">{html.escape(inicial)}</span></span>'
        )
    return f'''<span class="esc-row__thumb">
   <img src="{src}" srcset="{srcset}" sizes="{sizes}"
        alt="" width="160" height="160" loading="lazy" decoding="async"{estilo_de_foco(reg)} />
  </span>'''


def item(reg):
    """Uma linha do arquivo: link que abre o texto na janela de leitura."""
    e = html.escape
    return f'''<li class="esc-rows__row">
 <a class="esc-row" href="#{reg['slug']}" data-slug="{reg['slug']}" data-titulo="{e(reg['titulo'])}" data-data="{reg['data']}">
  {linha_thumb(reg)}
  <span class="esc-row__body">
   <span class="esc-row__title">{e(reg['titulo'])}</span>
   <time class="t-footnote esc-row__date tabular" datetime="{reg['data']}">{data_curta(reg['data'])}</time>
  </span>
  <span class="esc-row__chevron" aria-hidden="true"></span>
 </a>
</li>'''


CAPA = re.compile(r'<img[^>]+src="([^"]+)"', re.IGNORECASE)


def _capas_disponiveis():
    """Quais larguras existem de cada capa, lendo a pasta uma vez só."""
    pasta = RAIZ / "assets/img/acervo/capas"
    mapa = {}
    if pasta.is_dir():
        for arquivo in pasta.glob("*.webp"):
            slug, _, largura = arquivo.stem.rpartition("-")
            if slug and largura.isdigit():
                mapa.setdefault(slug, set()).add(int(largura))
    return mapa


CAPAS = _capas_disponiveis()


def capa(reg):
    """O slug do texto, se ele tem capa gerada. Senão, None."""
    return reg["slug"] if reg["slug"] in CAPAS else None


def srcset_capa(slug, larguras):
    """src e srcset com as larguras que realmente existem desta capa."""
    tem = sorted(w for w in larguras if w in CAPAS.get(slug, ()))
    if not tem:
        return None, None
    base = f"assets/img/acervo/capas/{slug}"
    srcset = ", ".join(f"{base}-{w}.webp {w}w" for w in tem)
    return f"{base}-{tem[-1]}.webp", srcset


def card(reg, tamanho):
    """Card de capa de um texto. `tamanho` é 'grande' ou 'media'."""
    e = html.escape
    slug = capa(reg)
    src, srcset = srcset_capa(slug, (320, 640, 960)) if slug else (None, None)
    sizes = (
        "(width >= 1040px) 20rem, (width >= 700px) 40vw, 74vw"
        if tamanho == "grande"
        else "(width >= 1040px) 13rem, (width >= 700px) 26vw, 46vw"
    )

    if src:
        media = f'''<span class="esc-card__media">
                  <img
                    src="{src}"
                    srcset="{srcset}"
                    sizes="{sizes}"
                    alt=""
                    width="640"
                    height="427"
                    loading="lazy"
                    decoding="async"{estilo_de_foco(reg)}
                  />
                </span>'''
        corpo = f'''<span class="esc-card__title">{e(reg['titulo'])}</span>
                  <time class="t-footnote esc-card__date tabular" datetime="{reg['data']}">{data_curta(reg['data'])}</time>'''
    else:
        media = '''<span class="esc-card__media esc-card__media--tipo">
                  <span class="esc-card__marca" aria-hidden="true">”</span>
                </span>'''
        corpo = f'''<span class="esc-card__title">{e(reg['titulo'])}</span>
                  <time class="t-footnote esc-card__date tabular" datetime="{reg['data']}">{data_curta(reg['data'])}</time>'''

    return f'''              <li class="esc-card esc-card--{tamanho}">
                <a class="esc-card__link" href="#{reg['slug']}" data-slug="{reg['slug']}" data-titulo="{e(reg['titulo'])}" data-data="{reg['data']}">
                  {media}
                  <span class="esc-card__body">
                  {corpo}
                  </span>
                </a>
              </li>'''


def estante(g, posts, tamanho, rotulo):
    """Fileira horizontal de capas."""
    if not posts:
        return ""
    e = html.escape
    cards = "\n".join(card(p, tamanho) for p in posts)
    id_rot = f"esc-{g['slug']}-{tamanho}"
    return f'''          <div class="esc-shelf" data-module="esc-shelf">
            <div class="esc-shelf__head">
              <h3 class="t-eyebrow esc-shelf__label" id="{id_rot}">{e(rotulo)}</h3>
              <div class="esc-shelf__nav">
                <button class="carousel-btn" type="button" data-dir="prev" aria-label="{e(rotulo)}: anteriores">
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75"
                       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M10 3.25 5.25 8 10 12.75" />
                  </svg>
                </button>
                <button class="carousel-btn" type="button" data-dir="next" aria-label="{e(rotulo)}: próximos">
                  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75"
                       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                    <path d="M6 3.25 10.75 8 6 12.75" />
                  </svg>
                </button>
              </div>
            </div>

            <ul class="esc-shelf__track" tabindex="0" aria-labelledby="{id_rot}">
{cards}
            </ul>
          </div>'''


def periodos(posts):
    """Rabo da lista em baldes de leitura curta: (id, rótulo, itens)."""
    por_ano = {}
    for p in posts:
        por_ano.setdefault(p["data"][:4], []).append(p)

    saida = []
    for ano in sorted(por_ano, reverse=True):
        itens = por_ano[ano]
        if len(itens) <= LIMITE_ANO:
            saida.append((ano, ano, itens))
            continue
        por_mes = {}
        for p in itens:
            por_mes.setdefault(p["data"][:7], []).append(p)
        for mes in sorted(por_mes, reverse=True):
            rotulo = f"{MESES_LONGOS[int(mes[5:7]) - 1]} de {mes[:4]}"
            saida.append((mes, rotulo, por_mes[mes]))
    return saida


def periodo_html(g, pid, rotulo, itens, ativo):
    """Um período: seção de linhas. Só o período ativo fica visível."""
    e = html.escape
    plural = "texto" if len(itens) == 1 else "textos"
    linhas = "\n".join(item(p) for p in itens)
    return f'''              <section class="esc-per" id="esc-{g['slug']}-{pid}" data-periodo="{pid}"{'' if ativo else ' hidden'}>
                <header class="esc-per__head">
                  <h3 class="t-title-3 esc-per__titulo">{e(rotulo)}</h3>
                  <p class="t-footnote esc-per__contagem tabular">{len(itens)} {plural}</p>
                </header>

                <ul class="esc-rows">
{linhas}
                </ul>
              </section>'''


def side_periodos(g, baldes):
    """Lista de períodos da categoria, para a barra lateral."""
    e = html.escape
    ativa = g["slug"] == GRUPOS[0]["slug"]
    itens = "\n".join(
        f'''                <li>
                  <button class="esc-side__link" type="button" data-periodo="{pid}"{' aria-current="true"' if (ativa and i == 0) else ''}>
                    <span class="esc-side__nome">{e(rotulo)}</span>
                    <span class="t-footnote esc-side__count tabular">{len(itens_p)}</span>
                  </button>
                </li>'''
        for i, (pid, rotulo, itens_p) in enumerate(baldes)
    )
    return f'''              <ul class="esc-side__list esc-side__list--periodos" data-cat="{g['slug']}"{'' if ativa else ' hidden'}>
{itens}
              </ul>'''


def side_categorias(grupos):
    e = html.escape
    itens = "\n".join(
        f'''                <li>
                  <button class="esc-side__link" type="button" data-cat="{g['slug']}"{' aria-current="true"' if i == 0 else ''}>
                    <span class="esc-side__nome">{e(g['rotulo'])}</span>
                    <span class="t-footnote esc-side__count tabular">{g['total']}</span>
                  </button>
                </li>'''
        for i, g in enumerate(grupos)
    )
    return itens


def grupo_html(g, ativo):
    """Painel de uma categoria: fileiras de capa + o período selecionado."""
    e = html.escape
    id_titulo = f"esc-{g['slug']}-titulo"
    posts = g["posts"]

    destaque = estante(g, posts[:DESTAQUE], "grande", "mais recentes")
    anteriores = estante(
        g, posts[DESTAQUE:DESTAQUE + ANTERIORES], "media", "antes dessas"
    )
    baldes = periodos(posts)
    periodos_html = "\n\n".join(
        periodo_html(g, pid, rotulo, itens, ativo=(i == 0))
        for i, (pid, rotulo, itens) in enumerate(baldes)
    )

    return f'''        <section class="esc-panel" id="esc-{g['slug']}" data-cat="{g['slug']}"
                 aria-labelledby="{id_titulo}"{'' if ativo else ' hidden'}>
          <header class="esc-panel__head">
            <h2 class="t-largetitle esc-panel__titulo" id="{id_titulo}">{e(g['rotulo'])}</h2>
            <p class="t-footnote esc-panel__contagem tabular">{g['total']} publicações</p>
            <p class="t-subhead esc-panel__desc">{e(g['linha'])}</p>
          </header>

{destaque}

{anteriores}

          <div class="esc-panel__periodos">
{periodos_html}
          </div>
        </section>'''


def pagina(grupos, total):
    total = total
    anos = {p["data"][:4] for g in grupos for p in g["posts"]}
    ultima = max(p["data"] for g in grupos for p in g["posts"])
    categorias = side_categorias(grupos)
    listas_periodo = "\n".join(side_periodos(g, periodos(g["posts"])) for g in grupos)
    grupos_html = "\n\n".join(
        grupo_html(g, ativo=(i == 0)) for i, g in enumerate(grupos)
    )

    return f'''<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>A escrita — Enrico Pierro</title>
    <meta
      name="description"
      content="Todos os {total} textos do enricopierro.com.br — a coluna, o acervo de textos e o diário — para ler aqui, sem sair do site."
    />
    <meta name="theme-color" content="#08090C" />
    <meta name="robots" content="noindex" />

    <link
      rel="icon"
      href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%23FFB232'/%3E%3C/svg%3E"
    />

    <!-- Mesma ordem do index: tokens → base → layout → componentes → seção. -->
    <link rel="stylesheet" href="styles/tokens.css" />
    <link rel="stylesheet" href="styles/base.css" />
    <link rel="stylesheet" href="styles/layout.css" />
    <link rel="stylesheet" href="styles/components.css" />
    <link rel="stylesheet" href="styles/sections/hero.css" />
    <link rel="stylesheet" href="styles/sections/escrita-arquivo.css" />
    <link rel="stylesheet" href="styles/sections/leitor.css" />
    <link rel="stylesheet" href="styles/sections/busca.css" />

    <script type="module" src="scripts/main.js"></script>
  </head>
  <body>

    <a class="skip-link" href="#conteudo">Pular para o conteúdo</a>

    <header class="site-header" data-module="header">
      <div class="container site-header__inner">
        <a class="site-header__brand" href="index.html" aria-label="Página inicial">
          <img
            class="site-header__logo"
            src="assets/img/brand/logo-enrico-branco-1600.png"
            alt="Enrico Pierro"
            width="1600"
            height="751"
          />
        </a>

        <nav class="site-nav" id="menu-principal" aria-label="Principal">
          <ul class="site-nav__list">
            <li><a class="site-nav__link" href="index.html">Início</a></li>
            <li><a class="site-nav__link" href="index.html#quem-e">Quem é</a></li>
            <li><a class="site-nav__link" href="escrita.html" aria-current="page">Escrita</a></li>
            <li><a class="site-nav__link" href="episodios.html">ABCPOD</a></li>
            <li><a class="site-nav__link" href="contato.html">Contato</a></li>
          </ul>
        </nav>

        <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="menu-principal">
          <span class="visually-hidden">Menu</span>
          <span class="menu-toggle__bars" aria-hidden="true"></span>
        </button>
      </div>
    </header>

    <main id="conteudo">
      <!--
        ==================================================================
        Subpágina "a escrita"
        CSS: styles/sections/hero.css + styles/sections/escrita-arquivo.css
        JS:  esc-app.js (lateral), esc-shelf.js (fileiras), esc-leitor.js (janela)

        Página inteira gerada por ferramentas/gen-escrita-arquivo.py — edite o
        script, não este arquivo. Conteúdo importado do enricopierro.com.br
        via API pública do WordPress.com em {LIDO_EM}.
        ==================================================================
      -->
      <section class="hero hero--escrita" id="hero" aria-labelledby="esc-titulo">
        <div class="hero__intro">
          <span class="t-eyebrow hero__eyebrow">ACERVO LITERÁRIO</span>
          <h1 class="t-display-1 hero__headline" id="esc-titulo">todos os textos</h1>
          <p class="hero__sub">
            a coleção completa de colunas, reflexões e páginas do diário, reunidas em um só lugar.
          </p>
        </div>

        <figure class="hero__photo">
          <picture>
            <source
              type="image/webp"
              srcset="
                assets/img/hero/enrico-escrita-hero-480.webp 480w,
                assets/img/hero/enrico-escrita-hero-960.webp 960w
              "
              sizes="(width >= 900px) 44vw, 100vw"
            />
            <img
              src="assets/img/hero/enrico-escrita-hero-960.jpg"
              alt="Enrico Pierro sorrindo de óculos, assinando um livro aberto sobre a mesa."
              width="960"
              height="1200"
              decoding="async"
              fetchpriority="high"
            />
          </picture>
        </figure>

        <div class="hero__scrim" aria-hidden="true"></div>

        <div class="hero__bottom">
          <div class="container">
            <dl class="esc-stats">
              <div class="esc-stats__item">
                <dt class="t-footnote esc-stats__label">Publicações</dt>
                <dd class="esc-stats__value tabular">{total}</dd>
              </div>
              <div class="esc-stats__item">
                <dt class="t-footnote esc-stats__label">Primeiro texto</dt>
                <dd class="esc-stats__value tabular">{min(anos)}</dd>
              </div>
              <div class="esc-stats__item">
                <dt class="t-footnote esc-stats__label">Atualizado em</dt>
                <dd class="esc-stats__value tabular">{data_curta(ultima)}</dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <!--
        ==================================================================
        Casco de aplicativo — barra lateral em vidro + painel de conteúdo

        Estrutura do app do Apple Podcasts: a navegação mora numa lateral fixa
        com material translúcido, e o painel à direita mostra UM recorte por vez
        (uma categoria, um período). Foi o que resolveu o comprimento da página:
        antes as quatro categorias e os 44 períodos ficavam empilhados no mesmo
        rolo.

        A lateral vira uma barra horizontal rolável abaixo de 1040px — em tela
        estreita uma coluna fixa comeria metade do espaço de leitura.
        ==================================================================
      -->
      <!-- BUSCA. O índice (183 KB) só é baixado quando alguém digita a
           primeira letra: quem chega para ler um texto nunca paga por ele. -->
      <section class="busca" data-module="busca" data-src="assets/data/busca.json"
               data-buscando="nao" data-tem-texto="nao" aria-labelledby="busca-titulo">
        <div class="container busca__inner">
          <h2 class="visually-hidden" id="busca-titulo">Buscar nos textos</h2>
          <div class="busca__campo">
            <svg class="busca__lupa" viewBox="0 0 16 16" fill="none" stroke="currentColor"
                 stroke-width="1.6" stroke-linecap="round" aria-hidden="true">
              <circle cx="7" cy="7" r="4.25" /><path d="m10.5 10.5 3 3" />
            </svg>
            <input type="search" data-busca-campo
                   placeholder="buscar por palavra nos textos e episódios"
                   aria-label="Buscar por palavra nos textos e episódios"
                   autocomplete="off" spellcheck="false" />
            <button class="busca__limpar" type="button" data-busca-limpar>
              <span class="visually-hidden">Limpar a busca</span>
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7"
                   stroke-linecap="round" aria-hidden="true">
                <path d="m4.5 4.5 7 7M11.5 4.5l-7 7" />
              </svg>
            </button>
          </div>
          <p class="t-footnote busca__contagem" data-busca-contagem role="status" aria-live="polite"></p>
          <div data-busca-resultados></div>
        </div>
      </section>

      <div class="esc-app" data-busca-esconder data-module="esc-app">
        <aside class="esc-side" aria-label="Navegação do arquivo">
          <div class="esc-side__inner">
            <nav class="esc-side__grupo" aria-label="Categorias">
              <p class="t-eyebrow esc-side__label">Categorias</p>
              <ul class="esc-side__list" data-lista="categorias">
{categorias}
              </ul>
            </nav>

            <nav class="esc-side__grupo esc-side__grupo--periodos" aria-label="Períodos">
              <p class="t-eyebrow esc-side__label">Períodos</p>
{listas_periodo}
            </nav>
          </div>
        </aside>

        <div class="esc-main" data-module="esc-leitor" data-src="assets/data/textos">
{grupos_html}
        </div>
      </div>

{leitor.MARCACAO}
    </main>

    <footer class="site-footer">
      <div class="container site-footer__inner">
        <a class="site-footer__brand" href="index.html" aria-label="Página inicial">
          <img
            class="site-footer__logo"
            src="assets/img/brand/logo-enrico-branco-1600.png"
            alt="Enrico Pierro"
            width="1600"
            height="751"
          />
        </a>

        <p class="t-subhead site-footer__role">
          escritor, colunista e comunicador
        </p>

        <nav class="site-footer__nav" aria-label="Navegação do rodapé">
          <ul class="site-footer__list">
            <li><a class="site-footer__link" href="index.html">Início</a></li>
            <li><a class="site-footer__link" href="escrita.html">Escrita</a></li>
            <li><a class="site-footer__link" href="episodios.html">ABCPOD</a></li>
            <li><a class="site-footer__link" href="index.html#quem-e">Quem é</a></li>
            <li><a class="site-footer__link" href="contato.html">Contato</a></li>
          </ul>
        </nav>

        <ul class="site-footer__social">
          <li>
            <a class="social-link" href="https://www.instagram.com/enricopierroofc/"
               target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 1.366.062 2.633.336 3.608 1.311.975.975 1.249 2.242 1.311 3.608.058 1.266.07 1.646.07 4.85s-.012 3.584-.07 4.85c-.062 1.366-.336 2.633-1.311 3.608-.975.975-2.242 1.249-3.608 1.311-1.266.058-1.646.07-4.85.07s-3.584-.012-4.85-.07c-1.366-.062-2.633-.336-3.608-1.311-.975-.975-1.249-2.242-1.311-3.608C2.175 15.584 2.163 15.204 2.163 12s.012-3.584.07-4.85c.062-1.366.336-2.633 1.311-3.608.975-.975 2.242-1.249 3.608-1.311C8.416 2.175 8.796 2.163 12 2.163zm0 1.802c-3.15 0-3.503.012-4.74.068-1.04.048-1.79.22-2.35.78-.56.56-.732 1.31-.78 2.35-.056 1.237-.068 1.59-.068 4.74s.012 3.503.068 4.74c.048 1.04.22 1.79.78 2.35.56.56 1.31.732 2.35.78 1.237.056 1.59.068 4.74.068s3.503-.012 4.74-.068c1.04-.048 1.79-.22 2.35-.78.56-.56.732-1.31.78-2.35.056-1.237.068-1.59.068-4.74s-.012-3.503-.068-4.74c-.048-1.04-.22-1.79-.78-2.35-.56-.56-1.31-.732-2.35-.78-1.237-.056-1.59-.068-4.74-.068zM12 6.865a5.135 5.135 0 1 1 0 10.27 5.135 5.135 0 0 1 0-10.27zm0 8.468a3.333 3.333 0 1 0 0-6.666 3.333 3.333 0 0 0 0 6.666zm6.538-8.671a1.2 1.2 0 1 1-2.4 0 1.2 1.2 0 0 1 2.4 0z" /></svg>
              <span class="visually-hidden">Instagram de Enrico Pierro</span>
            </a>
          </li>
          <li>
            <a class="social-link" href="https://www.youtube.com/@abcPod"
               target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" /></svg>
              <span class="visually-hidden">Canal ABCPOD no YouTube</span>
            </a>
          </li>
          <li>
            <a class="social-link" href="https://open.spotify.com/show/65VR3AdKUStYuN5U55ymKt"
               target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.339-2.58-12.24-1.42-.42.18-1.02-.24-.9-.72.12-.48.48-.72.9-.84 4.5-1.32 10.08-.66 13.8 1.56.421.24.54.78.3 1.14l.002-.02zm.12-3.42C15.24 8.4 9.6 7.8 5.999 8.94c-.48.18-1.02-.18-1.2-.66-.18-.48.18-1.02.66-1.2C9.24 5.64 15.6 6.3 19.68 8.94c.48.3.6.96.3 1.44-.3.36-.84.48-1.2.18l-.002.001z" /></svg>
              <span class="visually-hidden">ABCPOD no Spotify</span>
            </a>
          </li>
          <li>
            <a class="social-link" href="https://www.youtube.com/@enricopierroofc"
               target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" /></svg>
              <span class="visually-hidden">Canal de Enrico Pierro no YouTube</span>
            </a>
          </li>
          <li>
            <a class="social-link" href="https://www.tiktok.com/@enricopierroofc"
               target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z" /></svg>
              <span class="visually-hidden">TikTok de Enrico Pierro</span>
            </a>
          </li>
          <li>
            <a class="social-link" href="https://x.com/enricopierroofc"
               target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" /></svg>
              <span class="visually-hidden">Enrico Pierro no X</span>
            </a>
          </li>
          <li>
            <a class="social-link" href="https://www.threads.com/@enricopierroofc"
               target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12.186 24h-.007c-3.581-.024-6.334-1.205-8.184-3.509C2.35 18.44 1.5 15.586 1.472 12.01v-.017c.03-3.579.879-6.43 2.525-8.482C5.845 1.205 8.6.024 12.18 0h.014c2.746.02 5.043.725 6.826 2.098 1.677 1.29 2.858 3.13 3.509 5.467l-2.04.569c-1.104-3.96-3.898-5.984-8.304-6.015-2.91.022-5.11.936-6.54 2.717C4.307 6.504 3.616 8.914 3.589 12c.027 3.086.718 5.496 2.057 7.164 1.43 1.783 3.631 2.698 6.54 2.717 2.623-.02 4.358-.631 5.8-2.045 1.647-1.613 1.618-3.593 1.09-4.798-.31-.71-.873-1.3-1.634-1.75-.192 1.352-.622 2.446-1.284 3.272-.886 1.102-2.14 1.704-3.73 1.79-1.202.065-2.361-.218-3.259-.801-1.063-.689-1.685-1.74-1.752-2.964-.065-1.19.408-2.285 1.33-3.082.88-.76 2.119-1.207 3.583-1.291a13.853 13.853 0 0 1 3.02.142c-.126-.742-.375-1.332-.75-1.757-.513-.586-1.308-.883-2.359-.89h-.029c-.844 0-1.992.232-2.721 1.32L7.734 7.847c.98-1.454 2.568-2.256 4.478-2.256h.044c3.194.02 5.097 1.975 5.287 5.388.108.046.216.094.32.144 1.494.7 2.585 1.766 3.156 3.083.795 1.83.868 4.815-1.556 7.188-1.853 1.814-4.102 2.628-7.277 2.65Zm1.043-12.32c-.202 0-.407.006-.616.018-1.834.103-2.974.94-2.91 2.132.067 1.25 1.446 1.83 2.772 1.759 1.22-.066 2.803-.54 3.071-3.7a10.293 10.293 0 0 0-2.317-.21Z" /></svg>
              <span class="visually-hidden">Enrico Pierro no Threads</span>
            </a>
          </li>
          <li>
            <a class="social-link" href="https://www.facebook.com/enricopierroofc"
               target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M24 12.073C24 5.405 18.627 0 12 0S0 5.405 0 12.073C0 18.1 4.388 23.094 10.125 24v-8.437H7.078v-3.49h3.047V9.412c0-3.025 1.792-4.696 4.533-4.696 1.313 0 2.686.236 2.686.236v2.953H15.83c-1.491 0-1.956.929-1.956 1.882v2.286h3.328l-.532 3.49h-2.796V24C19.612 23.094 24 18.1 24 12.073z" /></svg>
              <span class="visually-hidden">Facebook de Enrico Pierro</span>
            </a>
          </li>
        </ul>

        <div class="site-footer__divider" aria-hidden="true"></div>

        <div class="site-footer__bottom">
          <p class="t-footnote">
            <span aria-hidden="true">©</span> 2026 Enrico Pierro
          </p>
          <a
            class="t-footnote site-footer__bottom-link"
            href="https://www.amazon.com.br/stores/author/B0DVQCC67C"
            target="_blank"
            rel="noopener"
          >
            Livros na Amazon
            {seta()}
          </a>
        </div>
      </div>
    </footer>
  </body>
</html>
'''


def dados_json(grupos, total):
    return {
        "fonte": "enricopierro.com.br — API pública do WordPress.com",
        "lido_em": LIDO_EM,
        "total": total,
        "aviso": "conteudo completo de cada publicacao, importado um a um da API.",
        "grupos": [
            {
                "slug": g["slug"],
                "rotulo": g["rotulo"],
                "total": g["total"],
                "linha": g["linha"],
                "arquivo": f"escrita.html#esc-{g['slug']}",
                "posts": [
                    {
                        "titulo": p["titulo"],
                        "data": p["data"],
                        "slug": p["slug"],
                        "conteudo": p["conteudo"],
                    }
                    for p in g["posts"]
                ],
            }
            for g in grupos
        ],
    }


def leitura(texto):
    """O HTML da janela de leitura: a capa no alto, e depois o texto."""
    capa = (texto.get("capa") or "").strip()
    corpo = texto["body"]
    topo = "" if (capa and capa in corpo) else figura(capa)
    return topo + para_html(corpo)


def monta_do_conteudo():
    """Os arquivos de conteudo/textos/ → a mesma lista de grupos que o monta()."""
    conhecidas = {g["slug"] for g in GRUPOS}
    agrupados = {slug: [] for slug in conhecidas}
    ignorados = 0

    for texto in ler_colecao("textos"):
        if texto.get("publicado") is False:
            ignorados += 1
            continue
        categoria = texto.get("categoria")
        if categoria not in conhecidas:
            categoria = "outros"
        agrupados[categoria].append(
            {
                "titulo": texto["titulo"],
                "data": texto["data"],
                "slug": texto["slug"],
                "enquadramento": texto.get("enquadramento"),
                "conteudo": leitura(texto),
            }
        )

    grupos = []
    for g in GRUPOS:
        itens = agrupados[g["slug"]]
        itens.sort(key=lambda x: x["data"], reverse=True)
        grupos.append({**g, "total": len(itens), "posts": itens})
    return grupos, ignorados


def escrever_textos_json(grupos):
    """Um JSON por texto, que é o que o leitor busca ao abrir."""
    destino = RAIZ / "assets/data/textos"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)

    n = 0
    for g in grupos:
        for post in g["posts"]:
            (destino / f"{post['slug']}.json").write_text(
                json.dumps(
                    {
                        "slug": post["slug"],
                        "titulo": post["titulo"],
                        "data": post["data"],
                        "categoria": g["rotulo"],
                        "conteudo": post["conteudo"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            n += 1
    return n


def importar_do_wordpress(offline=False):
    """Traz posts do WordPress para conteudo/textos/ sem tocar no que já existe."""
    destino = PROJETO / "conteudo/textos"
    destino.mkdir(parents=True, exist_ok=True)
    existentes = {p.stem for p in destino.glob("*.md")}

    posts = busca(offline=offline)
    novos = 0
    for g in monta(posts):
        for post in g["posts"]:
            if post["slug"] in existentes:
                continue
            escrever(
                destino / f"{post['slug']}.md",
                {
                    "titulo": post["titulo"],
                    "data": post["data"],
                    "categoria": g["slug"],
                    "publicado": True,
                    "url_original": post["url"],
                },
                post["conteudo"],
            )
            novos += 1

    print(f"  {len(posts)} no WordPress, {len(existentes)} já em conteudo/, {novos} novo(s)")
    if novos:
        print("  atenção: as imagens dos textos novos ainda apontam para o WordPress.")
        print("           rode baixar-acervo.py e reescrever-acervo.py para trazê-las.")
    return novos


def main():
    if "--importar" in sys.argv:
        offline = "--offline" in sys.argv
        print("gen-escrita-arquivo: importando do WordPress"
              + (" (cache local)" if offline else f" ({SITE})"))
        importar_do_wordpress(offline=offline)
        print()

    grupos, rascunhos = monta_do_conteudo()
    total = sum(g["total"] for g in grupos)

    pagina_html = pagina(grupos, total)
    (RAIZ / "escrita.html").write_text(pagina_html, encoding="utf-8")
    escritos = escrever_textos_json(grupos)

    for g in grupos:
        print(f"  {g['slug']:<8} {g['total']:>3} textos")
    print(f"  total   {total:>3} textos" + (f"  ({rascunhos} rascunho fora)" if rascunhos else ""))
    print(f"  -> escrita.html ({len(pagina_html):,} bytes) e {escritos} arquivos em assets/data/textos/")


if __name__ == "__main__":
    main()
