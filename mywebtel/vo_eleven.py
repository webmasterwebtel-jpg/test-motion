#!/usr/bin/env python3
"""Voix off V5 (ElevenLabs, voix « Simon ») : placement des segments sur la grille et mots datés.

Les segments viennent de voice/eleven_gen.py (build/mywebtel/voice/<id>.mp3 + <id>.json, horodatage par caractère).
Ici on les rogne, on les place scène par scène sur la grille des temps (100 BPM), avec une respiration après chaque
fonction pour laisser le temps de voir le résultat, et on écrit le même timeline.json que vo.py : le film, la musique
et les bruitages le lisent sans changement. Les mots sont datés par l'horodatage d'ElevenLabs (au caractère près).

Sorties (build/mywebtel/) : vo.wav (48 kHz mono) et timeline.json.
Usage : python3 mywebtel/vo_eleven.py
"""
import json, math, os, re, subprocess, sys
import numpy as np
import soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "build", "mywebtel")
VOICE = os.path.join(OUT, "voice")
SR = 48000
BPM, BEAT = 100, 0.6
TAIL = 3.6
# graphies forcées pour la prononciation -> mot affiché et cherché par le film
SHOWN = {"scanné": "scanner", "plu": "plus"}

# (scène, [segments], attente avant la parole, [silence après chaque segment], calage "bar" du 1er segment)
SCENES = [
    ("hook", ["hook", "hook2"], 1.2, [0.7, 0.9], None),
    ("reveal", ["reveal"], 0.2, [1.1], "bar"),
    ("pointage", ["pointage"], 0.9, [1.3], None),
    ("conges", ["conges"], 0.9, [1.3], None),
    ("absences", ["absences"], 0.9, [1.4], None),
    ("signature", ["signature"], 0.9, [1.5], None),
    ("demandes", ["demandes"], 0.9, [1.3], None),
    ("contenu", ["contenu"], 0.9, [1.3], None),
    ("mail", ["mail"], 0.9, [1.4], None),
    ("agent", ["agent"], 1.0, [1.2], None),
    ("fin", ["fin"], 0.0, [0.6], "bar"),
]


def load(sid):
    wav = os.path.join(VOICE, sid + ".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(VOICE, sid + ".mp3"), "-ac", "1", "-ar", str(SR), wav], check=True)
    a, _ = sf.read(wav)
    al = json.load(open(os.path.join(VOICE, sid + ".json"), encoding="utf-8"))
    return a, al


def trim(a, floor_db=-50, margin=0.04):
    """Rogne le silence de début et de fin ; renvoie aussi le décalage de début (pour l'horodatage)."""
    hop = int(0.005 * SR)
    fr = a[:len(a) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    on = np.nonzero(db > db.max() + floor_db)[0]
    i0 = max(0, on[0] * hop - int(margin * SR))
    i1 = min(len(a), (on[-1] + 1) * hop + int(margin * SR))
    out = a[i0:i1].copy()
    f = int(0.006 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out, i0 / SR


def words_of(al):
    """Mots et instant de leur première lettre, depuis l'horodatage par caractère."""
    chars, t0 = al["characters"], al["character_start_times_seconds"]
    words, cur, start = [], "", None
    for c, t in zip(chars, t0):
        if re.match(r"[\wÀ-ÿ'’-]", c):
            if not cur:
                start = t
            cur += c
        else:
            if cur:
                words.append([cur, start])
            cur = ""
    if cur:
        words.append([cur, start])
    out = []
    for w, t in words:                     # « l'agent » -> « l'agent » ; « t'as » reste entier ; affichage normalisé
        out.append([SHOWN.get(w.lower(), w), t])
    return out


def main():
    rows = {r[0]: r for r in json.load(open(os.path.join(HERE, "voice", "script_v5.json"), encoding="utf-8"))}
    t, scenes, clips, nwords, speech = 0.0, [], [], 0, 0.0
    for sid, segs, lead, gaps, snap in SCENES:
        start = math.ceil(t / BEAT - 1e-6) * BEAT
        cur = start + lead
        items = []
        for k, seg_id in enumerate(segs):
            if k == 0 and snap:
                unit = BEAT * (4 if snap == "bar" else 1)
                cur = math.ceil(cur / unit - 1e-6) * unit
            a, al = load(seg_id)
            a, off = trim(a)
            ws = [[w, round(cur + max(0.0, x - off), 3)] for w, x in words_of(al)]
            items.append(dict(text=rows[seg_id][1], start=round(cur, 3), end=round(cur + len(a) / SR, 3), words=ws))
            clips.append((cur, a))
            nwords += len(ws)
            speech += len(a) / SR
            cur += len(a) / SR + gaps[k]
        scenes.append(dict(id=sid, start=round(start, 3), segs=items))
        t = cur
    end_speech = scenes[-1]["segs"][-1]["end"]
    bar = 4 * BEAT
    total = math.ceil((end_speech + TAIL) / bar) * bar
    for i, sc in enumerate(scenes):
        sc["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else round(total, 3)
    track = np.zeros(int(total * SR) + 1)
    for t0, a in clips:
        i0 = int(round(t0 * SR))
        track[i0:i0 + len(a)] += a
    track = signal.sosfilt(signal.butter(2, 70, "high", fs=SR, output="sos"), track)   # la voix est déjà mastérisée
    track *= 10 ** (-3 / 20) / (np.abs(track).max() + 1e-9)
    sf.write(os.path.join(OUT, "vo.wav"), track.astype(np.float32), SR)
    tl = dict(bpm=BPM, beat=BEAT, fps=30, duration=round(total, 3), engine="elevenlabs:simon", scenes=scenes)
    json.dump(tl, open(os.path.join(OUT, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    span = end_speech - scenes[0]["segs"][0]["start"]
    print("durée %.1f s (%d mesures) · parole %.1f s · %d mots · %.0f mots/min sur la durée parlée"
          % (total, round(total / bar), speech, nwords, nwords / span * 60))
    for sc in scenes:
        print("  %-10s %6.2f → %6.2f s  première parole %6.2f" % (sc["id"], sc["start"], sc["end"], sc["segs"][0]["start"]))


if __name__ == "__main__":
    main()
