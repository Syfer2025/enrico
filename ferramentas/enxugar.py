#!/usr/bin/env python3
"""enxugar.py — tira os comentários do que vai ser servido."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"

IGNORAR = ("admin/vendor/",)

MARCADOR = re.compile(r"[A-Z]{3,}:(INICIO|FIM)")


def sem_comentario_css(fonte: str) -> str:
    """Tira /* */ de CSS, respeitando texto entre aspas."""
    saida = []
    i, n = 0, len(fonte)
    aspas = ""
    while i < n:
        c = fonte[i]
        if aspas:
            saida.append(c)
            if c == "\\" and i + 1 < n:
                saida.append(fonte[i + 1])
                i += 2
                continue
            if c == aspas:
                aspas = ""
            i += 1
            continue
        if c in "\"'":
            aspas = c
            saida.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and fonte[i + 1] == "*":
            fim = fonte.find("*/", i + 2)
            fim = n if fim == -1 else fim + 2
            i = fim
            continue
        saida.append(c)
        i += 1
    return "".join(saida)


def sem_comentario_js(fonte: str) -> str:
    """Tira // e /* */ de JavaScript."""
    saida = []
    i, n = 0, len(fonte)
    anterior = ""
    while i < n:
        c = fonte[i]
        prox = fonte[i + 1] if i + 1 < n else ""

        if c == "/" and prox == "/":
            fim = fonte.find("\n", i)
            i = n if fim == -1 else fim
            continue

        if c == "/" and prox == "*":
            fim = fonte.find("*/", i + 2)
            i = n if fim == -1 else fim + 2
            continue

        if c in "\"'":
            fim = i + 1
            while fim < n:
                if fonte[fim] == "\\":
                    fim += 2
                    continue
                if fonte[fim] == c:
                    break
                fim += 1
            saida.append(fonte[i : fim + 1])
            anterior = c
            i = fim + 1
            continue

        if c == "`":
            fim = i + 1
            profundidade = 0
            while fim < n:
                if fonte[fim] == "\\":
                    fim += 2
                    continue
                if fonte[fim] == "$" and fim + 1 < n and fonte[fim + 1] == "{":
                    profundidade += 1
                    fim += 2
                    continue
                if profundidade and fonte[fim] == "}":
                    profundidade -= 1
                    fim += 1
                    continue
                if not profundidade and fonte[fim] == "`":
                    break
                fim += 1
            saida.append(fonte[i : fim + 1])
            anterior = "`"
            i = fim + 1
            continue

        if c == "/" and anterior not in ("", ")", "]") and not anterior.isalnum() \
                and anterior not in ("_", "$"):
            fim = i + 1
            classe = False
            while fim < n:
                if fonte[fim] == "\\":
                    fim += 2
                    continue
                if fonte[fim] == "[":
                    classe = True
                elif fonte[fim] == "]":
                    classe = False
                elif fonte[fim] == "/" and not classe:
                    break
                elif fonte[fim] == "\n":
                    break
                fim += 1
            saida.append(fonte[i : fim + 1])
            anterior = "/"
            i = fim + 1
            continue

        saida.append(c)
        if not c.isspace():
            anterior = c
        i += 1
    return "".join(saida)


def sem_comentario_html(fonte: str, marcadores: bool = True) -> str:
    """Tira <!-- --> de HTML. Com `marcadores`, os alvos de gerador ficam."""

    def troca(achado: re.Match[str]) -> str:
        if marcadores and MARCADOR.search(achado.group(0)):
            return achado.group(0)
        return ""

    return re.sub(r"<!--.*?-->", troca, fonte, flags=re.S)


def arrumar_vazio(fonte: str) -> str:
    """Junta as linhas em branco que sobraram onde havia comentário."""
    fonte = re.sub(r"[ \t]+\n", "\n", fonte)
    fonte = re.sub(r"\n{3,}", "\n\n", fonte)
    return fonte.strip() + "\n"


TRATADORES = {
    ".css": sem_comentario_css,
    ".js": sem_comentario_js,
    ".html": sem_comentario_html,
}


def main() -> int:
    conferir = "--conferir" in sys.argv
    tudo = "--tudo" in sys.argv
    antes = depois = 0
    mexidos = 0

    for arquivo in sorted(SITE.rglob("*")):
        if not arquivo.is_file() or arquivo.suffix not in TRATADORES:
            continue
        relativo = str(arquivo.relative_to(SITE))
        if any(p in relativo for p in IGNORAR):
            continue

        original = arquivo.read_text(encoding="utf-8")
        if arquivo.suffix == ".html":
            limpo = sem_comentario_html(original, marcadores=not tudo)
        else:
            limpo = TRATADORES[arquivo.suffix](original)
        novo = arrumar_vazio(limpo)
        antes += len(original)
        depois += len(novo)
        if novo != original:
            mexidos += 1
            if not conferir:
                arquivo.write_text(novo, encoding="utf-8")

    economia = antes - depois
    verbo = "sairiam" if conferir else "saíram"
    print(f"enxugar: {mexidos} arquivo(s), {economia:,} bytes {verbo}".replace(",", "."))
    if antes:
        print(f"  {antes:,} -> {depois:,} bytes ({economia * 100 // antes}% menor)".replace(",", "."))
    if conferir:
        print("  (--conferir: nada foi escrito)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
