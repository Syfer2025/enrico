#!/usr/bin/env python3
"""gen-publicacao.py — o que o site precisa para existir na internet."""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

from conteudo import ler_colecao, ler_json

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"

PAGINAS = {
    "index.html": {
        "titulo": "Enrico Pierro — escritor, colunista e comunicador",
        "descricao": "Escritor, colunista e comunicador. Autor de as marés do meu "
                     "ser, as ondas do meu ser e amores que tropeçam, e apresentador "
                     "do abcpod.",
        "prioridade": "1.0",
    },
    "escrita.html": {
        "titulo": "A escrita — Enrico Pierro",
        "descricao": "Os 577 textos de Enrico Pierro: a coluna semanal, o diário e "
                     "o acervo aberto de prosa e poesia, para ler de ponta a ponta.",
        "prioridade": "0.9",
    },
    "episodios.html": {
        "titulo": "Os episódios do abcpod — Enrico Pierro",
        "descricao": "Os 67 episódios do abcpod, o podcast de Enrico Pierro: "
                     "conversas com nomes da cultura e do cotidiano, em vídeo e "
                     "em áudio.",
        "prioridade": "0.9",
    },
    "contato.html": {
        "titulo": "Contato e imprensa — Enrico Pierro",
        "descricao": "Como falar com Enrico Pierro: imprensa, eventos, palestras "
                     "e parcerias.",
        "prioridade": "0.8",
    },
}

MARCA_INICIO = "<!-- PUBLICACAO:INICIO (gerado por ferramentas/gen-publicacao.py) -->"
MARCA_FIM = "<!-- PUBLICACAO:FIM -->"


def cabecalho(pagina: str, dados: dict, cfg: dict) -> str:
    """As meta tags de uma página."""
    e = html.escape
    base = cfg["dominio"].rstrip("/")
    endereco = base + "/" + ("" if pagina == "index.html" else pagina)
    imagem = base + cfg["og_imagem"]
    no_ar = bool(cfg.get("no_ar"))

    linhas = [
        MARCA_INICIO,
        f'    <meta name="description" content="{e(dados["descricao"])}" />',
    ]

    if no_ar:
        linhas.append(f'    <link rel="canonical" href="{e(endereco)}" />')
    else:
        linhas += [
            '    <!-- noindex enquanto o site está no endereço temporário do',
            '         GitHub: indexar este endereço criaria um resultado de busca',
            '         que morre quando o domínio apontar para cá. Some quando o',
            '         conteudo/site.json marcar no_ar: true. -->',
            '    <meta name="robots" content="noindex, nofollow" />',
        ]

    linhas += [
        "",
        "    <!-- Prévia do link no WhatsApp, Instagram, Facebook e X. -->",
        '    <meta property="og:type" content="website" />',
        f'    <meta property="og:site_name" content="{e(cfg["titulo"])}" />',
        f'    <meta property="og:title" content="{e(dados["titulo"])}" />',
        f'    <meta property="og:description" content="{e(dados["descricao"])}" />',
        f'    <meta property="og:url" content="{e(endereco)}" />',
        f'    <meta property="og:image" content="{e(imagem)}" />',
        '    <meta property="og:image:width" content="1200" />',
        '    <meta property="og:image:height" content="630" />',
        '    <meta property="og:image:alt" content="Enrico Pierro sorrindo diante '
        'do microfone, no estúdio do abcpod." />',
        '    <meta property="og:locale" content="pt_BR" />',
        '    <meta name="twitter:card" content="summary_large_image" />',
        "",
        "    <!-- Ícones. O favicon.ico cobre navegador antigo; o de 512 vai para",
        "         a tela inicial no Android, e o apple-touch no iPhone.",
        "         Caminho RELATIVO: o site pode ser servido de um subcaminho",
        "         (…/enrico/), e a barra inicial procuraria na raiz do domínio. -->",
        '    <link rel="icon" href="favicon.ico" sizes="any" />',
        '    <link rel="icon" href="icone-512.png" type="image/png" sizes="512x512" />',
        '    <link rel="apple-touch-icon" href="apple-touch-icon.png" />',
        MARCA_FIM,
    ]
    return "\n".join(linhas)


def injetar(pagina: str, dados: dict, cfg: dict) -> bool:
    caminho = SITE / pagina
    if not caminho.exists():
        return False
    s = caminho.read_text(encoding="utf-8")
    bloco = cabecalho(pagina, dados, cfg)

    if MARCA_INICIO in s:
        i = s.index(MARCA_INICIO)
        f = s.index(MARCA_FIM) + len(MARCA_FIM)
        s = s[:i] + bloco + s[f:]
    else:
        s = re.sub(r'\n\s*<meta name="description"[^>]*/>', "", s)
        s = re.sub(r'\n\s*<meta name="robots"[^>]*/>', "", s)
        s = re.sub(r'\n\s*<link\s+rel="icon"\s+href="data:image/svg\+xml[^>]*/>', "", s, flags=re.S)
        s = re.sub(r"(</title>)", r"\1\n\n" + bloco.replace("\\", "\\\\"), s, count=1)

    caminho.write_text(s, encoding="utf-8")
    return True


def sitemap(cfg: dict, paginas: list[str]) -> Path:
    base = cfg["dominio"].rstrip("/")
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for pagina in paginas:
        endereco = base + "/" + ("" if pagina == "index.html" else pagina)
        linhas += ["  <url>",
                   f"    <loc>{html.escape(endereco)}</loc>",
                   f"    <priority>{PAGINAS[pagina]['prioridade']}</priority>",
                   "  </url>"]
    linhas.append("</urlset>")
    destino = SITE / "sitemap.xml"
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino


