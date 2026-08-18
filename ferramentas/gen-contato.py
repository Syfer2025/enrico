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
    <title>contato e imprensa · enrico pierro</title>
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
                para parceria, evento, palestra ou imprensa, o caminho é o
                <span class="nao-quebra">e-mail</span> abaixo.
              </p>
            </div>

{bloco_do_email(email)}
          </div>

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

    print(f"contato.html gerado — {len(REDES)} redes")
    if email:
        print(f"  e-mail: {email}")
    else:
        print("  ATENÇÃO: sem e-mail. A página avisa isso na tela, de propósito.")
        print("  Preencha email_contato em conteudo/site.json e rode de novo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
