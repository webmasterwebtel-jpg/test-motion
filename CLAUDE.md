# Projet motion design « Crochet Pop Collage »

Film TikTok 9:16 généré par code (Python, Pillow, numpy, scipy, ffmpeg). Voir `README.md` pour le contenu du film.

## Skills du projet (`.claude/skills/`) : à utiliser systématiquement
| Moment | Skill |
|---|---|
| Avant de concevoir ou modifier quoi que ce soit, et à chaque retour de l'utilisateur | `motion-direction` (préférences, DA, journal des retours) |
| Pour coder dans `motion/` | `motion-engine` (API du moteur, pièges, rendu rapide d'images) |
| Pour choisir une durée, un easing ou un rythme | `motion-timing` |
| Pour une musique, un bruitage ou la synchro | `motion-audio-sync` |
| Après chaque rendu (je ne vois pas les vidéos : jamais de jugement sur 2 ou 3 images fixes) | `motion-review` |
| Avant de livrer | `motion-delivery` (format, loudness, zones sûres) |
| Si le moteur Python ne suffit plus | `motion-tools` (Remotion, Blender, Lottie, ffmpeg) |

## Rappels
- La timeline est écrite **deux fois** : dans `motion/collage.py` (image) et dans `motion/audio_collage.py` (son).
  Toute modification de timing se fait dans les deux fichiers.
- `build/` n'est pas versionné. `python3 motion/prep.py` régénère les détourages (environ 25 s).
- Rendu complet : `./make.sh` (dépendances : `pip install pillow numpy scipy`, plus ffmpeg).
