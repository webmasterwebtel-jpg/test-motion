"""Effets audio partagés par la musique et les bruitages MyWebtel (V6).

- reverb() : réverbération stéreo par convolution avec une réponse impulsionnelle synthétique (bruit décorrélé à
  décroissance exponentielle, de plus en plus sombre), comme une salle : c'est elle qui donne de l'espace et du « cher »
  aux sons synthétisés, sans échantillons extérieurs.
- sons « cinéma » discrets : montée (riser), impact, éclats de verre, scintillement, faisceau, imprimante, balayage.
Tout est déterministe (graines fixes) : deux rendus donnent exactement le même son.
"""
import numpy as np
from scipy import signal

SR = 48000
_rng = np.random.default_rng(2026)


def tv(d): return np.arange(int(d * SR)) / SR
def noise(d, rng=None): return (rng or _rng).standard_normal(int(d * SR))
def bp(x, lo, hi): return signal.sosfilt(signal.butter(2, [lo, min(hi, SR / 2 - 100)], "band", fs=SR, output="sos"), x)
def hp(x, f): return signal.sosfilt(signal.butter(2, f, "high", fs=SR, output="sos"), x)
def lp(x, f): return signal.sosfilt(signal.butter(2, f, "low", fs=SR, output="sos"), x)
def norm(x, peak=1.0): return x / (np.abs(x).max() + 1e-12) * peak


def impulse(t60=2.2, predelay=0.014, seed=7):
    rng = np.random.default_rng(seed)
    n = int(t60 * 1.15 * SR)
    t = np.arange(n) / SR
    env = 10 ** (-3 * t / t60)
    chans = []
    for c in range(2):
        x = rng.standard_normal(n) * env
        bright, dark = lp(x, 7500), lp(x, 1600)
        w = np.clip(t / (0.55 * t60), 0, 1)
        y = bright * (1 - w) + dark * w
        y[: int(0.004 * SR)] *= np.linspace(0, 1, int(0.004 * SR))
        chans.append(np.concatenate([np.zeros(int(predelay * SR)), y]))
    h = np.stack(chans, 1)
    return h / np.sqrt((h ** 2).sum(0)).max()


def reverb(x, t60=2.0, wet=0.25, hpf=220, seed=7):
    """x : (n,) ou (n, 2). Renvoie (n, 2) : signal sec + réverbération (passe-haut sur l'envoi pour garder un grave net)."""
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    h = impulse(t60, seed=seed)
    src = signal.sosfilt(signal.butter(2, hpf, "high", fs=SR, output="sos"), x, axis=0)
    w = np.stack([signal.fftconvolve(src[:, c], h[:, c])[: len(x)] for c in range(2)], 1)
    return x + wet * w


def sweep_noise(d, f0, f1, q=1.6, rng=None):
    """Bruit filtré par un passe-bande qui glisse de f0 à f1 (par blocs)."""
    n = int(d * SR)
    x = noise(d, rng)
    fc = f0 * (f1 / f0) ** (np.arange(n) / max(n, 1))
    out = np.zeros(n)
    hop = 512
    for i in range(0, n, hop):
        c = fc[min(i, n - 1)]
        out[i:i + hop] = bp(x[max(0, i - 2048):i + hop], c / q, c * q)[-len(out[i:i + hop]):]
    return out


def riser(d=2.4, f0=300, f1=6000, level=0.4):
    """Montée : souffle qui s'éclaircit + note qui monte, s'arrête net à la fin (l'impact prend le relais)."""
    t = tv(d)
    p = t / d
    air = norm(sweep_noise(d, f0, f1)) * p ** 2.2
    f = 110 * (2 ** (2 * p))                          # deux octaves de montée
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35 * p ** 3
    x = air + tone
    x[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))
    return x * level


def impact(level=0.9, bright=True):
    """Impact cinéma, rond : sous-grave qui plonge + corps + souffle clair (la réverbe se met au bus)."""
    t = tv(2.2)
    f = 34 + 70 * np.exp(-t / 0.05)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    body = lp(noise(2.2), 900) * np.exp(-t / 0.09) * 0.5
    air = hp(noise(2.2), 3000) * np.exp(-t / 0.35) * (0.25 if bright else 0.08)
    return norm(sub + body + air) * level


