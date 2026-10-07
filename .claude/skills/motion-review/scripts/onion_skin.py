#!/usr/bin/env python3
"""Pelure d'oignon : superpose N instants d'un passage pour voir trajectoires, arcs et espacement.

Le fond statique est estimé par la médiane des échantillons ; seuls les pixels qui bougent sont
peints, teintés du bleu (début) au rouge (fin). Le centre de masse du mouvement est relié par une
ligne numérotée : des points serrés = lent (ease), des points écartés = rapide.
Un espacement régulier sur une entrée/sortie trahit un mouvement linéaire (mécanique).

Exemple :
    python3 onion_skin.py output/film.mp4 --start 4.0 --end 4.4 --n 10
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import probe, read_frames, label_font  # noqa: E402


def ramp(k, n):
    x = k / max(n - 1, 1)
    return np.array([lerp(40, 235, x), lerp(120, 60, abs(x - 0.5) * 2), lerp(255, 40, x)])


def lerp(a, b, x):
    return a + (b - a) * x


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--n", type=int, default=8, help="nombre d'instants superposés")
    ap.add_argument("--width", type=int, default=540)
    ap.add_argument("--thr", type=float, default=18.0, help="seuil de différence au fond (0–255)")
    ap.add_argument("--roi", default=None,
                    help="zone suivie x0,y0,x1,y1 en fractions de l'image (ex. 0,0.3,1,0.8) : isole l'élément à étudier")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    W, H, fps, dur = probe(a.video)
    w = a.width
    h = int(round(w * H / W / 2)) * 2
    frames = read_frames(a.video, a.start, min(a.end + 1.0 / fps, dur), w, h).astype(np.float32)
    idx = np.linspace(0, len(frames) - 1, a.n).round().astype(int)
    samples = frames[idx]
    bg = np.median(samples, axis=0)
    out = bg * 0.55 + 255 * 0.45            # fond délavé pour faire ressortir les fantômes
    roi = np.ones((h, w), bool)
    if a.roi:
        x0, y0, x1, y1 = (float(v) for v in a.roi.split(","))
        roi[:] = False
        roi[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = True
    cents = []
    for k, fr in enumerate(samples):
        diff = np.abs(fr - bg).max(axis=2)
        mb = ndimage.binary_opening(diff > a.thr, iterations=1) & roi
        m = ndimage.gaussian_filter(mb.astype(np.float32), 0.8)
        alpha = (0.35 + 0.55 * k / max(a.n - 1, 1)) * m
        tinted = fr * 0.6 + ramp(k, a.n) * 0.4
        out = out * (1 - alpha[..., None]) + tinted * alpha[..., None]
        # centre du plus gros objet en mouvement (pas de la moyenne de tout ce qui bouge)
        lab, nl = ndimage.label(mb)
        if nl:
            sizes = ndimage.sum(mb, lab, range(1, nl + 1))
            big = int(np.argmax(sizes)) + 1
            if sizes[big - 1] > 30:
                cy, cx = ndimage.center_of_mass(lab == big)
                cents.append((k, cx, cy))
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    f = label_font(13)
    if len(cents) > 1:
        d.line([(x, y) for _, x, y in cents], fill=(20, 20, 20), width=2)
    for k, x, y in cents:
        c = tuple(int(v) for v in ramp(k, a.n))
        d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=c, outline=(0, 0, 0))
        t = a.start + idx[k] / fps
        d.text((x + 8, y - 7), "%d  %.2fs" % (k + 1, t), fill=(0, 0, 0), font=f)
    if a.roi:
        ys, xs = np.nonzero(roi)
        d.rectangle([xs.min(), ys.min(), xs.max(), ys.max()], outline=(255, 196, 0), width=2)
    d.rectangle([0, 0, w, 22], fill=(20, 20, 20))
    d.text((6, 4), "pelure d'oignon %.2f–%.2f s · %d instants · bleu→rouge = début→fin" % (a.start, a.end, a.n),
           fill=(240, 240, 240), font=f)
    # espacement entre centres : indice d'easing
    if len(cents) > 2:
        sp = [np.hypot(cents[i + 1][1] - cents[i][1], cents[i + 1][2] - cents[i][2]) for i in range(len(cents) - 1)]
        print("espacement des centres (px, échelle %d px) : %s" % (w, " ".join("%.0f" % s for s in sp)))
        if max(sp) > 0 and (max(sp) - min(sp)) / max(sp) < 0.25:
            print("  -> espacement quasi constant : mouvement linéaire, ajouter un easing ?")
    out_path = a.out or os.path.join("build", "review", "onion_%05.2f_%05.2f.png" % (a.start, a.end))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    im.save(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
