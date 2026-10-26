# MyWebtel : film de présentation

Film de 1 min 53 (1920×1080, 30 i/s) qui présente MyWebtel, l'espace collaborateur de Webtel, **sur sa vraie interface** :
pointage (arrivée, pause, retour, fin de journée), congés (droits ouverts après 1 an d'ancienneté), Mes absences,
Mes documents, Mes demandes RH, Contenu, Mail et Support IT. Voix off française, musique originale, bruitages discrets,
sans sous-titres. Direction : `DIRECTION.md`.

Rendu final : `output/mywebtel_presentation.mp4`. Regénération complète : `mywebtel/make.sh <modèles> <APERCU-MYWEBTEL.html>`.

## Vraie interface
Les écrans viennent de l'aperçu HTML généré par le PHP de la plateforme (archive « MYWEBTEL_fichiers_retrouves_PARTIEL »,
14/10/2026). `prep_ui.py` en extrait les neuf écrans, coupe scripts et transitions, remplace les données de test par des
données de démonstration, et ajoute « Mail » et « Support IT » (absents de l'archive) avec les composants de la plateforme.
Le résultat (`build/mywebtel/ui.json`) n'est **jamais versionné** : ce dépôt est public. Le film charge chaque écran dans
une iframe et ne fait que remplir les champs, cliquer et changer les états avec les libellés réels du PHP
(« Commencer ma journée », « Je pars en pause », « Je reviens de pause », « Terminer ma journée »…).

## Chaîne
| Étape | Fichier | Sortie (`build/mywebtel/`) |
|---|---|---|
| Texte de la voix, découpage en scènes, prononciations forcées | `script.py` | |
| Voix off (Kokoro `ff_siwis`), rognage, mots datés par transcription (Parakeet), traitement studio | `vo.py` | `vo.wav`, `timeline.json` |
| Logo Webtel vectorisé depuis l'image fournie (potrace) | `vectorize_logo.py` | `film/brand/webtel-logo.svg` |
| Musique composée en MIDI, rendue piste par piste (FluidSynth + MuseScore General) | `music.py` | `music.wav`, `music/` |
| Bruitages synthétisés calés sur les gestes du film, ducking, loudness -16 LUFS | `sfx_mix.py` | `sfx.wav`, `mix.wav` |
| Vraie interface : écrans de l'aperçu PHP préparés pour le film | `prep_ui.py` | `ui.json` (non versionné) |
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
Les écrans « Mail » et « Support IT » sont composés avec les composants de la plateforme (ils ne figurent pas dans
l'archive du 14/10) : remplacer par les vrais écrans dès qu'ils sont disponibles. Les données affichées sont fictives.

Polices : Inter et Inter Display (`film/fonts/COPYRIGHT-Inter.txt`), Liberation Sans, aux chasses d'Arial comme l'application
(`film/fonts/COPYRIGHT-Liberation.txt`) ; toutes sous SIL Open Font License.
