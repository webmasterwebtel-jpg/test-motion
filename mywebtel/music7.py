#!/usr/bin/env python3
"""Musique V7 MyWebtel : électro-pop entraînante à 120 BPM, entièrement synthétisée (numpy), calée sur la voix.

Production : grosse caisse quatre temps, claps, charleston, roulement de caisse claire dans les montées, basse en
contretemps, accords « supersaw » qui pompent sous la grosse caisse (sidechain), mélodie en arpège pincé avec écho
ping-pong, nappes pour les respirations, réverbération de salle (audio_fx.reverb).
Structure (lue dans build/mywebtel/timeline.json) :
  intro énergique sur l'accroche -> montée sur « Et si tout se faisait au même endroit ? » -> DROP sur le logo ->
  groove plein sur les fonctions -> coupure sur « imprimer, signer, scanner… sauf que non » -> retour du groove ->
  respiration de l'agent -> montée -> DROP final sur le logo -> accord final.
Sorties : build/mywebtel/music7/<piste>.wav et build/mywebtel/music.wav (mixage sans ducking ; le ducking sous la voix
se fait dans sfx_mix.py).
"""
import json, os, sys
import numpy as np
import soundfile as sf
from scipy import signal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_fx as FX

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "mywebtel")
SR = 48000
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
rng = np.random.default_rng(120)


def hz(m): return 440.0 * 2 ** ((m - 69) / 12)


def saw(f, d, ph0=0.0):                            # dent de scie limitée en bande (polyBLEP)
    n = int(d * SR)
    dt = f / SR
    ph = (ph0 + dt * np.arange(n)) % 1.0
    y = 2 * ph - 1
    m = ph < dt; x = ph[m] / dt; y[m] -= x + x - x * x - 1
    m = ph > 1 - dt; x = (ph[m] - 1) / dt; y[m] -= x * x + x + x + 1
    return y


def env_adsr(n, a=0.005, d=0.1, s=0.6, r=0.05, hold=None):
    t = np.arange(n) / SR
    hold = n / SR - r if hold is None else hold
    e = np.where(t < a, t / max(a, 1e-4), s + (1 - s) * np.exp(-(t - a) / max(d, 1e-4)))
    rel = np.clip((t - hold) / max(r, 1e-4), 0, 1)
    return e * (1 - rel)


def lp_var(x, f0, f1, tau):                         # passe-bas à coupure qui glisse (par blocs)
    n = len(x); out = np.zeros(n); hop = 256; zi = None
    for i in range(0, n, hop):
        fc = f1 + (f0 - f1) * np.exp(-(i / SR) / tau)
        sos = signal.butter(2, min(fc, SR / 2 - 200), "low", fs=SR, output="sos")
        if zi is None: zi = signal.sosfilt_zi(sos) * x[0]
        out[i:i + hop], zi = signal.sosfilt(sos, x[i:i + hop], zi=zi)
    return out


# ------------------------------------------------------------------ instruments
def kick():
    t = np.arange(int(0.45 * SR)) / SR
    f = 46 + 115 * np.exp(-t / 0.032)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.27) * np.minimum(1, t / 0.001)
    click = FX.hp(FX.noise(0.45), 3500) * np.exp(-t / 0.0018) * 0.35
    return np.tanh(1.6 * (body + click)) / np.tanh(1.6)


def clap():
    d = 0.5; t = np.arange(int(d * SR)) / SR; x = np.zeros_like(t)
    for k, t0 in enumerate((0, 0.009, 0.018)):
        i = int(t0 * SR); tt = t[: len(t) - i]
        x[i:] += FX.bp(FX.noise(d), 900, 4200)[: len(tt)] * np.exp(-tt / 0.006)
    i = int(0.026 * SR); tt = t[: len(t) - i]
    x[i:] += FX.bp(FX.noise(d), 800, 5000)[: len(tt)] * np.exp(-tt / 0.11) * 0.8
    return FX.norm(x)


def hat(open_=False):
    d = 0.25 if open_ else 0.06
    t = np.arange(int(d * SR)) / SR
    return FX.norm(FX.hp(FX.noise(d), 7500) * np.exp(-t / (0.11 if open_ else 0.022)))


def bass_note(m, d):
    f = hz(m)
    x = saw(f, d) * 0.6 + np.sin(2 * np.pi * f / 2 * np.arange(int(d * SR)) / SR) * 0.8
    x = lp_var(x, 1100, 240, 0.06)
    return x * env_adsr(len(x), 0.004, 0.12, 0.7, 0.03)


