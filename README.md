# Crochet Pop Collage — motion design TikTok 60 s

Vidéo **TikTok 9:16 (1080×1920), 30 i/s, 60 s**, générée entièrement par code à partir des 24 visuels
sur fond blanc (`assets/articles/`). **Sans voix off ni texte** : animation, bruitages et musique de fond discrète.

- **Vidéo** : `output/crochet_tiktok_60s.mp4` (H.264 + AAC, ≈ −15 LUFS)
- Aperçu allégé : `output/crochet_tiktok_60s_apercu.mp4`

## Direction artistique

Inspirée des tendances motion 2026 : collage mixed-media (stickers découpés à liseré blanc, ruban adhésif,
formes pop, grain papier), timing « stop-motion » tactile, compositions modulaires (mosaïque, bento),
carrousel 3D. Le cadrage respecte les zones sûres TikTok (rien d'important sous la légende ni derrière
la colonne de boutons).

Tout est calé sur **120 BPM** (1 temps = 0,5 s). Rythme posé : **chaque tenue reste environ 2 s à l'écran**
(une mesure) — l'animation d'entrée est rapide, puis le look est présenté entier et bien lisible.

| Temps | Séquence | Image | Son |
|---|---|---|---|
| 0–4 s | Pelote → carrés → look | Une pelote roule en déroulant son fil ; deux carrés granny tamponnés sur les battements ; au 3ᵉ impact ils explosent et révèlent le premier look en sticker | Roulement, battements, claques papier, impact |
| 4–16 s | Pile de stickers | 6 looks plaqués un toutes les 2 s (chute, vrille, glissé, retournement), formes pop, ruban adhésif ; plongée caméra dans le dernier | Whooshes, claques de papier, ruban arraché |
| 16–28 s | Pose + zoom infini | Chaque look est posé ~1,4 s (léger flottement), puis la caméra plonge dans les mailles et un iris bordé de fil ouvre sur le suivant | « Bloups » d'iris, whooshes, montée |
| 28–35 s | Mosaïque | 0,5 s de silence, look seul ; BOOM : 60 carreaux ; ils se retournent en vague vers le look suivant, puis échos colorés façon riso et fils en orbite | Impact, nuées de clics |
| 35–39 s | Grille bento | 2×2 ensembles femme & homme, puis 2×3, fusion en plein cadre | Déclics, glissements |
| 39–55 s | Carrousel 3D | Cover-flow : une tenue de face toutes les 2 s, franges qui ondulent | Swish + clic à chaque cran |
| 55–60 s | Final | Tout est aspiré dans une pelote qui se déroule en fleur au crochet, mini carrés granny en orbite | Aspiration, BOOM final, scintillements |

## Régénérer

```bash
sudo apt-get install ffmpeg
pip install pillow numpy scipy
./make.sh
```

Images de contrôle : `python3 motion/collage.py --stills 2.7 17.6 38.5`
Aperçu d'un passage : `python3 motion/collage.py --range 17 24`

## Fichiers

- `motion/prep.py` — détourage automatique du fond blanc.
- `motion/render.py` — moteur de rendu (placement 2D/3D, fils de laine, effets) + première version du film.
- `motion/collage.py` — le film « Crochet Pop Collage ».
- `motion/audio.py` — instruments et musique afro-house / amapiano synthétisée (120 BPM).
- `motion/audio_collage.py` — bruitages du film et mixage (musique ≈ 11 dB sous les bruitages).

La musique est générée par code ; pour une diffusion commerciale on peut la remplacer par une piste
sous licence à 120 BPM sans toucher au montage.
