import PhotoSwipeLightbox from "./lib/photoswipe-lightbox.esm.min.js";

const DESKTOP_PADDING = { top: 20, bottom: 40, left: 100, right: 100 };
const MOBILE_PADDING = { top: 0, bottom: 0, left: 0, right: 0 };

/**
 * PhotoSwipe needs image dimensions. Thumbnails and full images share the same URL,
 * so take them from the already loaded <img> instead of downloading every image up front.
 */
function fillSizeFromThumbnail(itemData, index, lightbox) {
  if (itemData.width && itemData.height) return itemData;

  const img = itemData.element && itemData.element.querySelector("img");
  if (!img) return itemData;

  if (img.naturalWidth && img.naturalHeight) {
    itemData.width = itemData.w = img.naturalWidth;
    itemData.height = itemData.h = img.naturalHeight;
    return itemData;
  }

  // The thumbnail is still lazy: show a viewport-sized placeholder, load it now
  // and rebuild the slide once the real size is known.
  itemData.width = itemData.w = window.innerWidth;
  itemData.height = itemData.h = window.innerHeight;
  img.loading = "eager";
  img.addEventListener(
    "load",
    function () {
      if (lightbox.pswp) lightbox.pswp.refreshSlideContent(index);
    },
    { once: true }
  );
  return itemData;
}

class IdsGallery extends HTMLElement {
  constructor() {
    super();
    this.classList.add("ids__gallery");
  }

  connectedCallback() {
    const lightbox = new PhotoSwipeLightbox({
      gallery: this,
      children: "a",
      pswpModule: () => import("./lib/photoswipe.esm.min.js"),
      paddingFn: (viewportSize) =>
        viewportSize.x < 768 ? MOBILE_PADDING : DESKTOP_PADDING,
    });

    lightbox.addFilter("itemData", (itemData, index) =>
      fillSizeFromThumbnail(itemData, index, lightbox)
    );

    lightbox.on("uiRegister", () => {
      const ui = lightbox.pswp && lightbox.pswp.ui;
      if (!this.getAttribute("zoom") && ui && ui.uiElementsData) {
        ui.uiElementsData = ui.uiElementsData.filter((el) => el.name !== "zoom");
      }
    });

    lightbox.init();
    this.lightbox = lightbox;
  }

  disconnectedCallback() {
    if (this.lightbox) this.lightbox.destroy();
  }
}

if (!customElements.get("ids-gallery")) {
  customElements.define("ids-gallery", IdsGallery);
}
