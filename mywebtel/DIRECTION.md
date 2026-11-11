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

- **27 octobre 2026 (V4) :** « c'est bien, mais trop rapide, on n'a pas le temps de bien voir ; présente bien les
  fonctionnalités ; la voix et l'accent ne sont pas bons : accent normal, voix normale, vitesse normale, pas IA ; la voix
  doit être synchronisée à la vidéo ».

- **10 novembre 2026 (V5) :** nouvelle archive IT11 : présenter **l'Agent MyWebtel** (agent IA) et la **signature de
  documents** (décompte de prestation, contrats… signés avec son nom en manuscrit ou dessiné, validé par un code envoyé
  par e-mail). Voix ElevenLabs « Simon » choisie par l'utilisateur, puis : « il dit plus avec le s » (« t'as plus qu'à »)
  et « scannère » → prononciations forcées. « La voix doit être complètement calée à la vidéo » ; refaire la vidéo dans le
  style des trois vidéos envoyées (pub Drive Academy, reportage Binance, bande-annonce GTA 6), plus de 30 s possible,
  **vraies interfaces**, bruitages et effets **sans exagérer**, pro, premium et impressionnant ; l'accent ne doit jamais
  basculer vers l'anglais ; **aux couleurs du logiciel, sans exagérer**.

- **10 novembre 2026 (V6), retour sur la V5 :** « La voix fait des fautes de prononciation ; je t'ai dit de faire une
  refonte de la vidéo en t'inspirant des 3 que je t'avais données, reconstruis tout carrément, impressionne-moi ! »

- **10 novembre 2026 (V7), retour sur la V6 :** « la voix est beaucoup mieux, on la garde ; la vidéo est un peu fade, on
  ne voit même pas bien les interfaces, c'est trop long, pas de musique entraînante (pas plus forte que la voix, juste
  un peu forte), il manque des mock-ups téléphone, tablette et PC ; faut que la vidéo soit entraînante. »

- **11 novembre 2026 (V8), retour sur la V7 :** « toujours pas ça, et pourquoi ce battement boom boom de l'écran en
  permanence ? Le mock-up de l'ordinateur n'est pas bien fait, garde la voix et fais une refonte complète, digne d'une
  présentation Apple. »

## Parti pris V8 (présentation façon keynote)
- **Une scène sombre, un appareil à la fois** : fond bleu nuit presque noir, lueurs très lentes, lumière de l'écran qui
  se répand sous l'appareil. Chaque appareil arrive de la droite, net et lent, puis cède la place au suivant.
- **Aucun battement à l'image** : ni la caméra, ni les appareils, ni le fond ne suivent la grosse caisse. Pas d'éclair,
  de fouet de caméra ni de secousse. Le rythme vient de la musique et du montage sur les mots de la voix.
