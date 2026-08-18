const POR_CHAMADA = 40;

const HORAS_PARA_CONFIRMAR = 48;

const TENTATIVAS_MAX = 5;
const TENTATIVAS_JANELA_S = 600;

const agora = () => Math.floor(Date.now() / 1000);

function token() {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  return [...bytes].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function resumo(texto) {
  const dados = new TextEncoder().encode(texto);
  const hash = await crypto.subtle.digest("SHA-256", dados);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function emailValido(valor) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(valor);
}

function normalizar(valor) {
  return String(valor || "").trim().toLowerCase();
}

function segredoConfere(recebido, esperado) {
  if (!esperado || !recebido || recebido.length !== esperado.length) return false;
  let diferenca = 0;
  for (let i = 0; i < recebido.length; i += 1) {
    diferenca |= recebido.charCodeAt(i) ^ esperado.charCodeAt(i);
  }
  return diferenca === 0;
}

function json(dados, status = 200, cabecalhos = {}) {
  return new Response(JSON.stringify(dados), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...cabecalhos },
  });
}

function corsDe(request, env) {
  const permitidas = (env.ORIGENS || "").split(",").map((o) => o.trim()).filter(Boolean);
  const origem = request.headers.get("origin");
  if (!origem || !permitidas.includes(origem)) return {};
  return {
    "access-control-allow-origin": origem,
    "access-control-allow-methods": "POST, OPTIONS",
    "access-control-allow-headers": "content-type",
    "access-control-max-age": "86400",
    vary: "origin",
  };
}

async function enviarEmail(env, { para, assunto, html, texto, cancelarUrl }) {
  const cabecalhos = cancelarUrl
    ? {
        "List-Unsubscribe": `<${cancelarUrl}>`,
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
      }
    : {};

  if (env.PROVEDOR === "brevo") {
    const [, nome, endereco] = /^(.*?)\s*<(.+)>$/.exec(env.REMETENTE) || [
      null,
      "",
      env.REMETENTE,
    ];
    const resposta = await fetch("https://api.brevo.com/v3/smtp/email", {
      method: "POST",
      headers: { "api-key": env.CHAVE_ENVIO, "content-type": "application/json" },
      body: JSON.stringify({
        sender: { name: nome || "enrico pierro", email: endereco },
        to: [{ email: para }],
        subject: assunto,
        htmlContent: html,
        textContent: texto,
        headers: cabecalhos,
      }),
    });
    if (!resposta.ok) throw new Error(`brevo ${resposta.status}: ${await resposta.text()}`);
    return;
  }

  const resposta = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.CHAVE_ENVIO}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: env.REMETENTE,
      to: [para],
      subject: assunto,
      html,
      text: texto,
      headers: cabecalhos,
    }),
  });
  if (!resposta.ok) throw new Error(`resend ${resposta.status}: ${await resposta.text()}`);
}

