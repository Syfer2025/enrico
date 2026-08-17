const REDES = {
  whatsapp: (url, titulo) =>
    `https://wa.me/?text=${encodeURIComponent(`${titulo} ${url}`)}`,
  x: (url, titulo) =>
    `https://twitter.com/intent/tweet?text=${encodeURIComponent(titulo)}&url=${encodeURIComponent(url)}`,
  facebook: (url) =>
    `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
};

export function initEscLeitor(root) {
  const dialog = document.getElementById("esc-leitor");
  if (!dialog || typeof dialog.showModal !== "function") return;

  const pasta = (root.dataset.src || "assets/data/textos").replace(/\/$/, "");

  const cache = new Map();
  const buscar = (slug) => {
    if (!cache.has(slug)) {
      const pedido = fetch(`${pasta}/${encodeURIComponent(slug)}.json`).then(
        (r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status} em ${slug}`);
          return r.json();
        },
      );

      pedido.catch(() => cache.delete(slug));
      cache.set(slug, pedido);
    }
    return cache.get(slug);
  };

  const alvo = (nome) => dialog.querySelector(`[data-leitor="${nome}"]`);
  const el = {
    categoria: alvo("categoria"),
    data: alvo("data"),
    titulo: alvo("titulo"),
    corpo: alvo("corpo"),
    scroll: alvo("scroll"),
    copiar: alvo("copiar"),
    copiarRotulo: alvo("copiar-rotulo"),
    nativo: alvo("nativo"),
  };

  let atual = null;
  let devolverFoco = null;

  const linkDoTexto = (slug) =>
    `${location.origin}${location.pathname}#${encodeURIComponent(slug)}`;

  const montaShare = ({ slug, titulo }) => {
    const link = linkDoTexto(slug);
    for (const [rede, monta] of Object.entries(REDES)) {
      const a = alvo(rede);
      if (a) a.href = monta(link, titulo);
    }
    if (el.copiarRotulo) el.copiarRotulo.textContent = "Copiar link";
  };

  if (el.nativo && typeof navigator.share === "function") {
    el.nativo.hidden = false;
    el.nativo.addEventListener("click", async () => {
      if (!atual) return;
      try {
        await navigator.share({
          title: atual.titulo,
          text: atual.titulo,
          url: linkDoTexto(atual.slug),
        });
      } catch {

      }
    });
  }

  el.copiar?.addEventListener("click", async () => {
    if (!atual) return;
    try {
      await navigator.clipboard.writeText(linkDoTexto(atual.slug));
      if (el.copiarRotulo) el.copiarRotulo.textContent = "Link copiado";
    } catch {
      if (el.copiarRotulo) el.copiarRotulo.textContent = "Não deu para copiar";
    }
    setTimeout(() => {
      if (el.copiarRotulo) el.copiarRotulo.textContent = "Copiar link";
    }, 2200);
  });

  const preencher = (slug, dica) => {

    el.titulo.textContent = dica?.titulo || "";
    el.data.textContent = dica?.dataCurta || "";
    el.categoria.textContent = "";
    el.corpo.replaceChildren();

    const aviso = document.createElement("p");
    aviso.className = "esc-item__loading";
    aviso.textContent = "carregando o texto…";
    el.corpo.append(aviso);

    buscar(slug)
      .then((post) => {

        if (atual?.slug !== slug) return;

        el.titulo.textContent = post.titulo;
        el.categoria.textContent = post.categoria;
        el.data.textContent = dica?.dataCurta || post.data;
        el.data.setAttribute("datetime", post.data);

        const caixa = document.createElement("div");
        caixa.innerHTML = post.conteudo;
        el.corpo.replaceChildren(...caixa.childNodes);

        atual = { slug, titulo: post.titulo };
        montaShare(atual);
      })
      .catch((erro) => {
        if (atual?.slug !== slug) return;
        el.corpo.replaceChildren();
        const falha = document.createElement("p");
        falha.className = "esc-item__loading";
        falha.textContent = "não consegui carregar este texto.";
        el.corpo.append(falha);

        console.error(`[esc-leitor] ${slug}:`, erro);
      });
  };

  const abrir = (slug, dica) => {
    if (atual?.slug === slug && dialog.open) return;
    atual = { slug, titulo: dica?.titulo || slug };
    montaShare(atual);
    preencher(slug, dica);

    if (!dialog.open) {
      devolverFoco = document.activeElement;
      dialog.showModal();
    }

    el.scroll.scrollTop = 0;
    el.scroll.focus({ preventScroll: true });
  };

  const fechar = () => {
    if (dialog.open) dialog.close();
  };

  root.addEventListener("click", (evento) => {
    const gatilho = evento.target.closest("[data-slug]");
    if (!gatilho || !root.contains(gatilho)) return;
    evento.preventDefault();
    const slug = gatilho.dataset.slug;

    history.pushState({ leitor: slug }, "", `#${encodeURIComponent(slug)}`);
    abrir(slug, {
      titulo: gatilho.dataset.titulo,
      dataCurta: gatilho.querySelector("time")?.textContent?.trim(),
    });
  });

  alvo("fechar")?.addEventListener("click", fechar);

  dialog.addEventListener("click", (evento) => {
    if (evento.target === dialog) fechar();
  });

  dialog.addEventListener("close", () => {
    if (location.hash) {
      history.pushState(null, "", location.pathname + location.search);
    }
    atual = null;
    devolverFoco?.focus?.({ preventScroll: true });
    devolverFoco = null;
  });

  const doHash = () => {
    const slug = decodeURIComponent(location.hash.slice(1));
    if (!slug) {
      fechar();
      return;
    }
    const linha = root.querySelector(`[data-slug="${CSS.escape(slug)}"]`);
    if (!linha) return;
    abrir(slug, {
      titulo: linha.dataset.titulo,
      dataCurta: linha.querySelector("time")?.textContent?.trim(),
    });
  };

  window.addEventListener("popstate", doHash);
  doHash();
}
