import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const worker = (await import(join(AQUI, "worker.js"))).default;

function bancoDeMentira() {
  const db = new DatabaseSync(":memory:");
  db.exec(readFileSync(join(AQUI, "schema.sql"), "utf8"));
  return {
    prepare(sql) {
      const stmt = db.prepare(sql);
      const comArgs = (args) => ({
        async run() {
          const r = stmt.run(...args);
          return { meta: { changes: Number(r.changes) } };
        },
        async first() {
          return stmt.get(...args) ?? null;
        },
        async all() {
          return { results: stmt.all(...args) };
        },
      });
      return { bind: (...args) => comArgs(args), ...comArgs([]) };
    },
  };
}

const enviados = [];
const TEXTO = {
  slug: "dia-193-365",
  titulo: "dia 193/365.",
  data: "2026-08-05",
  categoria: "diário",
  conteudo:
    '<figure class="esc-item__media"><img src="assets/img/acervo/dia-193.webp" alt="" ' +
    'loading="lazy" decoding="async"></figure><p>o dia foi longo.</p>',
};

globalThis.fetch = async (url, opcoes = {}) => {
  const endereco = String(url);

  if (endereco.includes("/assets/data/textos/")) {
    if (!endereco.includes(TEXTO.slug)) return new Response("", { status: 404 });
    return new Response(JSON.stringify(TEXTO), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }

  if (endereco.includes("api.resend.com")) {
    enviados.push(JSON.parse(opcoes.body));
    return new Response(JSON.stringify({ id: "fingido" }), { status: 200 });
  }
  throw new Error(`o teste não esperava uma chamada a ${endereco}`);
};

const env = {
  DB: bancoDeMentira(),
  SITE: "https://enricopierro.com.br",
  ENDPOINT: "https://newsletter.enricopierro.com.br",
  REMETENTE: "enrico pierro <textos@enricopierro.com.br>",
  CHAVE_ENVIO: "chave-de-teste",
  SEGREDO_ENVIO: "segredo-de-teste",
  ORIGENS: "https://enricopierro.com.br",
  SAL: "sal-de-teste",
};

let redeAtual = "198.51.100.1";

const pedir = (caminho, opcoes = {}) =>
  worker.fetch(
    new Request(`https://newsletter.enricopierro.com.br${caminho}`, {
      ...opcoes,
      headers: { "cf-connecting-ip": redeAtual, ...(opcoes.headers || {}) },
    }),
    env,
  );

const comoJson = (corpo, extra = {}) => ({
  method: "POST",
  headers: { "content-type": "application/json", origin: env.ORIGENS, ...extra },
  body: JSON.stringify(corpo),
});

const linkDoUltimoEmail = (rota) => {
  const html = enviados.at(-1).html;
  const achado = new RegExp(`${env.ENDPOINT}/${rota}\\?t=([a-f0-9]+)`).exec(html);
  assert.ok(achado, `o último e-mail não traz link de /${rota}`);
  return achado[1];
};

let passos = 0;
const passo = (nome) => {
  passos += 1;
  console.log(`  ok  ${nome}`);
};

console.log("\nnewsletter — o percurso inteiro, sem rede e sem Cloudflare\n");

let r = await pedir("/inscrever", comoJson({ email: "não é e-mail" }));
assert.equal(r.status, 400);
assert.equal((await r.json()).estado, "email-invalido");
assert.equal(enviados.length, 0);
passo("endereço incompleto é recusado antes de qualquer envio");

r = await pedir("/inscrever", comoJson({ email: "robo@exemplo.com", site: "spam" }));
assert.equal((await r.json()).estado, "confirme");
assert.equal(enviados.length, 0, "a isca não pode gerar e-mail");
passo("robô que preenche a isca recebe sucesso e nada é enviado");

r = await pedir("/inscrever", comoJson({ email: " Leitor@Exemplo.COM ", origem: "/index.html" }));
assert.equal((await r.json()).estado, "confirme");
assert.equal(enviados.length, 1);
assert.equal(enviados[0].to[0], "leitor@exemplo.com", "o endereço é normalizado");
assert.match(enviados[0].subject, /confirme/);
passo("inscrição grava normalizada e manda o pedido de confirmação");

assert.equal(r.headers.get("access-control-allow-origin"), env.ORIGENS);
const forasteiro = await pedir(
  "/inscrever",
  comoJson({ email: "outro@exemplo.com" }, { origin: "https://site-de-terceiro.com" }),
);
assert.equal(forasteiro.headers.get("access-control-allow-origin"), null);
passo("CORS libera a origem do site e ignora as outras");

r = await pedir("/estado", { headers: { authorization: `Bearer ${env.SEGREDO_ENVIO}` } });
let contas = await r.json();
assert.equal(contas.confirmados, 0);
assert.equal(contas.pendentes, 2, "os dois pendentes: leitor@ e outro@");
passo("quem não confirmou fica pendente, fora da lista");

r = await pedir("/confirmar?t=" + "0".repeat(64));
assert.ok(r.headers.get("location").endsWith("newsletter-link-invalido.html"));
passo("token inventado cai na página de link inválido");

const tokenConfirmar = (() => {
  const html = enviados[0].html;
  return /\/confirmar\?t=([a-f0-9]+)/.exec(html)[1];
})();
r = await pedir(`/confirmar?t=${tokenConfirmar}`);
assert.ok(r.headers.get("location").endsWith("newsletter-confirmado.html"));
passo("o clique no e-mail confirma e leva à página de pronto");

r = await pedir(`/confirmar?t=${tokenConfirmar}`);
assert.ok(r.headers.get("location").endsWith("newsletter-link-invalido.html"));
passo("link de confirmação serve uma única vez");

enviados.length = 0;
r = await pedir("/inscrever", comoJson({ email: "leitor@exemplo.com" }));
assert.equal((await r.json()).estado, "confirme", "a resposta na tela não revela nada");
assert.equal(enviados.length, 1);
assert.match(enviados[0].subject, /já está na lista/);
passo("quem já está na lista recebe outro e-mail, e a tela não denuncia");

enviados.length = 0;
redeAtual = "203.0.113.50";
let bloqueou = false;
for (let i = 0; i < 8; i += 1) {
  const resposta = await pedir("/inscrever", comoJson({ email: `pessoa${i}@exemplo.com` }));
  if (resposta.status === 429) {
    bloqueou = true;
    break;
  }
}
assert.ok(bloqueou, "a mesma rede deveria ser barrada depois de algumas tentativas");

redeAtual = "203.0.113.51";
const vizinho = await pedir("/inscrever", comoJson({ email: "vizinho@exemplo.com" }));
assert.notEqual(vizinho.status, 429, "o limite é por rede: quem não abusou não pode ser barrado");
passo("tentativa em série de uma rede é barrada, e a rede ao lado não");

r = await pedir("/enviar", comoJson({ slug: TEXTO.slug }));
assert.equal(r.status, 401);
r = await pedir(
  "/enviar",
  comoJson({ slug: TEXTO.slug }, { authorization: "Bearer segredo-errado" }),
);
assert.equal(r.status, 401);
passo("/enviar recusa quem não tem o segredo");

enviados.length = 0;
const autorizado = { authorization: `Bearer ${env.SEGREDO_ENVIO}` };
r = await pedir("/enviar", comoJson({ slug: TEXTO.slug }, autorizado));
let envio = await r.json();
assert.equal(envio.enviados, 1, "só o confirmado recebe");
assert.equal(envio.restantes, 0);
assert.deepEqual(envio.falhas, []);
assert.equal(enviados[0].to[0], "leitor@exemplo.com");
assert.equal(enviados[0].subject, TEXTO.titulo);
passo("o texto vai só para quem confirmou");

const email = enviados[0];
assert.match(
  email.html,
  /src="https:\/\/enricopierro\.com\.br\/assets\/img\/acervo\/dia-193\.webp"/,
  "a imagem tem de virar endereço absoluto — relativo não abre em caixa de entrada",
);
assert.doesNotMatch(email.html, /class="esc-item__media"/, "classe do site não serve em e-mail");
assert.doesNotMatch(email.html, /loading="lazy"/);
assert.match(email.html, /5 de agosto de 2026/, "a data sai escrita em português");
assert.match(email.html, /escrita\.html#dia-193-365/, "e há link para ler no site");
assert.ok(email.headers["List-Unsubscribe"], "sem List-Unsubscribe o Gmail não mostra o botão");
assert.match(email.text, /para sair da lista: https:/, "a versão em texto também tem a saída");
passo("o e-mail do texto tem imagem absoluta, data em português e saída da lista");

enviados.length = 0;
r = await pedir("/enviar", comoJson({ slug: TEXTO.slug }, autorizado));
envio = await r.json();
assert.equal(envio.enviados, 0);
assert.equal(enviados.length, 0, "ninguém pode receber o mesmo texto duas vezes");
passo("chamar /enviar de novo com o mesmo texto não manda nada");

r = await pedir("/enviar", comoJson({ slug: "texto-que-nao-existe" }, autorizado));
assert.equal(r.status, 404);
passo("slug inexistente responde 404 em vez de mandar e-mail vazio");

enviados.length = 0;
r = await pedir(
  "/enviar",
  comoJson({ slug: TEXTO.slug, destino_teste: "eu@exemplo.com" }, autorizado),
);
assert.equal(r.status, 200);
assert.equal(enviados.length, 1);
assert.equal(enviados[0].to[0], "eu@exemplo.com");
passo("destino_teste manda só para um endereço");

const tokenCancelar = linkDoUltimoEmail("cancelar");
r = await pedir(`/cancelar?t=${tokenCancelar}`);
assert.ok(r.headers.get("location").endsWith("newsletter-link-invalido.html"),
  "o token do envio de TESTE é de exemplo e não cancela ninguém");
passo("o link do e-mail de teste não cancela inscrição de verdade");

enviados.length = 0;
redeAtual = "192.0.2.77";
await pedir("/inscrever", comoJson({ email: "sai@exemplo.com" }));
const t2 = linkDoUltimoEmail("confirmar");
await pedir(`/confirmar?t=${t2}`);
enviados.length = 0;
await pedir("/enviar", comoJson({ slug: "dia-193-365", destino_teste: "" }, autorizado));
const tokenSair = linkDoUltimoEmail("cancelar");
r = await pedir(`/cancelar?t=${tokenSair}`);
assert.ok(r.headers.get("location").endsWith("newsletter-cancelado.html"));
passo("o link do fim do e-mail tira a pessoa da lista");

r = await pedir("/estado", { headers: autorizado });
contas = await r.json();
const restante = await env.DB.prepare("SELECT COUNT(*) AS n FROM inscritos WHERE email = ?")
  .bind("sai@exemplo.com")
  .first();
assert.equal(restante.n, 0, "cancelar tem de APAGAR a linha, como a página promete");
passo("cancelar apaga o endereço do banco");

r = await pedir(`/cancelar?t=${tokenSair}`);
assert.ok(r.headers.get("location").endsWith("newsletter-link-invalido.html"));
passo("link de saída usado não continua valendo");

redeAtual = "192.0.2.90";
const comoFormulario = (campos) => ({
  method: "POST",
  headers: { "content-type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams(campos).toString(),
});

enviados.length = 0;
r = await pedir("/inscrever", comoFormulario({ email: "semjs@exemplo.com", origem: "/index.html" }));
assert.equal(r.status, 303, "sem JS a resposta tem de ser redirecionamento, não JSON");
assert.ok(r.headers.get("location").endsWith("newsletter-confirme.html"));
assert.equal(enviados.length, 1, "e o e-mail de confirmação sai igual");
passo("formulário sem JavaScript inscreve e cai na página de confirme");

r = await pedir("/inscrever", comoFormulario({ email: "isso-não-é-e-mail" }));
assert.ok(
  r.headers.get("location").endsWith("newsletter-nao-deu.html"),
  "endereço errado sem JS não pode cair em 'esse link não vale mais'",
);
passo("erro de inscrição sem JavaScript cai na página de não deu");

r = await pedir("/qualquer-coisa");
assert.equal(r.status, 404);
passo("rota desconhecida responde 404");

console.log(`\n${passos} passos, nenhum erro.\n`);
