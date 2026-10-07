import { getCollection, getEntry, render, type CollectionEntry } from 'astro:content';
import type { Lang } from './i18n';
import { HIDDEN_SECTIONS } from './site';

/** Collections that have a page per entry at /<folder>.html */
export type PageCollection = 'projects' | 'travels' | 'meetups' | 'videos' | 'notes';
export const PAGE_COLLECTIONS: PageCollection[] = ['projects', 'travels', 'meetups', 'videos', 'notes'];
export type PageEntry = CollectionEntry<PageCollection>;

/** Not indexed and out of the sitemap: hidden entries and everything in hidden sections */
export function isHidden(collection: PageCollection, entry: PageEntry): boolean {
  return HIDDEN_SECTIONS.has(collection) || Boolean(entry.data.hidden);
}

/** "Soon" entries have a card but no page */
export function hasPage(entry: PageEntry): boolean {
  return !('soon' in entry.data && entry.data.soon);
}

/** Texts of an entry in a language: the English ones come from en.md, falling back to Russian */
export async function textsOf(collection: PageCollection, entry: PageEntry, lang: Lang) {
  const data = entry.data as PageEntry['data'] & { cardTitle?: string; listTitle?: string; meta?: string[] };
  const ru = {
    title: data.title,
    cardTitle: data.cardTitle ?? data.title,
    listTitle: data.listTitle ?? data.title,
    meta: data.meta ?? [],
    description: data.description,
    body: entry.body ?? '',
    translated: lang === 'ru',
  };
  if (lang === 'ru') return { ...ru, entry: entry as PageEntry | CollectionEntry<'translations'> };
  const en = await getEntry('translations', `${collection}/${entry.id}`);
  if (!en) return { ...ru, entry: entry as PageEntry | CollectionEntry<'translations'> };
  return {
    title: en.data.title,
    cardTitle: en.data.cardTitle ?? en.data.title,
    listTitle: en.data.listTitle ?? en.data.title,
    meta: en.data.meta.length ? en.data.meta : ru.meta,
    description: en.data.description,
    body: en.body ?? '',
    translated: true,
    entry: en as PageEntry | CollectionEntry<'translations'>,
  };
}

/** The rendered text of an entry in a language */
export async function contentOf(collection: PageCollection, entry: PageEntry, lang: Lang) {
  const texts = await textsOf(collection, entry, lang);
  const { Content } = await render(texts.entry);
  return { ...texts, Content };
}

/** Entries of a collection in their list order, without hidden ones */
export async function listOf<C extends PageCollection>(collection: C): Promise<CollectionEntry<C>[]> {
  const entries = (await getCollection(collection)) as CollectionEntry<C>[];
  return entries
    .filter((entry) => !entry.data.hidden)
    .sort((a, b) => (a.data as { order: number }).order - (b.data as { order: number }).order);
}

/** Every page at /<folder>.html, for getStaticPaths */
export async function entryPaths() {
  const paths = [];
  for (const collection of PAGE_COLLECTIONS) {
    for (const entry of (await getCollection(collection)) as PageEntry[]) {
      if (hasPage(entry)) paths.push({ params: { slug: entry.id }, props: { collection, entry } });
    }
  }
  return paths;
}
