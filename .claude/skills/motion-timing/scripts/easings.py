#!/usr/bin/env python3
"""Bibliothèque d'easings + ressorts, et traceur de courbes / chartes d'espacement.

Importable (copier les fonctions utiles dans motion/render.py) ou exécutable pour *voir* un easing :
une courbe valeur(temps) et, dessous, la charte d'espacement image par image à la durée choisie —
exactement ce que verra l'œil (points serrés = lent, écartés = rapide).

Exemples :
    python3 easings.py --names out_cubic out_expo out_back spring --dur 0.4
    python3 easings.py --names spring:0.35:9 spring:0.6:14 --dur 0.6     # spring:amortissement:fréquence(Hz)
    python3 easings.py --list
"""
import argparse, math, os


# ----------------------------------------------------------------------------- easings x ∈ [0, 1] -> [0, 1]
def linear(x): return x
def in_sine(x): return 1 - math.cos(math.pi * x / 2)
def out_sine(x): return math.sin(math.pi * x / 2)
def in_out_sine(x): return -(math.cos(math.pi * x) - 1) / 2
def in_quad(x): return x * x
def out_quad(x): return 1 - (1 - x) ** 2
def in_out_quad(x): return 2 * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 2 / 2
def in_cubic(x): return x ** 3
def out_cubic(x): return 1 - (1 - x) ** 3
def in_out_cubic(x): return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def out_quart(x): return 1 - (1 - x) ** 4
def out_quint(x): return 1 - (1 - x) ** 5
def in_out_quint(x): return 16 * x ** 5 if x < 0.5 else 1 - (-2 * x + 2) ** 5 / 2
def in_expo(x): return 0.0 if x <= 0 else 2 ** (10 * x - 10)
def out_expo(x): return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)
def in_out_expo(x):
    if x <= 0 or x >= 1:
        return float(x >= 1)
    return 2 ** (20 * x - 10) / 2 if x < 0.5 else (2 - 2 ** (-20 * x + 10)) / 2
def out_circ(x): return math.sqrt(1 - (x - 1) ** 2)


def in_back(x, s=1.70158):
    return (s + 1) * x ** 3 - s * x ** 2


def out_back(x, s=1.70158):
    """Dépassement ≈ 10 % pour s=1.70 ; 1.2 ≈ 5 % (élégant), 2.5 ≈ 18 % (cartoon)."""
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def in_out_back(x, s=1.70158):
    c = s * 1.525
    return ((2 * x) ** 2 * ((c + 1) * 2 * x - c)) / 2 if x < 0.5 else \
        ((2 * x - 2) ** 2 * ((c + 1) * (2 * x - 2) + c) + 2) / 2


def out_elastic(x, period=0.3):
    if x <= 0 or x >= 1:
        return float(x >= 1)
    return 2 ** (-10 * x) * math.sin((x - period / 4) * 2 * math.pi / period) + 1


def out_bounce(x):
    n, d = 7.5625, 2.75
    if x < 1 / d:
        return n * x * x
    if x < 2 / d:
        x -= 1.5 / d; return n * x * x + 0.75
    if x < 2.5 / d:
        x -= 2.25 / d; return n * x * x + 0.9375
    x -= 2.625 / d; return n * x * x + 0.984375


def bezier(x1, y1, x2, y2):
    """Courbe cubic-bezier CSS/After Effects (P0=(0,0), P3=(1,1)). Renvoie une fonction x -> y."""
    def sample(u, a, b):
        return 3 * a * u * (1 - u) ** 2 + 3 * b * u * u * (1 - u) + u ** 3

    def f(x):
        lo, hi = 0.0, 1.0
        for _ in range(40):                     # dichotomie : u tel que X(u) = x
            mid = (lo + hi) / 2
            if sample(mid, x1, x2) < x:
                lo = mid
            else:
                hi = mid
        return sample((lo + hi) / 2, y1, y2)
    return f


# ----------------------------------------------------------------------------- ressorts (temps réel, pas x∈[0,1])
def spring(t, damping=0.4, freq=8.0):
    """Réponse d'un ressort amorti partant de 0 vers 1, t en secondes (non borné : dure ce qu'il dure).
    damping : 0.2 très rebondissant · 0.4 vivant · 0.7 ferme · 1.0 critique (aucun dépassement).
    freq    : fréquence propre (Hz) ; 6–10 pour des éléments d'interface, 3–5 pour des objets lourds."""
    if t <= 0:
        return 0.0
    w = 2 * math.pi * freq
    z = damping
    if z < 1:
        wd = w * math.sqrt(1 - z * z)
        return 1 - math.exp(-z * w * t) * (math.cos(wd * t) + z * w / wd * math.sin(wd * t))
    return 1 - math.exp(-w * t) * (1 + w * t)


