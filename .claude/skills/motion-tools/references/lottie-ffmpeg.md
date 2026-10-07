# Lottie et ffmpeg

## Lottie
Format JSON d'animation vectorielle (formes, chemins, transformations, masques, keyframes avec
courbes de Bézier), lu par lottie-web, lottie-ios/android ou dotLottie.
- **Pour** : icônes animées, loaders, micro-animations de site ou d'app, boucles légères (quelques Ko), net à toute taille.
- **Contre** : pas d'effets raster (flou, grain, displacement), images bitmap lourdes et mal gérées,
  pas de son. Le collage photo de ce projet ne s'y prête pas : seuls les éléments vectoriels
  (fils, formes pop, carrés granny simplifiés) le pourraient.
- **Créer** : After Effects + Bodymovin, ou par code (python-lottie / `lottie` sur PyPI, ou le JSON écrit
  à la main pour des formes simples). Les easings Lottie sont des Bézier `o`/`i` par keyframe :
  `bezier(x1, y1, x2, y2)` de `motion-timing/scripts/easings.py` donne les mêmes courbes.
- **Vérifier** : rendre en vidéo (par exemple avec Remotion `@remotion/lottie`, ou lottie-web dans Chromium) puis
  relire avec `motion-review`.

## ffmpeg : commandes utiles
```bash
# extraire un passage sans réencoder (coupe sur image clé la plus proche)
ffmpeg -ss 16 -to 28 -i in.mp4 -c copy part.mp4
# coupe précise à l'image (réencode)
ffmpeg -ss 16 -to 28 -i in.mp4 -c:v libx264 -crf 18 -c:a aac part.mp4
# assembler des segments de même format
printf "file 'a.mp4'\nfile 'b.mp4'\n" > list.txt && ffmpeg -f concat -safe 0 -i list.txt -c copy out.mp4
# remplacer la bande-son
ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest out.mp4
# 9:16 -> 4:5 centré sur y=935 (ligne des stickers)
ffmpeg -i in.mp4 -vf "crop=1080:1350:0:935-675" out_4x5.mp4
# ralentir ou accélérer l'image (et le son)
ffmpeg -i in.mp4 -vf "setpts=PTS/1.25" -af "atempo=1.25" out.mp4
# GIF de bonne qualité (palette)
ffmpeg -ss 4 -t 3 -i in.mp4 -vf "fps=15,scale=360:-1:flags=lanczos,split[a][b];[a]palettegen[p];[b][p]paletteuse" out.gif
# boucle parfaite : fondu enchaîné de la fin sur le début (0,5 s)
ffmpeg -i in.mp4 -filter_complex "[0]split[a][b];[a]trim=0:0.5,setpts=PTS-STARTPTS[s];[b]trim=0.5,setpts=PTS-STARTPTS[m];[m][s]xfade=transition=fade:duration=0.5:offset=59" loop.mp4
# incruster une image fixe (logo, filigrane) en bas à gauche
ffmpeg -i in.mp4 -i logo.png -filter_complex "overlay=60:H-h-700" -c:a copy out.mp4
```
