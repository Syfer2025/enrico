#!/usr/bin/env python3
"""conferir-segredos.py — procura credenciais dentro dos arquivos antes de subir."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent

PADROES = [
    ("token do GitHub (clássico)", re.compile(r"\bghp_[A-Za-z0-9]{36}\b")),
    ("token do GitHub (fine-grained)", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("token de app/OAuth do GitHub", re.compile(r"\bgh[opsu]_[A-Za-z0-9]{36}\b")),
    ("chave privada", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY")),
    ("chave da AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("chave da OpenAI", re.compile(r"\bsk-[A-Za-z0-9]{32,}\b")),
    ("token do Slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("senha dentro de URL", re.compile(r"://[^/\s:@]+:[^/\s:@]{4,}@[a-z0-9.-]+", re.I)),
]

IGNORAR_SUFIXOS = {
    ".webp", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".pdf", ".zip", ".dmg", ".mp4",
}


def arquivos_do_git() -> list[Path]:
    """Só o que está preparado para commit."""
    saida = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=PROJETO, capture_output=True, text=True, check=True,
    ).stdout
    return [PROJETO / linha for linha in saida.splitlines() if linha]


def arquivos_versionados() -> list[Path]:
    """Tudo que o Git acompanha ou acompanharia — o que iria para o público."""
    saida = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=PROJETO, capture_output=True, text=True, check=True,
    ).stdout
    return [PROJETO / linha for linha in saida.splitlines() if linha]


def main() -> int:
    alvos = arquivos_do_git() if "--git" in sys.argv else arquivos_versionados()
    alvos = [p for p in alvos if p.is_file() and p.suffix.lower() not in IGNORAR_SUFIXOS]

    achados: list[str] = []
    conferidos = 0

    for caminho in alvos:
        try:
            texto = caminho.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        conferidos += 1
        for rotulo, padrao in PADROES:
            for achado in padrao.finditer(texto):
                linha = texto[: achado.start()].count("\n") + 1
                relativo = caminho.relative_to(PROJETO)
                achados.append(f"  {relativo}:{linha} — {rotulo}")

    if achados:
        print(f"{len(achados)} possível(is) credencial(is) em {conferidos} arquivos:\n")
        print("\n".join(achados[:40]))
        print("\nTire isso antes de subir. O repositório é público.")
        return 1

    print(f"{conferidos} arquivos conferidos — nenhuma credencial encontrada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
