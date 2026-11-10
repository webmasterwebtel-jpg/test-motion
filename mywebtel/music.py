#!/usr/bin/env python3
"""Musique de fond MyWebtel (V6) : composée en MIDI, rendue piste par piste avec FluidSynth (banque libre MuseScore General),
plus une nappe grave synthétisée pour la nuit et une réverbération de salle commune (audio_fx.py).

100 BPM, une mesure = 2,4 s, ré majeur, un accord par mesure. L'arrangement suit les scènes de build/mywebtel/timeline.json
(voir setup) : intro au piano seul sur la nuit, accord lumineux sur le logo, groove discret qui s'étoffe au fil des
fonctions, montée, logo final et résolution.

Sorties : build/mywebtel/music/<piste>.wav (48 kHz stéréo) et build/mywebtel/music.wav (mixage des pistes, sans ducking).
Usage : python3 mywebtel/music.py
"""
import json, os, random, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_fx as FX
import numpy as np
import soundfile as sf
import mido
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "mywebtel")
SF2 = "/usr/share/sounds/sf3/MuseScore_General_Full.sf3"
SR = 48000
TPB = 480                      # ticks par temps
BPM = 100
BEAT = 60.0 / BPM
BAR = 4 * BEAT
rnd = random.Random(12)

# accords (fondamentale MIDI de la basse, notes du voicing de piano) — ré majeur
CH = {
    "D":     (38, [62, 66, 69, 73, 76]),     # Dmaj9 : D F# A C# E
    "D/F#":  (42, [62, 66, 69, 74, 76]),
    "Bm7":   (35, [62, 66, 69, 71, 74]),     # B D F# A
    "Gmaj7": (43, [62, 66, 67, 71, 74]),     # G B D F#
    "Gmaj9": (43, [62, 66, 69, 71, 74]),
    "Em9":   (40, [62, 66, 67, 71, 74]),
    "Asus":  (45, [62, 64, 69, 71, 76]),     # A D E (sus4)
    "A":     (45, [61, 64, 69, 71, 76]),
}
LOOP = ["Gmaj7", "D/F#", "Bm7", "Asus"]
PLAN, SECTION = {}, {}                       # mesure (1..N) -> accord, section ; calculés depuis la timeline
NBARS = 0


def setup(tl):
    """Arrangement V6, calé sur les mots de la voix : nuit (intro) -> logo -> groove dans le monde MyWebtel (A, A+) ->
    piano seul sur « imprimer, signer, scanner » (breath) -> groove plein (B) -> section de l'agent (agent) -> montée -> fin."""
    global NBARS
    NBARS = int(round(tl["duration"] / BAR))
    sc = {s["id"]: s for s in tl["scenes"]}
    fold = lambda w: w.lower().replace("é", "e").replace("’", "'")
    def W(sid, word, n=0):
        ws = [w for g in sc[sid]["segs"] for w in g["words"] if fold(w[0]) == fold(word)]
        return ws[n][1]
    bar_of = lambda t: int(t // BAR) + 1
    logo = int(round((W("reveal", "MyWebtel") - 0.35) / BAR)) + 1          # même calcul que le film (onBar)
    final = int(round((W("fin", "MyWebtel") - 0.4) / BAR)) + 1
    breath0, breath1 = bar_of(W("signature", "l'imprimer") - 0.6), bar_of(W("signature", "non") + 0.4)
    a_plus, agent0 = bar_of(sc["conges"]["start"]), bar_of(sc["agent"]["start"] + 0.5) + 1
    intro = ["Bm7", "Gmaj7", "Bm7", "Em9", "Gmaj7", "Asus"]
    k = 0
    for b in range(1, NBARS + 1):
        if b < logo:
            PLAN[b], SECTION[b] = intro[(b - 1) % len(intro)] if b < logo - 1 else "Asus", "intro" if b < logo - 1 else "question"
        elif b == logo:
            PLAN[b], SECTION[b] = "D", "logo"
        elif breath0 <= b <= breath1:
            PLAN[b], SECTION[b] = ["Em9", "Gmaj7", "Asus", "Asus"][min(b - breath0, 3)], "breath"
        elif b < final - 1 and b >= agent0:
            PLAN[b], SECTION[b] = ["Gmaj9", "D/F#", "Em9", "Asus"][(b - agent0) % 4], "agent"
        elif b < final - 1:
            PLAN[b] = LOOP[k % 4]; k += 1
            SECTION[b] = "A" if b < a_plus else ("A+" if b < breath0 else "B")
        elif b == final - 1:
            PLAN[b], SECTION[b] = "Asus", "lift"
        else:
            PLAN[b], SECTION[b] = ["D", "Gmaj9", "D"][min(b - final, 2)], "end"
    return logo, final


def section(b):
    return SECTION[b]


class Track:
    def __init__(self, program, channel=0):
        self.ev = []                 # (tick, msg)
        self.program, self.channel = program, channel

    def note(self, beat, dur, pitch, vel):
        t0 = int(round((beat + rnd.uniform(-0.012, 0.012)) * TPB))       # micro-décalage humain
        t1 = int(round((beat + dur) * TPB))
        v = max(1, min(127, int(vel + rnd.uniform(-5, 5))))
        self.ev.append((max(t0, 0), mido.Message("note_on", note=pitch, velocity=v, channel=self.channel)))
        self.ev.append((max(t1, t0 + 1), mido.Message("note_off", note=pitch, velocity=0, channel=self.channel)))

    def cc(self, beat, ctrl, val):
        self.ev.append((int(beat * TPB), mido.Message("control_change", control=ctrl, value=val, channel=self.channel)))

    def save(self, path):
        mid = mido.MidiFile(ticks_per_beat=TPB)
        tr = mido.MidiTrack()
        mid.tracks.append(tr)
        tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(BPM), time=0))
        if self.channel != 9:
            tr.append(mido.Message("program_change", program=self.program, channel=self.channel, time=0))
        tr.append(mido.Message("control_change", control=91, value=70, channel=self.channel, time=0))   # réverbe
        tr.append(mido.Message("control_change", control=93, value=20, channel=self.channel, time=0))   # chorus
        last = 0
        for t, m in sorted(self.ev, key=lambda e: (e[0], e[1].type == "note_on")):
            tr.append(m.copy(time=t - last))
            last = t
        mid.save(path)


