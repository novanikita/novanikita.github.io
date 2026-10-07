// Burger menu on phones (the button is hidden by CSS on wider screens)
const header = document.querySelector<HTMLElement>('.site-header');
const toggle = header?.querySelector<HTMLButtonElement>('.menu-toggle');

if (header && toggle) {
  const setOpen = (open: boolean) => {
    header.classList.toggle('is-menu-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', (open ? toggle.dataset.labelClose : toggle.dataset.labelOpen) ?? '');
  };

  toggle.addEventListener('click', () => setOpen(!header.classList.contains('is-menu-open')));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && header.classList.contains('is-menu-open')) {
      setOpen(false);
      toggle.focus();
    }
  });
  window.matchMedia('(min-width: 769px)').addEventListener('change', (event) => {
    if (event.matches) setOpen(false);
  });
}
