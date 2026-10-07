---
name: motion-audio-sync
description: Caler une animation sur la musique et les bruitages. Le skill détecte le tempo, les temps, les premiers temps de mesure, les attaques et la structure (drops, breaks, silences) d'une piste quelconque. Il relève aussi les bruitages directement dans le code et les compare aux événements visuels, avec des règles de sound design. Utilise ce skill dès qu'il faut remplacer ou ajouter une musique (piste sous licence, autre BPM), caler des transitions sur le beat, ajouter, déplacer ou corriger un bruitage, vérifier qu'un son tombe au bon moment, ou quand on te dit « le son est décalé », « ça ne tombe pas sur le temps » ou « mets cette musique ».
---

# Synchro image ↔ son

Le film est calé sur une grille de 120 BPM écrite à la main dans le code (image ET son). Ce skill sert à
**mesurer** au lieu de supposer : le tempo réel d'une musique, l'instant réel de chaque bruitage et
l'écart avec l'image, en images.

## Outils

**1. Analyser une musique** (wav, mp3 ou vidéo) :
```bash
python3 .claude/skills/motion-audio-sync/scripts/beat_grid.py musique.mp3 --fps 30
python3 .claude/skills/motion-audio-sync/scripts/beat_grid.py musique.mp3 --bpm 124   # tempo imposé
```
Sorties : le tempo, le premier temps, le premier temps fort de mesure (avec une confiance), la dérive
temps/images, les attaques fortes, un tableau par mesure (énergie, ruptures DROP/BREAK/silence) et un
JSON (`beats`, `downbeats`, `beat_frames`, `bars`, `onsets`).
Validé sur des pistes de test à 97, 120, 128 et 140 BPM (tempo exact, phase à ±10 ms près, soit moins d’un tiers d’image).
Quand la confiance sur le temps fort est faible (kick sur tous les temps), il faut confirmer avec la structure : les
ruptures tombent presque toujours sur un premier temps de phrase (4 ou 8 mesures).

**2. Relever les bruitages depuis le code et les comparer à l'image** :
```bash
python3 .claude/skills/motion-review/scripts/motion_graph.py output/film.mp4 --bpm 120   # produit le JSON d'événements
python3 .claude/skills/motion-audio-sync/scripts/cue_check.py --events build/review/motion_00.00_60.00.json --from 4 --to 16
```
Chaque `add(...)` de `audio_collage.sfx()` est listé avec sa ligne de code, son attaque réelle
(10 % du max), son pic et l'événement visuel le plus proche (départ, pic ou contact), écart en images.
`ok` = ±1 image, `!!` = à examiner. Tout `!!` n'est pas une erreur : un ruban qui se pose 2 images
après la claque est voulu, par exemple. Il faut juger la nature du son :
- **claque, impact, clic** : l'attaque doit tomber sur le **contact** (±1 image) ;
- **whoosh** : son **pic** doit précéder ou coïncider avec le pic de vitesse ;
- **riser, montée** : il doit finir **sur** l'impact qu'il prépare, jamais après ;
- **pop, bloup** : il tombe sur l'ouverture visible (le premier tiers de l'iris).

## Remplacer la musique par une piste sous licence

1. `beat_grid.py piste.mp3` → BPM, premier temps fort, structure.
2. **Même BPM (120)** : il suffit d'aligner le premier temps fort de la piste sur la grille du film. Couper
   le début de la piste (`ffmpeg -ss <décalage>`) pour qu'une mesure commence à 4,0 s (démarrage de la
   pile), puis vérifier que les DROP/BREAK de la piste tombent près des repères `MARKS` du film
   (build 22, cut 28, drop 35, climax 47, end 55). Sinon, préférer **déplacer la musique** (décalage par mesures
   entières) plutôt que l'image.
3. **Autre BPM** : les temps du film sont des secondes écrites en dur (PILE, ZOOM, BENTO, C0…), pas
   des multiples de `BEAT`. Deux options :
   - BPM proche (±5 %) : faire un time-stretch de la musique vers 120 (`ffmpeg -af atempo=120/BPM`, inaudible sous ±5 %) ;
   - BPM éloigné : convertir les temps du film en temps musicaux (`t = mesure * 4 * beat`) dans
     `collage.py` **et** `audio_collage.py`, puis vérifier toutes les frontières de sections.
4. Remixer : la musique reste ≈ 11 dB sous les bruitages (préférence du projet), puis mux et loudness
   (voir `motion-delivery`), et relecture avec `motion-review`.

## Règles de sound design (détails dans `references/sfx.md`)
- Un son par **contact** important. Tout ce qui bouge n'a pas besoin de son : réserver les sons aux
  changements significatifs, sinon ils deviennent du bruit.
- Le whoosh démarre 2 à 5 images avant le mouvement et culmine sur le pic de vitesse ; la claque tombe au contact.
- Superposer pour donner du poids : grave (corps) + médium (matière) + aigu (détail), avec un léger pan qui suit le mouvement.
- Un silence d'un demi-temps avant un BOOM. Couper aussi les queues de réverbe dans le silence.
- Varier les sons répétés (hauteur et gain aléatoires de ±5–10 %) pour éviter l'effet « mitraillette ».
- Le **niveau crête** affiché par `cue_check.py` n'est pas le volume perçu : un clic de 5 ms à −2 dB crête
  peut rester inaudible dans le mix. Vérifier dans `motion_graph.py` qu'il produit bien une attaque.

## Fichiers
- `scripts/beat_grid.py` : tempo, phase, temps forts, structure et JSON de grille.
- `scripts/cue_check.py` : relevé des bruitages par instrumentation de `add()` et rapprochement avec l'image.
- `references/sfx.md` : la bibliothèque de sons du projet (`audio.py`, `audio_collage.py`) et les recettes.
