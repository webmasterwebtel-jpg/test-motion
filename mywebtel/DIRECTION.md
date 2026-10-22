# MyWebtel — direction du film de présentation

## Demande (22 octobre 2026)
Vidéo motion design pro et premium pour présenter l'app MyWebtel et ses fonctionnalités. Voix off naturelle (bon timbre,
bon rythme, « que ça ne fasse pas IA »), musique de fond **jamais plus forte que la voix**, effets et bruitages **sans
exagération**, esprit **présentation Apple**, **sans sous-titres**. Source : le dossier fonctionnel MyWebtel.

## Parti pris
- **Une idée par plan.** Chaque phrase de la voix a un seul visuel, centré, avec beaucoup d'air autour. Le texte à
  l'écran se limite à des titres de quelques mots (ce ne sont pas des sous-titres : ils ne reprennent pas la voix mot à mot).
- **Fond calme, produit lumineux.** Fonds blanc cassé (`#f4f7fb`, le fond réel de l'app) et bleu nuit (`#061427`) en
  alternance ; la couleur vient de l'interface MyWebtel elle-même.
- **Identité réelle de l'app** (dépôt `webtel-intra-clean`, `app/globals.css`) : marine `#112d50`, encre `#061427`,
  gris `#66758a`, filets `#dce3ec`, fond `#f4f7fb`, vert `#16784a`, rouge `#b42318` ; logo carré arrondi « W » ;
  vocabulaire de l'interface (« Ma journée », « Session de travail », matricule `WTL-00001`).
- **Typographie** : Inter Display pour les titres (grands, serrés, graisse 600–700), Inter pour l'interface.
- **Mouvement** : lent et précis. Entrées en `out_expo`/ressort ferme (dépassement ≤ 5 %), déplacements en
  `in_out_cubic`, caméra en légère dérive continue (parallaxe), aucune secousse, aucun flash. Transitions par fondu
  enchaîné, glissement ou zoom doux, calées sur les temps (100 BPM, 1 temps = 0,6 s).
- **Son** : voix au premier plan ; musique calme (piano, nappe, pulsation légère) baissée automatiquement sous la voix ;
  bruitages d'interface discrets (clics, glissés, carillon doux) à peine audibles.

## Ce que la vidéo ne fait pas
- Elle ne cite que des fonctions décrites dans le dossier fonctionnel ; elle ne parle ni de la technique ni de la
  géolocalisation (règle en cours d'évolution).
- Elle n'utilise ni logo ni appareil d'une marque tierce : les écrans sont posés dans des cadres génériques.

## Attention avant diffusion
Le dossier fonctionnel décrit le **comportement souhaité** ; le dépôt actuel (V1) ne contient que la connexion et le
pointage, les autres modules y sont « Bientôt disponible ». Vérifier que les fonctions montrées sont en service avant
de diffuser la vidéo comme une présentation de l'existant.
