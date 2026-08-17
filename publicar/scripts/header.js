export function initHeader(header) {
  const toggle = header.querySelector(".menu-toggle");
  const nav = header.querySelector(".site-nav");
  const compact = window.matchMedia("(width < 800px)");

  const sentinel = document.createElement("div");
  sentinel.setAttribute("aria-hidden", "true");
  sentinel.style.cssText = "position:absolute;top:0;height:1px;width:1px;";
  document.body.prepend(sentinel);

  new IntersectionObserver(([entry]) => {
    header.dataset.scrolled = String(!entry.isIntersecting);
  }).observe(sentinel);

  if (!toggle || !nav) return;

  const linksDoMenu = () => [...nav.querySelectorAll("a[href]")];

  const setOpen = (open) => {
    toggle.setAttribute("aria-expanded", String(open));
    nav.hidden = !open;

    if (open) linksDoMenu()[0]?.focus();
  };

  const close = ({ refocus = false } = {}) => {
    if (toggle.getAttribute("aria-expanded") !== "true") return;
    setOpen(false);
    if (refocus) toggle.focus();
  };

  const syncToViewport = () => {

    if (compact.matches) {
      setOpen(false);
    } else {
      nav.hidden = false;
      toggle.setAttribute("aria-expanded", "false");
    }
  };

  syncToViewport();
  compact.addEventListener("change", syncToViewport);

  toggle.addEventListener("click", () => {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close({ refocus: true });
  });

  nav.addEventListener("keydown", (event) => {
    if (event.key !== "Tab" || !compact.matches || nav.hidden) return;
    const links = linksDoMenu();
    if (!links.length) return;

    const primeiro = links[0];
    const ultimo = links[links.length - 1];

    if (event.shiftKey && document.activeElement === primeiro) {
      event.preventDefault();
      toggle.focus();
    } else if (!event.shiftKey && document.activeElement === ultimo) {
      event.preventDefault();
      toggle.focus();
    }
  });

  document.addEventListener("pointerdown", (event) => {
    if (!compact.matches) return;
    if (!header.contains(event.target)) close();
  });

  nav.addEventListener("click", (event) => {
    if (compact.matches && event.target.closest("a")) close();
  });
}
