# API du moteur de rendu (`motion/render.py` + `motion/collage.py`)

Sommaire : 1. Constantes · 2. Temps et easing · 3. Placement · 4. Visuels · 5. Fils de laine ·
6. Formes et collage · 7. Effets · 8. Texte · 9. Composition et rendu

`collage.py` importe `render as R` et réutilise ses fonctions. Les signatures ci-dessous sont
exactes à la date d'écriture. En cas de doute, `grep -n "def nom" motion/*.py`.

## 1. Constantes
| Nom | Valeur | Rôle |
|---|---|---|
| `W, H, FPS` | 1080, 1920, 30 | format vertical 9:16 |
| `BEAT` | 0.5 s | 1 temps à 120 BPM = 15 images ; 1 mesure = 2 s |
| `BUILD` | `build/` | sorties intermédiaires (détourages, segments, audio) |
| `YARN` | 7 couleurs | rose, orange, jaune, turquoise, bleu, violet, rouge des fils |
| `LOOK_COLOR[i]` | RGB | couleur signature de la tenue `i` (1–24) |
| `BG` (collage) | (250, 246, 240) | papier blanc chaud |
| `CX, CY, CS` (collage) | 540, 935, 0.80 | pose standard d'un sticker (dans la zone sûre TikTok) |
| `PAD` (collage) | 40 | marge ajoutée autour des stickers (liseré + ombre) |
| `PALETTES` (collage) | 4 × 4 couleurs | palettes des carrés granny |
| `COUPLES` | {3, 4, 6, 7, 8, 11, 14, 19, 21} | visuels à deux personnes (cadrage plus large) |

Les visuels sources font 1024×1536, centre (512, 768) : les coordonnées « image » des fonctions
(ancres, points de détail) sont dans ce repère.

## 2. Temps et easing (render.py)
- `seg(t, a, b)` : la progression 0→1 de t entre a et b, bornée. C'est **la** brique de toute animation.
- `clamp01`, `lerp(a, b, x)`, `mix(c1, c2, x)` (couleurs), `tint(c, x=0.86)` (éclaircir vers le blanc).
- Easings `x∈[0,1]` : `out_cubic`, `in_cubic`, `in_out_cubic`, `in_out_sine`, `out_expo`, `in_expo`,
  `out_back(x, s=1.70158)`, `in_back(x, s)`. Le choix de l'easing est détaillé dans `motion-timing`.
- `decay(t, t0, k=8)` : une impulsion exponentielle après t0 (0 avant). Elle sert aux punchs, shakes et pulses sur le beat.
- `stepped(t, fps=12)` (collage) : le temps quantifié façon stop-motion. `jitter(t, amp, seed, fps=12)` : le tremblé aléatoire tenu sur 1/12 s.

Motif type : `p = seg(t, t0, t0 + 0.34); x = lerp(depart, arrivee, out_back(p, 1.4))`.

