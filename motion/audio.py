"""Bande-son complète : musique Afro-house / Amapiano synthétisée (120 BPM), SFX et voix off.

Tout est généré hors-ligne (numpy/scipy + Kokoro pour la voix) et calé sur la même
grille que l'image : 1 temps = 0,5 s, 1 double-croche = 0,125 s.
Sortie : build/audio/mix.wav (+ stems music/sfx/voice).
"""
import os, subprocess, math
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
DUR = 40.0
N = int(SR * DUR)
BPM = 120
BEAT = 60 / BPM
STEP = BEAT / 4
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "audio")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)


# ----------------------------------------------------------------------------- utilitaires
def buf():
    return np.zeros((N, 2), np.float32)


def add(bus, x, t0, gain=1.0, pan=0.0):
    """Ajoute un signal mono/stéréo à t0 (s) avec un pan à puissance constante."""
    i0 = int(round(t0 * SR))
    if x.ndim == 1:
        l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        x = np.stack([x * l, x * r], 1) * math.sqrt(2)
    if i0 < 0:
        x = x[-i0:]
        i0 = 0
    n = min(len(x), N - i0)
    if n > 0:
        bus[i0:i0 + n] += x[:n] * gain


def tvec(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.standard_normal(int(d * SR)).astype(np.float32)


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "high", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "low", fs=SR, output="sos"), x)


def svf_sweep(x, f, q=1.2):
    """Filtre passe-bande à état variable dont la fréquence suit le tableau f (Hz)."""
    y = np.zeros_like(x)
    low = band = 0.0
    k = 1.0 / q
    for i in range(len(x)):
        g = 2 * math.sin(math.pi * min(f[i], SR / 6) / SR)
        high = x[i] - low - k * band
        band += g * high
        low += g * band
        y[i] = band
    return y


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def adsr(n, a=0.005, d=0.1, s=0.6, r=0.1, dur=None):
    t = np.arange(n) / SR
    dur = dur if dur is not None else n / SR - r
    e = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    e = np.where(t > dur, e * np.clip(1 - (t - dur) / r, 0, 1), e)
    return e


# ----------------------------------------------------------------------------- instruments
def kick(gain=1.0):
    t = tvec(0.55)
    f = 44 + 120 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t / 0.3)
    click = hp(noise(0.004), 2000) * 0.3
    x[: len(click)] += click
    return np.tanh(x * 1.6) * gain


def log_drum(freq, dur=0.42, drive=2.2):
    """Log drum Amapiano : sinus à attaque de hauteur rapide, saturé, filtré."""
    t = tvec(dur)
    f = freq * (1 + 0.9 * np.exp(-t / 0.018))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    env = np.exp(-t / (dur * 0.42))
    env[-int(0.02 * SR):] *= np.linspace(1, 0, int(0.02 * SR))
    x = np.tanh(x * env * drive) / np.tanh(drive)
    return lp(x, 1400)


def shaker(acc=1.0):
    x = bp(noise(0.06), 5000, 12000)
    t = tvec(0.06)
    return x * np.exp(-t / 0.018) * 0.35 * acc


def open_hat():
    x = hp(noise(0.22), 7000, 3)
    return x * np.exp(-tvec(0.22) / 0.07) * 0.32


def clap(pitch=1.0):
    d = 0.3
    x = bp(noise(d), 900 * pitch, 2600 * pitch)
    t = tvec(d)
    env = np.zeros_like(t)
    for o in (0.0, 0.009, 0.019):
        env += (t >= o) * np.exp(-(t - o).clip(0) / 0.008) * 0.6
    env += (t >= 0.025) * np.exp(-(t - 0.025).clip(0) / 0.09)
    return x * env * 0.55


def conga(f):
    t = tvec(0.25)
    ff = f * (1 + 0.25 * np.exp(-t / 0.01))
    x = np.sin(2 * np.pi * np.cumsum(ff) / SR) * np.exp(-t / 0.07)
    x[:200] += hp(noise(200 / SR), 1500)[:200] * 0.2
    return x * 0.45


