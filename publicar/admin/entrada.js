(() => {
  "use strict";

  const painelDeTeste = async () => {

    const links = [...document.querySelectorAll('link[rel="cms-config-url"]')];
    const enderecos = links.length ? links.map((l) => l.href) : ["config.yml"];

    for (const endereco of enderecos) {
      try {
        const texto = await (await fetch(endereco)).text();
        const vale = texto
          .split("\n")
          .some((l) => /^\s*name\s*:\s*test-repo\s*$/.test(l) && !/^\s*#/.test(l));
        if (vale) return true;
      } catch {

      }
    }
    return false;
  };

  const esconderAvisos = () => {
    for (const faixa of document.querySelectorAll(".infobar")) faixa.remove();
  };

  const iniciar = async () => {
    const teste = await painelDeTeste();
    console.info(
      `[entrada] painel ${teste ? "de TESTE" : "de produção"} — ` +
        `avisos do CMS ${teste ? "mantidos" : "escondidos"}`,
    );
    if (teste) return;

    esconderAvisos();

    let agendado = null;
    new MutationObserver(() => {
      clearTimeout(agendado);
      agendado = setTimeout(esconderAvisos, 100);
    }).observe(document.body, { childList: true, subtree: true });
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
