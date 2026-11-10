# MyWebtel : film de présentation

Film de 1 min 48 (1920×1080, 30 i/s) qui présente MyWebtel, l'espace collaborateur de Webtel, **sur sa vraie interface** :
pointage (arrivée, pause, retour, fin de journée), congés (droits ouverts après 1 an d'ancienneté), Mes absences,
**signature de documents** (nom manuscrit ou signature dessinée, code de validation par e-mail), Mes demandes RH,
Contenu, Mail, Support IT et **l'Agent MyWebtel**. Voix off française (ElevenLabs eleven_v4, voix « Simon »), musique
originale, bruitages discrets, quelques mots clés à l'écran (pas de sous-titres). Direction : `DIRECTION.md`.

Rendu final : `output/mywebtel_presentation.mp4`. Regénération complète : `mywebtel/make.sh <APERCU-MYWEBTEL.html>`.

## Le film (V6)
Une seule caméra dans un monde en 3D, dans l'esprit des trois références de l'utilisateur :
1. **Nuit** : les démarches flottent dans le noir, l'heure s'emballe, des fils de lumière les rassemblent dans un anneau ;
   le logo naît dans l'anneau sur le premier temps et la caméra le traverse.
2. **Le monde MyWebtel** : les vraies pages sont posées comme les quartiers d'un plan ; la caméra vole de page en page,
   le composant utile sort de sa page en relief et on s'en sert (clics, saisie, états réels).
3. **Fin** : la nuit retombe, le plan s'illumine, le logo revient dans l'anneau.

## Vraie interface
Les écrans viennent de l'aperçu HTML généré par le PHP de la plateforme (archive « MYWEBTEL_fichiers_retrouves_PARTIEL »,
14/10/2026). `prep_ui.py` en extrait les écrans, coupe scripts et transitions et remplace les données de test par des
données de démonstration. Le résultat (`build/mywebtel/ui.json`) n'est **jamais versionné** : ce dépôt est public.
Chaque page est une iframe ; un composant « sorti » est une seconde copie de la même page, découpée sur ce composant, qui
reçoit exactement les mêmes états à chaque image.

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
| Texte : `[id, texte affiché, texte envoyé à la voix]` (graphies qui forcent la prononciation, sans liaisons fautives) | `voice/script_v6.json` | |
| Voix « Simon » (ElevenLabs `eleven_v4`, texte voisin pour une prosodie continue), plusieurs prises par phrase | `voice/eleven_gen6.py` | `voice6/t<prise>/<id>.mp3`, `.json` |
| Prise retenue pour chaque phrase (après contrôle, voir plus bas) | `voice/picks_v6.json` | |
| Placement des segments sur la grille (100 BPM), respirations, mots datés au caractère près | `vo_eleven.py` | `vo.wav`, `timeline.json` |
| Logo Webtel vectorisé (potrace) ; variantes blanche (nuit) et bleu profond (relief) | `vectorize_logo.py` | `film/brand/*.svg` |
| Musique composée en MIDI (FluidSynth + MuseScore General) + nappe synthétisée + réverbération | `music.py`, `audio_fx.py` | `music.wav`, `music/` |
| Vraie interface : écrans de l'aperçu PHP préparés pour le film | `prep_ui.py` | `ui.json` (non versionné) |
| Film HTML piloté par le temps (`renderAt(t)`) : moteur 3D, interface, mise en scène | `film/engine.js`, `film/ui.js`, `film/story.js` | |
| Rendu image par image (Chromium + ffmpeg) ; exporte aussi les repères des gestes | `render.js` | `video_silent.mp4`, `cues.json` |
| Bruitages synthétisés calés sur les gestes du film, réverbération, ducking, loudness -16 LUFS | `sfx_mix.py`, `audio_fx.py` | `sfx.wav`, `mix.wav` |

`timeline.json` (mots datés) est la seule source des temps : le film en dérive ses gestes (chaque clic tombe sur le mot
qui le nomme, les logos sur un premier temps), la musique ses sections, et les bruitages lisent les gestes exportés par
le film dans `cues.json`. Changer une prise puis relancer `make.sh` recale tout.

### Le moteur 3D (`film/engine.js`)
Repère en pixels, y vers le bas (le sol est le plan y = 0). Une caméra « orbite » (cible, distance, lacet, tangage,
roulis, focale) produit une matrice de vue ; chaque objet du monde reçoit sa propre matrice 4×4 (`matrix3d`). Les mêmes
matrices servent à projeter des points à l'écran : le sol, les lumières, les faisceaux et le curseur sont dessinés sur des
canvas exactement calés sur les éléments DOM en 3D.

## Contrôle de la voix
La prononciation se mesure : pour chaque prise, deux transcriptions indépendantes (Whisper small, Parakeet TDT), la
confiance mot à mot de Parakeet (log-probabilités), le suivi des formants (LPC) des voyelles sensibles (« tèl » de
MyWebtel, « mèl ») et l'énergie des sifflantes (« t'as plu qu'à » sans « s »). Les liaisons fautives que le modèle
faisait (« tu déclares‿z‿avec »…) sont supprimées dans le texte envoyé, sans changer le son voulu.

## Dépendances
- **Voix : abonnement ElevenLabs Starter au minimum** (voix de la bibliothèque par l'API ; sortie `mp3_44100_128`).
  La clé n'est jamais écrite dans le dépôt : elle est enregistrée comme secret réseau de l'environnement (en-tête
  `xi-api-key` vers `api.elevenlabs.io`) et injectée par le proxy.
- Python : `pip install numpy scipy soundfile pillow mido`
- Système : `ffmpeg`, `fluidsynth`, `musescore-general-soundfont` (`/usr/share/sounds/sf3/MuseScore_General_Full.sf3`),
  `potrace`, `fonts-urw-base35` (police manuscrite Z003 de la signature)
- Node : `npm ci` dans `mywebtel/` (playwright-core) et un Chromium (`CHROMIUM=/chemin/vers/chrome` si besoin)
- Contrôle de la voix (optionnel) : `sherpa-onnx` et les modèles
  [Parakeet TDT 0.6b v3](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8.tar.bz2)
  et [Whisper small](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2)

## Vérifier un passage
```bash
node mywebtel/render.js --stills 21.6,51.8,95             # images fixes -> build/mywebtel/stills/
python3 mywebtel/stills_sheet.py                         # planche des images fixes
node mywebtel/render.js --range 45 62                    # passage -> build/mywebtel/preview_45_62.mp4
python3 mywebtel/voice/eleven_gen6.py --takes 4 conges   # une prise de plus d'une phrase (puis picks_v6.json, vo_eleven.py…)
```

## À valider avant diffusion
- Le panneau de l'Agent MyWebtel et le contenu des pages Mail et Support IT sont composés : les remplacer par les vrais
  écrans dès qu'ils sont disponibles (captures ou rendu HTML).
- La signature présentée suit le parcours du modèle IT11 ; le film ne revendique pas de valeur juridique particulière.
- Les données affichées sont fictives (collaboratrice « Aïssatou Ndiaye », code 482 913…).

Polices : Inter et Inter Display (`film/fonts/COPYRIGHT-Inter.txt`), Liberation Sans, aux chasses d'Arial comme l'application
(`film/fonts/COPYRIGHT-Liberation.txt`) ; toutes sous SIL Open Font License. Z003 (URW, police système) pour la signature.
