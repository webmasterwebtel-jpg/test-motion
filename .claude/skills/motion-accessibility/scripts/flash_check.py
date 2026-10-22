#!/usr/bin/env python3
"""Détection des flashs à risque photosensible (inspirée du critère WCAG 2.3.1 « trois flashs ou moins »).

Méthode : l'image est découpée en blocs ; pour chaque bloc on suit la luminance relative (sRGB linéarisé).
Une « transition » est un changement d'au moins 10 % de la luminance max, dans un sens puis dans l'autre,
avec un état sombre sous 0,80. Deux transitions opposées = un flash. Un passage est À RISQUE si, dans une
fenêtre glissante d'une seconde, plus de 3 flashs touchent une surface supérieure à --area de l'image.
Les flashs rouges saturés (critère « red flash ») sont comptés à part : ils sont plus dangereux.

Ce n'est pas un test certifié (type Harding/PEAT) : c'est un garde-fou pour repérer les passages à revoir.

Exemples :
    python3 flash_check.py output/film.mp4
    python3 flash_check.py output/film.mp4 --area 0.1 --plot build/review/flash.png
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "motion-review", "scripts"))
from _common import probe, read_frames, label_font  # noqa: E402

DELTA = 0.10       # amplitude minimale d'une transition (fraction de la luminance max)
DARK = 0.80        # l'état le plus sombre doit être sous ce seuil
MAX_FLASHES = 3    # par seconde


def rel_lum(rgb):
    c = rgb.astype(np.float32) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def red_sat(rgb):
    """Composante « rouge saturé » selon la formule WCAG : (R-G-B)*320 si R/(R+G+B) >= 0,8."""
    c = rgb.astype(np.float32) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    s = c.sum(-1) + 1e-6
    ratio = c[..., 0] / s
    return np.where(ratio >= 0.8, np.maximum(c[..., 0] - c[..., 1] - c[..., 2], 0) * 320, 0)


def transitions(series, delta, dark=None):
    """Indices des transitions (zigzag avec hystérésis) d'une série 1D."""
    out, ext, direction = [], series[0], 0      # direction : +1 on monte, -1 on descend, 0 inconnu
    for i in range(1, len(series)):
        v = series[i]
        if direction == 0:
            if abs(v - ext) >= delta:
                direction, ext = (1 if v > ext else -1), v
        elif direction == 1:
            if v > ext:
                ext = v                          # le sommet monte encore
            elif ext - v >= delta:               # retournement : une transition descendante est confirmée
                if dark is None or v < dark:
                    out.append(i)
                direction, ext = -1, v
        else:
            if v < ext:
                ext = v                          # le creux descend encore
            elif v - ext >= delta:               # retournement : une transition montante est confirmée
                if dark is None or ext < dark:
                    out.append(i)
                direction, ext = 1, v
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--area", type=float, default=0.0625,
                    help="part de l'image au-delà de laquelle un flash compte (défaut 1/16, prudent sur mobile)")
    ap.add_argument("--grid", type=int, nargs=2, default=(9, 16), metavar=("COLS", "ROWS"))
    ap.add_argument("--plot", default=None, help="PNG du nombre de flashs par seconde au fil du temps")
    a = ap.parse_args()

    W, H, fps, dur = probe(a.video)
    cols, rows = a.grid
    w, h = cols * 8, rows * 8
    fr = read_frames(a.video, 0, dur, w, h)
    n = len(fr)
    lum = rel_lum(fr).reshape(n, rows, 8, cols, 8).mean(axis=(2, 4))       # n × rows × cols
    red = red_sat(fr).reshape(n, rows, 8, cols, 8).mean(axis=(2, 4))
    win = int(round(fps))
    gen = np.zeros((n, rows, cols), np.int16)
    rf = np.zeros((n, rows, cols), np.int16)
    for r in range(rows):
        for c in range(cols):
            for i in transitions(lum[:, r, c], DELTA, DARK):
                gen[i, r, c] = 1
            for i in transitions(red[:, r, c], 20.0):
                rf[i, r, c] = 1
    # flashs par bloc dans chaque fenêtre d'1 s, puis surface concernée
    k = np.ones(win)
    cg = np.apply_along_axis(lambda s: np.convolve(s, k)[:n], 0, gen) / 2.0
    cr = np.apply_along_axis(lambda s: np.convolve(s, k)[:n], 0, rf) / 2.0
    area_g = (cg > MAX_FLASHES).mean(axis=(1, 2))
    area_r = (cr > MAX_FLASHES).mean(axis=(1, 2))
    worst_g = cg.reshape(n, -1).max(1)
    risky = area_g > a.area
    risky_r = area_r > a.area
    any_flash = (cg >= 1).mean(axis=(1, 2)) > a.area

    trans_lum = gen.sum(axis=(1, 2)) > 0       # images où au moins un bloc bascule en luminance
    trans_red = rf.sum(axis=(1, 2)) > 0        # ... ou en rouge saturé

    def spans(mask, trans):
        """Plages où la fenêtre glissante d'1 s est en alerte, recalées sur les vraies transitions
        (la fenêtre s'étend vers l'arrière : sans ce recalage, le début serait annoncé jusqu'à 1 s trop tôt)."""
        out, i = [], 0
        while i < n:
            if mask[i]:
                j = i
                while j < n and mask[j]:
                    j += 1
                lo, hi = max(i - win, 0), j
                idx = np.nonzero(trans[lo:hi])[0]
                if len(idx):
                    out.append(((lo + idx[0]) / fps, (lo + idx[-1] + 1) / fps))
                i = j
            else:
                i += 1
        return out

    print("== %s · %.1f s · grille %dx%d · seuil de surface %.1f %%" % (os.path.basename(a.video), dur, cols, rows, a.area * 100))
    print("max de flashs/s sur un bloc : %.1f (à %.2f s)" % (worst_g.max(), worst_g.argmax() / fps))
    sg, sr = spans(risky, trans_lum), spans(risky_r, trans_red)
    print("passages À RISQUE (> %d flashs/s sur > %.0f %% de l'image) : %s" % (
        MAX_FLASHES, a.area * 100, ", ".join("%.2f–%.2f s" % s for s in sg) or "aucun"))
    print("flashs rouges saturés à risque : %s" % (", ".join("%.2f–%.2f s" % s for s in sr) or "aucun"))
    # les 3 moments les plus denses (même sans dépasser le seuil) : ce sont eux qu'il faut regarder en premier
    order, tops = np.argsort(-worst_g), []
    for i in order:
        if worst_g[i] < 1:
            break
        if all(abs(i - j) > win for j in tops):
            tops.append(int(i))
        if len(tops) == 3:
            break
    if tops:
        print("moments les plus denses : " + " · ".join("%.2f s (%.0f flash/s sur un bloc, %.0f %% de l'image concernée)" % (
            i / fps, worst_g[i], 100 * (cg[i] >= 1).mean()) for i in tops))
    verdict = "À CORRIGER" if sg or sr else "OK"
    print("verdict : %s" % verdict)
    if a.plot:
        img = Image.new("RGB", (int(dur * 30) + 60, 200), (250, 250, 248))
        d = ImageDraw.Draw(img)
        f = label_font(12)
        X = lambda t: 50 + t * 30  # noqa: E731
        Y = lambda v: 170 - min(v, 8) / 8 * 150  # noqa: E731
        d.line([X(0), Y(MAX_FLASHES), X(dur), Y(MAX_FLASHES)], fill=(220, 60, 60))
        d.text((4, Y(MAX_FLASHES) - 7), "3/s", fill=(220, 60, 60), font=f)
        pts = [(X(i / fps), Y(worst_g[i])) for i in range(n)]
        d.line(pts, fill=(60, 110, 220), width=2)
        for s in range(0, int(dur) + 1, 5):
            d.text((X(s) - 6, 178), "%ds" % s, fill=(90, 90, 90), font=f)
        d.text((50, 6), "flashs/s du bloc le plus touché (bleu) · limite WCAG 2.3.1 (rouge)", fill=(40, 40, 40), font=f)
        os.makedirs(os.path.dirname(a.plot) or ".", exist_ok=True)
        img.save(a.plot)
        print("->", a.plot)
    rep = dict(video=a.video, verdict=verdict, risky=sg, red=sr, max_flash_rate=float(worst_g.max()))
    out = os.path.join("build", "review", "flash_%s.json" % os.path.splitext(os.path.basename(a.video))[0])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(rep, fh)


if __name__ == "__main__":
    main()
