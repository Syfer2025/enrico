# Site do Enrico Pierro — como esta pasta está organizada

Três pastas, com uma regra só: **o que vai para o ar mora em `publicar/`. O resto, não.**

Antes tudo ficava misturado numa pasta de 350 MB — o site junto com backups,
instaladores do Unity e do AnyDesk, imagens soltas e o logo de outra empresa.
Qualquer publicação subia isso tudo.

---

## `publicar/` — **79 MB**

É o site. Quando for para o ar, sobe **só esta pasta**, e o conteúdo dela vira a
raiz do domínio (`index.html` na raiz, não dentro de `publicar/`).

```
publicar/
├── index.html          página inicial
├── escrita.html        os 577 textos
├── episodios.html      os 67 episódios do ABCPOD
├── assets/
│   ├── data/           gerados a partir de conteudo/
│   │   ├── textos/     um arquivo por texto (577) — o leitor busca só o que abrem
│   │   ├── livros.json  episodios.json  escrita.json
│   ├── img/            todas as imagens, inclusive as 1.719 do acervo
│   │   └── acervo/capas/  as larguras responsivas das capas dos textos
└── admin/              o painel
├── scripts/            o javascript
└── styles/             o css
```

Não há nada aqui que não precise ser servido. Nenhuma imagem vem de fora.

### O painel

Fica em `publicar/admin/`. É o Sveltia CMS: um CMS que roda inteiro no navegador
e grava direto no repositório, sem servidor e sem banco — por isso não tem
mensalidade.

Para abrir aqui na máquina, **no Chrome, Edge ou Brave** (o modo local usa uma
API que não existe no Safari nem no Firefox):

```bash
python3 ferramentas/dev-server.py 4322
open -a "Google Chrome" http://localhost:4322/admin/
```

Clique em **"Trabalhar com Repositório Local"** e escolha a pasta do projeto.

Seis abas, organizadas pelo que o Enrico faz: Diário, Coluna, Textos, Outros,
Livros e Episódios.