- **Appareils en volume** (`film/story8.js`, CSS `.d3`) : ordinateur portable refait (capot, écran, charnière, clavier
  touche par touche, grilles, pavé tactile ; il **s'ouvre** au moment du logo), tablette et téléphone avec tranche,
  verre et reflet qui balaie l'écran à l'arrivée.
- **Typographie** : un surtitre (nom de la fonction) et un titre court dont le mot clé est en dégradé bleu/cyan, à côté
  de l'appareil ; petites légendes en pastille pendant les gros plans. Jamais de sous-titres complets.
- **Gros plans** sur la vraie interface ; la fenêtre de signature et le panneau de l'agent sortent de l'écran, entourés
  d'une lueur ; les sources de l'agent sont des pastilles reliées par des fils de lumière.
- **Voix et placement inchangés** (V6/V7, 1 min 34). Musique `music7.py` conservée ; bruitages adoucis (souffle à
  l'arrivée d'un appareil, touchers, notification ; plus de frappes ni d'éclats de verre).
- **Retour du 11 novembre au soir :** « voici le bon logo » (logo **MyWebtel**) et « la musique est trop faible, on
  entend presque rien ». Le logo MyWebtel remplace l'ancien logo Webtel au début, à la fin et dans la barre latérale de
  l'interface (mention « Espace collaborateur » dessous). La musique remonte : ~6-7 dB sous la voix pendant la parole,
  ~4-5 dB entre les phrases (au lieu de ~11 dB) ; deux transcriptions du mixage restent exactes.

## Parti pris V7 (film produit rythmé, remplacé)
- **Les interfaces en grand, dans des mock-ups** : un appareil par fonction, avec la vraie mise en page responsive de la
  plateforme (mobile sur le téléphone, tablette sur la tablette, bureau sur l'ordinateur portable). Pointage et demandes RH
  sur le téléphone, congés et signature sur le portable, absences et contenu sur la tablette, mail sur le portable et
  support sur le téléphone, agent sur le portable. Gros plans sur la zone utile de chaque écran.
- **Rythme** : musique électro-pop synthétisée à 120 BPM (`music7.py`) : intro énergique, montée sur « Et si tout se
  faisait au même endroit ? », **drop sur le logo** avec les trois appareils, groove, coupure sur « imprimer, signer,
  scanner », retour du groove **sur les éclats**, respiration de l'agent, montée, **drop final**. L'image pulse sur la
  grosse caisse, la caméra fouette d'un appareil à l'autre sur les temps, les mots clés claquent sur les mots de la voix.
- **Couleurs** : fonds alternés bleu nuit / bleu vif / clair, aux couleurs de la plateforme.
- **Durée** : 1 min 34 (voix V6 conservée, respirations raccourcies).
- **Son** : musique ~10 dB sous la voix pendant la parole, plus présente entre les phrases ; un limiteur commandé par la
  voix la garde au moins 7 dB sous elle à chaque instant. Bruitages : fouets, frappes des mots, touchers d'écran,
  notification du code sur le téléphone, éclats de verre.

## Parti pris V6 (refonte complète)
- **Ce que les trois références ont en commun** (analyse image par image) : ce sont des pubs 16:9 filmées sur l'écran
  d'un ordinateur, et toutes les trois sont **un seul mouvement de caméra continu dans un monde en 3D** où les textes,
  les cartes et les écrans sont posés dans l'espace (survol d'une carte puis plongée sur la tour Eiffel chez Drive
  Academy, travelling dans la ville et à travers des cadres de néon chez GTA, travelling de cinéma chez Binance). La V5
  gardait une fenêtre de navigateur et des zooms : c'était la mauvaise grammaire.
- **Le monde MyWebtel** : les vraies pages de l'interface sont posées sur un sol comme les quartiers d'un plan
  (Pointage, Mes congés, Mes absences, Mes documents, Mes demandes RH, Contenu, Mail, Support IT, Mon espace au
  centre). La caméra vole de page en page (on monte, on traverse le plan, on redescend) ; à chaque fonction, le
  composant utile **sort de la page en relief** (copie exacte de la page, découpée) avec un halo aux couleurs de la
  plateforme, et on s'en sert : clics, saisie, états réels.
- **Ouverture (Binance)** : nuit bleu marine en format cinéma, trait de lumière anamorphique, les démarches en cartes de
  verre qui défilent, tunnel de graduations sur « un temps fou », fils de lumière qui rassemblent tout dans un anneau ;
  le logo naît dans l'anneau sur le premier temps, la caméra le traverse et l'on découvre le plan d'en haut.
- **Corps (Drive Academy)** : mots clés tapés mot à mot sur la voix (« un clic. », « à la minute près. », « en deux
  clics. »…), pastilles ✓, curseur, cartes en verre avec halo ; le justificatif PDF arrive en volant ; la règle
  d'ancienneté devient une frise qui se remplit et un cadenas qui s'ouvre.
- **Signature** : « Imprimer. Signer. Scanner ? » sur un panneau de verre avec la feuille (impression, signature à
  l'encre, faisceau du scanner) ; sur « non. », le panneau **vole en éclats** (façon Binance) et révèle la vraie page.
- **Agent (moment fort)** : la nuit retombe sur le plan, l'étincelle de l'agent (icône réelle du bouton « Agent
  MyWebtel ») apparaît au-dessus de tout, le panneau en sort ; ses réponses envoient des **faisceaux de lumière vers les
  pages concernées** (congés, demandes RH, support) ; la demande confirmée redescend vers « Mes demandes RH ».
- **Fin (GTA)** : le plan s'illumine, le logo revient dans l'anneau sur le premier temps, avec la liste des fonctions.
- **Voix** : nouveau modèle ElevenLabs **eleven_v4** (même voix Simon), trois prises par phrase, la meilleure choisie
  par deux transcriptions (Whisper, Parakeet), la confiance mot à mot et le suivi des formants des voyelles sensibles.
  Fautes corrigées : liaisons fautives (« tu la déclare‿z‿avec », « tu signe‿z‿avec », « tu la pose‿z‿à »,
  « tu arrive‿z‿un clic », « s'ouvre‿t‿après », « t'a‿z‿une »), « MyWebtel » prononcé à l'anglaise (« web-tail ») dans
  la V5, « Mail » prononcé « mèl » (voyelle française stable, mesurée), « plu » sans « s » (20 dB sous un vrai « s »).
- **Son** : musique recomposée sur l'histoire (nappe grave de nuit, accord sur le logo, groove dans le monde, piano seul
  pour l'ancienne méthode, coupure sur « Sauf que non », section cristalline pour l'agent, montée et résolution),
  réverbération de salle commune, bruitages calés sur les gestes exportés par le film.

## Parti pris V5
- **Trois références, une seule voix visuelle.** Ouverture façon reportage (nuit bleu marine de la barre latérale, démarches
  qui flottent, l'heure qui file) ; corps façon pub produit (fond clair, vraie interface, curseur, mots-clés ponctuels et
  badges ✓ en verre bleu nuit) ; touches de bande-annonce (traits de lumière cyan aux changements d'écran, montée vers le
  logo final), toujours discrètes.
- **Couleurs du logiciel uniquement** : `#06213e`/`#041b34` (barre latérale), bleu `#008ff1`, cyan `#05daf0`, fond `#f1f7fd`.
- **Signature** : séquence pivot (« Imprimer, signer, scanner ? Sauf que non. ») puis le vrai parcours : « Mes documents »,
  badge « À signer », fenêtre « Signer le document », nom manuscrit, signature dessinée en direct, e-mail du code,
  saisie, consentement, « Signé » et signature posée sur l'aperçu du document.
- **Agent en finale** : question tapée, réponse, demande de congé préparée, confirmée par l'utilisateur
  (« Rien n'est envoyé sans ta confirmation »).
- **Synchronisation** : la voix est placée sur une grille à 100 BPM ; chaque geste du film est calé sur le mot daté
  (horodatage ElevenLabs au caractère près) ; les logos tombent sur un premier temps de mesure.
- **Voix** : ElevenLabs « Simon », `eleven_multilingual_v2`, `language_code: fr`, texte voisin transmis pour une prosodie
  continue ; « scanné » et « plu » écrits ainsi pour la prononciation ; « IT » évité à l'oral (« support informatique ») ;
  chaque prise contrôlée par transcription (Parakeet), les prises fautives refaites.

## Parti pris V4
- **Le temps de voir** : 1 min 53 au lieu de 1 min 10 ; chaque fonction a sa phrase d'introduction, ses gestes un par un,
  puis une respiration de 0,9 s où l'image se pose sur le résultat. Avant chaque changement d'écran, la caméra recule
  pour montrer la barre latérale et le clic.
- **Synchronisation** : chaque écran s'ouvre quand la voix prononce son nom (« Dans « Mes congés »… » → clic sur
  « Mes congés »), chaque bouton est cliqué sur son verbe (« commencez », « pause », « revenez », « terminez »…).
- **Voix** : Kokoro `ff_siwis` pure (le mélange avec une voix anglaise donnait l'accent jugé « pas normal »),
  vitesse 1,0 (~135 mots/min sur la durée parlée), liaisons fautives corrigées par phonèmes.

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
