import { defineCollection, type SchemaContext } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

/** Tags of the portfolio filter. A project with any other tag fails the build. */
export const TAGS = [
  'сайт',
  'промо-кампания',
  'дроп одежды',
  'промышленный дизайн',
  'графика',
  'упаковка',
  'навигация',
  'брендинг',
  'леттеринг',
  'иллюстрация',
  'книга',
  'приложение',
] as const;

/**
 * One folder per entry: src/content/<collection>/<folder>/index.md (or .mdx) + its images.
 * The folder name is the page address: wibes/ → /wibes.html
 */
const byFolder = (collection: string) =>
  glob({
    pattern: '*/index.{md,mdx}',
    base: `./src/content/${collection}`,
    generateId: ({ entry }) => entry.split('/')[0],
  });

const figure = ({ image }: SchemaContext) =>
  z.union([
    z.object({ image: image(), size: z.enum(['M', 'XL']).default('M'), alt: z.string().optional() }),
    // videos live in public/, e.g. "/video/06-06-video.mp4"
    z.object({ video: z.string(), size: z.enum(['M', 'XL']).default('M') }),
  ]);

/** A card in a grid (portfolio, travels, design sundays, videos) */
const card = ({ image }: SchemaContext) =>
  z.object({
    /** Without a cover the card gets the «скоро» placeholder */
    cover: image().optional(),
    size: z.enum(['M', 'L', 'XL']).default('M'),
  });

/** Fields of a page with text on the left and galleries on the right */
const galleryPage = (ctx: SchemaContext) => ({
  title: z.string(),
  /** Title on the card, if it differs from the page title */
  cardTitle: z.string().optional(),
  /** Position in the list, smaller comes first. Leave gaps (10, 20, …) to insert new ones. */
  order: z.number(),
  card: card(ctx),
  /** Taken off the site for now: no card, the page is not indexed */
  hidden: z.boolean().default(false),
  /** No page yet: the card is shown without a link */
  soon: z.boolean().default(false),
  /** Text next to the gallery in caption size (most pages) or normal size */
  textSize: z.enum(['caption', 'normal']).default('caption'),
  /** Groups of figures separated by a large gap */
  galleries: z.array(z.array(figure(ctx))).default([]),
  /** For search results and link previews; by default made from the text */
  description: z.string().optional(),
});

const projects = defineCollection({
  loader: byFolder('projects'),
  schema: (ctx) => z.object({ ...galleryPage(ctx), tag: z.enum(TAGS) }),
});

const travels = defineCollection({
  loader: byFolder('travels'),
  schema: (ctx) => z.object({ ...galleryPage(ctx), year: z.number() }),
});

/** Design Sunday meetups */
const meetups = defineCollection({
  loader: byFolder('meetups'),
  schema: (ctx) => z.object(galleryPage(ctx)),
});

const videos = defineCollection({
  loader: byFolder('videos'),
  schema: (ctx) =>
    z.object({
      title: z.string(),
      cardTitle: z.string().optional(),
      order: z.number(),
      card: card(ctx),
      /** Player address (VK Video or YouTube embed) */
      embed: z.url(),
      hidden: z.boolean().default(false),
      description: z.string().optional(),
    }),
});

const notes = defineCollection({
  loader: byFolder('notes'),
  schema: z.object({
    title: z.string(),
    /** Title in the list of notes, if it differs from the page title */
    listTitle: z.string().optional(),
    order: z.number(),
    /** Lines in italics under the title: date, authors */
    meta: z.array(z.string()).default([]),
    hidden: z.boolean().default(false),
    description: z.string().optional(),
  }),
});

/**
 * English texts: en.md (or en.mdx) next to index.md in any folder above.
 * Only the text is translated; images, order, tags come from index.md.
 * Without en.md the English page shows the Russian text.
 */
const translations = defineCollection({
  loader: glob({
    pattern: '*/*/en.{md,mdx}',
    base: './src/content',
    generateId: ({ entry }) => entry.split('/').slice(0, 2).join('/'),
  }),
  schema: z.object({
    title: z.string(),
    cardTitle: z.string().optional(),
    listTitle: z.string().optional(),
    meta: z.array(z.string()).default([]),
    description: z.string().optional(),
  }),
});

export const collections = { projects, travels, meetups, videos, notes, translations };
