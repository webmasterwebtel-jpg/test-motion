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
import audio_fx as FX
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
revbus = np.zeros((N, 2))                  # envoi vers la réverbération (espace commun à tous les bruitages)


def add(x, t0, gain=1.0, pan=0.0, rev=0.25):
    i0 = int(round(t0 * SR))
    if i0 >= N:
        return
    if i0 < 0:
        x, i0 = x[-i0:], 0
    l, r = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
    n = min(len(x), N - i0)
    for c, g in ((0, l), (1, r)):
        bus[i0:i0 + n, c] += x[:n] * g * gain * math.sqrt(2)
        revbus[i0:i0 + n, c] += x[:n] * g * gain * math.sqrt(2) * rev


def keys(t0, t1, n, gain=0.45, pan=0.0):
    """Frappe au clavier : n déclics irréguliers entre t0 et t1."""
    r = np.random.default_rng(int(t0 * 100))
    for k in range(n):
        add(tick(), t0 + (t1 - t0) * (k + r.uniform(-0.3, 0.3)) / max(n, 1), gain * r.uniform(0.7, 1.0), pan + r.uniform(-0.1, 0.1))


def roll(t0, d=0.7, gain=0.35):
    """Défilement rapide de l'heure : petits déclics qui ralentissent."""
    for k in range(10):
        add(tick(), t0 + d * (1 - (1 - k / 10) ** 2), gain)


def pen(t0, d, gain=0.22, pan=0.1):
    """Plume sur l'écran : souffle filtré, modulé par les gestes (signature dessinée)."""
    n = noise(d)
    x = bp(n, 2500, 7000)
    t = tv(d)
    am = (0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 2.6 * t + 1.3 * np.sin(2 * np.pi * 0.9 * t)))) * np.minimum(1, t / 0.06) * np.minimum(1, (d - t) / 0.12)
    add(x * am * 0.18, t0, gain, pan)


def hit(level=0.35):
    """Frappe courte qui accompagne un mot qui claque : grave bref + claquement filtré."""
    t = tv(0.25)
    f = 70 + 90 * np.exp(-t / 0.02)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.07) + bp(noise(0.25), 1500, 6000) * np.exp(-t / 0.012) * 0.5) * level


def touch():
    """Toucher d'écran : petit « tic » de verre."""
    t = tv(0.05)
    return (np.sin(2 * np.pi * 2300 * t) * np.exp(-t / 0.008) * 0.5 + hp(noise(0.05), 4000) * np.exp(-t / 0.003) * 0.4)


