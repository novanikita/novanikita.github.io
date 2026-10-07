(function () {
  function getPageFilename(pathname) {
    const cleanPath = pathname.split("?")[0].split("#")[0];
    const parts = cleanPath.split("/").filter(Boolean);
    const last = parts.length ? parts[parts.length - 1] : "";
    if (!last || !last.endsWith(".html")) return "index.html";
    return last;
  }

  function applySwitcherLinks() {
    // Pages like 404 set their links in the markup
    if (document.body.hasAttribute("data-lang-static")) return;

    const filename = getPageFilename(window.location.pathname);
    const isEnglishPage = window.location.pathname.indexOf("/en/") !== -1;

    // Both the header and the footer have a switcher.
    document.querySelectorAll(".language-switcher").forEach(function (switcher) {
      const ru = switcher.querySelector('[data-lang="ru"]');
      const en = switcher.querySelector('[data-lang="en"]');
      if (!ru || !en) return;

      ru.setAttribute("href", isEnglishPage ? "../" + filename : filename);
      en.setAttribute("href", isEnglishPage ? filename : "en/" + filename);

      ru.classList.toggle("is-active", !isEnglishPage);
      en.classList.toggle("is-active", isEnglishPage);
    });
  }

  window.initLanguageSwitcher = applySwitcherLinks;
  if (document.readyState !== "loading") {
    applySwitcherLinks();
  } else {
    document.addEventListener("DOMContentLoaded", applySwitcherLinks);
  }
})();
