#!/usr/bin/env python3
"""ATENÇÃO — NÃO RODE DE NOVO SEM AJUSTAR."""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
ORIGEM = PROJETO / "publicar/index.html"
DESTINO = PROJETO / "conteudo/secoes.json"

SEPARADOR = '<span aria-hidden="true">·</span>'


def interno(fragmento: str) -> str:
    """Normaliza espaços mantendo as tags de dentro (<cite>, <a>, <span>)."""
    return re.sub(r"\s+", " ", fragmento).strip()


def puro(fragmento: str) -> str:
    """Texto sem nenhuma tag — para campos que comprovadamente não têm."""
    return interno(html.unescape(re.sub(r"(?s)<[^>]+>", " ", fragmento)))


def achar(padrao: str, fonte: str, limpo: bool = False) -> str | None:
    m = re.search(padrao, fonte, re.S)
    if not m:
        return None
    return puro(m.group(1)) if limpo else interno(m.group(1))


def main() -> int:
    if not ORIGEM.exists():
        print(f"erro: {ORIGEM} não existe")
        return 1

    s = ORIGEM.read_text(encoding="utf-8")
    secoes: dict[str, object] = {}

    secoes["hero"] = {
        "sobrelinha": achar(r'class="[^"]*hero__eyebrow"[^>]*>(.*?)</span>', s, limpo=True),
        "titulo": achar(r'class="[^"]*hero__headline"[^>]*>(.*?)</h1>', s, limpo=True),
        "descricao_html": achar(r'<p class="hero__sub">(.*?)</p>', s),
    }

    secoes["abcpod"] = {
        "marca": achar(r'class="wall-logo"[^>]*>(.*?)</h2>', s, limpo=True),
        "subtitulo": achar(r'class="wall-logo__sub">(.*?)</p>', s, limpo=True),
        "chamada": achar(r'class="[^"]*photo-wall__tagline">(.*?)</p>', s, limpo=True),
        "botao": achar(r'class="btn__label">(.*?)</span>', s, limpo=True),
    }

    corpo = re.search(r'class="bio__body"(.*?)</div>', s, re.S)
    paragrafos = (
        [interno(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", corpo.group(1), re.S)]
        if corpo
        else []
    )
    secoes["quem_e"] = {
        "nome": achar(r'class="[^"]*bio__name"[^>]*>(.*?)</h2>', s, limpo=True),
        "linha_fina": achar(r'class="bio__standfirst">(.*?)</p>', s, limpo=True),
        "paragrafos_html": [p for p in paragrafos if p],
        "legenda_retrato": achar(r'class="bio__portrait-caption">(.*?)</figcaption>', s, limpo=True),
    }

    rec = re.search(r'class="bio__recognition"(.*?)</section>', s, re.S)
    grupos: list[dict[str, object]] = []
    if rec:
        for titulo, lista in re.findall(
            r"<h3[^>]*>(.*?)</h3>(.*?)(?=<h3|\Z)", rec.group(1), re.S
        ):
            itens = []
            for li in re.findall(r"<li[^>]*>(.*?)</li>", lista, re.S):
                nome = re.search(r'bio-list__name">(.*?)</p>', li, re.S)
                meta = re.search(
                    r'class="([^"]*bio-list__meta[^"]*)">(.*?)</p>', li, re.S
                )
                if not nome:
                    continue
                detalhe = interno(meta.group(2)) if meta else None
                if detalhe:
                    detalhe = interno(detalhe.replace(SEPARADOR, "·"))
                itens.append(
                    {
                        "nome_html": interno(nome.group(1)),
                        "detalhe": detalhe,
                        "tabular": bool(meta and "tabular" in meta.group(1)),
                    }
                )
            grupos.append({"titulo": puro(titulo), "itens": itens})
    secoes["reconhecimento"] = grupos

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(secoes, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"gravado em {DESTINO.relative_to(PROJETO)}\n")
    for nome, valor in secoes.items():
        if isinstance(valor, list):
            print(f"  {nome}: {len(valor)} grupos, {sum(len(g['itens']) for g in valor)} itens")
        else:
            faltando = [k for k, v in valor.items() if v is None]
            print(f"  {nome}: {len(valor)} campos" + (f"  NÃO ENCONTRADOS: {faltando}" if faltando else ""))
    if secoes["abcpod"]["marca"] == "Logo":
        print("\n  atenção: a seção do ABCPOD ainda está com o texto de exemplo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
