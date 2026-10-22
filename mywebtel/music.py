#!/usr/bin/env python3
"""Musique de fond MyWebtel : composée en MIDI, rendue piste par piste avec FluidSynth (banque libre MuseScore General).

100 BPM, une mesure = 2,4 s, ré majeur, un accord par mesure. L'arrangement suit les scènes de build/mywebtel/timeline.json :
intro au piano seul, respiration sur la question, accord lumineux sur le logo (mesure 8), groove discret pendant les
fonctions, respiration sur documents/annonces, montée vers le logo final (mesure 50), résolution plagale.

Sorties : build/mywebtel/music/<piste>.wav (48 kHz stéréo) et build/mywebtel/music.wav (mixage des pistes, sans ducking).
Usage : python3 mywebtel/music.py
"""
import json, os, random, subprocess
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
PLAN = {}                                    # mesure (1..52) -> accord
for b, c in zip(range(1, 6), ["Bm7", "Gmaj7", "D/F#", "Asus", "Gmaj7"]):
    PLAN[b] = c
PLAN.update({6: "Em9", 7: "Asus", 8: "D", 9: "Bm7"})
for b in range(10, 49):
    PLAN[b] = LOOP[(b - 10) % 4]
PLAN.update({48: "Gmaj9", 49: "Asus", 50: "D", 51: "Gmaj9", 52: "D"})
NBARS = 52

# sections : quels instruments jouent
def section(b):
    if b <= 5: return "intro"
    if b <= 7: return "question"
    if b <= 9: return "logo"
    if b <= 17: return "A"          # vision, rôles
    if b <= 28: return "A+"         # pointage, congés
    if b <= 36: return "breath"     # documents, annonces
    if b <= 46: return "B"          # devis, réglages
    if b <= 49: return "lift"       # partout
    return "end"


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
        if sec in ("intro", "breath"):
            arp = [voic[0] - 12, voic[1], voic[2], voic[3], voic[4], voic[3], voic[2], voic[1]]
            for i, p in enumerate(arp):
                piano.note(B0 + i * 0.5, 0.9, p, 34 + (6 if i == 0 else 0) + (b - 1) * 2 * (sec == "intro"))
        elif sec == "question":
            piano.note(B0, 3.5, voic[4] + 12, 30)
            piano.note(B0 + 2, 1.8, voic[2] + 12, 26)
        elif sec == "logo":
            if b == 8:
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
            if b in (50, 52):
                for p in voic:
                    piano.note(B0, 7.5 if b == 52 else 3.8, p, 48 if b == 50 else 38)
            else:
                for i, p in enumerate([voic[0], voic[2], voic[4], voic[2] + 12]):
                    piano.note(B0 + i * 0.5, 2.5, p, 34)
        # --- nappe et cordes
        if sec != "intro" or b >= 2:
            vel = {"intro": 40, "question": 58, "logo": 60, "A": 46, "A+": 48, "breath": 52, "B": 50,
                   "lift": 58, "end": 54}[sec]
            for p in voic[:4]:
                pad.note(B0, 3.95, p, vel)
        if sec in ("question", "logo", "lift", "end", "breath"):
            for p in (voic[1] + 12, voic[3] + 12):
                strings.note(B0, 3.95, p, 44 if sec != "lift" else 54)
        # --- basse
        if sec in ("logo", "A", "A+", "B", "lift", "end", "breath"):
            if sec in ("A", "A+", "breath", "logo", "end"):
                bass.note(B0, 3.6 if sec != "end" else 3.95, root, 70)
            else:                                            # B / lift : un peu de mouvement
                for k, d in ((0, 1.4), (1.5, 0.45), (2, 1.4), (3.5, 0.45)):
                    bass.note(B0 + k, d, root + (12 if k == 3.5 else 0), 70)
        # --- cloche (célesta) : logo et fin
        if b in (8, 50):
            for i, p in enumerate([74, 78, 81, 85, 86]):
                bell.note(B0 + i * 0.25, 2.5, p, 50)
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
    fade = np.clip((total - np.arange(len(mix)) / SR) / 2.4, 0, 1) ** 1.5      # fondu sur la dernière mesure
    mix *= fade[:, None]
    mix /= np.abs(mix).max() + 1e-9
    sf.write(os.path.join(OUT, "music.wav"), (mix * 0.9).astype(np.float32), SR)
    print("-> build/mywebtel/music.wav (%.1f s, %d mesures)" % (total, NBARS))


if __name__ == "__main__":
    main()
