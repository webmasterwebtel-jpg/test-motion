# Structures types (120 BPM : 1 mesure = 2 s)

Ces plans sont des propositions de travail, tirées du film actuel et de l'arithmétique de la grille : ce ne sont pas
des résultats d'audience. On les soumet à l'utilisateur et on ajuste selon ses retours (`motion-direction`).

Principe commun : **accroche → montée → sommet → respiration → résolution**, avec une tenue posée d'environ une
mesure pour chaque look important, et un silence ou un creux d'une demi-mesure avant le sommet.

## 15 s (teaser, 7,5 mesures)
| Séquence | Mesures | Durée | Contenu | Énergie |
|---|---|---|---|---|
| accroche | 1 | 2 s | élément fort dès l'image 0 (pelote qui roule), premier look révélé | 3 |
| pile | 3 | 6 s | 3 looks, un par mesure | 3 |
| sommet | 1,5 | 3 s | silence 0,5 s, BOOM, mosaïque ou grille | 5 |
| final | 2 | 4 s | aspiration en pelote, fleur, scintillement | 3 |
Total : 7,5 mesures = 15 s. Looks présentés : 5 à 6 (1 + 3 + 1 ou 2 dans le sommet).

## 30 s (15 mesures)
| Séquence | Mesures | Durée | Contenu | Énergie |
|---|---|---|---|---|
| intro | 2 | 4 s | pelote, carrés, révélation du 1er look | 2 |
| pile | 4 | 8 s | 4 looks, un par mesure | 3 |
| zoom | 3 | 6 s | 3 looks : pose puis plongée dans les mailles | 3 |
| sommet | 2 | 4 s | silence, BOOM, mosaïque, échos | 5 |
| carrousel | 2 | 4 s | 2 tenues en cover-flow (ou grille bento) | 4 |
| final | 2 | 4 s | pelote → fleur | 3 |
Total : 15 mesures = 30 s. Looks présentés : 12 (1 + 4 + 3 + 2 + 2).

## 60 s (30 mesures) — le film actuel
`beat_sheet.py --example` donne le détail : intro 2, pile 6, zoom 6, mosaïque 1,875, échos 1,625, bento 2, carrousel 8,
final 2,5. Dans ce brief, l'énergie est estimée à 4–5 de 28 s à 55 s (mosaïque 5, échos 4, bento 4, carrousel 4) : ces notes
sont un jugement, pas une mesure (la mesure est dans `motion-review`). Si le film paraît long, c'est là qu'il faut
chercher où ajouter une respiration.

## Écrire un brief
- **Un look = une mesure** pour une présentation posée. En dessous (un par temps, un par demi-temps), c'est un
  montage énergique, réservé au sommet, 4 s au maximum.
- **Commencer et finir sur la grille.** Un départ sur une croche (demi-temps) est possible et même efficace après un
  silence, mais il se décide, il ne se subit pas.
- **Compter les looks.** 24 looks à présenter en 15 s donne 0,6 s par look : impossible de les lire. Soit on en
  choisit moins, soit on les regroupe (grille bento : plusieurs looks en une mesure, avec la tenue sur le look principal).
- **Prévoir la boucle** : la dernière image peut rimer avec la première (même couleur, même forme).
- **Nommer ce qui change à chaque mesure** (look, couleur, mouvement, son) : si rien ne change pendant 2 mesures de
  suite, la séquence est trop longue ou trop pauvre.