function molduraEmail(env, { titulo, corpo, rodape }) {
  const logo = `${env.SITE.replace(/\/$/, "")}/assets/img/brand/logo-enrico-preto-960.png`;
  return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width" />
<title>${escapar(titulo)}</title></head>
<body style="margin:0;padding:24px 16px;background:#f4f1ec;">
  <div style="max-width:36rem;margin:0 auto;padding:32px 28px;background:#fffdf9;
              border-radius:20px;font-family:-apple-system,BlinkMacSystemFont,
              'Segoe UI',Helvetica,Arial,sans-serif;font-size:17px;line-height:1.6;
              color:#1a1a1a;">
    <div style="text-align:center;margin:0 0 28px;">
      <img src="${logo}" width="176" alt="enrico pierro"
           style="width:176px;max-width:176px;height:auto;border:0;display:inline-block;" />
    </div>
${corpo}
  </div>
  <div style="max-width:36rem;margin:16px auto 0;padding:0 28px;font-family:-apple-system,
              BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px;
              line-height:1.5;color:#5c5c5c;">
${rodape}
  </div>
</body></html>`;
}

function escapar(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const BOTAO =
  "display:inline-block;padding:14px 28px;background:#ffb232;color:#0a0b06;" +
  "text-decoration:none;border-radius:999px;font-weight:600;line-height:1;";

function emailDeConfirmacao(env, confirmarUrl) {
  const corpo = `    <p style="margin:0 0 20px;">oi.</p>
    <p style="margin:0 0 20px;">
      alguém — espero que você — pediu para receber os textos do enrico pierro
      por e-mail. um clique confirma, e a partir daí cada texto novo chega aqui
      no dia em que sai.
    </p>
    <p style="margin:0 0 24px;">
      <a href="${escapar(confirmarUrl)}" style="${BOTAO}">confirmar</a>
    </p>
    <p style="margin:0 0 8px;color:#5c5c5c;font-size:15px;">
      o link vale por ${HORAS_PARA_CONFIRMAR} horas e serve uma vez.
    </p>
    <p style="margin:0;color:#5c5c5c;font-size:15px;">
      se não foi você, não faça nada: sem esse clique o endereço não entra na
      lista, e este é o único e-mail que ele recebe.
    </p>`;
  const texto = `oi.

alguém — espero que você — pediu para receber os textos do enrico pierro por
e-mail. confirme neste endereço:

${confirmarUrl}

o link vale por ${HORAS_PARA_CONFIRMAR} horas e serve uma vez.

se não foi você, não faça nada: sem esse clique o endereço não entra na lista,
e este é o único e-mail que ele recebe.`;
  return {
    assunto: "confirme para receber os textos do enrico",
    html: molduraEmail(env, {
      titulo: "confirme sua inscrição",
      corpo,
      rodape: "você não recebe mais nada neste endereço se não confirmar.",
    }),
    texto,
  };
}

function emailDeJaInscrito(env, cancelarUrl) {
  const corpo = `    <p style="margin:0 0 20px;">oi.</p>
    <p style="margin:0 0 20px;">
      este endereço já está na lista dos textos do enrico — alguém acabou de
      pedir a inscrição de novo, e não havia nada a fazer.
    </p>
    <p style="margin:0;color:#5c5c5c;font-size:15px;">
      se os textos não estão chegando, vale olhar o spam e marcar como "não é
      spam": é o que ensina o seu provedor a entregar os próximos.
    </p>`;
  const texto = `oi.

este endereço já está na lista dos textos do enrico — alguém acabou de pedir a
inscrição de novo, e não havia nada a fazer.

se os textos não estão chegando, vale olhar o spam e marcar como "não é spam".

para sair da lista: ${cancelarUrl}`;
  return {
    assunto: "este endereço já está na lista",
    html: molduraEmail(env, {
      titulo: "já está na lista",
      corpo,
      rodape: `<a href="${escapar(cancelarUrl)}" style="color:#5c5c5c;">sair da lista</a>`,
    }),
    texto,
  };
}

function dataLonga(iso) {
  const [ano, mes, dia] = String(iso).split("-").map(Number);
  if (!ano || !mes || !dia) return "";
  return new Intl.DateTimeFormat("pt-BR", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(Date.UTC(ano, mes - 1, dia)));
}

function textoParaEmail(html, site) {
  return html
    .replace(/\s(?:class|loading|decoding|sizes|srcset)="[^"]*"/g, "")
    .replace(/src="(?!https?:)\/?([^"]+)"/g, (_, caminho) => `src="${site}/${caminho}"`)
    .replace(/<img /g, '<img style="max-width:100%;height:auto;border-radius:8px;" ')
    .replace(/<figure[^>]*>/g, '<figure style="margin:0 0 20px;">')
    .replace(/<p>/g, '<p style="margin:0 0 20px;">')
    .replace(/<blockquote[^>]*>/g, '<blockquote style="margin:0 0 20px;padding-left:16px;border-left:2px solid #d9d2c7;color:#5c5c5c;">');
}

function emailDoTexto(env, texto, cancelarUrl) {
  const site = env.SITE.replace(/\/$/, "");
  const endereco = `${site}/escrita.html#${texto.slug}`;
  const corpo = `    <p style="margin:0 0 4px;font-size:13px;letter-spacing:0.06em;
       text-transform:uppercase;color:#a15a08;">${escapar(texto.categoria || "texto")}</p>
    <h1 style="margin:0 0 4px;font-size:26px;line-height:1.2;font-weight:700;">
      ${escapar(texto.titulo)}
    </h1>
    <p style="margin:0 0 28px;font-size:14px;color:#5c5c5c;">${escapar(dataLonga(texto.data))}</p>
${textoParaEmail(texto.conteudo || "", site)}
    <p style="margin:28px 0 0;">
      <a href="${escapar(endereco)}" style="color:#a15a08;">ler no site</a>
    </p>`;
  const texto_puro = `${texto.titulo}
${dataLonga(texto.data)}

${(texto.conteudo || "").replace(/<[^>]+>/g, "").replace(/\n{3,}/g, "\n\n").trim()}

ler no site: ${endereco}

para sair da lista: ${cancelarUrl}`;
  return {
    assunto: texto.titulo,
    html: molduraEmail(env, {
      titulo: texto.titulo,
      corpo,
      rodape:
        `você recebe isto porque pediu os textos do enrico pierro. ` +
        `<a href="${escapar(cancelarUrl)}" style="color:#5c5c5c;">sair da lista</a>.`,
    }),
    texto: texto_puro,
  };
}

