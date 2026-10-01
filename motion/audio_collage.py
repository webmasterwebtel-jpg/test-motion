"""Bande-son du « Crochet Pop Collage » : musique de fond discrète + bruitages, sans voix.

Réutilise les instruments et SFX de audio.py ; la musique (120 BPM) garde la même structure,
mais elle est mixée nettement sous les bruitages. Sortie : build/audio/collage_mix.wav
"""
import numpy as np
from scipy.io import wavfile
import audio as A
from audio import (SR, N, BEAT, buf, add, noise, tvec, bp, hp, lp, impact, heartbeat, whoosh, snap, tick,
                   yarn_slide, riser, rev_cymbal, shimmer, reverb, limiter, write)

rng = np.random.default_rng(7)


def paper_slap(level=1.0):
    """Sticker plaqué sur la table : claque de papier + petit coup sourd."""
    t = tvec(0.25)
    x = bp(noise(0.25), 600, 5000) * np.exp(-t / 0.025)
    x += np.sin(2 * np.pi * (90 + 80 * np.exp(-t / 0.02)) * t) * np.exp(-t / 0.06) * 0.7
    return np.tanh(x * 1.5) * 0.8 * level


def tape_rip(dur=0.22):
    t = tvec(dur)
    crackle = (rng.random(len(t)) < 0.08).astype(float) * rng.uniform(0.3, 1, len(t))
    x = hp(noise(dur) * 0.4 + crackle, 1500) * np.clip(t / 0.02, 0, 1) * np.exp(-t / (dur * 0.5))
    return x * 0.6


def pop(f0=500, f1=1400):
    """« Bloup » d'ouverture d'iris."""
    t = tvec(0.12)
    f = f0 + (f1 - f0) * (t / 0.12)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.035) * 0.7


def clatter(dur=0.45, n=40):
    """Nuée de petits clics (carreaux qui se retournent)."""
    out = np.zeros(int(dur * SR))
    c = tick()
    for _ in range(n):
        i = int(rng.uniform(0, dur * 0.85) * SR)
        g = rng.uniform(0.2, 0.7)
        seg = c[: len(out) - i] * g
        out[i:i + len(seg)] += seg
    return out


def clack():
    """Case de grille qui se verrouille (déclic mécanique)."""
    t = tvec(0.1)
    x = bp(noise(0.1), 1500, 7000) * np.exp(-t / 0.006)
    x += np.sin(2 * np.pi * 900 * t) * np.exp(-t / 0.015) * 0.4
    return x