def robots(cfg: dict) -> Path:
    base = cfg["dominio"].rstrip("/")
    if cfg.get("no_ar"):
        corpo = ["User-agent: *",
                 "Allow: /",
                 "",
                 "# O painel de edição não é conteúdo.",
                 "Disallow: /admin/",
                 "",
                 f"Sitemap: {base}/sitemap.xml"]
    else:
        corpo = ["# O site está num endereço temporário e ainda não deve ser",
                 "# indexado. Quando o domínio apontar para cá, o",
                 "# conteudo/site.json marca no_ar: true e este arquivo libera.",
                 "User-agent: *",
                 "Disallow: /"]
    destino = SITE / "robots.txt"
    destino.write_text("\n".join(corpo) + "\n", encoding="utf-8")
    return destino


def redirecionamentos(cfg: dict) -> tuple[int, int]:
    """Um arquivo por endereço antigo, levando ao texto novo."""
    base = cfg["dominio"].rstrip("/")
    feitos = 0
    ignorados = 0
    caminhos: set[str] = set()

    for texto in ler_colecao("textos"):
        if texto.get("publicado") is False:
            ignorados += 1
            continue
        antigo = (texto.get("url_original") or "").strip()
        if not antigo:
            ignorados += 1
            continue

        caminho = urlparse(antigo).path.strip("/")
        if not caminho:
            ignorados += 1
            continue
        caminhos.add(caminho)

        destino_url = f"{base}/escrita.html#{texto['slug']}"
        pasta = SITE / caminho
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "index.html").write_text(
            "<!doctype html>\n"
            '<html lang="pt-BR">\n'
            "  <head>\n"
            '    <meta charset="utf-8" />\n'
            f'    <title>{html.escape(texto["titulo"])} — Enrico Pierro</title>\n'
            f'    <link rel="canonical" href="{html.escape(destino_url)}" />\n'
            f'    <meta http-equiv="refresh" content="0; url={html.escape(destino_url)}" />\n'
            '    <meta name="robots" content="noindex, follow" />\n'
            "  </head>\n"
            "  <body>\n"
            f'    <p>Este texto mudou de endereço. '
            f'<a href="{html.escape(destino_url)}">Ler «{html.escape(texto["titulo"])}»</a>.</p>\n'
            "  </body>\n"
            "</html>\n",
            encoding="utf-8",
        )
        feitos += 1

    return feitos, ignorados


def pagina_404(cfg: dict) -> Path:
    """404 com a cara do site, e não a página crua do GitHub."""
    base = cfg["dominio"].rstrip("/")
    prefixo = urlparse(base).path.rstrip("/")
    destino = SITE / "404.html"
    destino.write_text(f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>Página não encontrada — Enrico Pierro</title>
    <meta name="robots" content="noindex" />
    <link rel="icon" href="{prefixo}/favicon.ico" sizes="any" />
    <link rel="stylesheet" href="{prefixo}/styles/tokens.css" />
    <link rel="stylesheet" href="{prefixo}/styles/base.css" />
    <link rel="stylesheet" href="{prefixo}/styles/layout.css" />
    <link rel="stylesheet" href="{prefixo}/styles/components.css" />
    <style>
      /* Uma tela só, centrada. Não vale puxar o CSS de seção nenhuma para isto. */
      .erro {{
        display: grid;
        place-content: center;
        justify-items: center;
        gap: var(--space-4);
        min-height: 100svh;
        padding: var(--space-6) var(--gutter);
        text-align: center;
      }}
      .erro__numero {{
        font-family: var(--font-display);
        font-size: clamp(4rem, 18vw, 8rem);
        line-height: 1;
        font-weight: var(--weight-heavy);
        letter-spacing: -0.03em;
        color: var(--accent);
      }}
      .erro__texto {{ max-width: 34ch; color: var(--label-secondary); }}
      .erro__acoes {{ display: flex; flex-wrap: wrap; gap: var(--space-3); justify-content: center; }}
    </style>
  </head>
  <body>
    <main class="erro">
      <p class="erro__numero">404</p>
      <h1 class="t-display-2">esta página não existe</h1>
      <p class="t-body erro__texto">
        O endereço pode ter mudado, ou o link que te trouxe até aqui pode estar
        com um erro de digitação.
      </p>
      <div class="erro__acoes">
        <a class="btn btn--accent" href="{prefixo}/">
          <span class="btn__label">ir para a página inicial</span>
        </a>
        <a class="btn" href="{prefixo}/escrita.html">
          <span class="btn__label">ver todos os textos</span>
        </a>
      </div>
    </main>
  </body>
</html>
""", encoding="utf-8")
    return destino


def main() -> int:
    cfg = ler_json("site.json")
    no_ar = bool(cfg.get("no_ar"))

    print(f"domínio: {cfg['dominio']}")
    print(f"no ar:   {'sim' if no_ar else 'não — as páginas ficam com noindex'}\n")

    injetadas = [p for p, d in PAGINAS.items() if injetar(p, d, cfg)]
    print(f"prévia de link e ícones em {len(injetadas)} página(s): {', '.join(injetadas)}")

    caminho = sitemap(cfg, injetadas)
    print(f"{caminho.name} com {len(injetadas)} endereços")

    caminho = robots(cfg)
    print(f"{caminho.name} — {'liberado' if no_ar else 'bloqueado (endereço temporário)'}")

    caminho = pagina_404(cfg)
    print(f"{caminho.name} com a cara do site")

    feitos, ignorados = redirecionamentos(cfg)
    print(f"{feitos} redirecionamentos de endereço antigo"
          + (f" ({ignorados} sem endereço antigo, ficaram de fora)" if ignorados else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
