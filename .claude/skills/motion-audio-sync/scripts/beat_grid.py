#!/usr/bin/env python3
"""Analyse d'une musique pour caler une animation : tempo, temps, premiers temps de mesure, attaques fortes,
structure (énergie par mesure, ruptures : drops, breaks, silences).

Fonctionne sur un .wav/.mp3 ou une vidéo (ffmpeg extrait l'audio). Dépendances : numpy, scipy, ffmpeg.

Exemples :
    python3 beat_grid.py musique.mp3                       # tout détecter
    python3 beat_grid.py musique.mp3 --bpm 120             # tempo connu : ne cherche que la phase
    python3 beat_grid.py musique.mp3 --fps 30 --out build/audio/grid.json
Sortie : rapport texte + JSON {bpm, offset, beats[], downbeats[], onsets[], bars[{t, energy, change}], frames}.
"""
import argparse, json, os, subprocess
import numpy as np
from scipy import ndimage, signal

SR = 22050
HOP = 220                    # ≈ 100 valeurs par seconde
RATE = SR / HOP
N_FFT = 1024
T0 = (N_FFT / 2) / SR        # l'indice i de l'enveloppe correspond au temps i/RATE + T0 (centre de fenêtre)
BIAS = 0.012                 # retard moyen mesuré entre l'attaque réelle et sa détection (pistes de test)


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def envelopes(x):
    """Enveloppe d'attaques (flux spectral par bandes) et énergie grave (kick) à RATE Hz."""
    n_fft = N_FFT
    f, t, Z = signal.stft(x, SR, nperseg=n_fft, noverlap=n_fft - HOP, boundary=None, padded=False)
    S = np.abs(Z)
    edges = np.geomspace(30, 11000, 9)
    bands = np.stack([S[(f >= a) & (f < b)].sum(0) for a, b in zip(edges[:-1], edges[1:])])
    lb = np.log10(bands ** 2 + (bands ** 2).mean(1, keepdims=True) * 1e-5 + 1e-12)
    flux = np.maximum(np.diff(lb, axis=1, prepend=lb[:, :1]), 0).sum(0)
    flux = np.maximum(flux - ndimage.median_filter(flux, 25), 0)
    low = np.log10((S[(f >= 30) & (f < 150)] ** 2).sum(0) + 1e-9)
    kick = np.maximum(np.diff(low, prepend=low[0]), 0)
    return flux, kick, t, (S ** 2).sum(0)


def tempo(env, lo=70, hi=180, prior=118):
    """BPM par autocorrélation pondérée (préférence douce autour de `prior`), affinée par interpolation."""
    e = env - env.mean()
    ac = np.correlate(e, e, "full")[len(e) - 1:]
    ac /= ac[0] + 1e-9
    lags = np.arange(len(ac))
    bpm = 60 * RATE / np.maximum(lags, 1)
    ok = (bpm >= lo) & (bpm <= hi)
    # renforcer les multiples (2 et 4 temps) pour éviter les erreurs d'octave
    score = np.zeros_like(ac)
    for L in np.nonzero(ok)[0]:
        s = ac[L]
        for m in (2, 4):
            if L * m < len(ac):
                s += 0.5 * ac[L * m]
        score[L] = s * np.exp(-0.5 * (np.log2(bpm[L] / prior) / 0.9) ** 2)
    L = int(np.argmax(score))
    if 1 <= L < len(score) - 1:                       # interpolation parabolique
        a, b, c = score[L - 1], score[L], score[L + 1]
        L = L + 0.5 * (a - c) / (a - 2 * b + c + 1e-12)
    return 60 * RATE / L


def grid_score(env, bpm, offs):
    """Score de la grille (bpm, décalages en indices d'enveloppe), vectorisé sur les décalages."""
    period = 60 * RATE / bpm
    k = np.arange(0, (len(env) - 2) / period)
    idx = np.round(offs[:, None] + k[None, :] * period).astype(int)
    idx = np.clip(idx, 1, len(env) - 2)
    return env[idx].sum(1) + 0.5 * (env[idx - 1].sum(1) + env[idx + 1].sum(1))


def refine(env, bpm, span=1.5, step=0.01):
    """Affine le tempo (±span BPM) et la phase en maximisant l'alignement de toute la grille."""
    best = (-1, bpm, 0.0)
    for b in np.arange(bpm - span, bpm + span + 1e-9, step):
        offs = np.arange(0, 60 * RATE / b, 0.25)
        sc = grid_score(env, b, offs)
        i = int(np.argmax(sc))
        if sc[i] > best[0]:
            best = (sc[i], b, offs[i])
    return best[1], best[2]


