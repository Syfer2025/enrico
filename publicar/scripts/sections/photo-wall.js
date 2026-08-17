const ROW_TRAVEL = [0.4, -1.0, 0.7, -0.55];

const baseTiles = new WeakMap();

function shuffle(items) {
  for (let i = items.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }
  return items;
}

function shuffleAcrossRows(rows) {
  const tracks = rows.map((row) => row.querySelector(".wall-row__track"));
  if (tracks.some((track) => !track)) return;

  const counts = tracks.map((track) => track.children.length);
  const all = shuffle(tracks.flatMap((track) => Array.from(track.children)));

  let at = 0;
  tracks.forEach((track, i) => {
    track.replaceChildren(...all.slice(at, at + counts[i]));
    at += counts[i];
  });
}

function tilePitch(tile) {
  const { width } = tile.getBoundingClientRect();
  const margin = parseFloat(getComputedStyle(tile).marginInlineEnd) || 0;
  return width + margin;
}

function cloneTile(tile) {
  const copy = tile.cloneNode(true);
  copy.dataset.clone = "true";
  const img = copy.querySelector("img");
  if (img) {

    img.setAttribute("loading", "eager");
  }
  return copy;
}

function layoutRow(row, index, containerWidth) {
  const track = row.querySelector(".wall-row__track");
  if (!track) return 0;

  let base = baseTiles.get(track);
  if (!base) {
    base = Array.from(track.children);
    baseTiles.set(track, base);
  }

  track.replaceChildren(...base);

  const pitch = tilePitch(base[0]);
  if (!pitch) return 0;

  const travel = pitch * (ROW_TRAVEL[index % ROW_TRAVEL.length] ?? 0.5);
  const start = pitch * -0.8;
  const setWidth = pitch * base.length;

  const needed = containerWidth + Math.abs(travel) + Math.abs(start) + pitch;
  const repeats = Math.ceil(needed / setWidth);

  if (repeats > 1) {
    const fill = document.createDocumentFragment();
    for (let r = 1; r < repeats; r += 1) {
      base.forEach((tile) => fill.appendChild(cloneTile(tile)));
    }
    track.appendChild(fill);
  }

  row.style.setProperty("--tile-pitch", `${pitch.toFixed(2)}px`);

  row.style.setProperty("--row-bias", `${(-Math.abs(travel) / 2).toFixed(2)}px`);
  return travel;
}

export function initPhotoWall(section) {
  const rows = Array.from(section.querySelectorAll(".wall-row"));
  if (!rows.length) return;

  const still = window.matchMedia("(prefers-reduced-motion: reduce)");
  let travels = [];
  let lastWidth = 0;
  let visible = true;
  let frame = 0;

  const place = () => {
    frame = 0;
    const rect = section.getBoundingClientRect();
    const span = window.innerHeight + rect.height;
    if (span <= 0) return;

    const raw = (window.innerHeight - rect.top) / span;
    const progress = Math.min(1, Math.max(0, raw));

    const offset = progress - 0.5;
    rows.forEach((row, i) => {
      row.style.setProperty("--row-x", `${(offset * travels[i]).toFixed(2)}px`);
    });
  };

  const schedule = () => {
    if (frame || !visible) return;
    frame = requestAnimationFrame(place);
  };

  section.style.setProperty("--row-count", String(rows.length));

  if (section.dataset.shuffle !== "false") shuffleAcrossRows(rows);

  const build = () => {
    const width = section.clientWidth;
    travels = rows.map((row, i) => layoutRow(row, i, width));
    lastWidth = width;
    section.dataset.ready = "true";
    if (!still.matches) place();
  };

  build();

  let pendingBuild = 0;
  new ResizeObserver(() => {
    if (Math.abs(section.clientWidth - lastWidth) < 2) return;
    cancelAnimationFrame(pendingBuild);
    pendingBuild = requestAnimationFrame(build);
  }).observe(section);

  new IntersectionObserver(
    ([entry]) => {
      visible = entry.isIntersecting;
      if (visible) schedule();
    },
    { rootMargin: "200px" }
  ).observe(section);

  const listen = () => {
    window.addEventListener("scroll", schedule, { passive: true });
    window.addEventListener("resize", schedule, { passive: true });
  };

  const unlisten = () => {
    window.removeEventListener("scroll", schedule);
    window.removeEventListener("resize", schedule);
    rows.forEach((row) => row.style.setProperty("--row-x", "0px"));
  };

  if (!still.matches) listen();

  still.addEventListener("change", () => (still.matches ? unlisten() : listen()));
}
