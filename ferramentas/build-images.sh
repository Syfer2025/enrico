#!/usr/bin/env bash
#
# build-images.sh — gera os derivados web das fotos do estúdio.
#
# Entrada : bastidores/originais/**/*.{png,jpg} — uma subpasta por finalidade
# Saída   : publicar/assets/img/<finalidade>/ — .webp em cada largura e um .jpg
#           de fallback
#
# Os originais moram fora de publicar/ de propósito: são 49 MB de PNG que geram
# o site mas não têm por que ser servidos junto com ele.
#
# Requisitos: sips (macOS, nativo) e cwebp (brew install webp)
# Uso: ./ferramentas/build-images.sh
#
set -euo pipefail

PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FONTES="$PROJETO/bastidores/originais"
SITE="$PROJETO/publicar"

# Pares "pasta de entrada:pasta de saída". O mural fica na raiz de originais/ por
# histórico; retratos e outros avulsos ficam em subpastas, que o glob de
# originais/*.png não alcança.
# Formato: "entrada:saída:larguras". A hero ocupa cerca de metade da tela, por
# isso pede densidade maior que o tile do mural.
PAIRS=(
  ":assets/img/wall:480,960"
  "portrait:assets/img/portrait:480,960"
  "hero:assets/img/hero:960,1440,2048,2880"
  "books:assets/img/books:320,640"
  # As capas da fileira "os últimos textos". O gen-escrita.py já deriva sozinho
  # ao baixar uma capa nova; este par existe para reconstruir tudo à mão depois
  # de trocar um original em bastidores/originais/escrita/.
  "escrita:assets/img/escrita:480,960"
)

JPEG_QUALITY=95
WEBP_QUALITY=95

command -v sips  >/dev/null || { echo "erro: sips não encontrado"; exit 1; }
command -v cwebp >/dev/null || { echo "erro: cwebp não encontrado — rode: brew install webp"; exit 1; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

shopt -s nullglob
for pair in "${PAIRS[@]}"; do
  IFS=':' read -r in_dir out_dir widths <<< "$pair"
  # in_dir vazio = a raiz de originais/, onde ficam as fotos do mural.
  SRC="$FONTES${in_dir:+/$in_dir}"
  OUT="$SITE/$out_dir"
  IFS=',' read -r -a WIDTHS <<< "$widths"
  [ -d "$SRC" ] || continue
  mkdir -p "$OUT"

  echo "originais/${in_dir}  ->  $out_dir  (${widths})"
  for src in "$SRC"/*.png "$SRC"/*.jpg; do
    [ -e "$src" ] || continue
    slug="$(basename "${src%.*}")"
    for w in "${WIDTHS[@]}"; do
      # sips -Z encaixa a imagem na maior dimensão mantendo a proporção.
      sips -Z "$w" "$src" --out "$TMP/$slug-$w.png" >/dev/null
      cwebp -quiet -q "$WEBP_QUALITY" "$TMP/$slug-$w.png" -o "$OUT/$slug-$w.webp"
    done
    # Um único JPEG de fallback na densidade maior.
    biggest="${WIDTHS[$((${#WIDTHS[@]} - 1))]}"  # índice negativo exige bash 4.3; o macOS traz 3.2
    sips -Z "$biggest" -s format jpeg -s formatOptions "$JPEG_QUALITY" \
         "$src" --out "$OUT/$slug-$biggest.jpg" >/dev/null
    echo "  ✓ $slug"
  done
  echo "  $(ls -1 "$OUT" | wc -l | tr -d ' ') arquivos, $(du -sh "$OUT" | cut -f1)"
  echo
done

echo "Pronto."
