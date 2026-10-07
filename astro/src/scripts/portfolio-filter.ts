// Portfolio heading: click a tag to show only its projects, click again to show all
const items = Array.from(document.querySelectorAll<HTMLElement>('.projects-grid-item[data-tag]'));
const buttons = Array.from(document.querySelectorAll<HTMLElement>('[data-tag-name]'));
let active: string | null = null;

function render() {
  items.forEach((item) => item.classList.toggle('is-filtered-out', active !== null && item.dataset.tag !== active));
  buttons.forEach((button) => {
    const isActive = button.dataset.tagName === active;
    button.classList.toggle('is-active', isActive);
    button.setAttribute('aria-pressed', String(isActive));
  });
}

buttons.forEach((button) => {
  const toggle = () => {
    active = active === button.dataset.tagName ? null : (button.dataset.tagName ?? null);
    render();
  };
  button.addEventListener('click', toggle);
  button.addEventListener('keydown', (event) => {
    if (event.key !== 'Enter' && event.key !== ' ') return;
    event.preventDefault();
    toggle();
  });
});
