---
name: motion-direction
description: Direction artistique et préférences validées pour les films de motion design de ce dépôt (crochet, collage pop, TikTok). Il couvre le style, les couleurs, les polices, le rythme attendu, ce qui a été refusé et le journal des retours de l'utilisateur. Utilise ce skill avant de concevoir, modifier ou proposer une séquence, un nouveau film, une variante, un visuel ou un choix de couleur, de son ou de rythme pour ce projet. Utilise-le aussi dès que l'utilisateur donne un retour (« trop rapide », « j'aime bien », « enlève… »), car ce retour doit être consigné dans le journal pour ne pas refaire la même erreur.
---

# Direction artistique et préférences

Ce fichier est la mémoire du goût de l'utilisateur. Les préférences et la direction artistique ci-dessous **priment sur
mes réflexes** : je les applique sans qu'on me les redemande. Le détail daté des retours est dans
`references/journal.md`.

## Préférences confirmées (par ordre d'importance)

1. **Un rythme posé, un produit lisible.** Chaque look reste **environ 2 s** à l'écran (une mesure à
   120 BPM) : l'entrée est rapide, puis le look est présenté entier et bien visible. La version à
   40 s, avec un changement par temps, a été jugée trop rapide et étirée à 60 s. En cas de doute,
   ralentir plutôt qu'accélérer. Le double-temps reste réservé à de très courts climax.
2. **Pas de voix off ni de texte à l'écran** dans le film actuel. L'histoire passe par
   l'animation, les bruitages et une musique de fond discrète.
3. **Pas de nom de marque ni de réseaux sociaux** sur l'écran final. La marque n'est jamais citée.
4. **Musique en fond** : environ 11 dB sous les bruitages. Les bruitages portent l'énergie.
5. **Format TikTok 9:16**, avec les zones sûres respectées (voir `motion-delivery`).
6. Quand une voix off est demandée : une **voix féminine française naturelle**. La voix neuronale
   Kokoro `ff_siwis` a été préférée à la synthèse SVOX Pico, jugée trop robotique.

## Préférences générales de l'utilisateur (tous projets)
Exprimées le 2026-10-22 pour le film MyWebtel, à appliquer par défaut à toute vidéo :
- **voix off naturelle**, bon timbre et bon rythme, qui « ne fasse pas IA » : vérifier chaque segment par transcription
  (`mywebtel/vo.py` le fait) et corriger la phonétique plutôt que d'accepter une diction douteuse ;
- **cadence normale** : ni lente (115 mots/min jugé « trop lent, IA » le 2026-10-23) ni précipitée (un film de 70 s
  pour 8 fonctions jugé « trop rapide » le 2026-10-27) : ~135-150 mots/min sur la durée parlée, et pour une démo
  produit ~10 s par fonction avec une respiration après chaque résultat ;
- **accent français naturel** : ne jamais mélanger le timbre avec une voix d'une autre langue ;
- **montrer le vrai produit, avec le vrai logo, sans rien inventer** : partir du code et des visuels réels, et ne
  montrer que les fonctions que l'utilisateur cite ;
- **musique de fond jamais plus forte que la voix** (ducking automatique sous la voix) ;
- **effets et bruitages sans exagération** : au service du propos, jamais démonstratifs ;
- quand une référence est donnée (ici « présentation Apple »), la suivre : une idée par plan, beaucoup d'air, sobriété ;
- **pas de sous-titres** sauf demande explicite (des mots-clés ponctuels façon pub produit sont acceptés, V5) ;
- **voix MyWebtel : ElevenLabs « Simon »** (choisie le 2026-11-10), prononciations forcées par l'orthographe envoyée,
  jamais de bascule d'accent vers l'anglais ;
- **aux couleurs du produit présenté, sans exagérer** (MyWebtel : bleu nuit `#06213e`, bleu `#008ff1`, cyan `#05daf0`) ;
- références de style données le 2026-11-10 : pub Drive Academy (fond clair, mots-clés, badges ✓, curseur), reportage
  Binance (ouverture cinéma sombre), bande-annonce GTA 6 (traits de lumière, transitions franches), à doser avec retenue.
  Leur point commun, à respecter : **une caméra continue dans un monde 3D** où vivent textes, cartes et écrans (V6) ;
