#!/usr/bin/env bash
# Film de présentation MyWebtel V6 (1920x1080, monde 3D sur la vraie interface, voix off, musique, bruitages).
# vraie interface -> voix (ElevenLabs « Simon », segments en cache) -> timeline -> musique -> rendu image (Chromium,
# exporte aussi les repères des gestes) -> bruitages + mixage -> mux final.
# Usage : mywebtel/make.sh <APERCU-MYWEBTEL.html>   (voir mywebtel/README.md)
set -euo pipefail
cd "$(dirname "$0")/.."
APERCU="${1:?aperçu HTML réel de MyWebtel (APERCU-MYWEBTEL.html)}"
python3 mywebtel/prep_ui.py "$APERCU"
python3 mywebtel/voice/eleven_gen6.py --takes 1,2,3   # prises absentes seulement ; choix dans voice/picks_v6.json
python3 mywebtel/voice/eleven_gen6.py --variant b --takes 2 mail   # « Mèl » : voyelle française stable
python3 mywebtel/vo_eleven.py
python3 mywebtel/music.py
(cd mywebtel && [ -d node_modules ] || npm ci --silent)
node mywebtel/render.js --workers "${WORKERS:-4}"
python3 mywebtel/sfx_mix.py                   # lit cues.json, écrit par render.js
mkdir -p output
ffmpeg -y -loglevel error -i build/mywebtel/video_silent.mp4 -i build/mywebtel/mix.wav -map 0:v -map 1:a \
  -c:v copy -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart output/mywebtel_presentation.mp4
python3 .claude/skills/motion-delivery/scripts/check_delivery.py output/mywebtel_presentation.mp4 --profile presentation
