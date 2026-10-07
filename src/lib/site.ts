/**
 * Sections taken off the site for now: not in the menu, their pages are not indexed
 * and stay out of the sitemap, but still open by direct link.
 * To bring one back: delete it here and add its item to the menu in src/components/Header.astro.
 */
export const HIDDEN_SECTIONS = new Set<string>(['videos', 'travels']);
