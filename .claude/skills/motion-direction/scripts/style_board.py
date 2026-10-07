#!/usr/bin/env python3
"""Planche de style générée depuis le code : les 24 looks avec leur couleur signature et les teintes de fond
réellement utilisées, les couleurs des fils, les palettes granny et les polices.

Comme elle lit les constantes de motion/render.py et motion/collage.py, elle reste à jour avec le film.
Usage (depuis la racine) :
    python3 .claude/skills/motion-direction/scripts/style_board.py            # -> build/review/style_board.png
"""
import argparse, os, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "motion")
import render as R  # noqa: E402
import collage as C  # noqa: E402

TINTS = [(0.55, "disque"), (0.72, "bento"), (0.78, "fond zoom"), (0.8, "fond plein")]


def font(name, size):
    p = os.path.join("assets", "fonts", name)
    if os.path.exists(p):
        return ImageFont.truetype(p, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)


def hexa(c):
    return "#%02X%02X%02X" % c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out", nargs="?", default=os.path.join("build", "review", "style_board.png"))
    out = ap.parse_args().out
    cw, th = 200, 300
    cols = 6
    W = 40 + cols * (cw + 16)
    H = 3400
    img = Image.new("RGB", (W, H), C.BG)
    d = ImageDraw.Draw(img)
    small = font("Montserrat-Medium.ttf", 16)
    title = font("Anton.ttf", 44)
    d.text((40, 24), "PLANCHE DE STYLE — générée depuis le code", fill=(30, 30, 30), font=title)
    y = 100
    for k in range(1, 25):
        x = 40 + ((k - 1) % cols) * (cw + 16)
        yy = y + ((k - 1) // cols) * (th + 110)
        col = R.LOOK_COLOR[k]
        d.rectangle([x, yy, x + cw, yy + th], fill=R.tint(col, 0.8))
        src = Image.open(os.path.join("assets", "articles", "article_%02d.jpg" % k)).convert("RGB")
        src.thumbnail((cw - 20, th - 20))
        img.paste(src, (x + (cw - src.width) // 2, yy + (th - src.height) // 2))
        d.rectangle([x, yy + th + 4, x + cw, yy + th + 40], fill=col)
        d.text((x + 6, yy + th + 12), "%02d  %s%s" % (k, hexa(col), "  ×2" if k in C.COUPLES else ""),
               fill=(255, 255, 255) if sum(col) < 400 else (20, 20, 20), font=small)
        for j, (tv, _) in enumerate(TINTS):
            d.rectangle([x + j * cw / 4, yy + th + 44, x + (j + 1) * cw / 4 - 2, yy + th + 70], fill=R.tint(col, tv))
    y += 4 * (th + 110) + 10
    d.text((40, y), "teintes sous chaque look : " + " · ".join("%s (tint %.2f)" % (n, v) for v, n in TINTS)
           + "   ×2 = visuel à deux personnes", fill=(80, 80, 80), font=small)
    y += 40
    d.text((40, y), "FILS (YARN)", fill=(30, 30, 30), font=font("Anton.ttf", 30))
    y += 44
    for j, c in enumerate(R.YARN):
        d.rectangle([40 + j * 150, y, 180 + j * 150, y + 60], fill=c)
        d.text((44 + j * 150, y + 66), hexa(c), fill=(60, 60, 60), font=small)
    y += 110
    d.text((40, y), "PALETTES GRANNY", fill=(30, 30, 30), font=font("Anton.ttf", 30))
    y += 44
    for j, pal in enumerate(C.PALETTES):
        g = C.granny(150, j)
        img.paste(g, (40 + j * 300, y), g)
        for m, c in enumerate(pal):
            d.rectangle([200 + j * 300, y + m * 40, 260 + j * 300, y + m * 40 + 34], fill=c)
    y += 210
    d.text((40, y), "FOND PAPIER %s · FOND MOSAÏQUE %s" % (hexa(C.BG), hexa(C.GAPC)), fill=(60, 60, 60), font=small)
    d.rectangle([520, y - 4, 600, y + 24], fill=C.BG, outline=(0, 0, 0))
    d.rectangle([610, y - 4, 690, y + 24], fill=C.GAPC)
    y += 50
    d.text((40, y), "POLICES", fill=(30, 30, 30), font=font("Anton.ttf", 30))
    y += 44
    for name in sorted(os.listdir(os.path.join("assets", "fonts"))):
        d.text((40, y), "%-26s  Crochet Pop Collage 0123" % name, fill=(20, 20, 20), font=font(name, 34))
        y += 52
    img = img.crop((0, 0, W, y + 30))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()
