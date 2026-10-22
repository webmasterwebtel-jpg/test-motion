#!/usr/bin/env python3
"""Planche des images fixes rendues par render.js --stills (build/mywebtel/stills/*.jpg)."""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFont
files = sorted(glob.glob("build/mywebtel/stills/*.jpg"))
if len(sys.argv) > 1:
    keep = {"t%06.2f.jpg" % float(x) for x in sys.argv[1].split(",")}
    files = [f for f in files if os.path.basename(f) in keep]
W, H, cols = 640, 360, 2
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * (W + 8) + 8, rows * (H + 30) + 8), (30, 30, 30))
d = ImageDraw.Draw(sheet)
f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
for k, p in enumerate(files):
    im = Image.open(p).resize((W, H), Image.LANCZOS)
    x, y = 8 + (k % cols) * (W + 8), 8 + (k // cols) * (H + 30)
    sheet.paste(im, (x, y))
    d.text((x + 4, y + H + 5), os.path.basename(p)[1:-4] + " s", fill=(230, 230, 230), font=f)
sheet.save("build/mywebtel/stills_sheet.jpg", quality=90)
print("build/mywebtel/stills_sheet.jpg", len(files))
