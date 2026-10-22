---
name: motion-delivery
description: Préparer et contrôler la livraison d'une vidéo verticale pour TikTok, Instagram Reels et YouTube Shorts. Le skill vérifie le format, la cadence, le codec, le faststart, la durée, le loudness et la crête vraie, l'accroche de la première image et la fin, superpose les zones sûres de chaque interface et corrige le loudness sans réencoder l'image. Utilise ce skill avant toute livraison, export, mux ou rendu final, quand on parle de publier, de format, de zones sûres, de loudness, de LUFS, de volume trop fort ou trop faible, de compression ou de miniature, et aussi pour adapter le film à une autre plateforme ou à un autre ratio.
---

# Livraison réseaux sociaux

## Contrôle (à faire sur chaque rendu final)
```bash
python3 .claude/skills/motion-delivery/scripts/check_delivery.py output/film.mp4             # profil social
python3 .claude/skills/motion-delivery/scripts/check_delivery.py output/film.mp4 --profile shorts
```
Le script renvoie un verdict par point (`OK`, `ATTENTION` ou `ERREUR`). Points à ne jamais laisser passer :
- **résolution 1080×1920, yuv420p, H.264, faststart** : sinon la plateforme rejette le fichier ou le réencode mal ;
- **loudness ≈ −14 LUFS intégrés et crête vraie ≤ −1 dBTP** : TikTok et Meta ne publient pas de cible
  officielle mais normalisent autour de −14. YouTube normalise à −14. Un fichier plus faible paraît
  mou à côté des autres vidéos du fil ;
- **1re image non vide** : elle sert de miniature et d'accroche. Une image de papier uni à t=0 fait perdre le
  scroll. Il faut que quelque chose soit déjà à l'écran à l'image 0.

**Corriger le loudness sans toucher à l'image** (deux passes de loudnorm, en abaissant le plafond tant que
l'AAC fait dépasser la crête) :
```bash
python3 .claude/skills/motion-delivery/scripts/check_delivery.py output/film.mp4 --fix output/film_final.mp4 --lufs -14
```
Pour corriger durablement, régler la cible dans `make.sh` (`loudnorm=I=-14:TP=-2:LRA=11`). À −1,5 dBTP
avant l'AAC, la crête mesurée après encodage remonte à environ −0,9 dBTP : il faut viser −2.

## Zones sûres
```bash
python3 .claude/skills/motion-delivery/scripts/safe_zone.py output/film.mp4 --times 2.7 10 17.6 30 45 58
```
Le script superpose les marges de chaque plateforme et le cadre « sujet » du projet. Lire la planche :
- **texte, logo, CTA** : strictement dans le rectangle de la plateforme la plus contraignante ;
- **sujet** (visage, produit) : dans le cadre vert (y 210 → 1610, x < 940). Les pieds ou le bas d'une
  robe peuvent déborder dans la zone de légende, mais pas le produit qu'on veut montrer.
Les valeurs sont dans `references/platforms.md`. Elles sont indicatives, car les interfaces changent ; on
re-vérifie sur une capture réelle si une publication importante en dépend.

## Pipeline de livraison du projet
1. `./make.sh`, qui rend le master H.264 CRF 20 (maxrate 10M) + AAC 256k, faststart, loudnorm.
2. `check_delivery.py`, puis `--fix` si le loudness ou la crête ne passe pas.
3. `safe_zone.py` sur les moments clés.
3b. `flash_check.py` et `colorblind.py` (skill `motion-accessibility`) : flashs à risque photosensible et lisibilité.
4. Un **aperçu allégé** pour partager (messagerie) :
   `ffmpeg -i output/film.mp4 -vf scale=720:-2 -c:v libx264 -crf 26 -preset slow -c:a aac -b:a 128k -movflags +faststart output/film_apercu.mp4`
5. Une **miniature** (image d'accroche pour la couverture) :
   `ffmpeg -ss 2.7 -i output/film.mp4 -frames:v 1 -q:v 2 output/film_cover.jpg`.

## Autres formats
Pour un 4:5 (fil Instagram) ou un 1:1, on ne recadre pas le 9:16 à l'aveugle. Le moteur dessine en
coordonnées absolues (W=1080, H=1920) : il faut un rendu dédié ou, à défaut, recadrer autour de `CY`
(ligne médiane des stickers, y ≈ 935) et vérifier avec `contact_sheet.py` que rien d'essentiel n'est coupé.
Pour du 16:9, les compositions verticales ne se transposent pas : il faut une nouvelle mise en page.

## Fichiers
- `scripts/check_delivery.py` : le contrôle et la correction du loudness (`--fix`, `--lufs`, `--tp`, `--profile`).
- `scripts/safe_zone.py` : la planche des zones sûres par plateforme.
- `references/platforms.md` : les specs, les marges, les durées et les sources.
