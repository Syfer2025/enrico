#!/usr/bin/env python3
"""gen-autorizar.py — a página onde a autorização do Instagram aterrissa."""

from __future__ import annotations

import sys
from pathlib import Path

import moldura

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"


PAGINA = """<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>autorização do instagram · enrico pierro</title>
    <meta name="robots" content="noindex, nofollow" />
    <meta name="theme-color" content="#08090C" />

    <link rel="stylesheet" href="styles/tokens.css" />
    <link rel="stylesheet" href="styles/base.css" />
    <link rel="stylesheet" href="styles/layout.css" />
    <link rel="stylesheet" href="styles/components.css" />
    <link rel="stylesheet" href="styles/sections/newsletter.css" />
    <link rel="stylesheet" href="styles/sections/autorizar.css" />

    <script type="module" src="scripts/main.js"></script>
  </head>
  <body>
    <a class="skip-link" href="#conteudo">pular para o conteúdo</a>

    {cabecalho}

    <main id="conteudo">
      <section class="np" data-module="autorizar" aria-labelledby="np-titulo">
        <div class="container np__inner">

          <!-- UM h1 só, e o script troca o texto conforme o estado. Três
               títulos (um por painel) davam três h1 na mesma página, mesmo com
               dois escondidos: o auditor acusou, e com razão — leitor de tela
               percorre a estrutura, não o que está visível. -->
          <div class="np__texto">
            <p class="t-eyebrow np__eyebrow">instagram</p>
            <h1 class="t-display-2 np__titulo" id="np-titulo"
                data-autorizar="titulo">autorização do instagram</h1>
          </div>

          <div class="np__texto" data-autorizar="ok" hidden>
            <p class="t-body np__paragrafo">
              agora falta só um passo: mandar o código abaixo para quem cuida do
              site. depois disso você não precisa fazer mais nada.
            </p>

            <p class="aut-codigo" data-autorizar="codigo"></p>

            <div class="np__acoes">
              <button class="btn btn--accent" type="button" data-autorizar="copiar">
                <span class="btn__label">copiar o código</span>
              </button>
              <a class="btn btn--light" data-autorizar="whatsapp" href="https://wa.me/">
                <span class="btn__label">mandar no whatsapp</span>
              </a>
            </div>

            <p class="t-caption-1 aut-nota">
              o código vale uma hora e serve uma vez só. se passar do tempo, abra
              o mesmo link de novo que ele gera outro.
            </p>
          </div>

          <div class="np__texto" data-autorizar="sem" hidden>
            <p class="t-body np__paragrafo">
              ela só faz sentido depois de você abrir o link de autorização que
              recebeu. sozinha, não há nada aqui.
            </p>
            <div class="np__acoes">
              <a class="btn btn--light np__acao" href="index.html">
                <span class="btn__label">ir para o site</span>
              </a>
            </div>
          </div>

          <div class="np__texto" data-autorizar="erro" hidden>
            <p class="t-body np__paragrafo">
              pode ter sido um toque em "cancelar", ou a conta usada não ser a
              certa. abrir o link de novo resolve.
            </p>
            <p class="t-caption-1 aut-nota" data-autorizar="motivo"></p>
            <div class="np__acoes">
              <a class="btn btn--light np__acao" href="index.html">
                <span class="btn__label">ir para o site</span>
              </a>
            </div>
          </div>

        </div>
      </section>
    </main>

    {rodape}
  </body>
</html>
"""


def main() -> int:
    conteudo = PAGINA.format(
        cabecalho=moldura.cabecalho("autorizar.html"),
        rodape=moldura.rodape(),
    )
    destino = SITE / "autorizar.html"
    destino.write_text(conteudo, encoding="utf-8")
    print(f"autorizar.html gerado — {destino.stat().st_size:,} bytes".replace(",", "."))
    print("  lembre-se: a URI de redirecionamento no painel da Meta precisa ser")
    print("  https://syfer2025.github.io/enrico/autorizar.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