def supersaw(m_list, d, cutoff=4200, attack=0.004, release=0.06, spread=(-14, -7, 0, 7, 14)):
    n = int(d * SR); L = np.zeros(n); R = np.zeros(n)
    for m in m_list:
        for k, c in enumerate(spread):
            v = saw(hz(m) * 2 ** (c / 1200), d, rng.random())
            (L if k % 2 == 0 else R)[:] += v * (0.8 if c else 1.0)
            if c == 0: R += v * 0.8
    x = np.stack([L, R], 1) / (len(m_list) * 3.5)
    x = FX.lp(x.T, cutoff).T if x.ndim == 2 else x
    e = env_adsr(n, attack, 0.2, 0.75, release)
    return x * e[:, None]


def pluck(m, d=0.32):
    n = int(d * SR); f = hz(m)
    x = saw(f, d) * 0.7 + np.sign(np.sin(2 * np.pi * f * np.arange(n) / SR)) * 0.25
    x = lp_var(x, 7000, 900, 0.07)
    return x * np.exp(-np.arange(n) / SR / 0.14) * np.minimum(1, np.arange(n) / SR / 0.002)


# ------------------------------------------------------------------ partition
CH = {"Bm": (47, [59, 62, 66, 71]), "G": (43, [59, 62, 67, 71]), "D": (50, [57, 62, 66, 69]), "A": (45, [57, 61, 64, 69])}
PROG = ["Bm", "G", "D", "A"]
ARP = {"Bm": [78, 74, 71, 74, 78, 81, 78, 74], "G": [79, 74, 71, 74, 79, 83, 79, 74],
       "D": [78, 74, 69, 74, 78, 81, 78, 74], "A": [76, 73, 69, 73, 76, 81, 76, 73]}


