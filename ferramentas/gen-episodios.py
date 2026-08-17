#!/usr/bin/env python3
"""gen-episodios.py — grava assets/data/episodios.json e escreve episodios.html"""

import html
import json
import pathlib

import moldura
from conteudo import ler_colecao

RAIZ = pathlib.Path(__file__).resolve().parent.parent / "publicar"
LIDO_EM = "2026-08-05"

CANAL = "https://www.youtube.com/@abcPod"
CANAL_ID = "UCKlHDYrLSJYldYdlixoUuCA"
SHOW_SPOTIFY = "https://open.spotify.com/show/65VR3AdKUStYuN5U55ymKt"
EMBED_SPOTIFY = (
    "https://open.spotify.com/embed/show/65VR3AdKUStYuN5U55ymKt"
    "?utm_source=generator&theme=0"
)
PLAYLIST = "https://www.youtube.com/playlist?list=PL3KBGAAHePexdkpK6gZB1bCnIh-tjVU6N"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]
MESES_LONGOS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho",
                "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]

def carregar_episodios():
    return [
        (
            ep["youtube_id"],
            ep["temporada"],
            ep["episodio"],
            ep["convidado"],
            ep["publicado_em"],
            ep["duracao_s"],
            ep["visualizacoes"],
        )
        for ep in ler_colecao("episodios", ordenar_por="publicado_em")
    ]


EPISODIOS = carregar_episodios()

TEMPORADAS = [
    (1, "1ª temporada"),
    (2, "2ª temporada"),
    (3, "3ª temporada"),
    (4, "4ª temporada"),
    (None, "Especiais"),
]

ORDEM_TEMPORADAS = [t for t, _ in TEMPORADAS if t is not None][::-1] + [None]

MOSAICO_COLUNAS = 5
MOSAICO_LINHAS = 8
FOTOS_MURAL = {
    **{f"ep-{i:02d}": (960, 540) for i in range(1, 12)},
    "ep-12": (960, 720),
    "ep-13": (960, 540),
    "ep-14": (960, 685),
    "ep-15": (960, 540),
    "ep-16": (960, 540),
    **{f"ep-{i:02d}": (960, 720) for i in range(17, 21)},
}


def data_curta(iso):
    ano, mes, dia = iso.split("-")
    return f"{dia} {MESES[int(mes) - 1]} {ano}"


def data_longa(iso):
    ano, mes, dia = iso.split("-")
    return f"{int(dia)} de {MESES_LONGOS[int(mes) - 1]} de {ano}"