def phase(env, bpm):
    """Décalage (s) du premier temps qui maximise l'énergie d'attaque sur la grille."""
    offs = np.arange(0, 60 * RATE / bpm, 0.25)
    return offs[int(np.argmax(grid_score(env, bpm, offs)))] / RATE + T0 + BIAS


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio")
    ap.add_argument("--bpm", type=float, default=None, help="tempo connu (sinon détecté)")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--beats-per-bar", type=int, default=4)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    x = load(a.audio)
    dur = len(x) / SR
    flux, kick, _, power = envelopes(x)
    flux_n = flux / (np.percentile(flux, 99) + 1e-9)
    if a.bpm:
        bpm = a.bpm
    else:
        bpm, _ = refine(flux_n, tempo(flux_n))
        # les productions sont presque toujours à BPM entier : on garde l'entier s'il aligne aussi bien
        r = float(round(bpm))
        offs = np.arange(0, 60 * RATE / r, 0.25)
        if abs(bpm - r) < 0.35 and grid_score(flux_n, r, offs).max() >= 0.97 * grid_score(
                flux_n, bpm, np.arange(0, 60 * RATE / bpm, 0.25)).max():
            bpm = r
    off = phase(flux_n, bpm)
    beat = 60 / bpm
    beats = list(np.arange(off, dur, beat))
    # premier temps de mesure : la phase (mod 4) où le grave frappe le plus
    kick_n = kick / (np.percentile(kick, 99) + 1e-9)
    bpb = a.beats_per_bar
    acc = []
    for k in range(bpb):
        idx = np.round((np.array(beats[k::bpb]) - T0 - BIAS) * RATE).astype(int)
        win = np.clip(idx[:, None] + np.arange(-3, 4)[None, :], 0, len(kick_n) - 1)   # ±30 ms
        acc.append(kick_n[win].max(1).sum() + 0.3 * flux_n[win].max(1).sum())
    down0 = int(np.argmax(acc))
    srt = sorted(acc)
    conf = (srt[-1] - srt[-2]) / (srt[-1] + 1e-9)
    downbeats = beats[down0::bpb]
    # musique effective : ignorer les temps dans le silence (intro sans musique)
    rms = np.sqrt(ndimage.uniform_filter1d(power, int(RATE * 0.5)) + 1e-12)
    loud = 20 * np.log10(rms / (rms.max() + 1e-12))
    # structure : énergie par mesure et ruptures
    bars = []
    edges = downbeats + [downbeats[-1] + bpb * beat] if downbeats else []
    for i in range(len(edges) - 1):
        s, e = int((edges[i] - T0) * RATE), int((min(edges[i + 1], dur) - T0) * RATE)
        s, e = max(s, 0), min(e, len(power))
        if e - s < 2:
            continue
        db = float(10 * np.log10(power[s:e].mean() / (power.mean() + 1e-12) + 1e-12))
        bars.append(dict(t=round(edges[i], 3), energy_db=round(db, 1),
                         onsets=int((flux_n[s:e] > 0.5).sum())))
    for i, b in enumerate(bars):
        prev = bars[i - 1]["energy_db"] if i else b["energy_db"]
        d = b["energy_db"] - prev
        b["change"] = "DROP/entrée" if d > 4 else "BREAK/retombée" if d < -4 else ""
        if b["energy_db"] < -20:
            b["change"] = (b["change"] + " silence").strip()
    onsets = [round(i / RATE + T0, 3) for i in signal.find_peaks(flux_n, height=0.6, distance=int(RATE * 0.08))[0]]
    frames = [int(round(t * a.fps)) for t in beats]
    drift = max(abs(t * a.fps - round(t * a.fps)) for t in beats) if beats else 0

    print("== %s · %.2f s" % (os.path.basename(a.audio), dur))
    print("tempo %.2f BPM%s · 1 temps = %.4f s = %.2f images à %g i/s · mesure = %.3f s"
          % (bpm, " (imposé)" if a.bpm else " (détecté)", beat, beat * a.fps, a.fps, beat * bpb))
    print("premier temps %.3f s · premier temps fort de mesure %.3f s (temps n°%d, confiance %s)"
          % (beats[0], downbeats[0], down0 + 1, ("%.2f" % conf) if conf > 0.05 else "faible : vérifier à l'oreille / sur la structure"))
    print("écart max temps / image entière : %.2f image%s" % (drift, " → arrondir chaque temps" if drift > 0.25 else ""))
    print("attaques fortes : %d · ex. %s" % (len(onsets), ", ".join("%.2f" % o for o in onsets[:12])))
    print("\nmesure  début(s)  énergie(dB)  attaques  rupture")
    for i, b in enumerate(bars):
        print("%5d  %8.2f  %10.1f  %8d  %s" % (i + 1, b["t"], b["energy_db"], b["onsets"], b["change"]))
    rep = dict(file=a.audio, duration=float(dur), bpm=round(bpm, 3), beat=beat, offset=round(beats[0], 4),
               first_downbeat=round(downbeats[0], 4), beats=[round(t, 4) for t in beats],
               downbeats=[round(t, 4) for t in downbeats], beat_frames=frames, fps=a.fps, onsets=onsets, bars=bars)
    out = a.out or os.path.join("build", "audio", os.path.splitext(os.path.basename(a.audio))[0] + "_grid.json")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as fh:
        json.dump(rep, fh, indent=1)
    print("\n->", out)


if __name__ == "__main__":
    main()
