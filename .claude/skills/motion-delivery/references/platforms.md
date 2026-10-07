# Specs plateformes (vertical 9:16)

> Marges et loudness relevés en octobre 2026 (sources en bas) ; durées maximales citées de mémoire,
> à revérifier. Les interfaces et les limites changent souvent : avant une
> publication importante, on vérifie la source ou une capture réelle.

## Fichier
| | TikTok | Instagram Reels | YouTube Shorts |
|---|---|---|---|
| Résolution | 1080×1920 | 1080×1920 | 1080×1920 |
| Cadence | 24–60 i/s (30 courant) | 23–60 | 24–60 |
| Codec | H.264 (ou HEVC), yuv420p, AAC | idem | idem |
| Durée max (publication) | jusqu'à 10 min | 3 min | 3 min |
| Loudness | pas de cible publiée, ≈ −14 LUFS en interne, −1 dBTP conseillé | idem | normalisation à −14 LUFS |

Cible commune retenue pour le projet : **−14 LUFS intégrés, ≤ −1 dBTP de crête vraie, LRA ≤ 11**.

## Marges masquées par l'interface (px sur 1080×1920 : haut, bas, gauche, droite)
| Plateforme | Haut | Bas | Gauche | Droite | Ce qui masque |
|---|---|---|---|---|---|
| TikTok | 240 | 660 | 120 | 120 | onglets, légende, musique, colonne de boutons |
| Instagram Reels | 269 | 672 | 65 | 65 | en-tête, légende, boutons |
| YouTube Shorts | 288 | 672 | 48 | 192 | titre, abonnement, colonne de boutons (la plus large) |
| **Union (le plus sûr)** | **288** | **672** | **120** | **192** | pour un texte lisible partout |

Ces marges sont celles qu'on applique au **texte et aux CTA**, et elles sont prudentes. Pour le **sujet**,
le projet utilise un cadre plus permissif (y 210 → 1610, x < 940). Le bas d'une silhouette peut passer
sous la légende sans gêner la lecture du produit.

Règle générale citée par les guides : réserver ~15 % en haut, 25–35 % en bas et 10–15 % sur les côtés.

## Bonnes pratiques de contenu
- Accroche dans la 1re seconde : mouvement ou son dès l'image 0, aucune image vide.
- La lecture se fait **souvent sans le son** : le film doit se comprendre à l'image seule.
- Boucle : une fin qui « rime » avec le début (couleur, forme) favorise le revisionnage.
- Pas de bandes noires : remplir le 9:16.

## Sources
- Marges : [postiz.com — vertical video dimensions](https://postiz.com/blog/vertical-video-dimensions),
  [reap.video — safe zones](https://reap.video/blog/short-form-video-safe-zones),
  [upload-post.com — safe zone checker](https://www.upload-post.com/tools/safe-zone-checker/)
- Loudness : [Fora Soft — LUFS targets per platform 2026](https://www.forasoft.com/learn/audio-for-video/articles-audio/lufs-targets-per-platform-2026),
  [OpenClip — audio normalization](https://openclip.app/learn/audio-normalization)
