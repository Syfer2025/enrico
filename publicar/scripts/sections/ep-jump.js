export function initEpJump(nav) {
  const links = Array.from(nav.querySelectorAll(".ep-jump__link"));
  if (!links.length) return;

  const seasons = Array.from(document.querySelectorAll(".ep-season"));
  if (!seasons.length) return;

  const defaultSeason = seasons[0]?.id || "temporada-4";

  function setSeason(targetId, shouldScroll = false) {
    let activeId = targetId;

    if (activeId !== "todas" && !seasons.some((s) => s.id === activeId)) {
      activeId = defaultSeason;
    }

    seasons.forEach((sec) => {
      if (activeId === "todas" || sec.id === activeId) {
        sec.style.display = "";
        sec.classList.remove("reveal-wait");
        sec.classList.add("reveal-in");
      } else {
        sec.style.display = "none";
      }
    });

    links.forEach((link) => {
      const href = link.getAttribute("href") || "";
      const id = href.startsWith("#") ? href.slice(1) : href;
      const isActive = id === activeId;
      link.toggleAttribute("aria-current", isActive);
    });

    if (shouldScroll) {
      const archiveHead = document.querySelector(".ep-archive__head");
      if (archiveHead) {
        const rect = archiveHead.getBoundingClientRect();
        if (rect.top < 0 || rect.bottom > window.innerHeight) {
          archiveHead.scrollIntoView({ behavior: "smooth" });
        }
      }
    }
  }

  links.forEach((link) => {
    link.addEventListener("click", (e) => {
      const href = link.getAttribute("href") || "";
      if (!href.startsWith("#")) return;

      e.preventDefault();
      const targetId = href.slice(1);
      setSeason(targetId, true);

      if (history.replaceState) {
        history.replaceState(null, "", `#${targetId}`);
      } else {
        window.location.hash = targetId;
      }
    });
  });

  function onHashChange() {
    const hash = window.location.hash.slice(1);
    if (hash) {
      setSeason(hash, false);
    } else {
      setSeason(defaultSeason, false);
    }
  }

  window.addEventListener("hashchange", onHashChange);
  onHashChange();
}
