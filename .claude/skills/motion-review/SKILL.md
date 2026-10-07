---
name: motion-review
description: Relire une animation ou une vidéo de motion design sans pouvoir la regarder, avec des planches-contacts, une pelure d'oignon et une courbe d'énergie de mouvement superposée aux attaques du son. Les outils mesurent les tenues, les temps morts, les surcharges et la synchro image/son. Utilise ce skill dès qu'il faut juger, vérifier, critiquer ou améliorer le rythme, le timing, la lisibilité ou la synchro d'une vidéo (.mp4, .mov, .webm), d'un rendu ou d'un passage. Cela vaut avant de livrer, après chaque rendu et quand on te dit « c'est trop rapide », « ça manque de punch », « le son est décalé » ou « regarde la vidéo ». Ne te contente jamais de 2 ou 3 images fixes pour juger du mouvement.
---

# Relire un motion design

Je ne vois pas les vidéos. Les images fixes isolées mentent sur le mouvement : une transition de
0,3 s peut sembler parfaite sur une image et être illisible en lecture. Ce skill transforme le
temps en images et en chiffres que je peux lire. Les scripts n'ont besoin que de `ffmpeg`,
`numpy`, `scipy` et `Pillow`. Ils écrivent par défaut dans `build/review/`.

## Méthode (dans cet ordre)

1. **Vue d'ensemble chiffrée** : lancer la courbe de mouvement sur tout le film.
   ```bash
   python3 .claude/skills/motion-review/scripts/motion_graph.py output/film.mp4 --bpm 120 \
       --marks "4:Pile,16:Zoom,28:Mosaïque,35:Bento,39:Carrousel,55:Final"
   ```
   Lire le rapport texte d'abord, puis ouvrir le PNG (Read) :
   - **TENUES** : passages où l'image est posée et lisible. Ce sont les seuls moments où le
     spectateur *voit* vraiment le produit. Une tenue de moins de ~1 s sur un visuel important
     est trop courte (voir `motion-direction` pour les préférences du projet).
   - **plus long passage sans tenue** : au-delà de ~6 à 8 s sans repos, le regard fatigue.
   - **SURCHARGES** : de l'agitation forte et continue pendant 2,5 s ou plus. C'est rarement voulu.
   - **ÉVÉNEMENTS** : chaque bouffée de mouvement avec son départ, son pic de vitesse et son
     **contact** (l'instant où ça s'arrête net). Une ligne `!` signale un son qui ne tombe ni sur
     le départ, ni sur le pic, ni sur le contact. Les **arrêts nets sans son** sont les impacts
     auxquels un bruitage donnerait du poids.
   - **calage sur la grille** : la part des contacts qui tombent sur un temps (±1,5 image).
2. **Planche-contact** des passages suspects, au pas d'un temps ou d'un demi-temps :
   ```bash
   python3 .claude/skills/motion-review/scripts/contact_sheet.py output/film.mp4 --start 16 --end 20 --step 0.25 --bpm 120
   ```
   Vérifier la lisibilité (sujet entier, cadré, assez grand), la continuité des couleurs et des
   formes d'une vignette à l'autre, ce qui change à chaque temps fort, les vignettes « vides » et
   les doublons.
3. **Pelure d'oignon** sur une transition précise (0,2 à 0,6 s, idéalement un seul élément qui
   bouge, `--roi` pour l'isoler) :
   ```bash
   python3 .claude/skills/motion-review/scripts/onion_skin.py output/film.mp4 --start 3.95 --end 4.35 --n 8 --roi 0,0.1,1,0.9
   ```
   Elle montre les arcs (une trajectoire en ligne droite paraît mécanique) et l'**espacement**
   des positions successives : serré au début ou à la fin, c'est un easing ; régulier, c'est
   linéaire et ça sonne faux.
4. **Grille de relecture** : passer `references/checklist.md` sur chaque séquence et noter ce
   qui ne va pas avec le timecode.
5. **Rapport** : présenter les constats sous la forme `temps → problème → correction proposée`,
   en joignant le PNG de la courbe et les planches utiles. Distinguer ce qui est mesuré (les
   chiffres des scripts) de ce qui relève du jugement.

Pour relire un passage **avant** de rendre tout le film, rendre directement des images depuis le
code avec `motion-engine` (`render_sheet.py`) : c'est beaucoup plus rapide qu'un rendu complet.

## Lire les chiffres avec discernement

- L'énergie se mesure en % de la plage 0–255, sur une image réduite à 120 px de large. Repères
  pour ce projet : moins de 0,8 % (écart flouté à 0,2 s), l'image est posée ; 3 à 15 %, c'est
  une transition ; plus de 25 %, c'est une coupe ou un flash.
- Le grain papier et le tremblé stop-motion font un « bruit de fond » d'environ 1 % image à image.
  C'est pour ça que les tenues sont mesurées sur des images floutées, à 0,2 s d'écart.
- La synchro est mesurée sur le **mixage final** : un kick de musique peut masquer un bruitage
  faible. Si un événement est marqué `!` alors qu'un bruitage existe dans le code, c'est souvent
  qu'il est trop faible, trop mou à l'attaque (whoosh) ou décalé. Les trois méritent d'être corrigés.
- Le décodage AAC peut avancer une attaque d'une image juste après un silence. Une tolérance
  de ±1 image est normale.
- Les seuils sont en tête de `motion_graph.py` (`HOLD_THR`, `BUSY_THR`, `HIT_THR`, `SYNC_WIN`).
  Pour un autre style (très calme ou très nerveux), les ajuster et le dire dans le rapport.

## Fichiers

- `scripts/motion_graph.py` : la courbe d'énergie, le rapport et le JSON (`--start`, `--end`, `--bpm`, `--offset`, `--marks`, `--row`).
- `scripts/contact_sheet.py` : la planche annotée avec le temps, le numéro d'image et la mesure.temps.
- `scripts/onion_skin.py` : la pelure d'oignon, la trajectoire et l'espacement.
- `scripts/_common.py` : le décodage ffmpeg, l'enveloppe d'attaques par image et la police.
- `references/checklist.md` : la grille de relecture (12 principes, lisibilité, son, plateforme).
