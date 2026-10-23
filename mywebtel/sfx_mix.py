#!/usr/bin/env python3
"""Bruitages d'interface discrets + mixage final MyWebtel (voix, musique avec ducking, bruitages).

Les instants des bruitages viennent de build/mywebtel/cues.json, que render.js exporte depuis le film lui-même :
chaque son tombe sur son geste à l'image, sans recopier les formules. Les sons sont synthétisés, courts et feutrés : présence, jamais démonstration.

Règles de mixage (préférences de l'utilisateur) :
  - la voix domine ; la musique est ~10 dB sous la voix et s'abaisse encore de 7 dB pendant la parole (ducking lent) ;
  - les bruitages restent ≥ 10 dB sous les crêtes de la voix ;
  - sortie normalisée à -16 LUFS intégrés, crête vraie ≤ -1,5 dBTP (ffmpeg loudnorm, deux passes).
Sorties : build/mywebtel/sfx.wav, build/mywebtel/mix.wav, et un rapport voix/musique pendant la parole.
"""
import json, math, os, subprocess
import numpy as np
import soundfile as sf
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "mywebtel")
SR = 48000
rng = np.random.default_rng(3)
TL = json.load(open(os.path.join(OUT, "timeline.json")))
SC = {s["id"]: s for s in TL["scenes"]}
DUR = TL["duration"]
N = int(DUR * SR)


def S0(i): return SC[i]["start"]
def S1(i): return SC[i]["end"]
def segT(i, k): return SC[i]["segs"][k]["start"]
def partT(i, k, j): return SC[i]["segs"][k]["parts"][j]
def wordT(i, k, needle):
    s = SC[i]["segs"][k]
    idx = s["text"].lower().index(needle.lower())
    return s["start"] + (s["end"] - s["start"]) * idx / len(s["text"])


# ------------------------------------------------------------------ sons
def tv(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.standard_normal(int(d * SR))
def bp(x, lo, hi): return signal.sosfilt(signal.butter(2, [lo, hi], "band", fs=SR, output="sos"), x)
def hp(x, f): return signal.sosfilt(signal.butter(2, f, "high", fs=SR, output="sos"), x)
def lp(x, f): return signal.sosfilt(signal.butter(2, f, "low", fs=SR, output="sos"), x)


def tap():          # toucher / clic d'interface feutré
    t = tv(0.06)
    return (bp(noise(0.06), 1500, 6000) * np.exp(-t / 0.004) * 0.5 + np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.012) * 0.6)


def tick():         # très petit déclic (dates, frappe)
    t = tv(0.03)
    return hp(noise(0.03), 3500) * np.exp(-t / 0.0025) * 0.35


def pop(f0=520, f1=860, level=0.5):   # apparition d'un élément
    t = tv(0.09)
    f = f0 + (f1 - f0) * (t / 0.09)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.025) * level


def swoosh(d=0.5, f0=500, f1=2500, level=0.35):   # glissé doux
    n = int(d * SR)
    p = np.arange(n) / n
    x = noise(d)
    fc = f0 * (f1 / f0) ** p
    out = np.zeros(n)
    hop = 512
    for i in range(0, n, hop):              # filtre passe-bande glissant, par blocs
        c = fc[min(i, n - 1)]
        out[i:i + hop] = bp(x[max(0, i - 2048):i + hop], c * 0.6, min(c * 1.6, 20000))[-len(out[i:i + hop]):]
    env = np.sin(np.pi * p) ** 2
    return out * env / (np.abs(out).max() + 1e-9) * level


def chime(notes=(1318.5, 1975.5), level=0.22, d=1.2):   # confirmation douce
    t = tv(d)
    x = np.zeros_like(t)
    for k, f in enumerate(notes):
        i0 = int(k * 0.07 * SR)
        tt = t[: len(t) - i0]
        x[i0:] += (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt / 0.08)) * np.exp(-tt / 0.35)
    return x * level


def ping():         # notification
    return chime((880.0, 1318.5), 0.2, 1.0)


def thump(level=0.6):   # impact sourd, sans agressivité (logo)
    t = tv(0.9)
    f = 48 + 40 * np.exp(-t / 0.06)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28) * level


def air(d=1.2, level=0.25):   # souffle montant (montée vers un moment)
    t = tv(d)
    return hp(noise(d), 2500) * (t / d) ** 2.5 * level


# ------------------------------------------------------------------ placement
bus = np.zeros((N, 2))


