---
name: motion-accessibility
description: Contrôler l'accessibilité d'une vidéo de motion design, avec la détection des flashs à risque photosensible (critère WCAG 2.3.1, y compris les flashs rouges), la simulation du daltonisme (protanopie, deutéranopie, tritanopie) et du niveau de gris, la distance entre couleurs d'une palette et le contraste texte/fond. Utilise ce skill avant toute livraison ou publication, et dès qu'une séquence contient des flashs, un stroboscope, des changements de luminosité rapides, des couleurs qui doivent se distinguer ou du texte, ou si on parle d'accessibilité, de daltonisme, d'épilepsie photosensible, de contraste, de lisibilité sans le son ou de mouvement qui donne mal au cœur, même si la demande ne cite pas ces mots.
---

# Accessibilité d'un motion design

Le film comporte beaucoup de flashs, de coupes, de zooms et de couleurs vives. Ce sont ses qualités, mais ils
touchent aussi un public vulnérable (épilepsie photosensible, daltonisme, sensibilité au mouvement). Le contrôle
est rapide et automatique, donc il se fait à chaque rendu final, avant `motion-delivery`.

## 1. Flashs (le point qui peut faire un vrai tort)
```bash
python3 .claude/skills/motion-accessibility/scripts/flash_check.py output/film.mp4 --plot build/review/flash.png
```
Le script suit la luminance de 144 blocs (9×16) et compte les flashs (deux changements opposés d'au moins 10 % de
luminance, l'état sombre sous 0,80) dans une fenêtre glissante d'une seconde. Il signale un passage **à risque**
si plus de 3 flashs/s touchent plus de 1/16 de l'image (valeur prudente pour un écran de téléphone, plus stricte
que la règle des 25 % de WCAG), et traite à part les **flashs rouges saturés**, plus dangereux.
- Verdict `À CORRIGER` : réduire le contraste de l'effet (flash blanc à 0,6 → 0,3), l'espacer (≥ 0,33 s entre deux
  flashs), le restreindre à une zone plus petite, ou remplacer le flash plein cadre par un fondu court.
- Le script vérifie ce qui est dans la vidéo. Il a été validé sur un stroboscope de test (6 Hz plein cadre, puis
  5 Hz rouge) qu'il détecte bien, et il laisse passer le film actuel. Ce n'est pas un test certifié : pour une
  diffusion à grande échelle, un outil officiel (Harding FPA / PEAT) fait foi.
- Dans le film, les gros moments (BOOM, mosaïque) combinent flash blanc, vignette, punch et shake. Les doses
  documentées dans `motion-timing` (flash ≤ 0,75, une décroissance de k ≥ 14) restent sous le seuil. Si on les
  augmente, relancer ce contrôle.

## 2. Daltonisme
```bash
python3 .claude/skills/motion-accessibility/scripts/colorblind.py frames output/film.mp4 --times 5 17 30 45
python3 .claude/skills/motion-accessibility/scripts/colorblind.py palette --project --looks
```
- `frames` produit une planche « original | protanopie | deutéranopie | tritanopie | gris ». Questions à se poser :
  le sujet se détache-t-il du fond ? deux éléments qui portent chacun une information se confondent-ils ?
- `palette` donne la distance de couleur (ΔE) minimale entre couleurs, avec et sans simulation. Sur la palette de
  fils du film, les fils 5 (bleu) et 6 (violet) tombent à ΔE 8 en protanopie, et 11,5 en deutéranopie : ils se
  confondent. C'est sans conséquence tant qu'ils ne servent qu'à décorer. Si on les met côte à côte pour
  distinguer deux informations, il faut ajouter une différence de luminance ou de forme.
- La règle de fond du projet protège déjà beaucoup : le liseré blanc des stickers, les fonds teintés clairs et la
  silhouette détourée gardent le produit lisible en niveaux de gris. À conserver.

## 3. Texte (si une variante en contient)
```bash
python3 .claude/skills/motion-accessibility/scripts/colorblind.py contrast "#111111" "#FAF6F0"
```
Cibles WCAG : 4,5:1 pour un texte courant, 3:1 pour un grand texte (≥ 24 px, ou 19 px gras) et les éléments
graphiques. Les couleurs vives du projet (jaune `#FFC400`, orange) sont **insuffisantes en texte sur fond clair**
(jaune sur blanc : 1,6:1). Utiliser le noir `#111111` ou un aplat de fond. Pour les sous-titres, voir `motion-captions`.

## 4. Mouvement et son
- **Sensibilité au mouvement** : zoom plein cadre, shake et rotation rapide peuvent provoquer un malaise. Règles de
  prudence du projet (pas des normes) : réserver ces effets à quelques moments marquants, garder le shake sous ~20 px,
  ne pas enchaîner plus de 2 plongées de caméra de suite.
- **Lisible sans le son** : la majorité des vues sur mobile se font sans son. Le film doit se comprendre à l'image
  seule (c'est le cas : l'histoire passe par les looks), et tout message important doit être aussi à l'écran.
- **Volume** : un impact très fort juste après un silence long surprend. Garder le contraste voulu du « BOOM »
  (c'est un effet de style du projet), mais ne pas le pousser au-delà de ce qu'on entend aujourd'hui, et vérifier
  la crête vraie avec `motion-delivery`.

## Fichiers
- `scripts/flash_check.py` : le risque photosensible (`--area`, `--grid`, `--plot`) et un JSON dans `build/review/`.
- `scripts/colorblind.py` : `frames`, `palette`, `contrast`.
- `references/accessibility.md` : les critères, les valeurs de seuil et les sources.
