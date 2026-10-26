#!/usr/bin/env python3
"""Voix off MyWebtel : synthèse segment par segment, alignement mot à mot, placement sur la grille, traitement « studio ».

Moteur : Kokoro (`ff_siwis`) ou une voix Piper (sherpa-onnx), selon script.ENGINE. Chaque segment est rogné de ses
silences de bord : les respirations entre phrases sont exactement celles du script. Les mots sont datés par la
transcription Parakeet TDT (horodatage par jeton), ce qui permet de caler un clic à l'image sur le mot prononcé.

Sorties (build/mywebtel/) :
  vo_segs/<scene>_<n>.wav  segments bruts, rognés
  vo.wav                   piste voix traitée, 48 kHz mono, placée sur la timeline du film
  timeline.json            scènes, segments et mots datés (sert à l'image, à la musique et aux bruitages)

Usage : python3 mywebtel/vo.py MODELS_DIR
  MODELS_DIR contient kokoro-v1.0.onnx, voices-v1.0.bin, tts/vits-piper-<voix>/ et
  sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8/ (liens dans mywebtel/README.md)
"""
import json, math, os, re, sys
import numpy as np
import soundfile as sf
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import script as S  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "mywebtel")
SR = 48000


# ----------------------------------------------------------------------------- phonétique
def phonemize(k, text):
    """Phonèmes espeak français, avec les corrections de OVERRIDES et sans marqueurs de langue « (en) »."""
    pat = re.compile("|".join("(%s)" % p for p, _ in S.OVERRIDES), re.I)   # « Vous ouvrez » comme « vous ouvrez »
    parts, pos = [], 0
    for m in pat.finditer(text):
        if m.start() > pos:
            parts.append(k.tokenizer.phonemize(text[pos:m.start()], "fr-fr"))
        for (p, ph), g in zip(S.OVERRIDES, m.groups()):
            if g:
                parts.append(ph)
                break
        pos = m.end()
    if pos < len(text):
        parts.append(k.tokenizer.phonemize(text[pos:], "fr-fr"))
    ph = " ".join(p for p in parts if p)
    ph = re.sub(r"\([a-z]{2}\)", "", ph)                 # marqueurs de changement de langue : prononcés sinon
    ph = ph.replace("œ̃", "ɛ̃")                            # « un » à la parisienne : le œ̃ de la voix sonne « an » (« d'un » → « dans »)
    ph = re.sub(r"\s+([.,:;?!»])", r"\1", ph)
    return re.sub(r"\s+", " ", ph).strip()


# ----------------------------------------------------------------------------- traitement
def biquad(kind, f0, gain_db=0.0, q=0.707, sr=SR):
    A = 10 ** (gain_db / 40)
    w = 2 * math.pi * f0 / sr
    cw, sw = math.cos(w), math.sin(w)
    al = sw / (2 * q)
    if kind == "peak":
        b = [1 + al * A, -2 * cw, 1 - al * A]; a = [1 + al / A, -2 * cw, 1 - al / A]
    elif kind == "lowshelf":
        s = 2 * math.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * cw + s), 2 * A * ((A - 1) - (A + 1) * cw), A * ((A + 1) - (A - 1) * cw - s)]
        a = [(A + 1) + (A - 1) * cw + s, -2 * ((A - 1) + (A + 1) * cw), (A + 1) + (A - 1) * cw - s]
    elif kind == "highshelf":
        s = 2 * math.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * cw + s), -2 * A * ((A - 1) + (A + 1) * cw), A * ((A + 1) + (A - 1) * cw - s)]
        a = [(A + 1) - (A - 1) * cw + s, 2 * ((A - 1) - (A + 1) * cw), (A + 1) - (A - 1) * cw - s]
    return np.array(b) / a[0], np.array(a) / a[0]


