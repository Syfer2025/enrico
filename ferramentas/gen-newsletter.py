#!/usr/bin/env python3
"""gen-newsletter.py — liga a inscrição por e-mail e escreve as páginas dela."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import moldura
from conteudo import ler_json

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"
HOME = SITE / "index.html"

def trocar(texto: str, padrao: str, novo: str, onde: str) -> str:
    """Troca o miolo do primeiro trecho que casar. Falha alto se não achar."""
    achado = re.search(padrao, texto, re.S)
    if not achado:
        raise SystemExit(
            f"erro: não encontrei '{onde}' no index.html.\n"
            f"       A marcação da seção mudou? O padrão era: {padrao}"
        )
    inicio, fim = achado.span(1)
    return texto[:inicio] + novo + texto[fim:]


def configurar_home(endpoint: str) -> str:
    """Escreve o modo e o endereço do serviço na seção do index.html."""
    s = HOME.read_text(encoding="utf-8")
    modo = "formulario" if endpoint else "email"

    s = trocar(s, r'class="newsletter"[^>]*?data-modo="([^"]*)"', modo, "data-modo da seção")
    s = trocar(
        s,
        r'class="newsletter__form"[^>]*?action="([^"]*)"',
        html.escape(f"{endpoint}/inscrever") if endpoint else "",
        "action do formulário",
    )
    s = trocar(
        s,
        r'class="newsletter__form"[^>]*?data-endpoint="([^"]*)"',
        html.escape(endpoint),
        "data-endpoint do formulário",
    )

    HOME.write_text(s, encoding="utf-8")
    return modo


def pagina(
    *,
    arquivo: str,
    titulo_aba: str,
    eyebrow: str,
    titulo: str,
    paragrafos: list[str],
    acoes: list[tuple[str, str, str]] | None = None,
) -> Path:
    """Uma página de uma mensagem só: sobrelinha, título, texto e saída."""
    e = html.escape
    texto = "\n".join(
        f'            <p class="t-body np__paragrafo">{p}</p>' for p in paragrafos
    )
    botoes = ""
    if acoes:
        itens = "\n".join(
            f'              <a class="btn {classe} np__acao" href="{e(href)}">'
            f'<span class="btn__label">{e(rotulo)}</span></a>'
            for rotulo, href, classe in acoes
        )
        botoes = f'\n            <div class="np__acoes">\n{itens}\n            </div>'

    conteudo = f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>{e(titulo_aba)}</title>
    <meta name="robots" content="noindex, nofollow" />
    <meta name="theme-color" content="#08090C" />

    <link rel="stylesheet" href="styles/tokens.css" />
    <link rel="stylesheet" href="styles/base.css" />
    <link rel="stylesheet" href="styles/layout.css" />
    <link rel="stylesheet" href="styles/components.css" />
    <link rel="stylesheet" href="styles/sections/newsletter.css" />

    <script type="module" src="scripts/main.js"></script>
  </head>
  <body>
    <a class="skip-link" href="#conteudo">pular para o conteúdo</a>

    {moldura.cabecalho("newsletter-resposta")}

    <main id="conteudo">
      <section class="np" aria-labelledby="np-titulo">
        <div class="container np__inner">
          <div class="np__texto">
            <p class="t-eyebrow np__eyebrow">{e(eyebrow)}</p>
            <h1 class="t-display-2 np__titulo" id="np-titulo">{e(titulo)}</h1>
{texto}{botoes}
          </div>
        </div>
      </section>
    </main>

    {moldura.rodape()}
  </body>
</html>
"""
    destino = SITE / arquivo
    destino.write_text(conteudo, encoding="utf-8")
    return destino


def main() -> int:
    cfg = ler_json("site.json")
    endpoint = (cfg.get("newsletter_endpoint") or "").strip().rstrip("/")

    modo = configurar_home(endpoint)

    escritas = [HOME]

    escritas.append(
        pagina(
            arquivo="newsletter-confirme.html",
            titulo_aba="falta um clique — enrico pierro",
            eyebrow="newsletter",
            titulo="falta um clique",
            paragrafos=[
                "um e-mail acabou de sair para o endereço que você digitou. "
                "abra e confirme, e é só isso — sem essa confirmação o "
                "endereço não entra na lista.",
                "não chegou em alguns minutos? o primeiro e-mail de um "
                "remetente novo às vezes cai no spam. vale olhar lá antes de "
                "tentar de novo.",
            ],
            acoes=[("ler os textos enquanto isso", "escrita.html", "btn--light")],
        )
    )

    escritas.append(
        pagina(
            arquivo="newsletter-confirmado.html",
            titulo_aba="você está na lista — enrico pierro",
            eyebrow="newsletter",
            titulo="pronto, você está na lista",
            paragrafos=[
                "o próximo texto chega no seu e-mail no dia em que sair.",
                "no fim de qualquer mensagem há um link para sair da lista. "
                "ele funciona de primeira, sem pedir motivo e sem formulário.",
            ],
            acoes=[("ler os textos agora", "escrita.html", "btn--accent")],
        )
    )

    escritas.append(
        pagina(
            arquivo="newsletter-cancelado.html",
            titulo_aba="você saiu da lista — enrico pierro",
            eyebrow="newsletter",
            titulo="você saiu da lista",
            paragrafos=[
                "o endereço foi apagado. não ficou guardado marcado como "
                "cancelado: foi apagado mesmo, e não há mais nada aqui ligado "
                "a ele.",
                "se um dia quiser voltar, é só se inscrever de novo — e os "
                "textos continuam abertos no site, sem inscrição nenhuma.",
            ],
            acoes=[("ler os textos", "escrita.html", "btn--light")],
        )
    )

    escritas.append(
        pagina(
            arquivo="newsletter-nao-deu.html",
            titulo_aba="não deu para inscrever — enrico pierro",
            eyebrow="newsletter",
            titulo="não deu para inscrever agora",
            paragrafos=[
                "pode ser o endereço com um erro de digitação, ou tentativas "
                "demais em pouco tempo — o serviço limita isso para que o "
                "formulário não seja usado para mandar e-mail a quem não pediu.",
                "esperar um minuto e tentar de novo resolve os dois casos. se o "
                "endereço estiver certo e continuar assim, o e-mail da página de "
                "contato chega até ele por outro caminho.",
            ],
            acoes=[
                ("tentar de novo", "index.html#receber", "btn--accent"),
                ("falar por e-mail", "contato.html", "btn--light"),
            ],
        )
    )

    escritas.append(
        pagina(
            arquivo="newsletter-link-invalido.html",
            titulo_aba="esse link não vale mais — enrico pierro",
            eyebrow="newsletter",
            titulo="esse link não vale mais",
            paragrafos=[
                "cada link de confirmação serve uma vez e vale por 48 horas. "
                "se este já foi usado ou passou do prazo, não dá para "
                "aproveitá-lo — é assim de propósito, para que um link antigo "
                "esquecido numa caixa de entrada não valha para sempre.",
                "inscrever-se de novo resolve: um link novo sai na hora.",
            ],
            acoes=[("voltar à inscrição", "index.html#receber", "btn--accent")],
        )
    )

    print(f"newsletter: modo {modo}")
    if modo == "formulario":
        print(f"  serviço: {endpoint}/inscrever")
    else:
        print("  sem serviço no ar — o botão fica sem função de propósito")
        print("  para ligar a inscrição de verdade: publique o Worker (veja")
        print("  newsletter/LEIA-ME.md) e preencha newsletter_endpoint no")
        print("  conteudo/site.json.")
    for p in escritas:
        print(f"  {p.relative_to(PROJETO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
