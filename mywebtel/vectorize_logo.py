#!/usr/bin/env python3
"""Vectorise le logo Webtel fourni (PNG) en SVG : une couche bleue, une couche grise, tracées par potrace.

Le PNG d'origine (565x250) est trop petit pour la 1080p : on sépare les deux couleurs, on agrandit chaque masque x8
avec un lissage, on seuille, puis potrace produit des courbes nettes. La mention « MYWEBTEL · ESPACE COLLABORATEUR »
n'est pas tracée : elle est réécrite en texte dans le film.
Usage : python3 mywebtel/vectorize_logo.py logo.png mywebtel/film/brand/webtel-logo.svg
"""
import re, subprocess, sys, tempfile, os
import numpy as np
from PIL import Image, ImageFilter

BLUE, GREY = (26, 146, 248), (80, 80, 76)
SCALE = 8

src, dst = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(src).convert("RGB")).astype(float)
crop = a[:190]                                            # au-dessus de la mention texte
bg = np.array([240, 247, 255.0])


def mask(col):
    # part de la couleur dans le pixel (mélange linéaire fond -> couleur), robuste à l'anticrénelage
    d = (crop - bg) @ (np.array(col) - bg) / np.sum((np.array(col) - bg) ** 2)
    other = GREY if col == BLUE else BLUE
    dist_c = np.linalg.norm(crop - (bg + np.clip(d, 0, 1)[..., None] * (np.array(col) - bg)), axis=2)
    m = np.clip(d, 0, 1) * (dist_c < 60)
    return m


paths, box = [], None
for name, col in (("grey", GREY), ("blue", BLUE)):
    m = mask(col)
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((m.shape[1] * SCALE, m.shape[0] * SCALE), Image.BICUBIC)
    im = im.filter(ImageFilter.GaussianBlur(SCALE * 0.45)).point(lambda v: 0 if v > 120 else 255).convert("1")
    with tempfile.TemporaryDirectory() as td:
        bmp = os.path.join(td, "m.bmp"); svg = os.path.join(td, "m.svg")
        im.save(bmp)
        subprocess.run(["potrace", bmp, "-s", "-o", svg, "--turdsize", "40", "--alphamax", "1.0", "--opttolerance", "0.4",
                        "--flat"], check=True)
        s = open(svg).read()
    g = re.search(r"<g transform=\"([^\"]+)\"[^>]*>(.*?)</g>", s, re.S)
    paths.append((name, col, g.group(1), g.group(2)))
    w, h = im.size
ys, xs = np.nonzero((mask(BLUE) + mask(GREY)) > 0.3)
x0, x1, y0, y1 = (xs.min() - 2) * SCALE, (xs.max() + 3) * SCALE, (ys.min() - 2) * SCALE, (ys.max() + 3) * SCALE
body = "".join(f'<g transform="{tr}" fill="rgb{col}" stroke="none" class="{n}">{p}</g>' for n, col, tr, p in paths)
open(dst, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}">{body}</svg>')
print(dst, x1 - x0, y1 - y0)
