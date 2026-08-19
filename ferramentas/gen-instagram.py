#!/usr/bin/env python3
"""gen-instagram.py — a seção com os posts do Instagram dele."""

from __future__ import annotations

import html
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

from conteudo import ler_json

PROJETO = Path(__file__).resolve().parent.parent
SITE = PROJETO / "publicar"
HOME = SITE / "index.html"
CACHE = PROJETO / "conteudo/instagram.json"
IMAGENS = SITE / "assets/img/instagram"

MARCA_INICIO = "<!-- INSTAGRAM:INICIO (gerado por ferramentas/gen-instagram.py) -->"
MARCA_FIM = "<!-- INSTAGRAM:FIM -->"

QUANTOS = 6

LARGURAS = (320, 640)
QUALIDADE = 82

CAMPOS = "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp"


def buscar(token: str, user_id: str, quantos: int) -> list[dict]:
    """Os posts mais recentes, pela API da Meta."""
    caminhos = [
        f"https://graph.instagram.com/v21.0/{urllib.parse.quote(user_id)}/media",
        f"https://graph.facebook.com/v21.0/{urllib.parse.quote(user_id)}/media",
    ]
    dados = None
    erros = []
    for base in caminhos:
        endereco = (
            f"{base}?fields={CAMPOS}&limit={quantos}"
            f"&access_token={urllib.parse.quote(token)}"
        )
        try:
            with urllib.request.urlopen(endereco, timeout=30) as r:
                dados = json.loads(r.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as erro:
            corpo = erro.read().decode("utf-8", "replace")[:200]
            erros.append(f"{base.split('/')[2]}: {erro.code} {corpo}")

    if dados is None:
        raise SystemExit(
            "erro: nenhum dos dois caminhos da Meta respondeu.\n  "
            + "\n  ".join(erros)
        )

    posts = []
    for item in dados.get("data", []):
        imagem = item.get("thumbnail_url") or item.get("media_url")
        if not imagem:
            continue
        posts.append(
            {
                "id": item["id"],
                "link": item.get("permalink", ""),
                "legenda": (item.get("caption") or "").strip(),
                "tipo": item.get("media_type", "IMAGE"),
                "data": (item.get("timestamp") or "")[:10],
                "imagem_origem": imagem,
            }
        )
    return posts


def baixar_imagens(posts: list[dict]) -> list[dict]:
    """Traz a imagem de cada post para cá, nas larguras do cartão."""
    IMAGENS.mkdir(parents=True, exist_ok=True)
    prontos = []
    for post in posts:
        bruto = IMAGENS / f"{post['id']}.tmp"
        try:
            pedido = urllib.request.Request(
                post["imagem_origem"],
                headers={"User-Agent": "site-enrico-pierro/1.0"},
            )
            with urllib.request.urlopen(pedido, timeout=60) as r:
                bruto.write_bytes(r.read())

            with Image.open(bruto) as imagem:
                imagem.load()
                if imagem.mode not in ("RGB", "RGBA"):
                    imagem = imagem.convert("RGB")
                larguras = []
                for largura in LARGURAS:
                    if largura > imagem.width and largura != LARGURAS[0]:
                        continue
                    altura = round(imagem.height * largura / imagem.width)
                    destino = IMAGENS / f"{post['id']}-{largura}.webp"
                    imagem.resize((largura, altura), Image.LANCZOS).save(
                        destino, "WEBP", quality=QUALIDADE
                    )
                    larguras.append(largura)
                post["larguras"] = larguras
                post["proporcao"] = round(imagem.width / imagem.height, 4)
            prontos.append(post)
        except (urllib.error.URLError, OSError, ValueError) as erro:
            print(f"  aviso: não baixei a imagem do post {post['id']} ({erro})")
        finally:
            bruto.unlink(missing_ok=True)

    for post in prontos:
        post.pop("imagem_origem", None)
    return prontos


def limpar_orfas(posts: list[dict]) -> int:
    """Apaga imagem de post que saiu da seção, para a pasta não crescer sem fim."""
    if not IMAGENS.exists():
        return 0
    vivos = {p["id"] for p in posts}
    apagadas = 0
    for arquivo in IMAGENS.glob("*.webp"):
        ident = arquivo.name.rsplit("-", 1)[0]
        if ident not in vivos:
            arquivo.unlink()
            apagadas += 1
    return apagadas


def primeira_linha(legenda: str, limite: int = 90) -> str:
    """A legenda encurtada para caber no cartão."""
    limpo = " ".join(
        p for p in legenda.split() if not p.startswith("#") and not p.startswith("@")
    )
    if len(limpo) <= limite:
        return limpo
    corte = limpo[:limite].rsplit(" ", 1)[0]
    return corte + "…"


def cartao(post: dict) -> str:
    e = html.escape
    larguras = post.get("larguras") or [LARGURAS[0]]
    base = f"assets/img/instagram/{post['id']}"
    srcset = ", ".join(f"{base}-{w}.webp {w}w" for w in larguras)
    legenda = primeira_linha(post.get("legenda", ""))
    rotulo = legenda or "ver publicação no Instagram"
    marca_video = (
        '\n            <span class="ig-card__video" aria-hidden="true">'
        '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>'
        "</span>"
        if post.get("tipo") in ("VIDEO", "REELS")
        else ""
    )
    return f"""        <li class="ig-card">
          <a class="ig-card__link" href="{e(post['link'])}" target="_blank" rel="noopener">
            <span class="ig-card__foto">
              <img
                src="{base}-{larguras[0]}.webp"
                srcset="{srcset}"
                sizes="(width >= 900px) 30vw, 45vw"
                alt=""
                width="{larguras[-1]}"
                height="{round(larguras[-1] / (post.get('proporcao') or 1))}"
                loading="lazy"
                decoding="async"
              />
            </span>{marca_video}
            <span class="ig-card__legenda">{e(legenda)}</span>
            <span class="visually-hidden">{e(rotulo)}</span>
          </a>
        </li>"""


def secao(posts: list[dict], perfil: str) -> str:
    """A seção inteira. Sem posts, devolve string vazia — e não uma caixa vazia."""
    if not posts:
        return ""
    cartoes = "\n".join(cartao(p) for p in posts)
    return f"""{MARCA_INICIO}
      <section class="instagram" id="instagram" aria-labelledby="instagram-titulo">
        <div class="container instagram__inner">
          <div class="instagram__head">
            <p class="t-eyebrow instagram__eyebrow">instagram</p>
            <h2 class="t-display-2 instagram__titulo" id="instagram-titulo">
              o que ele andou postando
            </h2>
          </div>

          <ul class="ig-grade">
{cartoes}
          </ul>

          <a class="instagram__perfil" href="{html.escape(perfil)}"
             target="_blank" rel="noopener">
            ver o perfil no instagram
          </a>
        </div>
      </section>
{MARCA_FIM}"""


def injetar(bloco: str) -> bool:
    """Escreve a seção no index.html, entre os marcadores."""
    s = HOME.read_text(encoding="utf-8")

    if MARCA_INICIO in s:
        i = s.index(MARCA_INICIO)
        f = s.index(MARCA_FIM) + len(MARCA_FIM)
        novo = s[:i] + (bloco or MARCA_INICIO + "\n" + MARCA_FIM) + s[f:]
    else:
        if not bloco:
            return False
        alvo = "      <!--\n        ==================================================================\n        SEÇÃO 03 — Mural de fotos"
        if alvo not in s:
            raise SystemExit(
                "erro: não achei o começo da seção do mural no index.html para\n"
                "      pôr a do Instagram antes dela. A marcação mudou?"
            )
        novo = s.replace(alvo, bloco + "\n\n" + alvo, 1)

    HOME.write_text(novo, encoding="utf-8")
    return True


def main() -> int:
    quantos = QUANTOS
    if "--quantos" in sys.argv:
        quantos = int(sys.argv[sys.argv.index("--quantos") + 1])

    cfg = ler_json("site.json")
    perfil = cfg.get("instagram_perfil") or "https://www.instagram.com/enricopierroofc/"

    if "--buscar" in sys.argv:
        token = os.environ.get("INSTAGRAM_TOKEN", "").strip()
        user_id = (
            os.environ.get("INSTAGRAM_USER_ID", "").strip()
            or str(cfg.get("instagram_user_id") or "").strip()
            or "me"
        )
        if not token:
            raise SystemExit(
                "erro: falta a variável INSTAGRAM_TOKEN.\n"
                "       Ela é a chave de longa duração da Meta. No fluxo agendado\n"
                "       ela vem do segredo do repositório; na sua máquina, use\n"
                "       INSTAGRAM_TOKEN=... python3 ferramentas/gen-instagram.py --buscar"
            )
        try:
            posts = buscar(token, user_id, quantos)
        except urllib.error.HTTPError as erro:
            corpo = erro.read().decode("utf-8", "replace")[:300]
            raise SystemExit(
                f"erro: a Meta respondeu {erro.code}.\n       {corpo}\n"
                "       Chave vencida (60 dias) ou permissão revogada são as causas\n"
                "       comuns. O site continua com os posts já baixados."
            ) from None

        posts = baixar_imagens(posts)
        if not posts:
            raise SystemExit(
                "erro: a busca não trouxe nenhum post com imagem. O cache\n"
                "       anterior foi mantido, e a seção segue como está."
            )
        CACHE.write_text(
            json.dumps({"perfil": perfil, "posts": posts}, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        orfas = limpar_orfas(posts)
        print(f"instagram: {len(posts)} post(s) baixado(s)")
        if orfas:
            print(f"  {orfas} imagem(ns) de post antigo apagada(s)")

    if not CACHE.exists():
        print("instagram: sem conteudo/instagram.json — a seção não é gerada.")
        print("  Rode com --buscar depois de configurar a chave da Meta.")
        injetar("")
        return 0

    guardado = json.loads(CACHE.read_text(encoding="utf-8"))
    posts = guardado.get("posts", [])[:quantos]
    entrou = injetar(secao(posts, guardado.get("perfil", perfil)))
    print(f"instagram: seção com {len(posts)} cartão(ões)" if entrou else "instagram: nada a fazer")
    return 0


if __name__ == "__main__":
    sys.exit(main())