def spring_settle(damping=0.4, freq=8.0, tol=0.01):
    """Temps (s) après lequel le ressort reste à ±tol de 1 : la vraie durée perçue de l'animation."""
    t, last_out = 0.0, 0.0
    while t < 5:
        if abs(spring(t, damping, freq) - 1) > tol:
            last_out = t
        t += 1 / 240
    return last_out


def overshoot(fn, n=400):
    """Dépassement maximal (en fraction de l'amplitude) d'un easing x∈[0,1]."""
    return max(fn(i / n) for i in range(n + 1)) - 1


# ----------------------------------------------------------------------------- tracé
NAMES = ["linear", "in_sine", "out_sine", "in_out_sine", "in_quad", "out_quad", "in_out_quad", "in_cubic",
         "out_cubic", "in_out_cubic", "out_quart", "out_quint", "in_out_quint", "in_expo", "out_expo", "in_out_expo",
         "out_circ", "in_back", "out_back", "in_out_back", "out_elastic", "out_bounce"]


def resolve(spec, dur):
    """'out_back:1.2', 'spring:0.4:8', 'bezier:.2:.8:.2:1' -> (libellé, f(x) sur [0,1] pour la durée dur)."""
    name, *args = spec.split(":")
    args = [float(v) for v in args]
    if name == "spring":
        z, fr = (args + [0.4, 8.0][len(args):])[:2]
        return "spring z=%g f=%g (posé %.2fs)" % (z, fr, spring_settle(z, fr)), lambda x: spring(x * dur, z, fr)
    if name == "bezier":
        return "bezier(%s)" % ",".join("%g" % v for v in args), bezier(*args)
    fn = globals()[name]
    if args:
        return "%s(%s)" % (name, ",".join("%g" % v for v in args)), (lambda x, f=fn, a=args: f(x, *a))
    return name, fn


def plot(specs, dur, fps, out):
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except OSError:
        font = ImageFont.load_default()
    cw, ch, sh, pad = 330, 220, 70, 18
    cols = min(len(specs), 4)
    rows = (len(specs) + cols - 1) // cols
    img = Image.new("RGB", (pad + cols * (cw + pad), pad + rows * (ch + sh + 40 + pad)), (250, 250, 248))
    d = ImageDraw.Draw(img)
    nfr = int(round(dur * fps))
    for k, spec in enumerate(specs):
        label, fn = resolve(spec, dur)
        x0 = pad + (k % cols) * (cw + pad)
        y0 = pad + (k // cols) * (ch + sh + 40 + pad)
        vals = [fn(i / 300) for i in range(301)]
        lo, hi = min(0, min(vals)), max(1, max(vals))
        Y = lambda v: y0 + 22 + (ch - 30) * (1 - (v - lo) / (hi - lo))  # noqa: E731
        d.rectangle([x0, y0 + 22, x0 + cw, y0 + ch - 8], outline=(200, 200, 200))
        d.line([x0, Y(1), x0 + cw, Y(1)], fill=(210, 210, 210))
        d.line([(x0 + cw * i / 300, Y(v)) for i, v in enumerate(vals)], fill=(40, 90, 220), width=2)
        for i in range(nfr + 1):
            xx = x0 + cw * i / max(nfr, 1)
            d.ellipse([xx - 2.5, Y(fn(i / max(nfr, 1))) - 2.5, xx + 2.5, Y(fn(i / max(nfr, 1))) + 2.5], fill=(220, 60, 40))
        os_ = max(vals) - 1
        d.text((x0, y0 + 2), label + (" · dép. %.0f %%" % (os_ * 100) if os_ > 0.005 else ""),
               fill=(30, 30, 30), font=font)
        # charte d'espacement : position de l'objet à chaque image (de gauche à droite)
        sy = y0 + ch + 14
        d.line([x0, sy, x0 + cw, sy], fill=(190, 190, 190))
        for i in range(nfr + 1):
            v = fn(i / max(nfr, 1))
            xx = x0 + cw * (v - lo) / (hi - lo)
            d.line([xx, sy - 10, xx, sy + 10], fill=(220, 60, 40) if i in (0, nfr) else (60, 60, 60), width=2)
        d.text((x0, sy + 14), "espacement : %d images à %g i/s (%.2f s)" % (nfr, fps, dur),
               fill=(110, 110, 110), font=font)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out)
    print(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--names", nargs="+", default=["out_cubic", "out_expo", "out_back", "spring"])
    ap.add_argument("--dur", type=float, default=0.4, help="durée de l'animation (s)")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--out", default=os.path.join("build", "review", "easings.png"))
    a = ap.parse_args()
    if a.list:
        for n in NAMES:
            f = globals()[n]
            print("%-14s  dépassement %3.0f %%   à mi-temps %.2f" % (n, overshoot(f) * 100, f(0.5)))
        print("spring:z:f      ressort (z amortissement, f Hz)    bezier:x1:y1:x2:y2   courbe CSS/AE")
        return
    plot(a.names, a.dur, a.fps, a.out)


if __name__ == "__main__":
    main()
