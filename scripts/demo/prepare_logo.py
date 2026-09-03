"""Turn the logo embedded in the supervisor's Word document into a web asset.

The .docx carries exactly one image: the official "the pulse" wordmark, sitting
on a large white canvas. This trims that canvas to the mark itself, drops the
white to transparency so the logo sits on any surface, and writes both the
light-surface (black) and dark-surface (white) variants the header needs.

    venv/bin/python scripts/demo/prepare_logo.py
"""

from __future__ import annotations

import pathlib
import sys
import zipfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCX = ROOT / "The-Pulse-wording-toutes-pages.docx"
OUT_DIR = ROOT / "new_design" / "public" / "brand"

# The exported PNG is not cleanly white: it carries faint compression speckle
# and vertical banding across the page. A plain "is it pure white" test keeps
# that noise, which both survives into the asset and defeats the crop. So the
# page is anything lighter than PAGE_CUTOFF, ink ramps to fully opaque by
# INK_FLOOR, and only genuinely dark pixels (BBOX_CUTOFF) define the crop box.
PAGE_CUTOFF = 168
INK_FLOOR = 60
BBOX_CUTOFF = 128
MIN_INK_PER_LINE = 4
# A row through the wordmark carries a large share of the densest row's ink; a
# row of scanning banding carries a trace of it. 5% separates the two cleanly.
LINE_DENSITY_RATIO = 0.05
# Shortest unbroken vertical run of dark pixels that counts as a real stroke.
# The thinnest part of the mark -- the pulse line's tail -- is comfortably
# thicker than this; the page banding is single dots.
MIN_INK_RUN = 3
MIN_ALPHA = 45
PADDING = 8


def load_embedded_logo() -> Image.Image:
    with zipfile.ZipFile(DOCX) as archive:
        media = [n for n in archive.namelist() if n.startswith("word/media/")]
        if len(media) != 1:
            raise SystemExit(f"expected one embedded image, found {media}")
        with archive.open(media[0]) as handle:
            return Image.open(handle).convert("RGBA")


def main() -> int:
    if not DOCX.exists():
        print(f"missing {DOCX}")
        return 1

    image = load_embedded_logo()
    pixels = image.load()
    width, height = image.size

    # Knock the white page out to transparency, remembering where the dark ink
    # landed so the crop can be worked out afterwards.
    span = PAGE_CUTOFF - INK_FLOOR
    dark: list[list[int]] = [[] for _ in range(height)]
    for y in range(height):
        row = dark[y]
        for x in range(width):
            r, g, b, a = pixels[x, y]
            luminance = (r + g + b) // 3
            if a == 0 or luminance >= PAGE_CUTOFF:
                pixels[x, y] = (0, 0, 0, 0)
                continue
            # Darkness becomes opacity, so the anti-aliased edges stay smooth
            # instead of turning into a hard 1-bit outline.
            ink = min(255, round((PAGE_CUTOFF - luminance) / span * 255))
            pixels[x, y] = (0, 0, 0, ink)
            if luminance < BBOX_CUTOFF:
                row.append(x)

    # A stray speckle is one dark pixel in its line; a glyph stroke is many. So
    # the crop follows the lines that actually carry the mark, which keeps the
    # scanning artefacts at the page edges out of the box.
    def occupied(counts: list[int]) -> tuple[int, int]:
        peak = max(counts)
        floor = max(MIN_INK_PER_LINE, round(peak * LINE_DENSITY_RATIO))
        hits = [i for i, n in enumerate(counts) if n >= floor]
        return (hits[0], hits[-1]) if hits else (-1, -1)

    min_y, max_y = occupied([len(row) for row in dark])
    if max_y < 0:
        print("no ink found in the embedded image")
        return 1

    # Columns need a different test. The banding on the left margin is dotted,
    # so across the wordmark's rows it accumulates enough dark pixels to clear
    # any density threshold that still admits the thin pulse-line tail on the
    # right. What separates them is continuity: a glyph stroke is an unbroken
    # vertical run, banding is speckle. So a column counts only if it carries a
    # run of at least MIN_INK_RUN touching pixels.
    row_sets = [set(dark[y]) for y in range(min_y, max_y + 1)]
    min_x, max_x = width, -1
    for x in range(width):
        run = 0
        for row in row_sets:
            run = run + 1 if x in row else 0
            if run >= MIN_INK_RUN:
                min_x, max_x = min(min_x, x), max(max_x, x)
                break
    if max_x < 0:
        print("no ink found in the embedded image")
        return 1

    box = (
        max(0, min_x - PADDING),
        max(0, min_y - PADDING),
        min(width, max_x + 1 + PADDING),
        min(height, max_y + 1 + PADDING),
    )
    cropped = image.crop(box)

    # Whatever banding survived inside the crop is faint by construction. Glyph
    # edges are anti-aliased but climb to full opacity within a pixel or two, so
    # clearing everything under MIN_ALPHA removes the artefacts without eating
    # into the mark.
    alpha = cropped.getchannel("A")
    faint = sum(alpha.histogram()[1:MIN_ALPHA])
    cropped.putalpha(alpha.point(lambda v: 0 if v < MIN_ALPHA else v))
    print(f"  cleared {faint} faint pixel(s) below alpha {MIN_ALPHA}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dark_on_light = OUT_DIR / "the-pulse-logo.png"
    cropped.save(dark_on_light, optimize=True)

    # White variant for dark surfaces: same alpha, inverted ink.
    light = Image.new("RGBA", cropped.size, (255, 255, 255, 0))
    light.putalpha(cropped.getchannel("A"))
    light_on_dark = OUT_DIR / "the-pulse-logo-light.png"
    light.save(light_on_dark, optimize=True)

    for path in (dark_on_light, light_on_dark):
        with Image.open(path) as check:
            kb = path.stat().st_size / 1024
            print(f"  {path.relative_to(ROOT)}  {check.size[0]}x{check.size[1]}  {kb:.1f} KB")
    print(f"\naspect ratio {cropped.size[0] / cropped.size[1]:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
