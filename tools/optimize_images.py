#!/usr/bin/env python3
"""Turn the images used by the pages into web versions.

For every JPG/PNG/GIF under images/ that a root-level *.html page references
(<img src>, <a href>, data-bg):
  - writes <name>.avif next to it: longest side at most 2560 px, quality 70,
    colour profile kept (CMYK converted to sRGB), EXIF/GPS dropped;
  - moves the original to .originals/ (ignored by git, so it is not published);
  - rewrites the reference in the page.

og:image / twitter:image get a 1200 px JPEG in images/og/, because social
networks and messengers don't read AVIF.

Safe to rerun: already converted images are skipped.

  python3 tools/optimize_images.py
"""
from __future__ import annotations

import io
import os
import re
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from PIL import Image, ImageCms, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ORIGINALS = ROOT / ".originals"
OG_DIR = ROOT / "images" / "og"
SITE = "https://nikitanova.com"

MAX_SIDE = 2560
AVIF_QUALITY = 70
OG_SIDE = 1200
CONVERT_EXT = {".jpg", ".jpeg", ".png", ".gif"}
# Kept as they are: the favicon and the default link preview.
KEEP = {ROOT / "images" / "icon.png", ROOT / "images" / "meta.png"}

ATTR_RE = re.compile(r'\b(src|href|data-bg)="([^"]+)"')
META_IMAGE_RE = re.compile(r'(<meta\s+(?:property="og:image"|name="twitter:image")\s+content=")([^"]+)(")')

SRGB = ImageCms.createProfile("sRGB")
GENERIC_CMYK = "/System/Library/ColorSync/Profiles/Generic CMYK Profile.icc"


def to_rgb(im: Image.Image) -> tuple[Image.Image, bytes | None]:
    """Normalise the colour mode; returns the image and the ICC profile to embed."""
    icc = im.info.get("icc_profile")
    if im.mode == "CMYK":
        source = ImageCms.ImageCmsProfile(io.BytesIO(icc)) if icc else ImageCms.getOpenProfile(GENERIC_CMYK)
        rgb = ImageCms.profileToProfile(im, source, SRGB, outputMode="RGB", renderingIntent=0)
        rgb.info.pop("icc_profile", None)  # the CMYK profile must not travel with the RGB pixels
        return rgb, None
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    im = im.convert("RGBA" if has_alpha else "RGB")
    im.info.pop("icc_profile", None)  # embedded explicitly by the caller
    if has_alpha and im.getchannel("A").getextrema()[0] == 255:
        im = im.convert("RGB")  # fully opaque alpha only costs bytes
    return im, icc


def load(path: Path) -> tuple[Image.Image, bytes | None]:
    with Image.open(path) as src:
        src.load()
        im = ImageOps.exif_transpose(src)
        im.info.setdefault("icc_profile", src.info.get("icc_profile"))
        return to_rgb(im)


def convert_one(job: tuple[str, str]) -> tuple[str, str]:
    src, dst = Path(job[0]), Path(job[1])
    im, icc = load(src)
    im.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    subsampling = "4:2:0" if src.suffix.lower() in (".jpg", ".jpeg") else "4:4:4"
    params = dict(quality=AVIF_QUALITY, speed=6, subsampling=subsampling, max_threads=2)
    if icc:
        params["icc_profile"] = icc
    im.save(dst, "AVIF", **params)
    return job


def make_og(src: Path, dst: Path) -> None:
    im, icc = load(src)
    if im.mode == "RGBA":
        background = Image.new("RGB", im.size, "white")
        background.paste(im, mask=im.getchannel("A"))
        im = background
    im.thumbnail((OG_SIDE, OG_SIDE), Image.LANCZOS)
    params = dict(quality=85, optimize=True, progressive=True)
    if icc:
        params["icc_profile"] = icc
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", **params)


def original_of(path: Path) -> Path:
    """Where the full-size original lives (it may already be moved to .originals/)."""
    backup = ORIGINALS / path.relative_to(ROOT)
    return path if path.exists() else backup


def local_path(page: Path, url: str) -> Path | None:
    if url.startswith(("#", "mailto:", "tel:", "data:", "javascript:")):
        return None
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        return None
    return Path(os.path.normpath(page.parent / unquote(parts.path)))


def main() -> None:
    pages = sorted(ROOT.glob("*.html"))

    # 1. Which images need a web version
    jobs: dict[Path, Path] = {}
    for page in pages:
        for _, url in ATTR_RE.findall(page.read_text(encoding="utf-8")):
            path = local_path(page, url)
            if not path or path.suffix.lower() not in CONVERT_EXT or path in KEEP:
                continue
            if (ROOT / "images") not in path.parents:
                continue
            avif = path.with_suffix(".avif")
            if path.exists() and not avif.exists():
                jobs[path] = avif

    # 2. Link previews, made from the full-size originals before they are moved away
    og_jobs: dict[Path, Path] = {}
    for page in pages:
        for _, url, _ in META_IMAGE_RE.findall(page.read_text(encoding="utf-8")):
            path = ROOT / unquote(urlsplit(url).path).lstrip("/")
            if path in KEEP or OG_DIR in path.parents:
                continue
            target = OG_DIR / (path.stem + ".jpg")
            if target.exists():
                continue
            source = original_of(path)
            if not source.exists():
                print(f"warning: no image for {url} in {page.name}")
                continue
            og_jobs[target] = source
    for target, source in og_jobs.items():
        make_og(source, target)
        print(f"og  {target.relative_to(ROOT)}")

    # 3. AVIF web versions
    if jobs:
        print(f"converting {len(jobs)} images to AVIF…")
        workers = max(1, (os.cpu_count() or 4) // 2)
        with ProcessPoolExecutor(max_workers=workers) as pool:
            for i, _ in enumerate(pool.map(convert_one, [(str(s), str(d)) for s, d in jobs.items()], chunksize=4), 1):
                if i % 100 == 0:
                    print(f"  {i}/{len(jobs)}")
        for src in jobs:
            backup = ORIGINALS / src.relative_to(ROOT)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(backup))

    # 4. Point the pages at the new files
    changed = 0
    for page in pages:
        text = page.read_text(encoding="utf-8")

        def fix_attr(m: re.Match) -> str:
            attr, url = m.group(1), m.group(2)
            path = local_path(page, url)
            if not path or path.suffix.lower() not in CONVERT_EXT or path in KEEP:
                return m.group(0)
            avif = path.with_suffix(".avif")
            if path.exists() or not avif.exists():
                return m.group(0)
            return f'{attr}="{url[: -len(path.suffix)]}.avif"'

        def fix_meta(m: re.Match) -> str:
            path = ROOT / unquote(urlsplit(m.group(2)).path).lstrip("/")
            if path in KEEP or OG_DIR in path.parents:
                return m.group(0)
            target = OG_DIR / (path.stem + ".jpg")
            if not target.exists():
                return m.group(0)
            return m.group(1) + SITE + "/" + quote(str(target.relative_to(ROOT))) + m.group(3)

        new = META_IMAGE_RE.sub(fix_meta, ATTR_RE.sub(fix_attr, text))
        if new != text:
            page.write_text(new, encoding="utf-8")
            changed += 1
    print(f"updated {changed} pages")


if __name__ == "__main__":
    sys.exit(main())
