import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { PAGE_COLLECTIONS, hasPage, isHidden, type PageEntry } from '../lib/content';
import { HIDDEN_SECTIONS } from '../lib/site';
import { localized } from '../lib/i18n';

// Every page in both languages, without hidden ones and "soon" cards
export const GET: APIRoute = async ({ site }) => {
  const paths = ['/', '/portfolio.html', '/articles.html', '/about.html', '/consultation.html', '/design-sunday.html'];
  if (!HIDDEN_SECTIONS.has('videos')) paths.push('/video.html');
  if (!HIDDEN_SECTIONS.has('travels')) paths.push('/travels.html');
  for (const collection of PAGE_COLLECTIONS) {
    for (const entry of (await getCollection(collection)) as PageEntry[]) {
      if (hasPage(entry) && !isHidden(collection, entry)) paths.push(`/${entry.id}.html`);
    }
  }
  const url = (path: string) => new URL(path, site).href;
  const urls = paths.flatMap((path) => {
    const alternates = ['ru', 'en']
      .map((lang) => `<xhtml:link rel="alternate" hreflang="${lang}" href="${url(localized(path, lang as 'ru' | 'en'))}"/>`)
      .join('');
    return ['ru', 'en'].map(
      (lang) => `  <url><loc>${url(localized(path, lang as 'ru' | 'en'))}</loc>${alternates}</url>`,
    );
  });
  return new Response(
    '<?xml version="1.0" encoding="UTF-8"?>\n' +
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' +
      urls.join('\n') +
      '\n</urlset>\n',
    { headers: { 'Content-Type': 'application/xml' } },
  );
};
