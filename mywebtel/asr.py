#!/usr/bin/env python3
"""Transcription de contrôle (Whisper small via sherpa-onnx) : vérifie ce que la voix prononce réellement.

Usage : python3 mywebtel/asr.py MODELE_DIR fichier1.wav [fichier2.wav ...]
"""
import sys
import numpy as np
import soundfile as sf
import sherpa_onnx


def recognizer(model_dir):
    return sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=model_dir + "/small-encoder.int8.onnx", decoder=model_dir + "/small-decoder.int8.onnx",
        tokens=model_dir + "/small-tokens.txt", language="fr", task="transcribe", num_threads=4)


def transcribe(rec, path):
    from math import gcd
    from scipy.signal import resample_poly
    a, sr = sf.read(path, dtype="float32", always_2d=True)
    a = a.mean(1)
    if sr != 16000:                                     # rééchantillonnage filtré (sans repliement)
        g = gcd(sr, 16000)
        a = resample_poly(a, 16000 // g, sr // g).astype(np.float32)
    # Whisper laisse tomber le dernier mot d'un extrait coupé net : on ajoute du silence autour
    a = np.concatenate([np.zeros(6400, np.float32), a, np.zeros(9600, np.float32)])
    s = rec.create_stream()
    s.accept_waveform(16000, a)
    rec.decode_stream(s)
    return s.result.text.strip()


if __name__ == "__main__":
    rec = recognizer(sys.argv[1])
    for p in sys.argv[2:]:
        print("%-40s %s" % (p.split("/")[-1], transcribe(rec, p)))
