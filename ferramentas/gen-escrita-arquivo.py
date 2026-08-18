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

import moldura
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
    <title>a escrita — enrico pierro</title>
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

    <a class="skip-link" href="#conteudo">pular para o conteúdo</a>

    {moldura.cabecalho("escrita.html")}

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
          <span class="t-eyebrow hero__eyebrow">acervo literário</span>
          <h1 class="t-display-1 hero__headline" id="esc-titulo">todos os textos</h1>
          <p class="hero__sub">
            tudo o que eu já escrevi e publiquei: a coluna, o diário e os textos soltos.
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
                <dt class="t-footnote esc-stats__label">publicações</dt>
                <dd class="esc-stats__value tabular">{total}</dd>
              </div>
              <div class="esc-stats__item">
                <dt class="t-footnote esc-stats__label">primeiro texto</dt>
                <dd class="esc-stats__value tabular">{min(anos)}</dd>
              </div>
              <div class="esc-stats__item">
                <dt class="t-footnote esc-stats__label">atualizado em</dt>
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

    {moldura.rodape()}
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