def add(x, t0, gain=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= N:
        return
    if i0 < 0:
        x, i0 = x[-i0:], 0
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    n = min(len(x), N - i0)
    bus[i0:i0 + n, 0] += x[:n] * l * gain * math.sqrt(2)
    bus[i0:i0 + n, 1] += x[:n] * r * gain * math.sqrt(2)


def keys(t0, t1, n, gain=0.45, pan=0.0):
    """Frappe au clavier : n déclics irréguliers entre t0 et t1."""
    r = np.random.default_rng(int(t0 * 100))
    for k in range(n):
        add(tick(), t0 + (t1 - t0) * (k + r.uniform(-0.3, 0.3)) / max(n, 1), gain * r.uniform(0.7, 1.0), pan + r.uniform(-0.1, 0.1))


def roll(t0, d=0.7, gain=0.35):
    """Défilement rapide de l'heure : petits déclics qui ralentissent."""
    for k in range(10):
        add(tick(), t0 + d * (1 - (1 - k / 10) ** 2), gain)


def cues():
    """Bruitages V2 : les instants viennent de build/mywebtel/cues.json, exporté par le film lui-même (render.js)."""
    C = json.load(open(os.path.join(OUT, "cues.json")))
    T = C["T"]
    # 1. ouverture : une démarche = un petit « pop », puis l'horloge qui s'emballe
    for k, t in enumerate(C["tasks"]):
        add(pop(480, 760, 0.45), t, 0.8, (-0.5, 0.5, -0.4, 0.4)[k])
    r0 = segT("hook", 1)
    tt, k = r0, 0
    while tt < T["logo"] - 0.6:
        add(tick(), tt, 0.55, 0.15 * (-1) ** k)
        tt += max(0.07, 0.3 * (1 - (tt - r0) / (T["logo"] - r0)) ** 1.5)
        k += 1
    add(air(1.6, 0.2), T["logo"] - 1.6)
    # 2. logo
    add(thump(0.55), T["logo"])
    add(chime((1174.7, 1760.0), 0.12, 1.6), T["logo"] + 0.05)
    add(swoosh(0.6, 2200, 700, 0.12), T["tag"] - 0.1)
    add(swoosh(1.2, 300, 1600, 0.24), T["winIn"])                   # la fenêtre monte
    # 3. connexion : frappe du matricule et du mot de passe
    keys(T["typeId"], T["typeId"] + 0.65, 9)
    keys(T["typeId"] + 1.1, T["typeId"] + 1.7, 10)
    # 4. clics (tous les clics du curseur) et changements de page
    for t in C["clicks"]:
        add(tap(), t - 0.02, 0.85, 0.15)
    for t in C["nav"]:
        add(swoosh(0.55, 500, 2200, 0.14), t - 0.1, 1, -0.2)
    # 5. pointage : confirmations, heure qui défile, réseau
    add(chime((1318.5, 1975.5), 0.1, 1.0), T["act"] + 0.45, 1, 0.1)
    add(pop(700, 1000, 0.18), T["minute"] - 0.1, 1, -0.2)
    add(swoosh(0.9, 400, 2000, 0.2), T["net"], 1, 0.5)
    add(swoosh(0.8, 2000, 500, 0.16), T["netEnd"], 1, 0.5)
    for t in (T["noon"], T["ret"], T["eve"]):
        roll(t)
    add(pop(600, 820, 0.22), T["pause"] + 0.05, 1, 0.1)
    add(pop(820, 600, 0.2), T["resume"] + 0.05, 1, 0.1)
    add(chime((1174.7, 1568.0), 0.11, 1.2), T["end"] + 0.05, 1, 0.1)
    # 6. justification
    add(swoosh(0.45, 600, 2600, 0.14), T["jus"] + 0.1)              # la fenêtre de saisie s'ouvre
    keys(T["motif"] + 0.35, T["motif"] + 1.35, 14, 0.4)
    add(pop(500, 750, 0.3), T["pj"] + 0.05, 0.8)
    add(chime((1568.0, 2093.0), 0.08, 0.9), T["jsend"] + 0.25)
    # 7. absences
    add(pop(560, 900, 0.25), T["dem"] + 0.4, 1, 0.4)
    add(pop(500, 750, 0.3), T["ajus"] + 0.05, 0.8, -0.2)
    # 8. tickets
    keys(T["tobj"], T["tobj"] + 0.8, 11, 0.4, -0.2)
    keys(T["tobj"] + 0.95, T["tcreate"] - 0.35, 20, 0.4, -0.2)
    add(pop(560, 900, 0.25), T["tcreate"] + 0.3, 1, 0.4)
    add(chime((1318.5, 1760.0), 0.08, 0.9), T["tcharge"] + 0.1, 1, 0.4)
    # 9. documents RH et documents
    add(swoosh(0.5, 700, 2400, 0.14), T["payslip"] + 0.1, 1, 0.4)
    add(pop(800, 1100, 0.22), T["dlT"] + 0.85, 1, 0.3)
    add(thump(0.22), T["seul"] - 0.05)
    add(tap(), T["seul"] - 0.05, 0.6)
    for k, t in enumerate(C["docs"]):
        add(pop(650 + 40 * k, 950 + 40 * k, 0.14), t, 1, -0.5 + 0.2 * k)
    # 10. signature
    add(air(1.4, 0.16), T["out"])
    add(thump(0.5), T["final"])
    add(chime((1174.7, 1760.0), 0.12, 1.8), T["final"] + 0.05)


# ------------------------------------------------------------------ mixage
def env_follow(x, att, rel):
    a1, a2 = math.exp(-1 / (att * SR)), math.exp(-1 / (rel * SR))
    out = np.empty_like(x)
    e = 0.0
    for i, v in enumerate(x):
        e = a1 * e + (1 - a1) * v if v > e else a2 * e + (1 - a2) * v
        out[i] = e
    return out


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def main():
    cues()
    sf.write(os.path.join(OUT, "sfx.wav"), bus.astype(np.float32), SR)
    vo, _ = sf.read(os.path.join(OUT, "vo.wav"))
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    mu, _ = sf.read(os.path.join(OUT, "music.wav"), always_2d=True)
    mu = np.pad(mu, ((0, max(0, N - len(mu))), (0, 0)))[:N]
    # zones de parole
    speech = np.zeros(N, bool)
    for s in TL["scenes"]:
        for g in s["segs"]:
            speech[int(g["start"] * SR):int(g["end"] * SR)] = True
    v_db = rms_db(vo[speech])
    m_db = rms_db(mu.mean(1))
    mu *= 10 ** ((v_db - 10 - m_db) / 20)                    # musique à -10 dB de la voix…
    hop = 480
    lvl = np.abs(vo[: N // hop * hop]).reshape(-1, hop).max(1)
    e = env_follow(lvl, 0.004, 0.25)                          # …puis ducking -7 dB quand la voix parle
    e = e / (np.percentile(e[e > 0], 95) + 1e-9)
    duck = np.clip(e / 0.25, 0, 1)
    g_db = -7 * env_follow(duck, 0.03, 0.45)                 # retour lent : pas de pompage entre les mots
    g = np.repeat(10 ** (g_db / 20), hop)
    g = np.pad(g, (0, N - len(g)), mode="edge")
    mu = mu * g[:, None]
    sfx = bus * (10 ** ((20 * np.log10(np.abs(vo).max()) - 10 - 20 * np.log10(np.abs(bus).max() + 1e-9)) / 20))
    mix = np.stack([vo, vo], 1) + mu + sfx
    mix *= 0.9 / (np.abs(mix).max() + 1e-9)
    sf.write(os.path.join(OUT, "mix_raw.wav"), mix.astype(np.float32), SR)
    # rapport : niveau de la musique pendant la parole
    mono_mu = mu.mean(1)
    gaps = ~speech
    print("voix pendant la parole : %.1f dB RMS" % rms_db(vo[speech]))
    print("musique pendant la parole : %.1f dB RMS (%.1f dB sous la voix)" % (rms_db(mono_mu[speech]), v_db - rms_db(mono_mu[speech])))
    print("musique hors parole : %.1f dB RMS (%.1f dB sous la voix)" % (rms_db(mono_mu[gaps]), v_db - rms_db(mono_mu[gaps])))
    win = int(0.4 * SR)                                       # fenêtres de 0,4 s parlées (les fins de phrase en souffle comptent)
    diffs = [rms_db(vo[i:i + win]) - rms_db(mono_mu[i:i + win]) for i in range(0, N - win, win) if speech[i:i + win].mean() > 0.8]
    print("écart voix/musique sur fenêtres de 0,4 s parlées : médiane %.1f dB, 10e centile %.1f dB" % (np.median(diffs), np.percentile(diffs, 10)))
    # loudness finale : deux passes loudnorm vers -16 LUFS / -1,5 dBTP
    src, dst = os.path.join(OUT, "mix_raw.wav"), os.path.join(OUT, "mix.wav")
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", "loudnorm=I=-16:TP=-2:LRA=11:print_format=json",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af",
                    "loudnorm=I=-16:TP=-2:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:offset=%s:linear=true"
                    % (m["input_i"], m["input_tp"], m["input_lra"], m["input_thresh"], m["target_offset"]), "-ar", str(SR), dst], check=True)
    print("->", dst)


if __name__ == "__main__":
    main()
