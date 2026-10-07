import { getImage } from 'astro:assets';
import type { ImageMetadata } from 'astro';

/** Longest side of the biggest version (the lightbox one). */
const MAX_WIDTH = 2560;
const AVIF_QUALITY = 70;
const FALLBACK_WIDTH = 800;

export interface ResponsiveImage {
  width: number;
  height: number;
  /** AVIF in several widths, the biggest one is `full` */
  avifSrcset: string;
  /** WebP for browsers without AVIF (Safari before 16, a percent or two of visitors), 800 px to keep the site small */
  fallback: string;
  /** Lightbox image */
  full: string;
}

/**
 * Web versions of an image: AVIF at `widths` (only those smaller than the image)
 * plus the full-size version, and a WebP fallback.
 * An AVIF that is already web-sized is used as is, without a second compression.
 */
export async function responsive(src: ImageMetadata, widths = [800, 1600]): Promise<ResponsiveImage> {
  const width = Math.min(src.width, MAX_WIDTH);
  const height = Math.round((src.height * width) / src.width);

  const full =
    src.format === 'avif' && src.width <= MAX_WIDTH
      ? src.src
      : (await getImage({ src, format: 'avif', width, quality: AVIF_QUALITY })).src;

  const steps = widths.filter((w) => w < width);
  const smaller = await Promise.all(
    steps.map((w) => getImage({ src, format: 'avif', width: w, quality: AVIF_QUALITY })),
  );
  const fallback = (await getImage({ src, format: 'webp', width: Math.min(FALLBACK_WIDTH, width), quality: 80 })).src;

  return {
    width,
    height,
    avifSrcset: [...smaller.map((img, i) => `${img.src} ${steps[i]}w`), `${full} ${width}w`].join(', '),
    fallback,
    full,
  };
}

/** A 1200 px JPEG for link previews (messengers and social networks don't read AVIF). */
export async function previewImage(src: ImageMetadata, site: URL): Promise<string> {
  const img = await getImage({ src, format: 'jpg', width: Math.min(1200, src.width), quality: 85 });
  return new URL(img.src, site).href;
}
