"""
Builds one labelled contact sheet from the PNGs of ui/godot/tools/contact_sheet.gd.
usage: python ui/tools/montage.py <png_dir> <out.png> [columns]
"""
import os
import sys
from PIL import Image, ImageDraw

src, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 5
names = sorted(f[:-4] for f in os.listdir(src) if f.endswith(".png"))
# keep the order of presets/library.json if available
lib = os.path.join(os.path.dirname(__file__), "..", "godot", "presets", "library.json")
if os.path.exists(lib):
    import json
    order = [p["name"] for p in json.load(open(lib))["presets"]]
    if set(names) <= set(order):
        names = [n for n in order if n in names]
imgs = [Image.open(os.path.join(src, n + ".png")).convert("RGB") for n in names]
imgs = [im.resize((im.width // 2, im.height // 2)) for im in imgs]
w, h = imgs[0].size
rows = (len(imgs) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * h), "white")
for i, (n, im) in enumerate(zip(names, imgs)):
    x, y = (i % cols) * w, (i // cols) * h
    sheet.paste(im, (x, y))
    ImageDraw.Draw(sheet).text((x + 8, y + 6), n, fill=(0, 0, 0))
sheet.save(out)
print("WROTE", out, sheet.size)
