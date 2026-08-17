#!/usr/bin/env python3
"""gen-secoes.py — escreve os textos da home a partir de conteudo/secoes.json."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from conteudo import ler_json
from marcacao import para_html

PROJETO = Path(__file__).resolve().parent.parent
ALVO = PROJETO / "publicar/index.html"

SEPARADOR = '<span aria-hidden="true">·</span>'


def trocar(texto: str, padrao: str, novo: str, onde: str) -> str:
    """Troca o miolo do primeiro elemento que casar. Falha alto se não achar."""
    achado = re.search(padrao, texto, re.S)
    if not achado:
        raise SystemExit(
            f"erro: não encontrei o campo '{onde}' no index.html.\n"
            f"       A marcação mudou? O padrão era: {padrao}"
        )
    inicio, fim = achado.span(1)
    return texto[:inicio] + novo + texto[fim:]


def logo_abcpod(marca: str) -> str:
    """A marca do podcast como imagem, com o texto do painel virando o alt."""
    return (
        '\n              <img\n'
        '                class="wall-logo__img"\n'
        '                src="assets/img/brand/logo-abcpod-320.webp"\n'
        '                srcset="assets/img/brand/logo-abcpod-160.webp 160w,\n'
        '                        assets/img/brand/logo-abcpod-320.webp 320w,\n'
        '                        assets/img/brand/logo-abcpod-480.webp 480w"\n'
        '                sizes="9rem"\n'
        f'                alt="{html.escape(marca)}"\n'
        '                width="320"\n'
        '                height="320"\n'
        '                loading="lazy"\n'
        '                decoding="async"\n'
        '              />\n            '
    )


def miolo_da_div(texto: str, abertura: str) -> tuple[int, int]:
    """Onde começa e termina o conteúdo de uma <div>, contando o aninhamento."""
    inicio = texto.find(abertura)
    if inicio == -1:
        raise SystemExit(f"erro: não encontrei '{abertura}' no index.html")
    cursor = inicio + len(abertura)
    profundidade = 1
    for marca in re.finditer(r"<div\b|</div>", texto[cursor:]):
        profundidade += 1 if marca.group(0) == "<div" else -1
        if profundidade == 0:
            return cursor, cursor + marca.start()
    raise SystemExit(f"erro: '{abertura}' nunca fecha no index.html")


def montar_reconhecimento(grupos: list[dict]) -> str:
    """As listas de prêmios e antologias — tamanho variável, então é gerada."""
    p = " " * 16
    blocos = []
    for grupo in grupos:
        itens = []
        for item in grupo["itens"]:
            linhas = [
                f"{p}    <li>",
                f'{p}      <p class="t-subhead bio-list__name">',
                f"{p}        {para_html(item['nome'])}",
                f"{p}      </p>",
            ]
            if item.get("detalhe"):
                classe = "t-footnote bio-list__meta"
                if item.get("tabular"):
                    classe += " tabular"
                detalhe = item["detalhe"].replace("·", SEPARADOR)
                linhas.append(f'{p}      <p class="{classe}">{detalhe}</p>')
            linhas.append(f"{p}    </li>")
            itens.append("\n".join(linhas))

        blocos.append(
            "\n".join(
                [
                    f"{p}<div>",
                    f'{p}  <h3 class="t-title-3 bio-list__title">',
                    f"{p}    {html.escape(grupo['titulo'])}",
                    f"{p}  </h3>",
                    f'{p}  <ul class="bio-list">',
                    "\n".join(itens),
                    f"{p}  </ul>",
                    f"{p}</div>",
                ]
            )
        )
    return "\n" + "\n".join(blocos) + "\n" + " " * 14


def main() -> int:
    secoes = ler_json("secoes.json")
    s = ALVO.read_text(encoding="utf-8")

    hero, abcpod, quem = secoes["hero"], secoes["abcpod"], secoes["quem_e"]

    campos = [
        (r'class="t-eyebrow hero__eyebrow">(.*?)</span>', html.escape(hero["sobrelinha"]), "hero.sobrelinha"),
        (r'class="t-display-1 hero__headline"[^>]*>(.*?)</h1>', html.escape(hero["titulo"]), "hero.titulo"),
        (r'<p class="hero__sub">(.*?)</p>', "\n            " + para_html(hero["descricao"], "hero__link") + "\n          ", "hero.descricao"),
        (r'class="wall-logo"[^>]*>(.*?)</h2>', logo_abcpod(abcpod["marca"]), "abcpod.marca"),
        (r'class="wall-logo__sub">(.*?)</p>', html.escape(abcpod["subtitulo"]), "abcpod.subtitulo"),
        (r'class="t-body photo-wall__tagline">(.*?)</p>', "\n            " + html.escape(abcpod["chamada"]) + "\n          ", "abcpod.chamada"),
        (r'class="btn__label">(.*?)</span>', html.escape(abcpod["botao"]), "abcpod.botao"),
        (r'class="t-display-2 bio__name"[^>]*>(.*?)</h2>', html.escape(quem["nome"]), "quem_e.nome"),
        (r'class="bio__standfirst">(.*?)</p>', "\n              " + html.escape(quem["linha_fina"]) + "\n            ", "quem_e.linha_fina"),
        (r'class="bio__portrait-caption">(.*?)</figcaption>', html.escape(quem["legenda_retrato"]), "quem_e.legenda_retrato"),
    ]
    for padrao, novo, onde in campos:
        s = trocar(s, padrao, novo, onde)

    p = " " * 16
    corpo = "\n" + "\n".join(
        f"{p}  <p>\n{p}    {para_html(texto)}\n{p}  </p>"
        for texto in quem["paragrafos"]
    ) + f"\n{p}"
    inicio, fim = miolo_da_div(s, '<div class="t-body bio__prose">')
    s = s[:inicio] + corpo + s[fim:]

    inicio, fim = miolo_da_div(s, '<div class="bio__recognition">')
    s = s[:inicio] + montar_reconhecimento(secoes["reconhecimento"]) + s[fim:]

    ALVO.write_text(s, encoding="utf-8")

    itens = sum(len(g["itens"]) for g in secoes["reconhecimento"])
    print(f"{len(campos)} campos, {len(quem['paragrafos'])} parágrafos "
          f"e {itens} prêmios/antologias -> index.html")
    if abcpod["marca"] == "Logo":
        print("  atenção: a seção do ABCPOD continua com o texto de exemplo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