const paginas = {
  confirme: "newsletter-confirme.html",
  confirmado: "newsletter-confirmado.html",
  cancelado: "newsletter-cancelado.html",

  invalido: "newsletter-link-invalido.html",
  "nao-deu": "newsletter-nao-deu.html",
};

function paraOSite(env, qual) {
  return Response.redirect(`${env.SITE.replace(/\/$/, "")}/${paginas[qual]}`, 303);
}

async function corpoDe(request) {
  const tipo = request.headers.get("content-type") || "";
  if (tipo.includes("application/json")) {
    return { dados: await request.json().catch(() => ({})), navegador: false };
  }
  const form = await request.formData().catch(() => new FormData());
  return { dados: Object.fromEntries(form), navegador: true };
}

async function limitePassou(env, redeHash) {
  const corte = agora() - TENTATIVAS_JANELA_S;
  await env.DB.prepare("DELETE FROM tentativas WHERE quando < ?").bind(corte).run();
  const { results } = await env.DB.prepare(
    "SELECT COUNT(*) AS n FROM tentativas WHERE rede_hash = ? AND quando >= ?",
  )
    .bind(redeHash, corte)
    .all();
  if ((results?.[0]?.n ?? 0) >= TENTATIVAS_MAX) return false;
  await env.DB.prepare("INSERT INTO tentativas (rede_hash, quando) VALUES (?, ?)")
    .bind(redeHash, agora())
    .run();
  return true;
}

