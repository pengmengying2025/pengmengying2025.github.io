#!/usr/bin/env python3
"""Regenerate the self-hosted font subsets in assets/fonts/.

Run this after adding Chinese text to the site, then commit assets/fonts/:

    python3 scripts/build_fonts.py

It reads the Chinese characters from the site's source files, so there is nothing
to edit by hand. The first run creates a private virtual environment and downloads
the source fonts into ~/.cache/academic-homepage-fonts; the repo only gets the
rewritten .woff2 files. Output is reproducible: unchanged text gives identical files.
"""

import io
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "fonts"
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "academic-homepage-fonts"
VENV = CACHE / "venv"
REQUIREMENTS = ["fonttools==4.60.2", "brotli==1.2.1"]  # 4.60 is the newest that still runs on the macOS system Python

# Source fonts come from this exact commit of github.com/google/fonts (SIL OFL).
FONTS_COMMIT = "fbe81817505e8aeadc53cc7a38a2b76fb57c333e"

CJK = re.compile("[⺀-鿿豈-﫿︰-﹏＀-￯]")

# Text set in the heading font: site and page titles, CV section titles,
# Markdown headings and product names.
HEADING_TEXT = [
    re.compile(r"^\s*(?:-\s*)?title:\s*(.+)$", re.M),
    re.compile(r"^#+\s+(.+)$", re.M),
    re.compile(r'class="product-name"[^>]*>(.*?)</(?:strong|a)>'),
]

LATIN = [
    *range(0x20, 0x7F),
    *range(0xA0, 0x100),
    0x131,
    0x152,
    0x153,
    0x2013,
    0x2014,
    0x2018,
    0x2019,
    0x201A,
    0x201C,
    0x201D,
    0x201E,
    0x2022,
    0x2026,
    0x2039,
    0x203A,
    0x20AC,
    0x2122,
    *range(0x2190, 0x2194),
    0x2212,
]
# Headings only need ASCII and typographic punctuation, which keeps this file small.
LATIN_HEADING = [*range(0x20, 0x7F), 0xA0, 0xB7, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D]

FEATURES = ["kern", "liga", "calt", "ccmp", "locl", "mark", "mkmk", "tnum", "case"]
NAME_IDS = [0, 1, 2, 3, 4, 5, 6, 13, 14]  # keeps the copyright and license inside each file, as the OFL asks


def run_in_private_venv():
    """Re-launch this script inside the cached virtual environment."""
    if Path(sys.prefix).resolve() == VENV.resolve():
        return
    python = VENV / "bin" / "python"
    if not python.exists():
        print("Creating the font tools environment (first run only)...")
        CACHE.mkdir(parents=True, exist_ok=True)
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV)])
    subprocess.check_call(
        [str(python), "-m", "pip", "install", "--quiet", "--disable-pip-version-check", *REQUIREMENTS]
    )
    os.execv(str(python), [str(python), str(Path(__file__).resolve())])


def source_font(path):
    """Return the local copy of a font from the pinned commit, downloading it if needed."""
    target = CACHE / "src" / FONTS_COMMIT[:12] / Path(path).name
    if not target.exists():
        print(f"Downloading {target.name}...")
        target.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://github.com/google/fonts/raw/{FONTS_COMMIT}/{path.replace('[', '%5B').replace(']', '%5D')}"
        partial = target.with_name(target.name + ".part")
        subprocess.check_call(["curl", "-fsSL", "--retry", "3", "-o", str(partial), url])
        partial.rename(target)
    return target


def site_characters():
    """Return the Chinese characters used anywhere on the site, and those used in headings."""
    files = [ROOT / "_config.yml", *ROOT.glob("_pages/*.md"), *ROOT.glob("_data/*.yml"), *ROOT.glob("_bibliography/*.bib")]
    every, headings = set(), set()
    for file in files:
        text = file.read_text(encoding="utf-8")
        every.update(CJK.findall(text))
        for pattern in HEADING_TEXT:
            for match in pattern.findall(text):
                headings.update(CJK.findall(match))
    return sorted(every), sorted(headings)


def build(out_name, source, axes, unicodes):
    from fontTools.subset import Options, Subsetter
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    font = instancer.instantiateVariableFont(TTFont(source_font(source), recalcTimestamp=False), axes)
    # Round-trip so gvar is rebuilt consistently before subsetting.
    buffer = io.BytesIO()
    font.save(buffer)
    buffer.seek(0)
    font = TTFont(buffer, recalcTimestamp=False)
    if "gvar" in font:
        for glyph in font.getGlyphOrder():
            font["gvar"].variations.setdefault(glyph, [])

    options = Options()
    options.flavor = "woff2"
    options.layout_features = FEATURES
    options.name_IDs = NAME_IDS
    options.notdef_outline = True
    options.hinting = False
    subsetter = Subsetter(options)
    subsetter.populate(unicodes=unicodes)
    subsetter.subset(font)
    font.flavor = "woff2"
    path = OUT / out_name
    font.save(path)
    print(f"  {out_name:26} {path.stat().st_size / 1024:5.1f} KB")


def main():
    run_in_private_venv()
    every, headings = site_characters()
    print(f"Chinese characters on the site: {len(every)}, in headings: {len(headings)} ({''.join(headings)})")
    body = [ord(c) for c in every]
    heading = [ord(c) for c in headings]
    build("inter-var.woff2", "ofl/inter/Inter[opsz,wght].ttf", {"opsz": 14, "wght": (400, 600)}, LATIN)
    build("inter-italic.woff2", "ofl/inter/Inter-Italic[opsz,wght].ttf", {"opsz": 14, "wght": 400}, LATIN)
    build("newsreader-var.woff2", "ofl/newsreader/Newsreader[opsz,wght].ttf", {"opsz": 40, "wght": (500, 600)}, LATIN_HEADING)
    build("noto-sans-sc-var.woff2", "ofl/notosanssc/NotoSansSC[wght].ttf", {"wght": (400, 600)}, body)
    build("noto-serif-sc-var.woff2", "ofl/notoserifsc/NotoSerifSC[wght].ttf", {"wght": (500, 600)}, heading)
    print(f"Done. Commit {OUT.relative_to(ROOT)}/ if it changed.")


if __name__ == "__main__":
    main()
