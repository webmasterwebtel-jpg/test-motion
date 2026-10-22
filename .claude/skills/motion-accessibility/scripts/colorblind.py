#!/usr/bin/env python3
"""Simulation du daltonisme et contrôle de lisibilité en niveaux de gris.

Deux modes :
  1. Images d'une vidéo : planche « original | protanopie | deutéranopie | tritanopie | niveaux de gris »
     pour vérifier que le produit, les fonds et les fils restent distinguables.
  2. Palette : distance de couleur minimale (ΔE CIE76) entre couleurs d'une même palette, avec et sans
     simulation. Une paire sous ΔE 20 se confond facilement ; sous 10, elle est quasi identique.

Simulation : matrices de Machado et al. (2009), sévérité 1.0, appliquées en RGB linéaire.
C'est une approximation (les daltonismes partiels sont plus fréquents que les totaux).

Exemples :
    python3 colorblind.py frames output/film.mp4 --times 5 17 30 45
    python3 colorblind.py palette --project          # YARN du moteur + couleurs signature des 24 looks
    python3 colorblind.py palette --colors "#E6197F" "#00B3A4" "#FFC400"
    python3 colorblind.py contrast "#111111" "#FAF6F0"     # texte sur fond : ratio WCAG
"""
import argparse, itertools, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "motion-review", "scripts"))
from _common import label_font  # noqa: E402

MACHADO = {
    "protanopie": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    "deutéranopie": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    "tritanopie": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}


def to_linear(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255


def simulate(rgb, kind):
    """rgb : tableau (..., 3) en 0–255. kind : clé de MACHADO ou 'gris'."""
    lin = to_linear(rgb.astype(np.float64))
    if kind == "gris":
        y = lin @ np.array([0.2126, 0.7152, 0.0722])
        return to_srgb(np.stack([y, y, y], -1))
    return to_srgb(lin @ MACHADO[kind].T)


def lab(rgb):
    lin = to_linear(np.asarray(rgb, np.float64))
    xyz = lin @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz = xyz / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def delta_e(a, b):
    return float(np.linalg.norm(lab(a) - lab(b)))


def parse(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cmd_frames(a):
    W, H = 270, 480
    cols = ["original", "protanopie", "deutéranopie", "tritanopie", "gris"]
    pad = 6
    sheet = Image.new("RGB", (pad + len(cols) * (W + pad), pad + len(a.times) * (H + 22 + pad)), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    f = label_font(13)
    for r, t in enumerate(a.times):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", a.video, "-frames:v", "1", "-vf",
                              "scale=%d:%d" % (W, H), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                             capture_output=True, check=True).stdout
        im = np.frombuffer(raw, np.uint8).reshape(H, W, 3)
        for c, name in enumerate(cols):
            out = im if name == "original" else simulate(im, "gris" if name == "gris" else name).astype(np.uint8)
            x, y = pad + c * (W + pad), pad + r * (H + 22 + pad)
            sheet.paste(Image.fromarray(out), (x, y))
            d.text((x + 2, y + H + 3), "%s · %.2f s" % (name, t), fill=(225, 225, 225), font=f)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    sheet.save(a.out)
    print(a.out)


def cmd_palette(a):
    named = {}
    if a.project:
        sys.path.insert(0, "motion")
        import render as R
        for i, c in enumerate(R.YARN):
            named["fil %d" % (i + 1)] = c
        if a.looks:
            for k, c in R.LOOK_COLOR.items():
                named["look %02d" % k] = c
    for h in a.colors or []:
        named[h] = parse(h)
    if len(named) < 2:
        sys.exit("il faut au moins deux couleurs (--project ou --colors)")
    names = list(named)
    print("%d couleurs · ΔE CIE76 minimal par paire (seuil d'alerte %.0f)\n" % (len(names), a.min_de))
    worst = {}
    for kind in ["normal"] + list(MACHADO):
        cols = {n: (np.array(named[n]) if kind == "normal" else simulate(np.array(named[n]), kind)) for n in names}
        pairs = sorted(((delta_e(cols[x], cols[y]), x, y) for x, y in itertools.combinations(names, 2)))
        bad = [p for p in pairs if p[0] < a.min_de]
        worst[kind] = pairs[0]
        print("%-13s plus proche : %-10s / %-10s ΔE %5.1f   · %d paire(s) sous le seuil" % (
            kind, pairs[0][1], pairs[0][2], pairs[0][0], len(bad)))
        for dd, x, y in bad[:a.show]:
            print("      ! %-10s %-10s ΔE %5.1f" % (x, y, dd))
    print("\nUne paire confondue n'est un problème que si les deux couleurs portent chacune une information "
          "(ex. deux fils côte à côte qui doivent se distinguer). Une forme, une position ou une luminance "
          "différente suffit à les départager.")


def luminance(rgb):
    return float(to_linear(np.asarray(rgb, np.float64)) @ np.array([0.2126, 0.7152, 0.0722]))


def cmd_contrast(a):
    fg, bg = parse(a.fg), parse(a.bg)
    l1, l2 = sorted((luminance(fg), luminance(bg)), reverse=True)
    ratio = (l1 + 0.05) / (l2 + 0.05)
    print("contraste %s sur %s : %.2f:1" % (a.fg, a.bg, ratio))
    print("  texte courant (≥ 4,5) : %s · grand texte ≥ 24 px ou 19 px gras (≥ 3) : %s · éléments graphiques (≥ 3) : %s" % (
        "OK" if ratio >= 4.5 else "NON", "OK" if ratio >= 3 else "NON", "OK" if ratio >= 3 else "NON"))
    for kind in MACHADO:
        r1, r2 = sorted((luminance(simulate(np.array(fg), kind)), luminance(simulate(np.array(bg), kind))), reverse=True)
        print("  sous %-12s : %.2f:1" % (kind, (r1 + 0.05) / (r2 + 0.05)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("frames", help="planche de simulation sur des images d'une vidéo")
    f.add_argument("video")
    f.add_argument("--times", type=float, nargs="+", required=True)
    f.add_argument("--out", default=os.path.join("build", "review", "colorblind.png"))
    p = sub.add_parser("palette", help="distances de couleur dans une palette")
    p.add_argument("--project", action="store_true", help="couleurs de fil (YARN) du moteur")
    p.add_argument("--looks", action="store_true", help="avec --project : ajoute les 24 couleurs signature")
    p.add_argument("--colors", nargs="*")
    p.add_argument("--min-de", type=float, default=20.0)
    p.add_argument("--show", type=int, default=6)
    c = sub.add_parser("contrast", help="ratio de contraste WCAG texte/fond")
    c.add_argument("fg")
    c.add_argument("bg")
    a = ap.parse_args()
    {"frames": cmd_frames, "palette": cmd_palette, "contrast": cmd_contrast}[a.cmd](a)


if __name__ == "__main__":
    main()