def envelope(x, attack, release, sr=SR):
    """Suiveur d'enveloppe (valeur absolue, attaque/relâchement exponentiels)."""
    a_at, a_re = math.exp(-1 / (attack * sr)), math.exp(-1 / (release * sr))
    env = np.empty_like(x)
    e = 0.0
    ax = np.abs(x)
    for i in range(len(x)):
        v = ax[i]
        e = a_at * e + (1 - a_at) * v if v > e else a_re * e + (1 - a_re) * v
        env[i] = e
    return env


def studio_chain(x):
    """Coupe-bas, chaleur, présence, de-esser, compression douce : voix posée et intelligible, sans effet visible."""
    x = signal.sosfilt(signal.butter(2, 75, "high", fs=SR, output="sos"), x)
    for kind, f, g, q in (("lowshelf", 180, 1.5, 0.7), ("peak", 420, -1.5, 1.0), ("peak", 3200, 2.0, 0.9),
                          ("highshelf", 9000, 1.0, 0.7)):
        b, a = biquad(kind, f, g, q)
        x = signal.lfilter(b, a, x)
    # de-esser : on atténue la bande 5–11 kHz seulement quand elle domine
    hi = signal.sosfilt(signal.butter(4, 5000, "high", fs=SR, output="sos"), x)
    lo = x - hi
    eh = envelope(hi, 0.002, 0.06) + 1e-6
    ef = envelope(x, 0.002, 0.06) + 1e-6
    ratio = eh / ef
    g = np.clip((0.35 / ratio) ** 0.6, 0.35, 1.0)                 # au-delà de 35 % d'énergie aiguë, on réduit
    x = lo + hi * g
    # compression RMS 2,5:1 au-dessus de -24 dBFS
    rms = np.sqrt(signal.lfilter([1 - 0.995], [1, -0.995], x * x) + 1e-12)
    lvl = 20 * np.log10(rms)
    gr = np.where(lvl > -24, (lvl + 24) * (1 / 2.5 - 1), 0.0)
    gr = signal.lfilter([1 - 0.999], [1, -0.999], gr)              # lissage (~20 ms)
    x = x * 10 ** (gr / 20)
    return x / (np.abs(x).max() + 1e-9) * 10 ** (-3 / 20)


