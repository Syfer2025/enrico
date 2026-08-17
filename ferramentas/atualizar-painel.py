#!/usr/bin/env python3
"""atualizar-painel.py — troca a versão do Sveltia CMS servida pelo painel."""

from __future__ import annotations

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
ADMIN = PROJETO / "publicar/admin"
VENDOR = ADMIN / "vendor"
PAGINA = ADMIN / "index.html"

REGISTRO = "https://registry.npmjs.org/@sveltia/cms/latest"
PACOTE = "https://unpkg.com/@sveltia/cms@{versao}/dist/sveltia-cms.js"


def ultima_versao() -> str:
    with urllib.request.urlopen(REGISTRO, timeout=30) as resposta:
        return json.load(resposta)["version"]


def main() -> int:
    versao = sys.argv[1] if len(sys.argv) > 1 else ultima_versao()

    atual = re.search(r'vendor/sveltia-cms-([\d.]+)\.js', PAGINA.read_text(encoding="utf-8"))
    if atual and atual.group(1) == versao:
        print(f"já está na {versao} — nada a fazer")
        return 0

    print(f"{atual.group(1) if atual else '(nenhuma)'} → {versao}\n")

    with urllib.request.urlopen(PACOTE.format(versao=versao), timeout=90) as resposta:
        dados = resposta.read()

    if not dados.lstrip().startswith((b"(function", b"var ", b"!function", b"import", b"const ")):
        print("erro: o que veio não parece javascript — nada foi trocado")
        print(f"       começa com: {dados[:80]!r}")
        return 1

    VENDOR.mkdir(parents=True, exist_ok=True)
    destino = VENDOR / f"sveltia-cms-{versao}.js"
    destino.write_bytes(dados)
    digital = hashlib.sha256(dados).hexdigest()

    pagina = PAGINA.read_text(encoding="utf-8")
    pagina = re.sub(r'vendor/sveltia-cms-[\d.]+\.js', f"vendor/sveltia-cms-{versao}.js", pagina)
    pagina = re.sub(r'Versão: [\d.]+', f"Versão: {versao}", pagina)
    pagina = re.sub(r'sha256: [0-9a-f]{64}', f"sha256: {digital}", pagina)
    PAGINA.write_text(pagina, encoding="utf-8")

    removidas = 0
    for antigo in VENDOR.glob("sveltia-cms-*.js"):
        if antigo != destino:
            antigo.unlink()
            removidas += 1

    print(f"  {len(dados) / 1_048_576:.1f} MB  sha256 {digital[:16]}…")
    print(f"  index.html atualizado" + (f", {removidas} versão(ões) antiga(s) removida(s)" if removidas else ""))
    print("\n  confira o painel antes de commitar: http://localhost:4322/admin/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