def main():
    tl = json.load(open(os.path.join(OUT, "timeline.json")))
    total = tl["duration"]; N = int(total * SR) + SR
    nb = int(round(total / BAR))
    sc = {s["id"]: s for s in tl["scenes"]}
    fold = lambda w: w.lower().replace("é", "e").replace("’", "'")
    def W(sid, word, n=0):
        return [w for g in sc[sid]["segs"] for w in g["words"] if fold(w[0]) == fold(word)][n][1]
    bar_at = lambda t: int(round(t / BAR))
    drop1 = bar_at(sc["reveal"]["segs"][0]["start"])                 # premier temps du logo
    drop2 = bar_at(sc["fin"]["segs"][0]["start"])                    # logo final
    t_imp, t_non = W("signature", "l'imprimer"), W("signature", "non")
    brk0 = int(t_imp // BAR) - 1 if (t_imp % BAR) < 0.6 else int(t_imp // BAR)   # coupure : imprimer, signer, scanner
    back = int(np.ceil((t_non + 0.2) / BAR))                                      # retour du groove sur les éclats (premier temps)
    agent0 = int(round((sc["agent"]["start"] + 0.4) / BAR))
    build2 = drop2 - 2
    SEC = {}
    for b in range(nb):
        if b < drop1 - 2: SEC[b] = "intro"
        elif b < drop1: SEC[b] = "build"
        elif b < brk0: SEC[b] = "drop" if b < drop1 + 8 else "groove"
        elif b < back: SEC[b] = "break"
        elif b < agent0: SEC[b] = "groove"
        elif b < build2: SEC[b] = "agent"
        elif b < drop2: SEC[b] = "build"
        elif b < nb - 1: SEC[b] = "drop"
        else: SEC[b] = "end"
    stems = {k: np.zeros((N, 2)) for k in ("kick", "perc", "bass", "chords", "lead", "pad", "fx")}

    def put(name, x, t0, gain=1.0, pan=0.0):
        i = int(round(t0 * SR))
        if i >= N: return
        if x.ndim == 1:
            l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            x = np.stack([x * l, x * r], 1) * np.sqrt(2)
        n = min(len(x), N - i)
        stems[name][i:i + n] += x[:n] * gain

    K, CL, HC, HO = kick(), clap(), hat(), hat(True)
    kicks = []
    stop0, stop1 = t_non - 0.12, back * BAR                           # silence de « Sauf que non. » jusqu'au retour
    for b in range(nb):
        s = SEC[b]; t0 = b * BAR; ch = PROG[b % 4]; root, voic = CH[ch]
        silent = lambda t: stop0 <= t < stop1
        # --- batterie
        for k in range(4):
            t = t0 + k * BEAT
            if silent(t): continue
            if s in ("intro", "drop", "groove", "agent") or (s == "build" and not (b == drop1 - 1 and k == 3) and not (b == drop2 - 1 and k == 3)):
                g = 0.55 if s == "agent" and k % 2 else 1.0
                if s == "agent" and k % 2: continue
                put("kick", K, t, g); kicks.append(t)
            if s in ("drop", "groove") or (s == "intro" and b >= 2):
                if k in (1, 3): put("perc", CL, t, 0.55, 0.05)
            if s in ("intro", "drop", "groove", "build", "agent"):
                for h in range(2):
                    th = t + h * BEAT / 2
                    if silent(th) or (s == "build" and b in (drop1 - 1, drop2 - 1) and k == 3): continue
                    put("perc", HO if (h == 1 and s in ("drop", "groove")) else HC, th, (0.22 if h else 0.16) * rng.uniform(0.85, 1.1), 0.25)
            if s in ("drop", "groove"):
                for h in (1, 3):
                    if not silent(t + h * BEAT / 4): put("perc", HC, t + h * BEAT / 4, 0.08, -0.3)
        if s == "build":                                               # roulement qui accélère vers le drop
            sub = 4 if b % 2 == 0 else 8
            for k in range(sub * 2):
                t = t0 + k * BAR / (sub * 2)
                if (b in (drop1 - 1, drop2 - 1)) and t >= t0 + 3 * BEAT: break
                put("perc", CL, t, 0.18 + 0.4 * (k / (sub * 2)) * (0.6 if b % 2 == 0 else 1.0), 0.0)
        # --- basse (contretemps)
        if s in ("drop", "groove") or (s == "intro" and b >= 4):
            for k in range(4):
                t = t0 + k * BEAT + BEAT / 2
                if not silent(t): put("bass", bass_note(root - 12 + (12 if (k == 3 and b % 2) else 0), BEAT * 0.45), t, 0.9)
                if k == 0 and not silent(t0): put("bass", bass_note(root - 12, BEAT * 0.3), t0, 0.55)
        if s == "agent":
            put("bass", bass_note(root - 12, BAR * 0.95), t0, 0.5)
        # --- accords
        if s in ("drop", "groove"):
            for k in range(4):
                t = t0 + k * BEAT + BEAT / 2
                if not silent(t): put("chords", supersaw(voic, BEAT * 0.42, 4800), t, 0.9)
            if s == "drop" and b % 2 == 0 and not silent(t0): put("chords", supersaw([v + 12 for v in voic[1:]], BEAT * 0.3, 7000), t0, 0.35)
        if s in ("intro",) and b >= 1:
            for k in range(4):
                t = t0 + k * BEAT + BEAT / 2
                put("chords", supersaw(voic, BEAT * 0.4, 1600 + 500 * b), t, 0.5)
        if s == "break":                                               # suspense : pulsation étouffée en croches
            for k in range(8):
                t = t0 + k * BEAT / 2
                if not silent(t): put("chords", supersaw(voic[:3], BEAT * 0.3, 700), t, 0.9)
            for k in range(4):
                if not silent(t0 + k * BEAT): put("kick", FX.lp(K, 180), t0 + k * BEAT, 0.5)
        if s in ("break", "agent", "build", "end"):
            if not (s == "break" and t0 + BAR > stop0 and t0 < stop1):
                put("pad", supersaw(voic, BAR * 1.02, 1800 if s != "build" else 1200 + 2500 * ((b % 2) / 1.0), attack=0.25, release=0.3), t0, 1.6)
            elif t0 < stop0:
                put("pad", supersaw(voic, stop0 - t0, 1800, attack=0.25, release=0.05), t0, 1.6)
        # --- mélodie (arpège pincé)
        if s in ("intro", "drop", "groove", "agent", "build") and not (s == "intro" and b < 0):
            notes = ARP[ch]
            for k in range(8):
                t = t0 + k * BEAT / 2
                if silent(t) or (s == "build" and b in (drop1 - 1, drop2 - 1) and k >= 6): continue
                lvl = {"intro": 0.32, "drop": 0.5, "groove": 0.36, "agent": 0.4, "build": 0.34}[s]
                put("lead", pluck(notes[k] - (12 if s == "agent" else 0), 0.3), t, lvl, 0.35 * (-1) ** k)
            if s == "agent":
                for k in range(8):
                    t = t0 + k * BEAT / 2 + BEAT / 4
                    put("lead", pluck(notes[(k * 3) % 8] + 12, 0.2), t, 0.14, -0.4 * (-1) ** k)
    # --- effets de structure
    for d, tb in ((drop1, drop1 * BAR), (drop2, drop2 * BAR)):
        put("fx", FX.riser(2 * BAR - 0.08, 200, 9000, 0.55), tb - 2 * BAR)
        put("fx", FX.impact(0.9), tb)
        put("fx", FX.reverse_swell(0.6, 0.0), tb)
        cr = FX.hp(FX.noise(2.5), 5000) * np.exp(-np.arange(int(2.5 * SR)) / SR / 0.7)
        put("fx", FX.norm(cr) * 0.3, tb)                               # crash
    put("fx", FX.reverse_swell(1.0, 0.35), back * BAR - 1.0)           # retour du groove après les éclats
    put("fx", FX.norm(FX.hp(FX.noise(2.5), 5000) * np.exp(-np.arange(int(2.5 * SR)) / SR / 0.7)) * 0.25, back * BAR)
    endt = (nb - 1) * BAR
    root, voic = CH["D"]
    put("pad", supersaw(voic + [74, 78], BAR * 1.4, 3000, attack=0.01, release=1.0), endt, 1.0)
    put("bass", bass_note(root - 12, BAR * 1.2), endt, 0.9)
    put("kick", K, endt, 1.0)
    # --- sidechain (pompage) sous la grosse caisse
    t = np.arange(N) / SR
    sc_env = np.ones(N)
    for tk in kicks:
        i = int(tk * SR); n = int(0.35 * SR)
        tt = np.arange(n) / SR
        g = 1 - 0.7 * np.exp(-tt / 0.11) * np.minimum(1, tt / 0.004 + 0.6)
        sc_env[i:i + n] = np.minimum(sc_env[i:i + n], g[: len(sc_env[i:i + n])])
    for k in ("bass", "chords", "pad"):
        stems[k] *= sc_env[:, None]
    # --- égalisation : creux autour de 2,5 kHz (place pour la voix), bus et réverbe
    b2, a2 = signal.iirpeak(2600, 0.8, fs=SR)
    for k in ("chords", "lead", "pad"):
        stems[k] = stems[k] - 0.45 * signal.lfilter(b2, a2, stems[k], axis=0)
    gains = {"kick": 0.95, "perc": 0.55, "bass": 0.75, "chords": 0.5, "lead": 0.42, "pad": 0.45, "fx": 0.6}
    os.makedirs(os.path.join(OUT, "music7"), exist_ok=True)
    mix = np.zeros((N, 2))
    for k, x in stems.items():
        x = x * gains[k]
        if k in ("chords", "lead", "pad", "perc", "fx"):
            x = FX.reverb(x, t60=1.8 if k != "pad" else 2.8, wet=0.18 if k in ("chords", "perc") else 0.3, hpf=300, seed=7 + sum(map(ord, k)) % 50)
        sf.write(os.path.join(OUT, "music7", k + ".wav"), x[: int(total * SR)].astype(np.float32), SR)
        mix += x
    mix = mix[: int(total * SR)]
    # dynamique par section : l'intro et les respirations en retrait, la montée qui gonfle, le drop à fond
    lvl = {"intro": 0.5, "build": None, "drop": 1.0, "groove": 0.82, "break": 0.62, "agent": 0.6, "end": 1.0}
    g = np.zeros(len(mix)); tt = np.arange(len(mix)) / SR
    for b in range(nb):
        i0, i1 = int(b * BAR * SR), min(len(mix), int((b + 1) * BAR * SR))
        if SEC[b] == "build":
            first = b == 0 or SEC[b - 1] != "build"
            a0 = 0.55 if first else 0.75
            g[i0:i1] = np.linspace(a0, a0 + 0.2, i1 - i0)
        else:
            g[i0:i1] = lvl[SEC[b]]
    g = np.convolve(g, np.ones(int(0.05 * SR)) / int(0.05 * SR), mode="same")
    mix *= g[:, None]
    mix = np.tanh(1.2 * mix / (np.abs(mix).max() + 1e-9)) / np.tanh(1.2)  # légère saturation de bus (cohésion)
    fade = np.clip((total - np.arange(len(mix)) / SR) / 1.2, 0, 1) ** 1.2
    mix *= fade[:, None]
    mix *= 0.9 / (np.abs(mix).max() + 1e-9)
    sf.write(os.path.join(OUT, "music.wav"), mix.astype(np.float32), SR)
    tl["music"] = {"bpm": BPM, "bar": BAR, "sections": [SEC[b] for b in range(nb)], "drops": [drop1 * BAR, drop2 * BAR], "back": back * BAR}
    json.dump(tl, open(os.path.join(OUT, "timeline.json"), "w"), ensure_ascii=False, indent=1)   # le film pulse sur la grosse caisse
    secs = []; prev = None
    for b in range(nb):
        if SEC[b] != prev: secs.append("%s@%.1fs" % (SEC[b], b * BAR)); prev = SEC[b]
    print(" ".join(secs))
    print("-> build/mywebtel/music.wav (%.1f s, %d mesures, drops à %.1f s et %.1f s)" % (total, nb, drop1 * BAR, drop2 * BAR))


if __name__ == "__main__":
    main()