def split_points(a, n):
    """Débuts des n parties d'une énumération dite d'un seul tenant : les n-1 plus longs micro-silences."""
    hop = int(0.01 * SR)
    fr = a[:len(a) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    quiet = db < db.max() - 32
    runs, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if i > 0 and j < len(quiet):
                runs.append((j - i, i, j))
            i = j
        else:
            i += 1
    best = sorted(sorted(runs, reverse=True)[:n - 1], key=lambda r: r[1])
    if len(best) < n - 1:
        raise RuntimeError("énumération : %d silences trouvés au lieu de %d" % (len(best), n - 1))
    return [0.0] + [r[2] * hop / SR for r in best]


# ----------------------------------------------------------------------------- moteurs, rognage, alignement
class Engine:
    def __init__(self, models):
        self.kind = S.ENGINE
        if self.kind == "kokoro":
            from kokoro_onnx import Kokoro
            self.k = Kokoro(os.path.join(models, "kokoro-v1.0.onnx"), os.path.join(models, "voices-v1.0.bin"))
        else:                                                   # "piper:<nom de la voix>"
            import sherpa_onnx
            d = os.path.join(models, "tts", "vits-piper-" + self.kind.split(":", 1)[1])
            onnx = [f for f in os.listdir(d) if f.endswith(".onnx")][0]
            self.k = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=os.path.join(d, onnx), tokens=os.path.join(d, "tokens.txt"),
                                                           data_dir=os.path.join(d, "espeak-ng-data")), num_threads=4)))

    def style(self):
        """VOICE = "nom" ou mélange "nom:poids,nom:poids" de vecteurs de style Kokoro."""
        if ":" not in S.VOICE:
            return S.VOICE
        return sum(float(w) * self.k.get_voice_style(n) for n, w in (p.split(":") for p in S.VOICE.split(",")))

    def say(self, text, speed):
        """Renvoie (audio 48 kHz, phonèmes ou texte effectivement envoyé)."""
        if self.kind == "kokoro":
            ph = phonemize(self.k, text)
            a, sr = self.k.create(ph, voice=self.style(), speed=speed, is_phonemes=True)
        else:
            ph = re.sub(r"[«»]", "", text)
            for pat, rep in S.SPELL:
                ph = re.sub(pat, rep, ph)
            r = self.k.generate(ph, sid=S.SPEAKER, speed=speed)
            a, sr = np.array(r.samples), r.sample_rate
        return signal.resample_poly(np.asarray(a, np.float64), SR // 1000, sr // 1000), ph


def trim(a, floor_db=-48, margin=0.03):
    """Rogne les silences de début et de fin (sous floor_db du maximum), en gardant une petite marge."""
    hop = int(0.005 * SR)
    fr = a[:len(a) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    on = np.nonzero(db > db.max() + floor_db)[0]
    i0 = max(0, on[0] * hop - int(margin * SR))
    i1 = min(len(a), (on[-1] + 1) * hop + int(margin * SR))
    out = a[i0:i1].copy()
    f = int(0.008 * SR)
    out[:f] *= np.linspace(0, 1, f)
    out[-f:] *= np.linspace(1, 0, f)
    return out


def norm_word(w):
    w = w.lower().replace("’", "'")
    w = "".join(c for c in w if c.isalnum() or c in "'-")
    return w.strip("'-")


class Aligner:
    """Date les mots d'un segment avec Parakeet TDT (jetons horodatés), puis les rapproche des mots du script."""
    def __init__(self, models):
        import sherpa_onnx
        d = os.path.join(models, "sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8")
        self.rec = sherpa_onnx.OfflineRecognizer.from_transducer(
            encoder=os.path.join(d, "encoder.int8.onnx"), decoder=os.path.join(d, "decoder.int8.onnx"),
            joiner=os.path.join(d, "joiner.int8.onnx"), tokens=os.path.join(d, "tokens.txt"),
            model_type="nemo_transducer", num_threads=4)

    def words(self, a, text):
        pad0 = 0.4
        x = signal.resample_poly(a, 1, 3).astype(np.float32)          # 48 k -> 16 k
        x = np.concatenate([np.zeros(int(pad0 * 16000), np.float32), x, np.zeros(9600, np.float32)])
        st = self.rec.create_stream()
        st.accept_waveform(16000, x)
        self.rec.decode_stream(st)
        r = st.result
        hyp = []                                                   # (mot, début)
        for tok, t in zip(r.tokens, r.timestamps):
            if tok.startswith(" ") or not hyp:
                hyp.append([tok.strip(), t - pad0])
            else:
                hyp[-1][0] += tok
        hyp = [(norm_word(w), t) for w, t in hyp if norm_word(w)]
        ref = [w for w in re.findall(r"[\wÀ-ÿ'’-]+", text)]
        import difflib
        sm = difflib.SequenceMatcher(a=[norm_word(w) for w in ref], b=[w for w, _ in hyp], autojunk=False)
        times = [None] * len(ref)
        for blk in sm.get_matching_blocks():
            for k in range(blk.size):
                times[blk.a + k] = hyp[blk.b + k][1]
        dur = len(a) / SR                                          # mots non reconnus : interpolation
        known = [(i, t) for i, t in enumerate(times) if t is not None]
        for i in range(len(times)):
            if times[i] is None:
                prev = max([k for k in known if k[0] < i], default=(-1, 0.0), key=lambda k: k[0])
                nxt = min([k for k in known if k[0] > i], default=(len(ref), dur), key=lambda k: k[0])
                times[i] = prev[1] + (nxt[1] - prev[1]) * (i - prev[0]) / (nxt[0] - prev[0])
        return r.text.strip(), [[w, round(max(0.0, t), 3)] for w, t in zip(ref, times)]


# ----------------------------------------------------------------------------- synthèse et placement
def main():
    models = sys.argv[1]
    eng, al = Engine(models), Aligner(models)
    os.makedirs(os.path.join(OUT, "vo_segs"), exist_ok=True)
    t, scenes, clips = 0.0, [], []
    words = speech = 0.0
    for sc in S.SCENES:
        start = math.ceil(t / S.BEAT - 1e-6) * S.BEAT            # la scène commence sur un temps
        cur = start + sc["lead"]
        segs = []
        for n, seg in enumerate(sc["segs"]):
            text, gap = seg[0], seg[1]
            speed = seg[2] if len(seg) > 2 and seg[2] else S.SPEED
            snap = seg[4] if len(seg) > 4 else None
            if snap:                                            # départ calé sur le temps ou la mesure suivante
                unit = S.BEAT * (4 if snap == "bar" else 1)
                cur = math.ceil(cur / unit - 1e-6) * unit
            a, ph = eng.say(text, speed)
            a = trim(a)
            sf.write(os.path.join(OUT, "vo_segs", "%s_%d.wav" % (sc["id"], n)), a.astype(np.float32), SR)
            heard, wl = al.words(a, text)
            item = dict(text=text, phonemes=ph, start=round(cur, 3), end=round(cur + len(a) / SR, 3), heard=heard,
                        words=[[w, round(cur + x, 3)] for w, x in wl])
            segs.append(item)
            clips.append((cur, a))
            words += len(wl)
            speech += len(a) / SR
            cur += len(a) / SR + gap
        scenes.append(dict(id=sc["id"], start=round(start, 3), segs=segs))
        t = cur
    end_speech = scenes[-1]["segs"][-1]["end"]
    bar = 4 * S.BEAT
    total = math.ceil((end_speech + S.TAIL) / bar) * bar
    for i, sc in enumerate(scenes):
        sc["end"] = scenes[i + 1]["start"] if i + 1 < len(scenes) else round(total, 3)
    track = np.zeros(int(total * SR) + 1)
    for t0, a in clips:
        i0 = int(round(t0 * SR))
        track[i0:i0 + len(a)] += a
    track = studio_chain(track)
    sf.write(os.path.join(OUT, "vo.wav"), track.astype(np.float32), SR)
    tl = dict(bpm=S.BPM, beat=S.BEAT, fps=30, duration=round(total, 3), engine=S.ENGINE, scenes=scenes)
    with open(os.path.join(OUT, "timeline.json"), "w") as f:
        json.dump(tl, f, ensure_ascii=False, indent=1)
    span = end_speech - scenes[0]["segs"][0]["start"]
    print("durée %.1f s (%d mesures) · parole %.1f s · %d mots · %.0f mots/min sur la durée parlée, %.0f sur la durée de voix"
          % (total, round(total / bar), speech, words, words / span * 60, words / speech * 60))
    for sc in scenes:
        print("  %-10s %6.2f → %6.2f s  première parole %6.2f" % (sc["id"], sc["start"], sc["end"], sc["segs"][0]["start"]))
    bad = 0
    for sc in scenes:                                           # contrôle de diction : ce que la transcription a entendu
        for g in sc["segs"]:
            ref = [norm_word(w) for w in re.findall(r"[\wÀ-ÿ'’-]+", g["text"])]
            hyp = [norm_word(w) for w in re.findall(r"[\wÀ-ÿ'’-]+", g["heard"])]
            import difflib
            r = difflib.SequenceMatcher(a=ref, b=hyp).ratio()
            if r < 0.999:
                bad += 1
                print("  ≠ %-9s %.2f  script : %s\n              entendu : %s" % (sc["id"], r, g["text"], g["heard"]))
    print("segments entendus à l'identique : %d/%d" % (sum(len(s["segs"]) for s in scenes) - bad, sum(len(s["segs"]) for s in scenes)))


if __name__ == "__main__":
    main()
