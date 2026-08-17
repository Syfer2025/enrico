# Base do site

Estrutura para montar o site seção por seção. HTML/CSS/JS puros, sem build e
sem dependências: abrir `index.html` num servidor local já roda.

```bash
./tools/dev-server.py
```

Depois: <http://localhost:4321>

> Módulos ES exigem `http://`. Abrir o arquivo por `file://` quebra os imports.

O servidor é um `http.server` com dois ajustes:

- `Cache-Control: no-store` em tudo. Sem isso o navegador serve CSS antigo do
  cache depois de uma edição — **inclusive com reload forçado** — e você fica
  olhando para uma versão que não existe mais no disco.
- Descarta `If-Modified-Since`/`If-None-Match` da requisição, para nunca cair
  em 304. Reescrever o 304 para 200 depois não resolve: a resposta sai sem
  corpo e sem `Content-Length`, e o navegador recusa os módulos ES com
  *"Failed to fetch dynamically imported module"*.
- Fixa `.js` como `text/javascript`. O `mime.types` de alguns macOS devolve
  `text/plain`, e módulo ES com esse tipo não carrega.

---

## Como está organizado

```
index.html                       monta a página e declara os módulos
episodios.html                   subpágina de episódios — GERADA, não editar
styles/
  tokens.css                     ← única fonte de verdade do sistema visual
  base.css                       reset, tipografia, acessibilidade
  layout.css                     casco: contêiner, cabeçalho, rodapé, redes
  components.css                 botão e material (todos os estados)
  sections/photo-wall.css        uma seção = um arquivo
scripts/
  main.js                        registro: data-module → função de init
  header.js
  sections/photo-wall.js
assets/
  source/                        PNGs originais (nunca modificados)
  img/wall/                      derivados web gerados pelo script
  data/                          dados capturados, com a data da captura
tools/build-images.sh            gera os derivados
tools/gen-books.py               carrossel de livros (injeta no index)
tools/gen-escrita.py             seção coluna/textos/diário (injeta no index)
tools/gen-episodios.py           escreve episodios.html inteiro
```

### Blocos gerados

Três partes do site não são escritas à mão. Cada script guarda os dados em
`assets/data/*.json` com a data da captura e escreve a marcação:

| script | dados | destino |
|---|---|---|
| `gen-books.py` | `livros.json` | `index.html`, entre `CARROSSEL:INICIO/FIM` |
| `gen-escrita.py` | `escrita.json` | `index.html`, entre `ESCRITA:INICIO/FIM` |
| `gen-episodios.py` | `episodios.json` | `episodios.html` (arquivo inteiro) |

Editar o bloco no HTML não adianta: a próxima rodada sobrescreve. Mexa na
lista dentro do script e rode de novo.

### Adicionar uma seção

1. `styles/sections/nome.css` → adicionar o `<link>` no `index.html`.
2. Marcação dentro do `<main>`, no lugar de um `.section-slot`.
3. Se precisar de comportamento: `scripts/sections/nome.js` exportando
   `initNome(el)`, registrado em `MODULES` no `main.js`, e `data-module="nome"`
   no elemento raiz.

Um módulo que quebra não derruba os outros — o `main.js` isola cada init.

### Trocar as fotos

Colocar os PNGs em `assets/source/` com nomes `ep-01.png`, `ep-02.png`… e rodar:

```bash
./tools/build-images.sh
```

Gera `-480.webp`, `-960.webp` e um `-960.jpg` de fallback para cada foto.
Requer `cwebp` (`brew install webp`). As 20 fotos atuais saíram de 37 MB para
3,0 MB.

São 20 fotos para as 20 posições do mural — nenhuma se repete. Se você mudar o
número de faixas ou de tiles por faixa, ajuste a marcação e confira que a conta
continua fechando (o script só clona o conjunto para cobrir a largura; não
inventa imagem).

### Marcadores de desenvolvimento

`<body data-dev="true">` mostra as caixas das seções ainda vazias. Remover o
atributo esconde todas.

---

## Seção 02 — Mural de fotos

Réplica da seção de referência (`stevenbartlett.com`), com a geometria medida
direto no site em viewport 1440×900:

