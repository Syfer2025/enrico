export function initEscApp(root) {
  const paineis = [...root.querySelectorAll(".esc-panel")];
  const listasPeriodo = [...root.querySelectorAll(".esc-side__list--periodos")];
  if (!paineis.length) return;

  const botoesCat = [...root.querySelectorAll("[data-cat].esc-side__link")];

  const marcar = (botoes, ativo) => {
    for (const b of botoes) {
      if (b === ativo) b.setAttribute("aria-current", "true");
      else b.removeAttribute("aria-current");
    }
  };

  const painelDe = (cat) => paineis.find((p) => p.dataset.cat === cat);

  const botoesPeriodo = () =>
    listasPeriodo.flatMap((l) => [...l.querySelectorAll("[data-periodo]")]);

  const mostraPeriodo = (painel, pid) => {
    const secoes = [...painel.querySelectorAll(".esc-per")];
    const alvo = secoes.find((s) => s.dataset.periodo === pid) || secoes[0];
    for (const s of secoes) s.hidden = s !== alvo;

    const lista = listasPeriodo.find((l) => l.dataset.cat === painel.dataset.cat);
    if (lista) {

      const doAlvo = [...lista.querySelectorAll("[data-periodo]")].find(
        (b) => b.dataset.periodo === alvo?.dataset.periodo
      );
      marcar(botoesPeriodo(), doAlvo);
    }
    return alvo;
  };

  const mostraCategoria = (cat, pid = null) => {
    const painel = painelDe(cat);
    if (!painel) return null;

    for (const p of paineis) p.hidden = p !== painel;
    for (const l of listasPeriodo) l.hidden = l.dataset.cat !== cat;
    marcar(botoesCat, botoesCat.find((b) => b.dataset.cat === cat));

    const primeiro = painel.querySelector(".esc-per")?.dataset.periodo;
    mostraPeriodo(painel, pid || primeiro);
    return painel;
  };

  root.addEventListener("click", (evento) => {
    const cat = evento.target.closest("[data-cat].esc-side__link");
    if (cat) {
      mostraCategoria(cat.dataset.cat);

      if (window.matchMedia("(width < 1040px)").matches) {
        painelDe(cat.dataset.cat)?.scrollIntoView({ block: "start", behavior: "smooth" });
      }
      return;
    }

    const per = evento.target.closest("[data-periodo].esc-side__link");
    if (per) {
      const painel = paineis.find((p) => !p.hidden);
      if (painel) mostraPeriodo(painel, per.dataset.periodo);
    }
  });

  const revelaPeloHash = () => {
    const slug = decodeURIComponent(location.hash.slice(1));
    if (!slug) return;

    const painelDireto = paineis.find((p) => `esc-${p.dataset.cat}` === slug);
    if (painelDireto) {
      mostraCategoria(painelDireto.dataset.cat);
      return;
    }

    const linha = root.querySelector(`.esc-row[data-slug="${CSS.escape(slug)}"]`);
    if (!linha) return;
    const painel = linha.closest(".esc-panel");
    const secao = linha.closest(".esc-per");
    if (painel) mostraCategoria(painel.dataset.cat, secao?.dataset.periodo || null);
  };

  revelaPeloHash();
  window.addEventListener("popstate", revelaPeloHash);
}
