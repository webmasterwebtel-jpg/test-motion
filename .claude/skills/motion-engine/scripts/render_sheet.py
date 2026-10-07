#!/usr/bin/env python3
"""Rend des images directement depuis le code d'un film (sans encoder la vidéo) et les assemble en planche.

Bien plus rapide qu'un rendu complet pour vérifier une modification : seules les images demandées
sont calculées (flou de mouvement et grain compris, exactement comme dans le film).

Exemples (depuis la racine du dépôt) :
    python3 .claude/skills/motion-engine/scripts/render_sheet.py --range 4 6 0.1
    python3 .claude/skills/motion-engine/scripts/render_sheet.py --times 2.5 2.6 2.7 --scale 0.5
    python3 .claude/skills/motion-engine/scripts/render_sheet.py --film render --range 0 4 0.5
    python3 .claude/skills/motion-engine/scripts/render_sheet.py --range 16 18 0.5 --frames build/review/frames
"""
import argparse, importlib, os, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FILM = None


def _init(motion_dir, film):
    global FILM
    sys.path.insert(0, motion_dir)
    FILM = importlib.import_module(film)
    (getattr(FILM, "load", None) or getattr(FILM, "load_images"))()


def _render(n):
    W, H = FILM.W, FILM.H
    return n, Image.frombytes("RGB", (W, H), FILM.render_frame(n))


def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "assets/fonts/Montserrat-Medium.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--film", default="collage", help="module dans motion/ (collage, render)")
    ap.add_argument("--motion-dir", default="motion")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--times", type=float, nargs="+", help="instants en secondes")
    g.add_argument("--range", type=float, nargs=3, metavar=("DEBUT", "FIN", "PAS"))
    ap.add_argument("--scale", type=float, default=0.2, help="taille des vignettes (1 = 1080 px de large)")
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--bpm", type=float, default=120)
    ap.add_argument("--frames", default=None, help="dossier où enregistrer aussi chaque image en pleine taille")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    motion_dir = os.path.abspath(a.motion_dir)
    sys.path.insert(0, motion_dir)
    mod = importlib.import_module(a.film)
    fps = mod.FPS
    times = a.times or list(np.arange(a.range[0], a.range[1] + 1e-6, a.range[2]))
    frames = sorted({int(round(t * fps)) for t in times})
    with Pool(min(os.cpu_count() or 1, len(frames)), initializer=_init, initargs=(motion_dir, a.film)) as pool:
        imgs = dict(pool.imap_unordered(_render, frames))

    if a.frames:
        os.makedirs(a.frames, exist_ok=True)
        for n, im in imgs.items():
            im.save(os.path.join(a.frames, "%s_f%05d_t%06.3f.png" % (a.film, n, n / fps)))
    tw, th = int(mod.W * a.scale), int(mod.H * a.scale)
    cols = min(a.cols, len(frames))
    rows = (len(frames) + cols - 1) // cols
    pad, lab = 6, 34
    sheet = Image.new("RGB", (pad + cols * (tw + pad), pad + rows * (th + lab + pad)), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    f = font(max(11, int(tw / 15)))
    beat = 60.0 / a.bpm
    for k, n in enumerate(frames):
        x, y = pad + (k % cols) * (tw + pad), pad + (k // cols) * (th + lab + pad)
        sheet.paste(imgs[n].resize((tw, th), Image.LANCZOS), (x, y))
        t = n / fps
        b = t / beat
        on = abs(b - round(b)) * beat * fps < 0.5
        d.text((x + 2, y + th + 2), "%.3fs  #%d" % (t, n), fill=(235, 235, 235), font=f)
        d.text((x + 2, y + th + 17), "mes %d · tps %.3g%s" % (int(b // 4) + 1, b % 4 + 1, " ●" if on else ""),
               fill=(255, 196, 0) if on else (150, 150, 150), font=f)
    out = a.out or os.path.join("build", "review", "render_%s_%06.2f_%06.2f.jpg"
                                % (a.film, frames[0] / fps, frames[-1] / fps))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    sheet.save(out, quality=88)
    print(out, "(%d images rendues)" % len(frames))


if __name__ == "__main__":
    main()
