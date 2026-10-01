# Le crochet. Autrement. — motion design 40 s

Vidéo verticale 1080×1920 (Reels / TikTok / Shorts), 30 i/s, 40 s, générée entièrement par code
à partir des 24 visuels sur fond blanc (`assets/articles/`).

- **Vidéo finale** : `output/crochet_motion_40s.mp4` (H.264 + AAC 256 kbit/s, ≈ −13 LUFS)
- **Sous-titres de la voix off** : `output/crochet_motion_40s.srt`

## Régénérer

```bash
sudo apt-get install ffmpeg sox libttspico-utils
pip install pillow numpy scipy
./make.sh
```

Pour changer le nom de la marque (écran final) : `BRAND_NAME`, `BRAND_TAGLINE` et `HANDLES`
en tête de `motion/render.py`. Pour retoucher la voix off (texte, départ, débit, hauteur) : la liste `VO`
dans `motion/audio.py`.

Images de contrôle : `python3 motion/render.py --stills 2.7 17.6 38.5`
Aperçu d'un passage : `python3 motion/render.py --range 17 24`

## Grille et découpage

Tout est calé sur **120 BPM** : 1 temps = 0,5 s = 15 images. Chaque changement de tenue tombe sur un temps.

| Temps | Section | Image | Son |
|---|---|---|---|
| 0–4 s | Intro / suspense | Fil chiné multicolore au ralenti ; BOOM à 0,5 / 1,5 / 2,5 s ; au 3ᵉ impact, zoom cinématique sur l'avatar. « LE CROCHET. *Autrement.* » | Battements graves, glissement de fil, whoosh, impact |
| 4–10 s | Premiers looks | 6 tenues, transitions zoom → flash → slide → rotation → whoosh → zoom ; mots cinétiques AUDACIEUX. / COLORÉ. / UNIQUE. | Groove afro-house entre ; whoosh / snap / boom |
| 10–17 s | Accélération | Gros plans mailles, fleurs, franges (anneau de fil), retour instantané sur l'avatar ; cuts au double-temps sur la dernière seconde | Percussions, montée, ticks et impacts |
| 17–24 s | Moment WOW | 17,0–17,5 s : silence total, avatar seul. BOOM. LOOK 01 → 05, une tenue par temps (balayage + fil) ; fils en orbite qui passent devant/derrière ; « NE / JAMAIS / PASSER / INAPERÇUE. » | Impact, groove repart, snaps sur chaque look |
| 24–31 s | Collection | 3 panneaux qui glissent puis pivotent, grille 2×2 femme & homme, grille 3×3, fusion vers le plein cadre | Montée afro-house / amapiano complète, basse profonde |
| 31–37 s | Final showcase | 12 tenues, une par kick (0,5 s), petit mouvement 3D + balancement des franges | Climax, mélodie, accents sur chaque kick |
| 37–40 s | Signature | Les tenues disparaissent, 6 fils convergent et dessinent le logo (fleur au crochet), nom de marque, « DÉCOUVREZ LA COLLECTION », réseaux | BOOM final, scintillement, réverbe courte |

## Pipeline

1. `motion/prep.py` — détourage automatique du fond blanc (remplissage depuis les bords → alpha doux).
   Ça permet de faire passer textes et fils **derrière** les personnages.
2. `motion/audio.py` — musique afro-house / amapiano synthétisée (kick, log drum, shaker, claps, congas,
   accords type Rhodes, nappes, sous-basse, lead), SFX (impacts, whooshes, snaps, ticks, frottement de fil,
   scintillements), voix off française (SVOX Pico, traitée EQ / compression / réverbe), ducking de la musique
   sous la voix, limiteur.
3. `motion/render.py` — rendu image par image (PIL/numpy), avec flou de mouvement par sur-échantillonnage
   temporel sur les transitions rapides, puis encodage ffmpeg.

## Limites

- La voix off est une synthèse vocale hors-ligne (SVOX Pico). Pour une voix premium, on peut enregistrer
  une comédienne ou passer par un service TTS (ElevenLabs, Azure…) sur les mêmes phrases et minutages (`VO`),
  puis relancer `python3 motion/audio.py` et l'étape de mux de `make.sh`.
- La musique est générée par code. Pour une diffusion commerciale, on peut la remplacer par une piste
  Afro-house sous licence à 120 BPM, sans toucher au montage.