- **prononciation mesurée, jamais supposée** : deux transcriptions + confiance mot à mot + formants ; pas de liaison
  fautive (« tu déclares avec » s'envoie « tu la déclare avec ») ;
- une demande de **refonte** = reconstruire, pas retoucher ;
- **film produit (V7, validé pour la voix)** : interfaces en grand dans des **mock-ups PC / tablette / téléphone**
  (vraie mise en page responsive), montage **entraînant** calé sur une musique électro-pop à 120 BPM, musique
  « un peu forte » mais toujours sous la voix (~10 dB pendant la parole), durée ~1 min 30. Une mise en scène
  contemplative (V6, monde 3D survolé) a été jugée « fade, donne envie de dormir ».
- **film produit, style « présentation Apple » (V8, demandé le 2026-11-11)** : fond sombre, un appareil à la fois,
  mouvements lents et continus, titres sobres. **L'image ne bat jamais sur la musique** (la V7 pulsait sur la grosse
  caisse : « pourquoi ce battement boom boom de l'écran ? ») ; pas d'éclairs, de fouets ni de secousses ; mock-ups en
  volume soignés (le portable de la V7 a été jugé « pas bien fait »).
Projet MyWebtel : direction détaillée dans `mywebtel/DIRECTION.md`.

## Direction artistique « Crochet Pop Collage »

- **Collage mixed-media** : visuels détourés en *stickers* (liseré blanc, ombre portée dure,
  façon papier), **ruban adhésif** washi, **formes pop** (cercle, arche, étoile, demi-lune,
  squircle) en teintes de la couleur du look, **grain papier** sur toute l'image.
- **Motifs crochet** : fils de laine torsadés multicolores, pelote, carrés granny,
  fleur au crochet en signature finale, mailles en très gros plan (zoom infini).
- **Timing tactile** : un tremblé stop-motion à 12 i/s sur les éléments posés, mêlé à des mouvements
  fluides à 30 i/s (glissés, plongées, carrousel).
- **Compositions modulaires** : mosaïque de carreaux qui se retournent, grilles bento qui se
  réorganisent, carrousel 3D en cover-flow.
- **Couleur pilotée par le look** : chaque tenue a une couleur signature (`LOOK_COLOR`). Le fond, le
  disque et les formes en sont des teintes (`tint`). Les fils utilisent la palette `YARN`
  (rose, orange, jaune, turquoise, bleu, violet, rouge). Le papier est blanc chaud `#FAF6F0`.
- **Énergie** : afro-house / amapiano à 120 BPM, gros impacts rares et mérités (BOOM précédé d'un silence d'un demi-temps).

Pour voir les couleurs et polices réelles du code (24 looks, teintes, fils, palettes granny,
polices) :
```bash
python3 .claude/skills/motion-direction/scripts/style_board.py   # -> build/review/style_board.png
```

## À éviter (refusé ou hors DA)
- Un enchaînement d'un look par temps sur une longue durée, ou des tenues de moins de ~1,3 s.
- Du texte, des slogans, le nom de marque, les @réseaux, sauf demande explicite.
- Une voix synthétique robotique.
- Des couleurs hors palette, des dégradés « corporate », des effets 3D réalistes qui jurent avec le papier.
- Un contenu important sous la légende TikTok ou derrière la colonne de boutons.

## Consigner chaque retour (important)

Quand l'utilisateur réagit à un rendu ou exprime une préférence :
1. Ajouter une entrée datée en tête de `references/journal.md` avec trois éléments : ce qui a été dit (en citant
   si possible), ce que j'en déduis comme règle générale et ce qui a été changé.
2. Si la règle est durable, mettre à jour la section « Préférences confirmées » ci-dessus.
3. Si elle contredit une préférence existante, la remplacer et le noter dans le journal plutôt que
   d'empiler des règles contradictoires.
Un retour ponctuel (« décale ce son de 2 images ») ne va pas dans le journal. Une préférence de goût ou de
rythme, si.

## Proposer un nouveau film ou une variante
Partir des préférences ci-dessus, proposer 2 ou 3 pistes courtes (concept, structure temporelle en
mesures, sons clés), puis faire valider avant de coder. Réutiliser le moteur existant (`motion-engine`) et
les recettes de `motion-timing`.
