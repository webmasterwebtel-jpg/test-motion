# MyWebtel — direction du film de présentation

## Demande
- **22 octobre 2026.** Vidéo motion design pro et premium pour présenter l'app MyWebtel et ses fonctionnalités. Voix off
  naturelle (« que ça ne fasse pas IA »), musique **jamais plus forte que la voix**, bruitages **sans exagération**,
  esprit **présentation Apple**, **sans sous-titres**.
- **23 octobre 2026 (V2), retour de l'utilisateur :** voix trop lente, encore « IA » → cadence normale et naturelle.
  Montrer **exactement la plateforme**, avec le **bon logo** (Webtel, cercle bleu et combiné, mention
  « MYWEBTEL · ESPACE COLLABORATEUR »), **sans rien inventer**, et les fonctions de base : pointer, aller en pause,
  finir la journée, justifier un pointage, absences, créer un ticket, documents RH, documents. « Impressionne-moi. »
  Sans captures de la plateforme en ligne (inaccessible depuis l'environnement), l'utilisateur a choisi de recréer les
  écrans dans la charte, limités à ces fonctions.

- **26 octobre 2026 (V3) :** « il faut la vraie interface ». Modules à montrer : Pointage, congés (droit après 1 an
  d'ancienneté), Mes absences, Mes documents (documents liés au contrat), Démarches RH, Contenu, Mail (discussion
  interne), Support IT (tickets). Voix naturelle, bonne prononciation, sans faute. L'utilisateur a fourni l'archive
  « MYWEBTEL_fichiers_retrouves_PARTIEL » : son aperçu HTML issu du PHP est la vraie interface utilisée par le film.

## Parti pris V3
- **La vraie interface, telle quelle** (barre latérale bleu nuit, logo, cartes, badges, libellés du PHP), chargée dans
  le film ; seuls changent les données de démonstration et les états qu'un utilisateur ferait changer.
- **Mail et Support IT** n'existent pas dans l'archive : écrans composés avec les composants de la plateforme, à
  remplacer par les vrais dès qu'ils sont disponibles.
- **Prononciation** : liaisons fautives corrigées une à une (« demandes-z-RH », « s'ouvrent-t », « l'IT » épelé…),
  chaque phrase contrôlée par transcription.

## Parti pris V2 (toujours valable pour la caméra, le logo et le son)
- **Un seul objet, une seule caméra.** La fenêtre de l'application reste à l'écran du début à la fin ; une caméra 3D
  la suit (plans larges inclinés, gros plans sur le bouton cliqué) au lieu d'enchaîner des cartes. Chaque geste tombe
  sur le mot que dit la voix (mots datés par transcription).
- **Écrans fidèles au code réel** (`webtel-intra-clean`) : structure de `app/login/page.tsx`, `app/dashboard/page.tsx`
  et `components/AttendanceCard.tsx`, styles de `app/globals.css` (Arial, marine `#112d50`, filets `#dce3ec`, fond
  `#f4f7fb`…), libellés réels (« Activer ma session », « Terminer ma session », « Session de travail active »,
  « Journée terminée », « Pointage enregistré. », « Pointage indisponible : vous devez être connecté au réseau
  Webtel. »). Les modules pause, justification, absences, tickets et documents reprennent les mêmes composants.
- **Logo réel** vectorisé depuis l'image fournie (`film/brand/`), animé : la marque tourne et se pose sur le premier
  temps, le mot se dévoile ; à « au même endroit », le logo vole jusqu'à sa place dans la carte de connexion.
- **Ouverture nuit, produit en lumière.** Les démarches du quotidien flottent dans la nuit, l'horloge s'emballe, puis la
  lumière se fait sur le logo.
- **Pas de sous-titres.** Seuls éléments de film hors application : l'heure de la journée (08:02, 12:31, 13:29, 17:46)
  et deux annotations sur le réseau Webtel.
- **Son** : voix au premier plan (~16 dB au-dessus de la musique pendant la parole), bruitages d'interface
  synchronisés automatiquement sur les gestes du film (`cues.json`).

## Voix
Kokoro, mélange 80 % `ff_siwis` + 20 % `af_heart`, vitesse 1,08 : meilleure note de naturel (NISQA-TTS 4,84 contre 4,64
pour `ff_siwis` seule ; les voix Piper françaises plafonnent vers 3,2). ~150 mots/min sur la durée parlée, respirations
courtes. Chaque segment est contrôlé par transcription (Parakeet) ; il ne reste que des homophones (« paie »/« paix »).

## Attention avant diffusion
Les écrans des modules pause, justification, absences, tickets et documents sont recréés dans la charte (le dépôt ne
contient que la connexion et le pointage) : faire valider la ressemblance avec la plateforme en service.
