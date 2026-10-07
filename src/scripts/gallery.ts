import PhotoSwipeLightbox from 'photoswipe/lightbox';
import 'photoswipe/style.css';

const DESKTOP_PADDING = { top: 20, bottom: 40, left: 100, right: 100 };
const MOBILE_PADDING = { top: 0, bottom: 0, left: 0, right: 0 };

// Lightbox images are AVIF; browsers without AVIF (Safari before 16) get the WebP fallback.
// Whether AVIF works is seen from which source the browser picked for a thumbnail.
let avif: boolean | undefined;
function supportsAvif(): boolean | undefined {
  if (avif === undefined) {
    const loaded = Array.from(document.querySelectorAll<HTMLImageElement>('ids-gallery img')).find((img) => img.currentSrc);
    if (loaded) avif = /\.avif(\?|$)/.test(loaded.currentSrc);
  }
  return avif;
}

class IdsGallery extends HTMLElement {
  lightbox?: PhotoSwipeLightbox;

  connectedCallback() {
    this.classList.add('ids__gallery');
    const lightbox = new PhotoSwipeLightbox({
      gallery: this,
      children: 'a',
      pswpModule: () => import('photoswipe'),
      paddingFn: (viewportSize) => (viewportSize.x < 768 ? MOBILE_PADDING : DESKTOP_PADDING),
    });

    lightbox.addFilter('itemData', (itemData) => {
      const link = itemData.element as HTMLAnchorElement | undefined;
      if (link?.dataset.pswpFallback && supportsAvif() === false) {
        itemData.src = link.dataset.pswpFallback;
      }
      return itemData;
    });

    lightbox.on('uiRegister', () => {
      const ui = lightbox.pswp?.ui;
      if (!this.hasAttribute('zoom') && ui) {
        ui.uiElementsData = ui.uiElementsData.filter((el) => el.name !== 'zoom');
      }
    });

    lightbox.init();
    this.lightbox = lightbox;
  }

  disconnectedCallback() {
    this.lightbox?.destroy();
  }
}

if (!customElements.get('ids-gallery')) {
  customElements.define('ids-gallery', IdsGallery);
}
