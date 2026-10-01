"""Rendu image par image du motion design « Le crochet. Autrement. » (40 s, 1080x1920, 30 i/s).

Toute la timeline est calée sur une grille de 120 BPM : 1 temps = 0,5 s = 15 images.
Usage :
    python3 motion/render.py                 # rendu complet -> build/video_silent.mp4
    python3 motion/render.py --stills 2.7 17.6 ...   # images de contrôle -> build/stills/
"""
import json, math, os, sys, subprocess, random
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
from scipy import ndimage

# ----------------------------------------------------------------------------- réglages
BRAND_NAME = "Maison Crochet"          # <- nom / logo de la marque (écran final)
BRAND_TAGLINE = "LE CROCHET. AUTREMENT."
HANDLES = "@Instagram  •  WhatsApp  •  Site"

W, H, FPS, DURATION = 1080, 1920, 30, 40.0
BPM = 120
BEAT = 60.0 / BPM

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "build")
FONTS = os.path.join(ROOT, "assets", "fonts")

INK = (17, 17, 17)
WHITE = (255, 255, 255)
YARN = [(230, 25, 127), (255, 122, 0), (255, 196, 0), (0, 179, 164), (47, 107, 255), (142, 68, 236), (225, 43, 43)]

# couleur signature de chaque tenue (choisie à l'œil sur les visuels)
LOOK_COLOR = {
    1: "#E8892B", 2: "#F0287F", 3: "#14A89A", 4: "#2E7D32", 5: "#3D8BFF", 6: "#1F4FC9",
    7: "#8E44EC", 8: "#8A5530", 9: "#FF1F6E", 10: "#7A4320", 11: "#1A1A1A", 12: "#FF7A00",
    13: "#2F80ED", 14: "#D61F26", 15: "#C0262D", 16: "#FF4FA3", 17: "#F0388C", 18: "#E9A800",
    19: "#8A5A35", 20: "#7B4B2A", 21: "#1F5FD1", 22: "#FF4F9A", 23: "#5FA8F5", 24: "#E2231A",
}
LOOK_COLOR = {k: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5)) for k, v in LOOK_COLOR.items()}

# placement standard d'un avatar (centre de l'image source -> canvas)
STD_X, STD_Y, STD_S = 540, 1085, 0.92


# ----------------------------------------------------------------------------- maths / easing
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def seg(t, a, b):
    return clamp01((t - a) / (b - a))


def lerp(a, b, x):
    return a + (b - a) * x


def out_cubic(x):
    return 1 - (1 - x) ** 3


def in_cubic(x):
    return x ** 3


