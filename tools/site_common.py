"""Shared parts of the site build: page metadata and the header/footer partials."""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://nikitanova.com"

TEMPLATES = {"project-blanck.html", "video-blanck.html", "article-blanck.html"}
NOT_TRANSLATED = TEMPLATES | {"404.html"}
NOT_INDEXED = NOT_TRANSLATED
SECTIONS = {"index.html", "portfolio.html", "video.html", "articles.html", "about.html", "travels.html"}
# Sections hidden for now: removed from the menu (partials/header*.partial), their pages get
# noindex and stay out of sitemap.xml, but still open by direct link.
# To bring one back: delete it here and return its menu item to both header partials.
HIDDEN_SECTIONS = {"travels.html", "video.html"}

DEFAULT_DESCRIPTION_RU = (
    "Меня правда зовут Никита. Я дизайнер с опытом менеджера, редактора, "
    "программиста, сценариста и арт‑директора"
)
SIGNATURE = {"ru": "Никита Нова, дизайнер.", "en": "Nikita Nova, designer."}
ALT_WORD = {"ru": "изображение", "en": "image"}
AUTO_ALT = re.compile(r"^(?P<title>.+), (?:изображение|image) (?P<n>\d+)$")
TITLE_SUFFIX = re.compile(r"\s+[—–-]\s+(?:Никит[аá] Нов[аá]|Nikita Nova)\s*$")

PARTIALS = ROOT / "partials"


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace(" ", " ").replace("­", "")).strip()


def page_url(filename: str, lang: str) -> str:
    return SITE + ("/en/" if lang == "en" else "/") + ("" if filename == "index.html" else filename)


def title_text(soup) -> str:
    return clean(soup.title.get_text()) if soup.title else ""


def short_title(soup) -> str:
    """The <title> without the "— Никита Нова" suffix."""
    return TITLE_SUFFIX.sub("", title_text(soup))


def truncate(text: str, limit: int = 160) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:—–-")
    return cut + "…"


def describe(soup, lang: str) -> str | None:
    """A page description: its first real paragraph, or the title and caption."""
    main = soup.find("main")
    if main is None:
        return None
    for p in main.find_all("p"):
        if "caption" in (p.get("class") or []):
            continue
        text = clean(p.get_text())
        if len(text) >= 60:
            return truncate(text)
    parts = [short_title(soup)]
    caption = main.find("p", class_="caption")
    if caption is not None and clean(caption.get_text()):
        parts.append(clean(caption.get_text()))
    return " ".join(part.rstrip(".") + "." for part in parts if part) + " " + SIGNATURE[lang]


def auto_alt(title: str, n: int, lang: str) -> str:
    return f"{title}, {ALT_WORD[lang]} {n}"


def _set_lang_links(markup: str, lang: str, filename: str) -> str:
    links = {
        "ru": ("../" if lang == "en" else "") + filename,
        "en": filename if lang == "en" else "en/" + filename,
    }

    def repl(m: re.Match) -> str:
        code = m.group(1)
        active = ' class="is-active"' if code == lang else ""
        return f'<a href="{links[code]}" data-lang="{code}"{active}>'

    return re.sub(r'<a href="[^"]*" data-lang="(ru|en)"(?: class="is-active")?>', repl, markup)


def render_header(lang: str, filename: str, nav: str | None) -> str:
    name = "header-en.partial" if lang == "en" else "header.partial"
    markup = (PARTIALS / name).read_text(encoding="utf-8").strip()
    if nav:
        markup = markup.replace(
            f'<div><a href="{nav}">', f'<div><a href="{nav}" class="is-nav-active" aria-current="page">', 1
        )
    return _set_lang_links(markup, lang, filename)


def render_footer(lang: str, filename: str) -> str:
    name = "footer-en.partial" if lang == "en" else "footer.partial"
    markup = (PARTIALS / name).read_text(encoding="utf-8").strip()
    markup = markup.replace('<footer class="portfolio-footer">', '<footer id="site-footer" class="portfolio-footer">', 1)
    return _set_lang_links(markup, lang, filename)


def attr(value: str) -> str:
    return html.escape(value, quote=True)
