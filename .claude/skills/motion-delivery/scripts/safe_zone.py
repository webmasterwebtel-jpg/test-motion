#!/usr/bin/env python3
"""Superpose les zones masquées par l'interface (TikTok, Reels, Shorts) sur des images d'une vidéo.

Les marges viennent de références publiques et restent **indicatives** (les interfaces changent) : elles valent
pour le texte, les logos et les appels à l'action. Un sujet (personne, produit) peut déborder un peu dans la
zone basse, mais son visage et le produit lui-même doivent rester dans le cadre sûr.

Exemples :
    python3 safe_zone.py output/film.mp4 --times 2.7 10 17.6 30 45 58
    python3 safe_zone.py output/film.mp4 --times 5 --platforms tiktok
"""
import argparse, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# marges (haut, bas, gauche, droite) en px pour 1080x1920
ZONES = {
    "tiktok": ((240, 660, 120, 120), (255, 40, 90)),
    "reels": ((269, 672, 65, 65), (170, 60, 255)),
    "shorts": ((288, 672, 48, 192), (255, 150, 0)),
}
# cadre « sujet » utilisé par le film (visage et produit) : plus permissif que la zone texte
SUBJECT = (210, 310, 0, 140)


def grab(path, t, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", path, "-frames:v", "1",
                          "-vf", "scale=%d:%d" % (w, h), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return Image.fromarray(np.frombuffer(raw, np.uint8).reshape(h, w, 3))


def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--times", type=float, nargs="+", required=True)
    ap.add_argument("--platforms", nargs="+", default=list(ZONES), choices=list(ZONES))
    ap.add_argument("--width", type=int, default=360)
    ap.add_argument("--out", default=os.path.join("build", "review", "safe_zones.png"))
    a = ap.parse_args()

    w = a.width
    h = int(round(w * 1920 / 1080))
    k = w / 1080
    f = font(13)
    pad = 8
    sheet = Image.new("RGB", (max(pad + len(a.times) * (w + pad), 820), h + 60), (24, 24, 24))
    for n, t in enumerate(a.times):
        im = grab(a.video, t, w, h).convert("RGBA")
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        # zones interdites au texte : union des plateformes choisies, voilée
        top = max(ZONES[p][0][0] for p in a.platforms) * k
        bot = max(ZONES[p][0][1] for p in a.platforms) * k
        lef = max(ZONES[p][0][2] for p in a.platforms) * k
        rig = max(ZONES[p][0][3] for p in a.platforms) * k
        for box in ([0, 0, w, top], [0, h - bot, w, h], [0, top, lef, h - bot], [w - rig, top, w, h - bot]):
            d.rectangle(box, fill=(0, 0, 0, 90))
        for p in a.platforms:
            (t_, b_, l_, r_), col = ZONES[p]
            d.rectangle([l_ * k, t_ * k, w - r_ * k, h - b_ * k], outline=col + (255,), width=2)
        st, sb, sl, sr = SUBJECT
        for y in range(int(st * k), int(h - sb * k), 8):     # cadre sujet en pointillés verts
            d.line([sl * k, y, sl * k, y + 4], fill=(40, 220, 120, 255), width=2)
            d.line([w - sr * k, y, w - sr * k, y + 4], fill=(40, 220, 120, 255), width=2)
        for x in range(int(sl * k), int(w - sr * k), 8):
            d.line([x, st * k, x + 4, st * k], fill=(40, 220, 120, 255), width=2)
            d.line([x, h - sb * k, x + 4, h - sb * k], fill=(40, 220, 120, 255), width=2)
        im = Image.alpha_composite(im, ov).convert("RGB")
        sheet.paste(im, (pad + n * (w + pad), pad))
        ImageDraw.Draw(sheet).text((pad + n * (w + pad), h + pad + 4), "%.2f s" % t, fill=(230, 230, 230), font=f)
    d = ImageDraw.Draw(sheet)
    x = pad
    for p in a.platforms:
        lab = "■ %s (texte/CTA)   " % p
        d.text((x, h + pad + 24), lab, fill=ZONES[p][1], font=f)
        x += d.textlength(lab, font=f)
    d.text((x, h + pad + 24), "┆ vert = cadre sujet du projet · voile = hors zone texte", fill=(40, 220, 120), font=f)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    sheet.save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
