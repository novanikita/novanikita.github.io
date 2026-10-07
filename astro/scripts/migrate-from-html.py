#!/usr/bin/env python3
"""One-off move of the old hand-written pages into Astro content folders.

  src/content/<collection>/<folder>/index.md(x)  + images   (Russian, from <page>.html)
  src/content/<collection>/<folder>/en.md(x)                (English texts, from en/<page>.html)

Collections: projects (portfolio.html), notes (articles.html), videos (video.html),
travels (travels.html), meetups (design-sunday.html).

Run from astro/:  python3 scripts/migrate-from-html.py
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ASTRO = Path(__file__).resolve().parents[1]
OLD = ASTRO.parent
sys.path.insert(0, str(OLD / ".vendor"))

from bs4 import BeautifulSoup, Comment, NavigableString, Tag  # noqa: E402

CONTENT = ASTRO / "src" / "content"
PUBLIC_VIDEO = ASTRO / "public" / "video"
LANG = "ru"  # language of the page being converted, for internal links
AUTO_ALT = re.compile(r", (?:изображение|image) \d+$")
TITLE_SUFFIX = re.compile(r"\s+[—–-]\s+(?:Никит[аá] Нов[аá]|Nikita Nova)\s*$")
MDX_NOTES = {"how-did-designers-come-about"}  # notes with galleries in the text

# Cards without a page have no file name to reuse
SOON_SLUGS = {
    "Сайт flowerdog": "flowerdog", "Oneweek": "oneweek", "Plate": "plate", "Design Atlas": "design-atlas",
    "Лендинг для Яндекс. Директа": "yandex-direct", "Календарь на 2026 год": "calendar-2026", "ONS club": "ons-club",
    "Сеул": "seoul", "Шанхай": "shanghai", "Пекин": "beijing", "Екатеринбург": "yekaterinburg", "Тюмень": "tyumen",
    "Кронштадт": "kronstadt", "Беларусь": "belarus", "Звенигород": "zvenigorod", "Коломна": "kolomna",
}


def soup_of(path: Path) -> BeautifulSoup:
    return BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(" ", " ")).strip()


def yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def text_of(tag: Tag) -> str:
    return re.sub(r"[ \t\r\n]+", " ", tag.get_text()).strip()


def escape_md(text: str, mdx: bool) -> str:
    text = re.sub(r"([*_`\[\]<>])", r"\\\1", text)
    if mdx:
        text = text.replace("{", "\\{").replace("}", "\\}")
    return text


def inline_md(node, mdx: bool = False) -> str:
    """Inline HTML → Markdown (links, emphasis); anything unusual stays as HTML."""
    if isinstance(node, Comment):
        return ""
    if isinstance(node, NavigableString):
        return escape_md(re.sub(r"[ \t\r\n]+", " ", str(node)), mdx)
    inner = "".join(inline_md(child, mdx) for child in node.children)
    if node.name == "a":
        href = node.get("href", "")
        if href.startswith("../"):
            href = href[2:]
        elif href and not re.match(r"^(https?:|mailto:|/|#)", href):
            href = ("/en/" if LANG == "en" else "/") + href
        return f"[{inner.strip()}]({href})"
    if node.name in ("b", "strong"):
        return f"**{inner.strip()}**"
    if node.name in ("i", "em"):
        return f"*{inner.strip()}*"
    if node.name == "br":
        return "<br />" if mdx else "<br>"
    if node.name == "code":
        return f"`{node.get_text()}`"
    return str(node)


def block_text(tag: Tag, mdx: bool = False) -> str:
    text = "".join(inline_md(child, mdx) for child in tag.children).strip()
    # a paragraph starting with "2025." or "- " must not turn into a list
    return re.sub(r"^(\d+)\. ", r"\1\\. ", re.sub(r"^([-+]) ", r"\\\1 ", text))


def list_md(tag: Tag, mdx: bool = False) -> str:
    marker = "1." if tag.name == "ol" else "-"
    return "\n".join(f"{marker} {block_text(li, mdx)}" for li in tag.find_all("li", recursive=False))


def copy_file(src: Path, folder: Path, name: str | None = None) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (name or src.name)
    shutil.copy2(src, target)
    return "./" + target.name


def copy_video(src: Path) -> str:
    PUBLIC_VIDEO.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, PUBLIC_VIDEO / src.name)
    return f"/video/{src.name}"


def write(path: Path, fields: list[tuple[str, str]], body: str = "") -> None:
    lines = ["---"]
    for key, value in fields:
        lines.append(f"{key}:{value}" if value.startswith("\n") else f"{key}: {value}")
    lines.append("---")
    text = "\n".join(lines) + "\n"
    if body.strip():
        text += "\n" + body.strip() + "\n"
    path.write_text(text, encoding="utf-8")


def fresh(collection: str, slug: str) -> Path:
    folder = CONTENT / collection / slug
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    return folder


def page_title(soup: BeautifulSoup) -> str:
    return TITLE_SUFFIX.sub("", soup.title.get_text().strip()) if soup.title else ""


# ---------------------------------------------------------------- cards and gallery pages

def cards_of(listing: BeautifulSoup):
    """Cards of a grid page: (card element, href or None, title, size, cover path)."""
    for card in listing.select(".projects-grid-item"):
        link = card.select_one("a.project-promo-link")
        if link is None:
            continue  # a text block in the grid, not a card
        promo = card.select_one(".project-promo, .video-promo")
        size = next((c for c in card.get("class", []) if c in ("L", "XL")), "M")
        yield card, link.get("href"), card.find("h2").get_text().strip(), size, promo["data-bg"]


def slug_for(href: str | None, title: str) -> str:
    return href[:-5] if href else SOON_SLUGS[norm(title)]


def text_blocks(info: Tag) -> tuple[str, str]:
    """Markdown of the text next to a gallery, and whether it is in caption size."""
    blocks = []
    for child in info.find_all(recursive=False):
        if child.name == "h1":
            continue
        if child.name in ("ul", "ol"):
            blocks.append(list_md(child))
        elif child.name == "p":
            blocks.append(block_text(child))
        else:
            blocks.append(str(child))
    paragraphs = [c for c in info.find_all(recursive=False) if c.name == "p"]
    size = "normal" if paragraphs and not all("caption" in (p.get("class") or []) for p in paragraphs) else "caption"
    return "\n\n".join(b for b in blocks if b), size


def galleries_yaml(page: BeautifulSoup, folder: Path) -> str | None:
    lines = []
    for gallery in page.select(".project-gallery ids-gallery"):
        first = True
        for figure in gallery.find_all("figure", recursive=False):
            size = "XL" if "XL" in (figure.get("class") or []) else "M"
            prefix = "  - - " if first else "    - "
            video = figure.find("video")
            if video is not None:
                source = video.get("src") or video.find("source")["src"]
                lines.append(f"{prefix}video: {copy_video(OLD / source)}")
            else:
                a, img = figure.find("a"), figure.find("img")
                src = a["href"] if a is not None else img["src"]
                lines.append(f"{prefix}image: {copy_file(OLD / src, folder)}")
                alt = img.get("alt", "") if img is not None else ""
                if alt and not AUTO_ALT.search(alt):
                    lines.append(f"      alt: {yaml_str(alt)}")
            if size != "M":
                lines.append(f"      size: {size}")
            first = False
    return "\n" + "\n".join(lines) if lines else None


def migrate_grid(collection: str, listing_file: str, extra=None) -> int:
    """Projects, travels, meetups: a grid of cards, each with a gallery page."""
    listing = soup_of(OLD / listing_file)
    listing_en = soup_of(OLD / "en" / listing_file)
    en_titles = [title for _, _, title, _, _ in cards_of(listing_en)]
    count = 0
    for index, (card, href, card_title, size, cover_path) in enumerate(cards_of(listing)):
        slug = slug_for(href, card_title)
        folder = fresh(collection, slug)
        cover = None if cover_path.endswith("soon-cover.avif") else copy_file(OLD / cover_path, folder, "cover" + Path(cover_path).suffix)

        title, body, text_size, galleries = card_title, "", "caption", None
        if href:
            page = soup_of(OLD / href)
            info = page.select_one(".sticky-project-info")
            title = info.find("h1").get_text().strip()
            body, text_size = text_blocks(info)
            galleries = galleries_yaml(page, folder)

        fields = [("title", yaml_str(title))]
        if norm(card_title) != norm(title):
            fields.append(("cardTitle", yaml_str(card_title)))
        if extra:
            fields += extra(card)
        fields.append(("order", str((index + 1) * 10)))
        fields.append(("card", f"\n  size: {size}" + (f"\n  cover: {cover}" if cover else "")))
        if card.has_attr("hidden"):
            fields.append(("hidden", "true"))
        if not href:
            fields.append(("soon", "true"))
        if text_size != "caption":
            fields.append(("textSize", text_size))
        if galleries:
            fields.append(("galleries", galleries))
        write(folder / "index.md", fields, body)

        # English texts
        en_card = en_titles[index] if index < len(en_titles) else card_title
        en_fields, en_body = [("title", yaml_str(en_card))], ""
        if href and (OLD / "en" / href).exists():
            global LANG
            LANG = "en"
            info = soup_of(OLD / "en" / href).select_one(".sticky-project-info")
            en_title = info.find("h1").get_text().strip()
            en_fields = [("title", yaml_str(en_title))]
            if norm(en_card) != norm(en_title):
                en_fields.append(("cardTitle", yaml_str(en_card)))
            en_body, _ = text_blocks(info)
            LANG = "ru"
        write(folder / "en.md", en_fields, en_body)
        count += 1
    return count


def travel_year(card: Tag) -> list[tuple[str, str]]:
    heading = card.find_parent("div", class_="projects-grid").find_previous_sibling("h1")
    return [("year", heading.get_text().strip())]


# ---------------------------------------------------------------- videos

def migrate_videos() -> int:
    listing = soup_of(OLD / "video.html")
    en_titles = [title for _, _, title, _, _ in cards_of(soup_of(OLD / "en" / "video.html"))]
    count = 0
    for index, (card, href, card_title, size, cover_path) in enumerate(cards_of(listing)):
        page = soup_of(OLD / href)
        folder = fresh("videos", href[:-5])
        title = page_title(page)
        fields = [("title", yaml_str(title))]
        if norm(card_title) != norm(title):
            fields.append(("cardTitle", yaml_str(card_title)))
        fields += [
            ("order", str((index + 1) * 10)),
            ("card", f"\n  size: {size}\n  cover: {copy_file(OLD / cover_path, folder, 'cover' + Path(cover_path).suffix)}"),
            ("embed", yaml_str(page.find("iframe")["src"])),
        ]
        write(folder / "index.md", fields)

        en_page = soup_of(OLD / "en" / href)
        en_title, en_card = page_title(en_page), en_titles[index]
        en_fields = [("title", yaml_str(en_title))]
        if norm(en_card) != norm(en_title):
            en_fields.append(("cardTitle", yaml_str(en_card)))
        write(folder / "en.md", en_fields)
        count += 1
    return count


# ---------------------------------------------------------------- notes

def gallery_mdx(gallery: Tag, folder: Path, offset: int) -> tuple[str, int]:
    items, images = [], 0
    for figure in gallery.find_all("figure"):
        a, img = figure.find("a"), figure.find("img")
        src = (a["href"] if a is not None else img["src"]).removeprefix("../")
        name = copy_file(OLD / src, folder)
        size = ", size: 'XL'" if "XL" in (figure.get("class") or []) else ""
        items.append(f"  {{ image: images['{name}']{size} }},")
        images += 1
    offset_prop = f" offset={{{offset}}}" if offset else ""
    return "<Gallery figures={[\n" + "\n".join(items) + f"\n]}} title={{frontmatter.title}} lang={{lang}} context=\"note\"{offset_prop} />", images


def note_body(wrapper: Tag, folder: Path, mdx: bool, copy_media: bool) -> tuple[list[str], list[str]]:
    """Meta lines and Markdown blocks of a note."""
    meta, blocks = [], []
    started = False  # the text begins after the first M space under the title
    offset = 0
    for child in [c for c in wrapper.children if isinstance(c, Tag)]:
        classes = child.get("class") or []
        if child.name == "h1":
            continue
        if not started:
            if child.name == "i":
                meta.append(text_of(child))
                continue
            if "ids__space" in classes:
                started = started or "M" in classes
                continue
        if "ids__space" in classes:
            blocks.append(f'<div class="{" ".join(classes)}" />' if mdx else f'<div class="{" ".join(classes)}"></div>')
        elif child.name == "p" and "loud" in classes:
            blocks.append(f'<p class="loud">{block_text(child, mdx)}</p>' if mdx else f'<p class="loud">{child.decode_contents().strip()}</p>')
        elif child.name == "p":
            blocks.append(block_text(child, mdx))
        elif child.name in ("h2", "h3", "h4"):
            blocks.append("#" * int(child.name[1]) + " " + block_text(child, mdx))
        elif child.name in ("ul", "ol"):
            blocks.append(list_md(child, mdx))
        elif child.name == "i":
            blocks.append(f"*{block_text(child, mdx)}*")
        elif child.name == "img":
            src = child["src"].removeprefix("../")
            name = copy_file(OLD / src, folder) if copy_media else "./" + Path(src).name
            blocks.append(f"![{child.get('alt', '')}]({name})")
        elif child.name == "video":
            source = (child.get("src") or child.find("source")["src"]).removeprefix("../")
            video = copy_video(OLD / source) if copy_media else "/video/" + Path(source).name
            blocks.append(f'<video src="{video}" autoplay muted loop playsinline></video>')
        elif child.name == "div" and "project-gallery" in classes and mdx:
            gallery, n = gallery_mdx(child.find("ids-gallery"), folder, offset)
            blocks.append(gallery)
            offset += n
        elif child.name == "div" and "card" in classes and mdx:
            inner, _ = note_body_inner(child, mdx)
            blocks.append('<div class="card">\n\n' + "\n\n".join(inner) + "\n\n</div>")
        elif child.name == "div" and child.find("img"):
            for img in child.find_all("img"):
                src = img["src"].removeprefix("../")
                name = copy_file(OLD / src, folder) if copy_media else "./" + Path(src).name
                blocks.append(f"![{img.get('alt', '')}]({name})")
        else:
            blocks.append(str(child))
    return meta, blocks


def note_body_inner(tag: Tag, mdx: bool) -> tuple[list[str], None]:
    blocks = []
    for child in [c for c in tag.children if isinstance(c, Tag)]:
        if child.name in ("h2", "h3", "h4"):
            blocks.append("#" * int(child.name[1]) + " " + block_text(child, mdx))
        elif child.name == "p":
            blocks.append(block_text(child, mdx))
        elif child.name in ("ul", "ol"):
            blocks.append(list_md(child, mdx))
        elif child.name == "i":
            blocks.append(f"*{block_text(child, mdx)}*")
        elif "ids__space" in (child.get("class") or []):
            blocks.append(f'<div class="{" ".join(child.get("class"))}" />')
        else:
            blocks.append(str(child))
    return blocks, None


MDX_HEADER = """import Gallery from '../../../components/Gallery.astro';
export const images = import.meta.glob('./*.{avif,jpg,jpeg,png,webp}', { eager: true, import: 'default' });
export const lang = '%s';
"""


def migrate_notes() -> int:
    listing = soup_of(OLD / "articles.html")
    en_listing = soup_of(OLD / "en" / "articles.html")
    en_list_titles = [a.get_text().strip() for a in en_listing.select(".title-list__title a")]
    count = 0
    for index, a in enumerate(listing.select(".title-list__title a")):
        href = a["href"]
        slug = href[:-5]
        mdx = slug in MDX_NOTES
        ext = "mdx" if mdx else "md"
        folder = fresh("notes", slug)

        global LANG
        for lang in ("ru", "en"):
            LANG = lang
            source = OLD / href if lang == "ru" else OLD / "en" / href
            page = soup_of(source)
            wrapper = page.select_one("main .ids__wrapper")
            title = wrapper.find("h1").get_text().strip()
            meta, blocks = note_body(wrapper, folder, mdx, copy_media=lang == "ru")
            list_title = a.get_text().strip() if lang == "ru" else en_list_titles[index]
            fields = [("title", yaml_str(title))]
            if norm(list_title) != norm(title):
                fields.append(("listTitle", yaml_str(list_title)))
            if lang == "ru":
                fields.append(("order", str((index + 1) * 10)))
            if meta:
                fields.append(("meta", "\n" + "\n".join(f"  - {yaml_str(m)}" for m in meta)))
            body = (MDX_HEADER % lang + "\n" if mdx else "") + "\n\n".join(blocks)
            write(folder / (f"index.{ext}" if lang == "ru" else f"en.{ext}"), fields, body)
        LANG = "ru"
        count += 1
    return count


if __name__ == "__main__":
    print("projects:", migrate_grid("projects", "portfolio.html", extra=lambda card: [("tag", yaml_str(card["data-tag"]))]))
    print("travels:", migrate_grid("travels", "travels.html", extra=travel_year))
    print("meetups:", migrate_grid("meetups", "design-sunday.html"))
    print("videos:", migrate_videos())
    print("notes:", migrate_notes())
