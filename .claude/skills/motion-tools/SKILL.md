---
name: motion-tools
description: Choisir et utiliser un autre moteur que le rendu Python image par image du projet. Couvre Remotion (React vers vidéo, gabarit 9:16 testé dans ce conteneur), Blender piloté par script (vraie 3D, éclairage, flou de mouvement physique), Lottie (animations vectorielles légères pour le web ou les apps) et ffmpeg seul. Utilise ce skill quand une demande dépasse ce que Pillow/numpy fait bien (vraie 3D, rendu photoréaliste, typographie animée riche, vitesse de rendu, animation interactive ou web, export After Effects/Lottie), quand on parle de Remotion, Blender, After Effects, Lottie, Rive, Manim ou de changer d'outil, ou quand un rendu devient trop lent.
---

# Autres moteurs de motion design

Le moteur maison (Python, Pillow, numpy) excelle pour le **collage 2D maîtrisé à l'image près**. Il
devient le mauvais outil quand il faut une vraie 3D, beaucoup de texte animé, des vidéos imbriquées ou
une sortie web. Changer de moteur coûte cher, alors on ne le propose qu'avec une raison concrète, et on
réutilise toujours les skills de relecture (`motion-review`) et de livraison (`motion-delivery`),
qui fonctionnent sur n'importe quel .mp4.

## Choisir

| Besoin | Outil | Pourquoi |
|---|---|---|
| Collage 2D, stickers, fils, contrôle à l'image près (le film actuel) | **moteur Python du projet** | déjà là, rendu déterministe, aucun coût de licence |
| Typographie animée, mises en page CSS (grilles, flex), templates à décliner en série, sous-titres | **Remotion** | React et CSS, `spring()` et `interpolate()` intégrés, rendu en parallèle, paramètres par JSON |
| Vraie 3D (tissu, lumière, ombres, profondeur de champ), produit photoréaliste | **Blender** (script `bpy`) | moteur physique, Cycles/EEVEE, vrai flou de mouvement |
| Animation vectorielle légère, en boucle, pour un site ou une app | **Lottie** (ou Rive pour l'interactif) | quelques Ko, net à toute taille |
| Assemblage, découpe, recadrage, overlays simples, sous-titres incrustés | **ffmpeg** seul | aucun code de rendu |
| Animation mathématique ou pédagogique (graphes, équations) | Manim | fait pour ça |

Signaux qu'il faut changer : un rendu complet de plus de 30 min, du code de 3D « bricolée » (perspective
à la main sur des plans 2D), plus de 20 % du code consacré au texte, ou une demande de déclinaisons
en série (10 variantes de produit, de langue ou de format).

## Remotion (testé)
Le gabarit est dans `assets/remotion-template/` (9:16, 30 i/s, 120 BPM, un look par mesure, entrée
en ressort, tenue flottante, sortie accélérée). Il a été rendu dans ce conteneur et passe `check_delivery.py`.
```bash
cp -r .claude/skills/motion-tools/assets/remotion-template remotion && cd remotion
cp ../build/cutouts/article_02.png public/look_a.png && cp ../build/cutouts/article_05.png public/look_b.png
npm install
export REMOTION_CHROMIUM=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell  # conteneur cloud
npm run render          # -> out/film.mp4 ; npm run still pour une image ; npm run studio pour l'aperçu
```
Mode d'emploi, API utile et pièges : `references/remotion.md`. **Licence** : Remotion est gratuit pour
les particuliers et les petites entreprises, mais payant au-delà. Il faut le signaler à l'utilisateur avant
d'en faire l'outil d'un projet commercial.

## Blender (non testé ici)
Blender n'est pas installé dans ce conteneur, et le module `bpy` de PyPI n'existe que pour certaines
versions de Python. Le guide `references/blender.md` donne un script de base (scène 9:16, plan-sticker
texturé, caméra, lumière, keyframes, rendu EEVEE) à lancer avec `blender -b -P script.py`.
On le teste d'abord sur 10 images (`--frame-end`) avant tout rendu long.

## Lottie et ffmpeg
Voir `references/lottie-ffmpeg.md` : quand exporter en Lottie, les limites (pas d'effets raster, pas
de flou), et une liste de commandes ffmpeg utiles (montage, recadrage, vitesse, boucle, GIF, incrustation).

## Toujours, quel que soit le moteur
1. Garder la grille BPM et les règles de `motion-timing` (durées, easings, tenues).
2. Respecter les préférences de `motion-direction`.
3. Relire le rendu avec `motion-review` (planche, courbe de mouvement, synchro).
4. Livrer avec `motion-delivery` (format, loudness, zones sûres).
