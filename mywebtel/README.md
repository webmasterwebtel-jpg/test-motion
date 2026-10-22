# MyWebtel : film de présentation

Film de 2 min 05 (1920×1080, 30 i/s) qui présente l'intranet MyWebtel et ses fonctions, à partir du dossier fonctionnel.
Voix off française, musique originale, bruitages d'interface discrets, sans sous-titres. Direction : `DIRECTION.md`.

Rendu final : `output/mywebtel_presentation.mp4`. Regénération complète : `mywebtel/make.sh <dossier des modèles>`.

## Chaîne
| Étape | Fichier | Sortie (`build/mywebtel/`) |
|---|---|---|
| Texte de la voix, découpage en scènes, prononciations forcées | `script.py` | |
| Voix off (Kokoro, voix `ff_siwis`), traitement studio, placement sur la grille 100 BPM | `vo.py` | `vo.wav`, `timeline.json` |
| Contrôle de la diction par transcription (Whisper small) | `asr.py` | |
| Musique composée en MIDI, rendue piste par piste (FluidSynth + MuseScore General) | `music.py` | `music.wav`, `music/` |
| Bruitages synthétisés calés sur les gestes, ducking, loudness -16 LUFS | `sfx_mix.py` | `sfx.wav`, `mix.wav` |
| Film HTML piloté par le temps (`renderAt(t)`), lit `timeline.json` | `film/index.html`, `film/film.js` | |
| Rendu image par image (Chromium + ffmpeg) | `render.js` | `video_silent.mp4` |

`timeline.json` est la seule source des temps : l'image (`film.js`) et les bruitages (`sfx_mix.py`) en dérivent.
Changer un texte dans `script.py` puis relancer `make.sh` recale tout.

## Dépendances
- Python : `pip install numpy scipy soundfile pillow mido kokoro-onnx sherpa-onnx`
- Système : `ffmpeg`, `fluidsynth`, `musescore-general-soundfont` (fichier `/usr/share/sounds/sf3/MuseScore_General_Full.sf3`)
- Node : `npm ci` dans `mywebtel/` (playwright-core) et un Chromium (`CHROMIUM=/chemin/vers/chrome` si besoin)
- Modèles (hors dépôt) :
  - voix : [kokoro-v1.0.onnx](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx) et [voices-v1.0.bin](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin)
  - transcription : [sherpa-onnx-whisper-small](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2)

## Vérifier un passage
```bash
node mywebtel/render.js --stills 42.8,61,93.6        # images fixes -> build/mywebtel/stills/
python3 mywebtel/stills_sheet.py                     # planche des images fixes
node mywebtel/render.js --range 39 54                # passage -> build/mywebtel/preview_39_54.mp4
python3 mywebtel/asr.py <modèles>/sherpa-onnx-whisper-small build/mywebtel/vo_segs/*.wav
```

## Remplacer la voix
La voix de synthèse est le maillon le plus faible. Pour une voix humaine : enregistrer le texte de `script.py` phrase par phrase,
déposer les fichiers dans `build/mywebtel/vo_segs/` sous les mêmes noms, puis adapter `vo.py` pour lire ces fichiers au lieu
de les synthétiser. Le placement, le film et le mixage suivent sans autre changement.

## À valider avant diffusion
Le film montre les fonctions décrites dans le dossier fonctionnel. Dans le code actuel de l'application, seuls la connexion et
le pointage sont en place : faire valider le contenu avant toute diffusion hors de l'équipe projet.

Polices : Inter et Inter Display (SIL Open Font License, `film/fonts/COPYRIGHT-Inter.txt`).