def sfx():
    b = buf()
    # 0–4 : pelote qui roule, carrés tamponnés, explosion -> look
    add(b, yarn_slide(0.6, 0.35), 0.0)
    add(b, lp(noise(0.5), 400) * np.exp(-tvec(0.5) / 0.3) * 0.25, 0.0)
    for t0 in (0.5, 1.5):
        add(b, heartbeat(), t0, 0.8)
        add(b, paper_slap(1.0), t0, 0.9)
    add(b, whoosh(0.5, 300, 3500, 0.85), 2.0, 0.5)
    add(b, impact(1.1), 2.5, 0.9)
    add(b, whoosh(0.6, 3000, 400, 0.2), 2.5, 0.6)
    add(b, shimmer(0.8), 2.55, 0.7)
    add(b, riser(1.0, 0.22), 3.0)
    # 4–10 : pile de stickers (entrée variée + claque + ruban)
    entries = [(4.0, "drop"), (5.0, "spin"), (6.0, "slide"), (7.0, "flip"), (8.0, "drop"), (9.0, "spin")]
    for t0, kind in entries:
        land = t0 + (0.16 if kind == "drop" else 0.1)
        if kind == "drop":
            add(b, whoosh(0.2, 2000, 400, 0.8), t0 - 0.04, 0.5)
        elif kind == "spin":
            add(b, whoosh(0.32, 300, 5000, 0.5), t0 - 0.05, 0.55)
        elif kind == "slide":
            add(b, whoosh(0.3, 600, 6000, 0.6), t0 - 0.08, 0.6)
        else:
            add(b, whoosh(0.25, 800, 4000, 0.5), t0 - 0.05, 0.45)
        add(b, paper_slap(), land, 0.85, rng.uniform(-0.3, 0.3))
        add(b, tape_rip(), t0 + 0.24, 0.55, 0.3)
    add(b, riser(0.5, 0.35), 9.5)
    add(b, whoosh(0.45, 300, 6000, 0.9), 9.55, 0.6)
    # 10–17 : zoom infini (whoosh qui monte + « bloup » à chaque iris)
    shots = [10.0 + 0.5 * k for k in range(12)] + [16.0, 16.25, 16.5, 16.75]
    for k, st in enumerate(shots):
        du = 0.5 if st < 16 else 0.25
        add(b, pop(450 + 30 * k, 1300 + 60 * k), st - du * 0.4 if k else 9.8, 0.55)
        add(b, whoosh(du, 400, 5000 + 200 * k, 0.9), st, 0.3)
        add(b, tick(), st, 0.6)
    add(b, riser(3.0, 0.35), 14.0)
    add(b, rev_cymbal(1.0, 0.25), 16.0)
    # 17–24 : silence, BOOM, mosaïque qui se retourne, échos riso
    add(b, impact(1.5, 2.5), 17.5, 1.0)
    add(b, clatter(0.5, 60), 17.5, 0.7)
    for t0 in (18.0, 18.5, 19.0, 19.5, 20.0):
        add(b, clatter(0.35, 35), t0, 0.75)
        add(b, snap(), t0, 0.45)
    add(b, whoosh(0.35, 5000, 500, 0.4), 20.45, 0.5)
    add(b, impact(0.5, 0.8), 20.75, 0.5)
    add(b, yarn_slide(2.8, 0.15), 20.8, 1.0, 0.3)
    add(b, whoosh(0.4, 300, 6000, 0.8), 23.6, 0.8)
    # 24–31 : grille bento (déclics + glissements à chaque réorganisation)
    for t0 in (24.0, 25.5, 27.0, 28.5):
        add(b, whoosh(0.35, 500, 6000, 0.4), t0 - 0.05, 0.45)
        for j in range(6):
            add(b, clack(), t0 + 0.045 * j + 0.25, 0.45, (j % 2 - 0.5) * 0.8)
    add(b, impact(0.8, 1.2), 24.0, 0.55)
    add(b, rev_cymbal(0.5, 0.25), 29.5)
    add(b, whoosh(0.6, 300, 4000, 0.5), 30.0, 0.6)
    add(b, impact(0.9, 1.4), 30.3, 0.6)
    # 31–37 : carrousel (swish + clic à chaque cran)
    add(b, impact(1.0, 1.5), 31.0, 0.6)
    for k in range(1, 12):
        t0 = 31.0 + k * BEAT
        add(b, whoosh(0.22, 700, 6000, 0.4), t0 - 0.02, 0.35, 0.5 if k % 2 else -0.5)
        add(b, tick(), t0 + 0.06, 0.55)
    add(b, riser(1.8, 0.28), 35.1)
    # 37–40 : aspiration en pelote, déroulé en fleur
    add(b, whoosh(0.6, 200, 7000, 0.85), 36.75, 0.85)
    add(b, yarn_slide(1.0, 0.35), 37.0)
    add(b, lp(noise(0.6), 250) * np.sin(np.linspace(0, np.pi, int(0.6 * SR))) * 0.3, 37.4)
    add(b, impact(1.6, 2.5), 38.0, 1.0)
    for k in range(10):
        add(b, whoosh(0.18, 2000, 9000, 0.3), 38.0 + 0.02 * k, 0.18, (k / 9 - 0.5) * 1.6)
    for k in range(10):
        add(b, pop(900 + 60 * k, 1800 + 80 * k), 38.2 + 0.05 * k, 0.3, (k / 9 - 0.5))
    add(b, shimmer(2.0), 38.05, 1.4)
    add(b, shimmer(1.8), 38.5, 1.0, 0.4)
    b += reverb(b, wet=0.2, dur=1.2, decay=0.35)
    i0, i1, r = int(17.0 * SR), int(17.5 * SR), int(0.004 * SR)
    b[i0 - r:i0] *= np.linspace(1, 0, r)[:, None]
    b[i0:i1] = 0
    return b


def main():
    print("musique…"); m = A.music()
    print("bruitages…"); s = sfx()
    m /= np.abs(m).max() + 1e-9
    s /= np.abs(s).max() + 1e-9
    # musique de fond : nettement sous les bruitages (≈ -11 dB)
    mix = m * 0.24 + s * 0.8
    mix = limiter(mix * 1.15)
    tt = np.arange(N) / SR
    fade = np.clip((40.0 - tt) / 0.6, 0, 1)
    mix *= fade[:, None]
    write("collage_music.wav", m * 0.24); write("collage_sfx.wav", s * 0.8)
    write("collage_mix.wav", mix)
    print("-> build/audio/collage_mix.wav")


if __name__ == "__main__":
    main()
