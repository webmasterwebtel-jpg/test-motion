# Critères et seuils

## Flashs (WCAG 2.3.1 « Three Flashes or Below Threshold »)
- Un **flash général** : une paire de changements opposés de luminance relative d'au moins **10 %** de la luminance
  maximale, l'état le plus sombre ayant une luminance relative **inférieure à 0,80**. Une suite de changements dans un
  même sens ne compte pas.
- Un **flash rouge** : une transition vers ou depuis un rouge saturé (rapport R/(R+G+B) ≥ 0,8, avec un écart
  (R−G−B)×320 ≥ 20).
- **Seuil** : pas plus de **3 flashs par seconde**, sauf si la zone de flash ne dépasse pas une surface d'environ
  **0,006 stéradian** (≈ 25 % d'un écran de 10° de champ visuel, pour un affichage standard).
- Le script applique la même logique par blocs, avec une surface par défaut plus stricte (1/16 de l'image) parce
  qu'un téléphone tenu près des yeux occupe un champ visuel plus large. `--area 0.25` donne la règle WCAG standard.
- Approximations : luminance par moyenne de blocs 8×8 px (pas par pixel), fenêtre fixe d'une seconde, aucune
  prise en compte de la distance de visionnage. Le script est un garde-fou, pas une certification.

## Daltonisme
- Environ 8 % des hommes et 0,5 % des femmes ont une déficience de la vision des couleurs, surtout rouge/vert
  (deutéranomalie et protanomalie). La tritanopie est rare.
- La simulation utilise les matrices de Machado, Oliveira et Fernandes (2009), sévérité 1,0 (dichromatie complète),
  en RGB linéaire. Les cas partiels sont moins marqués que la simulation.
- ΔE CIE76 : < 10 quasi identique, 10–20 confusion facile, 20–40 distinguable, > 40 net. La mesure inclut la
  luminance : deux couleurs de même teinte mais de clarté différente restent distinctes.

## Contraste (WCAG 1.4.3 et 1.4.11)
- Texte : 4,5:1 (3:1 pour un grand texte : ≥ 24 px, ou ≥ 18,66 px en gras).
- Éléments d'interface et graphiques porteurs d'information : 3:1.

## Mouvement (WCAG 2.3.3, 2.2.2)
- Pour le web : respecter `prefers-reduced-motion` ; proposer une pause pour tout mouvement de plus de 5 s.
- Pour la vidéo : pas d'équivalent normatif, mais éviter les zooms continus plein cadre de plus de 2 s et
  les oscillations rapides répétées.