| | referência | aqui |
|---|---|---|
| tile | 300 × 200 (3:2) | 300 × 200 |
| contorno do tile | `1px solid #444` | `1px solid #38383a` (separador opaco do HIG) |
| raio do tile | 20 px | 20 px (`--radius-lg`) |
| área da imagem | 298 × 198 (border-box) | 298 × 198 |
| vão entre tiles | 22 px | 23 px (grade de 8 pt) |
| altura da faixa | 220 px | 223 px |
| faixas | 4 | 4 |
| início da grade | 100 px abaixo do topo | 100 px |
| bloco de texto | `absolute; top: 120px` | `absolute; top: 13%` → 119 px |
| última faixa | cortada em 80 px pela base | cortada em 80 px |
| altura da seção | 900 px (100vh) | 912 px |

A altura da seção vem da grade (`--grid-top + --row-count × --row-h` menos o
corte), não de `100svh`. Com `svh` o mural não fechava: no celular o tile
encolhe, as 4 faixas somam bem menos que a tela e sobrava um vazio grande
embaixo. Do jeito atual bate com a referência no desktop e continua fechado em
430 × 932 (seção de 474 px, última faixa cortada).

Comportamento:

- **Sem animação automática.** As faixas deslizam na horizontal conforme a
  página rola, em sentidos alternados e com cursos diferentes — é o que lê
  como profundidade. Fora da viewport, o listener de scroll fica parado.
- **Topo e base mais escuros que o meio, em gradiente.** A primeira e a última
  faixa levam um gradiente preto por cima (`--edge-fade`), fechado na borda de
  fora e nulo na de dentro — aditivo, nada fica mais claro do que já estava. Na
  última faixa o pico é ancorado na linha de corte da seção
  (`--tile-h * 0.6 + --tile-gap`), não no fim do tile: os últimos 0.4 × tile
  ficam fora do quadro, e ancorar ali esconderia justamente a parte forte.
  O scrim da seção ficou de propósito mais leve embaixo — com os dois em força
  cheia a última faixa virava preto quase puro e a terceira saía mais escura
  que a segunda.

  `--edge-fade` está em `1` (preto pleno na ponta). Subir o alfa acima de ~0,8
  não muda quase nada: com o dim do tile e o scrim empilhados por baixo, a
  ponta já encosta no piso da cor do scrim (`rgb(4 5 7)`, luminância 5,3). Quem
  dá o resultado é o **alcance** — a parada intermediária a 50 % segura
  `0,62 × alfa` em vez dos `0,5 ×` de uma rampa reta. Luminância medida fora da
  coluna de texto, mesmas fotos nas mesmas posições:

  | | rampa reta, alfa 0,55/0,6 | alfa 1 + alcance |
  |---|---|---|
  | faixa 1 topo | 6,5 | **5,4** (piso) |
  | faixa 1 ¼ | 7,7 | 6,0 |
  | faixa 1 meio | 12,9 | 9,3 |
  | faixa 1 base | 23,4 | 23,2 (gradiente = 0) |
  | faixas 2 e 3 | 23,3 / 18,4 | inalteradas |
  | faixa 4 topo | 7,6 | 7,6 (gradiente = 0) |
  | faixa 4 meio | 9,8 | 7,9 |
  | faixa 4 corte | 10,2 | **6,1** |

  Medir com média na largura toda engana: a caixa branca do logo e o texto
  ficam em `z-index: 2`, acima do gradiente, e puxam a média para cima nas
  linhas onde aparecem.
- **Todo quadrado tem foto.** O script clona o conjunto de tiles até cobrir a
  viewport somada ao curso do deslize, então não abre fresta em nenhuma posição
  de scroll. São 20 fotos para as 20 posições — nenhuma imagem se repete na
  marcação.
- **Posições sorteadas a cada carregamento.** As 20 fotos são redistribuídas
  entre as quatro faixas por Fisher–Yates antes da montagem, então os clones já
  saem do arranjo sorteado. O arranjo fica estável durante a sessão (inclusive
  em resize) e só muda no próximo reload. `data-shuffle="false"` na seção
  desliga, para comparar screenshots.
