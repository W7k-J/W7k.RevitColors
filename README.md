# W7k.RevitColors

Custom **Autodesk Color Books** (`.acb`) for Revit. Use them to mark things on drawings consistently: filled regions, view filters, overrides, markups and legends.

| Color book | Colors | Use it for |
|---|---|---|
| **W7k.Colors.Pastels** | 30 (3 pages) | Soft fills and background marking. You can still read linework over them. |
| **W7k.Colors.ContrastingButUgly** | 20 (2 pages) | When categories must never be confused: clashes, QA checks, temporary markups. |
| **W7k.Colors.OkabeIto** | 8 (1 page) | Color-blind safe marking: drawings and legends that colleagues or clients with color vision deficiency must read. |

## Preview

### W7k.Colors.Pastels
![W7k.Colors.Pastels](previews/W7k.Colors.Pastels.png)

### W7k.Colors.ContrastingButUgly
![W7k.Colors.ContrastingButUgly](previews/W7k.Colors.ContrastingButUgly.png)

### W7k.Colors.OkabeIto
![W7k.Colors.OkabeIto](previews/W7k.Colors.OkabeIto.png)

## Installation

### Option A: Script (recommended)

1. Clone or download this repository.
2. Open PowerShell in the repository folder and run:

   ```powershell
   .\install.ps1              # installs into every Revit version found
   .\install.ps1 -Year 2024   # only Revit 2024
   .\install.ps1 -Uninstall   # removes the W7k color books again
   ```

   If you get an access error, run PowerShell **as Administrator**.

   If scripts are blocked by your execution policy, run this first, for the current session only:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```

3. Restart Revit if it was open.

### Option B: Manual

Copy the files from `ColorBooks\` into:

```
C:\ProgramData\Autodesk\RVT <year>\ColorBooks\
```

For example `C:\ProgramData\Autodesk\RVT 2024\ColorBooks\`. Then restart Revit.

### Using the colors in Revit

1. Open any Revit color picker, for example a filled region's foreground color or a view filter override.
2. Click **Color Books...**.
3. Pick **W7k.Colors.Pastels**, **W7k.Colors.ContrastingButUgly** or **W7k.Colors.OkabeIto** from the dropdown.
4. Browse the pages with the slider. You can also type a color name to jump to it.

Every color has a code (`PM01`–`PM30`, `CU01`–`CU20`, `OI01`–`OI08`). Reference the codes in your office standards and legends instead of RGB values.

## Usage notes

- **Pastels on white sheets:** the lightest pastels (PM05 Peach Cream, PM16 Mint Cream, PM23 Baby Blue, PM28 Lilac Mist) almost disappear as thin lines. Use them for fills only. Pairs such as Seafoam/Mint Cream and Powder Blue/Slate Blue are the closest in the set, so don't give them to adjacent categories.
- **ContrastingButUgly** has no near-white (the paper) and no near-black (default linework), so every color stands out from the drawing itself.
- **OkabeIto** is the only set built for color vision deficiency. Its 8 colors are fixed by the original palette, so if you need more categories, combine them with line patterns or fill patterns instead of adding colors. OI08 Black matches default linework: keep it for fills or emphasis, not for categories drawn as thin lines. OI04 Yellow is weak as a thin line on white paper.
- **Printing:** test-plot a sheet before relying on the colors in printed sets. Plotters and B&W/greyscale PDF exports change the result.

## How the colors were chosen

Both sets were generated in the perceptual **OKLab** color space by maximizing the minimum distance between any two colors (a max-min / farthest-point selection), within limits for each set:

- **Pastels:** lightness 0.79–0.93, chroma 0.05–0.11. The closest pair is about 0.06 ΔE_ok apart.
- **ContrastingButUgly:** the full sRGB gamut, lightness 0.25–0.92. The closest pair is about 0.18 ΔE_ok apart, roughly 3× more separated than the pastels. 20 colors was chosen because adding more shrinks the minimum separation steadily.

**OkabeIto** was not generated: it is the published Okabe-Ito palette (Masataka Okabe & Kei Ito, *Color Universal Design*, 2008) with its standard RGB values, chosen to remain distinguishable under protanopia, deuteranopia and tritanopia.

## Repository structure

```
W7k.RevitColors/
├── ColorBooks/            # .acb files to install (generated)
├── palettes/              # source of truth: one JSON per color book
├── previews/              # swatch sheets (generated)
├── tools/
│   └── build_colorbooks.py
├── install.ps1
└── README.md
```

## Editing or adding a color book

1. Edit a file in `palettes/`, or add a new one. A palette file looks like this:

   ```json
   {
     "bookName": "W7k.Colors.Something",
     "prefix": "XX",
     "pages": [{"title": "Page one"}],
     "colors": [{"name": "Red", "rgb": [255, 0, 0]}]
   }
   ```

2. Rebuild the color books and previews (needs Python 3.8+; Pillow is only needed for the previews):

   ```bash
   pip install pillow
   python tools/build_colorbooks.py
   ```

3. Re-run `install.ps1`.

Rules from the Revit color book format: color names must be unique within a book, Revit shows at most 10 colors per page (the build script paginates automatically), and spaces in file names must be real spaces.

## Reference

Autodesk Color Book format: *Revit API Developer's Guide → Advanced Topics → Autodesk Color Book*
https://help.autodesk.com/view/RVT/2024/ENU/?guid=Revit_API_Revit_API_Developers_Guide_Advanced_Topics_Autodesk_Color_Book_html
