(function () {
  // Cover images of grid cards are set as backgrounds only when the card gets close to the viewport.
  // (<img> tags already carry loading="lazy" in the markup.)
  function lazyBackgrounds() {
    const items = document.querySelectorAll('[data-bg]');
    if (!items.length) return;

    const applyBg = function (el) {
      const bg = el.getAttribute('data-bg');
      if (!bg) return;
      el.style.backgroundImage = 'url("' + bg + '")';
      el.removeAttribute('data-bg');
    };

    if (!('IntersectionObserver' in window)) {
      items.forEach(applyBg);
      return;
    }

    const observer = new IntersectionObserver(
      function (entries, obs) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          applyBg(entry.target);
          obs.unobserve(entry.target);
        });
      },
      { rootMargin: '300px 0px' }
    );

    items.forEach(function (item) {
      observer.observe(item);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', lazyBackgrounds);
  } else {
    lazyBackgrounds();
  }
})();