**As frases fixas da página inicial não estão no painel**, de propósito — veja
[A página inicial não se edita no painel](#a-página-inicial-não-se-edita-no-painel).

#### `admin/teste.html` — o painel sem login, para conferir mexidas na tela

```bash
open -a "Google Chrome" http://localhost:4322/admin/teste.html
```

Um clique em "Trabalhar com Repositório de Teste" e o painel abre: sem conta, sem
senha, sem escolher pasta, sem tocar em repositório nenhum — o `test-repo` é um
repositório de mentira que vive só na memória do navegador. Dá para criar uma
entrada, ver o formulário inteiro e conferir a tela.

**É por isso que ele existe.** Três mexidas seguidas no painel — a caixa de texto
centralizada, os "?" de ajuda, a prévia do enquadramento — foram entregues como
prontas e não funcionavam. Todas pelo mesmo motivo: o seletor de CSS ou de
JavaScript era suposto, e o teste era feito numa página montada em volta da
suposição. Duas regras nunca valeram para elemento nenhum:

| escrito por suposição | o que existe de verdade |
| --- | --- |
| `[role="document"] > section[data-field-type]` | `[role="group"][data-mode] section[data-field-type]` |
| `select` (o campo de enquadramento) | `div[role="combobox"]`, sem `<select>` na tela |
| `.component.block` | `.component.inline.wrapper` |
| `.preview.tile` | `span.preview` |

Antes de mexer em `tema-enrico.css`, `ajuda.js` ou `previa-capa.js`: abra o
teste.html e confira no console que o seletor casa com algo.

```js
document.querySelectorAll('SEU_SELETOR').length   // zero = a regra não vale
```

O `config-teste-backend.yml` tem só três linhas, o backend. O `teste.html`
carrega os DOIS arquivos — o `config.yml` de verdade e depois esse — então o
formulário testado é exatamente o de produção, sem cópia para envelhecer.

### Como o Enrico entra

Pela **conta do GitHub dele** — que na prática é e-mail e senha, digitados na tela
do GitHub. Ele clica em "Entrar com GitHub", entra, autoriza uma vez, e o
navegador o mantém conectado por meses.

**Não existe como ter uma tela de senha nossa usando só GitHub.** Conferir senha
exige código rodando num servidor: o Pages é estático e o Actions não atende
requisição. O painel também recusa o login direto pelo navegador
(`auth_type: pkce`) quando o backend é GitHub — a mensagem `github_pkce_unsupported`
está no pacote dele. Para GitLab e Gitea funcionaria; para GitHub, não.

O que isso custa ao Enrico: o GitHub exige verificação em duas etapas, então ele
precisa de um app autenticador no celular. Em troca, o projeto não depende de
nenhum serviço além do GitHub.

**Os avisos do painel estão desligados** para ele (`publicar/admin/entrada.js`):
status de serviço, versão nova, propaganda de celular e novo idioma. Erro do que
ELE faz continua aparecendo — esconder isso faria ele achar que publicou sem ter
publicado. No `admin/teste.html` os avisos ficam visíveis, para quem cuida do site.

## `conteudo/` — o que o painel edita

```
conteudo/
├── textos/<slug>.md      577 — cabeçalho com título, data, categoria e capa + o texto
├── livros/<slug>.md       10
├── episodios/t01e01.md    67
└── secoes.json             1 — os textos da página inicial
```

Antes isto tudo era código: os livros e os episódios eram listas em Python
dentro dos geradores, e os textos da home estavam escritos no `index.html`.
Mudar a nota de um livro exigia programar.

### A página inicial não se edita no painel

O topo do site, a chamada do abcpod, a biografia e as listas de prêmios ficam em
`conteudo/secoes.json`, e se editam **no arquivo**. Não há aba para eles.

Isso é escolha, não esquecimento. Essas frases mudam uma vez por ano, pedem
cuidado com a marcação, e não são o trabalho de quem escreve — o painel do Enrico
tem só o que ele faz toda semana. O formulário que existia ali tinha quatro
blocos e dezoito campos, e o nome dele ("Textos da página inicial") parecia um
segundo lugar para gerenciar textos, concorrendo com as abas Diário, Coluna e
Textos.

A marcação é a de `ferramentas/marcacao.py` — sem HTML:

```
*obra*             título de livro, sai em itálico
**destaque**       negrito
[texto](destino)   link
```

Depois de mexer:

```bash
python3 ferramentas/gen-secoes.py
```

O `ferramentas/varrer.py` confere esse arquivo a cada publicação: acusa HTML cru
e texto de exemplo esquecido lá dentro.

**Os últimos textos da home nunca tiveram campo**, nem no painel nem no
`secoes.json`: entram sozinhos, o último de cada categoria, por data. Quem
escreve mexe em Diário, Coluna e Textos, e a home se atualiza na publicação
seguinte.

### A capa é um campo, não "a primeira foto do texto"

No cabeçalho de cada texto há `capa:`, e é dela que sai a foto da lista, do
cartão e do alto da leitura. O campo tem upload próprio no painel. Fotos DENTRO
do texto são outra coisa, e entram pelo botão de imagem do editor.

Não era assim. A capa era descoberta na hora de gerar — "a primeira imagem do
corpo" —, então a foto ficava escrita dentro do texto e o campo do painel era
enfeite: trocar a capa lá não trocava nada no site. Pior, 282 textos tinham
`capa:` apontando para `acervo/capas/<slug>-320.webp`, que é a MINIATURA que o
`gerar-capas.py` cria. Como cartãozinho passava; no alto da leitura sairia
borrada, e nunca daria para gerar uma versão maior a partir dela.

O `separar-capas.py` desfez o nó, e a conferência foi feita contra a saída
anterior: nos 577 textos, **texto, fotos e parágrafos idênticos**. Em 21 deles a
foto da capa estava no MEIO do texto (num, no bloco 22 de 24) — essas voltaram
para o lugar em que o Enrico as pôs, e nesses casos o alto da leitura não
repete a foto.

**Depois de editar, é preciso gerar** — o painel grava o conteúdo, mas quem
escreve o HTML são os geradores. Rodar os cinco, nesta ordem, refaz o site
inteiro:

```bash
python3 ferramentas/gen-books.py           # livros
python3 ferramentas/gen-episodios.py       # episódios
python3 ferramentas/gen-secoes.py          # textos da home
python3 ferramentas/gen-escrita-arquivo.py # os 577 textos + a subpágina
python3 ferramentas/gen-escrita.py         # a fileira de textos da home
```

Os cinco são idempotentes: rodar duas vezes seguidas não muda um byte.

**Texto novo com imagem** precisa de dois passos a mais, porque a imagem chega
grande e o site serve versões por tamanho:

```bash
python3 ferramentas/gerar-capas.py          # as larguras da capa
python3 ferramentas/gen-escrita-arquivo.py  # e regera a página
```

**Rascunho:** um texto com `publicado: false` some da listagem e o arquivo dele
nem chega a ser escrito — não existe endereço onde alguém possa achá-lo.

## `bastidores/` — o que gera o site mas não é publicado

```
bastidores/
├── acervo-completo.json   como os 577 textos vieram do WordPress (histórico)
├── originais/             os PNG originais das fotos (49 MB) que geram os webp
├── imagens-ia/            imagens geradas por IA durante o projeto
├── acervo-mapa.json       cada url antiga → o arquivo local que a substituiu
├── acervo-falhas.json     as 16 imagens que não existem mais em lugar nenhum
└── documentacao/          o README do projeto
```

O `acervo-completo.json` **não é mais a fonte de verdade** — quem manda hoje é
`conteudo/textos/`, que é o que o painel edita. Ele fica guardado como registro
de como os textos chegaram do WordPress na importação de 05/08/2026.

## `ferramentas/` — os geradores

Rodam sempre a partir da raiz do projeto (esta pasta), não de dentro delas:

```bash
python3 ferramentas/dev-server.py 4322
```

| ferramenta | o que faz |
| --- | --- |
| `dev-server.py` | servidor local, serve **só** `publicar/` — igual ao que vai para o ar |
| `conteudo.py` | lê os arquivos de `conteudo/`; os geradores importam daqui |
| `gen-books.py` | monta o carrossel de livros a partir de `conteudo/livros/` |
| `gen-episodios.py` | monta a página de episódios a partir de `conteudo/episodios/` |
| `gen-secoes.py` | escreve os textos da home a partir de `conteudo/secoes.json` |
| `gen-escrita-arquivo.py` | gera `escrita.html` e os 577 arquivos do leitor |
| `gen-escrita.py` | monta a fileira de textos da home |
| `gerar-capas.py` | cria as larguras responsivas das capas dos textos |
| `ligar-capas.py` | criou o campo `capa` (rodou uma vez; **não rode mais** — o modelo mudou, veja o cabeçalho do arquivo) |
| `varrer.py` | **varredura geral**: arquivo inexistente, capa derivada, HTML cru em campo do painel, campo vazio, texto de exemplo, caminho absoluto, dependência do site antigo |
| `conferir-painel.py` | procura no `config.yml` os erros de YAML que impedem o painel de abrir |
| `marcacao.py` | a marcação simples dos textos da home (`*obra*`, `**negrito**`, `[texto](link)`) nos dois sentidos |
| `separar-capas.py` | fez da capa um campo de verdade (rodou uma vez) |
| `conferir-html.py` | compara duas versões de uma página ignorando espaçamento |
| `montar-conteudo.py` | montou `conteudo/` a partir das fontes antigas (rodou uma vez; hoje só com `--forcar`, porque sobrescreve o que o painel editou) |
| `extrair-secoes.py` | tirou os textos da home de dentro do HTML (rodou uma vez) |
| `build-images.sh` | gera os webp a partir de `bastidores/originais/` |
| `baixar-acervo.py` | baixa as imagens que estiverem em servidor de terceiro |
| `reescrever-acervo.py` | troca no HTML os endereços externos pelos arquivos locais |
| `quebrar-acervo.py` | parte o acervo num arquivo por texto |

**Regra importante:** `episodios.html` e `escrita.html` são geradas por
inteiro. Editar essas duas à mão não adianta — a próxima geração apaga. Já
aconteceu uma vez, com as redes sociais do rodapé. Mexa no gerador.

As três de baixar/reescrever/quebrar foram escritas para tirar o site da
dependência do blog antigo. Se entrarem textos novos com imagem hospedada fora,
é rodar na ordem: baixar → reescrever.

---

## Segurança — o repositório é público, o site não é vulnerável

As duas coisas são independentes, e vale entender por quê.

### Por que ver os arquivos não ajuda um atacante

O site é **estático**: só HTML, CSS, imagens e um pouco de JavaScript que roda
no navegador de quem visita. Não existe banco de dados, não existe programa
rodando num servidor, não existe login de visitante.

A maior parte dos ataques a sites precisa de alguma dessas coisas para existir:

| ataque comum | por que não se aplica aqui |
| --- | --- |
| Injeção de SQL | não há banco de dados |
| Execução de código no servidor | não há código rodando no servidor |
| Roubo de senha de usuário | visitante não tem conta nem faz login |
| Invasão por painel de administração | o painel não fica no servidor; é o GitHub que autentica |
| Upload malicioso | não há formulário que receba arquivo |

Um atacante que leia **todo** o código descobre exatamente o que qualquer pessoa
já vê olhando a página. Não há lógica escondida, endereço secreto nem senha
enterrada no meio dos arquivos — e é por isso que ler tudo não o aproxima de
nada. Esconder o código como forma de proteção só funciona enquanto ninguém
olha, o que não é proteção.

### Onde o risco realmente está

Num site assim, há **um** ponto sensível: quem tem permissão de escrever no
repositório. Quem tem essa permissão muda o site. Ela vale mais que todo o
resto junto.

Então a segurança do projeto se resume a três hábitos:

1. **Ligar a verificação em duas etapas** na conta do GitHub. É a fechadura.
2. **Nunca salvar o token em arquivo.** Ele se usa colando no painel, no
   navegador. Não precisa existir em lugar nenhum do disco. Se desconfiar que
   vazou, revogue no GitHub e gere outro — leva um minuto e invalida o antigo.
3. **Só dar acesso de escrita a quem precisa.** Hoje: você e o Enrico.

Antes de subir qualquer coisa, dá para conferir:

```bash
python3 ferramentas/conferir-segredos.py
```

Ele procura o **formato** das credenciais dentro dos arquivos (token do GitHub,
chave privada, senha embutida em endereço de banco). A checagem é por conteúdo,
e não por nome de arquivo, de propósito: bloquear tudo que tenha "senha" ou
"secret" no nome derrubaria textos do próprio Enrico — existe um chamado
"secret-place" — e conteúdo sumindo em silêncio é pior que o risco evitado.

### O código do painel é servido daqui, não de um CDN

A instalação padrão do Sveltia carrega o script de um endereço sem versão, que
entrega sempre a mais recente. Só que esse script roda numa página que carrega a
credencial de escrita: se o pacote fosse adulterado lá fora, o painel passaria a
rodar outro código com esse poder — sem nada ter mudado aqui dentro e sem
ninguém perceber.

Por isso o arquivo mora em `publicar/admin/vendor/`, com versão e impressão
digital anotadas no `admin/index.html`. O que roda é o que foi revisado e
commitado. Para atualizar:

```bash
python3 ferramentas/atualizar-painel.py
```

### O que ainda falta cuidar

- A rotina do GitHub Actions (ainda não escrita) precisa nascer com permissão
  mínima — só escrever no site publicado, nada além disso.
- O endereço `/admin` fica acessível para qualquer pessoa. Isso é normal e não é
  brecha: sem credencial do GitHub, a página não faz nada além de mostrar a tela
  de entrada. Ela já está marcada para não aparecer em buscas.

---

## O que ficou para trás

A pasta antiga (`Desktop/fotos enrico`) **continua intacta** — nada foi apagado.
Depois de conferir que este site funciona, ela pode ser apagada. O que havia lá
e não veio para cá, de propósito:

- `UnityHubSetup-arm64.dmg` (198 MB) e `anydesk.dmg` (26 MB) — instaladores
- `G3_Auto_Pecas_vetorizada.svg` — logo de outra empresa
- `.backup-abc/`, `.backup-bio/`, `.backup-carousel/`, `.backup-ep-polish/`,
  `.backup-footer/` — versões antigas das páginas
- `tmp/`, `output/`, `.DS_Store`

## Trazer textos novos do WordPress

Enquanto o Enrico ainda publicar lá, dá para puxar o que for novo:

```bash
python3 ferramentas/gen-escrita-arquivo.py --importar
python3 ferramentas/baixar-acervo.py       # traz as imagens dos textos novos
python3 ferramentas/reescrever-acervo.py   # e troca os endereços por locais
python3 ferramentas/gerar-capas.py
python3 ferramentas/gen-escrita-arquivo.py
```

O `--importar` só ACRESCENTA: texto que já está em `conteudo/` não é tocado,
então o que foi escrito ou corrigido no painel nunca é sobrescrito.

## O que ainda falta

A lista que estava aqui envelheceu: dava como pendente a página de contato, o
sitemap, o robots.txt, o canonical, o Open Graph, o favicon e a ordem de tabulação
do menu no celular — todos feitos. Lista de pendências errada é pior que nenhuma,
porque some com as que faltam de verdade.

### Depende do Enrico — eu não tenho como fazer

1. **Subir para o GitHub.** O repositório `Syfer2025/enrico` está vazio: 0 commits,
   e aqui são 4.315 arquivos. Precisa da credencial dele, e de ligar o Pages em
   "GitHub Actions" nas configurações do repositório.
2. **Decidir o que acontece com o enricopierro.com.br**, que segue no ar com os
   mesmos 577 textos. Enquanto os dois existirem, disputam o mesmo lugar no
   Google — é por isso que o site ainda sai com `noindex`. Depois da decisão:
   mudar `dominio` em `conteudo/site.json`, pôr `no_ar: true` e rodar
   `gen-publicacao.py`.
3. **O texto de verdade da seção do abcpod.** Hoje está "abcpod" / "O PODCAST" —
   funciona, mas é genérico. Fica em `conteudo/secoes.json`.
4. **Comprovar o que o site afirma:** "mais de 40 jornais e portais" e a lista de
   prêmios e antologias. Se algum número não confere, o risco é dele.
5. **Telefone**, se ele quiser um na página de contato (`telefone_contato` está
   vazio; sem ele a página mostra só o e-mail, o que é uma escolha válida).

### Decisões de produto que ninguém tomou ainda

6. **Endereço próprio por texto.** Hoje cada texto é `escrita.html#slug`. Serve
   para compartilhar, e os 577 redirecionamentos do site antigo apontam para lá
   com `canonical`. Mas para o Google é UMA página com 577 textos dentro: o
   `sitemap.xml` tem 4 endereços, não 581. Indexar texto por texto exige uma
   página por texto — é a maior tarefa que sobrou.
7. **Newsletter.** Não existe. Um autor sem lista de e-mails depende de rede
   social para reencontrar o leitor.
8. **Medição de audiência.** Nenhuma. Decisão dele, inclusive por privacidade —
   e, se for feita, tem de ser sem trazer serviço de terceiro para o projeto.
9. **Ação principal no topo.** O hero oferece Amazon, YouTube e Spotify. Não
   oferece "ler agora" nem "receber os textos".

### O que está verde

`varrer.py`, `auditar.py`, `conferir-painel.py` e `conferir-segredos.py` passam
sem erro. As quatro rodam a cada publicação, junto com os oito geradores.
