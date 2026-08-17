#!/usr/bin/env python3
"""gen-contato.py — a página de contato e imprensa."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import moldura
from conteudo import ler_json

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"

CANAIS = [
    {
        "titulo": "imprensa",
        "linha": "entrevistas, participações e pedidos de material",
        "detalhe": "fotos em alta resolução, biografia e capas dos livros estão "
                   "disponíveis para veículos — peça por e-mail e mando na hora.",
    },
    {
        "titulo": "eventos e palestras",
        "linha": "feiras, festivais, escolas e empresas",
        "detalhe": "para convites, o e-mail é o caminho mais rápido. vale incluir "
                   "data, cidade e formato do evento na primeira mensagem.",
    },
    {
        "titulo": "parcerias",
        "linha": "editoras, marcas e o abcpod",
        "detalhe": "propostas de parceria, publicidade no podcast e convites para "
                   "episódio também entram pelo e-mail.",
    },
]

REDES = [
    ("Instagram", "https://www.instagram.com/enricopierroofc/"),
    ("YouTube", "https://www.youtube.com/@enricopierroofc"),
    ("TikTok", "https://www.tiktok.com/@enricopierroofc"),
    ("Threads", "https://www.threads.com/@enricopierroofc"),
    ("X", "https://x.com/enricopierroofc"),
    ("Facebook", "https://www.facebook.com/enricopierroofc"),
]


def bloco_do_email(email: str) -> str:
    """O endereço, ou um aviso claro de que ele ainda não existe."""
    if email:
        e = html.escape(email)
        return f"""          <div class="contato__email">
            <p class="t-eyebrow contato__email-rotulo">e-mail</p>
            <a class="contato__email-endereco" href="mailto:{e}">{e}</a>
            <p class="t-footnote contato__email-nota">resposta em até dois dias úteis.</p>
          </div>"""
    return """          <p class="contato__pendente" role="status">
            <strong>Falta o e-mail de contato.</strong> Preencha
            <code>email_contato</code> em <code>conteudo/site.json</code> e rode
            <code>ferramentas/gen-contato.py</code> de novo. Até então esta
            página não tem como receber mensagem.
          </p>"""


def main() -> int:
    cfg = ler_json("site.json")
    email = (cfg.get("email_contato") or "").strip()

    cabecalho = moldura.cabecalho("contato.html")
    rodape = moldura.rodape()

    canais = "\n".join(
        f"""          <li class="contato-canal">
            <h2 class="t-title-3 contato-canal__titulo">{html.escape(c['titulo'])}</h2>
            <p class="t-footnote contato-canal__linha">{html.escape(c['linha'])}</p>
            <p class="t-body contato-canal__detalhe">{html.escape(c['detalhe'])}</p>
          </li>"""
        for c in CANAIS
    )

    redes = "\n".join(
        f'            <li><a class="contato__rede" href="{u}" target="_blank" '
        f'rel="noopener">{html.escape(n)}</a></li>'
        for n, u in REDES
    )

    pagina = f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>contato e imprensa — enrico pierro</title>
    <meta name="theme-color" content="#08090C" />

    <link rel="stylesheet" href="styles/tokens.css" />
    <link rel="stylesheet" href="styles/base.css" />
    <link rel="stylesheet" href="styles/layout.css" />
    <link rel="stylesheet" href="styles/components.css" />
    <link rel="stylesheet" href="styles/sections/contato.css" />

    <script type="module" src="scripts/main.js"></script>
  </head>
  <body>
    <a class="skip-link" href="#conteudo">pular para o conteúdo</a>

    {cabecalho}

    <main id="conteudo">
      <section class="contato" aria-labelledby="contato-titulo">
        <div class="container contato__inner">
          <div class="contato__topo">
            <div class="contato__abertura">
              <p class="t-eyebrow contato__eyebrow">contato</p>
              <h1 class="t-display-2" id="contato-titulo">como falar com o enrico</h1>
              <p class="t-body contato__intro">
                para imprensa, eventos, palestras e parcerias, o
                <span class="nao-quebra">e-mail</span> é o caminho mais direto.
              </p>
            </div>

{bloco_do_email(email)}
          </div>

          <ul class="contato-canais">
{canais}
          </ul>

          <div class="contato__redes">
            <h2 class="t-title-3">nas redes</h2>
            <ul class="contato__redes-lista">
{redes}
            </ul>
          </div>
        </div>
      </section>
    </main>

    {rodape}
  </body>
</html>
"""

    destino = SITE / "contato.html"
    destino.write_text(pagina, encoding="utf-8")

    print(f"contato.html gerado — {len(CANAIS)} canais, {len(REDES)} redes")
    if email:
        print(f"  e-mail: {email}")
    else:
        print("  ATENÇÃO: sem e-mail. A página avisa isso na tela, de propósito.")
        print("  Preencha email_contato em conteudo/site.json e rode de novo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
