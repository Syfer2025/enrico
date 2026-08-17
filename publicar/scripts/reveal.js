export function initReveal() {
  const still = window.matchMedia("(prefers-reduced-motion: reduce)");
  const items = [...document.querySelectorAll("[data-reveal]")];
  if (!items.length || still.matches) return;

  items.forEach((el) => el.classList.add("reveal-wait"));

  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.remove("reveal-wait");
        entry.target.classList.add("reveal-in");
        io.unobserve(entry.target);
      }
    },
    { rootMargin: "0px 0px -10% 0px" }
  );

  items.forEach((el) => io.observe(el));
}
