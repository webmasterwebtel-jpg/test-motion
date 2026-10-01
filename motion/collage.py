"""« Crochet Pop Collage » — motion design 60 s, format TikTok 9:16 (1080x1920, 30 i/s).

Sans voix ni texte : uniquement de l'animation, des bruitages et une musique de fond.
Direction : collage mixed-media (stickers découpés, ruban adhésif, grain papier), timing « stop-motion »
sur certains éléments, compositions modulaires (mosaïque, bento), carrousel 3D.
Toute la timeline est calée sur 120 BPM (1 temps = 0,5 s = 15 images), comme la bande-son.

Usage :
    python3 motion/collage.py                    # -> build/collage_silent.mp4
    python3 motion/collage.py --stills 2.7 17.6  # images de contrôle -> build/stills_collage/
"""
import math, os, sys, random, subprocess
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops
from scipy import ndimage

import render as R
from render import (W, H, FPS, BEAT, BUILD, YARN, LOOK_COLOR, WHITE, clamp01, seg, lerp, out_cubic, in_cubic,
                    in_out_cubic, out_expo, in_expo, out_back, in_back, decay, mix, tint, place, draw_yarn,
                    draw_orbit, catmull, _arclen, ripple, sparkle, flash, vignette_pulse)

DURATION = 60.0
BG = (250, 246, 240)                  # papier blanc chaud
GAPC = (38, 34, 32)                   # fond sombre visible entre les carreaux de la mosaïque
PAD = 40                              # marge autour des stickers (px source)
# zone sûre TikTok : rien d'important sous ~1600 px (légende) ni derrière la colonne de boutons à droite
CX, CY, CS = 540, 935, 0.80           # pose standard d'un sticker

PALETTES = [
    [(230, 25, 127), (255, 196, 0), (0, 179, 164), (245, 236, 220)],
    [(255, 122, 0), (47, 107, 255), (255, 196, 0), (245, 236, 220)],
    [(142, 68, 236), (255, 122, 0), (230, 25, 127), (245, 236, 220)],
    [(0, 179, 164), (225, 43, 43), (255, 196, 0), (245, 236, 220)],
]


# ----------------------------------------------------------------------------- assets
_ST = {}


def load():
    R.load_images()
    for i in range(1, 25):
        im = Image.open(os.path.join(BUILD, "cutouts", "article_%02d.png" % i)).convert("RGBA")
        a = np.asarray(im).copy()
        ramp = np.ones(a.shape[0]); ramp[:30] = np.linspace(0, 1, 30)
        a[..., 3] = (a[..., 3] * ramp[:, None]).astype(np.uint8)
        h, w = a.shape[:2]
        big = np.zeros((h + 2 * PAD, w + 2 * PAD, 4), np.uint8)
        big[PAD:PAD + h, PAD:PAD + w] = a
        al = big[..., 3].astype(np.float32) / 255
        # liseré blanc de sticker
        rim = ndimage.maximum_filter(ndimage.zoom(al, 0.25, order=1), size=5)
        rim = np.clip(ndimage.zoom(rim, 4, order=1)[: al.shape[0], : al.shape[1]], 0, 1)
        rim = ndimage.gaussian_filter(np.maximum(rim, al), 1.2)
        rim = (rim > 0.35).astype(np.float32)
        rim = ndimage.gaussian_filter(rim, 0.8)
        # ombre portée dure (papier)
        sh = np.zeros_like(rim)
        sh[14:, 10:] = rim[:-14, :-10]
        sh = ndimage.gaussian_filter(sh, 3) * 0.28
        out = np.zeros_like(big, np.float32)
        out[..., :3] = 0
        out[..., 3] = sh
        # blanc par-dessus l'ombre
        a_w = rim
        out[..., :3] = out[..., :3] * (1 - a_w[..., None]) + 255 * a_w[..., None]
        out[..., 3] = a_w + out[..., 3] * (1 - a_w)
        # image par-dessus
        a_i = al
        rgb = big[..., :3].astype(np.float32)
        tot = a_i + out[..., 3] * (1 - a_i)
        out[..., :3] = (rgb * a_i[..., None] + out[..., :3] * (out[..., 3] * (1 - a_i))[..., None]) / \
            np.maximum(tot[..., None], 1e-6)
        out[..., 3] = tot
        out[..., 3] *= 255
        st = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
        R._IMG[("st", i)] = st
        R._IMG[(("st", i), "half")] = st.reduce(2)
        _ST[i] = st


def sticker(c, i, cx=CX, cy=CY, s=CS, anchor=None, **kw):
    if anchor is not None:
        anchor = (anchor[0] + PAD, anchor[1] + PAD)
    place(c, R._IMG[("st", i)], cx, cy, s, key=("st", i), anchor=anchor, **kw)


@lru_cache(maxsize=32)
def granny(size, pal_idx):
    """Carré granny au crochet dessiné procéduralement."""
    pal = PALETTES[pal_idx % len(PALETTES)]
    S = size * 2
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    d.rounded_rectangle([0, 0, S - 1, S - 1], radius=S * 0.06, fill=pal[3] + (255,))
    # bordure externe
    bw = S * 0.07
    d.rounded_rectangle([bw * 0.3, bw * 0.3, S - bw * 0.3, S - bw * 0.3], radius=S * 0.05,
                        outline=pal[2] + (255,), width=int(bw))
    # rang de « grappes » (3 brides par groupe) le long du carré
    r2 = S * 0.36
    for side in range(4):
        for k in range(5):
            u = -r2 + (k + 0.5) * (2 * r2 / 5)
            pts = [(c + u, c - r2), (c + r2, c + u), (c - u, c + r2), (c - r2, c - u)]
            x, y = pts[side]
            ang = side * math.pi / 2
            for j in (-1, 0, 1):
                ox, oy = math.cos(ang) * j * S * 0.025, math.sin(ang) * j * S * 0.025
                nx, ny = -math.sin(ang), math.cos(ang)
                d.line([(x + ox - nx * S * 0.04, y + oy - ny * S * 0.04),
                        (x + ox + nx * S * 0.04, y + oy + ny * S * 0.04)], fill=pal[1] + (255,), width=int(S * 0.022))
    # fleur centrale
    for k in range(8):
        a = k * math.pi / 4
        px, py = c + math.cos(a) * S * 0.16, c + math.sin(a) * S * 0.16
        rr = S * 0.085
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=pal[0] + (255,))
        d.ellipse([px - rr * 0.45, py - rr * 0.45, px + rr * 0.45, py + rr * 0.45],
                  fill=mix(pal[0], (0, 0, 0), 0.2) + (255,))
    rr = S * 0.09
    d.ellipse([c - rr, c - rr, c + rr, c + rr], fill=pal[1] + (255,))
    # texture de mailles : petits « v »
    rnd = random.Random(size + pal_idx)
    for _ in range(int(S * 0.6)):
        x, y = rnd.uniform(S * 0.05, S * 0.95), rnd.uniform(S * 0.05, S * 0.95)
        d.line([(x - 3, y - 3), (x, y + 2), (x + 3, y - 3)], fill=(0, 0, 0, 28), width=2)
    im = im.resize((size, size), Image.LANCZOS)
    # ombre
    out = Image.new("RGBA", (size + 30, size + 30), (0, 0, 0, 0))
    shm = Image.new("L", out.size, 0)
    shm.paste(im.getchannel("A").point(lambda v: int(v * 0.3)), (18, 22))
    shm = shm.filter(ImageFilter.GaussianBlur(5))
    sl = Image.new("RGBA", out.size, (30, 20, 20, 0)); sl.putalpha(shm)
    out.alpha_composite(sl)
    out.alpha_composite(im, (6, 6))
    return out


