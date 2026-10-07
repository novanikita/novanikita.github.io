import { ui, type Lang } from './i18n';

/** Plain text of a Markdown paragraph */
function plain(markdown: string): string {
  return markdown
    .replace(/^(import|export) .*$/gm, '')
    .replace(/<[^>]+>/g, '')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\\([*_`[\]<>])/g, '$1')
    .replace(/[*_`#>]/g, '')
    .replace(/^\s*[-+]\s+/gm, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function truncate(text: string, limit = 160): string {
  if (text.length <= limit) return text;
  return text.slice(0, limit - 1).replace(/\s+\S*$/, '').replace(/[\s,;:—–-]+$/, '') + '…';
}

/**
 * Description for search results and link previews: the first real paragraph of the text,
 * otherwise the title and the last short line («Сделано в 2026 году»).
 */
export function describe(lang: Lang, title: string, body = ''): string {
  const paragraphs = body.split(/\n\s*\n/).map(plain).filter((p) => p && !p.startsWith('{'));
  const long = paragraphs.find((p) => p.length >= 60);
  if (long) return truncate(long);
  const parts = [title, paragraphs[paragraphs.length - 1]].filter(Boolean);
  return parts.map((p) => p.replace(/\.$/, '') + '.').join(' ') + ' ' + ui[lang].signature;
}