- **Ressalva geométrica:** o passo de repetição de cada faixa é
  `5 × 323 = 1615 px`. Para nunca exibir a mesma foto duas vezes na tela seria
  preciso `viewport + largura do tile = 1740 px`. Faltam 125 px, então em cerca
  de 8 % das posições de scroll uma fatia de 27–98 px de uma foto aparece nas
  duas bordas ao mesmo tempo. Não tem a ver com o sorteio — é a conta de 5 tiles
  por faixa em 1440 px. Resolver de verdade pede **6 tiles por faixa**, ou seja
  24 fotos; com 20 o jeito seria repetir 4, o que contraria o objetivo.
- **Hover clareia o tile devagar.** A grade tonal recua de `0,44` para `0,066`
  em 900 ms na entrada e 1300 ms na saída (`--duration-ambient`). É resposta de
  atmosfera, não um controle: sem `cursor: pointer`, sem escala, sem sombra —
  nada que anuncie um clique que não existe. Só em `(hover: hover) and (pointer:
  fine)`, porque em tela de toque o `:hover` fica preso depois do tap. A grade
  tem `pointer-events: none`; os tiles voltam para `auto`, senão o hover nunca
  dispara. Nas pontas o efeito é menor de propósito: o gradiente de borda fica
  acima dos tiles e continua fechado.
- As fotos são ambiente, não informação: a grade é `aria-hidden` e todo `alt`
  fica vazio. Quem usa leitor de tela recebe só o texto.

Ajustes ficam nas variáveis do topo de `styles/sections/photo-wall.css`
(`--tile-h`, `--tile-ratio`, `--tile-gap`, `--tile-dim`) e em `ROW_TRAVEL` no
`scripts/sections/photo-wall.js`.

---

## Seção 01 — Hero

`styles/sections/hero.css`, sem JS. Estrutura na linha da referência
(samharris.org): frase no alto à esquerda, foto sangrando pela direita e
dissolvendo no fundo, fileira de produtos ancorada na base. No lugar dos players
de app, mockups de livro.

### Livros — carrossel

10 títulos, cada card com capa, título, subtítulo, nota, número de avaliações,
recorte da sinopse e botão para **a página daquele livro** na Amazon.

Dados em `assets/data/livros.json`, gerados e injetados por
`./tools/gen-books.py` (procura os marcadores `CARROSSEL:INICIO/FIM` no
`index.html`). Para editar um livro, mude a lista no script e rode de novo.

**Nota e avaliações envelhecem.** Foram capturadas em **04/08/2026** e estão
fixas no HTML; o JSON registra a data. Rode o script de novo quando quiser
atualizar. As sinopses são recortes **literais e contíguos** da descrição da
Amazon — nada reescrito.

Rolagem: `overflow-x` + `scroll-snap-type: x mandatory`. Dedo, trackpad, roda e
teclado funcionam **sem JS**; as setas são conveniência por cima disso e já vêm
no HTML, então a lista continua rolável se o módulo não carregar. O passo de um
clique é a largura do card mais o vão (301 px em 1440), e cai exatamente no
ponto de snap do card seguinte.

