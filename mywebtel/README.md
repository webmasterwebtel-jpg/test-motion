# MyWebtel : film de présentation

Film de 1 min 17 (1920×1080, 30 i/s) qui présente MyWebtel, l'espace collaborateur de Webtel, et ses fonctions de base :
connexion, pointage (arrivée, pause, retour, fin de journée), justification d'un pointage, absences, tickets, documents RH
et documents de l'entreprise.
Voix off française, musique originale, bruitages d'interface discrets, sans sous-titres. Direction : `DIRECTION.md`.

Rendu final : `output/mywebtel_presentation.mp4`. Regénération complète : `mywebtel/make.sh <dossier des modèles>`.

## Chaîne
| Étape | Fichier | Sortie (`build/mywebtel/`) |
|---|---|---|
| Texte de la voix, découpage en scènes, prononciations forcées | `script.py` | |
| Voix off (Kokoro, mélange `ff_siwis` + `af_heart`), rognage, mots datés par transcription (Parakeet), traitement studio | `vo.py` | `vo.wav`, `timeline.json` |
| Logo Webtel vectorisé depuis l'image fournie (potrace) | `vectorize_logo.py` | `film/brand/webtel-logo.svg` |
| Musique composée en MIDI, rendue piste par piste (FluidSynth + MuseScore General) | `music.py` | `music.wav`, `music/` |
| Bruitages synthétisés calés sur les gestes du film, ducking, loudness -16 LUFS | `sfx_mix.py` | `sfx.wav`, `mix.wav` |
| Film HTML piloté par le temps (`renderAt(t)`), lit `timeline.json` | `film/index.html`, `film/film.js` | |
| Rendu image par image (Chromium + ffmpeg) ; exporte aussi les repères des gestes | `render.js` | `video_silent.mp4`, `cues.json` |

`timeline.json` (mots datés) est la seule source des temps : le film (`film.js`) en dérive ses gestes, et les bruitages
(`sfx_mix.py`) lisent les gestes exportés par le film dans `cues.json`.
Changer un texte dans `script.py` puis relancer `make.sh` recale tout.

## Dépendances
- Python : `pip install numpy scipy soundfile pillow mido kokoro-onnx sherpa-onnx`
- Système : `ffmpeg`, `fluidsynth`, `musescore-general-soundfont` (fichier `/usr/share/sounds/sf3/MuseScore_General_Full.sf3`), `potrace`
- Node : `npm ci` dans `mywebtel/` (playwright-core) et un Chromium (`CHROMIUM=/chemin/vers/chrome` si besoin)
- Modèles (hors dépôt) :
  - voix : [kokoro-v1.0.onnx](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx) et [voices-v1.0.bin](https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin)
  - transcription horodatée : [sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2)
  - voix Piper (option `ENGINE = "piper:<voix>"` dans `script.py`) : `vits-piper-fr_FR-*` des mêmes releases (`tts-models`), dans `<modèles>/tts/`

## Vérifier un passage
```bash
node mywebtel/render.js --stills 42.8,61,93.6        # images fixes -> build/mywebtel/stills/
python3 mywebtel/stills_sheet.py                     # planche des images fixes
node mywebtel/render.js --range 39 54                # passage -> build/mywebtel/preview_39_54.mp4
```

## Remplacer la voix
La voix de synthèse est le maillon le plus faible. Pour une voix humaine : enregistrer le texte de `script.py` phrase par phrase,
déposer les fichiers dans `build/mywebtel/vo_segs/` sous les mêmes noms, puis adapter `vo.py` pour lire ces fichiers au lieu
de les synthétiser. Le placement, le film et le mixage suivent sans autre changement.

## À valider avant diffusion
La connexion et le pointage reprennent le code réel (`webtel-intra-clean`). Les écrans de pause, justification, absences,
tickets et documents sont recréés dans la même charte, sans capture de la plateforme en ligne : faire valider leur
ressemblance avant toute diffusion hors de l'équipe projet.

Polices : Inter et Inter Display (`film/fonts/COPYRIGHT-Inter.txt`), Liberation Sans, aux chasses d'Arial comme l'application
(`film/fonts/COPYRIGHT-Liberation.txt`) ; toutes sous SIL Open Font License.
