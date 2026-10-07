"""Outils partagés par les scripts de relecture : sonde ffprobe, décodage vidéo/audio via ffmpeg, police."""
import json, os, subprocess
import numpy as np
from PIL import ImageFont

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/arial.ttf",
    os.path.join("assets", "fonts", "Montserrat-Medium.ttf"),
]


def label_font(size):
    """Police Unicode (accents, ·, →, ●) ; repli sur la police intégrée de Pillow."""
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()


def probe(path):
    """(largeur, hauteur, i/s, durée) de la première piste vidéo."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = j["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return int(s["width"]), int(s["height"]), float(num) / float(den), float(j["format"]["duration"])


def read_frames(path, start, end, w, h, fps=None, gray=False):
    """Décode [start, end[ redimensionné en w×h (RGB, ou niveaux de gris si gray=True).
    Avec fps=None on garde toutes les images de la source."""
    vf = "scale=%d:%d:flags=area" % (w, h)
    if fps:
        vf = "fps=%g," % fps + vf
    pix = "gray" if gray else "rgb24"
    cmd = ["ffmpeg", "-v", "error", "-ss", "%.4f" % start, "-i", path, "-t", "%.4f" % (end - start),
           "-vf", vf, "-f", "rawvideo", "-pix_fmt", pix, "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    shape = (-1, h, w) if gray else (-1, h, w, 3)
    return np.frombuffer(raw, np.uint8).reshape(shape)


def has_audio(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    return bool(out.strip())


def read_audio(path, sr=22050, start=0.0, end=None):
    """Audio mono float32 à sr Hz (fonctionne sur une vidéo ou un .wav)."""
    cmd = ["ffmpeg", "-v", "error", "-ss", "%.4f" % start, "-i", path]
    if end is not None:
        cmd += ["-t", "%.4f" % (end - start)]
    cmd += ["-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def onset_envelope(x, sr, hop, n_bands=8):
    """Force d'attaque, une valeur par bloc de `hop` échantillons (bloc k = image k si hop = sr/fps).

    Blocs jointifs et non recouvrants : une attaque qui tombe pendant l'image k est comptée sur
    l'image k, sans le biais d'avance d'une fenêtre glissante. Le flux est calculé par bandes
    logarithmiques de poids égal, pour qu'un impact grave compte autant qu'un clic aigu."""
    n = len(x) // hop
    blocks = x[:n * hop].reshape(n, hop)
    spec = np.abs(np.fft.rfft(blocks, axis=1)) ** 2
    freqs = np.fft.rfftfreq(hop, 1.0 / sr)
    edges = np.geomspace(40, min(16000, sr / 2), n_bands + 1)
    bands = np.stack([spec[:, (freqs >= lo) & (freqs < hi)].sum(axis=1) for lo, hi in zip(edges[:-1], edges[1:])], 1)
    # plancher à -50 dB sous le niveau moyen de chaque bande : un silence numérique ne crée pas d'attaque géante
    logb = np.log10(bands + bands.mean(axis=0) * 1e-5 + 1e-12)
    flux = np.maximum(logb[1:] - logb[:-1], 0).sum(axis=1)
    flux = np.concatenate([[0], flux])
    flux = np.maximum(flux - ndimage_median(flux, 15), 0)   # retire le fond (musique continue)
    return np.clip(flux / (np.percentile(flux, 99.5) + 1e-9), 0, 1)


def ndimage_median(x, size):
    from scipy import ndimage
    return ndimage.median_filter(x, size)


def peaks(sig, thr, min_gap):
    """Indices des maxima locaux au-dessus de thr, séparés d'au moins min_gap échantillons."""
    cand = [i for i in range(1, len(sig) - 1) if sig[i] >= thr and sig[i] >= sig[i - 1] and sig[i] > sig[i + 1]]
    out = []
    for i in sorted(cand, key=lambda i: -sig[i]):
        if all(abs(i - j) >= min_gap for j in out):
            out.append(i)
    return sorted(out)