def duracao(segundos):
    """3656 → '1h 00min'; 3200 → '53min'. Minuto arredondado para baixo."""
    h, m = divmod(segundos // 60, 60)
    return f"{h}h {m:02d}min" if h else f"{m}min"


def duracao_falada(segundos):
    h, m = divmod(segundos // 60, 60)
    if not h:
        return f"{m} minutos"
    return f"{h} hora{'s' if h > 1 else ''} e {m} minutos"


def rotulo(temporada, ep):
    return f"T{temporada:02d}E{ep:02d}" if temporada else "Especial"


def ancora(temporada):
    return f"temporada-{temporada}" if temporada else "especiais"


def horas_totais():
    return round(sum(e[5] for e in EPISODIOS) / 3600)


def card(vid, temporada, ep, nome, data, segundos, _views):
    e = html.escape
    marca = rotulo(temporada, ep)
    return f'''            <li class="ep-card">
              <a class="ep-card__link" href="https://www.youtube.com/watch?v={vid}"
                 target="_blank" rel="noopener">
                <span class="ep-card__thumb">
                  <img
                    src="https://i.ytimg.com/vi/{vid}/mqdefault.jpg"
                    srcset="https://i.ytimg.com/vi/{vid}/mqdefault.jpg 320w,
                            https://i.ytimg.com/vi/{vid}/hq720.jpg 1280w"
                    sizes="(width >= 1040px) 24vw, (width >= 700px) 44vw, 92vw"
                    alt=""
                    width="320"
                    height="180"
                    loading="lazy"
                    decoding="async"
                  />
                  <span class="ep-card__duration tabular" aria-hidden="true">{duracao(segundos)}</span>
                </span>

                <span class="ep-card__body">
                  <span class="t-eyebrow ep-card__num">{marca}</span>
                  <span class="ep-card__name">{e(nome)}</span>
                  <time class="t-footnote ep-card__date tabular" datetime="{data}">{data_curta(data)}</time>
                </span>

                <!-- Só o que NÃO está visível. Repetir aqui o rótulo, o nome e a
                     data faria o leitor de tela anunciar o card duas vezes: o
                     nome acessível do link é a soma de todo o conteúdo, e o
                     selo de duração é aria-hidden porque é redundante com esta
                     linha. -->
                <span class="visually-hidden">— {duracao_falada(segundos)}, assistir no YouTube</span>
              </a>
            </li>'''


def grupo(temporada, titulo):
    da_temporada = [x for x in EPISODIOS if x[1] == temporada]
    if not da_temporada:
        return ""

    da_temporada = sorted(da_temporada, key=lambda x: x[4], reverse=True)
    cards = "\n\n".join(card(*x) for x in da_temporada)
    n = len(da_temporada)
    plural = "episódio" if n == 1 else "episódios"
    id_titulo = f"{ancora(temporada)}-titulo"

    return f'''        <section class="ep-season" id="{ancora(temporada)}" aria-labelledby="{id_titulo}" data-reveal>
          <header class="ep-season__head">
            <h3 class="t-title-2 ep-season__title" id="{id_titulo}">{titulo}</h3>
            <p class="t-footnote ep-season__count tabular">{n} {plural}</p>
          </header>

          <ul class="ep-grid">
{cards}
          </ul>
        </section>'''


def mosaico():
    """Plano inclinado de fotos à direita do título."""
    slugs = list(FOTOS_MURAL)
    n = len(slugs)

    ciclo = n // MOSAICO_COLUNAS

    def indice(coluna, linha):
        return (linha * MOSAICO_COLUNAS + coluna + 2 * (linha // ciclo)) % n

    for c in range(MOSAICO_COLUNAS):
        for l in range(MOSAICO_LINHAS):
            atual = indice(c, l)
            if l + 1 < MOSAICO_LINHAS:
                assert atual != indice(c, l + 1), "foto repetida na vertical"
            if c + 1 < MOSAICO_COLUNAS:
                assert atual != indice(c + 1, l), "foto repetida na horizontal"

    colunas = []
    for c in range(MOSAICO_COLUNAS):
        tiles = []
        for l in range(MOSAICO_LINHAS):
            slug = slugs[indice(c, l)]
            larg, alt = FOTOS_MURAL[slug]
            tiles.append(f'''                <li class="ep-mosaic__tile">
                  <picture>
                    <source
                      type="image/webp"
                      srcset="
                        assets/img/wall/{slug}-480.webp 480w,
                        assets/img/wall/{slug}-960.webp 960w
                      "
                      sizes="12rem"
                    />
                    <img
                      src="assets/img/wall/{slug}-960.jpg"
                      alt=""
                      width="{larg}"
                      height="{alt}"
                      loading="lazy"
                      decoding="async"
                    />
                  </picture>
                </li>''')
        colunas.append(
            '              <ul class="ep-mosaic__col">\n'
            + "\n".join(tiles)
            + "\n              </ul>"
        )

    return '''        <figure class="ep-mosaic" aria-hidden="true">
          <div class="ep-mosaic__veu">
            <div class="ep-mosaic__plane">
''' + "\n\n".join(colunas) + '''
            </div>
          </div>
        </figure>'''


def pilulas():
    itens = [
        '          <li><a class="ep-jump__link" href="#todas">Todas</a></li>'
    ]
    titulos = dict(TEMPORADAS)
    for temporada in ORDEM_TEMPORADAS:
        if not any(x[1] == temporada for x in EPISODIOS):
            continue
        titulo = titulos[temporada]
        curto = titulo.replace(" temporada", "") if temporada else titulo
        itens.append(
            f'          <li><a class="ep-jump__link" href="#{ancora(temporada)}">{curto}</a></li>'
        )
    return "\n".join(itens)


def pagina():
    total = len(EPISODIOS)
    temporadas = len({x[1] for x in EPISODIOS if x[1]})
    titulos = dict(TEMPORADAS)
    grupos = "\n\n".join(
        g for g in (grupo(t, titulos[t]) for t in ORDEM_TEMPORADAS) if g
    )

    return f'''<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>Episódios do abcpod — Enrico Pierro</title>
    <meta
      name="description"
      content="Todos os {total} episódios do abcpod, o podcast de Enrico Pierro: {temporadas} temporadas no YouTube e a versão em áudio no Spotify."
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
    <link rel="stylesheet" href="styles/sections/episodios.css" />

    <script type="module" src="scripts/main.js"></script>
  </head>
  <body>

    <a class="skip-link" href="#conteudo">pular para o conteúdo</a>

    {moldura.cabecalho("episodios.html")}

    <main id="conteudo">
      <!--
        ==================================================================
        Cabeçalho da página
        CSS: styles/sections/episodios.css   (não precisa de JS próprio)

        Página inteira gerada por ferramentas/gen-episodios.py — edite o script,
        não este arquivo.
        ==================================================================
      -->
      <section class="ep-hero" aria-labelledby="ep-titulo">
        <div class="container">
          <p class="t-eyebrow ep-hero__eyebrow">ABCPOD</p>
          <h1 class="t-display-1 ep-hero__title" id="ep-titulo">os episódios</h1>
          <p class="ep-hero__standfirst">
            as conversas completas do abcpod, do primeiro episódio ao mais
            recente. em vídeo no youtube, em áudio no spotify.
          </p>

          <dl class="ep-stats">
            <div class="ep-stats__item">
              <dt class="t-footnote ep-stats__label">ABCPOD</dt>
              <dd class="ep-stats__value tabular">{total}</dd>
            </div>
            <div class="ep-stats__item">
              <dt class="t-footnote ep-stats__label">Temporadas</dt>
              <dd class="ep-stats__value tabular">{temporadas}</dd>
            </div>
            <div class="ep-stats__item">
              <dt class="t-footnote ep-stats__label">Horas de conversa</dt>
              <dd class="ep-stats__value tabular">{horas_totais()}</dd>
            </div>
          </dl>

          <div class="ep-hero__ctas">
            <a class="btn btn--light" href="{CANAL}" target="_blank" rel="noopener">
              <svg class="btn__icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" /></svg>
              <span class="btn__label">canal no YouTube</span>
            </a>
            <a class="btn btn--glass" href="{SHOW_SPOTIFY}" target="_blank" rel="noopener">
              <svg class="btn__icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.339-2.58-12.24-1.42-.42.18-1.02-.24-.9-.72.12-.48.48-.72.9-.84 4.5-1.32 10.08-.66 13.8 1.56.421.24.54.78.3 1.14l.002-.02zm.12-3.42C15.24 8.4 9.6 7.8 5.999 8.94c-.48.18-1.02-.18-1.2-.66-.18-.48.18-1.02.66-1.2C9.24 5.64 15.6 6.3 19.68 8.94c.48.3.6.96.3 1.44-.3.36-.84.48-1.2.18l-.002.001z" /></svg>
              <span class="btn__label">Show no Spotify</span>
            </a>
          </div>
        </div>

{mosaico()}
      </section>

      <!--
        ==================================================================
        Spotify — player do show

        É o embed oficial da página do show, e não uma lista montada aqui:
        a lista de episódios do Spotify não é acessível sem credenciais de
        API. Vantagem: o player toca na própria página e nunca fica velho.
        ==================================================================
      -->
      <section class="ep-audio" aria-labelledby="ep-audio-titulo">
        <div class="container ep-audio__inner">
          <div class="ep-audio__intro" data-reveal>
            <span class="ep-audio__logo ep-audio__logo--spotify" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.339-2.58-12.24-1.42-.42.18-1.02-.24-.9-.72.12-.48.48-.72.9-.84 4.5-1.32 10.08-.66 13.8 1.56.421.24.54.78.3 1.14l.002-.02zm.12-3.42C15.24 8.4 9.6 7.8 5.999 8.94c-.48.18-1.02-.18-1.2-.66-.18-.48.18-1.02.66-1.2C9.24 5.64 15.6 6.3 19.68 8.94c.48.3.6.96.3 1.44-.3.36-.84.48-1.2.18l-.002.001z" /></svg>
            </span>
            <h2 class="t-title-2 ep-audio__title" id="ep-audio-titulo">Ouvir em áudio</h2>
            <p class="t-body ep-audio__text">
              o catálogo em áudio toca aqui mesmo, direto do spotify — a lista
              abaixo é a do próprio show e sempre traz o episódio mais novo.
            </p>
            <a class="ep-audio__link" href="{SHOW_SPOTIFY}" target="_blank" rel="noopener">
              <span>abrir no Spotify</span>
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75"
                   stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M6 3.25 10.75 8 6 12.75" />
              </svg>
            </a>
          </div>

          <div class="ep-audio__frame">
            <iframe
              class="ep-audio__embed"
              src="{EMBED_SPOTIFY}"
              width="100%"
              height="352"
              title="ABCPOD no Spotify — lista de episódios"
              loading="lazy"
              allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            ></iframe>
          </div>
        </div>
      </section>

      <!--
        ==================================================================
        YouTube — o arquivo completo, agrupado por temporada

        As capas vêm do CDN de thumbnails do YouTube (i.ytimg.com), não do
        assets/: são {total} imagens que mudam quando o canal muda de capa, e
        baixá-las colocaria uma cópia velha no repositório. Todas em
        `loading="lazy"`, com `width`/`height` para não haver salto de
        layout.
        ==================================================================
      -->
      <section class="ep-archive" aria-labelledby="ep-archive-titulo">
        <div class="container">
          <header class="ep-archive__head" data-reveal>
            <span class="ep-audio__logo ep-audio__logo--youtube" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z" /></svg>
            </span>
            <h2 class="t-largetitle ep-archive__title" id="ep-archive-titulo">assistir em vídeo</h2>
            <p class="t-body ep-archive__text">
              {total} episódios completos no canal <a class="ep-archive__handle" href="{CANAL}" target="_blank" rel="noopener">@abcPod</a>,
              em {temporadas} temporadas. cada card abre o episódio no youtube.
            </p>
          </header>

          <nav class="ep-jump" data-module="ep-jump" aria-label="Ir para a temporada">
            <ul class="ep-jump__list">
{pilulas()}
            </ul>
          </nav>
        </div>

        <div class="container ep-archive__body">
{grupos}
        </div>

        <div class="container">
          <a class="ep-archive__top" href="#conteudo">
            <span>Voltar ao topo</span>
            <svg
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M8 12.75V3.25" />
              <path d="M3.5 7.5 8 3l4.5 4.5" />
            </svg>
          </a>
        </div>
      </section>
    </main>

    {moldura.rodape()}
  </body>
</html>
'''


def dados():
    return {
        "fontes": {
            "youtube": {
                "canal": CANAL,
                "canal_id": CANAL_ID,
                "playlist": PLAYLIST,
                "nota": "aba de videos do canal (paginada), playlist ABCPOD e a pagina de cada video",
            },
            "spotify": {
                "show": SHOW_SPOTIFY,
                "nota": "lista de episodios inacessivel sem credenciais de API; a pagina usa o player embed oficial",
            },
        },
        "lido_em": LIDO_EM,
        "aviso": "visualizacoes envelhecem e nao sao exibidas na pagina; so os episodios completos entram (cortes e shorts ficam fora)",
        "total": len(EPISODIOS),
        "horas": horas_totais(),
        "episodios": [
            {
                "youtube_id": vid,
                "temporada": t,
                "episodio": ep,
                "rotulo": rotulo(t, ep),
                "nome": nome,
                "publicado_em": data,
                "duracao_s": seg,
                "visualizacoes": views,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "thumb": f"https://i.ytimg.com/vi/{vid}/hq720.jpg",
            }
            for vid, t, ep, nome, data, seg, views in EPISODIOS
        ],
    }


if __name__ == "__main__":
    arquivo = RAIZ / "assets/data/episodios.json"
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(
        json.dumps(dados(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    (RAIZ / "episodios.html").write_text(pagina(), encoding="utf-8")

    print(
        f"{len(EPISODIOS)} episódios, {horas_totais()} h "
        f"-> assets/data/episodios.json e episodios.html"
    )