def compose():
    piano, pad, strings, bass, bell, drums = Track(0, 0), Track(89, 1), Track(49, 2), Track(33, 3), Track(8, 4), Track(0, 9)
    motif = [(0, 78), (1.5, 76), (2, 74), (3, 73)]          # petite phrase de piano (F#5 E5 D5 C#5), jouée par moments
    for b in range(1, NBARS + 1):
        c = PLAN[b]
        root, voic = CH[c]
        sec = section(b)
        B0 = (b - 1) * 4                                     # temps du début de mesure
        # --- piano
        if sec in ("intro", "breath", "agent"):
            arp = [voic[0] - 12, voic[1], voic[2], voic[3], voic[4], voic[3], voic[2], voic[1]]
            for i, p in enumerate(arp):
                piano.note(B0 + i * 0.5, 0.9, p, (28 if sec == "agent" else 34) + (6 if i == 0 else 0) + (b - 1) * 2 * (sec == "intro"))
        elif sec == "question":
            piano.note(B0, 3.5, voic[4] + 12, 30)
            piano.note(B0 + 2, 1.8, voic[2] + 12, 26)
        elif sec == "logo":
            if b == BELLS[0]:
                for p in voic:
                    piano.note(B0, 7.5, p, 52)
                piano.note(B0, 7.5, root, 46)
            else:
                for p in voic[1:]:
                    piano.note(B0 + 0.5, 3.0, p, 34)
        elif sec in ("A", "A+", "B", "lift"):
            for k in range(4):                               # accords sur les contretemps, doux
                for p in voic[1:4]:
                    piano.note(B0 + k + 0.5, 0.35, p, 30 if sec == "A" else 34)
            if sec in ("A+", "B") and b % 4 == 2:            # la petite phrase toutes les 4 mesures
                for off, p in motif:
                    piano.note(B0 + off, 1.0, p, 44)
        elif sec == "end":
            if b in (BELLS[1], NBARS):
                for p in voic:
                    piano.note(B0, 7.5 if b == NBARS else 3.8, p, 48 if b == BELLS[1] else 38)
            else:
                for i, p in enumerate([voic[0], voic[2], voic[4], voic[2] + 12]):
                    piano.note(B0 + i * 0.5, 2.5, p, 34)
        # --- nappe et cordes
        if sec != "intro" or b >= 2:
            vel = {"intro": 40, "question": 58, "logo": 60, "A": 46, "A+": 48, "breath": 52, "B": 50,
                   "agent": 56, "lift": 58, "end": 54}[sec]
            for p in voic[:4]:
                pad.note(B0, 3.95, p, vel)
        if sec in ("question", "logo", "lift", "end", "breath", "agent"):
            for p in (voic[1] + 12, voic[3] + 12):
                strings.note(B0, 3.95, p, 44 if sec != "lift" else 54)
        # --- basse
        if sec in ("logo", "A", "A+", "B", "lift", "end", "breath", "agent"):
            if sec in ("A", "A+", "breath", "logo", "end", "agent"):
                bass.note(B0, 3.6 if sec != "end" else 3.95, root, 70)
            else:                                            # B / lift : un peu de mouvement
                for k, d in ((0, 1.4), (1.5, 0.45), (2, 1.4), (3.5, 0.45)):
                    bass.note(B0 + k, d, root + (12 if k == 3.5 else 0), 70)
        # --- cloche (célesta) : logo et fin ; arpèges cristallins pour l'agent
        if b in BELLS:
            for i, p in enumerate([74, 78, 81, 85, 86]):
                bell.note(B0 + i * 0.25, 2.5, p, 50)
        if sec == "agent":
            up = sorted(voic[1:]) + [voic[1] + 12, voic[2] + 12]
            for i in range(16):
                bell.note(B0 + i * 0.25, 0.5, up[(i * 3) % len(up)] + 12, 30 + (8 if i % 4 == 0 else 0))
        # --- batterie (canal 10) : discrète
        if sec in ("A", "A+", "B", "lift"):
            for k in range(4):
                if sec != "A" or k in (0, 2):
                    drums.note(B0 + k, 0.2, 36, 58 if k in (0, 2) else 44)          # grosse caisse feutrée
                if k in (1, 3):
                    drums.note(B0 + k, 0.2, 37 if sec in ("A", "A+") else 39, 40)   # cercle / clap
            for k in range(8):
                drums.note(B0 + k * 0.5, 0.2, 82, 34 + (10 if k % 2 else 0))         # shaker
            if sec in ("A+", "B", "lift"):
                for k in range(8):
                    drums.note(B0 + k * 0.5, 0.15, 42, 26 + (8 if k % 2 else 0))     # charleston fermé
            if sec == "lift":
                for k in range(4):
                    drums.note(B0 + k + 0.5, 0.4, 46, 30)                            # charleston ouvert
        elif sec == "breath":
            for k in range(8):
                drums.note(B0 + k * 0.5, 0.2, 82, 26 + (8 if k % 2 else 0))
        elif sec == "agent":
            drums.note(B0, 0.2, 36, 50); drums.note(B0 + 2, 0.2, 36, 42)
            for k in range(8):
                drums.note(B0 + k * 0.5, 0.15, 42, 20 + (6 if k % 2 else 0))
    return dict(piano=piano, pad=pad, strings=strings, bass=bass, bell=bell, drums=drums)


