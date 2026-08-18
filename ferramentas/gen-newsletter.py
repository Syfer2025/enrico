#!/usr/bin/env python3
"""gen-newsletter.py — liga a inscrição por e-mail e escreve as páginas dela."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from urllib.parse import quote

import moldura
from conteudo import ler_json

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"
HOME = SITE / "index.html"

CAIXA_INICIO = "<!-- CAIXA:INICIO"
CAIXA_FIM = "<!-- CAIXA:FIM -->"


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


def link_de_email(endereco: str) -> str:
    """O `mailto:` do modo sem serviço, com assunto e corpo já escritos."""
    assunto = quote("quero receber os textos")
    corpo = quote(
        "oi, enrico.\n\n"
        "quero entrar na lista para receber seus textos por e-mail.\n\n"
        "meu endereço é este mesmo de onde estou escrevendo.\n"
    )
    return f"mailto:{endereco}?subject={assunto}&body={corpo}"


def configurar_home(endpoint: str, mailto: str) -> str:
    """Escreve o modo e os endereços na seção do index.html. Devolve o modo."""
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
    s = trocar(
        s,
        r'newsletter__direto-botao"\s+href="([^"]*)"',
        html.escape(mailto, quote=True),
        "href do botão de e-mail",
    )

    HOME.write_text(s, encoding="utf-8")
    return modo


def caixa_da_home() -> str:
    """A caixa do formulário, copiada da home já configurada."""
    s = HOME.read_text(encoding="utf-8")
    try:
        i = s.rindex("\n", 0, s.index(CAIXA_INICIO)) + 1
        f = s.index(CAIXA_FIM) + len(CAIXA_FIM)
    except ValueError:
        raise SystemExit(
            "erro: os marcadores CAIXA:INICIO/CAIXA:FIM não estão no index.html.\n"
            "       Sem eles a página newsletter.html não tem de onde copiar o "
            "formulário."
        ) from None
    return s[i:f]


def pagina(
    *,
    arquivo: str,
    titulo_aba: str,
    eyebrow: str,
    titulo: str,
    paragrafos: list[str],
    corpo_extra: str = "",
    acoes: list[tuple[str, str, str]] | None = None,
    modo: str = "email",
    fora_do_indice: bool = True,
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

    robots = (
        '\n    <meta name="robots" content="noindex, nofollow" />'
        if fora_do_indice
        else ""
    )

    conteudo = f"""<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
    <title>{e(titulo_aba)}</title>{robots}
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

    {moldura.cabecalho("newsletter.html")}

    <main id="conteudo">
      <section
        class="np"
        data-module="newsletter"
        data-modo="{modo}"
        aria-labelledby="np-titulo"
      >
        <div class="container np__inner">
          <div class="np__texto">
            <p class="t-eyebrow np__eyebrow">{e(eyebrow)}</p>
            <h1 class="t-display-2 np__titulo" id="np-titulo">{e(titulo)}</h1>
{texto}{botoes}
          </div>
{corpo_extra}
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
    contato = (cfg.get("email_contato") or "").strip()

    if not endpoint and not contato:
        raise SystemExit(
            "erro: sem newsletter_endpoint E sem email_contato no site.json.\n"
            "       Nesse estado a seção não teria como receber inscrição\n"
            "       nenhuma — nem pelo serviço, nem por e-mail. Preencha um dos\n"
            "       dois em conteudo/site.json e rode de novo."
        )

    mailto = link_de_email(contato) if contato else ""
    modo = configurar_home(endpoint, mailto)
    caixa = caixa_da_home()

    escritas = [HOME]

    escritas.append(
        pagina(
            arquivo="newsletter.html",
            titulo_aba="receber os textos por e-mail — enrico pierro",
            eyebrow="newsletter",
            titulo="os textos, por e-mail",
            paragrafos=[
                "o diário, a coluna e os textos novos chegam no seu "
                '<span class="nao-quebra">e-mail</span> no dia em que saem. '
                "não há resumo semanal, indicação de terceiro nem propaganda: "
                "o que sai daqui é texto dele.",
                "a inscrição tem duas etapas. depois de digitar o endereço, "
                "chega um e-mail pedindo confirmação — é o clique nele que põe "
                "você na lista. serve para que ninguém inscreva outra pessoa "
                "sem que ela saiba.",
            ],
            corpo_extra=caixa,
            modo=modo,
            fora_do_indice=False,
        )
    )

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
                ("tentar de novo", "newsletter.html", "btn--accent"),
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
            acoes=[("voltar à inscrição", "newsletter.html", "btn--accent")],
        )
    )

    print(f"newsletter: modo {modo}")
    if modo == "formulario":
        print(f"  serviço: {endpoint}/inscrever")
    else:
        print(f"  sem serviço no ar — o convite abre um e-mail para {contato}")
        print("  para ligar a inscrição de verdade: publique o Worker (veja")
        print("  newsletter/LEIA-ME.md) e preencha newsletter_endpoint no")
        print("  conteudo/site.json.")
    for p in escritas:
        print(f"  {p.relative_to(PROJETO)}")
    print("\n  lembre-se de rodar gen-publicacao.py depois — é ele que põe a")
    print("  prévia de link e o canonical na newsletter.html.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
