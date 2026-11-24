"""Outline the banner copy in Geist and its title in Instrument Serif.

Run with FontTools and Brotli installed, passing the Latin Geist and
Instrument Serif WOFF2 files in that order. The daily build uses these paths.
"""
import json
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


COPY = {
    "tagline": ("Design · Develop · Deploy", 23, 500, 0),
    "name": ("Lem Fulgencio", 111, 400, -.015),
    "role": ("Full Stack Developer", 30, 650, -.025),
    "stats": ("2+ years building  ·  15+ projects  ·  100+ users served", 24, 500, -.015),
}


def outline(font, label, size, weight, tracking):
    glyphs = font.getGlyphSet(location={"wght": weight} if "fvar" in font else None)
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    position = 0
    paths = SVGPathPen(glyphs, ntos=lambda value: f"{value:.2f}".rstrip("0").rstrip("."))
    bounds = BoundsPen(glyphs)
    for character in label:
        glyph = glyphs[cmap[ord(character)]]
        transform = (scale, 0, 0, -scale, position, 0)
        glyph.draw(TransformPen(paths, transform))
        glyph.draw(TransformPen(bounds, transform))
        position += glyph.width * scale + tracking * size
    left, _, right, _ = bounds.bounds
    return {"label": label, "center": round((left + right) / 2, 2), "path": paths.getCommands()}


if __name__ == "__main__":
    with TTFont(sys.argv[1]) as body_font, TTFont(sys.argv[2]) as title_font:
        heading = {
            key: outline(title_font if key == "name" else body_font, *style)
            for key, style in COPY.items()
        }
    Path(__file__).with_name("heading.json").write_text(
        json.dumps(heading, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
