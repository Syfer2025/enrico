function passo(track) {
  const card = track.querySelector(":scope > *");
  if (!card) return track.clientWidth;
  const vao = parseFloat(getComputedStyle(track).columnGap) || 0;
  return card.getBoundingClientRect().width + vao;
}

export function initBookCarousel(section) {
  const track = section.querySelector(".book-carousel__track");
  const botoes = [...section.querySelectorAll(".carousel-btn")];
  if (!track || !botoes.length) return;

  const menosMovimento = window.matchMedia("(prefers-reduced-motion: reduce)");

  const progress = document.createElement("div");
  progress.className = "book-carousel__progress";
  progress.setAttribute("aria-hidden", "true");
  const barra = document.createElement("div");
  barra.className = "book-carousel__progress-bar";
  progress.append(barra);
  section.querySelector(".book-carousel__head")?.after(progress);

  const sincroniza = () => {

    const noInicio = track.scrollLeft <= 1;
    const noFim = track.scrollLeft + track.clientWidth >= track.scrollWidth - 1;
    botoes.forEach((b) => {
      const fim = b.dataset.dir === "next" ? noFim : noInicio;
      b.setAttribute("aria-disabled", String(fim));
    });

    const max = track.scrollWidth - track.clientWidth;
    barra.style.width = `${max > 0 ? (track.scrollLeft / max) * 100 : 0}%`;
  };

  botoes.forEach((botao) => {
    botao.addEventListener("click", () => {
      const sentido = botao.dataset.dir === "next" ? 1 : -1;
      track.scrollBy({
        left: passo(track) * sentido,
        behavior: menosMovimento.matches ? "auto" : "smooth",
      });
    });
  });

  let agendado = 0;
  track.addEventListener(
    "scroll",
    () => {
      if (agendado) return;
      agendado = requestAnimationFrame(() => {
        agendado = 0;
        sincroniza();
      });
    },
    { passive: true }
  );

  new ResizeObserver(sincroniza).observe(track);

  sincroniza();
}
