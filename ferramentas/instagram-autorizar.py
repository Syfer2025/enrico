#!/usr/bin/env python3
"""instagram-autorizar.py — troca o código da autorização pela chave definitiva."""

from __future__ import annotations

import getpass
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

REDIRECIONAMENTO = "https://syfer2025.github.io/enrico/"

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
    print("O `code` fica na barra de endereço, assim:")
    print(f"  {REDIRECIONAMENTO}?code=AQUELE_PEDACAO_COMPRIDO#_")
    print("Copie só o que vem depois de `code=` e antes de `#_`, se houver.")
    print()

    app_id = pedir("ID do app do Instagram: ")
    segredo = pedir("Chave secreta do app (não aparece na tela): ", secreto=True)
    codigo = pedir("O `code` da autorização: ")

    codigo = codigo.split("#")[0].strip()

    print("\n1/3 trocando o código pela chave curta…")
    chave = user_id = usuario = ""
    dias = 0

    try:
        curta = postar(
            TROCA_CURTA,
            {
                "client_id": app_id,
                "client_secret": segredo,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECIONAMENTO,
                "code": codigo,
            },
        )
        print("     (caminho: login pelo Instagram)")
        chave_curta = curta["access_token"]

        print("2/3 trocando pela chave de longa duração…")
        longa = buscar(
            TROCA_LONGA,
            {
                "grant_type": "ig_exchange_token",
                "client_secret": segredo,
                "access_token": chave_curta,
            },
        )
        chave = longa["access_token"]
        dias = int(longa.get("expires_in", 0)) // 86400

        print("3/3 conferindo de qual conta é…")
        quem = buscar(PERFIL, {"fields": "id,username", "access_token": chave})
        user_id = str(quem.get("id") or curta.get("user_id") or "")
        usuario = quem.get("username", "?")

    except (SystemExit, KeyError):
        print("     (o caminho do Instagram recusou; indo pelo do Facebook)")

        curta = buscar(
            "https://graph.facebook.com/v21.0/oauth/access_token",
            {
                "client_id": app_id,
                "client_secret": segredo,
                "redirect_uri": REDIRECIONAMENTO,
                "code": codigo,
            },
        )
        chave_curta = curta.get("access_token")
        if not chave_curta:
            raise SystemExit(f"erro: nenhum dos dois caminhos deu chave.\n  {curta}")

        print("2/3 trocando pela chave de longa duração…")
        longa = buscar(
            "https://graph.facebook.com/v21.0/oauth/access_token",
            {
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": segredo,
                "fb_exchange_token": chave_curta,
            },
        )
        chave = longa.get("access_token", chave_curta)
        dias = int(longa.get("expires_in", 0)) // 86400

        print("3/3 procurando a conta do Instagram nas Páginas…")
        paginas = buscar(
            "https://graph.facebook.com/v21.0/me/accounts",
            {"fields": "name,instagram_business_account", "access_token": chave},
        )
        for pagina in paginas.get("data", []):
            conta = pagina.get("instagram_business_account")
            if conta:
                user_id = str(conta["id"])
                perfil = buscar(
                    f"https://graph.facebook.com/v21.0/{user_id}",
                    {"fields": "username", "access_token": chave},
                )
                usuario = perfil.get("username", "?")
                print(f"     achei em: {pagina.get('name', '?')}")
                break

        if not user_id:
            raise SystemExit(
                "erro: a autorização funcionou, mas nenhuma Página do Facebook\n"
                "      tem conta do Instagram ligada. É isso que falta:\n"
                "      no Instagram, Editar perfil -> Página -> ligar a uma Página."
            )

    print()
    print("=" * 66)
    print(f"  Funcionou. A conta é @{usuario}, e a chave vale {dias} dias.")
    print("=" * 66)
    print()
    print("Agora crie DOIS segredos no GitHub, em")
    print("  Settings -> Secrets and variables -> Actions -> New repository secret")
    print()
    print("  Nome:  INSTAGRAM_TOKEN")
    print(f"  Valor: {chave}")
    print()
    print("  Nome:  INSTAGRAM_USER_ID")
    print(f"  Valor: {user_id}")
    print()
    print("Depois disso, na aba Actions, rode o fluxo `instagram` uma vez à mão.")
    print("Ele busca os posts, comita, e a partir daí se atualiza sozinho.")
    print()
    print("Feche este terminal quando terminar: a chave está só aqui na tela,")
    print("não foi gravada em arquivo nenhum.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