def rim():
    t = tvec(0.06)
    return (np.sin(2 * np.pi * 1650 * t) + 0.5 * np.sin(2 * np.pi * 820 * t)) * np.exp(-t / 0.012) * 0.25


def keys(notes, dur=0.45):
    """Piano électrique (type Rhodes) façon accords jazzy amapiano."""
    t = tvec(dur + 0.3)
    x = np.zeros_like(t)
    for n in notes:
        f = midi(n)
        trem = 1 + 0.08 * np.sin(2 * np.pi * 5.5 * t)
        x += (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.08)) * trem
    env = np.exp(-t / 0.35) * np.clip(t / 0.004, 0, 1)
    env *= np.clip(1 - (t - dur) / 0.3, 0, 1)
    return lp(x * env, 3500) * 0.11


def saw(f, t, nh=24):
    x = np.zeros_like(t)
    for h in range(1, nh + 1):
        if f * h > 12000:
            break
        x += np.sin(2 * np.pi * f * h * t) / h
    return x


def pad(notes, dur, cutoff=1800, attack=0.4):
    t = tvec(dur)
    x = np.zeros_like(t)
    for n in notes:
        for det in (-0.08, 0.0, 0.08):
            x += saw(midi(n + det), t, 14)
    env = np.clip(t / attack, 0, 1) * np.clip((dur - t) / 0.4, 0, 1)
    return lp(x * env, cutoff) * 0.03


def sub(freq, dur):
    t = tvec(dur)
    env = np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 0.03, 0, 1)
    return np.sin(2 * np.pi * freq * t) * env * 0.5


def pluck(n, dur=0.3):
    t = tvec(dur + 0.2)
    f = midi(n)
    x = saw(f, t, 12) * np.exp(-t / 0.12)
    return lp(x, 4000) * 0.12


# ----------------------------------------------------------------------------- SFX
def impact(big=1.0, dur=2.2):
    t = tvec(dur)
    f = 36 + 70 * np.exp(-t / 0.08)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.55 * big))
    nz = lp(noise(dur), 900) * np.exp(-t / 0.12) * 0.6
    crack = hp(noise(dur), 2500) * np.exp(-t / 0.03) * 0.3
    return np.tanh((x + nz + crack) * 1.8) * 0.9 * big


def heartbeat():
    t = tvec(1.0)
    f = 42 + 60 * np.exp(-t / 0.05)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    x += lp(noise(1.0), 300) * np.exp(-t / 0.05) * 0.4
    return np.tanh(x * 2.2) * 0.95


