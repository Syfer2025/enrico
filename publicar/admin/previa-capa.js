(() => {
  "use strict";

  const POSICAO = {
    "centro (padrão)": "50% 50%",
    centro: "50% 50%",
    topo: "50% 0%",
    "parte de baixo": "50% 100%",
    esquerda: "0% 50%",
    direita: "100% 50%",
  };

  const CLASSE = "previa-capa";
  const CAMPO = 'section[data-field-type="select"][data-key-path="enquadramento"]';

  const posicaoDe = (combobox) => {
    const rotulo = (combobox.textContent || "").trim().toLowerCase();
    return POSICAO[rotulo] || POSICAO.centro;
  };

  const CAMINHO = /\/assets\/img\/[\w./-]+\.(?:webp|jpe?g|png|avif|gif)/i;

  const acharEndereco = (secao) => {
    const formulario = secao.closest("[role='group'][data-mode]") || secao.parentElement;
    if (!formulario) return "";

    const campoCapa = formulario.querySelector("[data-key-path='capa']");
    if (campoCapa) {
      for (const no of campoCapa.querySelectorAll("*")) {
        if (no.children.length) continue;
        const achado = (no.textContent || "").trim().match(CAMINHO);
        if (achado) return achado[0];
      }
      for (const img of campoCapa.querySelectorAll("img")) {
        const src = img.getAttribute("src") || img.src || "";
        if (CAMINHO.test(src)) return src;
      }
    }

    const editor = formulario.querySelector(".lexical-root, [contenteditable='true']");
    if (editor) {

      let restam = 600;
      for (const no of editor.querySelectorAll("*")) {
        if (restam-- <= 0) break;
        if (no.children.length) continue;
        const achado = (no.textContent || "").trim().match(CAMINHO);
        if (achado) return achado[0];
      }
    }

    for (const caixa of formulario.querySelectorAll("textarea")) {
      const achado = (caixa.value || "").match(CAMINHO);
      if (achado) return achado[0];
    }

    for (const img of formulario.querySelectorAll("img")) {
      if (img.closest(`.${CLASSE}`)) continue;
      const src = img.getAttribute("src") || img.src || "";
      if (CAMINHO.test(src)) return src;
    }

    return "";
  };

  const montar = (secao) => {
    const combobox = secao.querySelector('[role="combobox"]');
    if (!combobox) return false;

    let previa = secao.querySelector(`.${CLASSE}`);
    if (!previa) {
      previa = document.createElement("div");
      previa.className = CLASSE;
      previa.innerHTML = `
        <figure class="${CLASSE}__caixa">
          <div class="${CLASSE}__moldura ${CLASSE}__moldura--quadrado"><img alt="" /></div>
          <figcaption>na lista</figcaption>
        </figure>
        <figure class="${CLASSE}__caixa">
          <div class="${CLASSE}__moldura ${CLASSE}__moldura--cartao"><img alt="" /></div>
          <figcaption>no cartão</figcaption>
        </figure>
        <p class="${CLASSE}__recado">Sem capa. Escolha uma foto no campo
        <b>Capa</b>, acima: o recorte aparece aqui.</p>`;

      (combobox.closest(".sui.combobox") || combobox).after(previa);
    }

    const atualizar = () => {
      const endereco = acharEndereco(secao);
      const posicao = posicaoDe(combobox);
      previa.dataset.vazia = endereco ? "nao" : "sim";
      for (const img of previa.querySelectorAll("img")) {
        if (endereco && img.src !== endereco) img.src = endereco;
        img.style.objectPosition = posicao;
      }
    };

    if (!combobox.dataset.previaLigada) {
      combobox.dataset.previaLigada = "sim";

      new MutationObserver(atualizar).observe(combobox, {
        childList: true,
        subtree: true,
        characterData: true,
      });
    }
    atualizar();
    return true;
  };

  const aplicar = () => {
    let n = 0;
    for (const secao of document.querySelectorAll(CAMPO)) {
      if (montar(secao)) n += 1;
    }
    return n;
  };

  const iniciar = () => {
    let ultimo = -1;
    let agendado = null;
    const passar = () => {
      const n = aplicar();
      if (n !== ultimo) {
        ultimo = n;
        console.info(
          `[previa-capa] ${n} campo(s) de enquadramento com prévia. ` +
            `Zero, com um texto aberto, significa que ${CAMPO} não casou — ` +
            `confira no painel de teste (admin/teste.html).`,
        );
      }
    };

    document.addEventListener(
      "input",
      () => {
        clearTimeout(agendado);
        agendado = setTimeout(passar, 150);
      },
      { capture: true, passive: true },
    );

    new MutationObserver(() => {
      clearTimeout(agendado);
      agendado = setTimeout(passar, 150);
    }).observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["src"],
    });
    passar();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
