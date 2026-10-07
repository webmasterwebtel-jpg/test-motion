# Canon de timing (30 i/s)

## 1. Durées de référence
| Élément | Images | Secondes | Remarque |
|---|---|---|---|
| Flash, pop d'icône, étincelle | 4–8 | 0,13–0,27 | presque subliminal |
| Petit élément (forme, ruban, étiquette) | 6–9 | 0,2–0,3 | |
| Sticker, carte, visuel moyen | 9–12 | 0,3–0,4 | le standard du film (0,34 s) |
| Transition plein cadre (volet, iris, glissé) | 10–18 | 0,33–0,6 | |
| Mouvement de caméra, plongée | 15–30 | 0,5–1,0 | |
| Sortie | 60–70 % de l'entrée | | on ne regarde pas partir |
| Tenue produit | ≥ 40 | ≥ 1,3 | préférence du projet : ~2 s par look |
| Dernier plan | ≥ 45 | ≥ 1,5 | |

Selon la distance : `durée ≈ durée_ref × √(distance / distance_ref)`. Un glissé d'un écran entier
(1080 px) en 0,3 s est vif. Sur 300 px, 0,16 s suffit.

## 2. Valeurs mesurées des courbes (`easings.py --list`)
| Courbe | Valeur à mi-durée | Remarque |
|---|---|---|
| `out_cubic` | 0,88 | 97 % atteints à 70 % de la durée |
| `out_quint` | 0,97 | arrive très tôt : la fin paraît « collée » |
| `out_expo` | 0,97 | claque, très vif ; les 50 derniers % sont presque immobiles |
| `in_out_cubic` | 0,50 | déplacement neutre |
| `in_out_sine` | 0,50 | plus doux, pour les flottements |
| `in_cubic` | 0,12 | chute, sortie |

`out_back(x, s)` : dépassement et instant où la cible est atteinte pour la première fois.
| s | dépassement | cible atteinte à |
|---|---|---|
| 1.0 | 3,7 % | 50 % de la durée |
| 1.2 | 5,3 % | 46 % |
| 1.4 | 7,1 % | 42 % |
| 1.6 | 9,0 % | 39 % |
| 1.70158 | 10 % | 37 % |
| 2.0 | 13,2 % | 34 % |
| 2.5 | 18,9 % | 29 % |

## 3. Ressorts (`spring(t, damping, freq)`)
| damping | freq (Hz) | dépassement | posé (±1 %) à | caractère |
|---|---|---|---|---|
| 0.3 | 6 | 37 % | 0,38 s | élastique, ludique |
| 0.4 | 6 | 25 % | 0,30 s | vivant |
| 0.5 | 8 | 16 % | 0,17 s | dynamique et propre |
| 0.7 | 8 | 5 % | 0,13 s | ferme, premium |
| 1.0 | 8 | 0 % | 0,13 s | critique (aucun rebond) |

Le ressort dure ce qu'il dure : on n'impose pas sa durée, on règle `freq`. On l'utilise pour une
échelle ou une position, en appelant `spring(t - t0, d, f)` sur un temps absolu.

## 4. Grille musicale
| BPM | 1 temps | images | 1 mesure (4 temps) |
|---|---|---|---|
| 100 | 0,600 s | 18 | 2,4 s |
| 110 | 0,545 s | 16,4 | 2,18 s |
| 120 | 0,500 s | 15 | 2,0 s |
| 128 | 0,469 s | 14,1 | 1,875 s |
| 140 | 0,429 s | 12,9 | 1,71 s |

À un BPM non entier en images, arrondir **chaque** temps (`round(k * beat * fps)`) plutôt que
cumuler une durée arrondie, pour éviter la dérive.

Phrasé : les phrases musicales vont par 4 ou 8 mesures. Les changements de séquence tombent sur le
premier temps d'une phrase. Un « drop » est précédé d'une montée (riser) de 1 à 2 mesures, et souvent d'un silence d'un demi-temps.

## 5. Anticipation, squash, stagger, overlap
- **Anticipation** : un recul de 5–10 % de l'amplitude, sur 2–4 images, avec `in_out_sine`.
- **Squash à l'impact** : `sq = decay(t, t_contact, 14)` ; `sy = 1 - 0.14*sq`, `sx = 1 + 0.08*sq` (le volume est à peu près conservé).
- **Stretch pendant la vitesse** : `sy = 1 + 0.25*sin(pi*p)` sur un déplacement vertical rapide.
- **Stagger** : 0,03–0,1 s (1–3 images) entre éléments, et une cascade totale ≤ 0,3 s. Pour une grande grille,
  piloter le délai par motif (radial, diagonale, rangées, aléatoire, spirale : `_delay` dans collage.py).
- **Overlap** : les éléments secondaires (ruban, ombre, forme de fond) arrivent 2–4 images **après** l'élément principal.

## 6. Impacts et caméra
| Effet | Normal | BOOM | Décroissance (`decay` k) |
|---|---|---|---|
| Punch zoom | +2–3 % | +6–8 % | 9–12 / 7 |
| Shake | — | 10–20 px | 7–10 |
| Flash blanc | 0,3–0,5 | 0,6–0,75 | 14–16 |
| Vignette | 0,25 | 0,45–0,5 | 4–5 |
Le shake est réservé aux 3 ou 4 plus gros moments du film, sinon il perd son effet et fatigue.

## 7. Texte (si le film en contient)
- Lecture : au moins 0,5 s + 0,3 s par mot (≈ 200 mots/min), plus long pour un public large.
- Un mot à la fois sur le beat : 1 temps minimum par mot court, 2 temps pour un mot long.
- Animation lettre à lettre : un stagger de 0,03–0,045 s, chaque lettre durant 0,3 s.
- Le texte entre **après** l'image qu'il commente (0,1–0,2 s) et sort **avant** elle.
