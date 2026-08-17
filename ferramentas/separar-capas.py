#!/usr/bin/env python3
"""separar-capas.py — faz da capa um campo de verdade, e não "a primeira foto do texto"."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from conteudo import escrever, ler_colecao

PROJETO = Path(__file__).resolve().parent.parent

QUALQUER_IMAGEM = re.compile(r'!\[[^\]]*\]\(([^)\s]+)\)|<img[^>]+src="([^"]+)"')

IMAGEM_SOLTA = re.compile(
    r"""^[ \t]*
        (?: !\[[^\]]*\]\((?P<md>[^)\s]+)\)
          | <img[^>]+src="(?P<html>[^"]+)"[^>]*> )
        [ \t]*$""",
    re.M | re.X,
)

DERIVADA = "/assets/img/acervo/capas/"


def caminho_de(m: re.Match[str] | None) -> str:
    if not m:
        return ""
    return m.group(1) or m.group(2) or ""


def primeira_foto(corpo: str) -> str:
    return caminho_de(QUALQUER_IMAGEM.search(corpo))


def sem_a_capa(corpo: str, capa: str) -> str | None:
    """O corpo sem a primeira imagem, se ela for a capa. Senão, None."""
    m = QUALQUER_IMAGEM.search(corpo)
    if not m or caminho_de(m) != capa:
        return None

    novo = corpo[: m.start()] + corpo[m.end():]

    inicio = novo.rfind("\n", 0, m.start()) + 1
    fim = novo.find("\n", inicio)
    fim = len(novo) if fim == -1 else fim
    linha = novo[inicio:fim]
    if linha.strip():
        arrumada = re.sub(r"[ \t]{2,}", " ", linha).strip()
        novo = novo[:inicio] + arrumada + novo[fim:]

    return novo.lstrip("\n")


def main() -> int:
    valendo = "--valendo" in sys.argv
    textos = ler_colecao("textos")

    mudancas: list[tuple[dict, str, str]] = []
    corrigidas = preenchidas = tiradas = 0
    intocados = 0

    for texto in textos:
        capa = (texto.get("capa") or "").strip()
        corpo = texto.get("body") or ""
        capa_nova, corpo_novo = capa, corpo

        if DERIVADA in capa_nova:
            original = primeira_foto(corpo)
            if original:
                capa_nova = original
                corrigidas += 1
        elif not capa_nova:
            original = primeira_foto(corpo)
            if original:
                capa_nova = original
                preenchidas += 1

        if capa_nova:
            limpo = sem_a_capa(corpo_novo, capa_nova)
            if limpo is not None:
                corpo_novo = limpo
                tiradas += 1

        if capa_nova != capa or corpo_novo != corpo:
            mudancas.append((texto, capa_nova, corpo_novo))
        else:
            intocados += 1

    print(f"{len(textos)} textos lidos\n")
    print(f"  {corrigidas:>4}  capa apontava para a miniatura de 320px → aponta para o original")
    print(f"  {preenchidas:>4}  sem campo capa → capa preenchida com a primeira foto")
    print(f"  {tiradas:>4}  a foto da capa saiu do corpo")
    print(f"  {intocados:>4}  nada a mudar")
    print(f"\n  {len(mudancas)} arquivos a reescrever")

    if mudancas:
        print("\n  exemplos:")
        for texto, capa_nova, _ in mudancas[:3]:
            print(f"    {texto['slug']}")
            if (texto.get('capa') or '') != capa_nova:
                print(f"      capa antes:  {texto.get('capa') or '(vazia)'}")
                print(f"      capa depois: {capa_nova}")

    if not valendo:
        print("\nEnsaio. Para gravar: python3 ferramentas/separar-capas.py --valendo")
        return 0

    pasta = PROJETO / "conteudo/textos"
    for texto, capa_nova, corpo_novo in mudancas:
        campos = {k: v for k, v in texto.items() if k not in ("body", "slug")}
        campos["capa"] = capa_nova
        escrever(pasta / f"{texto['slug']}.md", campos, corpo_novo)

    print(f"\n{len(mudancas)} textos reescritos.")
    print("Agora rode os geradores: a capa volta ao alto da leitura pelo campo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