def in_out_cubic(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def in_out_sine(x):
    return -(math.cos(math.pi * x) - 1) / 2


def out_expo(x):
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def in_expo(x):
    return 0.0 if x <= 0 else 2 ** (10 * x - 10)


def out_back(x, s=1.70158):
    x = x - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def in_back(x, s=1.70158):
    return (s + 1) * x ** 3 - s * x ** 2


def decay(t, t0, k=8.0):
    return 0.0 if t < t0 else math.exp(-(t - t0) * k)


def mix(c1, c2, x):
    return tuple(int(round(lerp(a, b, x))) for a, b in zip(c1, c2))


def tint(c, x=0.86):
    return mix(c, WHITE, x)


# ----------------------------------------------------------------------------- assets
_IMG = {}


def load_images():
    for i in range(1, 25):
        im = Image.open(os.path.join(BUILD, "cutouts", "article_%02d.png" % i)).convert("RGBA")
        a = np.asarray(im).copy()
        h = a.shape[0]
        # adoucir les bords haut/bas (chignon et pieds touchent le cadre source)
        ramp = np.ones(h)
        ramp[:36] = np.linspace(0, 1, 36) ** 0.8
        ramp[-10:] = np.linspace(1, 0.4, 10)
        a[..., 3] = (a[..., 3] * ramp[:, None]).astype(np.uint8)
        im = Image.fromarray(a)
        # ombre portée au sol
        ys, xs = np.nonzero(a[..., 3] > 128)
        foot = int(np.percentile(ys, 99.7))
        x0, x1 = np.percentile(xs[ys > foot - 120], [3, 97])
        sh = Image.new("L", im.size, 0)
        d = ImageDraw.Draw(sh)
        cx, wdt = (x0 + x1) / 2, (x1 - x0) * 0.62 + 60
        d.ellipse([cx - wdt / 2, foot - 16, cx + wdt / 2, foot + 18], fill=70)
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        base = Image.new("RGBA", im.size, (40, 30, 30, 0))
        base.putalpha(sh)
        base.alpha_composite(im)
        _IMG[i] = base
        _IMG[(i, "half")] = base.reduce(2)


def img(i):
    return _IMG[i]


@lru_cache(maxsize=64)
def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


# ----------------------------------------------------------------------------- placement (affine / perspective)
def _persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def place(canvas, im, cx, cy, s=1.0, rot=0.0, alpha=1.0, anchor=None, sx=1.0, sy=1.0, ry=0.0,
          clip=None, wash=0.0, key=None):
    """Pose `im` (RGBA) sur `canvas` : ancre `anchor` (coords image) -> (cx, cy), échelle s,
    rotation rot (degrés), rotation 3D ry (degrés, perspective), clip=(x0,y0,x1,y1)."""
    if alpha <= 0.003 or s * sx == 0 or s * sy == 0:
        return
    if key is not None and s < 0.55 and (key, "half") in _IMG:
        im = _IMG[(key, "half")]
        s *= 2
        if anchor is not None:
            anchor = (anchor[0] / 2, anchor[1] / 2)
    w, h = im.size
    ax, ay = anchor if anchor is not None else (w / 2, h / 2)
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    cr, sr = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    cyr, syr = math.cos(math.radians(ry)), math.sin(math.radians(ry))
    F = 2200.0
    dst = []
    for (u, v) in src:
        x, y = (u - ax) * s * sx, (v - ay) * s * sy
        if ry:
            z = x * syr
            x = x * cyr
            p = F / (F + z)
            x, y = x * p, y * p
        dst.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    xs = [p[0] for p in dst]; ys = [p[1] for p in dst]
    bx0, by0 = max(int(math.floor(min(xs))), 0), max(int(math.floor(min(ys))), 0)
    bx1, by1 = min(int(math.ceil(max(xs))), canvas.width), min(int(math.ceil(max(ys))), canvas.height)
    if clip:
        bx0, by0 = max(bx0, int(clip[0])), max(by0, int(clip[1]))
        bx1, by1 = min(bx1, int(clip[2])), min(by1, int(clip[3]))
    if bx1 <= bx0 or by1 <= by0:
        return
    local = [(x - bx0, y - by0) for x, y in dst]
    coeffs = _persp_coeffs(local, src)
    layer = im.transform((bx1 - bx0, by1 - by0), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    if wash > 0:
        a = layer.getchannel("A")
        layer = Image.blend(layer, Image.new("RGBA", layer.size, (255, 255, 255, 255)), min(wash, 1.0))
        layer.putalpha(a)
    if alpha < 1:
        layer.putalpha(layer.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(layer, (bx0, by0))


def avatar(canvas, i, cx=STD_X, cy=STD_Y, s=STD_S, **kw):
    place(canvas, img(i), cx, cy, s, key=i, **kw)


def closeup(canvas, i, spec, zoom=1.0, rot=0.0, dx=0.0, dy=0.0, alpha=1.0, wash=0.0):
    ax, ay, cw = spec
    s = W / cw * zoom
    place(canvas, img(i), W / 2 + dx, H / 2 + dy, s, rot=rot, anchor=(ax, ay), alpha=alpha, wash=wash)


# ----------------------------------------------------------------------------- texte
@lru_cache(maxsize=512)
def text_img(text, fname, size, color, tracking=0, stroke=0, outline_only=False):
    f = font(fname, size)
    asc, desc = f.getmetrics()
    pad = 8 + stroke * 2
    widths = [f.getlength(c) for c in text]
    tw = sum(widths) + tracking * max(len(text) - 1, 0)
    im = Image.new("L", (int(tw + 2 * pad), asc + desc + 2 * pad), 0)
    d = ImageDraw.Draw(im)
    x = pad
    for c, wc in zip(text, widths):
        d.text((x, pad), c, font=f, fill=255, stroke_width=stroke, stroke_fill=255)
        x += wc + tracking
    if outline_only:
        fill = Image.new("L", im.size, 0)
        d2 = ImageDraw.Draw(fill)
        x = pad
        for c, wc in zip(text, widths):
            d2.text((x, pad), c, font=f, fill=255)
            x += wc + tracking
        im = ImageChops.subtract(im, fill)
    bb = im.getbbox() or (0, 0, 1, 1)
    out = Image.new("RGBA", im.size, color + (0,))
    out.putalpha(im)
    # recadrage vertical serré sur l'encre (le centrage visuel se fait sur la hauteur des capitales)
    return out.crop((0, bb[1] - 2, im.width, bb[3] + 2))


def text(canvas, s, fname, size, color, cx, cy, tracking=0, scale=1.0, alpha=1.0, rot=0.0, **kw):
    im = text_img(s, fname, size, tuple(color), tracking)
    place(canvas, im, cx, cy, scale, rot=rot, alpha=alpha, **kw)
    return im.size


def fit_size(s, fname, width, max_size, tracking=0):
    size = max_size
    while size > 20 and text_img(s, fname, size, INK, tracking).width > width:
        size -= 4
    return size


def text_letters(canvas, s, fname, size, color, cx, cy, t, t0, stagger=0.035, dur=0.32, tracking=0,
                 drop=70, alpha=1.0, mode="drop"):
    """Lettres qui tombent une à une (overshoot)."""
    f = font(fname, size)
    widths = [f.getlength(c) for c in s]
    tw = sum(widths) + tracking * (len(s) - 1)
    x = cx - tw / 2
    full = text_img(s, fname, size, tuple(color), tracking)
    hh = full.height
    for k, (c, wc) in enumerate(zip(s, widths)):
        p = seg(t, t0 + k * stagger, t0 + k * stagger + dur)
        if p > 0 and c != " ":
            li = text_img(c, fname, size, tuple(color), 0)
            # garder la ligne de base commune : on recadre avec la même hauteur que le mot entier
            e = out_back(p, 2.2) if mode == "drop" else out_expo(p)
            yy = cy - (1 - e) * drop
            sc = 1.0 if mode == "drop" else lerp(1.8, 1.0, out_expo(p))
            place(canvas, li, x + wc / 2, yy + _baseline_shift(c, fname, size, hh), sc,
                  alpha=alpha * clamp01(p * 3))
        x += wc + tracking


@lru_cache(maxsize=2048)
def _baseline_shift(c, fname, size, hh):
    """Décalage vertical d'un glyphe isolé pour qu'il retombe sur la ligne de base du mot."""
    f = font(fname, size)
    bb = f.getbbox(c)
    ref = f.getbbox("H")
    glyph_center = (bb[1] + bb[3]) / 2
    word_center = (ref[1] + ref[3]) / 2
    return glyph_center - word_center


def text_mask_reveal(canvas, s, fname, size, color, cx, cy, p, tracking=0, direction=1, alpha=1.0):
    """Texte qui monte depuis un masque (p: 0->1 entrée ; direction=-1 pour sortie vers le haut)."""
    im = text_img(s, fname, size, tuple(color), tracking)
    h = im.height
    off = (1 - out_expo(p)) * h * 1.1 * direction
    place(canvas, im, cx, cy + off, 1.0, alpha=alpha,
          clip=(0, cy - h / 2 - 6, W, cy + h / 2 + 6))


def pill(canvas, s, cx, cy, t, t0, t1, fname="Anton.ttf", size=88, bg=INK, fg=WHITE, padx=34, pady=22):
    """Étiquette noire façon « tag mode » qui s'ouvre horizontalement."""
    if t < t0 or t > t1:
        return
    ti = text_img(s, fname, size, fg, 2)
    pw, ph = ti.width + 2 * padx, ti.height + 2 * pady
    pin = out_expo(seg(t, t0, t0 + 0.22))
    pout = in_cubic(seg(t, t1 - 0.14, t1))
    wcur = pw * pin * (1 - pout)
    if wcur < 4:
        return
    x0, y0 = cx - wcur / 2, cy - ph / 2
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([x0, y0, x0 + wcur, y0 + ph], radius=10, fill=bg + (255,))
    off = (1 - out_expo(seg(t, t0 + 0.05, t0 + 0.3))) * ph
    place(canvas, ti, cx, cy + off, 1.0, clip=(x0 + 6, y0 + 4, x0 + wcur - 6, y0 + ph - 4))


# ----------------------------------------------------------------------------- fils de crochet
def catmull(points, n=24):
    P = np.array(points, float)
    P = np.vstack([P[0], P, P[-1]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for tt in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = tt * tt, tt * tt * tt
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * tt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-2])
    return np.array(out)


def _arclen(pts):
    d = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
    return np.concatenate([[0], np.cumsum(d)])


def sub_path(pts, L0, L1):
    """Portion de la polyline entre les abscisses curvilignes L0 et L1 (retourne pts, abscisses)."""
    s = _arclen(pts)
    L0, L1 = max(L0, 0), min(L1, s[-1])
    if L1 - L0 < 1:
        return None, None
    grid = np.arange(L0, L1, 3.0)
    grid = np.append(grid, L1)
    x = np.interp(grid, s, pts[:, 0]); y = np.interp(grid, s, pts[:, 1])
    return np.stack([x, y], 1), grid


def draw_yarn(canvas, pts, width=12, colors=None, L0=0.0, L1=None, seglen=150.0, alpha=1.0, shadow=True):
    """Fil de laine torsadé (multicolore « chiné »), anti-aliasé par sur-échantillonnage x2."""
    if pts is None or len(pts) < 2:
        return
    total = _arclen(pts)[-1]
    if L1 is None:
        L1 = total
    p, sabs = sub_path(pts, L0, L1)
    if p is None:
        return
    colors = colors or YARN
    m = width * 2 + 20
    x0, y0 = int(p[:, 0].min() - m), int(p[:, 1].min() - m)
    x1, y1 = int(p[:, 0].max() + m), int(p[:, 1].max() + m)
    cx0, cy0, cx1, cy1 = max(x0, 0), max(y0, 0), min(x1, W), min(y1, H)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    SS = 2
    lw, lh = (x1 - x0) * SS, (y1 - y0) * SS
    q = (p - [x0, y0]) * SS
    wpx = width * SS
    lay = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    if shadow:
        shm = Image.new("L", (lw, lh), 0)
        ImageDraw.Draw(shm).line([tuple(v) for v in (q + [5 * SS, 7 * SS])], fill=60, width=int(wpx), joint="curve")
        shm = shm.filter(ImageFilter.GaussianBlur(6 * SS))
        shl = Image.new("RGBA", (lw, lh), (60, 40, 40, 0))
        shl.putalpha(shm)
        lay.alpha_composite(shl)
    d = ImageDraw.Draw(lay)
    # tangentes / normales
    tg = np.gradient(q, axis=0)
    tg /= (np.linalg.norm(tg, axis=1, keepdims=True) + 1e-6)
    nm = np.stack([-tg[:, 1], tg[:, 0]], 1)
    cidx = (sabs // seglen).astype(int) % len(colors)
    # corps du fil, segment de couleur par segment de couleur
    start = 0
    for k in range(1, len(q) + 1):
        if k == len(q) or cidx[k] != cidx[start]:
            chunk = q[start:min(k + 1, len(q))]
            col = colors[cidx[start]]
            if len(chunk) >= 2:
                d.line([tuple(v) for v in chunk], fill=col + (255,), width=int(wpx), joint="curve")
            for e in (chunk[0], chunk[-1]):
                d.ellipse([e[0] - wpx / 2 + 0.5, e[1] - wpx / 2 + 0.5, e[0] + wpx / 2 - 0.5, e[1] + wpx / 2 - 0.5],
                          fill=col + (255,))
            start = k
    # torsade : petits traits obliques plus sombres
    step = max(int(round(width * 1.0 / 3.0)), 1)
    for k in range(0, len(q), step):
        col = colors[cidx[k]]
        dark = mix(col, (0, 0, 0), 0.32)
        a = q[k] - nm[k] * wpx * 0.42 - tg[k] * wpx * 0.30
        b = q[k] + nm[k] * wpx * 0.42 + tg[k] * wpx * 0.30
        d.line([tuple(a), tuple(b)], fill=dark + (150,), width=max(int(wpx * 0.16), 1))
    # reflet
    hl = q - nm * wpx * 0.2
    d.line([tuple(v) for v in hl], fill=(255, 255, 255, 70), width=max(int(wpx * 0.14), 1), joint="curve")
    lay = lay.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    if alpha < 1:
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * alpha)))
    lay = lay.crop((cx0 - x0, cy0 - y0, cx1 - x0, cy1 - y0))
    canvas.alpha_composite(lay, (cx0, cy0))


def orbit(cx, cy, rx, ry, phase, span=0.75, tilt=0.0, n=220):
    """Ellipse partielle autour d'un personnage. Retourne (pts, z) ; z<0 = derrière."""
    th = phase + np.linspace(0, 2 * math.pi * span, n)
    x = cx + rx * np.cos(th)
    y = cy + ry * np.sin(th) + tilt * np.cos(th)
    z = np.sin(th)
    return np.stack([x, y], 1), z


def draw_orbit(canvas, cx, cy, rx, ry, phase, layer, colors, width=11, span=0.75, tilt=0.0, grow=1.0, alpha=1.0):
    pts, z = orbit(cx, cy, rx, ry, phase, span * grow, tilt)
    front = z >= 0
    # découper en tronçons contigus devant / derrière
    runs, start = [], 0
    for k in range(1, len(pts) + 1):
        if k == len(pts) or front[k] != front[start]:
            runs.append((front[start], max(start - 1, 0), k))
            start = k
    s = _arclen(pts)
    for is_front, a, b in runs:
        if is_front == (layer == "front") and b - a >= 2:
            draw_yarn(canvas, pts, width, colors, s[a], s[b - 1], alpha=alpha, shadow=is_front)


# ----------------------------------------------------------------------------- effets globaux
_VIG = None


def vignette_pulse(canvas, amount):
    global _VIG
    if amount <= 0.004:
        return
    if _VIG is None:
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2)
        _VIG = Image.fromarray((np.clip(r - 0.35, 0, 1) ** 1.6 * 255).astype(np.uint8))
    a = _VIG.point(lambda v: int(v * amount))
    lay = Image.new("RGBA", (W, H), (20, 10, 15, 0))
    lay.putalpha(a)
    canvas.alpha_composite(lay)


