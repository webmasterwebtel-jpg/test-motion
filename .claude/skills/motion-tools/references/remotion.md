# Remotion : mode d'emploi (v4.0.534, testé dans ce conteneur)

## Principe
Une vidéo est un composant React rendu image par image par Chromium. `useCurrentFrame()` donne
l'image courante. **Toute animation se dérive du numéro d'image**, et jamais des transitions CSS, de
`setTimeout` ou de l'état React : ce serait l'équivalent de la « fonction pure du temps » du moteur Python.

## API utile (exports vérifiés dans la version installée)
| API | Rôle | Équivalent moteur Python |
|---|---|---|
| `<Composition id width height fps durationInFrames defaultProps>` | déclare une vidéo | `W, H, FPS, DURATION` |
| `useCurrentFrame()`, `useVideoConfig()` | image courante, fps | `t = n / FPS` |
| `interpolate(frame, [a, b], [v0, v1], {easing, extrapolateLeft:'clamp', extrapolateRight:'clamp'})` | progression bornée et easée | `lerp(v0, v1, ease(seg(t, a, b)))` |
| `Easing.out(Easing.cubic)`, `Easing.bezier(x1, y1, x2, y2)`, `Easing.in(Easing.exp)` | courbes | `out_cubic`, `bezier`, `in_expo` |
| `spring({frame, fps, config: {damping, stiffness, mass}})` + `measureSpring` | ressort, durée réelle | `spring()` de `motion-timing` |
| `<Sequence from durationInFrames>` | décale le temps des enfants | sections `SECTIONS` / `*_shifted` |
| `<Series>`, `<Loop>`, `<Freeze>` | enchaîner, boucler, figer | |
| `<Img src={staticFile('x.png')}>` | image de `public/` (le rendu attend son chargement) | `place()` |
| `<Audio>` / `<Html5Audio>`, `<OffthreadVideo>` | son, vidéo incrustée (précise à l'image) | mux ffmpeg |
| `random('seed')` | hasard déterministe | `random.Random(seed)` |
| `delayRender()` / `continueRender()` | attendre une ressource asynchrone (police, JSON) | |
| `interpolateColors(frame, [a, b], ['#f00', '#00f'])` | couleur | `mix()` |

Correspondance du ressort : `damping` 10–14 et `stiffness` 150–200 donnent ≈ 8–12 % de dépassement (vivant) ;
`damping: 200` supprime le rebond. `measureSpring({fps, config})` donne la durée réelle, à utiliser pour caler
le son au contact.

## Pièges
- **Chromium** : dans le conteneur cloud, il faut utiliser le headless shell préinstallé (`REMOTION_CHROMIUM`, voir
  `remotion.config.ts`). Sinon Remotion tente d'en télécharger un.
- **Plage de couleurs** : sans `Config.setColorSpace('bt709')`, la sortie est en `yuvj420p` (plein écart),
  que `check_delivery.py` signale. Le gabarit le règle.
- **Flou de mouvement** : il n'y en a pas par défaut. `@remotion/motion-blur` (`<Trail>`, `<CameraMotionBlur>`)
  existe mais multiplie le coût. On le réserve aux mouvements rapides, comme dans le moteur Python.
- **Polices** : les charger via `@remotion/google-fonts` ou `staticFile` + `delayRender`, sinon la
  première image s'affiche avec une police de repli.
- **Performance** : `--concurrency` (par défaut la moitié des cœurs) ; les filtres CSS (`blur`, `drop-shadow`)
  coûtent cher sur de grandes images.
- **Grain papier** : il n'y a pas de bruit natif. On superpose une image ou une vidéo de grain en `mix-blend-mode: multiply`, ou
  un `<canvas>` seedé par l'image.

## Rendu et relecture
```bash
npx remotion render Film out/film.mp4 --frames=0-59      # passage seulement
npx remotion still Film out/f45.png --frame=45           # une image
npx remotion render Film out/film.mp4 --props='{"looks":["a.png","b.png","c.png"]}'   # déclinaison
python3 ../.claude/skills/motion-review/scripts/contact_sheet.py out/film.mp4 --step 0.25 --bpm 120
```
La durée peut dépendre des props via `calculateMetadata` sur `<Composition>` (par exemple `looks.length * 60` images).
