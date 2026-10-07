// The cat in the footer follows the cursor through its walk cycle
const cat = document.querySelector<HTMLImageElement>('.portfolio-footer__cat img');

if (cat?.dataset.frames) {
  const frames: string[] = JSON.parse(cat.dataset.frames);
  const rest = cat.src;
  let current = rest;
  let preloaded = false;

  const show = (src: string) => {
    if (src === current) return;
    current = src;
    cat.src = src;
  };

  cat.addEventListener('mouseenter', () => {
    if (preloaded) return;
    preloaded = true;
    frames.forEach((src) => (new Image().src = src));
  });
  cat.addEventListener('mousemove', (event) => {
    const rect = cat.getBoundingClientRect();
    const zone = Math.floor(((event.clientX - rect.left) / rect.width) * frames.length);
    show(frames[Math.min(frames.length - 1, Math.max(0, zone))]);
  });
  cat.addEventListener('mouseleave', () => show(rest));
}
