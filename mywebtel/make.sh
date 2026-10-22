#!/usr/bin/env bash
# Film de présentation MyWebtel (1920x1080, voix off, musique, bruitages, sans sous-titres).
# voix off -> musique -> bruitages + mixage -> rendu image (Chromium) -> mux final.
# Usage : mywebtel/make.sh <dossier des modèles Kokoro>   (voir mywebtel/README.md)
set -euo pipefail
cd "$(dirname "$0")/.."
MODELS="${1:?dossier contenant kokoro-v1.0.onnx et voices-v1.0.bin}"
python3 mywebtel/vo.py "$MODELS"
python3 mywebtel/music.py
python3 mywebtel/sfx_mix.py
(cd mywebtel && [ -d node_modules ] || npm ci --silent)
node mywebtel/render.js --workers "${WORKERS:-4}"
mkdir -p output
ffmpeg -y -loglevel error -i build/mywebtel/video_silent.mp4 -i build/mywebtel/mix.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart output/mywebtel_presentation.mp4
python3 .claude/skills/motion-delivery/scripts/check_delivery.py output/mywebtel_presentation.mp4 --profile presentation
