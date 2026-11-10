# MyWebtel : film de présentation

Film de 1 min 50 (1920×1080, 30 i/s) qui présente MyWebtel, l'espace collaborateur de Webtel, **sur sa vraie interface** :
pointage (arrivée, pause, retour, fin de journée), congés (droits ouverts après 1 an d'ancienneté), Mes absences,
**signature de documents** (nom manuscrit ou signature dessinée, code de validation par e-mail), Mes demandes RH,
Contenu, Mail, Support IT et **l'Agent MyWebtel**. Voix off française (ElevenLabs, voix « Simon »), musique originale,
bruitages discrets, quelques mots-clés à l'écran (pas de sous-titres). Direction : `DIRECTION.md`.

Rendu final : `output/mywebtel_presentation.mp4`. Regénération complète : `mywebtel/make.sh <APERCU-MYWEBTEL.html>`.

## Vraie interface
Les écrans viennent de l'aperçu HTML généré par le PHP de la plateforme (archive « MYWEBTEL_fichiers_retrouves_PARTIEL »,
14/10/2026). `prep_ui.py` en extrait les écrans, coupe scripts et transitions et remplace les données de test par des
données de démonstration. Le résultat (`build/mywebtel/ui.json`) n'est **jamais versionné** : ce dépôt est public.
Le film charge chaque écran dans une iframe et ne fait que remplir les champs, cliquer et changer les états avec les
libellés réels du PHP (« Commencer ma journée », « Je pars en pause », « Signer le document »…).

| Écran | Source |
|---|---|
| Mon espace, Pointage, Mes congés, Mes absences, Mes documents, Mes demandes RH, Contenu | aperçu PHP, tel quel |
| Signature | page et fenêtre « Signer le document » réelles de l'aperçu, complétées avec les libellés du modèle IT11 (`signatures.php` : onglets « Nom manuscrit » / « Dessiner », code par e-mail valable 10 minutes, consentement) |
| Menu Mail et Support IT | routes et icônes réelles (`interface.php` IT11) |
| Contenu des pages Mail et Support IT | **composé** avec les composants de la plateforme (pas de rendu disponible) |
| Panneau de l'Agent MyWebtel | **composé** avec les composants de la plateforme (`console.php` absent de l'archive) |

## Chaîne
| Étape | Fichier | Sortie (`build/mywebtel/`) |
|---|---|---|
| Texte : `[id, texte affiché, texte envoyé à la voix]` (prononciations forcées : « scanné », « plu ») | `voice/script_v5.json` | |
| Voix « Simon » (ElevenLabs `eleven_multilingual_v2`, texte voisin pour une prosodie continue), segments en cache | `voice/eleven_gen.py` | `voice/<id>.mp3`, `voice/<id>.json` |
| Placement des segments sur la grille (100 BPM), respirations, mots datés au caractère près | `vo_eleven.py` | `vo.wav`, `timeline.json` |
| Logo Webtel vectorisé depuis l'image fournie (potrace) | `vectorize_logo.py` | `film/brand/webtel-logo.svg` |
| Musique composée en MIDI, rendue piste par piste (FluidSynth + MuseScore General) | `music.py` | `music.wav`, `music/` |
| Vraie interface : écrans de l'aperçu PHP préparés pour le film | `prep_ui.py` | `ui.json` (non versionné) |
| Film HTML piloté par le temps (`renderAt(t)`), lit `timeline.json` | `film/index.html`, `film/film.js` | |
| Rendu image par image (Chromium + ffmpeg) ; exporte aussi les repères des gestes | `render.js` | `video_silent.mp4`, `cues.json` |
| Bruitages synthétisés calés sur les gestes du film, ducking, loudness -16 LUFS | `sfx_mix.py` | `sfx.wav`, `mix.wav` |

`timeline.json` (mots datés) est la seule source des temps : le film (`film.js`) en dérive ses gestes (chaque clic tombe
sur le mot qui le nomme), la musique en tire ses mesures de logo, et les bruitages lisent les gestes exportés par le film
dans `cues.json`. Changer un segment de voix puis relancer `make.sh` recale tout.

L'ancienne voix locale (Kokoro, `script.py` + `vo.py`) reste disponible ; elle écrit le même `timeline.json`.

## Dépendances
- **Voix : abonnement ElevenLabs Starter au minimum** (les voix de la bibliothèque ne sont pas disponibles via l'API en
  gratuit ; sortie `mp3_44100_128`). La clé n'est jamais écrite dans le dépôt : elle est enregistrée comme secret réseau de
  l'environnement (en-tête `xi-api-key` vers `api.elevenlabs.io`) et injectée par le proxy. Ailleurs, remplacer
  `"proxy-injected"` dans `eleven_gen.py` par la lecture d'une variable d'environnement.
- Python : `pip install numpy scipy soundfile pillow mido`
- Système : `ffmpeg`, `fluidsynth`, `musescore-general-soundfont` (`/usr/share/sounds/sf3/MuseScore_General_Full.sf3`),
  `potrace`, `fonts-urw-base35` (police manuscrite Z003 de la signature)
- Node : `npm ci` dans `mywebtel/` (playwright-core) et un Chromium (`CHROMIUM=/chemin/vers/chrome` si besoin)
- Contrôle d'intelligibilité (optionnel) : `sherpa-onnx` et le modèle
  [sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2)

## Vérifier un passage
```bash
node mywebtel/render.js --stills 42.8,61,93.6        # images fixes -> build/mywebtel/stills/
python3 mywebtel/stills_sheet.py                     # planche des images fixes
node mywebtel/render.js --range 45 63                # passage -> build/mywebtel/preview_45_63.mp4
python3 mywebtel/voice/eleven_gen.py conges          # refaire une prise de voix (puis vo_eleven.py, music.py…)
```

## À valider avant diffusion
- Le panneau de l'Agent MyWebtel et le contenu des pages Mail et Support IT sont composés : les remplacer par les vrais
  écrans dès qu'ils sont disponibles (captures ou rendu HTML).
- La signature présentée suit le parcours du modèle IT11 ; le film ne revendique pas de valeur juridique particulière.
- Les données affichées sont fictives (collaboratrice « Aïssatou Ndiaye », code 482 913…).

Polices : Inter et Inter Display (`film/fonts/COPYRIGHT-Inter.txt`), Liberation Sans, aux chasses d'Arial comme l'application
(`film/fonts/COPYRIGHT-Liberation.txt`) ; toutes sous SIL Open Font License. Z003 (URW, police système) pour la signature.