Acessibilidade: a capa é um link `tabindex="-1" aria-hidden="true"` — ela leva ao
mesmo lugar que o botão, e deixá-la focável duplicaria cada link na navegação por
teclado. O nome acessível do botão inclui o título ("Ver na Amazon — Amores Que
Tropeçam"), então dez botões iguais não viram dez rótulos idênticos. A barra de
estrelas é decorativa (`aria-hidden`); a nota vai em texto.

Um bug que essa seção revelou no reset: `base.css` tinha
`ul[class] { padding: 0 }`, com especificidade (0,1,1) — maior que a de uma
classe (0,1,0). O `padding-inline` do carrossel era zerado e o primeiro card
encostava na borda. Reset não pode ganhar de componente, então virou
`:where(ul[class], ol[class])`, que pesa zero.

## Seção 02 — Coluna, textos e diário

`styles/sections/escrita.css`, sem JS. Entra entre o hero e o mural. Três
colunas de índice, uma por categoria do `enricopierro.com.br`: **coluna** (108),
**textos** (235) e **diário** (189), com as seis publicações mais recentes de
cada uma e um link para o arquivo completo da categoria.

**São só título, data e link.** O texto de cada publicação fica no site onde ele
é publicado — a seção é um índice, não uma cópia. Cada linha abre o post
original em nova aba.

A estrutura reaproveita a lista da bio (linhas separadas por hairline, o padrão
"inset grouped" da Apple). O que muda é que cada linha aqui é um link, então
ganha alvo de 44 pt, hover e a seta que desliza — o mesmo gesto do CTA dos
livros. Abaixo de 460 px a data desce para baixo do título: em 320 px as três
colunas da linha brigavam e o título quebrava em quatro linhas.

Dados e totais em `assets/data/escrita.json`, capturados em **2026-08-05** via a
API pública do WordPress.com. **Os totais envelhecem** — rode
`./tools/gen-escrita.py` de novo para atualizar.

Contraste: a contagem de publicações estava em `--label-tertiary` e dava
**2,58:1** — exatamente o erro já registrado no rodapé. Corrigido para
`--label-secondary` → 7,31:1. A seta levou o mesmo tratamento: em tertiary ficava
abaixo dos 3:1 que a WCAG 1.4.11 pede para componente de interface.

## Subpágina — a escrita (`escrita.html`)

`styles/sections/escrita-arquivo.css` + `scripts/sections/esc-app.js`,
`esc-shelf.js` e `esc-leitor.js`. **A página inteira é gerada** por
`./tools/gen-escrita-arquivo.py` — editar o HTML não adianta. Com `--offline`
ele usa `tools/.cache-escrita.json` e não toca na rede.

577 textos em quatro categorias, nesta ordem: **diário** (196), **coluna**
(108), **textos** (235) e **outros** (38). O HTML traz só título e data de cada
um; o texto entra sob demanda do `assets/data/escrita-arquivo.json`.

### Casco de aplicativo

Estrutura do app do Apple Podcasts: barra lateral em vidro à esquerda com as
categorias e os períodos, e um painel que mostra **um recorte por vez** — uma
categoria, um período. As quatro categorias e os 44 períodos existem no HTML,
mas só um par fica visível.

Duas versões anteriores morreram no caminho, pelo mesmo motivo, e valem o
registro:

1. **Pílulas de categoria + cards expansíveis.** Cada publicação era um
   `<details>` com o texto dentro. Abrir uma esticava a página; abrir duas,
   mais ainda.
2. **Acordeões por período.** Melhorou o comprimento (30 071 px → 8 989 px),
   mas continuava empilhando barras no mesmo rolo, e "textos" virava uma parede
   de 24 barras fechadas.

Hoje a página abre em **2 404 px, 2,7 telas** — contra as quarenta do começo.
Nenhum dropdown nasce aberto.

A lateral é `--material-thick` com blur e vibrancy, mais um fio de luz na aresta
de cima (`inset 0 1px 0`) e sombra de contato: é o que faz o vidro parecer uma
placa sobre a página em vez de um retângulo translúcido. Abaixo de 1040 px ela
vira faixa horizontal rolável — coluna fixa comeria metade da largura de
leitura.

### Janela de leitura

`<dialog>` **único**, reaproveitado pelas 577 publicações — 577 diálogos no HTML
seriam um arquivo gigante para nada. O texto rola dentro dele, então abrir uma
publicação muda a altura da página em **exatamente 0 px** (medido).

O hash é a fonte da verdade: clicar numa linha muda para `#slug`, o que abre a
janela; fechar limpa o hash. Cada texto ganha URL própria — é o que o
compartilhamento envia — e o botão "voltar" fecha a leitura.

**Compartilhamento:** WhatsApp, X, Facebook e copiar link, mais o botão nativo
(`navigator.share`), que só aparece onde o navegador tem a API. O nativo é o
**único caminho para Instagram e Stories**: o Instagram não tem endereço de
compartilhamento na web, então não existe botão direto honesto para ele. As URLs
de share usam `location.origin` — em `localhost` elas apontam para localhost, e
passam a valer sozinhas quando o site for publicado.

### Quatro erros que essa página revelou

- **`display` de autor derrota o atributo `hidden`.** `.esc-side__list` tinha
  `display: grid`, e o `hidden` esconde via `display: none` do estilo do
  navegador — que perde de qualquer regra de autor. As quatro listas de período
  renderizavam juntas: a lateral ia a 1559 px e mostrava os períodos das quatro
  categorias. Precisa de `.esc-side__list[hidden] { display: none }` explícito.
- **Camada de luz absoluta com inset negativo = rolagem horizontal na página
  inteira.** O `.esc-app::before` transbordava 20 % de cada lado e somava 256 px
  de scroll horizontal. Por ser pseudo-elemento, não aparecia numa varredura de
  `getBoundingClientRect` nos elementos — só comparando `scrollWidth` com
  `clientWidth` e depois lendo o `left`/`right` computado dos pseudos. Resolvido
  com `position: fixed`, que não transborda por definição e cobre a largura toda
  (a caixa do pai para em 1320 px e deixaria as beiradas chapadas).
- **`overflow: clip` no pai quebra `sticky` no filho.** Foi a primeira tentativa
  de conter o vazamento acima. Qualquer `overflow` diferente de `visible` passa a
  ser o scrollport dos descendentes `sticky`, e a lateral parou de colar.
- **`sticky` precisa de trilho.** Com `align-items: start` na grade, a coluna da
  lateral encolhia para a altura do conteúdo e não sobrava curso. A coluna tem de
  esticar e o `sticky` vai no elemento de dentro (`.esc-side__inner`).

E um do CSS base que valeu para a janela: **`* { margin: 0 }` do `base.css` mata
o `margin: auto`** que o navegador usa para centralizar `dialog:modal` — a janela
ia para o canto superior esquerdo. Por isso `position: fixed; inset: 0;
margin: auto` estão declarados à mão.

### Capas e miniaturas

A capa de cada texto é a **primeira imagem do próprio post** — 514 dos 577 têm
uma —, servida pelo Photon do WordPress em várias larguras via `?w=`. Nada foi
baixado para o repositório e nenhuma imagem foi escolhida à mão. Os **63 sem
imagem** viram card tipográfico (título grande na cor de destaque) nas fileiras e
quadrado com a inicial nas linhas; nenhum ganhou foto inventada.

Contraste conferido: título da linha 19,91:1, itens da lateral 10,79:1,
contagens e datas 7,31:1. Nenhum alvo de toque abaixo de 44 pt. **Zero rolagem
horizontal** nas três páginas em 320, 375 e 1440 px, com a janela aberta e
fechada.

## Subpágina — os episódios (`episodios.html`)

`styles/sections/episodios.css`. **A página inteira é gerada** por
`./tools/gen-episodios.py` — editar o HTML não adianta.

Três blocos: cabeçalho com os números do podcast, o player do Spotify e o
arquivo de vídeo agrupado por temporada.

**São 67 episódios completos**, 101 horas, quatro temporadas mais um especial.
Cortes, shorts e clipes de divulgação ficam de fora: são 128 vídeos no canal e
transformariam a página num feed.

De onde vieram os dados:

- **YouTube** — a aba de vídeos do canal, paginada até o fim pela innertube (132
  vídeos), somada à playlist "ABCPOD"; a data de publicação e a duração exatas
  vieram da página de cada vídeo, um a um.
- **Spotify** — a lista de episódios **não é acessível sem credenciais de API**
  (a página do show e o `get_access_token` respondem 403). Por isso a coluna de
  áudio é o player embed oficial do show, que já traz todos os episódios e se
  atualiza sozinho. **Nenhum episódio de Spotify foi inventado.**

### Mosaico do cabeçalho

À direita do título, uma parede inclinada com as **20 fotos do mural**
(`assets/img/wall`) — as mesmas do abcpod —, no espírito das páginas de catálogo
da Apple. Decorativo: `aria-hidden` na `<figure>` e todo `alt` vazio, como no
mural. Sem JS e sem animação.

**Escalonamento de meia foto.** Cada coluna sobe metade de uma foto em relação à
anterior, em escada, então o **meio** de cada foto cai na **junção** das duas da
coluna vizinha — nunca uma grade alinhada. A conta é em porcentagem da altura da
coluna (`translate` no eixo Y resolve sobre a altura do próprio elemento):
8 linhas → uma foto é 12,5 %, meia foto é 6,25 %, e as colunas ficam em
0 / −6,25 / −12,5 / −18,75 / −25 %. Fica ~0,4 % fora do meio exato porque a folga
entra na altura; medido, o passo deu 78,2 px contra 79 ideais. Em troca continua
certo em qualquer tela, sem pixel fixo.

**5 colunas de 8.** Cinco porque a caixa é larga (a diagonal precisa de curso):
com 4 as fotos cresciam junto com a caixa e ficavam grandes demais para ler como
parede. Oito linhas porque, com o escalonamento, a última coluna sobe 2 fotos —
com 5 por coluna o pé dela entrava no quadro. São 40 posições para 20 fotos,
então 20 repetem; a distribuição é calculada para que **nenhuma foto encoste
nela mesma**, nem na vertical nem na horizontal, e um `assert` no gerador quebra
se alguém mudar as contagens e furar isso.

### A divisão em duas metades — o erro que custou três tentativas

O sintoma: uma linha vertical nítida no meio da seção, com fotos de um lado e
nada do outro. Duas causas somadas, e nenhuma delas era o gradiente estar fraco:

1. **`0,98` de preto não é `1`.** O mosaico é uma caixa que começa a ~32 % da
   tela. Com só o gradiente por cima, na borda esquerda dela a foto ficava em
   0,98 — e os 2 % restantes, mais a borda de 1 px de cada tile
   (`--separator-opaque`), desenhavam a linha.
2. **`--bg-scrim` ≠ `--bg-base`.** Fechar em alfa 1 não resolvia: o scrim é
   `rgb(4 5 7)` e o fundo da página é `#08090c` = `rgb(8 9 12)`. **Cores
   diferentes.** O bloco "opaco" ficava mais escuro que a página, virava um
   retângulo visível e ainda tapava o brilho (`.ep-hero::before`) por baixo.

3. **A borda do tile desenhava a grade.** Cada foto tinha
   `border: 1px solid var(--separator-opaque)` (#38383a) e
   `background-color: var(--bg-elevated)` (#121419). São 40 fotos, quase todas
   em `loading="lazy"`: enquanto não carregam — e na zona onde a máscara está
   parcial — cada uma aparecia como um retângulo contornado, e o conjunto lia
   como riscos de divisória. A foto preenche o tile inteiro por `cover`, então a
   moldura não acrescentava nada além do artefato. **Removidas as duas**; o vão
   entre as fotos já dá a separação.

A correção é de divisão de trabalho, não de valores:

- **Apagar é da máscara.** Onde ela vai a zero o elemento não pinta nada, e
  passa o fundo real com o brilho e tudo — não existe emenda possível.
- **Gradar é do gradiente.** O `::after` só escurece progressivamente, no
  **mesmo eixo diagonal** (`--mosaic-eixo: 68deg`), para as fotos irem surgindo
  do mais escuro para o mais claro. Não precisa fechar em opaco.

**Uma camada de máscara só.** Tentei duas cruzadas por
`mask-composite: intersect` — a diagonal e o fecho da base — e não serve: o
`-webkit-mask-composite` legado sobrescreve o padrão, o computado sai
`source-in, source-in` e a interseção não acontece de forma confiável. O vinco
voltava. O fecho da base foi para o `::after`, que não depende de compositing
nenhum, e a máscara ficou com a diagonal sozinha.

Houve ainda uma tentativa errada antes dessas: máscara no `.ep-mosaic__plane`.
Como o plano transborda 16 % de cada lado e é rotacionado, o gradiente ficava
totalmente opaco justamente onde a caixa corta. A máscara tem de ir na **caixa**,
onde as porcentagens são as da área visível.

### Geometria

A caixa é `clamp(34rem, 68vw, 82rem)` — bem mais larga que a área onde as fotos
aparecem, porque os primeiros 2–44 % estão em máscara quase zero. Ela avança por
baixo do texto sem que exista borda, e é isso que apaga a divisão. Travada num
rem (`min(54%, 48rem)`) ela parava de crescer em tela larga enquanto a folga do
texto continuava, e abria um vazio de ~250 px entre os dois.

O mosaico fica **fora do `.container`**. Dentro dele a camada absoluta ficava
presa à caixa do texto (o container já é `position: relative`): não pegava a
altura cheia do cabeçalho nem sangrava até a borda da tela. Como irmão, entra em
`z-index: 0` e o cabeçalho que já existia não precisou de mudança de layout
nenhuma — só da folga à direita (47 %).

A faixa escura no alto do mosaico não é decoração: a barra de navegação só ganha
material depois que a página rola, e sobre as fotos claras os links do menu
perdiam contraste.

**Legibilidade do texto sobre o mosaico.** O texto avança sobre a zona onde as
fotos começam a surgir, então a conta que importa é quanto de foto aparece atrás
dele — máscara × (1 − escurecimento), medido no pior canto de cada bloco:

| | foto visível atrás |
|---|---|
| título (48 px, bold, branco) | 23 % |
| linha de apoio | 13 % |
| números | 11 % |
| botões | 6 % |

Abaixo de 1040 px o mosaico deixa de ser camada e entra como **faixa sangrada
depois dos botões** — mesmo recurso do retrato da bio no compacto. O cabeçalho
acima dela não muda em nada.

### Outras decisões

- **As capas dos cards vêm do CDN do YouTube (`i.ytimg.com`), não do
  `assets/`.** São 67
  imagens que mudam quando o canal muda de capa; baixá-las colocaria uma cópia
  velha no repositório. Todas em `loading="lazy"`, com `width`/`height` e
  `aspect-ratio` para não haver salto de layout. `mqdefault` e `hq720` foram
  verificadas nos 67 vídeos — as duas existem em todos.
- **As visualizações são capturadas mas não exibidas.** Número de views num site
  de autor não informa nada ao leitor e envelhece rápido. Ficam no JSON para
  registro.
- **Dentro da temporada, o mais recente primeiro.** Quem chega na página quer o
  último episódio, não o primeiro de 2023.
- **O nome acessível do card não repete o que já está visível.** A primeira
  versão duplicava rótulo, nome e data num `.visually-hidden`, e o leitor de tela
  anunciava o card duas vezes — o nome acessível de um link é a soma de todo o
  conteúdo dele. Agora o texto oculto só acrescenta o que falta: a duração falada
  e o destino. O selo de duração é `aria-hidden` por ser redundante com ela.
- **A barra de temporadas fica presa no alto** (`position: sticky`) porque numa
  página de 67 cards voltar ao topo só para trocar de temporada é ida e volta
  desnecessária. Cada `.ep-season` leva `scroll-margin-top` — o `scroll-padding`
  do `html` só desconta o cabeçalho, não a barra de pílulas.
- **Grade tonal por cima das capas**, como nos tiles do mural, recuando no hover.
  As capas do YouTube têm cores e brilhos muito diferentes entre si; sem isso a
  grade de 67 cards fica um mosaico agitado.
- Mesma armadilha do retrato da bio: o `.ep-card__thumb img` precisa de
  `height: auto`, senão o `height="180"` do HTML vence o `aspect-ratio`.

**A numeração da 4ª temporada tem lacunas** (pula E19–E23 e E26–E31): esses
episódios não estão públicos no canal. O que está na página é o que existe lá.

## Seção 03 — Quem é o Enrico Pierro

`styles/sections/bio.css`, sem JS. Retrato 4:5 numa coluna de 33 %, texto na
outra; empilha abaixo de 900 px. As duas listas de reconhecimentos ficam **fora**
das duas colunas, na largura toda — presas na coluna de texto, sobrava um vazio
grande sob o retrato e cada lista ficava em 347 px.

Duas decisões que valem registro:

- **O texto da biografia está em minúsculas de propósito.** É a assinatura
  literária do Enrico, e o próprio texto explica isso. Mantido exatamente como
  recebido. Só os títulos de seção, os nomes dos prêmios e os nomes próprios das
  antologias seguem a capitalização normal. Se quiser minúsculas em tudo, é
  trocar no HTML — o CSS não força caixa em nenhum dos dois.
- **Entrelinha 1.6 no corpo, não os 22/17 pt do HIG.** Aquela medida é para
  rótulo curto de interface; em quatro parágrafos seguidos ela fecha demais.
  O tamanho e o tracking seguem o estilo Body do HIG.

O retrato precisa de `height: auto` no CSS. O atributo `height="960"` do HTML
entra como *presentational hint*; sobrescrevendo só a largura, as duas dimensões
ficam definidas, o `aspect-ratio` é ignorado e a foto sai 409 × 960 em vez de
409 × 511.

## Rodapé

Identificação, navegação, fileira de redes e uma barra inferior. Os ícones de
rede são só o símbolo; o nome de cada uma vai em `.visually-hidden`, senão o
rodapé vira uma lista de rótulos. Alvo de 44 pt como qualquer outro link.

Contraste verificado depois de um erro meu: os títulos de coluna e a barra
inferior estavam em `--label-tertiary` e davam **2,59:1**, abaixo do mínimo de
4,5:1. No HIG o `tertiaryLabel` é para placeholder e desabilitado, não para
conteúdo. Corrigido para `--label-secondary` → 7,33:1.

## Links externos

Todos conferidos contra o rodapé e as páginas do `enricopierro.com.br` em
**2026-08-05**. Nenhum é genérico e nenhum foi inventado:

| destino | URL |
|---|---|
| Amazon (loja do autor) | `amazon.com.br/stores/author/B0DVQCC67C` |
| YouTube | `youtube.com/@abcPod` |
| Spotify | `open.spotify.com/show/65VR3AdKUStYuN5U55ymKt` |
| Instagram | `instagram.com/enricopierroofc/` |
| Facebook | `facebook.com/enricopierroofc` |
| Blog | `enricopierro.com.br` |

Os dez botões do carrossel continuam apontando para a **página de cada livro**
(`/dp/ASIN`), não para a loja — é o link específico que interessa ali.

Antes, o hero levava para `youtube.com` e `open.spotify.com` na raiz, e a Amazon
para uma busca por nome. Os três viraram os endereços reais.

---

## Apple HIG — o que foi aplicado

| Diretriz | Onde |
|---|---|
| Tipografia San Francisco | `--font-text` / `--font-display` / `--font-mono` |
| Escala de estilos de texto (Large Title → Caption 2) | `tokens.css`, com o tracking oficial convertido de pt para `em` |
| Dynamic Type | tudo em `rem`; display fluido com `clamp()` |
| Cores semânticas | `--label-*`, `--fill-*`, `--separator`, nas opacidades do HIG para aparência escura |
| Evitar preto puro | `--bg-base: #08090c` |
| Grade de 8 pt | `--space-1` … `--space-12` |
| Alvo de toque de 44 pt | `--tap-min`, aplicado em botões e itens de navegação |
| Áreas seguras | `env(safe-area-inset-*)` + `viewport-fit=cover` |
| Materiais e vibrancy | `.material`, `.btn--glass`, cabeçalho ao rolar |
| Cantos contínuos | `corner-shape: squircle` sob `@supports` |
| Indicador de foco | outline de 3 px na cor de destaque, nunca removido |
| Movimento com propósito | deriva ligada ao scroll, não autônoma; `prefers-reduced-motion` |
| Acessibilidade | `prefers-reduced-transparency`, `prefers-contrast: more` |
| Estados completos | botão com hover, focus, active, disabled e loading |

Contraste verificado: texto do mural ≥ 11:1; cor de destaque sobre o fundo
≈ 15,9:1; texto escuro sobre a cor de destaque ≈ 16:1.

---

## A confirmar antes de publicar

O que ainda é **provisório** e existe só para ocupar o lugar certo:

- **Texto do mural** — o `Logo`/`Subtítulo da marca` dentro de `.wall-brand` e as
  três linhas de `.photo-wall__tagline`. É o último bloco de texto de exemplo que
  restou na home.
- **Cor de destaque** — `--accent` em `tokens.css`. Está num amarelo amostrado
  das fotos do estúdio; é uma linha para trocar, nenhum componente usa o valor
  direto.
- **`<meta name="robots" content="noindex">`** nas duas páginas. Remover quando
  for publicar de verdade.

Dados que **envelhecem** e pedem uma rodada dos geradores:

- nota e nº de avaliações dos livros (capturados em 2026-08-04);
- totais das três categorias de escrita (2026-08-05);
- a lista de episódios, quando sair um novo (2026-08-05).

Nada de números, depoimentos ou logotipos de terceiros foi inventado.
