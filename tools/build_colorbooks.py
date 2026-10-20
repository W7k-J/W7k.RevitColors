"""
Builds Autodesk Color Book (.acb) files and preview PNGs from the palette
definitions in ../palettes/*.json.

Usage:  python tools/build_colorbooks.py
Needs:  Python 3.8+, Pillow for previews (pip install pillow)

Format reference: Revit API Developer's Guide > Advanced Topics > Autodesk Color Book.
Revit shows max 10 colors per page and requires unique color names.
"""
import json
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


if __name__ == "__main__":
    main()
