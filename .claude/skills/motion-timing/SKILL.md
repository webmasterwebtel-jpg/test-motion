---
name: motion-timing
description: Canon chiffré du timing et de l'easing en motion design, avec des durées en images à 30 i/s, le choix de courbe par situation, le dépassement, l'anticipation, le squash, le stagger, les ressorts, les tenues de lecture, le calage sur le BPM et les punchs/shakes. Il fournit aussi un outil qui dessine les courbes et leur charte d'espacement image par image. Utilise ce skill dès que tu choisis ou corriges une durée, un easing, un délai, un rebond ou un rythme d'animation, ou quand on te dit que c'est trop rapide, trop lent, mou, mécanique, saccadé, que ça manque de punch ou de fluidité, même sans le mot « easing ».
---

# Timing et easing

Les choix de timing ne s'improvisent pas à chaque fois : ils suivent un canon. Je l'applique
d'office et je ne m'en écarte que pour une raison que je peux formuler. Les valeurs détaillées sont dans
`references/timing.md` ; ce fichier donne la méthode et les règles qui comptent le plus.

## Méthode

1. **Partir de la musique** : 1 temps = 60/BPM s (120 BPM = 0,5 s = 15 images ; 1 mesure = 2 s).
   On choisit d'abord le *niveau de grille* de chaque séquence :
   - présentation produit : un changement par **mesure** (2 s), le produit restant lisible au moins 1,3 s ;
   - montage énergique : un changement par **temps** ;
   - climax uniquement : au **demi-temps**, jamais plus de 2 à 4 s d'affilée.
2. **Caler les contacts sur les temps** : c'est l'instant où l'élément se pose qui tombe sur le
   beat, pas le début du mouvement. Une entrée de 0,3 s pour le temps `tb` part donc à `tb - 0,2`
   environ, ou part sur `tb` avec une claque à `tb + 0,2` (voir `motion-engine`).
3. **Choisir l'easing selon le rôle** (tableau ci-dessous), puis **le regarder** :
   ```bash
   python3 .claude/skills/motion-timing/scripts/easings.py --names out_cubic out_back:1.3 spring:0.5:7 --dur 0.33
   ```
   La charte d'espacement montre où tombent les images. Si les 2 dernières images sont
   quasiment au même endroit, l'élément « arrive » visuellement plus tôt que la durée nominale.
4. **Vérifier en contexte** avec `motion-review`.

## Quel easing pour quel rôle

| Rôle | Courbe | Dans `render.py` |
|---|---|---|
| Entrée (arrive et se pose) | décélération | `out_cubic` (sobre), `out_expo` (vif, claquant) |
| Entrée avec vie / rebond | dépassement | `out_back(p, 1.2–1.6)` ou `spring` (d=0.4–0.6) |
| Sortie (part et disparaît) | accélération | `in_cubic`, `in_expo` ; sortie ≈ 60–70 % de la durée d'entrée |
| Déplacement A → B à l'écran | accélération puis décélération | `in_out_cubic`, `in_out_sine` (doux) |
| Chute ou impact | accélération pure, puis squash | `in_cubic` puis `decay` sur `sy`/`sx` |
| Boucle, flottement, respiration | sinusoïde | `math.sin`, amplitude faible (1–2 % en échelle, ±1° en rotation) |
| Plongée de caméra / zoom infini | exponentielle | échelle `S0 * (S1/S0) ** p` (vitesse perçue constante) |
| Mécanique, stop-motion | marches | `stepped(t, 12)` + `jitter` |

**Le linéaire est interdit** pour tout mouvement de position, d'échelle ou de rotation qui démarre
ou s'arrête à l'écran. Il reste acceptable pour un défilement continu, une rotation perpétuelle ou un fondu d'opacité court.

## Règles d'or (détails et valeurs dans `references/timing.md`)

- **Durée selon la taille et la distance** : petit élément 6–9 images, carte ou sticker 9–12,
  plein cadre 12–18, caméra 15–30. Doubler la distance ne double pas la durée (règle √ : ×1,4).
- **Tenue de lecture** : produit ≥ 1,3 s immobile (préférence du projet : ~2 s par look) ;
  texte ≥ 0,5 s + 0,3 s par mot. Après une tenue de plus de 2 s, ajouter une action secondaire (flottement).
- **Dépassement** : élégant 3–6 % (`out_back` 1.0–1.3), vivant 8–12 % (1.5–1.8), cartoon 15 % et plus.
  Ne pas en mettre partout : réserver le rebond aux éléments « héros ».
- **Anticipation** : un recul de 5–10 % dans le sens opposé pendant 2–4 images avant un gros mouvement.
- **Stagger** : 1–3 images entre éléments frères, et une cascade totale de 0,3 s maximum (au-delà, on attend).
- **Impacts** : punch zoom 2–3 % (normal) à 6–8 % (BOOM), shake 8–20 px seulement sur les 3 ou 4
  plus gros moments du film, squash 8–15 % sur 2–4 images.
- **Flou de mouvement** dès qu'un élément dépasse ~40 px par image.
- **Contraste** : alterner rapide et lent. Après 3 ou 4 coupes rapides, une respiration. Un silence de 0,5 s avant un BOOM double son impact.

## Fichiers
- `scripts/easings.py` : toutes les courbes classiques, `out_back` paramétrable, `bezier(x1,y1,x2,y2)`
  (valeurs CSS/After Effects), `spring(t, damping, freq)` et `spring_settle`. Le module est importable (copier
  les fonctions utiles dans `motion/render.py`) et sert aussi à tracer les courbes (`--names`, `--dur`, `--list`).
- `references/timing.md` : le canon détaillé (durées, valeurs mesurées des courbes, ressorts, BPM, texte).
- `assets/easing-lab.html` : laboratoire interactif (artefact publié, source dans le dépôt). Choisir une courbe, régler la durée
  en images, voir l'espacement réel et copier le code Python, CSS ou Remotion. Les équivalences Remotion ont été vérifiées
  numériquement (exactes, sauf `exp` à moins de 0,001 près ; l'élastique n'a pas d'équivalent et la page le dit).
