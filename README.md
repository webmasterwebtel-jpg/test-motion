# Crochet Pop Collage — motion design TikTok 40 s

Vidéo **TikTok 9:16 (1080×1920), 30 i/s, 40 s**, générée entièrement par code à partir des 24 visuels
sur fond blanc (`assets/articles/`). **Sans voix off ni texte** : animation, bruitages et musique de fond discrète.

- **Vidéo** : `output/crochet_tiktok_40s.mp4` (H.264 + AAC, ≈ −15 LUFS)
- Aperçu allégé : `output/crochet_tiktok_40s_apercu.mp4`

## Direction artistique

Inspirée des tendances motion 2026 : collage mixed-media (stickers découpés à liseré blanc, ruban adhésif,
formes pop, grain papier), timing « stop-motion » tactile, compositions modulaires (mosaïque, bento),
carrousel 3D. Le cadrage respecte les zones sûres TikTok (rien d'important sous la légende ni derrière
la colonne de boutons).

Tout est calé sur **120 BPM** : 1 temps = 0,5 s = 15 images.

| Temps | Séquence | Image | Son |
|---|---|---|---|
| 0–4 s | Pelote → carrés → look | Une pelote roule en déroulant son fil ; deux carrés granny sont tamponnés sur les battements ; au 3ᵉ impact ils explosent en quartiers et révèlent le premier look en sticker | Roulement, battements, claques papier, impact |
| 4–10 s | Pile de stickers | 6 looks plaqués un par un (chute, vrille, glissé, retournement), formes pop et ruban adhésif ; plongée caméra dans le dernier | Whooshes, claques de papier, ruban arraché |
| 10–17 s | Zoom infini | La caméra plonge dans les mailles ; un iris bordé de fil ouvre sur le look suivant, couleur de fond à chaque fois ; accélération au double-temps | « Bloups » d'iris, whooshes, montée |
| 17–24 s | Mosaïque | 0,5 s de silence, avatar seul ; BOOM : l'écran se découpe en 60 carreaux qui se retournent en vagues (radiale, diagonale, rangées, aléatoire, spirale), un look par temps ; puis échos colorés façon impression riso et fils en orbite | Impact, nuées de clics, snaps |
| 24–31 s | Grille bento | Cases qui se réorganisent (1+3, 3 colonnes, 2×2 femme & homme, 2×3), contenu qui glisse, fusion en plein cadre | Déclics, glissements |
| 31–37 s | Carrousel 3D | Cover-flow : une tenue de face par temps, franges qui ondulent | Swish + clic à chaque cran |
| 37–40 s | Final | Tout est aspiré dans une pelote qui se déroule en fleur au crochet, entourée de mini carrés granny en orbite | Aspiration, BOOM final, scintillements |

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