async function inscrever(request, env) {
  const cors = corsDe(request, env);
  const { dados, navegador } = await corpoDe(request);

  const responder = (estado, status = 200) =>
    navegador
      ? paraOSite(env, estado === "confirme" ? "confirme" : "nao-deu")
      : json({ estado }, status, cors);

  if (normalizar(dados.site)) return responder("confirme");

  const email = normalizar(dados.email);
  if (!emailValido(email)) return responder("email-invalido", 400);

  const rede = request.headers.get("cf-connecting-ip") || "sem-ip";
  const redeHash = await resumo(`${rede}:${env.SAL || ""}`);
  if (!(await limitePassou(env, redeHash))) return responder("muitas-tentativas", 429);

  const site = env.SITE.replace(/\/$/, "");
  const existente = await env.DB.prepare(
    "SELECT estado, cancelar_hash FROM inscritos WHERE email = ?",
  )
    .bind(email)
    .first();

  try {
    if (existente?.estado === "confirmado") {

      const bruto = token();
      await env.DB.prepare("UPDATE inscritos SET cancelar_hash = ? WHERE email = ?")
        .bind(await resumo(bruto), email)
        .run();
      const { assunto, html, texto } = emailDeJaInscrito(
        env,
        `${env.ENDPOINT}/cancelar?t=${bruto}`,
      );
      await enviarEmail(env, { para: email, assunto, html, texto });
      return responder("confirme");
    }

    const confirmar = token();
    const cancelar = token();
    await env.DB.prepare(
      `INSERT INTO inscritos
         (email, estado, confirmar_hash, confirmar_expira, cancelar_hash,
          criado_em, origem, rede_hash)
       VALUES (?, 'pendente', ?, ?, ?, ?, ?, ?)
       ON CONFLICT(email) DO UPDATE SET
         confirmar_hash = excluded.confirmar_hash,
         confirmar_expira = excluded.confirmar_expira,
         cancelar_hash = excluded.cancelar_hash,
         origem = excluded.origem,
         rede_hash = excluded.rede_hash`,
    )
      .bind(
        email,
        await resumo(confirmar),
        agora() + HORAS_PARA_CONFIRMAR * 3600,
        await resumo(cancelar),
        agora(),
        String(dados.origem || "").slice(0, 120),
        redeHash,
      )
      .run();

    const { assunto, html, texto } = emailDeConfirmacao(
      env,
      `${env.ENDPOINT}/confirmar?t=${confirmar}`,
    );
    await enviarEmail(env, { para: email, assunto, html, texto });
    return responder("confirme");
  } catch (erro) {
    console.error("inscrever:", erro?.message || erro);
    return navegador ? paraOSite(env, "nao-deu") : json({ estado: "indisponivel" }, 502, cors);
  }
}

async function confirmar(request, env) {
  const bruto = new URL(request.url).searchParams.get("t") || "";
  if (!bruto) return paraOSite(env, "invalido");

  const hash = await resumo(bruto);
  const linha = await env.DB.prepare(
    "SELECT email, confirmar_expira FROM inscritos WHERE confirmar_hash = ?",
  )
    .bind(hash)
    .first();

  if (!linha || (linha.confirmar_expira || 0) < agora()) return paraOSite(env, "invalido");

  await env.DB.prepare(
    `UPDATE inscritos
        SET estado = 'confirmado', confirmado_em = ?, confirmar_hash = NULL,
            confirmar_expira = NULL
      WHERE email = ?`,
  )
    .bind(agora(), linha.email)
    .run();

  return paraOSite(env, "confirmado");
}

async function cancelar(request, env) {
  const bruto = new URL(request.url).searchParams.get("t") || "";
  if (!bruto) return paraOSite(env, "invalido");

  const resultado = await env.DB.prepare("DELETE FROM inscritos WHERE cancelar_hash = ?")
    .bind(await resumo(bruto))
    .run();

  const saiu = (resultado.meta?.changes ?? 0) > 0;
  return paraOSite(env, saiu ? "cancelado" : "invalido");
}

