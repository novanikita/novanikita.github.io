(function () {
  // Tag ids are the Russian names used in data-tag / data-tag-name;
  // they stay untranslated on the English copy of the page.
  const TAG_FORMS = {
    ru: {
      "сайт": ["сайт", "сайта", "сайтов"],
      "промо-кампания": ["промо-кампания", "промо-кампании", "промо-кампаний"],
      "дроп одежды": ["дроп одежды", "дропа одежды", "дропов одежды"],
      "промышленный дизайн": ["проект в промышленном дизайне", "проекта в промышленном дизайне", "проектов в промышленном дизайне"],
      "графика": ["графика", "графики", "графики"],
      "упаковка": ["упаковка", "упаковки", "упаковок"],
      "навигация": ["навигация", "навигации", "навигаций"],
      "брендинг": ["брендинг", "брендинга", "брендингов"],
      "леттеринг": ["леттеринг", "леттеринга", "леттерингов"],
      "иллюстрация": ["иллюстрация", "иллюстрации", "иллюстраций"],
      "книга": ["книга", "книги", "книг"],
      "приложение": ["приложение", "приложения", "приложений"]
    },
    en: {
      "сайт": ["website", "websites"],
      "промо-кампания": ["promo campaign", "promo campaigns"],
      "дроп одежды": ["clothing drop", "clothing drops"],
      "промышленный дизайн": ["industrial design project", "industrial design projects"],
      "графика": ["graphics project", "graphics projects"],
      "упаковка": ["packaging project", "packaging projects"],
      "навигация": ["navigation project", "navigation projects"],
      "брендинг": ["branding project", "branding projects"],
      "леттеринг": ["lettering project", "lettering projects"],
      "иллюстрация": ["illustration", "illustrations"],
      "книга": ["book", "books"],
      "приложение": ["app", "apps"]
    }
  };

  const lang = document.documentElement.lang === "en" ? "en" : "ru";
  const forms = TAG_FORMS[lang];

  const pluralFormIndex = lang === "en"
    ? function (count) { return count === 1 ? 0 : 1; }
    : function (count) {
        const mod10 = count % 10;
        const mod100 = count % 100;
        if (mod10 === 1 && mod100 !== 11) return 0;
        if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 1;
        return 2;
      };

  // Items with the hidden attribute are projects taken off the site for now
  const projectItems = Array.from(document.querySelectorAll("[data-tag]:not([hidden])"));
  const tagButtons = Array.from(document.querySelectorAll("code[data-tag-name]"));
  if (!tagButtons.length) return;

  const tagCounts = {};
  projectItems.forEach(function (item) {
    const tag = item.dataset.tag;
    tagCounts[tag] = (tagCounts[tag] || 0) + 1;
  });

  let activeTag = null;

  function render() {
    projectItems.forEach(function (item) {
      item.classList.toggle("is-filtered-out", Boolean(activeTag) && item.dataset.tag !== activeTag);
    });
    tagButtons.forEach(function (button) {
      const isActive = button.dataset.tagName === activeTag;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
  }

  tagButtons.forEach(function (button) {
    const tag = button.dataset.tagName;
    const count = tagCounts[tag] || 0;
    const tagForms = forms[tag] || [tag, tag, tag];
    const label = tagForms[Math.min(pluralFormIndex(count), tagForms.length - 1)];
    button.textContent = count + "\u00A0" + label;

    button.setAttribute("role", "button");
    button.setAttribute("tabindex", "0");
    button.setAttribute("aria-pressed", "false");

    function toggle() {
      activeTag = activeTag === tag ? null : tag;
      render();
    }

    button.addEventListener("click", toggle);
    button.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      toggle();
    });
  });
})();
