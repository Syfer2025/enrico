#!/usr/bin/env python3
"""baixar-acervo.py — traz para casa todas as imagens que a página Escrita ainda"""

from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent / "publicar"
DESTINO = RAIZ / "assets/img/acervo"
BASTIDORES = RAIZ.parent / "bastidores"

LARGURA_MAX = 1200
QUALIDADE = 82

TIMEOUT = 25
TENTATIVAS = 3
WORKERS = 12

CABECALHOS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
}

PADRAO_URL = re.compile(r'https?://[^\s"\'<>)\\]+')
PADRAO_IMG = re.compile(r"\.(png|jpe?g|gif|webp|svg)(\?|$)", re.I)


def coletar_urls() -> list[str]:
    """Toda url de imagem citada no HTML da listagem ou no JSON do acervo."""
    urls: set[str] = set()
    for arquivo in (RAIZ / "escrita.html", BASTIDORES / "acervo-completo.json"):
        texto = arquivo.read_text(encoding="utf-8")
        urls |= {u for u in PADRAO_URL.findall(texto) if PADRAO_IMG.search(u)}
    return sorted(urls)


def nome_local(url: str, extensao: str) -> str:
    """Nome estável e legível: o basename original + hash curto da url inteira."""
    base = url.split("?")[0].rsplit("/", 1)[-1]
    base = re.sub(r"\.[^.]+$", "", base)
    base = re.sub(r"[^a-zA-Z0-9]+", "-", base).strip("-").lower()[:48] or "img"
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"{base}-{digest}{extensao}"


def baixar(url: str) -> bytes:
    erro_final: Exception | None = None
    for tentativa in range(TENTATIVAS):
        try:
            pedido = urllib.request.Request(url, headers=CABECALHOS)
            with urllib.request.urlopen(pedido, timeout=TIMEOUT) as resposta:
                return resposta.read()
        except Exception as erro:
            erro_final = erro
            if isinstance(erro, urllib.error.HTTPError) and erro.code in (404, 410):
                break
    raise erro_final


def processar(url: str) -> tuple[str, str | None, str | None]:
    """Devolve (url, caminho_local, erro)."""
    try:
        dados = baixar(url)
    except Exception as erro:
        return url, None, f"{type(erro).__name__}: {erro}"

    if not dados:
        return url, None, "resposta vazia"

    if dados[:200].lstrip()[:5] in (b"<?xml", b"<svg") or url.lower().endswith(".svg"):
        destino = DESTINO / nome_local(url, ".svg")
        destino.write_bytes(dados)
        return url, destino.relative_to(RAIZ).as_posix(), None

    try:
        imagem = Image.open(io.BytesIO(dados))
        imagem.load()
    except Exception as erro:
        return url, None, f"não é imagem válida: {type(erro).__name__}"

    animado = getattr(imagem, "n_frames", 1) > 1
    if animado:
        destino = DESTINO / nome_local(url, ".gif")
        destino.write_bytes(dados)
        return url, destino.relative_to(RAIZ).as_posix(), None

    if imagem.mode not in ("RGB", "RGBA"):
        imagem = imagem.convert("RGBA" if "A" in imagem.getbands() else "RGB")

    if imagem.width > LARGURA_MAX:
        altura = round(imagem.height * LARGURA_MAX / imagem.width)
        imagem = imagem.resize((LARGURA_MAX, altura), Image.LANCZOS)

    destino = DESTINO / nome_local(url, ".webp")
    imagem.save(destino, "WEBP", quality=QUALIDADE, method=5)
    return url, destino.relative_to(RAIZ).as_posix(), None


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    BASTIDORES.mkdir(parents=True, exist_ok=True)

    urls = coletar_urls()
    print(f"{len(urls)} imagens únicas para baixar", flush=True)

    mapa: dict[str, str] = {}
    falhas: dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for i, (url, caminho, erro) in enumerate(pool.map(processar, urls), 1):
            if caminho:
                mapa[url] = caminho
            else:
                falhas[url] = erro or "desconhecido"
            if i % 50 == 0 or i == len(urls):
                print(f"  {i}/{len(urls)} — ok {len(mapa)} / falhou {len(falhas)}", flush=True)

    (BASTIDORES / "acervo-mapa.json").write_text(
        json.dumps(mapa, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (BASTIDORES / "acervo-falhas.json").write_text(
        json.dumps(falhas, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    peso = sum(p.stat().st_size for p in DESTINO.iterdir() if p.is_file())
    print(f"\nbaixadas {len(mapa)} — {peso / 1_048_576:.1f} MB em {DESTINO.relative_to(RAIZ)}")
    print(f"falharam {len(falhas)} — detalhe em bastidores/acervo-falhas.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
