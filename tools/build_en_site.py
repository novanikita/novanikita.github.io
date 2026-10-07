#!/usr/bin/env python3
"""Generate English site copies in en/ from root-level *.html.

Normally run as part of tools/build_site.py.

Uses Google Translate via deep-translator, with a JSON cache under .cache/
so reruns are fast. Fixes common BeautifulSoup serialization glitches.

  python3 tools/build_en_site.py            # translate new strings online, then build
  python3 tools/build_en_site.py --offline  # build from the cache only, list untranslated strings

To fix a machine translation, edit its value in .cache/ru_en_translation.json and rebuild.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / ".vendor"
CACHE_PATH = ROOT / ".cache" / "ru_en_translation.json"
EN_DIR = ROOT / "en"

CYR = re.compile(r"[А-Яа-яЁё]")
WS_ONLY = re.compile(r"^\s*$")
SKIP_PARENTS = {"script", "style", "noscript"}

sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from site_common import (  # noqa: E402
    AUTO_ALT,
    NOT_TRANSLATED as SKIP_PAGES,
    SECTIONS,
    auto_alt,
    describe,
    page_url,
    render_footer,
    render_header,
    short_title,
    title_text,
)

from bs4 import BeautifulSoup, Comment, NavigableString  # noqa: E402

OFFLINE = "--offline" in sys.argv[1:]

try:
    from deep_translator import GoogleTranslator
except ImportError as e:
    raise SystemExit(
        "Install dependencies: python3 -m pip install -r tools/requirements.txt"
    ) from e

MISSING: set[str] = set()


def load_cache() -> dict[str, str]:
    if CACHE_PATH.is_file():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding="utf-8")


def translate_one(translator: GoogleTranslator, text: str, cache: dict[str, str]) -> str:
    if text in cache:
        return cache[text]
    stripped = text.strip()
    if not stripped or not CYR.search(text):
        cache[text] = text
        return text
    if OFFLINE:
        MISSING.add(text)
        return text
    for attempt in range(4):
        try:
            out = translator.translate(stripped)
            break
        except Exception:
            if attempt == 3:
                cache[text] = text
                return text
            time.sleep(1.5 * (attempt + 1))
    leading = text[: len(text) - len(text.lstrip())]
    trailing = text[len(text.rstrip()) :]
    result = f"{leading}{out}{trailing}"
    cache[text] = result
    time.sleep(0.12)
    return result


def rewrite_url(url: str) -> str:
    if not url:
        return url
    if url.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return url
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        return url
    path = parts.path
    if path.startswith("../"):
        return url
    if path.endswith(".html"):
        return Path(path).name
    return "../" + path.lstrip("/")


def collect_strings(soup: BeautifulSoup) -> set[str]:
    found: set[str] = set()
    for node in soup.find_all(string=True):
        parent = node.parent
        if parent is None or parent.name in SKIP_PARENTS or isinstance(node, Comment):
            continue
        s = str(node)
        if WS_ONLY.match(s) or not CYR.search(s):
            continue
        found.add(s)
    for tag in soup.find_all(True):
        for attr in ("alt", "title", "placeholder", "content"):
            v = tag.get(attr)
            if isinstance(v, str) and CYR.search(v):
                found.add(v)
    if soup.title:
        tt = soup.title.get_text()
        if tt and CYR.search(tt):
            found.add(tt)
    return found


def apply_translations(soup: BeautifulSoup, cache: dict[str, str], translator: GoogleTranslator) -> None:
    for node in soup.find_all(string=True):
        parent = node.parent
        if parent is None or parent.name in SKIP_PARENTS or isinstance(node, Comment):
            continue
        s = str(node)
        if WS_ONLY.match(s) or not CYR.search(s):
            continue
        new_s = translate_one(translator, s, cache)
        if new_s != s:
            node.replace_with(NavigableString(new_s))

    for tag in soup.find_all(True):
        for attr in ("alt", "title", "placeholder", "content"):
            v = tag.get(attr)
            if isinstance(v, str) and CYR.search(v):
                tag[attr] = translate_one(translator, v, cache)

    if soup.title:
        t = soup.title.get_text()
        if t and CYR.search(t):
            soup.title.clear()
            soup.title.append(translate_one(translator, t, cache))


def fix_asset_urls(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(True):
        for attr in ("href", "src", "poster", "data-bg"):
            v = tag.get(attr)
            if isinstance(v, str):
                tag[attr] = rewrite_url(v)


TITLE_METAS = (("property", "og:title"), ("name", "twitter:title"), ("property", "og:image:alt"))
DESCRIPTION_METAS = (("name", "description"), ("property", "og:description"), ("name", "twitter:description"))


def find_meta(soup: BeautifulSoup, kind: str, key: str):
    return soup.find("meta", attrs={kind: key})


def prepare(soup: BeautifulSoup) -> dict:
    """Take out what is generated rather than translated, so it is never sent to the translator.

    The header/footer come from the English partials; auto alt texts, the hidden h1, title-based
    meta tags and auto descriptions are rebuilt from the translated page in finish().
    """
    state: dict = {"alts": [], "hidden_h1": None, "auto_description": False}
    body = soup.body
    state["nav"] = body.get("data-nav") if body else None

    description = find_meta(soup, "name", "description")
    state["auto_description"] = description is not None and description.has_attr("data-auto")

    header = soup.find(id="site-header")
    if header is not None:
        header.clear()
    footer = soup.find(id="site-footer")
    if footer is not None:
        footer.clear()

    for img in soup.find_all("img", alt=True):
        m = AUTO_ALT.match(img["alt"])
        if m:
            state["alts"].append((img, int(m.group("n"))))
            img["alt"] = ""
    h1 = soup.find("h1", class_="visually-hidden")
    if h1 is not None:
        state["hidden_h1"] = h1
        h1.clear()
    for kind, key in TITLE_METAS:
        tag = find_meta(soup, kind, key)
        if tag is not None:
            tag["content"] = ""
    if state["auto_description"]:
        for kind, key in DESCRIPTION_METAS:
            tag = find_meta(soup, kind, key)
            if tag is not None:
                tag["content"] = ""
    return state


def finish(soup: BeautifulSoup, state: dict, name: str) -> None:
    """Fill in the English versions of everything prepare() took out."""
    title = short_title(soup)
    for img, n in state["alts"]:
        img["alt"] = auto_alt(title, n, "en")
    if state["hidden_h1"] is not None:
        state["hidden_h1"].string = title
    for kind, key in TITLE_METAS:
        tag = find_meta(soup, kind, key)
        if tag is not None:
            tag["content"] = title_text(soup)
    if state["auto_description"]:
        description = describe(soup, "en")
        for kind, key in DESCRIPTION_METAS:
            tag = find_meta(soup, kind, key)
            if tag is not None:
                tag["content"] = description

    url = page_url(name, "en")
    for tag in soup.find_all("meta", attrs={"property": "og:locale"}):
        tag["content"] = "en_US"
    for tag in soup.find_all("meta", attrs={"property": "og:url"}):
        tag["content"] = url
    for tag in soup.find_all("link", rel="canonical"):
        tag["href"] = url

    nav = state["nav"] or (name if name in SECTIONS else None)
    header = soup.find(id="site-header")
    if header is not None:
        header.append(BeautifulSoup(render_header("en", name, nav), "html.parser"))
    footer = soup.find(id="site-footer")
    if footer is not None:
        footer.replace_with(BeautifulSoup(render_footer("en", name), "html.parser"))


def postprocess_html(html: str) -> str:
    html = html.replace("</link>", "")
    html = html.replace("</meta>", "")
    return html


def build_one(path: Path, translator: GoogleTranslator, cache: dict[str, str]) -> None:
    raw = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")

    if soup.html is not None:
        soup.html["lang"] = "en"

    state = prepare(soup)
    apply_translations(soup, cache, translator)
    fix_asset_urls(soup)
    finish(soup, state, path.name)

    out = postprocess_html(str(soup))
    EN_DIR.mkdir(parents=True, exist_ok=True)
    (EN_DIR / path.name).write_text(out, encoding="utf-8")


def main() -> None:
    translator = None if OFFLINE else GoogleTranslator(source="ru", target="en")
    cache = load_cache()

    html_files = sorted(p for p in ROOT.glob("*.html") if p.is_file() and p.name not in SKIP_PAGES)
    if not html_files:
        print("No HTML files at repo root.")
        return

    # Pass 1: fill translation cache from all pages
    all_strings: set[str] = set()
    for p in html_files:
        soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
        prepare(soup)
        all_strings |= collect_strings(soup)

    pending = [s for s in sorted(all_strings, key=len) if s not in cache and CYR.search(s)]
    print(f"Unique Russian strings: {len(all_strings)}, pending translate: {len(pending)}")

    for i, s in enumerate(pending):
        translate_one(translator, s, cache)
        if (i + 1) % 50 == 0:
            save_cache(cache)
            print(f"  translated {i + 1}/{len(pending)}")

    save_cache(cache)

    # Pass 2: write en/*.html
    for p in html_files:
        build_one(p, translator, cache)
        print(f"wrote en/{p.name}")

    # English copies of pages that no longer exist (or are templates)
    sources = {p.name for p in html_files}
    for stale in sorted(EN_DIR.glob("*.html")):
        if stale.name not in sources:
            stale.unlink()
            print(f"removed en/{stale.name}")

    save_cache(cache)
    if MISSING:
        print(f"\n{len(MISSING)} strings are not translated yet (left in Russian):")
        for s in sorted(MISSING, key=len):
            print("  " + json.dumps(s, ensure_ascii=False))
    print("Done.")


if __name__ == "__main__":
    main()
