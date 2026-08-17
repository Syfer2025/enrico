#!/usr/bin/env python3
"""conferir-painel.py — procura no config.yml os erros que derrubam o painel inteiro."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
CONFIG = PROJETO / "publicar/admin/config.yml"

PAR = re.compile(r"^(?P<recuo>\s*)(?:- )?(?P<chave>[A-Za-z_][\w-]*):[ \t]+(?P<valor>\S.*)$")


EXPLICACAO = re.compile(r'\b(comment|hint):[ \t]*(?:"(?P<aspas>[^"]*)"|(?P<bloco>[>|]-?)\s*$|(?P<solto>[^,}\n]+))')


def explicacoes(linhas: list[str]) -> list[tuple[int, str, str]]:
    """(linha, chave, texto) de cada comment/hint, bloco já juntado."""
    achadas = []
    for i, linha in enumerate(linhas):
        if linha.lstrip().startswith("#"):
            continue
        for m in EXPLICACAO.finditer(linha):
            chave = m.group(1)
            if m.group("bloco"):
                recuo = len(linha) - len(linha.lstrip())
                partes = []
                for seguinte in linhas[i + 1:]:
                    if not seguinte.strip():
                        break
                    if len(seguinte) - len(seguinte.lstrip()) <= recuo:
                        break
                    partes.append(seguinte.strip())
                achadas.append((i + 1, chave, " ".join(partes)))
            else:
                achadas.append((i + 1, chave, (m.group("aspas") or m.group("solto") or "").strip()))
    return achadas


def conferir_marcacao(linhas: list[str]) -> list[str]:
    """Exemplo de marcação solto numa dica: o painel formata em vez de mostrar."""
    erros = []
    for n, chave, valor in explicacoes(linhas):
        fora = re.sub(r"`[^`]*`", "", valor)
        if re.search(r"\*\S|\[[^\]]+\]\(", fora):
            erros.append(
                f"linha {n}: `{chave}` tem exemplo de marcação fora de acentos "
                f"graves — o painel vai formatar em vez de mostrar. Escreva `*assim*`."
            )
    return erros


def conferir(texto: str) -> list[str]:
    linhas = texto.splitlines()
    erros: list[str] = conferir_marcacao(linhas)

    for n, linha in enumerate(linhas, 1):
        crua = linha.rstrip("\n")

        if "\t" in crua:
            erros.append(f"linha {n}: tabulação — YAML só aceita espaços")

        if crua.lstrip().startswith("#"):
            continue

        m = PAR.match(crua)
        if not m:
            continue
        valor = m.group("valor").strip()

        if valor.startswith('"'):
            miolo = re.sub(r"[,}\]]*\s*(#.*)?$", "", valor)
            if not (len(miolo) >= 2 and miolo.endswith('"')):
                erros.append(
                    f'linha {n}: `{m.group("chave")}` abre aspas e não fecha na '
                    f"mesma linha — o YAML engole as linhas seguintes"
                )
            continue

        if valor.startswith(("'", ">", "|", "{", "[", "&", "*")):
            continue

        if ": " in valor:
            erros.append(
                f'linha {n}: `{m.group("chave")}` sem aspas com ": " no meio — '
                f"o YAML lê como campo dentro de campo. Ponha entre aspas."
            )
        if " #" in valor:
            erros.append(
                f'linha {n}: `{m.group("chave")}` sem aspas com " #" no meio — '
                f"daí para frente o YAML trata como comentário. Ponha entre aspas."
            )

    return erros


def main() -> int:
    if not CONFIG.exists():
        print(f"não achei {CONFIG.relative_to(PROJETO)}")
        return 1

    erros = conferir(CONFIG.read_text(encoding="utf-8"))
    alvo = CONFIG.relative_to(PROJETO)

    if not erros:
        print(f"{alvo} — nenhum dos erros conhecidos de YAML")
        print("  (isto não substitui abrir admin/teste.html e olhar)")
        return 0

    print(f"{alvo} — {len(erros)} problema(s):\n")
    for e in erros:
        print(f"  {e}")
    print("\nO painel NÃO vai abrir assim.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