def whoosh(dur=0.45, f0=400, f1=4000, peak=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    p = t / dur
    f = f0 * (f1 / f0) ** np.sin(np.pi * p * 0.5) if f1 > f0 else f0 * (f1 / f0) ** p
    x = svf_sweep(noise(dur), f, 1.4)
    env = np.where(p < peak, (p / peak) ** 2, ((1 - p) / (1 - peak)) ** 1.5)
    x = x * env
    x /= np.abs(x).max() + 1e-9
    pan = np.linspace(-0.8, 0.8, n)
    return np.stack([x * np.cos((pan + 1) * np.pi / 4), x * np.sin((pan + 1) * np.pi / 4)], 1) * 0.8


def snap():
    t = tvec(0.12)
    x = bp(noise(0.12), 1800, 4500) * np.exp(-t / 0.012)
    x += np.sin(2 * np.pi * 2100 * t) * np.exp(-t / 0.01) * 0.3
    return x * 1.1


def tick():
    t = tvec(0.05)
    return (hp(noise(0.05), 4000) * np.exp(-t / 0.004) + np.sin(2 * np.pi * 3200 * t) * np.exp(-t / 0.008) * 0.5) * 0.6


def yarn_slide(dur, level=0.25):
    """Frottement de fil : bruit filtré modulé par un grain aléatoire."""
    x = bp(noise(dur), 1200, 5000)
    grain = np.abs(lp(rng.standard_normal(int(dur * SR)), 40))
    grain /= grain.max() + 1e-9
    t = tvec(dur)
    env = np.clip(t / 0.3, 0, 1) * np.clip((dur - t) / 0.4, 0, 1)
    return x * (0.3 + grain) * env * level


def riser(dur, level=0.35):
    n = int(dur * SR)
    p = np.arange(n) / n
    f = 300 * (9000 / 300) ** p
    x = svf_sweep(noise(dur), f, 2.0) * p ** 2
    t = tvec(dur)
    x += np.sin(2 * np.pi * np.cumsum(200 * (6 ** p)) / SR) * p ** 3 * 0.25
    x /= np.abs(x).max() + 1e-9
    return x * level


def rev_cymbal(dur=1.0, level=0.3):
    t = tvec(dur)
    x = hp(noise(dur), 5000) * (t / dur) ** 3
    return x * level


def shimmer(dur=2.0):
    t = tvec(dur)
    x = np.zeros_like(t)
    notes = [81, 84, 86, 88, 91, 93, 96, 98]
    for k in range(18):
        o = rng.uniform(0, dur * 0.6)
        n = notes[rng.integers(len(notes))]
        f = midi(n)
        i0 = int(o * SR)
        tt = t[: len(t) - i0]
        x[i0:] += np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.35) * rng.uniform(0.3, 1)
    return x * 0.06


def crash():
    t = tvec(1.8)
    return hp(noise(1.8), 4500) * np.exp(-t / 0.5) * 0.18


def reverb_ir(dur=1.8, decay=0.55):
    t = tvec(dur)
    ir = np.stack([rng.standard_normal(len(t)), rng.standard_normal(len(t))], 1) * np.exp(-t / decay)[:, None]
    ir[:, 0] = lp(ir[:, 0], 6000); ir[:, 1] = lp(ir[:, 1], 6000)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum(0))


def reverb(x, wet=0.25, dur=1.8, decay=0.55):
    ir = reverb_ir(dur, decay)
    y = np.stack([signal.fftconvolve(x[:, 0], ir[:, 0])[:N], signal.fftconvolve(x[:, 1], ir[:, 1])[:N]], 1)
    return y * wet


# ----------------------------------------------------------------------------- musique
# Am9 | Fmaj9 | Dm9 | E7(b9) — une mesure (2 s) par accord
CHORDS = [
    (45, [57, 60, 64, 67, 71]),
    (41, [53, 57, 60, 64, 67]),
    (38, [50, 53, 57, 60, 64]),
    (40, [52, 56, 59, 62, 65]),
]


