---
name: motion-engine
description: Mode d'emploi du moteur de motion design Python de ce dépôt (motion/render.py, motion/collage.py, motion/audio*.py, make.sh). Il couvre l'API de placement 2D/3D, les fils de laine, les stickers, les effets caméra, le flou de mouvement, les sections, les bruitages synchronisés, les rendus partiels, les pièges et les recettes. Utilise ce skill dès que tu modifies, débogues, accélères ou étends le film, ajoutes une séquence, une transition, un effet ou un bruitage, ou veux rendre quelques images pour vérifier un changement, même si la demande ne cite pas les fichiers. Lis-le avant de relire les ~3 000 lignes du moteur.
---

# Moteur de rendu du projet

Le film est une **fonction pure du temps** : `compose(t)` dessine l'image à l'instant `t`
avec Pillow et numpy, puis `render_frame(n)` ajoute le flou de mouvement et le grain. ffmpeg
encode le tout, et la bande-son est synthétisée à part, sur la même grille de 120 BPM.

```
assets/articles/*.jpg ─ prep.py ─▶ build/cutouts/*.png
                                       │
motion/collage.py (+ render.py) ───────┴─▶ build/collage_silent.mp4 ┐
motion/audio_collage.py (+ audio.py) ─▶ build/audio/collage_mix.wav ┴─ make.sh ─▶ output/*.mp4
```

L'API complète (signatures, paramètres, clés `fx`) est dans `references/api.md`. Lis la section utile
plutôt que le code source.

## Boucle de travail rapide

1. Modifier le code.
2. **Rendre seulement les images utiles** directement depuis le code :
   ```bash
   python3 .claude/skills/motion-engine/scripts/render_sheet.py --range 5.9 6.4 0.0333 --scale 0.15
   python3 .claude/skills/motion-engine/scripts/render_sheet.py --times 2.5 17.6 38.5 --scale 0.4 --frames build/review/frames
   ```
   Il faut compter environ 1,5 s par image sur 4 cœurs. Le flou de mouvement et le grain sont inclus.
   Si `build/cutouts/` est vide, lancer d'abord `python3 motion/prep.py` (environ 25 s).
3. Une fois le passage satisfaisant, faire l'aperçu vidéo du passage, `python3 motion/collage.py --range 4 8`
   (muet, écrit dans `build/collage_segments/<hash>/seg_004.0_008.0.mp4`), puis le relire avec `motion-review`.
4. Faire le rendu complet avec `./make.sh` (prep, audio, image, mux et loudnorm). Les segments de 5 s sont
   mis en cache par hash du code : seul le code modifié est recalculé, et une interruption reprend là où elle s'est arrêtée.

## Règles qui évitent les bugs

- **La timeline existe en double.** Les temps de `collage.py` (PILE, ZOOM, BENTO, CAR, C0, CSTEP,
  CEND, FIN_SHIFT…) sont recopiés dans `audio_collage.py` (PILE, ZOOM, MARKS, CAR0…). Toute
  modification de timing se fait **dans les deux fichiers**, puis se vérifie avec `motion_graph.py`
  (section synchro). C'est la cause n°1 des désynchronisations.
- **Le son d'un impact se cale sur l'instant où l'image se pose, pas sur le début du mouvement.**
  Une entrée combine souvent plusieurs canaux (échelle `out_back`, rotation `out_expo`…), et elle
  n'est « posée » que quand **tous** ont atteint leur cible. Repères : `out_back(s=1.7)` passe la
  cible à 37 % de sa durée (46 % pour s=1.2), `out_expo` arrive à 97 % de la cible à mi-durée, et
  `in_cubic` (chute) arrive pile à la fin. Exemple mesuré : sur la « spin » de 6,0 s, la claque à
  `ta + 0.1` tombe pendant que le sticker tourne encore, flou. Elle devrait tomber vers `ta + 0.2`.
- **Fonction pure** : aucun état global modifié dans une section, et un hasard toujours seedé
  (`random.Random(seed)`, `jitter`). Sinon le flou de mouvement et le rendu parallèle produisent des
  images incohérentes.
- **Caméra** : multiplier ou ajouter `fx["cam_scale"]`, `fx["cam_dx"]` et `fx["cam_dy"]`, ne jamais les écraser.
  Ce qui doit rester fixe à l'écran (iris, incrustation) passe par `fx["post"]`.
- **Frontières de sections** : vérifier `t = fin - 1/30` et `t = fin` sur une planche au pas
  d'une image. Les sauts d'une image (pops) y naissent.
- **Caches** : `lru_cache` uniquement sur des arguments discrets (indices, tailles entières), jamais
  sur `t`. Le cache de segments ne voit que `collage.py` et `render.py`. Si les visuels,
  `prep.py` ou les polices changent, supprimer `build/collage_segments/`.
- **Performance** : passer `key=` à `place` ; `mb` multiplie le coût, donc ne le mettre que pendant les
  mouvements rapides ; `swayed_img` coûte cher ; on peut dessiner les petits éléments à 2× puis réduire
  (`LANCZOS`), comme le font `shape` et `ball`.
- **Zone sûre** : le contenu important reste entre y ≈ 210 et 1610 et à gauche de x ≈ 940 (voir `motion-delivery`).

## Recettes

**Entrée d'un élément sur le temps fort `tb`**
```python
p = seg(t, tb, tb + 0.34)
sticker(c, i, s=CS * lerp(0.55, 1.0, out_back(p, 1.5)), rot=-12 * (1 - out_cubic(p)), alpha=clamp01(p * 5))
if p < 0.6: fx["mb"] = 4
fx["punch"] += 0.025 * decay(t, tb + 0.2, 11)           # au contact, pas au départ
```
Dans `audio_collage.sfx()` : `add(b, whoosh(0.3, 600, 5000, 0.6), tb - 0.08, 0.5)` puis
`add(b, paper_slap(), tb + 0.2, 0.85)`.

**Tenue vivante** (le visuel reste lisible mais pas figé)
```python
fl = math.sin((t - st) * 2.2)
sticker(c, i, s=CS * (1 + 0.02 * seg(t, st, z0)), cy=CY + 8 * fl, rot=1.2 * fl)
```

**Nouvelle séquence** : écrire `sec_nom(c, t, fx)` en temps absolus (ou internes + décalage),
l'ajouter à `SECTIONS` avec un léger chevauchement si une transition doit croiser la précédente,
ajouter ses bruitages dans `audio_collage.py`, mettre à jour le tableau du `README.md`, puis rendre
la planche et relire.

**Stagger (décalage en cascade)** : `seg(t, tb + 0.045 * j, tb + 0.045 * j + 0.5)` pour l'élément `j`.
Les motifs de délai de la mosaïque (`_delay` : radial, diag, rows, random, spiral) sont réutilisables.
