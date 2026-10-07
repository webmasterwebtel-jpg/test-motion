# Bibliothèque de sons et recettes

Tous les sons sont synthétisés (numpy et scipy) à 48 kHz. Le mixage se fait sur des bus stéréo de
`N = SR * DUR` échantillons.

## Primitives (`motion/audio.py`)
| Fonction | Son | Usage |
|---|---|---|
| `add(bus, x, t0, gain=1, pan=0)` | place un son mono ou stéréo à t0, pan à puissance constante (-1…1) | **tout** placement |
| `impact(big=1, dur=2.2)` | sub qui descend, souffle et craquement | BOOM, révélation |
| `heartbeat()` | battement grave | suspense, intro |
| `whoosh(dur, f0, f1, peak)` | souffle filtré balayé ; `peak` = position du maximum (0–1) ; pan gauche→droite intégré | transitions, passages |
| `snap()`, `tick()` | claquement de doigts, clic sec | crans, petits pops |
| `yarn_slide(dur, level)` | frottement de fil granuleux | fil qui se déroule |
| `riser(dur, level)` | montée bruit et sinus | préparation d'un drop (finir **sur** l'impact) |
| `rev_cymbal(dur, level)` | cymbale inversée | aspiration avant un temps fort |
| `shimmer(dur)` | scintillement de notes aiguës | magie, final |
| `crash()` | cymbale | accent |
| `reverb(x, wet, dur, decay)` | réverbe par convolution | cohésion, à mettre sur le bus entier |
| `limiter(x, ceiling)`, `envelope(x)` | limiteur et suiveur d'enveloppe | mix, ducking |
| filtres `bp`, `hp`, `lp`, `svf_sweep` | | façonner des sons |

## Sons propres au collage (`motion/audio_collage.py`)
`paper_slap(level)` (sticker plaqué), `tape_rip(dur)` (ruban arraché), `pop(f0, f1)` (bloup d'iris),
`clatter(dur, n)` (nuée de clics, carreaux), `clack()` (case qui se verrouille).

## Recettes
**Entrée d'un sticker au temps `tb` (contact à `tb + c`)**
```python
add(b, whoosh(0.3, 600, 5000, 0.6), tb - 0.08, 0.5, -0.3)   # pic vers tb+0.10
add(b, paper_slap(), tb + c, 0.85, rng.uniform(-0.3, 0.3))  # c = instant où l'image se pose
```
**BOOM après un silence**
```python
add(b, riser(1.0, 0.3), tb - 1.0)          # finit pile sur tb
add(b, impact(1.4, 2.4), tb, 1.0)
add(b, shimmer(0.8), tb + 0.05, 0.6)
# puis, sur le bus final : b[i(tb-0.5):i(tb)] = 0 (le silence coupe aussi les queues de réverbe)
```
**Cascade (grille, carreaux)** : un `clack()` par élément avec le même stagger que l'image
(`tb + 0.045*j + latence`) et un pan qui suit la position (`(x/W - 0.5) * 1.6`).

## Mix (préférences du projet)
- Musique ≈ −11 dB sous les bruitages (`mix = m*0.24 + s*0.8` après normalisation des deux bus).
- Avec une voix off : ducking de la musique d'environ 7 dB sous la voix, sans changer les bruitages.
- Fondu de sortie de 0,8 s, puis loudnorm dans `make.sh` (voir `motion-delivery` pour les cibles).

## Niveau de densité
Dans une seconde de film, on vise au maximum 3 ou 4 bruitages distincts au premier plan. Au-delà, il faut supprimer
les moins importants plutôt que baisser tout le monde.
