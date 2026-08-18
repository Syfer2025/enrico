import { initHeader } from "./header.js";
import { initPhotoWall } from "./sections/photo-wall.js";
import { initBookCarousel } from "./sections/book-carousel.js";
import { initEpJump } from "./sections/ep-jump.js";
import { initEscApp } from "./sections/esc-app.js";
import { initEscLeitor } from "./sections/esc-leitor.js";
import { initEscShelf } from "./sections/esc-shelf.js";
import { initEscReading } from "./sections/esc-reading.js";
import { initBusca } from "./sections/busca.js";
import { initNewsletter } from "./sections/newsletter.js";
import { initReveal } from "./reveal.js";

const v = new URLSearchParams(location.search).get("escrita");
if (v) document.querySelector(".writing")?.setAttribute("data-variant", v);

const MODULES = {
  header: initHeader,
  "photo-wall": initPhotoWall,
  "book-carousel": initBookCarousel,
  "ep-jump": initEpJump,
  "esc-app": initEscApp,
  "esc-leitor": initEscLeitor,
  "esc-shelf": initEscShelf,
  "esc-reading": initEscReading,
  busca: initBusca,
  newsletter: initNewsletter,
};

for (const element of document.querySelectorAll("[data-module]")) {
  const init = MODULES[element.dataset.module];
  if (!init) continue;

  try {
    init(element);
  } catch (error) {

    console.error(`[${element.dataset.module}] falhou ao inicializar:`, error);
  }
}

try {
  initReveal();
} catch (error) {
  console.error("[reveal] falhou ao inicializar:", error);
}
