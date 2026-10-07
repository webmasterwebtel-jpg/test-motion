# Grille de relecture motion design

Passer chaque séquence au crible. Noter `timecode → constat → correction`. Ne garder que ce qui
change vraiment le ressenti.

## 1. Lisibilité (le plus important pour un film produit)
- [ ] Chaque visuel important a une **tenue** d'au moins ~1,3 s, sujet entier et immobile (ou
      presque). Mesure : section TENUES de `motion_graph.py`.
- [ ] L'œil sait où regarder : **un seul centre d'intérêt** à la fois, ou une hiérarchie claire
      (taille, contraste, mouvement).
- [ ] Le sujet n'est jamais coupé par un élément de premier plan pendant sa tenue.
- [ ] Après une transition rapide, l'image se stabilise **avant** qu'on ait besoin de la lire.
- [ ] Rien d'important dans les zones masquées par l'interface (voir `motion-delivery`).

## 2. Les 12 principes, version écran
- [ ] **Timing** : les durées ont un sens (léger = rapide, lourd = lent) et sont calées sur la musique.
- [ ] **Slow in / slow out** : aucun mouvement visible en vitesse constante, sauf voulu
      (défilement continu). Pelure d'oignon : l'espacement doit varier.
- [ ] **Anticipation** : les gros mouvements partent après un petit recul ou une respiration (2 à 4 images).
- [ ] **Follow-through / overlap** : les éléments liés n'arrivent pas tous à la même image.
      Un décalage (stagger) de 1 à 3 images entre eux suffit.
- [ ] **Squash & stretch** : les impacts écrasent légèrement (5 à 15 %) puis rebondissent, et le volume est conservé.
- [ ] **Arcs** : les trajectoires naturelles sont courbes.
- [ ] **Exagération** : les moments clés sont poussés (overshoot, flash, shake). Les moments
      secondaires restent sobres.
- [ ] **Secondary action** : des détails vivants pendant les tenues (franges qui ondulent,
      flottement), assez subtils pour ne pas gêner la lecture.
- [ ] **Staging** : la composition de chaque tenue fonctionne en image fixe.
- [ ] **Appeal** : formes et couleurs cohérentes avec la DA (voir `motion-direction`).

## 3. Rythme global
- [ ] Les 1 à 2 premières secondes accrochent : il y a du mouvement ou du son dès l'image 1, pas d'écran vide.
- [ ] L'énergie varie : des montées, des respirations, un pic, une résolution. La courbe ne doit pas être plate.
- [ ] Les **surcharges** (agitation continue de plus de 2,5 s) et les **temps morts** (une tenue
      trop longue sans vie secondaire) sont voulus.
- [ ] La fin se lit : le dernier plan reste au moins 1,5 s.

## 4. Son
- [ ] Chaque contact net (arrêt, impact, claque) a un son à ±1 image. Les whooshes **précèdent**
      le pic de vitesse de 2 à 4 images.
- [ ] Les silences sont voulus et suivis d'un impact fort.
- [ ] Musique sous les bruitages, sans masquer les bruitages importants.
- [ ] Le loudness est conforme à la cible (voir `motion-delivery`).

## 5. Technique
- [ ] Pas de saut d'une image (pop) : vérifier les frontières de sections dans le code
      (`SECTIONS`) et sur la planche au pas d'une image (`--step 0.0333`).
- [ ] Pas de bord dur au détourage, de halo blanc ni de crénelage sur les petites tailles.
- [ ] Le flou de mouvement est présent sur les déplacements rapides (plus de ~40 px par image).
- [ ] Les couleurs sont stables et sans banding visible sur les dégradés (le grain aide).
