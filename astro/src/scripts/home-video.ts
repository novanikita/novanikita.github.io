// Home page: the video is drawn into a canvas, scaled to cover it
const video = document.querySelector<HTMLVideoElement>('#background-video');
const canvas = document.querySelector<HTMLCanvasElement>('#background-canvas');
const ctx = canvas?.getContext('2d');

if (video && canvas && ctx) {
  const mobile = window.matchMedia('(max-width: 768px)');
  let started = false;

  const draw = () => {
    if (!video.videoWidth || !video.videoHeight) return;
    const scale = Math.max(canvas.width / video.videoWidth, canvas.height / video.videoHeight);
    const w = video.videoWidth * scale;
    const h = video.videoHeight * scale;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, (canvas.width - w) / 2, (canvas.height - h) / 2, w, h);
  };

  const resize = () => {
    const viewport = window.innerHeight;
    canvas.width = window.innerWidth;
    canvas.height = mobile.matches ? viewport * 0.75 : viewport;
    canvas.style.top = (mobile.matches ? viewport * 0.25 : 0) + 'px';
    draw(); // resizing clears the canvas
  };

  // Draw only when the video has a new frame, not on every screen refresh
  const loop = () => {
    draw();
    if ('requestVideoFrameCallback' in video) video.requestVideoFrameCallback(loop);
    else requestAnimationFrame(loop);
  };

  const start = () => {
    if (started) return;
    started = true;
    video.play().catch(() => {});
    loop();
  };

  resize();
  window.addEventListener('resize', resize);
  if (video.readyState >= 2) start();
  else video.addEventListener('loadeddata', start, { once: true });
}
