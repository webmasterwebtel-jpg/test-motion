"""Pré-traitement des visuels : détourage (fond blanc -> alpha), couleur dominante,
recherche automatique des zones de gros plan (mailles, fleurs, franges)."""
import glob, json, os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "assets", "articles")
OUT = os.path.join(ROOT, "build", "cutouts")
os.makedirs(OUT, exist_ok=True)

COUPLES = {3, 4, 6, 7, 8, 11, 14, 19, 21}


def matte(rgb):
    d = 255.0 - rgb.min(axis=2)                     # distance au blanc
    near = d < 14
    lab, n = ndimage.label(near)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    bg = ndimage.binary_opening(bg, iterations=1, border_value=1)
    soft = np.clip((d - 2.0) / 16.0, 0, 1)          # rampe douce sur les bords
    a = np.where(bg, soft, 1.0)
    a = ndimage.gaussian_filter(a, 0.7)
    a[~bg] = 1.0
    return (a * 255).astype(np.uint8)


def dominant_color(rgb, alpha):
    hsv = np.asarray(Image.fromarray(rgb).convert("HSV")).astype(float)
    m = (alpha > 200) & (hsv[..., 1] > 110) & (hsv[..., 2] > 70)
    # exclure la peau (teintes orange-brun peu saturées)
    skin = (hsv[..., 0] > 3) & (hsv[..., 0] < 30) & (hsv[..., 2] < 225)
    m &= ~skin
    if m.sum() < 500:
        return [40, 40, 40]
    h = hsv[..., 0][m].astype(int)
    hist = np.bincount(h // 8, minlength=32)
    hist = hist + np.roll(hist, 1) + np.roll(hist, -1)
    b = int(hist.argmax())
    sel = m & (np.abs(hsv[..., 0] // 8 - b) <= 1)
    c = rgb[sel].astype(float)
    # prendre les pixels les plus saturés du cluster
    s = hsv[..., 1][sel]
    c = c[s >= np.percentile(s, 60)].mean(0)
    return [int(x) for x in c]


def closeups(rgb, alpha, k=3):
    """Trouve k fenêtres 9:16 riches en texture colorée (hors visage)."""
    H, W = alpha.shape
    g = rgb.astype(float).mean(2)
    tex = np.abs(ndimage.sobel(g, 0)) + np.abs(ndimage.sobel(g, 1))
    hsv = np.asarray(Image.fromarray(rgb).convert("HSV")).astype(float)
    sat = hsv[..., 1] / 255.0
    skin = (hsv[..., 0] > 3) & (hsv[..., 0] < 30) & (hsv[..., 2] < 225)
    score = tex * (0.3 + sat) * (alpha > 128) * (~skin)
    score[: int(H * 0.22)] = 0                     # pas de visage
    cw = int(W * 0.42); ch = int(cw * 16 / 9)
    ii = score.cumsum(0).cumsum(1)
    res = []
    taken = np.zeros_like(alpha, bool)
    for _ in range(k):
        best = None
        for y in range(int(H * 0.2), H - ch, 16):
            for x in range(0, W - cw, 16):
                s = ii[y + ch - 1, x + cw - 1] - ii[y - 1, x + cw - 1] - ii[y + ch - 1, x - 1] + ii[y - 1, x - 1]
                if taken[y + ch // 2, x + cw // 2]:
                    continue
                if best is None or s > best[0]:
                    best = (s, x, y)
        if best is None:
            break
        _, x, y = best
        res.append([x + cw / 2, y + ch / 2, cw])
        taken[y + ch // 4: y + ch - ch // 4, x + cw // 4: x + cw - cw // 4] = True
    return res


def main():
    meta = {}
    for f in sorted(glob.glob(os.path.join(SRC, "*.jpg"))):
        name = os.path.splitext(os.path.basename(f))[0]
        idx = int(name.split("_")[1])
        rgb = np.asarray(Image.open(f).convert("RGB"))
        a = matte(rgb)
        Image.fromarray(np.dstack([rgb, a])).save(os.path.join(OUT, name + ".png"))
        ys, xs = np.nonzero(a > 128)
        meta[idx] = dict(
            file=name + ".png",
            couple=idx in COUPLES,
            bbox=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
            color=dominant_color(rgb, a),
            closeups=closeups(rgb, a),
        )
        print(name, meta[idx]["color"], meta[idx]["bbox"])
    json.dump(meta, open(os.path.join(ROOT, "build", "meta.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
