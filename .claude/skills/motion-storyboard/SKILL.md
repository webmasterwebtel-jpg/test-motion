---
name: motion-storyboard
description: Planifier un film de motion design en mesures avant de coder, avec un découpage en séquences converti en temps, en images et en repères de code, des contrôles de rythme (tenue par look, bursts trop longs, arc d'énergie, durée cible) et des gabarits de structure pour des formats de 15, 30 et 60 s. Contient aussi un contrôle de cohérence de la timeline écrite en double dans collage.py et audio_collage.py. Utilise ce skill dès qu'on propose, conçoit ou rallonge un film, une séquence ou une variante (teaser 15 s, version 30 s), qu'on change une durée ou un nombre de looks, qu'on remplace la musique, ou avant de modifier un temps dans collage.py ou audio_collage.py, et après, pour vérifier que l'image et le son sont toujours alignés.
---

# Storyboard en mesures

À 120 BPM, une mesure dure 2 s, soit un look posé. Planifier en mesures plutôt qu'en secondes donne un film qui respire
avec la musique, et rend évidents les problèmes de rythme avant d'écrire une ligne de code. Le plan sert aussi de
contrat avec l'utilisateur : on le valide avant de coder (voir `motion-direction`).

## 1. Écrire le brief
```bash
python3 .claude/skills/motion-storyboard/scripts/beat_sheet.py --example > build/brief.json   # le film actuel
```
Modifier le JSON : une entrée par séquence avec `bars` (fractions permises), `looks` (nombre de visuels), `type`
(`hold` posé, `burst` enchaînement rapide, `intro`, `outro`, `break`) et `energy` (1 à 5). Puis :
```bash
python3 .claude/skills/motion-storyboard/scripts/beat_sheet.py build/brief.json --plot build/review/timeline.png
```
Le tableau donne début, fin, durée, mesures, images et durée par look, avec une jauge d'énergie. Les contrôles :
- `✗` **blocage** : une tenue sous 1,3 s par look (trop rapide pour lire le produit), un burst de plus de 4 s,
  une énergie plate, un départ hors grille de croches, une durée différente de la cible ;
- `△` **à examiner** : une tenue sous 2 s (l'idéal du projet), trois séquences intenses de suite, un départ sur une
  croche (correct si voulu), un pic d'énergie en bout de film ;
- `·` rappel d'accroche : il faut quelque chose à l'écran dès l'image 0.
Le code de sortie vaut 1 s'il y a un blocage. Option `--code` : extraits à coller dans les deux fichiers.
Les seuils sont des règles du projet (`motion-direction`), pas des lois : on peut passer outre, mais en le disant.

## 2. Choisir une structure
`references/structures.md` propose des plans de 15, 30 et 60 s (accroche, montée, sommet, résolution) exprimés en
mesures. Les adapter au nombre de looks disponibles : le film actuel présente 24 looks en 60 s.

## 3. Garder image et son alignés (à chaque modification de temps)
```bash
python3 .claude/skills/motion-storyboard/scripts/timeline_check.py
```
Le script ne rend rien (environ 5 s). Il vérifie : (1) les constantes qui doivent être identiques dans `collage.py` et
`audio_collage.py`, (2) les repères musicaux `MARKS` par rapport aux sections de l'image, (3) que chacun des événements
visuels (entrées de la pile, plongées du zoom, bento, crans du carrousel, BOOM) a un bruitage dans la fenêtre
`-0,2 s / +0,4 s`. Il a été validé en cassant volontairement trois temps d'une copie du code : les trois ont été signalés.
Le code de sortie vaut 1 s'il y a une incohérence. Corriger **du côté qui n'a pas été mis à jour**, puis relancer.
Ce contrôle regarde le code : il ne dit pas si le son tombe *au bon instant* dans le mixage. Pour cela, voir
`motion-audio-sync` (`cue_check.py`) et `motion-review` (courbe de mouvement).

## Procédure complète d'un changement de timing
1. Brief modifié → `beat_sheet.py` sans blocage.
2. Modifier `collage.py` ET `audio_collage.py` (mêmes valeurs).
3. `timeline_check.py` → cohérent.
4. Rendu partiel (`motion-engine`), puis `motion-compare` avec `--expect` sur la plage touchée.
5. Si la durée totale change : mettre à jour `DURATION`, `A.DUR`, le tableau du `README.md` et `make.sh`.

## Fichiers
- `scripts/beat_sheet.py` : brief → timeline (`--example`, `--code`, `--plot`).
- `scripts/timeline_check.py` : cohérence image ↔ son sur le code (`--verbose`, `--before`, `--after`).
- `references/structures.md` : plans types en mesures et règles d'écriture d'un brief.
- `assets/beat-planner.html` : planificateur interactif (artefact publié, source dans le dépôt). Mêmes règles et mêmes messages que
  `beat_sheet.py` (comparés sur cinq briefs, résultats identiques) ; exporte et importe le brief JSON.