def ball(c, x, y, r, rot, color=(230, 25, 127)):
    """Pelote de laine."""
    if r < 2:
        return
    S = int(r * 2 + 40) * 2
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cc, rr = S / 2, r * 2
    d.ellipse([cc - rr + 14, cc - rr + 20, cc + rr + 14, cc + rr + 20], fill=(40, 20, 20, 60))
    lay = lay.filter(ImageFilter.GaussianBlur(6))
    d = ImageDraw.Draw(lay)
    d.ellipse([cc - rr, cc - rr, cc + rr, cc + rr], fill=color + (255,))
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([cc - rr, cc - rr, cc + rr, cc + rr], fill=255)
    st = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ds = ImageDraw.Draw(st)
    dark = mix(color, (0, 0, 0), 0.3) + (255,)
    light = mix(color, WHITE, 0.35) + (255,)
    for fam, ang0 in ((0, rot), (1, rot + 1.1), (2, rot + 2.3)):
        ca, sa = math.cos(ang0), math.sin(ang0)
        for k in range(-7, 8):
            off = k * rr / 6.5
            p0 = (cc + ca * (-rr * 1.2) - sa * off, cc + sa * (-rr * 1.2) + ca * off)
            p1 = (cc + ca * (rr * 1.2) - sa * off, cc + sa * (rr * 1.2) + ca * off)
            ds.line([p0, p1], fill=dark if (k + fam) % 2 else light, width=max(int(rr * 0.07), 2))
    st.putalpha(ImageChops.multiply(st.getchannel("A"), mask))
    lay.alpha_composite(st)
    d = ImageDraw.Draw(lay)
    d.ellipse([cc - rr * 0.55, cc - rr * 0.7, cc - rr * 0.1, cc - rr * 0.35], fill=(255, 255, 255, 60))
    lay = lay.resize((S // 2, S // 2), Image.LANCZOS)
    c.alpha_composite(lay, (int(x - S / 4), int(y - S / 4)))


def tape(c, x, y, ang, w=190, h=54, color=(255, 196, 0), alpha=0.75, p=1.0):
    """Morceau de ruban adhésif (washi) aux bords dentelés."""
    if p <= 0:
        return
    w = w * p
    S = int(max(w, h) * 1.6)
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = S / 2, S / 2
    pts = []
    n = 6
    for k in range(n + 1):
        pts.append((cx - w / 2 + (k % 2) * 5, cy - h / 2 + k * h / n))
    for k in range(n + 1):
        pts.append((cx + w / 2 - (k % 2) * 5, cy + h / 2 - k * h / n))
    d.polygon(pts, fill=color + (int(255 * alpha),))
    for k in range(4):
        yy = cy - h / 2 + (k + 0.5) * h / 4
        d.line([(cx - w / 2 + 6, yy), (cx + w / 2 - 6, yy)], fill=(255, 255, 255, 45), width=3)
    lay = lay.rotate(-ang, resample=Image.BICUBIC)
    c.alpha_composite(lay, (int(x - S / 2), int(y - S / 2)))


def shape(c, kind, x, y, r, rot, color, alpha=1.0):
    """Formes géométriques pop (collage)."""
    if r < 2 or alpha <= 0:
        return
    S = int(r * 2.4) * 2
    lay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cc, rr = S / 2, r * 2
    col = color + (int(255 * alpha),)
    if kind == "circle":
        d.ellipse([cc - rr, cc - rr, cc + rr, cc + rr], fill=col)
    elif kind == "arch":
        d.rounded_rectangle([cc - rr * 0.8, cc - rr, cc + rr * 0.8, cc + rr], radius=int(rr * 0.8), fill=col)
        d.rectangle([cc - rr * 0.8, cc, cc + rr * 0.8, cc + rr], fill=col)
    elif kind == "star":
        pts = []
        for k in range(24):
            a = k * math.pi / 12
            q = rr * (1.0 if k % 2 == 0 else 0.78)
            pts.append((cc + q * math.cos(a), cc + q * math.sin(a)))
        d.polygon(pts, fill=col)
    elif kind == "half":
        d.pieslice([cc - rr, cc - rr, cc + rr, cc + rr], 180, 360, fill=col)
        d.pieslice([cc - rr * 0.55, cc - rr * 0.55, cc + rr * 0.55, cc + rr * 0.55], 0, 180, fill=col)
    elif kind == "squircle":
        d.rounded_rectangle([cc - rr * 0.85, cc - rr * 0.85, cc + rr * 0.85, cc + rr * 0.85], radius=int(rr * 0.35),
                            fill=col)
    lay = lay.rotate(-rot, resample=Image.BICUBIC).resize((S // 2, S // 2), Image.LANCZOS)
    c.alpha_composite(lay, (int(x - S / 4), int(y - S / 4)))


def stepped(t, fps=12):
    """Temps quantifié façon stop-motion."""
    return math.floor(t * fps) / fps


def jitter(t, amp, seed=0, fps=12):
    r = random.Random(int(t * fps) * 7919 + seed)
    return r.uniform(-amp, amp)


def bgfill(c, color):
    ImageDraw.Draw(c).rectangle([0, 0, W, H], fill=color + (255,))


# ----------------------------------------------------------------------------- 0–4 s : pelote -> carrés -> look
def sec_intro(c, t, fx):
    tq = stepped(t)
    # fil déroulé derrière la pelote
    if t < 0.62:
        e = out_cubic(seg(tq, 0.0, 0.45))
        bx = lerp(-140, CX, e)
        xs = np.linspace(-200, bx, 50)
        pts = np.stack([xs, CY + 26 * np.sin(xs / 70) * (1 - (xs - bx) / -800).clip(0, 1)], 1)
        draw_yarn(c, pts, 16, [YARN[0]], seglen=999)
        r = 125 * (1 - out_cubic(seg(t, 0.47, 0.6)))
        ball(c, bx, CY, r, -bx / 60)
    # deux carrés granny tamponnés sur les battements
    for t0, size, rot, pal in ((0.5, 680, -6, 0), (1.5, 430, 8, 1)):
        if t0 <= t < 2.5:
            p = seg(t, t0, t0 + 0.14)
            sc = lerp(1.45, 1.0, out_cubic(p))
            place(c, granny(size, pal), CX + jitter(t, 2, int(t0)), CY + jitter(t, 2, 5 + int(t0)), sc,
                  rot=rot + jitter(t, 0.6, 9))
    # explosion des carrés en quartiers au 3e impact
    if 2.5 <= t < 3.3:
        p = out_expo(seg(t, 2.5, 3.2))
        for t0, size, rot, pal in ((0.5, 680, -6, 0), (1.5, 430, 8, 1)):
            tile = granny(size, pal)
            hw = tile.width // 2
            for qx in (0, 1):
                for qy in (0, 1):
                    piece = tile.crop((qx * hw, qy * hw, qx * hw + hw, qy * hw + hw))
                    dx, dy = (qx - 0.5) * 2, (qy - 0.5) * 2
                    dist = 900 * p * (1.2 if size < 500 else 1.0)
                    place(c, piece, CX + dx * (hw / 2 + dist), CY + dy * (hw / 2 + dist), 1 + 0.3 * p,
                          rot=rot + dx * dy * 140 * p, alpha=1 - seg(t, 2.9, 3.3))
        fx["mb"] = 4
    # le look apparaît (sticker) sur un disque coloré
    if t >= 2.5:
        p = seg(t, 2.5, 3.05)
        r = 470 * out_back(seg(t, 2.5, 2.85), 1.8)
        shape(c, "circle", CX, CY + 20, r, 0, tint(LOOK_COLOR[2], 0.55))
        s = CS * lerp(1.7, 1.0, out_expo(p))
        sticker(c, 2, s=s, rot=lerp(-14, -3, out_expo(p)) + (jitter(t, 0.8, 3) if p >= 1 else 0))
        if p < 0.4:
            fx["mb"] = 4
    for b in (0.5, 1.5, 2.5):
        fx["punch"] += (0.025 if b < 2.5 else 0.06) * decay(t, b, 9)
        fx["vig"] += 0.28 * decay(t, b, 5)
        ripple(c, t, b, CX, CY, YARN[0] if b == 2.5 else (60, 50, 50), 1000, 0.8, 6 if b == 2.5 else 3,
               0.5 if b == 2.5 else 0.22)
    fx["shake"] += 12 * decay(t, 2.5, 9)


# ----------------------------------------------------------------------------- 4–10 s : pile de stickers
# chaque look reste ~2 s (une mesure) au sommet de la pile pour qu'on ait le temps de bien le voir
PILE = [(2.5, 2, "none"), (4.0, 5, "drop"), (6.0, 12, "spin"), (8.0, 16, "slide"), (10.0, 1, "flip"),
        (12.0, 9, "drop"), (14.0, 18, "spin")]
SHAPES = ["circle", "arch", "star", "half", "squircle", "star", "arch"]
TAPE_COLORS = [(255, 196, 0), (0, 179, 164), (230, 25, 127), (47, 107, 255), (255, 122, 0), (142, 68, 236),
               (255, 196, 0)]


def _pose(k):
    rnd = random.Random(k * 31 + 5)
    if k == 0:
        return CX, CY, -3.0
    return CX + rnd.uniform(-70, 70), CY + rnd.uniform(-30, 30), (5 + rnd.uniform(0, 3)) * (1 if k % 2 else -1)


def _top_point(cx, cy, s, rot):
    # point haut-centre du sticker (au-dessus de la tête), transformé
    vx, vy = 0, -(768 - 40) * s
    r = math.radians(rot)
    return cx + vx * math.cos(r) - vy * math.sin(r), cy + vx * math.sin(r) + vy * math.cos(r)


def draw_pile(c, t, fx, upto=None):
    # formes pop derrière toute la pile
    shape(c, "circle", CX, CY + 20, 470, 0, tint(LOOK_COLOR[2], 0.55))
    for k, (ta, i, kind) in enumerate(PILE):
        if k == 0 or t < ta - 0.05:
            continue
        x, y, r = _pose(k)
        sp = seg(t, ta - 0.05, ta + 0.3)
        shape(c, SHAPES[k], x + (230 if k % 2 else -230), y - 300 + 90 * (k % 3), 260 * out_back(sp, 2.0),
              (t - ta) * 25 * (1 if k % 2 else -1), tint(LOOK_COLOR[i], 0.45))
    for k, (ta, i, kind) in enumerate(PILE):
        if t < ta or (upto is not None and k > upto):
            continue
        x, y, r = _pose(k)
        p = seg(t, ta, ta + 0.34)
        s, sx, sy, ry, rr, xx, yy = CS, 1.0, 1.0, 0.0, r, x, y
        if kind == "drop":
            e = in_cubic(seg(t, ta, ta + 0.16))
            yy = lerp(y - 1500, y, e)
            sq = decay(t, ta + 0.16, 14) if t >= ta + 0.16 else 0
            sy, sx = 1 - 0.14 * sq, 1 + 0.08 * sq
        elif kind == "spin":
            rr = r + 220 * (1 - out_expo(p))
            s = CS * out_back(p, 1.6)
        elif kind == "slide":
            xx = lerp(x + 1300, x, out_back(p, 1.3))
            rr = r + 18 * (1 - out_cubic(p))
        elif kind == "flip":
            ry = 85 * (1 - out_back(p, 1.4))
        if p < 0.6 and kind != "none":
            fx["mb"] = 4
        # les plus anciens reculent un peu
        older = sum(1 for (tb, _, _) in PILE[k + 1:] if t >= tb)
        s *= 1 - 0.035 * min(older, 3)
        sticker(c, i, cx=xx, cy=yy, s=s, rot=rr + (jitter(t, 0.7, k) if p >= 1 else 0), sx=sx, sy=sy, ry=ry)
        if k > 0:
            tp = seg(t, ta + 0.24, ta + 0.34)
            tx, ty = _top_point(xx, yy, s, rr)
            tape(c, tx, ty, rr + (22 if k % 2 else -22), color=TAPE_COLORS[k], p=out_cubic(tp))
        if k > 0:
            fx["punch"] += 0.025 * decay(t, ta + (0.16 if kind == "drop" else 0.1), 11)


def sec_pile(c, t, fx):
    draw_pile(c, t, fx)
    # 15,5 → 16 : la caméra plonge dans le dernier sticker (point de détail)
    if t >= 15.5:
        x, y, r = _pose(6)
        e = in_expo(seg(t, 15.5, 16.0))
        k = 1 + 3.2 * e
        dpx, dpy = x + (500 - 512) * CS, y + (760 - 768) * CS
        fx["cam_scale"] *= k
        fx["cam_dx"] -= (dpx - W / 2) * (k - 1) * 1.0
        fx["cam_dy"] -= (dpy - H / 2) * (k - 1) * 1.0
        if e > 0.2:
            fx["mb"] = 3
    if t >= 15.78:
        fx["post"].append(lambda fr, tt=t: iris(fr, tt, 15.78, 16.0, ZOOM[0]))


# ----------------------------------------------------------------------------- 10–17 s : zoom infini
# (début, durée, image, point de détail en coords image)
ZOOM = [
    (16.0, 2.0, 13, (560, 1130)), (18.0, 2.0, 10, (500, 1140)), (20.0, 2.0, 15, (520, 800)),
    (22.0, 2.0, 17, (500, 1190)), (24.0, 2.0, 23, (500, 760)), (26.0, 2.0, 20, (470, 1060)),
]
ZOOM_IN = 0.6   # la plongée n'occupe que la fin du plan : le look est d'abord bien visible
S0, S1 = 0.80, 3.4


def zoom_state(shot, p):
    st, du, i, (dx, dy) = shot
    s = S0 * (S1 / S0) ** p
    f = (s - S0) / (S1 - S0)
    p0x, p0y = CX + (dx - 512) * S0, CY + (dy - 768) * S0
    return s, lerp(p0x, W / 2, f), lerp(p0y, H / 2, f)


def draw_shot(c, shot, p, small=1.0):
    st, du, i, (dx, dy) = shot
    bgfill(c, tint(LOOK_COLOR[i], 0.78))
    if p <= 0:
        # état de départ (éventuellement plus petit, dans l'iris)
        shape(c, "circle", CX, CY + 20, 470 * small, 0, tint(LOOK_COLOR[i], 0.6))
        sticker(c, i, s=CS * small, rot=0)
        return
    s, x, y = zoom_state(shot, p)
    r = 470 * s / S0
    ox, oy = x + (512 - dx) * s, y + (768 + 25 - dy) * s
    ImageDraw.Draw(c).ellipse([ox - r, oy - r, ox + r, oy + r], fill=tint(LOOK_COLOR[i], 0.6) + (255,))
    place(c, R._IMG[("st", i)], x, y, s, anchor=(dx + PAD, dy + PAD), key=("st", i))


def iris(frame, t, t0, t1, nxt):
    q = seg(t, t0, t1)
    if q <= 0:
        return
    r = 1180 * in_out_cubic(q)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_shot(lay, nxt, 0.0, small=lerp(0.45, 1.0, out_cubic(q)))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=255)
    lay.putalpha(m)
    frame.alpha_composite(lay)
    ths = np.linspace(0, 2 * math.pi * 1.02, 220)
    pts = np.stack([W / 2 + (r + 6) * np.cos(ths), H / 2 + (r + 6) * np.sin(ths)], 1)
    if r > 20:
        draw_yarn(frame, pts, 15, [LOOK_COLOR[nxt[2]], (255, 196, 0), WHITE], seglen=110, shadow=False)


def sec_zoom(c, t, fx):
    for k, shot in enumerate(ZOOM):
        st, du, i, d = shot
        if st <= t < st + du:
            z0 = st + du - ZOOM_IN
            if t < z0:
                # pose : le look est présenté entier, avec un léger flottement
                bgfill(c, tint(LOOK_COLOR[i], 0.78))
                shape(c, "circle", CX, CY + 20, 470, 0, tint(LOOK_COLOR[i], 0.6))
                fl = math.sin((t - st) * 2.2)
                sticker(c, i, s=CS * (1 + 0.02 * seg(t, st, z0)), cy=CY + 8 * fl, rot=1.2 * fl)
            else:
                p = (t - z0) / ZOOM_IN
                draw_shot(c, shot, p ** 1.15)
                if p > 0.3:
                    fx["mb"] = 3
                if k + 1 < len(ZOOM):
                    fx["post"].append(lambda fr, tt=t, a=z0 + ZOOM_IN * 0.58, b=st + du, n=ZOOM[k + 1]:
                                      iris(fr, tt, a, b, n))
            fx["punch"] += 0.02 * decay(t, st, 12)


# ----------------------------------------------------------------------------- 17–24 s : mosaïque de carreaux
WOW = [(17.0, 22), (19.0, 24)]   # (temps internes ; la section est jouée à +11 s)
WOW_SHIFT = 11.0
COLS, ROWS = 6, 10
TW, TH = W / COLS, H / ROWS


@lru_cache(maxsize=12)
def look_frame(i):
    c = Image.new("RGBA", (W, H), tint(LOOK_COLOR[i], 0.8) + (255,))
    ImageDraw.Draw(c).ellipse([CX - 440, CY - 420, CX + 440, CY + 460], fill=tint(LOOK_COLOR[i], 0.55) + (255,))
    sticker(c, i)
    return c


def _delay(pattern, col, row):
    cx, cy = (col + 0.5) / COLS - 0.5, (row + 0.5) / ROWS - 0.5
    if pattern == "radial":
        return math.hypot(cx, cy * 1.6) * 0.3
    if pattern == "diag":
        return (col / COLS + row / ROWS) * 0.14
    if pattern == "rows":
        return row / ROWS * 0.22
    if pattern == "random":
        return random.Random(col * 97 + row * 13).uniform(0, 0.2)
    if pattern == "spiral":
        return ((math.atan2(cy, cx) + math.pi) / (2 * math.pi)) * 0.24
    return 0


PATTERNS = ["radial", "diag", "rows", "random", "spiral"]


def sec_wow(c, t, fx):
    if t < 17.5:
        bgfill(c, BG)
        sticker(c, 22)
        return
    if t < 20.75:
        bgfill(c, GAPC)
        gap = 7 * out_cubic(seg(t, 17.5, 17.7)) * (1 - out_cubic(seg(t, 20.45, 20.75)))
        for row in range(ROWS):
            for col in range(COLS):
                x0, y0 = col * TW, row * TH
                # look affiché par ce carreau
                face_from, face_to, f = WOW[0][1], WOW[0][1], 0.0
                for k in range(1, len(WOW)):
                    tb = WOW[k][0]
                    dl = _delay(PATTERNS[k - 1], col, row)
                    fk = seg(t, tb + dl, tb + dl + 0.24)
                    if fk > 0:
                        face_from, face_to, f = WOW[k - 1][1], WOW[k][1], fk
                face = face_from if f < 0.5 else face_to
                sx = abs(math.cos(math.pi * f))
                # pulsation radiale du BOOM
                dl0 = _delay("radial", col, row)
                pop = math.sin(math.pi * seg(t, 17.5 + dl0, 17.5 + dl0 + 0.3)) * 0.12
                sc = 1 - pop
                piece = look_frame(face).crop((int(x0), int(y0), int(x0 + TW), int(y0 + TH)))
                if f > 0 and f < 1:
                    shade = 1 - 0.45 * math.sin(math.pi * f)
                    piece = Image.blend(Image.new("RGBA", piece.size, (0, 0, 0, 255)), piece, shade)
                tw = (TW - gap) * sc * max(sx, 0.02)
                th = (TH - gap) * sc
                if tw < 1:
                    continue
                piece = piece.resize((max(int(tw), 1), max(int(th), 1)), Image.BILINEAR)
                c.alpha_composite(piece, (int(x0 + TW / 2 - tw / 2), int(y0 + TH / 2 - th / 2)))
        for tb, _ in WOW[1:]:
            fx["punch"] += 0.02 * decay(t, tb, 10)
    else:
        sec_echo(c, t, fx)
    fx["punch"] += 0.08 * decay(t, 17.5, 7)
    fx["shake"] += 20 * decay(t, 17.5, 7)
    fx["vig"] += 0.45 * decay(t, 17.5, 4)
    fx["flash"] = (WHITE, 0.6 * decay(t, 17.5, 16))


@lru_cache(maxsize=8)
def silhouette(i, color):
    st = _ST[i]
    a = st.getchannel("A").point(lambda v: 255 if v > 140 else int(v * 1.8))
    im = Image.new("RGBA", st.size, color + (0,))
    im.putalpha(a.point(lambda v: int(v * 0.92)))
    return im


def sec_echo(c, t, fx):
    """Look 24 en impression « riso » : échos colorés décalés qui pulsent sur le beat + orbites de fil."""
    exit_q = in_cubic(seg(t, 23.62, 24.0))
    bgfill(c, tint(LOOK_COLOR[24], 0.82))
    beat_k = math.floor((t - 20.5) / BEAT)
    tb = 20.5 + beat_k * BEAT
    pulse = decay(t, tb, 6)
    rot_bg = (t - 20.5) * 20
    fade = 1 - seg(t, 20.75, 21.0)
    if fade > 0:
        ImageDraw.Draw(c).ellipse([CX - 440, CY - 420, CX + 440, CY + 460],
                                  fill=mix(tint(LOOK_COLOR[24], 0.82), tint(LOOK_COLOR[24], 0.55), fade) + (255,))
    shape(c, "star", CX, CY + 10, 520 * (1 + 0.05 * pulse) * (1 - exit_q) * out_back(seg(t, 20.75, 21.05), 1.6),
          rot_bg, tint(LOOK_COLOR[24], 0.55))
    ripple(c, t, tb, CX, CY, (255, 196, 0), 900, 0.5, 10, 0.5)
    sc = (1 + 0.03 * pulse) * (1 - 0.85 * exit_q)
    rr = 720 * exit_q
    off = 26 + 46 * pulse
    for k, col in enumerate([(0, 179, 164), (230, 25, 127), (255, 196, 0)]):
        a = (t - 20.5) * 2.2 + k * 2 * math.pi / 3
        place(c, silhouette(24, col), CX + off * math.cos(a) * sc, CY + off * math.sin(a) * sc, CS * sc,
              rot=-2 + rr, alpha=0.9 * (1 - exit_q))
    grow = out_cubic(seg(t, 20.6, 21.2))
    ph = (t - 20.5) * 2.6
    oa = 1 - exit_q
    draw_orbit(c, CX, 1110, 400 * sc, 100 * sc, ph, "back", [LOOK_COLOR[24], (255, 196, 0)], 14, 0.8, -40, grow, oa)
    draw_orbit(c, CX, 720, 340 * sc, 80 * sc, -ph * 1.2, "back", [(0, 179, 164), (230, 25, 127)], 12, 0.7, 30, grow, oa)
    sticker(c, 24, s=CS * sc, rot=-2 + rr)
    draw_orbit(c, CX, 1110, 400 * sc, 100 * sc, ph, "front", [LOOK_COLOR[24], (255, 196, 0)], 14, 0.8, -40, grow, oa)
    draw_orbit(c, CX, 720, 340 * sc, 80 * sc, -ph * 1.2, "front", [(0, 179, 164), (230, 25, 127)], 12, 0.7, 30, grow, oa)
    if exit_q > 0:
        fx["mb"] = 5
    fx["punch"] += 0.025 * pulse * (1 - exit_q)


# ----------------------------------------------------------------------------- 24–31 s : grille bento modulaire
AX0, AY0, AX1, AY1 = 36, 210, 1044, 1610
L0 = [(0.5, 0.5, 0.5, 0.5)] * 6
L1 = [(0, 0, .6, 1), (.6, 0, 1, .34), (.6, .34, 1, .67), (.6, .67, 1, 1), (1, 1, 1, 1), (1, 1, 1, 1)]
L2 = [(0, 0, .333, 1), (.333, 0, .667, 1), (.667, 0, 1, 1), (1, .5, 1, .5), (1, .5, 1, .5), (1, .5, 1, .5)]
L3 = [(0, 0, .5, .5), (.5, 0, 1, .5), (0, .5, .5, 1), (.5, .5, 1, 1), (.5, .5, .5, .5), (.5, .5, .5, .5)]
L4 = [(0, 0, .5, .333), (.5, 0, 1, .333), (0, .333, .5, .667), (.5, .333, 1, .667), (0, .667, .5, 1),
      (.5, .667, 1, 1)]
FULL = ((0 - AX0) / (AX1 - AX0), (0 - AY0) / (AY1 - AY0), (W - AX0) / (AX1 - AX0), (H - AY0) / (AY1 - AY0))
L5 = [FULL] + [((a + c_) / 2, (b + d) / 2, (a + c_) / 2, (b + d) / 2) for (a, b, c_, d) in L4[1:]]
BENTO = [(35.0, L3, [3, 4, 6, 7, 7, 7]), (37.0, L4, [8, 11, 14, 19, 5, 17]), (38.6, L5, [21, 11, 14, 19, 5, 17])]
LAST = len(BENTO) - 1
COUPLES = {3, 4, 6, 7, 8, 11, 14, 19, 21}


def _rect(u):
    return (AX0 + u[0] * (AX1 - AX0), AY0 + u[1] * (AY1 - AY0), AX0 + u[2] * (AX1 - AX0), AY0 + u[3] * (AY1 - AY0))


def _cell(c, i, rect, oy=0.0, full=0.0):
    x0, y0, x1, y1 = rect
    w, h = x1 - x0, y1 - y0
    if w < 3 or h < 3:
        return
    g = 7 * (1 - full)
    x0, y0, x1, y1 = x0 + g, y0 + g, x1 - g, y1 - g
    if x1 - x0 < 3 or y1 - y0 < 3:
        return
    ImageDraw.Draw(c).rounded_rectangle([x0, y0, x1, y1], radius=int(18 * (1 - full)) + 1,
                                        fill=tint(LOOK_COLOR[i], 0.72) + (255,))
    cw, ch = x1 - x0, y1 - y0
    if i in COUPLES:
        s, ay = max(cw / 1000, ch / 1450), 760
    else:
        s, ay = max(cw / 650, ch / 1420), 720
    s = lerp(s, CS, full)
    ay = lerp(ay, 768, full)
    cy = lerp((y0 + y1) / 2, CY, full)
    place(c, R.img(i), (x0 + x1) / 2, cy + oy * ch, s, anchor=(512, ay), clip=(x0, y0, x1, y1), key=i)


def sec_bento(c, t, fx):
    bgfill(c, BG)
    # quelle mise en page / quelle transition
    k = max(j for j, (tb, _, _) in enumerate(BENTO) if t >= tb)
    tb, lay, cont = BENTO[k]
    prev_lay = BENTO[k - 1][1] if k > 0 else L0
    prev_cont = BENTO[k - 1][2] if k > 0 else cont
    for j in range(6):
        p = out_expo(seg(t, tb + 0.045 * j, tb + 0.045 * j + 0.5)) if k < LAST else out_expo(seg(t, tb + 0.1, tb + 0.6))
        if k == LAST and j > 0:
            p = out_cubic(seg(t, tb, tb + 0.35))
        u = tuple(lerp(a, b, p) for a, b in zip(prev_lay[j], lay[j]))
        rect = _rect(u)
        full = p if (k == LAST and j == 0) else 0.0
        if cont[j] != prev_cont[j] and k > 0:
            q = seg(t, tb + 0.03 * j, tb + 0.03 * j + 0.28)
            if q < 1:
                _cell(c, prev_cont[j], rect, oy=-out_cubic(q) * 1.05)
            _cell(c, cont[j], rect, oy=(1 - out_cubic(q)) * 1.05, full=full)
        else:
            _cell(c, cont[j], rect, full=full)
        if p < 0.7:
            fx["mb"] = 3
    # petit carré granny qui « épingle » la composition
    if t < BENTO[LAST][0] - 0.1:
        gp = out_back(seg(t, tb + 0.15, tb + 0.45), 2.2)
        anchors = [(0.5, 0.5), (0.5, 0.333)]
        if k < LAST:
            ax, ay = anchors[k]
            x, y = AX0 + ax * (AX1 - AX0), AY0 + ay * (AY1 - AY0)
            place(c, granny(150, k), x, y, gp * (1 - seg(t, BENTO[k + 1][0] - 0.12, BENTO[k + 1][0])),
                  rot=(t - tb) * 90)
    fx["punch"] += sum(0.025 * decay(t, b, 10) for b, _, _ in BENTO)


# ----------------------------------------------------------------------------- 31–37 s : carrousel 3D
CAR = [21, 14, 19, 11, 8, 2, 12, 24]
C0, CSTEP, CEND = 39.0, 2.0, 55.0   # une tenue de face toutes les 2 s


def swayed_img(im, t, amp):
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    yy = np.arange(h, dtype=np.float32)
    wgt = np.clip((yy / h - 0.45) / 0.5, 0, 1) ** 1.6
    shift = amp * wgt * np.sin(t * 9.0 - yy / 55.0)
    xs = np.arange(w, dtype=np.float32)
    rows = np.nonzero(wgt > 0)[0]
    out = a.copy()
    xi = xs[None, :] - shift[rows, None]
    x0 = np.clip(np.floor(xi).astype(int), 0, w - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    fr = (xi - np.floor(xi))[..., None]
    ar = a[rows]
    out[rows] = np.take_along_axis(ar, x0[..., None].repeat(4, 2), 1) * (1 - fr) + \
        np.take_along_axis(ar, x1[..., None].repeat(4, 2), 1) * fr
    return Image.fromarray(out.astype(np.uint8))


def sec_carousel(c, t, fx):
    k = max(0, math.floor((t - C0) / CSTEP))
    tb = C0 + k * CSTEP
    rot = (k - 1) + out_back(seg(t, tb, tb + 0.45), 1.4) if k > 0 else 0.0
    front = CAR[int(round(rot)) % len(CAR)]
    bgfill(c, tint(LOOK_COLOR[front], 0.8))
    pulse = decay(t, tb, 7)
    # collapse final 36,85 → 37,4
    col = in_cubic(seg(t, CEND - 0.15, CEND + 0.35))
    spin = 2.5 * col
    shape(c, "circle", CX, CY + 40, 500 * (1 + 0.06 * pulse) * (1 - col), 0, tint(LOOK_COLOR[front], 0.5))
    ths = np.linspace(0, 2 * math.pi * 1.02, 200) + t * 1.2
    rr_ = 540 * (1 + 0.06 * pulse) * (1 - col)
    if rr_ > 30:
        ring = np.stack([CX + rr_ * np.cos(ths), CY + 40 + rr_ * np.sin(ths)], 1)
        draw_yarn(c, ring, 10, [(255, 196, 0), WHITE, LOOK_COLOR[front]], seglen=70)
    # cover-flow 3D : la carte de face est grande, les voisines pivotent sur les côtés
    cards = []
    n = len(CAR)
    for j, i in enumerate(CAR):
        d = ((j - rot + n / 2) % n) - n / 2
        ad, sg = abs(d), (1 if d >= 0 else -1)
        m = min(ad, 1.0)
        x = CX + sg * (m * 300 + max(ad - 1, 0) * 105)
        sc = (lerp(0.88, 0.46, m) - 0.05 * max(ad - 1, 0)) * (1 - 0.85 * col)
        ry = -sg * 62 * m
        y = CY + 20 * m
        x = lerp(x, CX, col)
        fade = clamp01((4.2 - ad) / 0.8)
        cards.append((-ad, j, i, x, y, sc, ry, fade, ad))
    cards.sort()
    for _, j, i, x, y, sc, ry, fade, ad in cards:
        wash = 0.18 * min(ad, 1) + 0.12 * max(ad - 1, 0)
        rr = 540 * col * (1 if j % 2 else -1)
        if ad < 0.05 and col == 0:
            im = swayed_img(_ST[i], t, 8)
            place(c, im, x, y, sc * (1 + 0.05 * pulse), ry=6 * math.sin((t - tb) * 6), alpha=fade)
        elif fade > 0:
            place(c, R._IMG[("st", i)], x, y, sc, ry=ry, wash=wash, key=("st", i), rot=rr, alpha=fade)
    if (k > 0 and seg(t, tb, tb + 0.45) < 0.6) or col > 0:
        fx["mb"] = 3
    fx["punch"] += 0.04 * pulse * (1 - col)


# ----------------------------------------------------------------------------- 37–40 s : pelote -> fleur
FLOWER_C = (540, 900)


def _petal(k, n=8, R_=230):
    a = k * 2 * math.pi / n - math.pi / 2
    tt = np.linspace(0, 2 * math.pi, 100)
    lx = R_ * 0.5 * (1 - np.cos(tt))
    ly = R_ * 0.2 * np.sin(tt)
    x = FLOWER_C[0] + 50 * math.cos(a) + lx * math.cos(a) - ly * math.sin(a)
    y = FLOWER_C[1] + 50 * math.sin(a) + lx * math.sin(a) + ly * math.cos(a)
    return np.stack([x, y], 1)


FIN_SHIFT = 18.0


def sec_finale_shifted(c, t, fx):
    if t < CEND + 0.35:
        sec_carousel(c, t, fx)
    else:
        bgfill(c, BG)
    sec_finale(c, t - FIN_SHIFT, fx)


def sec_finale(c, t, fx):
    """Pelote -> fleur (temps internes 37 → 42)."""
    # pelote
    if 37.0 <= t < 38.15:
        g = out_back(seg(t, 37.0, 37.4), 1.8)
        sq = math.sin((t - 37.4) * 18) * 0.06 * seg(t, 37.4, 38.0) if t > 37.4 else 0
        r = 120 * g * (1 + sq) * (1 - in_cubic(seg(t, 38.0, 38.15)))
        ball(c, FLOWER_C[0], FLOWER_C[1], r, (t - 37.0) * 9)
        fx["shake"] += 4 * seg(t, 37.5, 38.0)
    if t >= 38.0:
        p = seg(t, 38.0, 38.55)
        rot = (t - 38.0) * 0.15
        breathe = 1 + 0.02 * math.sin((t - 38.0) * 4)
        # rayons de fil qui jaillissent
        if t < 38.6:
            q = seg(t, 38.0, 38.6)
            for k in range(10):
                ang = k * math.pi / 5 + 0.2
                pts = np.array([(FLOWER_C[0] + r_ * math.cos(ang + 0.0005 * r_),
                                 FLOWER_C[1] + r_ * math.sin(ang + 0.0005 * r_)) for r_ in np.linspace(0, 1500, 40)])
                tot = _arclen(pts)[-1]
                draw_yarn(c, pts, 9, [YARN[k % 7], YARN[(k + 3) % 7]], tot * out_cubic(seg(q, 0.2, 1)) + 200,
                          tot * out_expo(q) + 220, 120, shadow=False)
        # mini carrés granny en orbite
        for k in range(10):
            a = k * 2 * math.pi / 10 + (t - 38.0) * 0.35
            pk = out_back(seg(t, 38.2 + k * 0.05, 38.5 + k * 0.05), 2.0)
            place(c, granny(110, k), FLOWER_C[0] + 420 * math.cos(a), FLOWER_C[1] + 420 * math.sin(a), pk,
                  rot=math.degrees(a) + 45)
        rr = np.array([[math.cos(rot), -math.sin(rot)], [math.sin(rot), math.cos(rot)]])
        for k in range(8):
            pts = (_petal(k) - FLOWER_C) @ rr.T * breathe + FLOWER_C
            tot = _arclen(pts)[-1]
            pk = seg(p, k * 0.05, k * 0.05 + 0.6)
            draw_yarn(c, pts, 15, [YARN[k % 7]], 0, tot * out_cubic(pk), 999)
        ths = np.linspace(0, 2 * math.pi * 1.04, 120) + rot
        ring = np.stack([FLOWER_C[0] + 46 * np.cos(ths), FLOWER_C[1] + 46 * np.sin(ths)], 1)
        draw_yarn(c, ring, 15, [(255, 196, 0)], 0, _arclen(ring)[-1] * out_cubic(seg(p, 0, 0.6)), 999)
        rnd = random.Random(11)
        for j in range(30):
            ang = rnd.uniform(0, 2 * math.pi)
            rad = rnd.uniform(260, 620)
            ph = rnd.uniform(0, 1)
            tw = 0.5 + 0.5 * math.sin((t - 38.0) * rnd.uniform(5, 9) + ph * 6.28)
            life = seg(t, 38.0 + ph * 0.8, 38.25 + ph * 0.8)
            sparkle(c, FLOWER_C[0] + rad * math.cos(ang), FLOWER_C[1] + rad * math.sin(ang),
                    rnd.uniform(8, 18) * tw * life, life * tw, color=YARN[j % 7] if j % 3 else (255, 200, 60))
    fx["punch"] += 0.07 * decay(t, 38.0, 7)
    fx["shake"] += 12 * decay(t, 38.0, 9)
    ripple(c, t, 38.0, FLOWER_C[0], FLOWER_C[1], YARN[0], 1100, 1.0, 8, 0.55)
    ripple(c, t, 38.12, FLOWER_C[0], FLOWER_C[1], YARN[3], 1100, 1.0, 5, 0.45)
    if t >= 38.0:
        fx["flash"] = (WHITE, 0.75 * decay(t, 38.0, 14))
        fx["cam_scale"] *= 1 + 0.035 * seg(t, 38.0, 40.0)


# ----------------------------------------------------------------------------- composition
def sec_wow_shifted(c, t, fx):
    sec_wow(c, t - WOW_SHIFT, fx)


SECTIONS = [(0.0, 4.0, sec_intro), (4.0, 16.0, sec_pile), (16.0, 28.0, sec_zoom), (28.0, 35.0, sec_wow_shifted),
            (35.0, 39.0, sec_bento), (39.0, CEND, sec_carousel), (CEND, DURATION + 0.01, sec_finale_shifted)]
_GRAIN = None


def grain(k):
    global _GRAIN
    if _GRAIN is None:
        rng = np.random.default_rng(3)
        _GRAIN = [np.clip(ndimage.gaussian_filter(rng.standard_normal((H, W)), 0.7) * 9, -14, 14).astype(np.int16)
                  for _ in range(4)]
    return _GRAIN[k % 4]


def camera(frame, scale, dx, dy, rot):
    if abs(scale - 1) < 1e-4 and abs(dx) < 0.05 and abs(dy) < 0.05 and abs(rot) < 1e-3:
        return frame
    out = Image.new("RGBA", (W, H), BG + (255,))
    place(out, frame, W / 2 + dx, H / 2 + dy, scale, rot=rot)
    return out


def compose(t):
    c = Image.new("RGBA", (W, H), BG + (255,))
    fx = dict(punch=0.0, shake=0.0, vig=0.0, mb=1, flash=None, cam_scale=1.0, cam_dx=0.0, cam_dy=0.0, post=[])
    # au début de la section 2, la pile commence avec le look de l'intro : on garde l'intro jusqu'à 4,0
    for a, b, fn in SECTIONS:
        if a <= t < b:
            fn(c, t, fx)
    if fx["flash"]:
        flash(c, *fx["flash"])
    vignette_pulse(c, fx["vig"])
    rnd = random.Random(int(t * 1000))
    sh = fx["shake"]
    frame = camera(c, fx["cam_scale"] * (1 + fx["punch"]), fx["cam_dx"] + rnd.uniform(-sh, sh),
                   fx["cam_dy"] + rnd.uniform(-sh, sh), rnd.uniform(-sh, sh) * 0.04)
    for fn in fx["post"]:
        fn(frame)
    return frame, fx["mb"]


def render_frame(n):
    t = n / FPS
    frame, mb = compose(t)
    acc = np.asarray(frame.convert("RGB"), np.float32)
    if mb > 1:
        shutter = 0.5 / FPS
        for j in range(1, mb):
            tj = t - shutter / 2 + shutter * j / (mb - 1)
            acc += np.asarray(compose(tj)[0].convert("RGB"), np.float32)
        acc /= mb
    acc += grain(int(t * 12))[..., None]
    return np.clip(acc, 0, 255).astype(np.uint8).tobytes()


def main():
    args = sys.argv[1:]
    if args and args[0] == "--stills":
        load()
        out = os.path.join(BUILD, "stills_collage"); os.makedirs(out, exist_ok=True)
        for a in args[1:]:
            t = float(a)
            Image.frombytes("RGB", (W, H), render_frame(int(round(t * FPS)))).save(
                os.path.join(out, "t%06.2f.jpg" % t), quality=88)
        return
    from multiprocessing import Pool
    if args and args[0] == "--range":
        segs = [(float(args[1]), float(args[2]))]
        final = None
    else:
        segs = [(k * 5.0, k * 5.0 + 5.0) for k in range(int(DURATION // 5))]
        final = os.path.join(BUILD, "collage_silent.mp4")
    # le cache de segments dépend du code : une modification invalide automatiquement les anciens segments
    import hashlib
    here = os.path.dirname(os.path.abspath(__file__))
    sig = hashlib.md5(b"".join(open(os.path.join(here, f), "rb").read() for f in ("collage.py", "render.py")))
    seg_dir = os.path.join(BUILD, "collage_segments", sig.hexdigest()[:10]); os.makedirs(seg_dir, exist_ok=True)
    paths = []
    with Pool(os.cpu_count(), initializer=load) as pool:
        for a, b in segs:
            path = os.path.join(seg_dir, "seg_%05.1f_%05.1f.mp4" % (a, b))
            paths.append(path)
            if final and os.path.exists(path):
                continue  # segment déjà rendu (reprise après interruption)
            tmp = path + ".part.mp4"
            ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                                   "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", tmp],
                                  stdin=subprocess.PIPE)
            start, end = int(round(a * FPS)), int(round(b * FPS))
            for buf in pool.imap(render_frame, range(start, end), chunksize=4):
                ff.stdin.write(buf)
            ff.stdin.close()
            ff.wait()
            os.replace(tmp, path)
            print("segment %.1f–%.1f s ok" % (a, b), flush=True)
    if final:
        lst = os.path.join(seg_dir, "list.txt")
        with open(lst, "w") as f:
            f.writelines("file '%s'\n" % p for p in paths)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                        "-c", "copy", "-movflags", "+faststart", final], check=True)
        print("->", final)


if __name__ == "__main__":
    main()
