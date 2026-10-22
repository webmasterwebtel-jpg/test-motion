# Journal des retours et décisions

Les entrées les plus récentes sont en haut. Format : **date — retour → règle déduite → changement**.
Les entrées de 2026-10-01 ont été reconstituées à partir de l'historique Git (messages de commits et README).

---

**2026-10-22 (soir)** — Nouvelle demande : un film de présentation de l'app **MyWebtel** (intranet de Webtel), « pro,
premium », voix off naturelle « pas IA », musique jamais plus forte que la voix, effets sans exagération, style
présentation Apple, sans sous-titres → préférences générales ajoutées dans SKILL.md ; direction dans
`mywebtel/DIRECTION.md`. Contraintes rencontrées : Hugging Face bloqué par le réseau de l'environnement (pas de modèle
de voix plus récent) ; voix Kokoro `ff_siwis` retenue, chaque segment vérifié par transcription Whisper.
Livré : `output/mywebtel_presentation.mp4` (124,8 s, 1920×1080). Réglages retenus, à confirmer par l'utilisateur :
- musique ≈ 16 dB sous la voix pendant la parole (ducking -7 dB à retour lent 0,45 s, pour ne pas pomper entre les mots) ;
- bruitages ≥ 10 dB sous les crêtes de la voix ; mix final -16 LUFS, crête -2 dBTP ;
- relecture `motion_graph` : un raccord sec repéré à 116,1 s (signature posée d'un coup sur l'écran précédent) et deux
  écrans vides d'environ 0,5 s (75,9 s et 110,0 s), corrigés par des fondus et des entrées plus tôt ;
- statuts rouge/ambre confondus en deutéranopie, mais chaque statut porte son libellé : sans conséquence.

---

**2026-10-22** — L'utilisateur demande « d'autres skills et artefacts pour le motion design » → quatre skills ajoutés
(`motion-accessibility`, `motion-compare`, `motion-storyboard`, `motion-captions`) et deux artefacts interactifs
(Easing Lab, Beat Planner). Aucune règle de goût nouvelle : c'est de l'outillage. Constats faits en les testant sur
`crochet_tiktok_60s.mp4` :
- **flashs** : aucun passage à risque photosensible (au plus 4 flashs/s sur un bloc, sur moins de 6 % de l'image) ;
- **daltonisme** : les fils 5 (bleu) et 6 (violet) se confondent en protanopie (ΔE 8) ; sans conséquence tant qu'ils restent décoratifs ;
- **timeline image/son** : cohérente (30 événements visuels, tous avec un bruitage dans la fenêtre) ;
- le texte reste exclu du film : `motion-captions` ne sert que sur demande explicite.

---

**2026-10-07** — L'utilisateur demande quels skills m'aideraient à progresser en motion design,
puis « fais tout » → créer les outils de relecture, le canon de timing, ce journal, l'API du moteur, la
synchro audio, les specs de livraison et le guide des autres moteurs → `.claude/skills/motion-*`.
Constats faits en testant les outils sur `crochet_tiktok_60s.mp4` (à valider avec l'utilisateur
avant de corriger) :
- loudness mesurée à **−16,0 LUFS intégrés, crête vraie −0,9 dBTP**, alors que le README annonce
  ≈ −15 et que `make.sh` vise −1,5 dBTP (le dépassement vient de l'encodage AAC) ;
- sur les entrées « spin » (6,0 s et 14,0 s), la claque de papier (`t0 + 0.1`) tombe pendant que le
  sticker tourne encore, avant qu'il se pose (vers `t0 + 0.2`) ;
- dans le zoom infini, le « bloup » d'iris précède de 3 à 5 images le pic visuel de l'ouverture ;
- sur le carrousel (39–55 s), le clic de cran est trop faible pour ressortir du mix.

**2026-10-01** — Rythme jugé trop rapide sur la version 40 s → **chaque tenue doit rester ~2 s
à l'écran (une mesure)** ; le film passe à 60 s, la musique et les bruitages sont recalés (commit `7abb162`).

**2026-10-01** — Nouveau film demandé au format TikTok, **sans voix ni texte**, avec bruitages et
musique de fond → musique ≈ 11 dB sous les bruitages ; DA « collage mixed-media » inspirée des
tendances 2026 (commit `ad2bc72`).

**2026-10-01** — Écran final : **retirer le nom de marque et les réseaux** ; la voix off SVOX Pico
a été remplacée par la voix neuronale **Kokoro `ff_siwis`** (féminine, française) (commit `c0e5868`).

**2026-10-01** — Première version « Le crochet. Autrement. » : 40 s, voix off, textes cinétiques,
logo fleur au crochet en signature (commit `3794613`).