def render(name, track, total):
    mid = os.path.join(OUT, "music", name + ".mid")
    wav = os.path.join(OUT, "music", name + "_raw.wav")
    track.save(mid)
    subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.5", "-r", str(SR), "-F", wav, SF2, mid], check=True,
                   capture_output=True)
    a, sr = sf.read(wav, always_2d=True)
    n = int(total * SR)
    a = np.pad(a, ((0, max(0, n - len(a))), (0, 0)))[:n]
    return a


def main():
    tl = json.load(open(os.path.join(OUT, "timeline.json")))
    total = tl["duration"]
    os.makedirs(os.path.join(OUT, "music"), exist_ok=True)
    global BELLS
    BELLS = setup(tl)
    print("logo mesure %d, logo final mesure %d, %d mesures" % (BELLS[0], BELLS[1], NBARS))
    tracks = compose()
    # niveau relatif et égalisation par piste : rien ne doit occuper la zone 1–4 kHz de la voix
    shape = {
        "piano":   (0.85, [("high", 90), ("low", 6500)]),
        "pad":     (0.55, [("high", 160), ("low", 5000)]),
        "strings": (0.40, [("high", 220), ("low", 6000)]),
        "bass":    (0.70, [("high", 38), ("low", 1800)]),
        "bell":    (0.45, [("high", 600)]),
        "drums":   (0.55, [("high", 45)]),
    }
    mix = np.zeros((int(total * SR), 2))
    for name, tr in tracks.items():
        a = render(name, tr, total)
        gain, filters = shape[name]
        for kind, f in filters:
            a = signal.sosfilt(signal.butter(2, f, kind, fs=SR, output="sos"), a, axis=0)
        # creux de -3 dB autour de 2,5 kHz : la musique laisse la place à la voix
        b, aa = signal.iirpeak(2500, 0.9, fs=SR)
        a = a - 0.29 * signal.lfilter(b, aa, a, axis=0)
        sf.write(os.path.join(OUT, "music", name + ".wav"), (a * gain).astype(np.float32), SR)
        mix += a * gain
    # nappe grave de la nuit (synthèse) : ré grave et quinte, souffle lent, jusqu'au logo
    t = np.arange(len(mix)) / SR
    tlogo = (BELLS[0] - 1) * BAR
    env = np.clip(t / 2.0, 0, 1) * np.clip((tlogo + 0.6 - t) / 0.8, 0, 1)
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * t)
    drone = (np.sin(2 * np.pi * 73.42 * t) + 0.5 * np.sin(2 * np.pi * 110.0 * t) + 0.25 * np.sin(2 * np.pi * 146.83 * t * 1.003)) * env * lfo
    drone = FX.hp(FX.lp(drone, 900), 55) * 0.08
    mix += np.stack([drone, drone], 1)
    mix = FX.reverb(mix, t60=2.6, wet=0.22, hpf=260, seed=4)                    # une salle commune à tous les instruments
    fade = np.clip((total - np.arange(len(mix)) / SR) / 2.4, 0, 1) ** 1.5      # fondu sur la dernière mesure
    mix *= fade[:, None]
    mix /= np.abs(mix).max() + 1e-9
    sf.write(os.path.join(OUT, "music.wav"), (mix * 0.9).astype(np.float32), SR)
    print("-> build/mywebtel/music.wav (%.1f s, %d mesures)" % (total, NBARS))


if __name__ == "__main__":
    main()
