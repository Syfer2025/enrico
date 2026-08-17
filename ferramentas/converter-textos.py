#!/usr/bin/env python3
"""converter-textos.py — troca o HTML dos 577 textos por texto normal (Markdown)."""

from __future__ import annotations

import html as libhtml
import re
import sys
from pathlib import Path

from conteudo import CONTEUDO, escrever, ler_colecao

PROJETO = Path(__file__).resolve().parent.parent

ORDEM = ["titulo", "data", "categoria", "publicado", "capa", "url_original"]


def inline(s: str) -> str:
    """Converte a formatação de dentro de um parágrafo."""
    s = re.sub(r"<a[^>]*>\s*</a>", "", s, flags=re.S | re.I)
    def _link(m: re.Match[str]) -> str:
        rotulo = re.sub(r"\s*\n\s*", " ", m.group(2)).strip()
        return f"[{rotulo}]({m.group(1)})"

    s = re.sub(r"<a[^>]*href=\"([^\"]*)\"[^>]*>(.*?)</a>", _link, s, flags=re.S | re.I)
    s = re.sub(r"<(?:strong|b)\b[^>]*>(.*?)</(?:strong|b)>", r"**\1**", s, flags=re.S | re.I)
    s = re.sub(r"<(?:em|i)\b[^>]*>(.*?)</(?:em|i)>", r"*\1*", s, flags=re.S | re.I)
    s = re.sub(r"<img[^>]*src=\"([^\"]*)\"[^>]*>", r"![](\1)", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</?(?:span|div|figure|figcaption)[^>]*>", "", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = libhtml.unescape(s)
    s = re.sub(r"\*\*[ \t\xa0]*\*\*|__[ \t\xa0]*__|(?<!\*)\*[ \t\xa0]*\*(?!\*)", "", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def para_markdown(corpo: str) -> str:
    """O HTML de um texto → Markdown."""
    s = corpo
    s = re.sub(r"<figure[^>]*>\s*(<img[^>]*>)\s*(?:<figcaption[^>]*>(.*?)</figcaption>)?\s*</figure>",
               lambda m: "\n\n" + inline(m.group(1)) + ("\n\n_" + inline(m.group(2)) + "_" if m.group(2) else "") + "\n\n",
               s, flags=re.S | re.I)

    blocos: list[str] = []

    def bloco(texto: str, prefixo: str = "") -> None:
        t = inline(texto)
        if t:
            blocos.append("\n".join(prefixo + linha if linha.strip() else linha
                                    for linha in t.split("\n")))

    padrao = re.compile(
        r"<(p|h[1-6]|blockquote|pre|ul|ol)\b[^>]*>(.*?)</\1>|(<img[^>]*>)",
        re.S | re.I,
    )
    pos = 0
    for m in padrao.finditer(s):
        solto = inline(s[pos:m.start()])
        if solto:
            blocos.append(solto)
        pos = m.end()

        if m.group(3):
            blocos.append(inline(m.group(3)))
            continue

        tag, dentro = m.group(1).lower(), m.group(2)
        if tag == "p":
            bloco(dentro)
        elif tag.startswith("h"):
            nivel = "#" * min(int(tag[1]), 6)
            t = inline(dentro)
            if t:
                blocos.append(f"{nivel} {t}")
        elif tag == "blockquote":
            bloco(re.sub(r"</?p[^>]*>", "\n", dentro, flags=re.I), "> ")
        elif tag == "pre":
            t = libhtml.unescape(re.sub(r"<[^>]+>", "", dentro)).strip()
            if t:
                blocos.append("```\n" + t + "\n```")
        elif tag in ("ul", "ol"):
            itens = re.findall(r"<li\b[^>]*>(.*?)</li>", dentro, re.S | re.I)
            linhas = []
            for i, item in enumerate(itens, 1):
                t = inline(item)
                if t:
                    linhas.append((f"{i}. " if tag == "ol" else "- ") + t)
            if linhas:
                blocos.append("\n".join(linhas))

    resto = inline(s[pos:])
    if resto:
        blocos.append(resto)

    return re.sub(r"\n{3,}", "\n\n", "\n\n".join(blocos)).strip()


BLOCO = re.compile(r"</?(?:p|div|br|h[1-6]|li|ul|ol|blockquote|pre|figure|figcaption)\b[^>]*>", re.I)
INLINE_TAG = re.compile(r"<[^>]+>")


def palavras(s: str) -> list[str]:
    """As palavras de verdade, sem tag, sem pontuação, sem caixa."""
    s = BLOCO.sub(" ", s)
    s = INLINE_TAG.sub("", s)
    s = libhtml.unescape(s)
    return re.findall(r"[^\W_]+", s.lower(), re.UNICODE)


def imagens_html(s: str) -> list[str]:
    return sorted(set(re.findall(r"<img[^>]*src=\"([^\"]+)\"", s, re.I)))


def imagens_md(s: str) -> list[str]:
    """Só imagem de verdade: ![](x). Um link comum, [texto](x), não conta."""
    return sorted(set(re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", s)))


def main() -> int:
    ensaio = "--ensaio" in sys.argv
    pasta = CONTEUDO / "textos"

    convertidos = 0
    ja_texto = 0
    recusados: list[str] = []

    for texto in ler_colecao("textos"):
        corpo = texto.get("body") or ""
        if "<" not in corpo:
            ja_texto += 1
            continue

        md = para_markdown(corpo)

        antes, depois = palavras(corpo), palavras(md)
        perdidas = [p for p in antes if p not in depois]
        img_antes, img_depois = imagens_html(corpo), imagens_md(md)

        if perdidas or img_antes != img_depois:
            motivo = []
            if perdidas:
                motivo.append(f"{len(perdidas)} palavra(s): {perdidas[:4]}")
            if img_antes != img_depois:
                motivo.append(f"imagens {len(img_antes)}→{len(img_depois)}")
            recusados.append(f"{texto['slug']} — {'; '.join(motivo)}")
            continue

        if not ensaio:
            campos = {c: texto.get(c) for c in ORDEM}
            escrever(pasta / f"{texto['slug']}.md", campos, md)
        convertidos += 1

    print(("ENSAIO — nada gravado\n" if ensaio else "") + f"{convertidos} textos convertidos para texto normal")
    if ja_texto:
        print(f"{ja_texto} já estavam sem HTML")
    if recusados:
        print(f"\n{len(recusados)} NÃO convertidos, para não perder conteúdo:")
        for r in recusados[:15]:
            print(f"  {r}")
        if len(recusados) > 15:
            print(f"  … e mais {len(recusados) - 15}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
