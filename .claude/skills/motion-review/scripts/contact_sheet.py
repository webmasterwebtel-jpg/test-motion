#!/usr/bin/env python3
"""Planche-contact d'une vidéo : une vignette tous les `--step` secondes, annotée (temps, image, mesure.temps).

Sert à « voir » le rythme d'un passage d'un seul coup d'œil : tenues, transitions, densité.

Exemples :
    python3 contact_sheet.py output/film.mp4 --start 16 --end 28 --step 0.25 --bpm 120
    python3 contact_sheet.py output/film.mp4 --step 1 --cols 10 --out build/review/sheet_full.jpg
"""
import argparse, os, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import probe, read_frames, label_font  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None, help="fin (s), défaut : fin de la vidéo")
    ap.add_argument("--step", type=float, default=0.5, help="écart entre vignettes (s) ; 1 temps à 120 BPM = 0.5")
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--thumb", type=int, default=216, help="largeur d'une vignette (px)")
    ap.add_argument("--bpm", type=float, default=None, help="affiche mesure.temps (4/4) sous chaque vignette")
    ap.add_argument("--offset", type=float, default=0.0, help="temps du premier temps fort (s) pour --bpm")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    W, H, fps, dur = probe(a.video)
    end = min(a.end if a.end is not None else dur, dur)
    tw = a.thumb
    th = int(round(tw * H / W / 2)) * 2
    # on décode toutes les images du passage puis on pioche l'image exacte de chaque instant
    frames = read_frames(a.video, a.start, end, tw, th)
    times = np.arange(a.start, end - 1e-6, a.step)
    n_src = len(frames)
    picks = [min(int(round((t - a.start) * fps)), n_src - 1) for t in times]

    lab_h = 34 if a.bpm else 20
    cols = min(a.cols, len(times))
    rows = (len(times) + cols - 1) // cols
    pad = 6
    sheet = Image.new("RGB", (cols * (tw + pad) + pad, rows * (th + lab_h + pad) + pad), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    f = label_font(14)
    for k, (t, i) in enumerate(zip(times, picks)):
        x = pad + (k % cols) * (tw + pad)
        y = pad + (k // cols) * (th + lab_h + pad)
        sheet.paste(Image.fromarray(frames[i]), (x, y))
        n = int(round(t * fps))
        d.text((x + 2, y + th + 2), "%.2fs  #%d" % (t, n), fill=(235, 235, 235), font=f)
        if a.bpm:
            beat = (t - a.offset) * a.bpm / 60.0
            bar, b = int(beat // 4) + 1, beat % 4 + 1
            on = abs(beat - round(beat)) < 0.02
            d.text((x + 2, y + th + 17), "mes %d · tps %.2g%s" % (bar, b, " ●" if on else ""),
                   fill=(255, 196, 0) if on else (150, 150, 150), font=f)
    out = a.out or os.path.join("build", "review", "sheet_%05.2f_%05.2f.jpg" % (a.start, end))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    sheet.save(out, quality=88)
    print(out, "(%d vignettes, %dx%d)" % (len(times), sheet.width, sheet.height))


if __name__ == "__main__":
    main()
