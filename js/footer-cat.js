(function () {
  // Walk cycle frames for the five horizontal zones of the image (ping-pong: 2-3-4-3-2).
  const ZONE_FRAMES = [2, 3, 4, 3, 2];
  const REST_FRAME = 1;

  window.initFooterCatAnimation = function initFooterCatAnimation() {
    const footerCatImage = document.querySelector(".portfolio-footer__cat img");
    if (!footerCatImage || footerCatImage.dataset.catAnimationReady === "true") {
      return;
    }

    const defaultSrc = footerCatImage.getAttribute("src");
    const match = defaultSrc && defaultSrc.match(/^(.*cat-)\d+(\.\w+)$/);
    if (!match) {
      return;
    }

    footerCatImage.dataset.catAnimationReady = "true";

    const cat = function (index) {
      return match[1] + index + match[2];
    };

    let currentFrame = REST_FRAME;
    let preloaded = false;

    function showFrame(frame) {
      if (frame === currentFrame) return;
      currentFrame = frame;
      footerCatImage.src = cat(frame);
    }

    footerCatImage.addEventListener("mouseenter", function () {
      if (preloaded) return;
      preloaded = true;
      ZONE_FRAMES.forEach(function (frame) {
        new Image().src = cat(frame);
      });
    });

    footerCatImage.addEventListener("mousemove", function (event) {
      const rect = footerCatImage.getBoundingClientRect();
      const zone = Math.min(
        ZONE_FRAMES.length - 1,
        Math.max(0, Math.floor(((event.clientX - rect.left) / rect.width) * ZONE_FRAMES.length))
      );
      showFrame(ZONE_FRAMES[zone]);
    });

    footerCatImage.addEventListener("mouseleave", function () {
      showFrame(REST_FRAME);
    });
  };
})();
