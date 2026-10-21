"""
Builds Autodesk Color Book (.acb) files and preview PNGs from the palette
definitions in ../palettes/*.json, and preview PNGs for the ready-made
color books in ../ColorBooks/Contributed/*.acb (those .acb files are not rebuilt).

Usage:  python tools/build_colorbooks.py
Needs:  Python 3.8+, Pillow for previews (pip install pillow)

Format reference: Revit API Developer's Guide > Advanced Topics > Autodesk Color Book.
Revit shows max 10 colors per page and requires unique color names.
"""
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
PAGE_SIZE = 10


def rgb8(rgb, ind):
    r, g, b = rgb
    return (f"{ind}<RGB8>\n{ind}  <red>{r}</red>\n{ind}  <green>{g}</green>\n"
            f"{ind}  <blue>{b}</blue>\n{ind}</RGB8>")


def entries(pal):
    """Return [(unique colorName, rgb)], e.g. ('PM01 Coral Rose', (254, 162, 167))."""
    out = [(f"{pal['prefix']}{i + 1:02d} {c['name']}", tuple(c["rgb"]))
           for i, c in enumerate(pal["colors"])]
    names = [n for n, _ in out]
    if len(set(names)) != len(names):
        raise ValueError(f"Duplicate color names in {pal['bookName']}")
    for n, rgb in out:
        if len(rgb) != 3 or not all(0 <= v <= 255 for v in rgb):
            raise ValueError(f"Bad RGB for {n}: {rgb}")
    return out


def build_acb(pal, path):
    cols = entries(pal)
    x = ['<?xml version="1.0" encoding="UTF-8"?>', "<colorBook>",
         f"  <bookName>{escape(pal['bookName'])}</bookName>",
         "  <majorVersion>1</majorVersion>", "  <minorVersion>0</minorVersion>"]
    for p in range(0, len(cols), PAGE_SIZE):
        page = cols[p:p + PAGE_SIZE]
        x += ["  <colorPage>", "    <pageColor>",
              rgb8(page[len(page) // 2][1], "      "), "    </pageColor>"]
        for name, rgb in page:
            x += ["    <colorEntry>", f"      <colorName>{escape(name)}</colorName>",
                  rgb8(rgb, "      "), "    </colorEntry>"]
        x.append("  </colorPage>")
    x += ["</colorBook>", ""]
    path.write_text("\n".join(x), encoding="utf-8")


def _font(size, bold=False):
    from PIL import ImageFont
    names = ["DejaVuSans-Bold.ttf", "arialbd.ttf"] if bold else ["DejaVuSans.ttf", "arial.ttf"]
    for f in names:
        for base in ("", "/usr/share/fonts/truetype/dejavu/", "C:/Windows/Fonts/"):
            try:
                return ImageFont.truetype(base + f, size)
            except OSError:
                pass
    return ImageFont.load_default()


def build_preview(pal, path):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("  (Pillow not installed - skipping preview)")
        return
    cols = entries(pal)
    pages = (len(cols) + PAGE_SIZE - 1) // PAGE_SIZE
    im = Image.new("RGB", (1500, 90 + pages * 295), "white")
    d = ImageDraw.Draw(im)
    fb, f, fs = _font(26, True), _font(17), _font(14)
    d.text((40, 25), f"{pal['bookName']}  -  {len(cols)} colors, {pages} page(s)", fill="black", font=fb)
    titles = [pg.get("title", "") for pg in pal.get("pages", [])]
    for p in range(pages):
        y0 = 90 + p * 295
        title = titles[p] if p < len(titles) else ""
        d.text((40, y0), f"Page {p + 1} · {title}", fill=(60, 60, 60), font=f)
        for k, (name, c) in enumerate(cols[p * PAGE_SIZE:(p + 1) * PAGE_SIZE]):
            x0, y = 40 + k * 143, y0 + 30
            d.rectangle([x0, y, x0 + 128, y + 130], fill=c, outline=(200, 200, 200))
            d.line([x0, y + 160, x0 + 128, y + 160], fill=c, width=4)  # line sample on paper
            code, _, label = name.partition(" ")
            d.text((x0, y + 172), code, fill="black", font=f)
            d.text((x0, y + 194), label, fill="black", font=fs)
            d.text((x0, y + 214), "{},{},{}".format(*c), fill=(90, 90, 90), font=fs)
    im.save(path)


def read_acb(path):
    """Return (bookName, [(colorName, rgb)]) from an existing .acb file."""
    root = ET.parse(path).getroot()
    cols = [(e.findtext("colorName"),
             tuple(int(e.findtext(f"RGB8/{k}")) for k in ("red", "green", "blue")))
            for e in root.iter("colorEntry")]
    return root.findtext("bookName"), cols


def _fit(d, text, font, width):
    """Wrap text into at most 2 lines no wider than width, ellipsis if cut."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if d.textlength(trial, font=font) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] += "…"
    while d.textlength(lines[-1], font=font) > width and len(lines[-1]) > 2:
        lines[-1] = lines[-1][:-2] + "…"
    return lines


def build_acb_preview(acb, path):
    """Compact swatch grid for a contributed .acb (any size)."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("  (Pillow not installed - skipping preview)")
        return
    book, cols = read_acb(acb)
    per_row = 10 if len(cols) <= 150 else 15
    cell_w = 1420 // per_row
    cell_h = 145 if per_row == 10 else 120
    rows = (len(cols) + per_row - 1) // per_row
    im = Image.new("RGB", (1500, 90 + rows * cell_h), "white")
    d = ImageDraw.Draw(im)
    fb, f = _font(26, True), _font(13 if per_row == 10 else 11)
    d.text((40, 25), f"{book}  -  {len(cols)} colors", fill="black", font=fb)
    sw = 70 if per_row == 10 else 56
    for i, (name, c) in enumerate(cols):
        x0, y = 40 + (i % per_row) * cell_w, 80 + (i // per_row) * cell_h
        d.rectangle([x0, y, x0 + cell_w - 12, y + sw], fill=c, outline=(200, 200, 200))
        for j, line in enumerate(_fit(d, name, f, cell_w - 12)):
            d.text((x0, y + sw + 6 + j * 16), line, fill="black", font=f)
        d.text((x0, y + sw + 38), "{},{},{}".format(*c), fill=(110, 110, 110), font=f)
    im.save(path)


def main():
    for src in sorted((ROOT / "palettes").glob("*.json")):
        pal = json.loads(src.read_text(encoding="utf-8"))
        acb = ROOT / "ColorBooks" / f"{pal['bookName']}.acb"
        png = ROOT / "previews" / f"{pal['bookName']}.png"
        acb.parent.mkdir(exist_ok=True)
        png.parent.mkdir(exist_ok=True)
        build_acb(pal, acb)
        build_preview(pal, png)
        print(f"Built {acb.relative_to(ROOT)} ({len(pal['colors'])} colors)")
    for acb in sorted((ROOT / "ColorBooks" / "Contributed").glob("*.acb")):
        png = ROOT / "previews" / "Contributed" / f"{acb.stem}.png"
        png.parent.mkdir(exist_ok=True)
        build_acb_preview(acb, png)
        print(f"Preview {png.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
