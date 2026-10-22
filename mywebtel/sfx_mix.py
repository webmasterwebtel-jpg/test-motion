#!/usr/bin/env python3
"""Bruitages d'interface discrets + mixage final MyWebtel (voix, musique avec ducking, bruitages).

Les instants des bruitages reprennent les formules de film/film.js (mêmes repères de timeline.json), pour que chaque son
tombe sur son geste à l'image. Les sons sont synthétisés, courts et feutrés : présence, jamais démonstration.

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


def cues():
    # 1. ouverture
    for k, pan in enumerate((-0.5, 0.5, -0.4, 0.4)):
        add(pop(480, 760, 0.45), segT("hook", k) - 0.12, 0.8, pan)
    for k in range(10):
        add(tick(), segT("hook", 4) + k * 0.16, 0.5, (k % 5 - 2) / 3)
    add(air(2.4, 0.22), 11.7)
    # 2. logo
    logo = segT("reveal", 1)
    add(air(1.4, 0.18), logo - 1.4)
    add(thump(0.55), logo)
    add(chime((1174.7, 1760.0), 0.12, 1.6), logo + 0.05)
    # 3. vision
    v0 = S0("vision")
    add(swoosh(0.9, 300, 1800, 0.28), v0 - 0.4)
    for k, w in enumerate(["collaborateurs", "horaires", "congés", "documents", "annonces", "devis"]):
        add(pop(560, 900, 0.35), wordT("vision", 0, w) - 0.1, 0.8, -0.5 if k < 3 else 0.5)
    add(swoosh(0.8, 2500, 600, 0.25), segT("vision", 1))
    add(chime((1318.5, 1760.0), 0.1, 1.0), segT("vision", 1) + 0.75)
    # 4. rôles (zoom de sortie de l'ordinateur)
    add(swoosh(0.8, 400, 2200, 0.2), S0("roles") - 0.55)
    for k in range(5):
        add(swoosh(0.35, 800, 3000, 0.12), segT("roles", 0) + 0.05 + k * 0.09, 1, (k - 2) / 2.5)
    for k, w in enumerate(["salarié", "manager", "rh", "direction", "administrateur"]):
        add(tick(), wordT("roles", 1, w) + 0.25, 0.8, (k - 2) / 2.5)
    for k in range(5):
        add(pop(700, 1000, 0.18), segT("roles", 2) - 0.1 + k * 0.12, 1, (k - 2) / 2.5)
    # 5. pointage
    add(swoosh(0.7, 300, 1500, 0.22), S0("pointage") + 0.05)
    for k in range(4):
        add(tap(), partT("pointage", 1, k) - 0.08, 0.9, -0.3)
    add(ping(), wordT("pointage", 2, "les RH") - 0.1, 1, 0.4)
    for k in range(3):
        add(pop(600, 820, 0.25), segT("pointage", 3) + 0.15 + k * 0.35, 1, 0.4)
    # 6. congés
    c0 = S0("conges")
    add(swoosh(0.7, 300, 1500, 0.22), c0 + 0.05)
    td = wordT("conges", 1, "dates") - 0.2
    for k in range(4):
        add(tick(), td + k * 0.12, 0.9, -0.3)
    tm = wordT("conges", 1, "motif") - 0.1
    for k in range(6):
        add(tick(), tm + k * 0.1, 0.5, 0.2)
    add(pop(500, 750, 0.35), wordT("conges", 1, "justificatif") - 0.05, 0.8, 0.2)
    flowT = segT("conges", 2) - 0.25
    add(tap(), flowT - 0.35, 0.9, 0.2)
    for k in range(3):
        add(chime((1318.5 * 2 ** (k / 12 * 2), 1975.5 * 2 ** (k / 12 * 2)), 0.09, 0.9), flowT + 0.5 + k * 0.85, 1, 0.4)
    add(pop(700, 520, 0.25), segT("conges", 3) + 0.6, 1, 0.4)
    # 7. documents
    add(swoosh(0.7, 300, 1500, 0.2), S0("documents") + 0.05)
    tp, tdl, tc = (partT("documents", 1, k) for k in range(3))
    add(swoosh(0.5, 600, 2400, 0.2), tp - 0.15, 1, 0.4)
    add(tap(), tdl - 0.05, 0.9, 0.4)
    add(pop(800, 1100, 0.25), tdl + 0.7, 1, 0.4)
    for k in range(7):
        add(tick(), tc + 0.2 + k * 0.1, 0.45, -0.3)
    # 8. annonces
    add(swoosh(0.7, 300, 1500, 0.2), segT("annonces", 0) - 0.3)
    tcl = wordT("annonces", 1, "clic") - 0.05
    add(tap(), tcl, 1.0, -0.2)
    add(chime((1568.0, 2093.0), 0.1, 1.0), tcl + 0.05, 1, -0.2)
    # 9. devis
    send = wordT("devis", 0, "arrive") - 0.6
    add(tap(), send, 0.9, -0.5)
    add(swoosh(1.0, 500, 2800, 0.28), send + 0.05, 1, 0.0)
    add(pop(520, 820, 0.4), send + 1.0, 1, 0.5)
    for k in (1, 2, 3):
        add(tick(), segT("devis", k), 1.0, 0.4)
    add(chime((1318.5, 1975.5), 0.1, 1.0), segT("devis", 3) + 0.05, 1, 0.4)
    # 10. réglages
    add(swoosh(0.9, 300, 1500, 0.2), S0("reglages") - 0.4)
    k0 = segT("reglages", 1) + 0.45
    for k in range(3):
        add(tap(), k0 + k * 0.85, 0.8, 0.3)
    sess = segT("reglages", 2) - 0.2
    add(swoosh(0.9, 2000, 400, 0.18), sess)
    add(thump(0.35), sess + 2.65)
    add(tap(), sess + 2.65, 0.9)
    # 11. partout
    for w, pan in (("ordinateur", 0.0), ("tablette", -0.6), ("smartphone", 0.6)):
        tw = wordT("partout", 0, w) - 0.25
        add(swoosh(0.6, 400, 2000, 0.2), min(tw, S0("partout") + 0.05) if w == "ordinateur" else tw, 1, pan)
    # 12. signature
    logo2 = segT("signature", 0)
    add(air(1.6, 0.16), logo2 - 1.6)
    add(thump(0.5), logo2)
    add(chime((1174.7, 1760.0), 0.12, 1.8), logo2 + 0.05)


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
