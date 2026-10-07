#!/usr/bin/env python3
"""Build the site. Run it after adding or editing pages:

  python3 tools/build_site.py            # English: new text is translated online
  python3 tools/build_site.py --offline  # English: translation cache only

1. Images: JPG/PNG referenced by pages become AVIF web versions (tools/optimize_images.py).
2. Russian pages (root *.html) are updated in place:
   - width/height of every image (lazy loading needs them; the layout doesn't jump),
   - alt text for images that have none,
   - description (if it is still the default one), Open Graph/Twitter tags,
     canonical and hreflang links,
   - a hidden h1 on pages without a visible one,
   - the header and footer from partials/, so they are in the HTML and not loaded by JS.
3. English copies in en/ (tools/build_en_site.py).
4. sitemap.xml and robots.txt.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))

import optimize_images  # noqa: E402
from site_common import (  # noqa: E402
    DEFAULT_DESCRIPTION_RU,
    HIDDEN_SECTIONS,
    NOT_INDEXED,
    NOT_TRANSLATED,
    ROOT,
    SECTIONS,
    SITE,
    attr,
    auto_alt,
    describe,
    page_url,
    render_footer,
    render_header,
    short_title,
    title_text,
)

sys.path.insert(0, str(ROOT / ".vendor"))
from bs4 import BeautifulSoup  # noqa: E402
from PIL import Image  # noqa: E402

IMG_TAG = re.compile(r"<img\b[^>]*>")
GALLERY_LINK = re.compile(
    r'(<a href="([^"]+\.(?:avif|jpe?g|png|webp|gif))")(?: data-pswp-width="\d+" data-pswp-height="\d+")?(>\s*<img\b)',
    re.I,
)
HEADER_MOUNT = re.compile(r'<div id="site-header">(?:\s*<header\b.*?</header>\s*)?</div>', re.S)
FOOTER_MOUNT = re.compile(r'<footer id="site-footer"[^>]*>.*?</footer>', re.S)

_sizes: dict[Path, tuple[int, int] | None] = {}


def image_size(page: Path, url: str) -> tuple[int, int] | None:
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or url.startswith("data:"):
        return None
    path = Path(os.path.normpath(page.parent / unquote(parts.path)))
    if path not in _sizes:
        try:
            with Image.open(path) as im:
                w, h = im.size
                if (im.getexif() or {}).get(0x0112, 1) in (5, 6, 7, 8):  # rotated by EXIF
                    w, h = h, w
                _sizes[path] = (w, h)
        except (OSError, ValueError):
            _sizes[path] = None
    return _sizes[path]


def sync_sizes(page: Path, text: str) -> str:
    def img(m: re.Match) -> str:
        tag = m.group(0)
        src = re.search(r'\bsrc="([^"]+)"', tag)
        size = src and image_size(page, src.group(1))
        if not size:
            return tag
        tag = re.sub(r'\s(?:width|height)="\d+"', "", tag)
        return tag.replace(src.group(0), f'{src.group(0)} width="{size[0]}" height="{size[1]}"', 1)

    def link(m: re.Match) -> str:
        size = image_size(page, m.group(2))
        if not size:
            return m.group(0)
        return f'{m.group(1)} data-pswp-width="{size[0]}" data-pswp-height="{size[1]}"{m.group(3)}'

    return GALLERY_LINK.sub(link, IMG_TAG.sub(img, text))


def main_span(text: str) -> tuple[int, int]:
    start = text.find("<main")
    end = text.find("</main>")
    return (start, end) if start != -1 and end != -1 else (0, 0)


def fill_alts(text: str, title: str) -> str:
    """Images in <main> without an alt get "<page title>, изображение N"."""
    start, end = main_span(text)
    counter = 0

    def repl(m: re.Match) -> str:
        nonlocal counter
        counter += 1
        tag = m.group(0)
        if re.search(r"\balt=", tag):
            return tag
        return tag.replace("<img", f'<img alt="{attr(auto_alt(title, counter, "ru"))}"', 1)

    return text[:start] + IMG_TAG.sub(repl, text[start:end]) + text[end:]


def set_meta(text: str, key: str, value: str) -> str:
    pattern = re.compile(r'(<meta\s+(?:name|property)="%s"\s+content=")[^"]*(")' % re.escape(key))
    return pattern.sub(lambda m: m.group(1) + attr(value) + m.group(2), text, count=1)


def update_meta(text: str, page: Path, soup) -> str:
    name = page.name
    text = text.replace("https://nikitanova.ru/", SITE + "/").replace("https://nikitanova.ru\"", SITE + "/\"")
    if name in NOT_INDEXED:
        return text

    title = title_text(soup)
    url = page_url(name, "ru")
    for key, value in (("og:url", url), ("og:locale", "ru_RU"), ("og:title", title),
                       ("twitter:title", title), ("og:image:alt", title)):
        text = set_meta(text, key, value)

    # Descriptions marked data-auto (or still the default one) follow the page content;
    # a hand-written description without data-auto is left alone.
    current = soup.find("meta", attrs={"name": "description"})
    is_auto = current is not None and (current.has_attr("data-auto") or current.get("content") == DEFAULT_DESCRIPTION_RU)
    if is_auto and name not in SECTIONS:
        description = describe(soup, "ru")
        if description:
            for key in ("description", "og:description", "twitter:description"):
                text = set_meta(text, key, description)
            text = re.sub(r'(<meta\s+name="description"\s+content="[^"]*")(?:\s+data-auto)?', r"\1 data-auto", text, count=1)

    text = re.sub(r'\n[ \t]*<link rel="(?:canonical|alternate)"[^>]*>', "", text)
    text = re.sub(r'\n[ \t]*<meta name="robots" content="noindex" data-auto />', "", text)
    robots = '\n    <meta name="robots" content="noindex" data-auto />' if is_hidden(text, name) else ""
    links = (
        robots
        + f'\n    <link rel="canonical" href="{url}" />'
        f'\n    <link rel="alternate" hreflang="ru" href="{url}" />'
        f'\n    <link rel="alternate" hreflang="en" href="{page_url(name, "en")}" />'
        f'\n    <link rel="alternate" hreflang="x-default" href="{url}" />'
    )
    return re.sub(r'(<meta name="viewport"[^>]*>)', lambda m: m.group(1) + links, text, count=1)


def ensure_h1(text: str, title: str) -> str:
    start, end = main_span(text)
    if not end or "<h1" in text[start:end]:
        return text
    return re.sub(r"(<main[^>]*>)", lambda m: f'{m.group(1)}\n      <h1 class="visually-hidden">{attr(title)}</h1>',
                  text, count=1)


_hidden_projects: set[str] | None = None


def hidden_projects() -> set[str]:
    """Pages of projects whose card in portfolio.html has the hidden attribute."""
    global _hidden_projects
    if _hidden_projects is None:
        soup = BeautifulSoup((ROOT / "portfolio.html").read_text(encoding="utf-8"), "html.parser")
        _hidden_projects = {
            a["href"] for item in soup.select(".projects-grid-item[hidden]") for a in item.select("a[href]")
        }
    return _hidden_projects


def is_hidden(text: str, name: str) -> bool:
    return name in HIDDEN_SECTIONS or page_nav(text, name) in HIDDEN_SECTIONS or name in hidden_projects()


def page_nav(text: str, name: str) -> str | None:
    m = re.search(r'<body[^>]*\bdata-nav="([^"]+)"', text)
    if m:
        return m.group(1)
    return name if name in SECTIONS else None


def inject_partials(text: str, name: str) -> str:
    # Templates and 404 have no English copy: their language switch leads to the home page
    links_for = "index.html" if name in NOT_TRANSLATED else name
    nav = page_nav(text, name)
    header = render_header("ru", links_for, nav)
    footer = render_footer("ru", links_for)
    text = HEADER_MOUNT.sub(lambda m: f'<div id="site-header">\n{header}\n    </div>', text, count=1)
    return FOOTER_MOUNT.sub(lambda m: footer, text, count=1)


def build_russian_pages() -> None:
    changed = 0
    for page in sorted(ROOT.glob("*.html")):
        text = original = page.read_text(encoding="utf-8")
        soup = BeautifulSoup(text, "html.parser")
        title = short_title(soup)

        text = sync_sizes(page, text)
        text = fill_alts(text, title)
        text = update_meta(text, page, soup)
        text = ensure_h1(text, title)
        text = inject_partials(text, page.name)

        if text != original:
            page.write_text(text, encoding="utf-8")
            changed += 1
    print(f"Russian pages updated: {changed}")


def write_sitemap() -> None:
    entries = []
    for page in sorted(ROOT.glob("*.html")):
        if page.name in NOT_INDEXED or is_hidden(page.read_text(encoding="utf-8"), page.name):
            continue
        ru, en = page_url(page.name, "ru"), page_url(page.name, "en")
        alternates = f'\n    <xhtml:link rel="alternate" hreflang="ru" href="{ru}"/>'
        locations = [ru]
        if (ROOT / "en" / page.name).exists():
            alternates += f'\n    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>'
            locations.append(en)
        for loc in locations:
            entries.append(f"  <url>\n    <loc>{loc}</loc>{alternates}\n  </url>")
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(entries) + "\n</urlset>\n",
        encoding="utf-8",
    )
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    print(f"sitemap.xml: {len(entries)} URLs")


def main() -> None:
    optimize_images.main()
    build_russian_pages()
    import build_en_site

    build_en_site.main()
    write_sitemap()


if __name__ == "__main__":
    main()