def ripple(canvas, t, t0, cx=W / 2, cy=H / 2, color=INK, maxr=950, dur=0.9, width=4, strength=0.35):
    if t < t0 or t > t0 + dur:
        return
    p = clamp01((t - t0) / dur)
    r = 60 + maxr * out_cubic(p)
    a = int(255 * strength * (1 - p) ** 1.5)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse([cx - r, cy - r, cx + r, cy + r], outline=color + (a,), width=width)
    canvas.alpha_composite(lay)


def flash(canvas, color, a):
    if a > 0.004:
        canvas.alpha_composite(Image.new("RGBA", (W, H), tuple(color) + (int(255 * min(a, 1)),)))


def camera(frame, scale=1.0, dx=0.0, dy=0.0, rot=0.0):
    if abs(scale - 1) < 1e-4 and abs(dx) < 0.05 and abs(dy) < 0.05 and abs(rot) < 1e-3:
        return frame
    out = Image.new("RGBA", (W, H), WHITE + (255,))
    place(out, frame, W / 2 + dx, H / 2 + dy, scale, rot=rot)
    return out


def sparkle(canvas, x, y, r, a, color=(255, 200, 60)):
    if a <= 0.01 or r < 1:
        return
    lay_sz = int(r * 2.4 + 8)
    lay = Image.new("RGBA", (lay_sz * 2, lay_sz * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = lay_sz
    R = r * 2
    pts = [(c, c - R), (c + R * 0.22, c - R * 0.22), (c + R, c), (c + R * 0.22, c + R * 0.22),
           (c, c + R), (c - R * 0.22, c + R * 0.22), (c - R, c), (c - R * 0.22, c - R * 0.22)]
    d.polygon(pts, fill=color + (int(255 * a),))
    lay = lay.resize((lay_sz, lay_sz), Image.LANCZOS)
    canvas.alpha_composite(lay, (int(x - lay_sz / 2), int(y - lay_sz / 2)))


# ----------------------------------------------------------------------------- 0–4 s : INTRO / SUSPENSE
INTRO_PATH = catmull([(-260, 1300), (120, 1090), (380, 1210), (560, 980), (700, 820), (560, 700),
                      (470, 820), (640, 960), (880, 900), (1060, 1040), (1380, 900)], n=30)
BOOMS = [0.5, 1.5, 2.5]


def sec_intro(c, t, fx):
    total = _arclen(INTRO_PATH)[-1]
    # le fil traverse l'écran au ralenti
    head = lerp(0, total + 900, in_out_sine(seg(t, 0.0, 3.6)) * 0.55 + seg(t, 0.0, 3.6) * 0.45)
    tail = head - 1100
    # avatar 02 — zoom cinématique au 3e impact
    if t >= 2.5:
        p = seg(t, 2.5, 3.25)
        s = STD_S * (1 + 1.25 * (1 - out_expo(p))) * (1 + 0.035 * seg(t, 3.25, 4.0))
        rot = -7 * (1 - out_expo(p))
        a = seg(t, 2.5, 2.58)
        if t > 3.84:  # sortie « zoom » vers la section 2
            q = in_cubic(seg(t, 3.84, 4.0))
            s *= 1 + 1.4 * q
            a *= 1 - q
        avatar(c, 2, s=s, rot=rot, alpha=a, wash=0.8 * (1 - seg(t, 2.5, 2.7)))
    draw_yarn(c, INTRO_PATH, width=14, L0=tail, L1=head, seglen=170)
    # textes
    if 1.5 <= t < 4.0:
        p = seg(t, 1.5, 1.85)
        sc = lerp(1.45, 1.0, out_expo(p))
        mv = in_out_cubic(seg(t, 2.5, 2.85))
        y = lerp(960, 168, mv)
        sc *= lerp(1.0, 0.78, mv)
        out = seg(t, 3.84, 4.0)
        if out <= 0:
            text(c, "LE CROCHET.", "Anton.ttf", 190, INK, W / 2, y, tracking=4, scale=sc, alpha=clamp01(p * 4))
        else:
            text_mask_reveal(c, "LE CROCHET.", "Anton.ttf", 148, INK, W / 2, 168, 1 - out, tracking=3, direction=-1)
    if 2.9 <= t < 4.0:
        out = seg(t, 3.84, 4.0)
        if out <= 0:
            text_letters(c, "Autrement.", "Playfair-BlackItalic.ttf", 120, LOOK_COLOR[2], W / 2, 300, t, 2.9,
                         stagger=0.04, dur=0.35)
        else:
            text_mask_reveal(c, "Autrement.", "Playfair-BlackItalic.ttf", 120, LOOK_COLOR[2], W / 2, 300,
                             1 - out, direction=-1)
    for b in BOOMS:
        ripple(c, t, b, color=(40, 40, 40) if b < 2.5 else LOOK_COLOR[2], strength=0.25 if b < 2.5 else 0.45,
               width=3 if b < 2.5 else 6)
        fx["punch"] += (0.022 if b < 2.5 else 0.05) * decay(t, b, 9)
        fx["vig"] += (0.35 if b < 2.5 else 0.25) * decay(t, b, 5)
    if 2.5 <= t < 2.9:
        fx["mb"] = 5
    fx["shake"] += 10 * decay(t, 2.5, 10)


# ----------------------------------------------------------------------------- 4–10 s : PREMIERS LOOKS
S2_LOOKS = [(4.0, 5, "zoom"), (5.0, 12, "flash"), (6.0, 16, "slide"), (7.0, 1, "rotate"), (8.0, 9, "whoosh"),
            (9.0, 18, "zoom")]
S2_WORDS = [("AUDACIEUX.", 4.05, 6.0), ("COLORÉ.", 6.0, 8.0), ("UNIQUE.", 8.0, 10.0)]


def look_transition(c, t, prev, nxt, kind, tb, fx, idle_from=None):
    """Dessine la paire de tenues autour du changement tb (sur le beat)."""
    def idle(i, t0):
        k = seg(t, t0, t0 + 1.0)
        return STD_S * (1 + 0.03 * k)

    if kind == "zoom":
        if t < tb and prev:
            q = in_cubic(seg(t, tb - 0.16, tb))
            avatar(c, prev, s=idle(prev, tb - 1) * (1 + 1.3 * q), alpha=1 - q)
        if t >= tb:
            p = seg(t, tb, tb + 0.32)
            avatar(c, nxt, s=idle(nxt, tb) * lerp(0.55, 1.0, out_back(p, 1.6)), alpha=clamp01(p * 5))
        if tb - 0.16 <= t < tb + 0.2:
            fx["mb"] = 5
    elif kind == "flash":
        if t < tb and prev:
            q = seg(t, tb - 0.12, tb)
            avatar(c, prev, s=idle(prev, tb - 1), wash=q)
        if t >= tb:
            p = seg(t, tb, tb + 0.3)
            avatar(c, nxt, s=idle(nxt, tb) * lerp(1.06, 1.0, out_expo(p)), wash=1 - out_cubic(p))
            fx["flash"] = (LOOK_COLOR[nxt], 0.55 * (1 - seg(t, tb, tb + 0.1)))
    elif kind == "slide":
        p = seg(t, tb - 0.1, tb + 0.16)
        e = out_expo(p) if p > 0 else 0
        if prev and e < 1:
            avatar(c, prev, s=idle(prev, tb - 1), cx=STD_X - W * 1.15 * e)
        if p > 0:
            avatar(c, nxt, s=idle(nxt, tb), cx=STD_X + W * 1.15 * (1 - e))
        if 0 < p < 0.8:
            fx["mb"] = 6
    elif kind == "rotate":
        if t < tb and prev:
            q = in_cubic(seg(t, tb - 0.16, tb))
            avatar(c, prev, s=idle(prev, tb - 1) * (1 - 0.45 * q), rot=55 * q, alpha=1 - q)
        if t >= tb:
            p = seg(t, tb, tb + 0.34)
            avatar(c, nxt, s=idle(nxt, tb) * lerp(0.55, 1.0, out_back(p, 1.4)), rot=-55 * (1 - out_cubic(p)),
                   alpha=clamp01(p * 4))
        if tb - 0.16 <= t < tb + 0.22:
            fx["mb"] = 5
    elif kind == "whoosh":
        p = seg(t, tb - 0.1, tb + 0.14)
        e = out_expo(p) if p > 0 else 0
        stretch = 1 + 0.25 * math.sin(math.pi * p)
        if prev and e < 1:
            avatar(c, prev, s=idle(prev, tb - 1), cy=STD_Y - H * 1.1 * e, sy=stretch)
        if p > 0:
            avatar(c, nxt, s=idle(nxt, tb), cy=STD_Y + H * 1.1 * (1 - e), sy=stretch)
        if 0 < p < 0.85:
            fx["mb"] = 6


def sec_looks(c, t, fx):
    # tenue courante / précédente
    k = max(i for i, (tb, _, _) in enumerate(S2_LOOKS) if t >= tb - 0.17) if t >= S2_LOOKS[0][0] - 0.17 else 0
    tb, nxt, kind = S2_LOOKS[k]
    prev = S2_LOOKS[k - 1][1] if k > 0 else None
    if k == 0 and t < tb:
        return  # (l'intro gère la sortie de l'avatar 02)
    if t >= 9.82:
        # zoom avant vers le premier gros plan de la section 3
        q = in_expo(seg(t, 9.82, 10.0))
        s = STD_S * 1.03 * (1 + 2.0 * q)
        avatar(c, nxt, s=s, cy=STD_Y + 250 * q)
        fx["mb"] = 5
    else:
        look_transition(c, t, prev, nxt, kind, tb, fx)
    # mots cinétiques
    for word, t0, t1 in S2_WORDS:
        if t0 <= t < t1:
            col = LOOK_COLOR[[l for (b, l, _) in S2_LOOKS if b <= t + 0.001][-1]]
            if t < t1 - 0.16:
                text_letters(c, word, "Anton.ttf", 196, col, W / 2, 200, t, t0, stagger=0.045, dur=0.34, tracking=6)
            else:
                text_mask_reveal(c, word, "Anton.ttf", 196, col, W / 2, 200, 1 - seg(t, t1 - 0.16, t1),
                                 tracking=6, direction=-1)
    # petits accents graphiques : fil qui balaie sur chaque changement
    for tb_, l, kd in S2_LOOKS:
        if tb_ - 0.12 <= t < tb_ + 0.3:
            p = seg(t, tb_ - 0.12, tb_ + 0.3)
            pts = catmull([(-100, 1500), (300, 1380), (700, 1520), (1180, 1360)], 20)
            tot = _arclen(pts)[-1]
            draw_yarn(c, pts, 10, [LOOK_COLOR[l], (255, 196, 0)], tot * in_cubic(p), tot * out_expo(p), 90)
    fx["punch"] += sum(0.02 * decay(t, tb_, 10) for tb_, _, _ in S2_LOOKS)


# ----------------------------------------------------------------------------- 10–17 s : ACCÉLÉRATION
S3_SHOTS = [
    (10.0, 0.5, "cu", 13, (560, 1130, 400)),
    (10.5, 0.5, "full", 13, None),
    (11.0, 0.5, "cu", 10, (500, 1140, 400)),
    (11.5, 0.5, "full", 10, None),
    (12.0, 0.5, "cu", 15, (520, 800, 400)),
    (12.5, 0.5, "full", 15, None),
    (13.0, 0.5, "cu", 17, (500, 1190, 400)),
    (13.5, 0.5, "full", 17, None),
    (14.0, 0.5, "cu", 23, (500, 760, 400)),
    (14.5, 0.5, "full", 23, None),
    (15.0, 0.5, "cu", 20, (470, 1060, 400)),
    (15.5, 0.5, "full", 20, None),
    (16.0, 0.25, "cu", 24, (520, 640, 380)),
    (16.25, 0.25, "cu", 2, (560, 980, 400)),
    (16.5, 0.25, "cu", 12, (520, 1040, 400)),
    (16.75, 0.25, "cu", 3, (310, 520, 400)),
]
S3_TAGS = [("CHAQUE MAILLE.", 10.0, 11.0), ("CHAQUE COULEUR.", 11.0, 12.0), ("CHAQUE DÉTAIL…", 12.0, 13.0),
           ("PENSÉ POUR SE FAIRE REMARQUER.", 13.05, 15.0)]


def sec_accel(c, t, fx):
    for n, (st, du, kind, i, spec) in enumerate(S3_SHOTS):
        if st <= t < st + du:
            p = seg(t, st, st + du)
            if kind == "cu":
                pin = out_expo(seg(t, st, st + 0.16))
                zoom = lerp(1.18, 1.0, pin) * (1 + 0.06 * p)
                sgn = 1 if n % 4 == 0 else -1
                closeup(c, i, spec, zoom=zoom, rot=sgn * 2.0 * p, dx=sgn * 30 * (1 - pin))
                # anneau de fil autour du détail
                ring_p = seg(t, st + 0.02, st + min(du, 0.4))
                if ring_p > 0 and du >= 0.5:
                    th0 = -math.pi / 2 + sgn * 0.6
                    ths = th0 + np.linspace(0, 2 * math.pi * out_cubic(ring_p) * 1.08, 160)
                    R = 300 + 20 * p
                    pts = np.stack([W / 2 + R * np.cos(ths), H / 2 + 120 + R * 1.05 * np.sin(ths)], 1)
                    draw_yarn(c, pts, 13, [WHITE, (255, 196, 0)], seglen=70)
                if t < st + 0.12:
                    fx["mb"] = 4
            else:
                pin = out_expo(seg(t, st, st + 0.2))
                s = STD_S * lerp(1.32, 1.0, pin) * (1 + 0.02 * p)
                avatar(c, i, s=s)
                if t < st + 0.12:
                    fx["mb"] = 4
            fx["punch"] += 0.025 * decay(t, st, 12)
    for s_, t0, t1 in S3_TAGS:
        size = 88 if len(s_) < 20 else 60
        pill(c, s_, W / 2, 200, t, t0, t1, size=size)


# ----------------------------------------------------------------------------- 17–24 s : MOMENT WOW
S4_LOOKS = [(17.0, 23), (18.0, 18), (18.5, 22), (19.0, 17), (19.5, 15), (20.0, 24)]
S4_STACK = [("NE", 21.5), ("JAMAIS", 22.0), ("PASSER", 22.5), ("INAPERÇUE.", 23.0)]
S4_STACK_Y = [520, 790, 1060, 1330]
STACK_X, STACK_W = 56, 640


def _s4_current(t):
    cur, prev, tb = S4_LOOKS[0][1], None, S4_LOOKS[0][0]
    for b, l in S4_LOOKS:
        if t >= b:
            prev, cur, tb = cur, l, b
    return prev, cur, tb


def _stack(c, t, dy, outline):
    for (wd, ts), y in zip(S4_STACK, S4_STACK_Y):
        if t >= ts:
            p = seg(t, ts, ts + 0.22)
            size = fit_size(wd, "Anton.ttf", STACK_W, 280, 6)
            col = INK if wd in ("NE", "PASSER") else LOOK_COLOR[24]
            im = text_img(wd, "Anton.ttf", size, col, 6, 3 if outline else 0, outline)
            sc = lerp(1.35, 1.0, out_expo(p))
            place(c, im, STACK_X + im.width / 2, y + dy, sc, anchor=(im.width / 2, im.height / 2),
                  alpha=(0.9 if outline else 1.0) * clamp01(p * 4))


def sec_wow(c, t, fx):
    prev, cur, tb = _s4_current(t)
    exit_q = in_cubic(seg(t, 23.62, 24.0))
    if exit_q > 0:
        fx["mb"] = 6
    dy = -H * 1.1 * exit_q
    colr = LOOK_COLOR[cur]
    # gros texte empilé (derrière l'avatar)
    _stack(c, t, dy, False)
    mv = out_expo(seg(t, 21.05, 21.5))
    ox, osc = lerp(STD_X, 770, mv), lerp(1.0, 0.82, mv)
    # orbites de fils (arrière)
    orb_a = seg(t, 17.5, 17.7) * (1 - exit_q)
    if t >= 17.5:
        ph = (t - 17.5) * 2.4
        grow = out_cubic(seg(t, 17.5, 18.2))
        draw_orbit(c, ox, 1150 + dy + 60 * mv, 420 * osc, 110 * osc, ph, "back", [colr, (255, 196, 0)], 12, 0.8, -40, grow, orb_a)
        draw_orbit(c, ox, 760 + dy + 120 * mv, 360 * osc, 80 * osc, -ph * 1.3 + 2, "back", [YARN[0], YARN[3]], 10, 0.7, 30, grow, orb_a)
    # avatar + changement de tenue par balayage
    bump = 1 + 0.045 * decay(t, tb, 9) if t >= 18.0 else 1
    push = 1 + 0.03 * seg(t, 20.0, 23.6)
    s = STD_S * bump * push * osc
    wipe_d = 0.14
    if prev is not None and t < tb + wipe_d:
        edge = lerp(250, 1900, out_cubic(seg(t, tb, tb + wipe_d)))
        avatar(c, prev, s=s, cy=STD_Y + dy, clip=(0, edge, W, H))
        avatar(c, cur, s=s, cy=STD_Y + dy, clip=(0, 0, W, edge))
        xs = np.linspace(-40, W + 40, 60)
        pts = np.stack([xs, edge + 22 * np.sin(xs / 90 + t * 20)], 1)
        draw_yarn(c, pts, 12, [colr, (255, 255, 255), (255, 196, 0)], seglen=110)
    else:
        avatar(c, cur, s=s, cx=ox, cy=STD_Y + dy + 120 * mv)
    # contour (devant) du gros texte : lisible même derrière l'avatar
    _stack(c, t, dy, True)
    if t >= 17.5:
        ph = (t - 17.5) * 2.4
        grow = out_cubic(seg(t, 17.5, 18.2))
        draw_orbit(c, ox, 1150 + dy + 60 * mv, 420 * osc, 110 * osc, ph, "front", [colr, (255, 196, 0)], 12, 0.8, -40, grow, orb_a)
        draw_orbit(c, ox, 760 + dy + 120 * mv, 360 * osc, 80 * osc, -ph * 1.3 + 2, "front", [YARN[0], YARN[3]], 10, 0.7, 30, grow, orb_a)
    # BOOM : fils qui jaillissent
    if 17.5 <= t < 18.3:
        p = seg(t, 17.5, 18.3)
        for k in range(8):
            ang = k * math.pi / 4 + 0.3
            pts = np.array([(W / 2 + r * math.cos(ang + 0.0004 * r), 980 + r * math.sin(ang + 0.0004 * r))
                            for r in np.linspace(0, 1400, 40)])
            tot = _arclen(pts)[-1]
            draw_yarn(c, pts, 9, [YARN[k % 7], YARN[(k + 2) % 7]], tot * out_cubic(seg(p, 0.15, 1)) * 0.9 + 120,
                      tot * out_expo(p) + 160, 120, shadow=False)
    # « LOOK 0n »
    if 18.0 <= t < 20.6:
        n = sum(1 for b, _ in S4_LOOKS[1:] if t >= b)
        a_out = seg(t, 20.45, 20.6)
        sz = text_img("LOOK", "Anton.ttf", 170, INK, 6).size
        x_look = W / 2 - 80
        text_mask_reveal(c, "LOOK", "Anton.ttf", 170, INK, x_look, 200, seg(t, 18.0, 18.25) * (1 - a_out),
                         tracking=6)
        # compteur façon roulette
        bb = 200
        for j in range(1, 6):
            b = S4_LOOKS[j][0]
            num = "%02d" % j
            nx = x_look + sz[0] / 2 + 95
            if j == n:
                p = seg(t, b, b + 0.16)
                place(c, text_img(num, "Playfair-BlackItalic.ttf", 150, LOOK_COLOR[S4_LOOKS[j][1]]),
                      nx, bb + (1 - out_expo(p)) * 150, 1, clip=(0, 110, W, 290), alpha=1 - a_out)
            elif j == n - 1:
                b2 = S4_LOOKS[j + 1][0]
                p = seg(t, b2, b2 + 0.16)
                if p < 1:
                    place(c, text_img(num, "Playfair-BlackItalic.ttf", 150, LOOK_COLOR[S4_LOOKS[j][1]]),
                          nx, bb - out_expo(p) * 150, 1, clip=(0, 110, W, 290))
    pill(c, "UNE SEULE RÈGLE :", W / 2, 200, t, 20.6, 21.45, size=80)
    # pas de musique 17.0–17.5 : image figée, puis BOOM
    fx["punch"] += 0.07 * decay(t, 17.5, 7) + sum(0.03 * decay(t, b, 11) for b, _ in S4_LOOKS[1:])
    fx["punch"] += sum(0.03 * decay(t, ts, 10) for _, ts in S4_STACK)
    fx["shake"] += 18 * decay(t, 17.5, 7)
    fx["vig"] += 0.5 * decay(t, 17.5, 4)
    ripple(c, t, 17.5, cy=1000, color=YARN[0], width=8, strength=0.6, dur=0.8)
    ripple(c, t, 17.6, cy=1000, color=YARN[2], width=5, strength=0.5, dur=0.8)


# ----------------------------------------------------------------------------- 24–31 s : COLLECTION
GAP = 14
TOP, BOT = 360, 1640


@lru_cache(maxsize=64)
def cell(i, w, h, ax, ay, s, radius=26):
    """Case de grille : fond teinté + avatar recadré, coins arrondis."""
    w, h = int(w), int(h)
    im = Image.new("RGBA", (w, h), tint(LOOK_COLOR[i], 0.84) + (255,))
    place(im, img(i), w / 2, h / 2, s, anchor=(ax, ay), key=i)
    m = Image.new("L", (w * 2, h * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], radius=radius * 2, fill=255)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), m.resize((w, h), Image.LANCZOS)))
    return im