def cues():
    """Bruitages V8 : instants exportés par le film (cues.json). Souffle doux à l'arrivée de chaque appareil, touchers, clics,
    effets propres à chaque fonction. La musique porte les drops ; les bruitages ponctuent."""
    C = json.load(open(os.path.join(OUT, "cues.json")))
    T = C["T"]
    for k, t in enumerate(C.get("moves", [])):                     # un appareil arrive : souffle doux, sans impact
        add(swoosh(0.9, 420, 2600, 0.15), t + 0.05, 1, 0.25 * (-1) ** k, rev=0.45)
    touches = set(round(x, 3) for x in C.get("touches", []))
    for t in C["clicks"]:
        add(touch() if round(t, 3) in touches else tap(), t - 0.02, 0.9, 0.1, rev=0.1)
    for t in C.get("checks", []):
        add(chime((1568.0, 2349.3), 0.06, 0.9), t + 0.02, 1, 0.25, rev=0.5)
    # pointage
    for t in (T["in"], T["pause"], T["ret"], T["out"]):
        add(pop(700, 1000, 0.17), t + 0.06, 1, 0.1)
        roll(t - 0.05, 0.35, 0.14)
    # congés : compteur, frise, cadenas
    for k in range(1, 25):
        sk = 1 - (1 - k / 24) ** (1 / 3)
        add(tick(), T["solde"] - 0.25 + sk * 1.0, 0.45, 0.2, rev=0.1)
    add(FX.beam(380, 900, max(0.4, T["seniority"] - T["rights"]), 0.12), T["rights"] + 0.1, 1, 0, rev=0.3)
    add(pop(900, 1300, 0.18), T["seniority"] + 0.1, 1, 0.1, rev=0.4)
    # absences
    add(tick(), T["declare"] + 0.1, 0.6); add(tick(), T["declare"] + 0.35, 0.6)
    add(swoosh(max(0.4, T["fileIn"] - T["proof"] + 0.25), 1600, 500, 0.18), T["proof"] - 0.25, 1, -0.4, rev=0.3)
    add(FX.paper(0.32), T["fileIn"] - 0.02, 1, 0.1, rev=0.3)
    add(pop(700, 1000, 0.15), T["rh"], 1, 0.3)
    # signature
    add(FX.printer(0.8, 0.22), T["kImp"] - 0.45, 1, 0.3, rev=0.3)
    pen(T["kSig"] - 0.1, 0.6, 0.2, 0.3)
    add(FX.scan(0.7, 0.16), T["kScan"] - 0.1, 1, 0.3, rev=0.3)
    add(swoosh(0.7, 2600, 500, 0.14), T["nonEnd"] - 0.25, 1, 0, rev=0.5)     # la feuille s'efface, sans fracas
    add(pop(640, 940, 0.18), T["open"] + 0.12, 1, 0.1, rev=0.3)
    pen(T["draw"] + 0.15, max(0.4, T["drawEnd"] - T["draw"] - 0.15), 0.24, 0.1)
    add(swoosh(0.45, 2400, 700, 0.12), T["code"] - 0.15, 1, 0.6, rev=0.3)          # le téléphone arrive
    add(chime((1318.5, 1760.0), 0.12, 0.8), T["mail"] - 0.08, 1, 0.6, rev=0.4)      # notification
    keys(T["tape"] - 0.1, T["tape"] + 0.45, 6, 0.4, 0.1)
    add(tick(), T["consent"], 0.7, 0.2)
    add(chime((1318.5, 1975.5, 2637.0), 0.10, 1.6), T["signed"] + 0.3, 1, 0.1, rev=0.6)
    add(FX.shimmer(0.8, 0.07, seed=31), T["signed"] + 0.5, 1, 0.2, rev=0.6)
    # demandes, contenu, mail, support
    keys(T["fill"], T["fill"] + 0.35, 8, 0.4, -0.2)
    keys(T["fill"] + 0.38, T["clics"] - 0.12, 12, 0.4, -0.2)
    add(pop(700, 1000, 0.15), T["process"], 1, 0.4)
    add(tick(), T["confirm"] + 0.02, 0.7, 0.2)
    keys(T["mailType"], T["mailSend"] - 0.15, 20, 0.36, 0.2)
    add(swoosh(0.35, 900, 3000, 0.12), T["mailSend"] + 0.05, 1, 0.3)
    keys(T["tickType"], T["ticket"] - 0.2, 18, 0.36, -0.2)
    add(pop(560, 900, 0.2), T["ticket"] + 0.15, 1, 0.4)
    add(pop(700, 1000, 0.15), T["charge"], 1, 0.4)
    # agent
    add(FX.shimmer(1.6, 0.12, seed=41, lo=1500, hi=4800), T["q"] - 0.45, 1, -0.3, rev=0.75)
    keys(T["ask"], T["askSend"] - 0.15, 24, 0.32, 0.1)
    for k, t in enumerate(T["chips"]):
        add(FX.beam(520 * 1.12 ** k, 1560 * 1.12 ** k, 0.5, 0.16), t - 0.1, 1, (-0.4, 0.4, 0.4)[k], rev=0.5)
    add(FX.shimmer(1.0, 0.06, seed=43), T["answer"] + 0.3, 1, 0.1, rev=0.5)
    add(pop(560, 860, 0.2), T["prep"] + 0.02, 1, 0.1, rev=0.35)
    add(chime((1318.5, 1760.0), 0.09, 1.1), T["okAgent"] + 0.1, 1, 0.1, rev=0.5)


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
    global bus
    cues()
    bus = bus + (FX.reverb(revbus, t60=2.4, wet=1.0, hpf=200) - revbus)
    sf.write(os.path.join(OUT, "sfx.wav"), bus.astype(np.float32), SR)
    vo, _ = sf.read(os.path.join(OUT, "vo.wav"))
    vo = np.pad(vo, (0, max(0, N - len(vo))))[:N]
    mu, _ = sf.read(os.path.join(OUT, "music.wav"), always_2d=True)
    mu = np.pad(mu, ((0, max(0, N - len(mu))), (0, 0)))[:N]
    # V7 : la musique gère elle-même ses coupures (« Sauf que non ») et ses montées (music7.py)
    # zones de parole
    speech = np.zeros(N, bool)
    for s in TL["scenes"]:
        for g in s["segs"]:
            speech[int(g["start"] * SR):int(g["end"] * SR)] = True
    v_db = rms_db(vo[speech])
    m_db = rms_db(mu.mean(1))
    # Niveaux de la musique (retour du 2026-11-11 : « la musique est trop faible, on entend presque rien » ; la V8 la
    # laissait ~11 dB sous la voix). Demande d'origine : « pas plus forte que la voix, juste un peu forte ».
    MUSIC_DB, DUCK_DB, GAP_DB = -1.0, -3.0, 4.0              # niveau de base / baisse sous la parole / écart minimal garanti
    mu *= 10 ** ((v_db + MUSIC_DB - m_db) / 20)              # musique presque au niveau de la voix entre les phrases…
    hop = 480
    lvl = np.abs(vo[: N // hop * hop]).reshape(-1, hop).max(1)
    e = env_follow(lvl, 0.004, 0.25)                          # …puis ducking -7 dB quand la voix parle
    e = e / (np.percentile(e[e > 0], 95) + 1e-9)
    duck = np.clip(e / 0.25, 0, 1)
    g_db = DUCK_DB * env_follow(duck, 0.03, 0.35)            # …baissée quand la voix parle (retour assez vif entre les phrases)
    g = np.repeat(10 ** (g_db / 20), hop)
    g = np.pad(g, (0, N - len(g)), mode="edge")
    mu = mu * g[:, None]
    # limiteur commandé par la voix : pendant la parole, la musique reste au moins GAP_DB sous la voix, instant par instant
    hop2 = 960                                                # trames de 20 ms (50 par seconde)
    nf = N // hop2
    ve = np.sqrt(np.mean(vo[: nf * hop2].reshape(nf, hop2) ** 2, 1)) + 1e-9
    me = np.sqrt(np.mean(mu.mean(1)[: nf * hop2].reshape(nf, hop2) ** 2, 1)) + 1e-9
    def follow(x, up, down, fs=50.0):                         # suiveur d'enveloppe à la cadence des trames
        au, ad = math.exp(-1 / (up * fs)), math.exp(-1 / (down * fs))
        out = np.empty_like(x); e = x[0]
        for i, v in enumerate(x):
            e = au * e + (1 - au) * v if v > e else ad * e + (1 - ad) * v
            out[i] = e
        return out
    ve = follow(ve, 0.01, 0.18)                                # la voix « tient » ~180 ms après chaque mot : la musique suit les fins de phrase
    sp2 = speech[: nf * hop2].reshape(nf, hop2).mean(1) > 0.2
    need = np.where(sp2 & (ve > 10 ** ((v_db - 40) / 20)), np.minimum(1.0, ve * 10 ** (-GAP_DB / 20) / me), 1.0)
    gl = follow(need, 0.25, 0.01)                              # le gain descend tout de suite, remonte en douceur
    gl = np.repeat(gl, hop2); gl = np.pad(gl, (0, N - len(gl)), mode="edge")
    mu = mu * gl[:, None]
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
    wins = [(i / SR, rms_db(vo[i:i + win]) - rms_db(mono_mu[i:i + win])) for i in range(0, N - win, win)
            if speech[i:i + win].mean() > 0.8 and rms_db(vo[i:i + win]) > v_db - 12]           # fenêtres où la voix parle vraiment
    diffs = [d for _, d in wins]
    print("fenêtres les plus serrées :", ", ".join("%.1f s (%.1f dB)" % w for w in sorted(wins, key=lambda w: w[1])[:5]))
    print("écart voix/musique sur fenêtres de 0,4 s parlées : médiane %.1f dB, 10e centile %.1f dB, minimum %.1f dB" % (np.median(diffs), np.percentile(diffs, 10), np.min(diffs)))
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
