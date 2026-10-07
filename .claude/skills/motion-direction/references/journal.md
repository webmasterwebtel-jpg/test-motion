# Journal des retours et décisions

Les entrées les plus récentes sont en haut. Format : **date — retour → règle déduite → changement**.
Les entrées de 2026-10-01 ont été reconstituées à partir de l'historique Git (messages de commits et README).

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
