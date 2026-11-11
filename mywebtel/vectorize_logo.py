#!/usr/bin/env python3
"""Vectorise un logo bicolore fourni en PNG (une couche bleue, une couche grise) en SVG net, tracé par potrace.

Le PNG fourni est trop petit pour la 1080p : on sépare les deux couleurs, on agrandit chaque masque x8 avec un lissage,
on seuille, puis potrace produit des courbes nettes. Écrit aussi la variante de nuit (gris -> blanc) à côté.
Usage :
  python3 mywebtel/vectorize_logo.py logo-mywebtel.png mywebtel/film/brand/mywebtel-logo.svg          (logo MyWebtel, 490x168)
  python3 mywebtel/vectorize_logo.py logo.png webtel-logo.svg --blue 26,146,248 --grey 80,80,76 --crop 190   (ancien logo Webtel)
"""
import argparse, re, subprocess, tempfile, os
import numpy as np
from PIL import Image, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst")
ap.add_argument("--blue", default="1,152,252"); ap.add_argument("--grey", default="74,73,72")
ap.add_argument("--crop", type=int, default=0, help="garde seulement les N premières lignes (0 = tout)")
ap.add_argument("--night-blue", default="24,163,255", help="bleu de la variante de nuit, un peu plus clair sur fond sombre")
A = ap.parse_args()
rgb = lambda s: tuple(int(v) for v in s.split(","))
BLUE, GREY = rgb(A.blue), rgb(A.grey)
SCALE = 8

src, dst = A.src, A.dst
a = np.asarray(Image.open(src).convert("RGB")).astype(float)
crop = a[:A.crop] if A.crop else a
bg = np.median(np.concatenate([crop[:4].reshape(-1, 3), crop[-4:].reshape(-1, 3)]), 0)   # fond : bandes du haut et du bas


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
night = {"grey": (255, 255, 255), "blue": rgb(A.night_blue)}
body = "".join(f'<g transform="{tr}" fill="rgb{night[n]}" stroke="none" class="{n}">{p}</g>' for n, c, tr, p in paths)
dn = re.sub(r"\.svg$", "-white.svg", dst)
open(dn, "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0} {y0} {x1 - x0} {y1 - y0}">{body}</svg>')
print(dst, dn, x1 - x0, y1 - y0)
