---
name: motion-captions
description: Ajouter des sous-titres, une accroche ou du texte incrusté à une vidéo verticale, avec génération SRT et ASS depuis une liste de cues, placement dans la zone sûre TikTok/Reels/Shorts, retours à la ligne mesurés sur le vrai rendu, contrôle de lisibilité (durée, mots par seconde, 2 lignes maximum) et incrustation ffmpeg avec la police du projet. Utilise ce skill dès qu'on demande du texte à l'écran, des sous-titres, une voix off sous-titrée, une accroche, une légende ou une version sous-titrée, et avant d'incruster quoi que ce soit dans une vidéo. Le film actuel est volontairement sans texte, donc n'ajoute du texte que sur demande explicite.
---

# Sous-titres et texte incrusté

**Préférence du projet** : le film « Crochet Pop Collage » n'a ni voix ni texte (voir `motion-direction`). Ce skill sert pour
une variante où du texte est explicitement demandé. Sans demande, on n'en ajoute pas.

## Procédure
1. **Écrire les cues** en JSON, en secondes (utiliser `motion-storyboard` pour convertir mesures et secondes) :
   ```json
   [{"start": 4.0, "end": 6.0, "text": "Un look par mesure"},
    {"start": 6.0, "end": 8.5, "text": "Chaque maille compte"}]
   ```
2. **Générer et contrôler** :
   ```bash
   python3 .claude/skills/motion-captions/scripts/captions.py build cues.json --out build/captions/demo
   ```
   Le script écrit `demo.srt` et `demo.ass` et signale (`✗`, code de sortie 1) : une cue de moins de 1 s, un texte trop long
   pour sa durée (0,5 s + 0,3 s par mot), plus de 17 caractères/s (repère courant des sous-titres, pas une norme),
   plus de 2 lignes, un chevauchement, un texte qui descend dans la zone masquée par l'interface.
3. **Incruster** (image réencodée, son copié) :
   ```bash
   python3 .claude/skills/motion-captions/scripts/captions.py burn output/film.mp4 build/captions/demo.ass --out build/captions/film_sub.mp4
   ```
   `--start` et `--end` limitent l'extrait ; les cues gardent leur temps d'origine.
4. **Relire** : planche aux instants des cues (`motion-review`), zones sûres (`motion-delivery`), contraste (`motion-accessibility`).

## Pièges évités par l'outil (tous rencontrés pendant les tests)
- **Nom de police** : libass ne signale aucune erreur si le nom est inexact, il retombe sur une autre police (ici Inter).
  Les polices du projet déclarent la famille « Montserrat Thin » pour tous les poids : le gras s'appelle
  « Montserrat Thin Black ». L'outil déduit le nom du fichier (`--font-file`) et l'affiche dans son rapport. Si on
  change de police, vérifier visuellement la première incrustation.
- **Taille de police** : la taille ASS n'est pas la taille PIL ou CSS : le rendu est environ 0,64 fois plus petit pour
  Montserrat. L'outil mesure ce facteur en rendant une ligne de test, puis s'en sert pour les retours à la ligne
  (écart mesuré de 0,3 % entre la largeur prédite et la largeur rendue). La taille par défaut est 88.
- **Horodatage** : `-ss` avant `-i` remet les horodatages à zéro et décale tous les sous-titres ; `burn` place `-ss`
  côté sortie, ce qui garde les temps d'origine (vérifié sur des images extraites de l'extrait).

## Mise en page
- **Zone** : marges gauche 120, droite 192, bas à 700 px du bord (juste au-dessus de la zone d'interface), soit une largeur
  utile de 768 px. Valeurs de `motion-delivery/references/platforms.md`.
- **Style** : blanc `#FFFFFF`, contour `#111111` de 6 px, ombre légère, entrée en « pop » (échelle 85 → 100 % en 0,16 s) avec
  fondu de 90 ms. `--anim fade` pour un fondu seul, `--color` et `--outline-color` pour changer.
- **Contenu** : phrases courtes, un message par cue, pas de ponctuation lourde. Le texte arrive 0,1 à 0,2 s après l'image qu'il
  commente et part avant elle (`motion-timing`).
- **Accessibilité** : le contour garantit le contraste sur n'importe quel fond. Sans contour, vérifier avec
  `colorblind.py contrast`. Les jaunes et oranges du projet sont insuffisants en texte sur fond clair.

## Fichiers
- `scripts/captions.py` : `build` (cues → SRT + ASS + contrôles) et `burn` (incrustation).
- `.srt` : utile si une plateforme accepte un fichier de sous-titres séparé (à vérifier plateforme par plateforme). L'incrustation `.ass`
  reste la seule méthode qui garantit le rendu partout.
