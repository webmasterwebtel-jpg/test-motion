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


def pen(t0, d, gain=0.22, pan=0.1):
    """Plume sur l'écran : souffle filtré, modulé par les gestes (signature dessinée)."""
    n = noise(d)
    x = bp(n, 2500, 7000)
    t = tv(d)
    am = (0.55 + 0.45 * np.abs(np.sin(2 * np.pi * 2.6 * t + 1.3 * np.sin(2 * np.pi * 0.9 * t)))) * np.minimum(1, t / 0.06) * np.minimum(1, (d - t) / 0.12)
    add(x * am * 0.18, t0, gain, pan)


def cues():
    """Bruitages V5 : les instants viennent de build/mywebtel/cues.json, exporté par le film lui-même (render.js).
    Sobres : un geste = un son, rien sur les mots seuls ; la voix reste au premier plan."""
    C = json.load(open(os.path.join(OUT, "cues.json")))
    T = C["T"]
    # 1. ouverture (nuit) : une démarche = un petit « pop », l'heure qui file, la question, la montée vers le logo
    for k, t in enumerate(C["tasks"]):
        add(pop(480, 760, 0.45), t, 0.8, (-0.5, 0.5, -0.4, 0.4)[k])
    roll(T["boulot"], 1.4, 0.22)
    add(swoosh(0.5, 1800, 500, 0.12), T["fou"] - 0.05, 1, 0)
    keys(T["ques"], T["endroit"] + 0.45, 18, 0.3, 0)
    add(swoosh(1.4, 1800, 400, 0.14), T["endroit"] + 0.2)               # les démarches convergent
    add(air(1.8, 0.2), T["logo"] - 1.8)
    # 2. logo, puis la fenêtre qui monte
    add(thump(0.55), T["logo"])
    add(chime((1174.7, 1760.0), 0.12, 1.6), T["logo"] + 0.05)
    add(swoosh(0.6, 2200, 700, 0.12), T["tag"] - 0.1)
    add(swoosh(1.2, 300, 1600, 0.24), T["winIn"])
    # 3. tous les clics, et un trait de lumière à chaque changement d'écran
    for t in C["clicks"]:
        add(tap(), t - 0.02, 0.85, 0.15)
    for t in C["nav"]:
        add(swoosh(0.55, 600, 2600, 0.1), t - 0.2, 1, -0.2)
    # badges ✓ : une note douce, toujours la même (signature sonore)
    for t in C["checks"]:
        add(chime((1568.0, 2349.3), 0.06, 0.8), t + 0.02, 1, 0.25)
    # 4. pointage : chaque état confirmé, l'heure qui défile
    for t in (T["in"], T["pause"], T["ret"], T["out"]):
        add(pop(700, 1000, 0.2), t + 0.06, 1, 0.1)
        roll(t - 0.05, 0.4, 0.2)
    # 5. congés
    add(pop(700, 960, 0.12), T["solde"] - 0.1, 1, 0.2)
    add(pop(650, 900, 0.12), T["rights"] - 0.15, 1, 0.3)
    # 6. absences : dates, justificatif, envoi, vérification RH
    add(tick(), T["declare"] + 0.1, 0.6); add(tick(), T["declare"] + 0.35, 0.6)
    add(pop(500, 750, 0.3), T["proof"] + 0.15, 0.8, -0.2)
    add(pop(560, 900, 0.25), T["absSend"] + 0.25, 1, 0.4)
    add(pop(700, 1000, 0.16), T["rh"], 1, 0.4)
    # 7. signature : « Imprimer, signer, scanner » puis « Sauf que non. »
    add(air(0.9, 0.12), T["kImp"] - 0.8)
    for t in (T["kImp"], T["kSig"], T["kScan"]):
        add(pop(420, 600, 0.22), t - 0.1, 0.8, 0)
    add(swoosh(0.45, 900, 3600, 0.18), T["non"] + 0.12, 1, 0)           # le trait qui barre
    add(swoosh(0.9, 2400, 500, 0.16), T["back"], 1, 0)                  # retour à l'écran
    add(pop(640, 940, 0.2), T["open"] + 0.12, 1, 0.1)                   # la fenêtre de signature s'ouvre
    add(pop(800, 1150, 0.12), T["nom"] - 0.15, 1, 0.2)
    pen(T["draw"] + 0.15, T["code"] - 0.5 - T["draw"])
    add(ping(), T["mail"] - 0.1, 0.8, 0.5)                              # l'e-mail du code arrive
    keys(T["tape"] - 0.1, T["tape"] + 0.4, 6, 0.4, 0.1)
    add(tick(), T["tape"] + 0.55, 0.7, 0.2)                             # case de consentement
    add(chime((1318.5, 1975.5, 2637.0), 0.1, 1.6), T["signed"] + 0.3, 1, 0.1)
    # 8. demandes RH : frappe, envoi, suivi
    keys(T["fill"], T["fill"] + 0.35, 8, 0.4, -0.2)
    keys(T["fill"] + 0.4, T["clics"] - 0.15, 12, 0.4, -0.2)
    add(pop(560, 900, 0.25), T["clics"] + 0.2, 1, 0.4)
    add(pop(700, 1000, 0.16), T["process"], 1, 0.4)
    # 9. contenu : case cochée, lecture confirmée
    add(tick(), T["confirm"] + 0.02, 0.7, 0.2)
    # 10. mail : frappe et envoi
    keys(C["nav"][6] + 0.5, T["mailSend"] - 0.15, 22, 0.36, 0.2)
    add(swoosh(0.35, 900, 3000, 0.12), T["mailSend"] + 0.05, 1, 0.3)
    add(pop(600, 880, 0.2), T["mailSend"] + 0.15, 1, 0.3)
    # 11. support informatique : frappe, ticket envoyé, pris en charge
    keys(C["nav"][7] + 0.35, T["ticket"] - 0.2, 20, 0.36, -0.2)
    add(pop(560, 900, 0.25), T["ticket"] + 0.15, 1, 0.4)
    add(pop(700, 1000, 0.16), T["charge"], 1, 0.4)
    # 12. agent : le panneau s'ouvre, la question, la réponse, la demande préparée, la confirmation
    add(swoosh(0.5, 500, 2200, 0.14), T["launch"] + 0.05, 1, 0.3)
    keys(T["ask"], T["askSend"] - 0.15, 26, 0.34, 0.3)
    add(swoosh(0.3, 1000, 3200, 0.1), T["askSend"] + 0.05, 1, 0.3)
    for k, t in enumerate(T["chips"]):
        add(pop(760 + 80 * k, 1040 + 80 * k, 0.1), t - 0.05, 1, 0.3)
    add(pop(620, 900, 0.14), T["answer"], 1, 0.3)
    add(pop(560, 860, 0.22), T["prep"] + 0.02, 1, 0.3)
    add(chime((1318.5, 1760.0), 0.09, 1.0), T["okAgent"] + 0.1, 1, 0.3)
    # 13. fin
    add(air(1.4, 0.16), T["end"])
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
