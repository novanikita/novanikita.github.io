(function () {
  function getPageFilename(pathname) {
    const cleanPath = pathname.split("?")[0].split("#")[0];
    const parts = cleanPath.split("/").filter(Boolean);
    const last = parts.length ? parts[parts.length - 1] : "";
    if (!last || !last.endsWith(".html")) return "index.html";
    return last;
  }

  // The section a page belongs to comes from <body data-nav="portfolio.html">;
  // section pages themselves (portfolio.html, video.html, …) match by filename.
  window.initActiveNav = function initActiveNav() {
    const nav = document.querySelector(".site-header .main-page-nav");
    if (!nav) return;

    const activeTarget = document.body.dataset.nav || getPageFilename(window.location.pathname);

    nav.querySelectorAll(":scope > div:not(.language-switcher) > a").forEach(function (link) {
      const href = link.getAttribute("href") || "";
      const linkFile = href.split("/").pop().split("?")[0];
      const isActive = linkFile === activeTarget;

      link.classList.toggle("is-nav-active", isActive);
      if (isActive) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    });
  };
})();
