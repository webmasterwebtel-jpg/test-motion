#!/usr/bin/env bash
# Génère la vidéo TikTok « Crochet Pop Collage » (sans voix ni texte) :
# détourage -> bande-son (musique de fond + bruitages) -> rendu image -> mux final.
# Dépendances : python3 (pillow numpy scipy), ffmpeg.
set -euo pipefail
cd "$(dirname "$0")"
python3 motion/prep.py
(cd motion && python3 audio_collage.py)
ffmpeg -y -loglevel error -i build/audio/collage_mix.wav -af loudnorm=I=-15:TP=-1.5:LRA=11 -ar 48000 \
  build/audio/collage_final.wav
python3 motion/collage.py
mkdir -p output
ffmpeg -y -loglevel error -i build/collage_silent.mp4 -i build/audio/collage_final.wav \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -ar 48000 -movflags +faststart -shortest \
  output/crochet_tiktok_40s.mp4
echo "-> output/crochet_tiktok_40s.mp4"