def chord_at(t):
    return CHORDS[int(t // (BEAT * 4)) % 4]


def between(t, *ranges):
    return any(a <= t < b for a, b in ranges)


def music():
    drums, bass, harm, perc = buf(), buf(), buf(), buf()
    nsteps = int(DUR / STEP)
    K = kick()
    for s in range(nsteps):
        t = s * STEP
        st = s % 16
        swing = 0.018 if s % 2 == 1 else 0.0
        ts = t + swing
        root, notes = chord_at(t)
        # kick 4/4
        if st % 4 == 0 and between(t, (4.0, 17.0), (18.0, 37.0)):
            add(drums, K, t, 0.95 if t >= 24 else 0.8)
        # clap sur 2 et 4
        if st in (4, 12) and between(t, (4.0, 16.0), (18.0, 37.0)):
            add(drums, clap(), t, 0.7, 0.05)
        # shaker en double-croches swinguées
        if between(t, (4.0, 17.0), (18.0, 37.0)):
            acc = 1.0 if st % 4 == 2 else 0.55
            add(perc, shaker(acc), ts, 0.9, 0.35)
        # charleston ouverte sur les contretemps
        if st % 4 == 2 and between(t, (10.0, 16.0), (20.0, 37.0)):
            add(perc, open_hat(), t, 0.8, -0.3)
        # congas / rim
        if between(t, (10.0, 17.0), (24.0, 37.0)):
            if st in (3, 7, 10, 13, 15):
                add(perc, conga(330 if st in (3, 10) else 220), ts, 0.7, -0.45 if st % 2 else 0.45)
            if st in (6, 14):
                add(perc, rim(), ts, 0.7, 0.4)
        # log drum (motif syncopé typique)
        ld_pat = {0: 0, 3: 0, 6: 12, 8: 0, 11: 7, 14: 10} if t < 24 else {0: 0, 3: 0, 5: 12, 7: 0, 10: 7, 11: 12, 14: 10}
        if st in ld_pat and between(t, (4.0, 16.0), (18.0, 37.0)):
            f = midi(root + 12 + ld_pat[st]) if t < 24 else midi(root + ld_pat[st])
            add(bass, log_drum(f, 0.42 if t >= 24 else 0.32, 2.8 if t >= 24 else 2.0), ts,
                0.55 if t < 24 else 0.75)
        # accords piano électrique
        if st in (0, 3, 7, 10, 14) and between(t, (4.0, 17.0), (18.0, 37.0)):
            add(harm, keys(notes, 0.28 if st else 0.5), ts, 0.9 if t < 24 else 1.1, 0.15 if st % 2 else -0.15)
        # sous-basse sur la montée afro-house
        if st in (0, 8) and between(t, (24.0, 37.0)):
            add(bass, sub(midi(root - 12), BEAT * 2 - 0.02), t, 0.5)
        # lead « pluck » pentatonique pour le climax
        if between(t, (31.0, 37.0)):
            mel = {0: 81, 3: 84, 6: 88, 8: 86, 10: 84, 12: 81, 14: 79}
            if st in mel:
                add(harm, pluck(mel[st] + (0 if (s // 16) % 2 == 0 else -2)), ts, 1.0, 0.25)
    # nappes
    for b in range(int(DUR / (BEAT * 4))):
        t = b * BEAT * 4
        root, notes = chord_at(t)
        if between(t, (24.0, 37.0)):
            add(harm, pad(notes, BEAT * 4 + 0.3, 2200, 0.2), t, 1.0)
        elif between(t, (10.0, 16.0), (18.0, 24.0)):
            add(harm, pad(notes, BEAT * 4 + 0.3, 1200, 0.3), t, 0.6)
    # drone d'intro (montée en ouverture de filtre)
    d = pad([45, 57, 64, 67], 4.2, 600, 2.5)
    add(harm, d, 0.0, 1.3)
    # roulement de claps 16 → 17 s
    for k in range(4):
        add(drums, clap(1.0), 16.0 + k * BEAT / 2, 0.45 + 0.08 * k)
    for k in range(4):
        add(drums, clap(1.15), 16.5 + k * STEP, 0.55 + 0.08 * k)
    for t in (4.0, 18.0, 24.0, 31.0):
        add(perc, crash(), t, 1.0 if t > 4 else 0.6)
    mix = drums * 1.0 + bass * 1.0 + harm * 1.0 + perc * 0.8
    mix += reverb(drums * 0.25 + harm * 0.6 + perc * 0.2, wet=0.35)
    # montée en filtre de la section 10–17 (ouverture progressive)
    # coupure nette 17.0 → 17.5 et arrêt en 37.0
    g = np.ones(N, np.float32)
    tt = np.arange(N) / SR
    g[(tt >= 17.0) & (tt < 17.5)] = 0
    g[tt >= 37.02] = 0
    ramp = int(0.004 * SR)
    for edge in (17.0, 37.02):
        i = int(edge * SR)
        g[i - ramp:i] = np.linspace(1, 0, ramp)
    i = int(17.5 * SR)
    g[i:i + ramp] = np.linspace(0, 1, ramp)
    mix *= g[:, None]
    # accord final tenu (signature)
    fin = pad([45, 57, 60, 64, 71, 76], 2.6, 3000, 0.05)
    add(mix, fin, 37.95, 1.3)
    return mix


# ----------------------------------------------------------------------------- SFX (calés sur l'image)
def sfx():
    b = buf()
    # INTRO
    add(b, yarn_slide(3.6, 0.22), 0.0, 1.0, -0.3)
    for t0, g in ((0.5, 0.75), (1.5, 0.85), (2.5, 0.0)):
        if g:
            add(b, heartbeat(), t0, g)
    add(b, whoosh(0.55, 300, 3500, 0.85), 1.95, 0.55)
    add(b, impact(1.0), 2.5, 0.9)
    add(b, heartbeat(), 2.5, 0.7)
    add(b, riser(1.0, 0.25), 3.0)
    add(b, rev_cymbal(0.8, 0.25), 3.2)
    # PREMIERS LOOKS : zoom → flash → slide → rotation → whoosh → zoom
    add(b, whoosh(0.4, 300, 5000, 0.6), 3.78, 0.6)
    add(b, impact(0.5, 1.0), 4.0, 0.45)
    add(b, snap(), 5.0, 0.8); add(b, shimmer(0.6), 5.0, 0.8)
    add(b, whoosh(0.35, 500, 6000, 0.5), 5.85, 0.7)
    add(b, whoosh(0.5, 250, 3000, 0.4), 6.8, 0.6); add(b, snap(), 7.0, 0.6)
    add(b, whoosh(0.35, 600, 7000, 0.6), 7.85, 0.75)
    add(b, impact(0.7, 1.2), 9.0, 0.6); add(b, whoosh(0.35, 400, 5000, 0.5), 8.85, 0.4)
    add(b, riser(0.4, 0.3), 9.6)
    # ACCÉLÉRATION : clicks / impacts sur les gros plans
    for t0 in (10.0, 11.0, 12.0, 13.0, 14.0, 15.0):
        add(b, tick(), t0, 0.8); add(b, impact(0.25, 0.4), t0, 0.35)
    for t0 in (10.5, 11.5, 12.5, 13.5, 14.5, 15.5):
        add(b, whoosh(0.18, 800, 6000, 0.7), t0 - 0.12, 0.45)
    for t0 in (16.0, 16.25, 16.5, 16.75):
        add(b, tick(), t0, 0.9); add(b, snap(), t0, 0.35)
    add(b, riser(3.0, 0.4), 14.0)
    add(b, rev_cymbal(1.0, 0.3), 16.0)
    # MOMENT WOW
    add(b, impact(1.4, 2.5), 17.5, 1.0)
    add(b, whoosh(0.7, 200, 6000, 0.2), 17.5, 0.5)
    for t0 in (18.0, 18.5, 19.0, 19.5, 20.0):
        add(b, snap(), t0, 0.7); add(b, whoosh(0.16, 900, 7000, 0.5), t0 - 0.03, 0.4)
        add(b, impact(0.35, 0.5), t0, 0.4)
    add(b, yarn_slide(3.0, 0.12), 18.0, 1.0, 0.4)
    for t0 in (21.5, 22.0, 22.5, 23.0):
        add(b, impact(0.55, 0.8), t0, 0.55)
    add(b, whoosh(0.4, 300, 6000, 0.8), 23.6, 0.8)
    add(b, rev_cymbal(1.0, 0.3), 23.0)
    # COLLECTION
    add(b, impact(1.0, 1.6), 24.0, 0.7)
    for k in range(3):
        add(b, whoosh(0.3, 400, 6000, 0.5), 23.95 + 0.08 * k, 0.4, (-0.6, 0, 0.6)[k])
    for k in range(3):
        add(b, snap(), 25.6 + 0.07 * k, 0.5, (-0.5, 0, 0.5)[k])
    add(b, whoosh(0.45, 250, 3500, 0.5), 26.8, 0.6)
    for k in range(4):
        add(b, tick(), 27.0 + 0.06 * k, 0.6)
    add(b, whoosh(0.4, 500, 7000, 0.6), 28.35, 0.6)
    add(b, rev_cymbal(0.5, 0.3), 29.6)
    add(b, whoosh(0.5, 4000, 300, 0.3), 30.0, 0.6)
    add(b, impact(0.8, 1.2), 30.1, 0.6)
    # FINAL SHOWCASE : accent sur chaque kick
    for k in range(12):
        t0 = 31.0 + k * BEAT
        add(b, snap() if k % 2 else tick(), t0, 0.45)
    add(b, impact(1.0, 1.5), 31.0, 0.6)
    add(b, riser(2.0, 0.3), 35.0)
    # SIGNATURE
    add(b, whoosh(0.5, 300, 6000, 0.5), 36.8, 0.9)
    add(b, yarn_slide(1.1, 0.3), 37.0, 1.0)
    add(b, riser(1.0, 0.35), 37.0)
    add(b, impact(1.6, 2.5), 38.0, 1.0)
    add(b, shimmer(2.0), 38.0, 1.5)
    add(b, shimmer(1.8), 38.4, 1.0, 0.4)
    b += reverb(b, wet=0.22, dur=1.2, decay=0.35)
    return b


# ----------------------------------------------------------------------------- voix off (Kokoro, voix féminine fr « ff_siwis »)
# (début s, texte, débit) — le débit est relevé automatiquement si une phrase déborde sur la suivante
VO = [
    (0.45, "Et si le crochet devenait…", 0.88),
    (2.62, "une véritable déclaration de style ?", 0.95),
    (4.85, "Des couleurs qui captent le regard.", 1.0),
    (6.85, "Des créations qui imposent leur présence.", 1.0),
    (10.02, "Chaque maille.", 1.05),
    (11.02, "Chaque couleur.", 1.05),
    (12.02, "Chaque détail…", 1.0),
    (13.1, "pensé pour se faire remarquer.", 1.0),
    (18.05, "Du plus doux…", 0.9),
    (19.0, "au plus audacieux.", 0.95),
    (20.42, "Une seule règle :", 0.95),
    (21.55, "ne jamais passer inaperçue.", 0.95),
    (24.55, "Une collection créée pour transformer chaque apparition…", 0.95),
    (28.0, "en moment.", 0.88),
    (31.02, "Crochet.", 1.0),
    (32.02, "Couleur.", 1.0),
    (33.02, "Créativité.", 1.0),
    (34.02, "Et surtout…", 0.95),
    (35.0, "du caractère.", 0.92),
    (37.25, "Portez l'originalité.", 0.95),
    (38.68, "Affirmez votre style.", 0.95),
]
KOKORO = os.path.join(ROOT, "build", "kokoro")
VOICE = "ff_siwis"


def _tts(tts, txt, speed, path):
    x, sr = tts.create(txt, voice=VOICE, speed=speed, lang="fr-fr")
    x = signal.resample_poly(np.asarray(x, np.float64), SR, sr)
    # coupe les silences de début / fin
    e = np.abs(x) > 0.01 * np.abs(x).max()
    i0, i1 = np.argmax(e), len(e) - np.argmax(e[::-1])
    x = x[max(i0 - int(0.01 * SR), 0):i1 + int(0.04 * SR)]
    wavfile.write(path, SR, (np.clip(x / (np.abs(x).max() + 1e-9), -1, 1) * 22000).astype(np.int16))
    return len(x) / SR


def voice():
    from kokoro_onnx import Kokoro
    tts = Kokoro(os.path.join(KOKORO, "kokoro-v1.0.onnx"), os.path.join(KOKORO, "voices-v1.0.bin"))
    b = buf()
    vdir = os.path.join(OUT, "vo")
    os.makedirs(vdir, exist_ok=True)
    report = []
    for k, (t0, txt, speed) in enumerate(VO):
        raw = os.path.join(vdir, "raw_%02d.wav" % k)
        pro = os.path.join(vdir, "vo_%02d.wav" % k)
        limit = (VO[k + 1][0] - 0.08) if k + 1 < len(VO) else DUR - 0.05
        d = _tts(tts, txt, speed, raw)
        while t0 + d > limit and speed < 1.3:
            speed += 0.05
            d = _tts(tts, txt, speed, raw)
        # timbre : EQ douce (présence + air), compression légère, normalisation
        subprocess.run(["sox", raw, pro, "highpass", "80", "equalizer", "250", "1q", "-1.5",
                        "equalizer", "3500", "1.2q", "+2.5", "treble", "+2", "9000",
                        "compand", "0.005,0.12", "-60,-60,-30,-16,-10,-7,0,-3", "-2",
                        "gain", "-n", "-1"], check=True)
        sr, x = wavfile.read(pro)
        x = x.astype(np.float32) / 32768.0
        fo = int(0.03 * SR)
        x[:240] *= np.linspace(0, 1, 240); x[-fo:] *= np.linspace(1, 0, fo)
        add(b, x, t0, 1.0)
        report.append((t0, t0 + len(x) / SR, txt, speed))
    for a, e, txt, sp in report:
        print("  VO %6.2f → %6.2f  x%.2f  %s" % (a, e, sp, txt))
    wet = reverb(b, wet=0.12, dur=0.9, decay=0.25)
    return b + wet, [r[:3] for r in report]


# ----------------------------------------------------------------------------- mixage
def envelope(x, att=0.01, rel=0.25):
    a = np.abs(x).max(1)
    # suivi d'enveloppe (attaque rapide / relâchement lent)
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    e = maximum_filter1d(a, int(rel * SR))
    return uniform_filter1d(e, int(att * SR * 4))


def limiter(x, ceiling=0.94):
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    pk = maximum_filter1d(np.abs(x).max(1), int(0.006 * SR))
    pk = uniform_filter1d(pk, int(0.004 * SR))
    g = np.minimum(1.0, ceiling / (pk + 1e-9))
    g = -maximum_filter1d(-g, int(0.01 * SR))
    g = uniform_filter1d(g, int(0.005 * SR))
    return x * g[:, None]


def write(name, x):
    y = np.clip(x, -1, 1)
    wavfile.write(os.path.join(OUT, name), SR, (y * 32767).astype(np.int16))


def main():
    print("musique…"); m = music()
    print("sfx…"); s = sfx()
    print("voix…"); v, report = voice()
    # silence absolu 17,0 → 17,5 s (l'arrêt brutal du script), y compris les queues de réverbe
    i0, i1, r = int(17.0 * SR), int(17.5 * SR), int(0.004 * SR)
    s[i0 - r:i0] *= np.linspace(1, 0, r)[:, None]
    s[i0:i1] = 0
    m /= np.abs(m).max() + 1e-9
    s /= np.abs(s).max() + 1e-9
    v /= np.abs(v).max() + 1e-9
    # ducking : la musique baisse d'environ 7 dB sous la voix
    env = envelope(v)
    duck = 1 - 0.55 * np.clip(env / 0.3, 0, 1)
    mix = m * 0.62 * duck[:, None] + s * 0.55 * (1 - 0.25 * np.clip(env / 0.3, 0, 1))[:, None] + v * 0.95
    mix = limiter(mix * 1.1)
    write("music.wav", m * 0.62); write("sfx.wav", s * 0.55); write("voice.wav", v * 0.95)
    write("mix.wav", mix)
    # sous-titres
    with open(os.path.join(ROOT, "build", "voix_off.srt"), "w") as f:
        for k, (a, e, txt) in enumerate(report, 1):
            ts = lambda x: "%02d:%02d:%02d,%03d" % (x // 3600, x % 3600 // 60, x % 60, round((x % 1) * 1000))
            f.write("%d\n%s --> %s\n%s\n\n" % (k, ts(a), ts(e + 0.15), txt))
    print("-> build/audio/mix.wav")


if __name__ == "__main__":
    main()
