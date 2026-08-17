(() => {
  "use strict";

  const EXPLICACOES = {
    "Origem":
      "Arquivo da imagem. Substituir troca a foto; Remover tira ela do texto.",
    "Texto Alternativo":
      "Descrição da foto em palavras. Lida por leitores de tela e exibida quando a imagem não carrega. Ex.: “enrico no estúdio, de jaqueta azul”.",
    "Título":
      "Balão exibido ao passar o mouse sobre a foto. Opcional.",
    "Link":
      "Torna a foto clicável, levando ao endereço informado. Opcional.",
    "Imagem":
      "Foto no meio do texto. A capa do texto é definida no campo Capa, no alto do formulário.",
  };

  const CLASSE = "ajuda-enrico";
  const MARGEM = 10;

  const balao = document.createElement("div");
  balao.className = `${CLASSE}__balao`;
  balao.setAttribute("role", "tooltip");
  balao.hidden = true;

  let atual = null;

  const esconder = () => {
    if (!atual) return;
    delete atual.dataset.aberto;
    atual = null;
    balao.hidden = true;
  };

  const posicionar = () => {
    if (!atual) return;
    const b = atual.getBoundingClientRect();
    const t = balao.getBoundingClientRect();

    let topo = b.top - t.height - 8;
    if (topo < MARGEM) topo = b.bottom + 8;

    let esquerda = b.left + b.width / 2 - t.width / 2;
    const limite = document.documentElement.clientWidth - t.width - MARGEM;
    esquerda = Math.max(MARGEM, Math.min(esquerda, limite));

    balao.style.top = `${Math.round(topo)}px`;
    balao.style.left = `${Math.round(esquerda)}px`;
  };

  const mostrar = (botao) => {
    if (atual === botao) return;
    esconder();
    atual = botao;
    botao.dataset.aberto = "sim";
    balao.textContent = botao.dataset.ajuda || "";
    balao.hidden = false;

    posicionar();
  };

  const criarBotao = (texto) => {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = CLASSE;
    botao.textContent = "?";
    botao.dataset.ajuda = texto;

    botao.setAttribute("aria-label", `O que é isto? ${texto}`);

    botao.addEventListener("pointerenter", () => mostrar(botao));
    botao.addEventListener("pointerleave", () => {

      if (botao.dataset.fixado !== "sim") esconder();
    });
    botao.addEventListener("focus", () => mostrar(botao));
    botao.addEventListener("blur", () => {
      delete botao.dataset.fixado;
      esconder();
    });
    botao.addEventListener("click", (evento) => {
      evento.preventDefault();
      evento.stopPropagation();
      if (botao.dataset.fixado === "sim") {
        delete botao.dataset.fixado;
        esconder();
      } else {
        botao.dataset.fixado = "sim";
        mostrar(botao);
      }
    });

    return botao;
  };

  const jaExplicado = (rotulo) => {
    const caixa = rotulo.closest("section, div, li") || rotulo.parentElement;
    return caixa ? !!caixa.querySelector(".comment, .hint") : false;
  };

  const aplicar = () => {
    let postos = 0;
    const candidatos = document.querySelectorAll(
      "label, legend, h2, h3, h4, p, span, div, summary",
    );

    for (const elemento of candidatos) {
      if (elemento.querySelector(`.${CLASSE}`)) continue;
      if (elemento.closest(`.${CLASSE}`)) continue;

      if (elemento.querySelector("label, legend, p, span, div")) continue;

      const texto = (elemento.textContent || "").replace(/\s+/g, " ").trim();

      const explicacao = EXPLICACOES[texto.replace(/\s*\*\s*$/, "")];
      if (!explicacao) continue;
      if (jaExplicado(elemento)) continue;

      elemento.append(criarBotao(explicacao));
      postos += 1;
    }
    return postos;
  };

  const INUTEIS = ["Validação", "Validation", "Backlinks"];

  const arrumarPaineis = () => {
    const abas = document.querySelector('[aria-controls="entry-sidebar-content"]');
    if (!abas) return;

    let escondeuAAtiva = false;
    let historico = null;

    for (const aba of abas.querySelectorAll("button, [role='tab']")) {
      const nome =
        aba.getAttribute("aria-label") ||
        (aba.textContent || "").replace(/\s+/g, " ").trim();

      if (INUTEIS.some((x) => nome.includes(x))) {
        if (aba.getAttribute("aria-selected") === "true") escondeuAAtiva = true;
        aba.hidden = true;
        aba.style.display = "none";
      } else if (/Hist[óo]ri/i.test(nome)) {
        historico = aba;
      }
    }

    if (escondeuAAtiva && historico) historico.click();
  };

  const iniciar = () => {
    document.body.append(balao);
    const n = aplicar();
    arrumarPaineis();

    let agendado = null;
    new MutationObserver(() => {
      clearTimeout(agendado);
      agendado = setTimeout(() => {
        aplicar();

        arrumarPaineis();
      }, 120);
    }).observe(document.body, { childList: true, subtree: true });

    addEventListener("scroll", () => (atual ? posicionar() : null), true);
    addEventListener("resize", () => (atual ? posicionar() : null));

    document.addEventListener("click", (evento) => {
      if (evento.target instanceof Element && evento.target.closest(`.${CLASSE}`)) return;
      document.querySelectorAll(`.${CLASSE}`).forEach((b) => delete b.dataset.fixado);
      esconder();
    });

    document.addEventListener("keydown", (evento) => {
      if (evento.key !== "Escape") return;
      document.querySelectorAll(`.${CLASSE}`).forEach((b) => delete b.dataset.fixado);
      esconder();
    });

    console.info(
      `[ajuda] ${n} explicação(ões) posta(s). ` +
        `Faltando alguma? O rótulo na tela não bate com a lista em admin/ajuda.js.`,
    );
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", iniciar);
  } else {
    iniciar();
  }
})();
