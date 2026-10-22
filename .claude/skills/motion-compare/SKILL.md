---
name: motion-compare
description: Comparer deux rendus d'un même film (avant/après une modification) pour vérifier qu'un changement a bien produit l'effet voulu sans rien casser ailleurs. Le skill localise les plages d'images qui diffèrent, produit une planche A | B | écart amplifié, superpose les courbes d'énergie et compare tenues lisibles, loudness, crête vraie et accroche. Utilise ce skill après toute correction ou retouche d'un rendu (timing, son, couleur, effet), quand on te demande « qu'est-ce qui a changé ? », « est-ce mieux qu'avant ? », « compare les deux versions » ou « vérifie que je n'ai rien cassé », avant de remplacer un master dans output/, et à chaque fois qu'on itère sur un rendu final.
---

# Comparer deux versions

Une modification de timing ou d'effet a presque toujours des effets de bord : un décalage de 2 images en début de
section déplace tout ce qui suit, un changement de couleur d'un look touche aussi la mosaïque qui le réutilise.
Comme je ne vois pas la vidéo, je mesure l'écart entre l'avant et l'après au lieu de supposer que « ça va ».

## Protocole
1. **Avant de toucher au code**, figer l'état actuel :
   ```bash
   mkdir -p build/baseline && cp output/crochet_tiktok_60s.mp4 build/baseline/avant.mp4
   ```
   (`build/` n'est pas versionné : c'est le bon endroit pour les copies de travail.)
2. Modifier, puis rendre (`./make.sh` ou un segment, voir `motion-engine`).
3. Comparer en annonçant **où** on attend le changement :
   ```bash
   python3 .claude/skills/motion-compare/scripts/compare_versions.py build/baseline/avant.mp4 output/crochet_tiktok_60s.mp4 --expect 14:16
   ```
4. Lire le rapport :
   - **ATTENDU** : `changements HORS de la plage attendue` doit dire `aucun ✔`. Sinon, un effet de bord est à
     expliquer (et c'est souvent un décalage de timing qui s'est propagé, voir la règle « timeline en double »
     de `motion-engine`).
   - **plages attendues SANS changement visible** : la modification n'a rien produit à l'image. Vérifier que le
     bon fichier a été rendu (le cache de segments dépend du hash du code).
   - **RYTHME ET SON** : `↑ mieux` / `↓ moins bien` ne signale que les écarts de plus de 2 %. Un changement de tenues,
     de loudness ou de crête qui n'était pas voulu se voit ici.
5. Ouvrir la planche (`build/review/compare.png`) : colonnes A, B et écart ×3 (rouge = différence forte). Ça
   montre *quoi* a changé, pas seulement où. Puis `compare_energie.png` pour le rythme global.
6. Si seul le **son** a changé, l'image doit afficher 0 plage différente, et la différence se lit dans le loudness.
   Pour voir où : `motion_graph.py` sur les deux versions (`motion-review`) puis comparer la section synchro.

## Limites à connaître
- Les deux fichiers doivent avoir la même résolution et la même cadence (le script s'arrête sinon).
- L'écart est mesuré sur des images réduites à 120 px de large en niveaux de gris : un changement de teinte à luminance
  égale, ou un détail de quelques pixels, peut passer sous le seuil (0,5 %). Pour ces cas, lancer la planche avec
  `--times` sur l'instant concerné.
- Le grain papier est animé à 12 i/s : s'il change (graine différente), toute l'image diffère faiblement. Garder
  la même graine d'une version à l'autre.
- Si les durées diffèrent, la comparaison porte sur la durée commune et le script le signale.

## Fichiers
- `scripts/compare_versions.py` : le rapport texte, la planche `build/review/compare.png` et les courbes `compare_energie.png`.
  Options : `--times` (instants de la planche), `--expect a:b,c:d`, `--out`.
