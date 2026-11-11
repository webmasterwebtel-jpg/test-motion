#!/usr/bin/env bash
# Film de présentation MyWebtel V8 (1920x1080, mock-ups PC/tablette/téléphone sur la vraie interface, style keynote).
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
python3 mywebtel/music7.py                    # électro-pop 120 BPM synthétisée, écrit aussi ses sections dans timeline.json
(cd mywebtel && [ -d node_modules ] || npm ci --silent)
node mywebtel/render.js --workers "${WORKERS:-4}" --fps 60    # 60 i/s : deux images fondues par image finale = flou de mouvement
python3 mywebtel/sfx_mix.py                   # lit cues.json, écrit par render.js
mkdir -p output
B=build/mywebtel; V="tmix=frames=2:weights='1 1',fps=30"
X="-c:v libx264 -preset slow -pix_fmt yuv420p -profile:v high"
# master 1080p (≈14 Mbit/s, ≈190 Mo) : à diffuser ; trop lourd pour GitHub, il n'est pas versionné
ffmpeg -y -loglevel error -i $B/video_silent.mp4 -vf "$V" $X -b:v 14M -maxrate 22M -bufsize 28M -pass 1 -passlogfile $B/x264pass -an -f null /dev/null
ffmpeg -y -loglevel error -i $B/video_silent.mp4 -i $B/mix.wav -map 0:v -map 1:a -vf "$V" $X -b:v 14M -maxrate 22M -bufsize 28M -pass 2 \
  -passlogfile $B/x264pass -c:a aac -b:a 256k -ar 48000 -shortest -movflags +faststart output/mywebtel_presentation.mp4
# copie versionnée (< 100 Mo, limite de GitHub)
ffmpeg -y -loglevel error -i output/mywebtel_presentation.mp4 $X -b:v 6M -maxrate 9M -bufsize 12M -pass 1 -passlogfile $B/webpass -an -f null /dev/null
ffmpeg -y -loglevel error -i output/mywebtel_presentation.mp4 $X -b:v 6M -maxrate 9M -bufsize 12M -pass 2 -passlogfile $B/webpass -c:a copy \
  -movflags +faststart output/mywebtel_presentation_web.mp4
python3 .claude/skills/motion-delivery/scripts/check_delivery.py output/mywebtel_presentation.mp4 --profile presentation
