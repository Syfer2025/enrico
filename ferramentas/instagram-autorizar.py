#!/usr/bin/env python3
"""instagram-autorizar.py — troca o código da autorização pela chave definitiva."""

from __future__ import annotations

import getpass
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent

ID_PADRAO = "1091594863444165"
ID_FACEBOOK = "1582552550335887"

REDIRECIONAMENTOS = [
    "https://syfer2025.github.io/enrico/",
    "https://syfer2025.github.io/enrico/autorizar.html",
]

TROCA_CURTA = "https://api.instagram.com/oauth/access_token"
TROCA_LONGA = "https://graph.instagram.com/access_token"
PERFIL = "https://graph.instagram.com/me"


def pedir(rotulo: str, secreto: bool = False) -> str:
    valor = (getpass.getpass(rotulo) if secreto else input(rotulo)).strip()
    if not valor:
        raise SystemExit("erro: vazio. Nada foi feito.")
    return valor


def postar(endereco: str, campos: dict) -> dict:
    corpo = urllib.parse.urlencode(campos).encode()
    pedido = urllib.request.Request(endereco, data=corpo)
    try:
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"erro: a Meta respondeu {erro.code}.\n  {detalhe}") from None


def buscar(endereco: str, campos: dict) -> dict:
    url = endereco + "?" + urllib.parse.urlencode(campos)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", "replace")[:400]
        raise SystemExit(f"erro: a Meta respondeu {erro.code}.\n  {detalhe}") from None


def main() -> int:
    print(__doc__.split("Uso:")[0].strip().splitlines()[0])
    print()
    print("Tenha em mão: o ID do app do Instagram, a chave secreta do app, e o")
    print("`code` que apareceu no endereço depois de ele autorizar.")
    print()
    print("O `code` é o que a página de autorização mostrou na caixa, e o que")
    print("ele mandou de volta no WhatsApp. Vale por uma hora e serve uma vez.")
    print()

    print("Qual endereço estava no link que você mandou para ele?")
    print("(se você usou o link que eu te passei, é o 1 — só aperte Enter)")
    for i, r in enumerate(REDIRECIONAMENTOS, 1):
        print(f"  {i}) {r}" + ("   (padrão, o que o painel gera)" if i == 1 else ""))
    escolha = input("Número [1]: ").strip() or "1"
    if escolha not in {"1", "2"}:
        raise SystemExit("erro: escolha 1 ou 2. Nada foi feito.")
    redirecionamento = REDIRECIONAMENTOS[int(escolha) - 1]
    print(f"  usando: {redirecionamento}")
    print()

    app_id = input(f"ID do app do Instagram [{ID_PADRAO}]: ").strip() or ID_PADRAO
    segredo = pedir("Chave secreta do app (não aparece na tela): ", secreto=True)
    codigo = pedir("O `code` da autorização: ")

    codigo = codigo.split("#")[0].strip()

    print("\n1/3 trocando o código pela chave curta…")

    try:
        curta = postar(
            TROCA_CURTA,
            {
                "client_id": app_id,
                "client_secret": segredo,
                "grant_type": "authorization_code",
                "redirect_uri": redirecionamento,
                "code": codigo,
            },
        )
    except (SystemExit, KeyError) as recusa:
        print()
        print("  A Meta recusou. O que ela respondeu:")
        for linha in str(recusa).splitlines():
            print(f"    {linha}")
        print()
        texto = str(recusa)
        if "has been used" in texto:
            print("  ESTE CÓDIGO JÁ FOI GASTO. Cada código serve uma vez só.")
            print("  Precisa de um novo: mande o link de autorização outra vez.")
        elif "Invalid authorization code" in texto or "expired" in texto:
            print("  O código não vale mais — passou da hora, ou veio cortado.")
            print("  Confira se você colou ele inteiro, sem faltar o começo.")
        else:
            print("  Confira, nesta ordem:")
            print("   · a chave secreta é a DO INSTAGRAM, não a do Facebook")
            print("     (página 'Configuração da API com login do Instagram')")
            print("   · o endereço escolhido no começo é o que estava no link")
        print()
        print("  O código NÃO foi trocado. Nada foi gravado.")
        raise SystemExit(1)

    chave_curta = curta.get("access_token")
    user_id = str(curta.get("user_id") or "")
    if not chave_curta:
        raise SystemExit(f"erro: a Meta respondeu sem chave.\n  {curta}")

    parcial = PROJETO / "chave-instagram-parcial.txt"
    parcial.write_text(
        "Chave CURTA (vale cerca de 1 hora). Rede de segurança: se os passos\n"
        "seguintes falharem, ela ainda pode ser trocada pela de 60 dias sem\n"
        "precisar de nova autorização. Apague este arquivo quando terminar.\n\n"
        f"{chave_curta}\n",
        encoding="utf-8",
    )
    parcial.chmod(0o600)
    print("     deu certo. Chave curta já guardada, por segurança.")

    print("2/3 trocando pela chave de longa duração…")
    try:
        longa = buscar(
            TROCA_LONGA,
            {
                "grant_type": "ig_exchange_token",
                "client_secret": segredo,
                "access_token": chave_curta,
            },
        )
    except (SystemExit, KeyError) as recusa:
        print()
        print("  A troca pela chave de 60 dias falhou:")
        for linha in str(recusa).splitlines():
            print(f"    {linha}")
        print()
        print("  MAS NÃO PRECISA PEDIR NADA AO AUTOR OUTRA VEZ.")
        print("  A chave curta está salva e vale cerca de uma hora:")
        print(f"    {parcial}")
        print("  Me mostre o erro acima e eu concluo a partir dela.")
        raise SystemExit(1)

    chave = longa.get("access_token", chave_curta)
    dias = int(longa.get("expires_in", 0)) // 86400

    print("3/3 conferindo de qual conta é…")
    usuario = "?"
    try:
        quem = buscar(PERFIL, {"fields": "username", "access_token": chave})
        usuario = quem.get("username", "?")
        user_id = str(quem.get("user_id") or user_id)
    except (SystemExit, KeyError):
        print("     (não deu para ler o @; não faz falta, seguindo)")

    if not user_id:
        raise SystemExit(
            "erro: a chave veio, mas sem o identificador da conta.\n"
            f"      A chave está salva em {parcial} — me avise."
        )

    parcial.unlink()

    destino = PROJETO / "chave-instagram.txt"
    destino.write_text(
        "Cole cada valor no GitHub e depois APAGUE este arquivo.\n"
        "https://github.com/Syfer2025/enrico/settings/secrets/actions/new\n\n"
        "Nome:  INSTAGRAM_TOKEN\n"
        f"Valor: {chave}\n\n"
        "Nome:  INSTAGRAM_USER_ID\n"
        f"Valor: {user_id}\n",
        encoding="utf-8",
    )
    destino.chmod(0o600)

    print()
    print("=" * 66)
    print(f"  Funcionou. A conta e @{usuario}, e a chave vale {dias} dias.")
    print("=" * 66)
    print()
    print("A chave NAO aparece aqui, de proposito. Ela esta neste arquivo:")
    print(f"  {destino}")
    print()
    print("Abra o arquivo, cole os dois valores no GitHub, e apague o arquivo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