def reverse_swell(d=1.2, level=0.35):
    """Souffle inversé qui gonfle jusqu'à un instant (cymbale à l'envers, douce)."""
    t = tv(d)
    x = hp(noise(d), 1800) * (t / d) ** 3
    return norm(x) * level


def glass(level=0.6, seed=11):
    """Éclats de verre : un craquement, puis une pluie de petits tintements résonants qui s'éparpillent."""
    rng = np.random.default_rng(seed)
    d = 1.6
    t = tv(d)
    x = hp(noise(d, rng), 2500) * np.exp(-t / 0.02) * 0.9          # craquement
    x += lp(noise(d, rng), 500) * np.exp(-t / 0.06) * 0.5           # corps
    for k in range(70):                                             # tintements
        t0 = 0.004 + 0.9 * rng.random() ** 1.8
        f = rng.uniform(2200, 8500)
        dec = rng.uniform(0.015, 0.09)
        i0 = int(t0 * SR)
        tt = t[: len(t) - i0]
        x[i0:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / dec) * rng.uniform(0.08, 0.3) * (1 - 0.6 * t0)
    return norm(x) * level


def shimmer(d=1.2, level=0.25, seed=5, lo=1800, hi=5200):
    """Scintillement (magie discrète) : petites notes aiguës aléatoires de la gamme de ré."""
    rng = np.random.default_rng(seed)
    t = tv(d)
    x = np.zeros_like(t)
    scale = [587.3, 659.3, 740.0, 880.0, 987.8, 1174.7, 1318.5, 1480.0, 1760.0, 1975.5, 2349.3, 2637.0, 2960.0, 3520.0, 3951.1, 4698.6]
    notes = [f for f in scale if lo <= f <= hi] or scale[-6:]
    for k in range(int(14 * d)):
        t0 = rng.uniform(0, d * 0.85)
        f = rng.choice(notes)
        i0 = int(t0 * SR)
        tt = t[: len(t) - i0]
        x[i0:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.18) * rng.uniform(0.3, 1.0)
    env = np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.3)
    return norm(x * env) * level


def beam(f0=520, f1=1560, d=0.5, level=0.3):
    """Faisceau de lumière : glissando doux vers l'aigu, avec un léger souffle."""
    t = tv(d)
    p = t / d
    f = f0 * (f1 / f0) ** E_out(p)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x = x * np.sin(np.pi * p) ** 1.5 + 0.15 * norm(sweep_noise(d, 1200, 6000)) * np.sin(np.pi * p)
    return norm(x) * level


def E_out(p): return 1 - (1 - p) ** 3


def printer(d=0.75, level=0.28):
    """Impression : moteur modulé + petits cliquetis (sans agressivité)."""
    t = tv(d)
    motor = bp(noise(d), 300, 2400) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 26 * t)))
    clicks = np.zeros_like(t)
    for k in range(int(d * 14)):
        i0 = int((k / 14 + 0.01) * SR)
        n = min(int(0.008 * SR), len(t) - i0)
        if n > 0: clicks[i0:i0 + n] += hp(noise(0.008), 3000)[:n] * 0.5
    env = np.minimum(1, t / 0.04) * np.minimum(1, (d - t) / 0.08)
    return norm((motor + clicks) * env) * level


def scan(d=0.7, level=0.22):
    """Balayage du scanner : tonalité douce qui glisse, trémolo léger."""
    t = tv(d)
    f = 300 + 900 * (t / d)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.75 + 0.25 * np.sin(2 * np.pi * 18 * t))
    x += 0.4 * norm(bp(noise(d), 2000, 6000))
    return norm(x * np.sin(np.pi * t / d)) * level


def paper(level=0.35):
    """Feuille qui se pose : souffle bref + petit choc mat."""
    t = tv(0.25)
    return norm(bp(noise(0.25), 400, 3000) * np.exp(-t / 0.03) + np.sin(2 * np.pi * 160 * t) * np.exp(-t / 0.03) * 0.6) * level
