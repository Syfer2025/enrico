#!/usr/bin/env python3
"""varrer.py — passa o projeto inteiro em busca de defeitos, de uma vez."""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from conteudo import ler_colecao, ler_json

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"
CONTEUDO = PROJETO / "conteudo"

DERIVADAS = "/assets/img/acervo/capas/"

def prefixo_do_site() -> str:
    from urllib.parse import urlparse
    try:
        return urlparse(ler_json("site.json").get("dominio", "")).path.rstrip("/")
    except Exception:
        return ""


PREFIXO = prefixo_do_site()

ABSOLUTO_ESPERADO = {"404.html"}

CAMPOS_HISTORICOS = {"url_original"}

EXEMPLOS = [
    (re.compile(r"\blorem ipsum\b", re.I), "lorem ipsum"),
    (re.compile(r"\bTODO\b"), "TODO"),
    (re.compile(r"\bFIXME\b"), "FIXME"),
    (re.compile(r"\bplaceholder\b", re.I), "placeholder"),
    (re.compile(r"^Logo$", re.I), 'o texto de exemplo "Logo"'),
]

TAG_CRUA = re.compile(r"</?(a|cite|strong|em|b|i|span|div|p|br|img)\b", re.I)


class Referencias(HTMLParser):
    """Todo endereço que uma página pede ao servidor."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        for chave in ("src", "href"):
            if a.get(chave):
                self.refs.append((chave, a[chave]))
        if a.get("srcset"):
            for parte in a["srcset"].split(","):
                url = parte.strip().split(" ")[0]
                if url:
                    self.refs.append(("srcset", url))


def externo(url: str) -> bool:
    return url.startswith(
        ("http://", "https://", "//", "mailto:", "tel:", "data:", "#", "javascript:")
    )


def paginas_publicadas() -> list[Path]:
    return sorted(p for p in SITE.rglob("*.html") if "/vendor/" not in str(p))


def caminhos_de_json() -> list[tuple[str, str]]:
    """(de onde, caminho de imagem) dentro dos dados gerados."""
    achados = []
    padrao = re.compile(r"(?:assets/|/assets/)[\w./-]+\.(?:webp|jpe?g|png|avif|gif|svg)")
    for arq in sorted((SITE / "assets/data").rglob("*.json")):
        for m in padrao.finditer(arq.read_text(encoding="utf-8")):
            achados.append((str(arq.relative_to(SITE)), m.group(0)))
    return achados


def andar(no, caminho=""):
    """Cada valor de texto de um JSON, com o caminho até ele."""
    if isinstance(no, dict):
        for k, v in no.items():
            yield from andar(v, f"{caminho}.{k}" if caminho else k)
    elif isinstance(no, list):
        for i, v in enumerate(no):
            yield from andar(v, f"{caminho}[{i}]")
    elif isinstance(no, str):
        yield caminho, no


def conferir_referencias() -> tuple[list[str], list[str]]:
    quebradas, absolutas = [], []
    vistos: set[str] = set()

    for pagina in paginas_publicadas():
        p = Referencias()
        p.feed(pagina.read_text(encoding="utf-8"))
        rel = pagina.relative_to(SITE)
        for atributo, url in p.refs:
            if externo(url):
                continue
            limpo = url.split("?")[0].split("#")[0]
            if not limpo:
                continue

            if limpo.startswith("/"):
                if not str(rel).startswith("admin/") and str(rel) not in ABSOLUTO_ESPERADO:
                    absolutas.append(f"{rel}: {atributo}=\"{url}\"")
                sem_prefixo = limpo
                if PREFIXO and limpo.startswith(PREFIXO + "/"):
                    sem_prefixo = limpo[len(PREFIXO):]
                elif PREFIXO and limpo == PREFIXO:
                    sem_prefixo = "/"
                alvo = SITE / sem_prefixo.lstrip("/")
                if sem_prefixo.endswith("/"):
                    alvo = alvo / "index.html"
            else:
                alvo = (pagina.parent / limpo).resolve()

            chave = f"{rel}|{limpo}"
            if chave in vistos:
                continue
            vistos.add(chave)
            if not alvo.exists():
                quebradas.append(f"{rel}: {atributo}=\"{url}\" não existe")

    for onde, caminho in caminhos_de_json():
        alvo = SITE / caminho.lstrip("/")
        if not alvo.exists():
            quebradas.append(f"{onde}: {caminho} não existe")

    return quebradas, absolutas


def conferir_conteudo() -> dict[str, list[str]]:
    r: dict[str, list[str]] = {
        "derivadas": [], "faltando": [], "vazios": [], "exemplos": [], "tags": [],
    }

    obrigatorios = {
        "textos": ("titulo", "data", "categoria"),
        "livros": ("titulo", "url", "ordem"),
        "episodios": ("convidado", "youtube_id", "publicado_em"),
    }

    for colecao, campos in obrigatorios.items():
        for item in ler_colecao(colecao):
            onde = f"conteudo/{colecao}/{item['slug']}.md"
            for campo in campos:
                if item.get(campo) in (None, "", []):
                    r["vazios"].append(f"{onde}: `{campo}` vazio")

            capa = (item.get("capa") or "").strip()
            if capa:
                if DERIVADAS in capa:
                    r["derivadas"].append(f"{onde}: capa aponta para {capa}")
                elif not (SITE / capa.lstrip("/")).exists():
                    r["faltando"].append(f"{onde}: capa {capa} não existe")

            for campo, valor in item.items():
                if campo in ("body", "slug") or not isinstance(valor, str):
                    continue
                for regex, nome in EXEMPLOS:
                    if regex.search(valor):
                        r["exemplos"].append(f"{onde}: `{campo}` tem {nome}")

    secoes = ler_json("secoes.json")
    for caminho, valor in andar(secoes):
        onde = f"conteudo/secoes.json → {caminho}"
        if TAG_CRUA.search(valor):
            tags = sorted(set(t.lower() for t in TAG_CRUA.findall(valor)))
            r["tags"].append(f"{onde}: tag {', '.join(tags)} dentro do texto")
        for regex, nome in EXEMPLOS:
            if regex.search(valor):
                r["exemplos"].append(f"{onde}: tem {nome}")

    return r


def conferir_site_antigo() -> list[str]:
    marcas = ("wp-content", "wp-includes", "i0.wp.com", "i1.wp.com", "i2.wp.com",
              "enricopierro.com.br/wp", "photon")
    achados = []

    for pagina in paginas_publicadas():
        texto = pagina.read_text(encoding="utf-8")
        for marca in marcas:
            if marca in texto:
                achados.append(f"{pagina.relative_to(SITE)}: cita {marca}")

    for item in ler_colecao("textos"):
        for campo, valor in item.items():
            if campo in CAMPOS_HISTORICOS or not isinstance(valor, str):
                continue
            for marca in marcas:
                if marca in valor:
                    achados.append(f"conteudo/textos/{item['slug']}.md: `{campo}` cita {marca}")
    return achados


def bloco(titulo: str, itens: list[str], grau: str, limite: int = 8) -> int:
    print(f"── {titulo}")
    if not itens:
        print("     nada\n")
        return 0
    for i in itens[:limite]:
        print(f"     {grau}  {i}")
    if len(itens) > limite:
        print(f"     … e mais {len(itens) - limite}")
    print()
    return len(itens)


def main() -> int:
    print("varredura geral do projeto\n")

    quebradas, absolutas = conferir_referencias()
    c = conferir_conteudo()
    antigo = conferir_site_antigo()

    erros = 0
    erros += bloco("1. arquivo apontado que não existe", quebradas, "ERRO")
    erros += bloco("2. capa apontando para arquivo derivado", c["derivadas"], "ERRO")
    erros += bloco("3. HTML cru em campo que o painel edita", c["tags"], "ERRO")
    erros += bloco("4. campo obrigatório vazio", c["vazios"], "ERRO")
    erros += bloco("5. capa que não existe no disco", c["faltando"], "ERRO")
    erros += bloco("6. caminho absoluto em página do site", absolutas, "ERRO")
    avisos = 0
    avisos += bloco("7. texto de exemplo esquecido", c["exemplos"], "aviso")
    erros += bloco("8. dependência do site antigo", antigo, "ERRO")

    print(f"total: {erros} erro(s), {avisos} aviso(s)")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
