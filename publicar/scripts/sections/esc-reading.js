const SETA = `
  <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.75"
       stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path d="M6 3.25 10.75 8 6 12.75" />
  </svg>`;

export function initEscReading(section) {
  if (section.dataset.variant !== "d") return;

  const pasta = (section.dataset.src || "assets/data/textos").replace(/\/$/, "");
  const links = [...section.querySelectorAll(".writing-post__link[data-slug]")];
  if (!links.length) return;

  const montar = (link, post) => {
    const li = link.closest(".writing-post");
    if (!li) return;

    const panel = document.createElement("div");
    panel.className = "writing-post__panel";

    const bar = document.createElement("div");
    bar.className = "writing-post__bar";

    const cat = document.createElement("span");
    cat.className = "t-eyebrow writing-post__cat";
    cat.textContent = link.querySelector(".writing-post__cat")?.textContent || "";

    const titulo = document.createElement("a");
    titulo.className = "writing-post__title";
    titulo.href = link.getAttribute("href") || "#";
    titulo.textContent = post.titulo;

    const data = document.createElement("time");
    data.className = "t-footnote writing-post__date tabular";
    data.dateTime = post.data;
    data.textContent =
      link.querySelector(".writing-post__date")?.textContent || "";

    bar.append(cat, titulo, data);

    const corpo = document.createElement("div");
    corpo.className = "esc-item__body writing-post__text";
    const caixa = document.createElement("div");
    caixa.innerHTML = post.conteudo;
    corpo.append(...caixa.childNodes);

    const mais = document.createElement("a");
    mais.className = "writing-post__more";
    mais.href = link.getAttribute("href") || "#";
    mais.innerHTML = "ler completo " + SETA;

    panel.append(bar, corpo, mais);
    link.hidden = true;
    li.append(panel);
  };

  for (const link of links) {
    const slug = link.dataset.slug;
    fetch(`${pasta}/${encodeURIComponent(slug)}.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((post) => montar(link, post))
      .catch((erro) => console.error(`[esc-reading] ${slug}:`, erro));
  }
}