## 3. Placement : `place(canvas, im, cx, cy, s=1, rot=0, alpha=1, anchor=None, sx=1, sy=1, ry=0, clip=None, wash=0, key=None)`
Le point `anchor` de l'image (par défaut son centre) est posé en (cx, cy) avec :
- l'échelle `s`, l'étirement `sx`/`sy` (squash & stretch) et la rotation `rot` en degrés (sens horaire à l'écran) ;
- `ry` : une rotation 3D autour de l'axe vertical avec perspective (focale 2200 px), pour un flip ou un cover-flow ;
- `clip=(x0, y0, x1, y1)` : un masque rectangulaire, pour les volets, les révélations et les cases de grille ;
- `wash` : un délavage vers le blanc (0–1), pour un flash d'entrée ou les cartes en arrière-plan ;
- `key` : si `s < 0.55` et que `_IMG[(key, "half")]` existe, la version demi-taille est utilisée
  (plus nette et plus rapide). **Toujours passer `key`** pour les visuels.
Coût proportionnel à la surface affichée. C'est la fonction la plus appelée.

Raccourcis : `R.avatar(c, i, cx, cy, s, **kw)` (visuel brut avec ombre au sol),
`R.closeup(c, i, (ax, ay, cw), zoom, rot, dx, dy)`, `sticker(c, i, cx=CX, cy=CY, s=CS, anchor, **kw)`
(collage : visuel détouré avec liseré blanc et ombre dure ; `anchor` en coordonnées image, `PAD` est ajouté automatiquement).

## 4. Visuels
- `motion/prep.py` → `build/cutouts/article_XX.png` (détourage du fond blanc). À relancer si les
  visuels changent.
- `R.load_images()` remplit `R._IMG[i]` et `R._IMG[(i, "half")]`. `collage.load()` ajoute les
  stickers `R._IMG[("st", i)]` et `_ST[i]`.
- `silhouette(i, color)` : l'aplat de couleur à la forme du sticker (échos riso).
- `swayed_img(im, t, amp)` : une ondulation horizontale croissante vers le bas, pour les franges qui bougent.
  Elle est coûteuse : ne l'appliquer qu'au visuel principal.
- `look_frame(i)` : l'image plein cadre « look i sur fond teinté » (mise en cache), utilisée par la mosaïque.

## 5. Fils de laine
- `catmull(points, n=24)` : une spline passant par les points, qui renvoie une polyline (np.array N×2).
- `_arclen(pts)` : les abscisses curvilignes cumulées. `sub_path(pts, L0, L1)` : un tronçon.
- `draw_yarn(c, pts, width=12, colors=None, L0=0, L1=None, seglen=150, alpha=1, shadow=True)` : un fil
  torsadé multicolore (une couleur tous les `seglen` px). **Pour animer un fil qui se dessine**, faire
  varier `L1` (la tête) et `L0` (la queue) : `draw_yarn(c, pts, 10, cols, tot*in_cubic(p), tot*out_expo(p))`.
- `orbit(...)` et `draw_orbit(c, cx, cy, rx, ry, phase, layer, colors, width, span, tilt, grow, alpha)` :
  une ellipse partielle autour d'un sujet. Appeler une fois avec `layer="back"` **avant** le sujet,
  puis avec `"front"` **après** : le fil passe derrière puis devant.

## 6. Formes et collage (collage.py)
- `shape(c, kind, x, y, r, rot, color, alpha)` avec `kind` ∈ circle, arch, star, half, squircle.
- `tape(c, x, y, ang, w=190, h=54, color, alpha=0.75, p=1)` : un ruban adhésif ; `p` le fait se dérouler.
- `granny(size, pal_idx)` : un carré granny procédural (mis en cache), à poser ensuite avec `place`.
- `ball(c, x, y, r, rot, color)` : une pelote de laine.
- `bgfill(c, color)` : un fond uni.

## 7. Effets
Par image, chaque section remplit le dict `fx`, que `compose` applique ensuite :
| Clé | Effet | Usage type |
|---|---|---|
| `punch` | zoom caméra additif | `fx["punch"] += 0.03 * decay(t, tb, 10)` sur un impact |
| `shake` | tremblement (px) | `fx["shake"] += 12 * decay(t, tb, 9)` |
| `vig` | vignette sombre (0–1) | sur un BOOM |
| `flash` | `(couleur, alpha)` plein cadre | `(WHITE, 0.6 * decay(t, tb, 16))` |
| `mb` | sous-images de flou de mouvement (1 = aucun) | 3–6 pendant les mouvements rapides (coût ×mb) |
| `cam_scale`, `cam_dx`, `cam_dy` | caméra (multiplier ou ajouter, ne pas écraser) | plongée vers un point |
| `post` | liste de fonctions `fn(frame)` appliquées **après** la caméra | iris, incrustations fixes à l'écran |

Fonctions directes : `ripple(c, t, t0, cx, cy, color, maxr, dur, width, strength)` (une onde de choc),
`flash(c, color, a)`, `vignette_pulse(c, amount)`, `sparkle(c, x, y, r, a, color)`,
`iris(frame, t, t0, t1, shot)` (une ouverture circulaire bordée de fil vers le plan suivant).

Plongée de caméra vers un point (px, py) : `k = 1 + z; fx["cam_scale"] *= k;
fx["cam_dx"] -= (px - W/2) * (k - 1); fx["cam_dy"] -= (py - H/2) * (k - 1)`.

## 8. Texte (render.py, inutilisé dans le film « sans texte »)
`text(...)`, `text_letters(...)` (lettres qui tombent, effet slam), `text_mask_reveal(...)` (montée
depuis un masque), `pill(...)` (étiquette noire), `fit_size(...)`. Polices dans `assets/fonts/` :
Anton, Montserrat (Medium, Bold, Black), Playfair Italic et BlackItalic.

## 9. Composition et rendu
- `SECTIONS = [(debut, fin, fonction), ...]` : chaque fonction `sec_x(c, t, fx)` dessine sur `c` si
  `debut <= t < fin`. Les plages **peuvent se chevaucher** (passage de relais), et l'ordre de la
  liste est l'ordre de dessin.
- Pour réutiliser une section écrite pour d'autres temps, utiliser une fonction décalée :
  `sec_wow_shifted = lambda c, t, fx: sec_wow(c, t - WOW_SHIFT, fx)`.
- `compose(t)` crée la toile `BG`, appelle les sections, puis applique flash, vignette, caméra
  (punch et shake, avec un hasard seedé par t) et enfin `post`. Elle renvoie `(frame, mb)`.
- `render_frame(n)` calcule le flou de mouvement en moyennant `mb` compositions sur un obturateur à 180°
  (0,5/FPS), puis ajoute le grain papier (4 motifs qui alternent à 12 i/s). **Elle doit rester une
  fonction pure de n** : elle tourne en parallèle dans un `Pool`.
- `main()` : `--stills t1 t2…` → `build/stills_collage/`, `--range a b` → aperçu, sans argument →
  des segments de 5 s mis en cache dans `build/collage_segments/<md5 du code>/` puis concaténés.
