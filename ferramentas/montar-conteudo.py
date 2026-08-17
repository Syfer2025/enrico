#!/usr/bin/env python3
"""montar-conteudo.py — transforma o conteúdo do site em arquivos que o painel edita."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"
BASTIDORES = PROJETO / "bastidores"
CONTEUDO = PROJETO / "conteudo"

from conteudo import escrever


def limpar(pasta: Path) -> Path:
    """Recria a pasta: item removido da fonte não pode sobrar como arquivo velho."""
    if pasta.exists():
        shutil.rmtree(pasta)
    pasta.mkdir(parents=True)
    return pasta


def montar_textos() -> int:
    acervo = json.loads((BASTIDORES / "acervo-completo.json").read_text(encoding="utf-8"))
    pasta = limpar(CONTEUDO / "textos")
    n = 0
    for grupo in acervo["grupos"]:
        for post in grupo["posts"]:
            escrever(
                pasta / f"{post['slug']}.md",
                {
                    "titulo": post["titulo"],
                    "data": post["data"],
                    "categoria": grupo["slug"],
                    "publicado": True,
                    "url_original": post["url"],
                },
                post["conteudo"],
            )
            n += 1
    return n


def montar_livros() -> int:
    dados = json.loads((SITE / "assets/data/livros.json").read_text(encoding="utf-8"))
    pasta = limpar(CONTEUDO / "livros")
    for ordem, livro in enumerate(dados["livros"], 1):
        escrever(
            pasta / f"{livro['slug']}.md",
            {
                "titulo": livro["titulo"],
                "subtitulo": livro.get("subtitulo"),
                "ordem": ordem,
                "asin": livro["asin"],
                "url": livro["url"],
                "capa": "/" + livro["capa"] if livro.get("capa") else None,
                "nota": livro.get("nota"),
                "avaliacoes": livro.get("avaliacoes"),
            },
            livro.get("sinopse", ""),
        )
    return len(dados["livros"])


def montar_episodios() -> int:
    dados = json.loads((SITE / "assets/data/episodios.json").read_text(encoding="utf-8"))
    pasta = limpar(CONTEUDO / "episodios")
    for ep in dados["episodios"]:
        if ep["temporada"] is not None and ep["episodio"] is not None:
            nome = f"t{ep['temporada']:02d}e{ep['episodio']:02d}"
        else:
            nome = f"especial-{ep['publicado_em']}"
        escrever(
            pasta / f"{nome}.md",
            {
                "convidado": ep["nome"],
                "temporada": ep["temporada"],
                "episodio": ep["episodio"],
                "youtube_id": ep["youtube_id"],
                "publicado_em": ep["publicado_em"],
                "duracao_s": ep["duracao_s"],
                "visualizacoes": ep["visualizacoes"],
            },
        )
    return len(dados["episodios"])


def main() -> int:
    ja_existe = [p.name for p in (CONTEUDO / "textos", CONTEUDO / "livros",
                                  CONTEUDO / "episodios") if p.exists()]
    if ja_existe and "--forcar" not in sys.argv:
        print("conteudo/ já existe — este script sobrescreve e não vai rodar.\n")
        print(f"  pastas que seriam apagadas: {', '.join(ja_existe)}")
        print("  elas são a fonte de verdade do site hoje; o que estiver nelas")
        print("  veio do painel e não está em mais lugar nenhum.\n")
        print("  se é isso mesmo que você quer, repita com --forcar")
        return 1

    CONTEUDO.mkdir(exist_ok=True)
    contagens = {
        "textos": montar_textos(),
        "livros": montar_livros(),
        "episodios": montar_episodios(),
    }
    print(f"conteúdo montado em {CONTEUDO.relative_to(PROJETO)}/\n")
    for nome, n in contagens.items():
        print(f"  {nome:11} {n:4}")
    print("\n  seções: geradas pelo extrair-secoes.py, não por este script")
    peso = sum(p.stat().st_size for p in CONTEUDO.rglob("*") if p.is_file())
    print(f"  {peso / 1024:.0f} KB no total — texto puro, versionável")
    return 0


if __name__ == "__main__":
    sys.exit(main())
