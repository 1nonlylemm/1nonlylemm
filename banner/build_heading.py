"""Outline the banner copy from the portfolio's Geist variable font.

Run with FontTools and Brotli installed, passing the Latin Geist WOFF2 used
by the portfolio. The daily banner build uses the resulting paths offline.
"""
import json
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont


COPY = {
    "tagline": ("Design · Develop · Deploy", 23, 500, 0),
    "name": ("Lem Fulgencio", 114, 650, -.065),
    "role": ("Full Stack Developer", 30, 650, -.025),
    "stats": ("2+ years building  ·  15+ projects  ·  100+ users served", 24, 500, -.015),
}


def outline(font, label, size, weight, tracking):
    glyphs = font.getGlyphSet(location={"wght": weight})
    cmap = font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    position = 0
    paths = SVGPathPen(glyphs, ntos=lambda value: f"{value:.2f}".rstrip("0").rstrip("."))
    for character in label:
        glyph = glyphs[cmap[ord(character)]]
        glyph.draw(TransformPen(paths, (scale, 0, 0, -scale, position, 0)))
        position += glyph.width * scale + tracking * size
    return {"label": label, "width": round(position - tracking * size, 2), "path": paths.getCommands()}


if __name__ == "__main__":
    with TTFont(sys.argv[1]) as font:
        heading = {key: outline(font, *style) for key, style in COPY.items()}
    Path(__file__).with_name("heading.json").write_text(
        json.dumps(heading, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
