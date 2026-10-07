(function () {
  const isEnglishPage = window.location.pathname.indexOf("/en/") !== -1;
  const root = isEnglishPage ? "../" : "";

  function loadPartial(path) {
    return fetch(path).then(function (response) {
      if (!response.ok) {
        throw new Error("Failed to load " + path);
      }
      return response.text();
    });
  }

  function loadScript(src, initName) {
    return new Promise(function (resolve) {
      if (typeof window[initName] === "function") {
        resolve();
        return;
      }

      const script = document.createElement("script");
      script.src = src;
      script.onload = resolve;
      script.onerror = resolve;
      document.body.appendChild(script);
    });
  }

  function initLanguageSwitcher() {
    if (typeof window.initLanguageSwitcher === "function") {
      window.initLanguageSwitcher();
    }
  }

  // Burger menu on phones (the button is hidden by CSS on wider screens)
  function initMenu() {
    const header = document.querySelector("#site-header .site-header");
    const toggle = header && header.querySelector(".menu-toggle");
    if (!toggle || toggle.dataset.ready === "true") return;
    toggle.dataset.ready = "true";

    const labels = isEnglishPage ? ["Open menu", "Close menu"] : ["Открыть меню", "Закрыть меню"];

    function setOpen(open) {
      header.classList.toggle("is-menu-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", labels[open ? 1 : 0]);
    }

    toggle.addEventListener("click", function () {
      setOpen(!header.classList.contains("is-menu-open"));
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && header.classList.contains("is-menu-open")) {
        setOpen(false);
        toggle.focus();
      }
    });
    window.matchMedia("(min-width: 769px)").addEventListener("change", function (event) {
      if (event.matches) setOpen(false);
    });
  }

  // tools/build_site.py writes the header and footer into the pages; they are only
  // fetched here for pages it hasn't processed yet. Partials and helper scripts load in parallel.
  const mount = document.getElementById("site-header");
  if (mount) {
    const prefilled = Boolean(mount.querySelector("header"));
    if (prefilled) initMenu();
    Promise.all([
      prefilled ? null : loadPartial(root + (isEnglishPage ? "partials/header-en.partial" : "partials/header.partial")),
      loadScript(root + "js/nav-active.js", "initActiveNav"),
    ])
      .then(function (results) {
        if (!prefilled) mount.innerHTML = results[0];
        initMenu();
        if (typeof window.initActiveNav === "function") {
          window.initActiveNav();
        }
        initLanguageSwitcher();
      })
      .catch(function (error) {
        console.error(error);
      });
  }

  const footer = document.getElementById("site-footer");
  if (footer) {
    const prefilled = footer.classList.contains("portfolio-footer");
    Promise.all([
      prefilled ? null : loadPartial(root + (isEnglishPage ? "partials/footer-en.partial" : "partials/footer.partial")),
      loadScript(root + "js/footer-cat.js", "initFooterCatAnimation"),
    ])
      .then(function (results) {
        if (!prefilled) footer.outerHTML = results[0];
        if (typeof window.initFooterCatAnimation === "function") {
          window.initFooterCatAnimation();
        }
        document.dispatchEvent(new CustomEvent("siteFooterLoaded"));
        initLanguageSwitcher();
      })
      .catch(function (error) {
        console.error(error);
      });
  }
})();
