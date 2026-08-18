#!/usr/bin/env python3
"""auditar.py — varre as páginas atrás de defeitos que passam despercebidos."""

from __future__ import annotations

import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"
PAGINAS = [
    "index.html",
    "escrita.html",
    "episodios.html",
    "contato.html",
    "newsletter-confirme.html",
    "newsletter-confirmado.html",
    "newsletter-cancelado.html",
    "newsletter-nao-deu.html",
    "newsletter-link-invalido.html",
    "404.html",
]

FORA_DO_INDICE_OK = {
    "404.html",
    "newsletter-confirme.html",
    "newsletter-confirmado.html",
    "newsletter-cancelado.html",
    "newsletter-nao-deu.html",
    "newsletter-link-invalido.html",
}

INTERATIVOS = {"a", "button"}


class Analise(HTMLParser):
    """Um passe pela página, juntando o que precisa ser conferido."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.imagens: list[dict] = []
        self.titulos: list[int] = []
        self.links_abrindo_fora: list[str] = []
        self.html_lang: str | None = None
        self.pilha: list[dict] = []
        self.interativos: list[dict] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)

        if "id" in a:
            self.ids.append(a["id"])
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag == "img":
            self.imagens.append(a)
        if tag and re.fullmatch(r"h[1-6]", tag):
            self.titulos.append(int(tag[1]))
        if tag == "a" and a.get("target") == "_blank":
            if "noopener" not in (a.get("rel") or ""):
                self.links_abrindo_fora.append(a.get("href", "?"))

        if tag in INTERATIVOS:
            self.pilha.append({"tag": tag, "attrs": a, "texto": "", "escondido": False})
        elif self.pilha and a.get("class", "").find("visually-hidden") >= 0:
            self.pilha[-1]["escondido"] = True

    def handle_endtag(self, tag):
        if tag in INTERATIVOS and self.pilha:
            for i in range(len(self.pilha) - 1, -1, -1):
                if self.pilha[i]["tag"] == tag:
                    self.interativos.append(self.pilha.pop(i))
                    break

    def handle_data(self, data):
        if self.pilha:
            self.pilha[-1]["texto"] += data


def achados_de(s: str, pagina: str = "") -> list[tuple[str, str]]:
    p = Analise()
    p.feed(s)
    r: list[tuple[str, str]] = []

    for ident, n in Counter(p.ids).items():
        if n > 1:
            r.append(("ERRO", f'id repetido {n}×: "{ident}"'))

    sem_alt = [i for i in p.imagens if "alt" not in i]
    if sem_alt:
        r.append(("ERRO", f"{len(sem_alt)} <img> sem atributo alt "
                          f"(ex.: {sem_alt[0].get('src','?')[:60]})"))
    sem_medida = [i for i in p.imagens if not ("width" in i and "height" in i)]
    if sem_medida:
        r.append(("AVISO", f"{len(sem_medida)} <img> sem width/height — o texto "
                           f"pula quando a imagem chega "
                           f"(ex.: {sem_medida[0].get('src','?')[:60]})"))

    for href in p.links_abrindo_fora:
        r.append(("ERRO", f"abre em outra aba sem rel=noopener: {href[:60]}"))

    for e in p.interativos:
        a = e["attrs"]
        if a.get("aria-hidden") == "true":
            continue
        tem_nome = (
            e["texto"].strip()
            or a.get("aria-label")
            or a.get("aria-labelledby")
            or a.get("title")
            or e["escondido"]
        )
        if not tem_nome:
            onde = a.get("href") or a.get("class") or "(sem pistas)"
            r.append(("ERRO", f"<{e['tag']}> sem nome acessível: {onde[:60]}"))

    if p.titulos.count(1) == 0:
        r.append(("ERRO", "página sem <h1>"))
    elif p.titulos.count(1) > 1:
        r.append(("AVISO", f"{p.titulos.count(1)} elementos <h1> — o normal é um"))
    anterior = 0
    for n in p.titulos:
        if anterior and n > anterior + 1:
            r.append(("AVISO", f"salto de título h{anterior} → h{n}"))
            break
        anterior = n

    if not p.html_lang:
        r.append(("ERRO", "<html> sem lang — leitor de tela lê com a pronúncia errada"))
    fora_do_indice = "noindex" in s

    if fora_do_indice and pagina not in FORA_DO_INDICE_OK:
        r.append(("AVISO", "noindex — a página é invisível para o Google "
                           "(esperado enquanto site.json tiver no_ar: false)"))
    if not fora_do_indice:
        if 'rel="canonical"' not in s:
            r.append(("AVISO", "sem canonical"))
        if 'property="og:' not in s:
            r.append(("AVISO", "sem Open Graph — link compartilhado não mostra prévia"))

    return r


def main() -> int:
    total = Counter()
    print("varredura das páginas publicadas\n")

    for pagina in PAGINAS:
        caminho = SITE / pagina
        if not caminho.exists():
            continue
        achados = achados_de(caminho.read_text(encoding="utf-8"), pagina)
        erros = [m for g, m in achados if g == "ERRO"]
        avisos = sorted(set(m for g, m in achados if g == "AVISO"))
        total["ERRO"] += len(erros)
        total["AVISO"] += len(avisos)

        print(f"── {pagina}  ({len(erros)} erro, {len(avisos)} aviso)")
        for m in erros[:12]:
            print(f"     ERRO   {m}")
        if len(erros) > 12:
            print(f"     … e mais {len(erros) - 12} erro(s)")
        for m in avisos:
            print(f"     aviso  {m}")
        print()

    print(f"total: {total['ERRO']} erro(s), {total['AVISO']} aviso(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
