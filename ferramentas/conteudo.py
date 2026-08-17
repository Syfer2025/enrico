#!/usr/bin/env python3
"""conteudo.py — lê os arquivos que o painel edita."""

from __future__ import annotations

import json
import re
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
CONTEUDO = PROJETO / "conteudo"


def _valor(bruto: str) -> object:
    """Converte um valor do cabeçalho para o tipo certo."""
    bruto = bruto.strip()
    if not bruto or bruto in ('""', "''"):
        return None
    if bruto[0] in "\"'" and bruto[-1] == bruto[0]:
        return bruto[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    if bruto in ("true", "false"):
        return bruto == "true"
    if bruto == "null":
        return None
    if re.fullmatch(r"-?\d+", bruto):
        return int(bruto)
    if re.fullmatch(r"-?\d*\.\d+", bruto):
        return float(bruto)
    return bruto


def ler_arquivo(caminho: Path) -> dict:
    """Um arquivo → dict com os campos do cabeçalho mais `body` e `slug`."""
    texto = caminho.read_text(encoding="utf-8")
    campos: dict[str, object] = {}
    corpo = texto

    if texto.startswith("---"):
        fim = texto.find("\n---", 3)
        if fim != -1:
            cabecalho = texto[3:fim]
            corpo = texto[fim + 4 :]
            chave_lista: str | None = None
            for linha in cabecalho.splitlines():
                if not linha.strip():
                    continue
                item = re.match(r"\s+-\s+(.*)$", linha)
                if item and chave_lista:
                    campos[chave_lista].append(_valor(item.group(1)))
                    continue
                par = re.match(r"([A-Za-z_][\w-]*):\s*(.*)$", linha)
                if not par:
                    continue
                chave, bruto = par.group(1), par.group(2)
                if bruto.strip() == "":
                    campos[chave] = []
                    chave_lista = chave
                else:
                    campos[chave] = _valor(bruto)
                    chave_lista = None

    campos["body"] = corpo.strip()
    campos["slug"] = caminho.stem
    return campos


def ler_colecao(nome: str, ordenar_por: str | None = None) -> list[dict]:
    """Todos os itens de conteudo/<nome>/, em ordem de nome de arquivo."""
    pasta = CONTEUDO / nome
    if not pasta.is_dir():
        raise FileNotFoundError(
            f"conteudo/{nome}/ não existe — rode ferramentas/montar-conteudo.py"
        )
    itens = [ler_arquivo(p) for p in sorted(pasta.glob("*.md"))]
    if ordenar_por:
        itens.sort(key=lambda i: (i.get(ordenar_por) is None, i.get(ordenar_por)))
    return itens


def _yaml_valor(v: object) -> str:
    """Escapa um valor para o cabeçalho YAML. Só o necessário, sem dependência."""
    if v is None:
        return '""'
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def escrever(destino: Path, campos: dict[str, object], corpo: str = "") -> None:
    """Grava um arquivo no mesmo formato que o painel lê e escreve."""
    linhas = ["---"]
    for chave, valor in campos.items():
        if isinstance(valor, list):
            linhas.append(f"{chave}:")
            linhas += [f"  - {_yaml_valor(i)}" for i in valor]
        else:
            linhas.append(f"{chave}: {_yaml_valor(valor)}")
    linhas += ["---", ""]
    if corpo:
        linhas += [corpo.strip(), ""]
    destino.write_text("\n".join(linhas), encoding="utf-8")


def ler_json(nome: str) -> dict:
    """Um arquivo de conteúdo que é JSON puro, como o secoes.json."""
    caminho = CONTEUDO / nome
    if not caminho.exists():
        raise FileNotFoundError(
            f"conteudo/{nome} não existe — rode ferramentas/montar-conteudo.py"
        )
    return json.loads(caminho.read_text(encoding="utf-8"))
