"""Bande-son du « Crochet Pop Collage » : musique de fond discrète + bruitages, sans voix.

Réutilise les instruments et SFX de audio.py ; la musique (120 BPM) suit les repères du film de 60 s
(MARKS) et elle est mixée nettement sous les bruitages. Sortie : build/audio/collage_mix.wav
"""
import numpy as np
from scipy.io import wavfile
import audio as A

A.DUR = 60.0                       # le film dure 60 s : on redimensionne les bus avant tout import de N
A.N = int(A.SR * A.DUR)
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


# repères musicaux du film de 60 s
MARKS = dict(start=4.0, build=22.0, roll=27.0, cut=28.0, back=28.5, restart=29.0, hats2=31.0, drop=35.0,
             climax=47.0, end=55.0)
PILE = [(4.0, "drop"), (6.0, "spin"), (8.0, "slide"), (10.0, "flip"), (12.0, "drop"), (14.0, "spin")]
ZOOM = [16.0, 18.0, 20.0, 22.0, 24.0, 26.0]
ZOOM_IN = 0.6
CAR0, CSTEP, CEND = 39.0, 2.0, 55.0
FIN = 18.0   # décalage du final (temps internes 37–42 -> 55–60)


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
    # 4–16 : pile de stickers, un look toutes les 2 s
    for t0, kind in PILE:
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
    add(b, riser(0.5, 0.35), 15.5)
    add(b, whoosh(0.45, 300, 6000, 0.9), 15.55, 0.6)
    add(b, pop(450, 1300), 15.8, 0.55)
    # 16–28 : chaque look posé ~1,4 s, puis plongée dans les mailles + iris
    for k, st in enumerate(ZOOM):
        z0 = st + 2.0 - ZOOM_IN
        add(b, tick(), st, 0.5)
        add(b, whoosh(ZOOM_IN, 400, 5000 + 300 * k, 0.9), z0, 0.35)
        if k + 1 < len(ZOOM):
            add(b, pop(480 + 40 * k, 1350 + 80 * k), z0 + ZOOM_IN * 0.58, 0.55)
    add(b, riser(2.0, 0.3), 26.0)
    add(b, rev_cymbal(1.0, 0.25), 27.0)
    # 28–35 : silence, BOOM, mosaïque, échos riso
    add(b, impact(1.5, 2.5), 28.5, 1.0)
    add(b, clatter(0.5, 60), 28.5, 0.7)
    add(b, clatter(0.45, 50), 30.0, 0.8)
    add(b, snap(), 30.0, 0.45)
    add(b, whoosh(0.35, 5000, 500, 0.4), 31.45, 0.5)
    add(b, impact(0.5, 0.8), 31.75, 0.5)
    add(b, yarn_slide(2.8, 0.15), 31.8, 1.0, 0.3)
    add(b, whoosh(0.4, 300, 6000, 0.8), 34.6, 0.8)
    # 35–39 : grille bento (déclics + glissements)
    for t0 in (35.0, 37.0):
        add(b, whoosh(0.35, 500, 6000, 0.4), t0 - 0.05, 0.45)
        for j in range(6):
            add(b, clack(), t0 + 0.045 * j + 0.25, 0.45, (j % 2 - 0.5) * 0.8)
    add(b, impact(0.8, 1.2), 35.0, 0.55)
    add(b, whoosh(0.6, 300, 4000, 0.5), 38.6, 0.6)
    add(b, impact(0.9, 1.4), 38.9, 0.6)
    # 39–55 : carrousel, un cran toutes les 2 s
    for k in range(1, int((CEND - CAR0) / CSTEP)):
        t0 = CAR0 + k * CSTEP
        add(b, whoosh(0.35, 600, 5500, 0.4), t0 - 0.03, 0.4, 0.5 if k % 2 else -0.5)
        add(b, tick(), t0 + 0.1, 0.5)
    add(b, riser(1.8, 0.28), CEND - 1.9)
    # 55–60 : aspiration en pelote, déroulé en fleur
    add(b, whoosh(0.6, 200, 7000, 0.85), CEND - 0.25, 0.85)
    add(b, yarn_slide(1.0, 0.35), CEND)
    add(b, lp(noise(0.6), 250) * np.sin(np.linspace(0, np.pi, int(0.6 * SR))) * 0.3, CEND + 0.4)
    add(b, impact(1.6, 2.5), CEND + 1.0, 1.0)
    for k in range(10):
        add(b, whoosh(0.18, 2000, 9000, 0.3), CEND + 1.0 + 0.02 * k, 0.18, (k / 9 - 0.5) * 1.6)
    for k in range(10):
        add(b, pop(900 + 60 * k, 1800 + 80 * k), CEND + 1.2 + 0.05 * k, 0.3, (k / 9 - 0.5))
    add(b, shimmer(2.0), CEND + 1.05, 1.4)
    add(b, shimmer(1.8), CEND + 1.5, 1.0, 0.4)
    b += reverb(b, wet=0.2, dur=1.2, decay=0.35)
    i0, i1, r = int(MARKS["cut"] * SR), int(MARKS["back"] * SR), int(0.004 * SR)
    b[i0 - r:i0] *= np.linspace(1, 0, r)[:, None]
    b[i0:i1] = 0
    return b


def main():
    print("musique…"); m = A.music(MARKS)
    print("bruitages…"); s = sfx()
    m /= np.abs(m).max() + 1e-9
    s /= np.abs(s).max() + 1e-9
    # musique de fond : nettement sous les bruitages (≈ -11 dB)
    mix = m * 0.24 + s * 0.8
    mix = limiter(mix * 1.15)
    tt = np.arange(N) / SR
    fade = np.clip((A.DUR - tt) / 0.8, 0, 1)
    mix *= fade[:, None]
    write("collage_music.wav", m * 0.24); write("collage_sfx.wav", s * 0.8)
    write("collage_mix.wav", mix)
    print("-> build/audio/collage_mix.wav")


if __name__ == "__main__":
    main()