def _panels():
    pw = (W - 4 * GAP) / 3
    return [(GAP + k * (pw + GAP) + pw / 2, (TOP + BOT) / 2, pw, BOT - TOP) for k in range(3)]


def _grid2():
    cw, ch = (W - 3 * GAP) / 2, (BOT - TOP - GAP) / 2
    return [(GAP + (k % 2) * (cw + GAP) + cw / 2, TOP + (k // 2) * (ch + GAP) + ch / 2, cw, ch) for k in range(4)]


def _grid3():
    cw, ch = (W - 4 * GAP) / 3, (BOT - TOP - 2 * GAP) / 3
    return [(GAP + (k % 3) * (cw + GAP) + cw / 2, TOP + (k // 3) * (ch + GAP) + ch / 2, cw, ch) for k in range(9)]


def _content(i, kind):
    couple = i in (3, 4, 6, 7, 8, 11, 14, 19, 21)
    if kind == "panel":
        return (512, 830, 0.66)
    if kind == "g2":
        return (512, 700, 0.56) if couple else (512, 640, 0.6)
    return (512, 640, 0.37) if couple else (512, 560, 0.5)


S5_A1, S5_A2 = [9, 16, 22], [12, 15, 24]
S5_B = [3, 4, 6, 7]
S5_C = [2, 14, 5, 19, 21, 11, 13, 8, 12]


def sec_collection(c, t, fx):
    # Phase A : 3 panneaux verticaux (glissent, puis pivotent)
    if t < 27.05:
        for k, (x, y, w, h) in enumerate(_panels()):
            t_in = 24.0 + 0.08 * k
            p = seg(t, t_in, t_in + 0.38)
            if p <= 0:
                continue
            off = (1 - out_expo(p)) * (H + 200) * (-1 if k % 2 == 0 else 1)
            tf = 25.5 + 0.07 * k
            f = seg(t, tf, tf + 0.3)
            i = S5_A1[k] if f < 0.5 else S5_A2[k]
            sx = abs(math.cos(math.pi * f))
            ax, ay, s = _content(i, "panel")
            im = cell(i, w, h, ax, ay, s)
            q = in_cubic(seg(t, 26.82 + 0.05 * k, 27.02 + 0.05 * k))
            place(c, im, x, y + off, 1 - q, rot=-90 * q, sx=max(sx, 0.001), alpha=1 - q * 0.3)
            if p < 0.6 or 0 < q < 1:
                fx["mb"] = 5
    # Phase B : 2x2 ensembles femme/homme (pivotent en entrée)
    if 26.9 <= t < 28.7:
        for k, (x, y, w, h) in enumerate(_grid2()):
            t_in = 26.95 + 0.06 * k
            p = seg(t, t_in, t_in + 0.4)
            if p <= 0:
                continue
            i = S5_B[k]
            ax, ay, s = _content(i, "g2")
            im = cell(i, w, h, ax, ay, s)
            q = in_cubic(seg(t, 28.32, 28.52))
            dx = (-1 if k % 2 == 0 else 1) * (W * 0.75) * q
            place(c, im, x + dx, y, lerp(0.2, 1.0, out_back(p, 1.3)), rot=90 * (1 - out_cubic(p)),
                  alpha=clamp01(p * 3))
            if p < 0.7 or q > 0:
                fx["mb"] = 5
    # Phase C : grille 3x3 (rangées alternées), Phase D : fusion vers la case centrale
    if t >= 28.45:
        g = _grid3()
        mq = out_cubic(seg(t, 30.0, 30.4))
        for k, (x, y, w, h) in enumerate(g):
            if k == 4:
                continue
            row = k // 3
            t_in = 28.5 + 0.05 * row
            p = seg(t, t_in, t_in + 0.36)
            if p <= 0:
                continue
            dirn = 1 if row % 2 == 0 else -1
            off = (1 - out_expo(p)) * W * dirn
            i = S5_C[k]
            ax, ay, s = _content(i, "g3")
            im = cell(i, w, h, ax, ay, s)
            cx0, cy0 = g[4][0], g[4][1]
            place(c, im, lerp(x, cx0, mq) + off, lerp(y, cy0, mq), lerp(1, 0.4, mq), alpha=1 - mq)
            if p < 0.7:
                fx["mb"] = 5
        # case centrale -> plein cadre
        x, y, w, h = g[4]
        p = seg(t, 28.5 + 0.05, 28.91)
        if p > 0:
            e = out_expo(seg(t, 30.1, 30.62))
            if e <= 0:
                i = S5_C[4]
                ax, ay, s = _content(i, "g3")
                place(c, cell(i, w, h, ax, ay, s), x + (1 - out_expo(p)) * -W, y, 1)
            else:
                x0, y0 = lerp(x - w / 2, 0, e), lerp(y - h / 2, 0, e)
                x1, y1 = lerp(x + w / 2, W, e), lerp(y + h / 2, H, e)
                d = ImageDraw.Draw(c)
                d.rounded_rectangle([x0, y0, x1, y1], radius=int(26 * (1 - e)) + 1,
                                    fill=mix(tint(LOOK_COLOR[21], 0.84), WHITE, e) + (255,))
                ax, ay, s = _content(21, "g3")
                # interpolation ancre/échelle vers la pose standard
                ccx, ccy = (x0 + x1) / 2, (y0 + y1) / 2
                place(c, img(21), lerp(ccx, STD_X, e), lerp(ccy, STD_Y, e), lerp(s, STD_S, e),
                      anchor=(512, lerp(ay, 768, e)), clip=(x0, y0, x1, y1), key=21)
                if e < 0.8:
                    fx["mb"] = 4
    # textes
    if 24.15 <= t < 28.0:
        if t < 27.84:
            text_letters(c, "LA COLLECTION", "Anton.ttf", 150, INK, W / 2, 190, t, 24.15, stagger=0.03, dur=0.3,
                         tracking=6)
        else:
            text_mask_reveal(c, "LA COLLECTION", "Anton.ttf", 150, INK, W / 2, 190, 1 - seg(t, 27.84, 28.0),
                             tracking=6, direction=-1)
    if 27.1 <= t < 28.45:
        p = seg(t, 27.1, 27.4) * (1 - seg(t, 28.3, 28.45))
        text_mask_reveal(c, "FEMME  &  HOMME", "Montserrat-Black.ttf", 60, INK, W / 2, 1755, p, tracking=14)
    if 28.0 <= t < 30.1:
        p = seg(t, 28.0, 28.3)
        o = seg(t, 29.9, 30.1)
        text_mask_reveal(c, "un moment.", "Playfair-BlackItalic.ttf", 150, LOOK_COLOR[2], W / 2, 190,
                         p * (1 - o), direction=1 if o == 0 else -1)
    if 24.6 <= t < 26.8:
        p = seg(t, 24.6, 24.9) * (1 - seg(t, 26.6, 26.8))
        text_mask_reveal(c, "CRÉÉE POUR CHAQUE APPARITION", "Montserrat-Black.ttf", 40, INK, W / 2, 1755, p,
                         tracking=8)
    fx["punch"] += 0.025 * decay(t, 24.0, 8) + 0.02 * decay(t, 27.0, 9) + 0.02 * decay(t, 28.5, 9) \
        + 0.035 * decay(t, 30.1, 8)


# ----------------------------------------------------------------------------- 31–37 s : FINAL SHOWCASE
S6 = [2, 12, 3, 5, 15, 7, 16, 24, 14, 13, 9, 6]
S6_WORDS = [("CROCHET.", 31.0, 32.0), ("COULEUR.", 32.0, 33.0), ("CRÉATIVITÉ.", 33.0, 34.0),
            ("ET SURTOUT…", 34.0, 35.0)]
_SWAY = {}


def swayed(i, t, amp):
    """Petit mouvement 3D des franges / bas de tenue : onde horizontale croissante vers le bas."""
    base = img(i).reduce(1)
    a = np.asarray(base).astype(np.float32)
    h, w = a.shape[:2]
    yy = np.arange(h, dtype=np.float32)
    wgt = np.clip((yy / h - 0.42) / 0.5, 0, 1) ** 1.6
    shift = amp * wgt * np.sin(t * 9.0 - yy / 55.0)
    xs = np.arange(w, dtype=np.float32)
    out = np.empty_like(a)
    for r in range(h):
        if wgt[r] == 0:
            out[r] = a[r]
        else:
            xi = xs - shift[r]
            x0 = np.clip(np.floor(xi).astype(int), 0, w - 1)
            x1 = np.clip(x0 + 1, 0, w - 1)
            fr = (xi - np.floor(xi))[:, None]
            out[r] = a[r, x0] * (1 - fr) + a[r, x1] * fr
    return Image.fromarray(out.astype(np.uint8))


def sec_showcase(c, t, fx):
    k = min(int((t - 31.0) / BEAT), len(S6) - 1)
    tb = 31.0 + k * BEAT
    i = S6[k]
    colr = LOOK_COLOR[i]
    p = seg(t, tb, tb + 0.22)
    # disque de couleur qui pulse sur le kick
    r = 480 * lerp(0.82, 1.0, out_back(p, 2.0))
    d = ImageDraw.Draw(c)
    d.ellipse([W / 2 - r, 1040 - r, W / 2 + r, 1040 + r], fill=tint(colr, 0.8) + (255,))
    # anneau de fil
    ths = np.linspace(0, 2 * math.pi * 1.02, 200) + t * 1.5
    R = r + 34
    draw_yarn(c, np.stack([W / 2 + R * np.cos(ths), 1040 + R * np.sin(ths)], 1), 9, [colr, (255, 196, 0), WHITE],
              seglen=80, L1=_arclen(np.stack([W / 2 + R * np.cos(ths), 1040 + R * np.sin(ths)], 1))[-1] * out_cubic(p))
    sgn = 1 if k % 2 == 0 else -1
    ry = 9 * math.sin((t - tb) * 5.5 + k)
    sc = STD_S * lerp(1.09, 1.0, out_expo(p))
    exit_q = in_back(seg(t, 36.85, 37.22), 1.2) if k == len(S6) - 1 else 0
    im = swayed(i, t, 9.0)
    place(c, im, STD_X + sgn * 40 * (1 - out_expo(p)) * 0 + 0, STD_Y, sc * (1 - exit_q) if exit_q < 1 else 0,
          rot=sgn * 3 * (1 - out_expo(p)) + 140 * exit_q, ry=ry * (1 - exit_q), alpha=1 - exit_q * 0.5)
    if p < 0.25 or exit_q > 0:
        fx["mb"] = 4
    # mots
    for wd, t0, t1 in S6_WORDS:
        if t0 <= t < t1 and t < 36.85:
            q = seg(t, t0, t0 + 0.18)
            text(c, wd, "Anton.ttf", 190, INK, W / 2, 200, tracking=6, scale=lerp(1.6, 1.0, out_expo(q)),
                 alpha=clamp01(q * 4) * (1 - seg(t, t1 - 0.06, t1)))
    if 35.0 <= t < 36.9:
        q = 1 - seg(t, 36.75, 36.9)
        text_letters(c, "du caractère.", "Playfair-BlackItalic.ttf", 140, colr, W / 2, 195, t, 35.0, stagger=0.035,
                     dur=0.3, alpha=q, mode="slam")
    fx["punch"] += 0.045 * decay(t, tb, 10)


# ----------------------------------------------------------------------------- 37–40 s : SIGNATURE
LOGO_C = (540, 760)


def _spiral(k):
    ang0 = k * math.pi / 3 + 0.4
    rs = np.linspace(1400, 0, 160)
    th = ang0 + np.linspace(0, 3.6, 160)
    return np.stack([LOGO_C[0] + rs * np.cos(th), LOGO_C[1] + rs * np.sin(th)], 1)


def _petal(k, n=8, R=175):
    a = k * 2 * math.pi / n - math.pi / 2
    tt = np.linspace(0, 2 * math.pi, 90)
    # boucle de crochet (une « bride ») : ellipse allongée partant du centre
    lx = R * 0.5 * (1 - np.cos(tt))
    ly = R * 0.2 * np.sin(tt)
    x = LOGO_C[0] + 40 * math.cos(a) + lx * math.cos(a) - ly * math.sin(a)
    y = LOGO_C[1] + 40 * math.sin(a) + lx * math.sin(a) + ly * math.cos(a)
    return np.stack([x, y], 1)


def sec_signature(c, t, fx):
    # fils qui convergent vers le centre
    if t < 38.08:
        p = in_out_cubic(seg(t, 36.9, 38.0))
        for k in range(6):
            pts = _spiral(k)
            tot = _arclen(pts)[-1]
            draw_yarn(c, pts, 11, [YARN[k], YARN[(k + 3) % 7]], tot * p - 700, tot * p + 10, 140)
        if 37.4 < t < 38.0:
            fx["mb"] = 3
    # logo fleur au crochet
    if t >= 37.98:
        p = seg(t, 37.98, 38.5)
        rot = (t - 38.0) * 0.12
        for k in range(8):
            pts = _petal(k)
            cx, cy = LOGO_C
            rr = np.array([[math.cos(rot), -math.sin(rot)], [math.sin(rot), math.cos(rot)]])
            pts = (pts - LOGO_C) @ rr.T + LOGO_C
            tot = _arclen(pts)[-1]
            pk = seg(p, k * 0.06, k * 0.06 + 0.55)
            draw_yarn(c, pts, 12, [YARN[k % 7]], 0, tot * out_cubic(pk), 999)
        ths = np.linspace(0, 2 * math.pi * 1.04, 120) + rot
        ring = np.stack([LOGO_C[0] + 36 * np.cos(ths), LOGO_C[1] + 36 * np.sin(ths)], 1)
        draw_yarn(c, ring, 12, [(255, 196, 0)], 0, _arclen(ring)[-1] * out_cubic(seg(p, 0, 0.6)), 999)
        # nom de marque
        q = seg(t, 38.12, 38.5)
        text(c, BRAND_NAME, "Playfair-BlackItalic.ttf", 128, INK, W / 2, 1070, scale=lerp(1.25, 1.0, out_expo(q)),
             alpha=clamp01(q * 3))
        lw = 380 * out_expo(seg(t, 38.3, 38.7))
        if lw > 1:
            d = ImageDraw.Draw(c)
            d.rectangle([W / 2 - lw, 1168, W / 2 + lw, 1172], fill=LOOK_COLOR[2] + (255,))
        text_mask_reveal(c, "DÉCOUVREZ LA COLLECTION", "Montserrat-Black.ttf", 50, INK, W / 2, 1250,
                         seg(t, 38.45, 38.8), tracking=8)
        handles(c, W / 2, 1352, seg(t, 38.75, 39.1))
        tag = seg(t, 38.9, 39.3)
        text(c, BRAND_TAGLINE, "Montserrat-Bold.ttf", 30, (120, 120, 120), W / 2, 1735, tracking=12,
             alpha=out_cubic(tag))
        # scintillements
        rnd = random.Random(7)
        for j in range(26):
            ang = rnd.uniform(0, 2 * math.pi)
            rad = rnd.uniform(230, 470)
            ph = rnd.uniform(0, 1)
            tw = 0.5 + 0.5 * math.sin((t - 38.0) * rnd.uniform(5, 9) + ph * 6.28)
            life = seg(t, 38.0 + ph * 0.6, 38.25 + ph * 0.6)
            x = LOGO_C[0] + rad * math.cos(ang); y = LOGO_C[1] + rad * math.sin(ang) * 0.9 + 60
            sparkle(c, x, y, rnd.uniform(7, 16) * tw * life, life * tw,
                    color=YARN[j % 7] if j % 3 else (255, 200, 60))
    fx["punch"] += 0.06 * decay(t, 38.0, 7)
    fx["shake"] += 10 * decay(t, 38.0, 9)
    ripple(c, t, 38.0, LOGO_C[0], LOGO_C[1], YARN[0], 1000, 1.0, 7, 0.55)
    ripple(c, t, 38.1, LOGO_C[0], LOGO_C[1], YARN[2], 1000, 1.0, 4, 0.45)
    fx["flash"] = (WHITE, 0.7 * decay(t, 38.0, 14))
    fx["cam_scale"] = 1 + 0.03 * seg(t, 38.0, 40.0)


def handles(c, cx, cy, p):
    if p <= 0:
        return
    f = "Montserrat-Bold.ttf"
    parts = [("ig", "@Instagram"), ("wa", "WhatsApp"), ("web", "Site")]
    size = 36
    icon = 40
    gap_i, gap_p = 14, 50
    widths = [icon + gap_i + text_img(s, f, size, INK).width for _, s in parts]
    total = sum(widths) + gap_p * (len(parts) - 1)
    x = cx - total / 2
    a = out_cubic(p)
    lay = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    yc = 60
    for (kind, s), wd in zip(parts, widths):
        ix, iy = x, yc - icon / 2
        col = INK + (255,)
        if kind == "ig":
            d.rounded_rectangle([ix, iy, ix + icon, iy + icon], radius=11, outline=col, width=4)
            d.ellipse([ix + 11, iy + 11, ix + icon - 11, iy + icon - 11], outline=col, width=4)
            d.ellipse([ix + icon - 12, iy + 6, ix + icon - 6, iy + 12], fill=col)
        elif kind == "wa":
            d.ellipse([ix + 2, iy + 2, ix + icon - 2, iy + icon - 2], outline=col, width=4)
            d.polygon([(ix + 2, iy + icon), (ix + 8, iy + icon - 15), (ix + 17, iy + icon - 7)], fill=col)
            d.arc([ix + 12, iy + 11, ix + icon - 12, iy + icon - 11], 100, 250, fill=col, width=4)
        else:
            d.ellipse([ix + 2, iy + 2, ix + icon - 2, iy + icon - 2], outline=col, width=4)
            d.ellipse([ix + 12, iy + 2, ix + icon - 12, iy + icon - 2], outline=col, width=3)
            d.line([ix + 2, iy + icon / 2, ix + icon - 2, iy + icon / 2], fill=col, width=3)
        ti = text_img(s, f, size, INK)
        lay.alpha_composite(ti, (int(ix + icon + gap_i), int(yc - ti.height / 2)))
        x += wd + gap_p
        if kind != "web":
            d.ellipse([x - gap_p / 2 - 4, yc - 4, x - gap_p / 2 + 4, yc + 4], fill=LOOK_COLOR[2] + (255,))
    place(c, lay, W / 2, cy + (1 - a) * 40, 1.0, alpha=a)


# ----------------------------------------------------------------------------- composition d'une image
SECTIONS = [(0.0, 4.0, sec_intro), (3.8, 10.0, sec_looks), (10.0, 17.0, sec_accel), (17.0, 24.0, sec_wow),
            (24.0, 31.0, sec_collection), (31.0, 37.25, sec_showcase), (36.95, 40.01, sec_signature)]


def compose(t):
    c = Image.new("RGBA", (W, H), WHITE + (255,))
    fx = dict(punch=0.0, shake=0.0, vig=0.0, mb=1, flash=None, cam_scale=1.0)
    for a, b, fn in SECTIONS:
        if a <= t < b:
            fn(c, t, fx)
    if fx["flash"]:
        flash(c, *fx["flash"])
    vignette_pulse(c, fx["vig"])
    rnd = random.Random(int(t * 1000))
    sh = fx["shake"]
    frame = camera(c, fx["cam_scale"] * (1 + fx["punch"]), rnd.uniform(-sh, sh), rnd.uniform(-sh, sh),
                   rnd.uniform(-sh, sh) * 0.04)
    return frame, fx["mb"]


def render_frame(n):
    t = n / FPS
    frame, mb = compose(t)
    if mb > 1:
        # flou de mouvement : moyenne de sous-images sur un obturateur à 180°
        acc = np.asarray(frame.convert("RGB"), np.float32)
        shutter = 0.5 / FPS
        for j in range(1, mb):
            tj = t - shutter / 2 + shutter * j / (mb - 1)
            acc += np.asarray(compose(tj)[0].convert("RGB"), np.float32)
        acc /= mb
        return acc.astype(np.uint8).tobytes()
    return frame.convert("RGB").tobytes()


def _init():
    load_images()


def main():
    args = sys.argv[1:]
    if args and args[0] == "--stills":
        load_images()
        out = os.path.join(BUILD, "stills"); os.makedirs(out, exist_ok=True)
        for a in args[1:]:
            t = float(a)
            n = int(round(t * FPS))
            Image.frombytes("RGB", (W, H), render_frame(n)).save(os.path.join(out, "t%06.2f.jpg" % t), quality=88)
        return
    from multiprocessing import Pool
    start, end = 0, int(DURATION * FPS)
    out_path = os.path.join(BUILD, "video_silent.mp4")
    if args and args[0] == "--range":
        start, end = int(float(args[1]) * FPS), int(float(args[2]) * FPS)
        out_path = os.path.join(BUILD, "preview_%s_%s.mp4" % (args[1], args[2]))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                           "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_path],
                          stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=_init) as pool:
        for k, buf in enumerate(pool.imap(render_frame, range(start, end), chunksize=4)):
            ff.stdin.write(buf)
            if k % 60 == 0:
                print("frame %d/%d" % (start + k, end), flush=True)
    ff.stdin.close()
    ff.wait()
    print("->", out_path)


if __name__ == "__main__":
    main()