async function enviar(request, env) {
  const dados = await request.json().catch(() => ({}));
  const slug = String(dados.slug || "").trim();
  if (!slug) return json({ erro: "falta o slug do texto" }, 400);

  const site = env.SITE.replace(/\/$/, "");
  const resposta = await fetch(`${site}/assets/data/textos/${encodeURIComponent(slug)}.json`);
  if (!resposta.ok) {
    return json({ erro: `texto '${slug}' não existe no site publicado` }, 404);
  }
  const texto = await resposta.json();

  if (dados.destino_teste) {
    const email = normalizar(dados.destino_teste);
    if (!emailValido(email)) return json({ erro: "destino_teste inválido" }, 400);
    const { assunto, html, texto: puro } = emailDoTexto(
      env,
      texto,
      `${env.ENDPOINT}/cancelar?t=exemplo`,
    );
    await enviarEmail(env, { para: email, assunto, html, texto: puro });
    return json({ teste: email, assunto });
  }

  await env.DB.prepare(
    "INSERT INTO envios (slug, titulo, iniciado_em) VALUES (?, ?, ?) ON CONFLICT(slug) DO NOTHING",
  )
    .bind(slug, texto.titulo || slug, agora())
    .run();

  const { results: fila } = await env.DB.prepare(
    `SELECT i.email, i.cancelar_hash
       FROM inscritos i
      WHERE i.estado = 'confirmado'
        AND NOT EXISTS (SELECT 1 FROM envio_feito f WHERE f.slug = ? AND f.email = i.email)
      LIMIT ?`,
  )
    .bind(slug, POR_CHAMADA)
    .all();

  let enviados = 0;
  const falhas = [];
  for (const inscrito of fila || []) {

    const bruto = token();
    try {
      await env.DB.prepare("UPDATE inscritos SET cancelar_hash = ? WHERE email = ?")
        .bind(await resumo(bruto), inscrito.email)
        .run();
      const { assunto, html, texto: puro } = emailDoTexto(
        env,
        texto,
        `${env.ENDPOINT}/cancelar?t=${bruto}`,
      );
      await enviarEmail(env, {
        para: inscrito.email,
        assunto,
        html,
        texto: puro,
        cancelarUrl: `${env.ENDPOINT}/cancelar?t=${bruto}`,
      });
      await env.DB.prepare(
        "INSERT INTO envio_feito (slug, email, quando) VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
      )
        .bind(slug, inscrito.email, agora())
        .run();
      enviados += 1;
    } catch (erro) {

      falhas.push({ email: inscrito.email, erro: String(erro?.message || erro).slice(0, 160) });
    }
  }

  const { results: resta } = await env.DB.prepare(
    `SELECT COUNT(*) AS n
       FROM inscritos i
      WHERE i.estado = 'confirmado'
        AND NOT EXISTS (SELECT 1 FROM envio_feito f WHERE f.slug = ? AND f.email = i.email)`,
  )
    .bind(slug)
    .all();
  const restantes = resta?.[0]?.n ?? 0;

  if (restantes === 0) {
    await env.DB.prepare("UPDATE envios SET terminado_em = ? WHERE slug = ?")
      .bind(agora(), slug)
      .run();
  }

  return json({ slug, titulo: texto.titulo, enviados, restantes, falhas });
}

async function estado(env) {
  const { results } = await env.DB.prepare(
    `SELECT
       (SELECT COUNT(*) FROM inscritos WHERE estado = 'confirmado') AS confirmados,
       (SELECT COUNT(*) FROM inscritos WHERE estado = 'pendente')   AS pendentes,
       (SELECT COUNT(*) FROM envios WHERE terminado_em IS NOT NULL) AS envios_completos,
       (SELECT COUNT(*) FROM envios WHERE terminado_em IS NULL)     AS envios_no_meio`,
  ).all();
  return json(results?.[0] || {});
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    const rota = (nome) => url.pathname.replace(/\/$/, "").endsWith(`/${nome}`);

    for (const nome of ["SITE", "ENDPOINT", "REMETENTE"]) {
      if (!env[nome]) {
        console.error(`falta a variável ${nome} no wrangler.toml`);
        return json({ estado: "indisponivel" }, 500);
      }
    }

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsDe(request, env) });
    }

    if (request.method === "POST" && rota("inscrever")) return inscrever(request, env);
    if (request.method === "GET" && rota("confirmar")) return confirmar(request, env);
    if (request.method === "GET" && rota("cancelar")) return cancelar(request, env);

    const autorizado = segredoConfere(
      (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, ""),
      env.SEGREDO_ENVIO,
    );
    if (request.method === "POST" && rota("enviar")) {
      if (!autorizado) return json({ erro: "não autorizado" }, 401);
      return enviar(request, env);
    }
    if (request.method === "GET" && rota("estado")) {
      if (!autorizado) return json({ erro: "não autorizado" }, 401);
      return estado(env);
    }

    return json({ erro: "rota não existe" }, 404);
  },
};
