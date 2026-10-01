#!/usr/bin/env bash
# Génère la vidéo complète : détourage -> bande-son -> rendu image -> mux final.
# Dépendances : python3 (pillow numpy scipy kokoro-onnx), ffmpeg, sox.
set -euo pipefail
cd "$(dirname "$0")"
python3 motion/prep.py
# modèle de voix Kokoro (≈ 350 Mo, téléchargé une seule fois)
K=build/kokoro; mkdir -p $K
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  [ -s $K/$f ] || curl -sSL -o $K/$f https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/$f
done
python3 motion/audio.py
python3 motion/render.py
mkdir -p output
ffmpeg -y -loglevel error -i build/video_silent.mp4 -i build/audio/mix.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest \
  output/crochet_motion_40s.mp4
cp build/voix_off.srt output/crochet_motion_40s.srt
echo "-> output/crochet_motion_40s.mp4"
