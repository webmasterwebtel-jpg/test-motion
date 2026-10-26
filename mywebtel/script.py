"""Texte de la voix off MyWebtel (V2), découpé en scènes et en segments.

Chaque segment est synthétisé d'un seul tenant (une ou deux phrases : la prosodie reste continue) ; on connaît donc
l'instant exact où il commence, et les mots repères sont retrouvés par alignement (voir vo.py). `gap` est le silence
après le segment (s). Les scènes commencent sur la grille des temps (100 BPM, 1 temps = 0,6 s) ; `lead` = délai entre
le début de la scène et la première parole.

V2 (retour de l'utilisateur, 23/10) : rythme normal et naturel (~165-175 mots/min dans la parole, respirations courtes),
seulement les fonctions de base qu'il a citées (connexion, pointer, pause, finir la journée, justifier un pointage,
absences, ticket, documents RH, documents), rien d'inventé ; les libellés de boutons sont ceux du code réel.
"""

BPM = 100
BEAT = 60.0 / BPM          # 0,6 s = 18 images à 30 i/s
ENGINE = "kokoro"          # ou "piper:fr_FR-miro-high"
SPEAKER = 0
VOICE = "ff_siwis"          # voix française pure : le mélange avec af_heart (V2-V3) donnait un accent étranger
SPEED = 1.0
TAIL = 3.6

# (texte, gap après en secondes[, vitesse ou None[, inutilisé[, calage "beat" ou "bar"]]])
# V4 (27/10) : « trop rapide, on n'a pas le temps de bien voir » → chaque fonction est présentée en entier, avec des
# respirations ; voix française pure (sans mélange anglais : accent jugé « pas normal »), vitesse naturelle.
SCENES = [
    dict(id="hook", lead=1.0, segs=[
        ("Pointer, poser un congé, retrouver un document, écrire à un collègue…", 0.45),
        ("Au quotidien, tout cela prend du temps.", 0.6),
    ]),
    dict(id="reveal", lead=0.2, segs=[
        ("Avec MyWebtel, votre espace collaborateur,", 0.15, None, 1, "bar"),
        ("tout est réuni au même endroit.", 0.9),
    ]),
    dict(id="dashboard", lead=0.3, segs=[
        ("Dès la connexion, « Mon espace » vous présente l'essentiel de votre journée :", 0.2),
        ("votre pointage, votre solde de congés, vos documents, et la dernière note interne.", 0.9),
    ]),
    dict(id="pointage", lead=0.3, segs=[
        ("Le pointage se fait en un clic.", 0.4),
        ("Le matin, vous commencez votre journée.", 0.5),
        ("À midi, vous partez en pause, puis vous revenez.", 0.5),
        ("Et le soir, vous terminez votre journée.", 0.5),
        ("Chaque horaire est enregistré, à la minute près.", 0.9),
    ]),
    dict(id="conges", lead=0.3, segs=[
        ("Dans « Mes congés », vous voyez votre solde de jours disponibles.", 0.4),
        ("Et la règle est simple : vos droits aux congés s'ouvrent après un an d'ancienneté.", 0.9),
    ]),
    dict(id="absences", lead=0.3, segs=[
        ("La rubrique « Mes absences » vous permet de déclarer une absence, avec son justificatif.", 0.4),
        ("Les RH vérifient votre déclaration, et vous suivez son traitement.", 0.9),
    ]),
    dict(id="documents", lead=0.3, segs=[
        ("Dans « Mes documents », vous recevez tous les documents liés à votre contrat :", 0.2),
        ("contrats, avenants, attestations.", 0.35),
        ("Vous les consultez et les téléchargez à tout moment.", 0.9),
    ]),
    dict(id="demarches", lead=0.3, segs=[
        ("Pour une démarche RH, ouvrez « Mes demandes RH ».", 0.4),
        ("Choisissez le type de demande, décrivez votre besoin, puis envoyez.", 0.4),
        ("Vous suivez ensuite son traitement, étape par étape.", 0.9),
    ]),
    dict(id="contenu", lead=0.3, segs=[
        ("La rubrique « Contenu » rassemble les notes de la Direction, des RH et de l'IT.", 0.4),
        ("Après lecture, vous confirmez simplement en avoir pris connaissance.", 0.9),
    ]),
    dict(id="mail", lead=0.3, segs=[
        ("Avec « Mail », vous échangez avec vos collègues, directement depuis MyWebtel.", 0.9),
    ]),
    dict(id="support", lead=0.3, segs=[
        ("Enfin, pour un souci technique, ouvrez le « Support IT ».", 0.4),
        ("Vous ouvrez un ticket, et l'équipe informatique le prend en charge.", 0.9),
    ]),
    dict(id="signature", lead=0.5, segs=[
        ("MyWebtel.", 0.35, None, 1, "bar"),
        ("Votre espace collaborateur.", 0.6),
    ]),
]

OVERRIDES = [
    (r"\bTout Webtel\b", "tu wɛbtˈɛl"),      # sans accent sur « tout » (sinon « Souvez-vous »)
    (r"\bMyWebtel\b", "mˈaj wɛbtˈɛl"),     # « maï-ouèb-tèl » (seul : « Ma web telle » avec majwˈɛbtɛl)
    (r"\bWebtel\b", "wɛbtˈɛl"),            # accent final à la française (sinon « webtail »)
    (r"\bmanagers?\b", "manadʒˈœʁ"),       # le nom, pas le verbe « manager »
    (r"\brôles?\b", "ʁˈol"),               # o bref (sinon entendu « roule »)
    (r"\bDémarches RH\b", "demˈaʁʃ ɛʁˈaʃ"), # sans liaison fautive « démarches-z-RH »
    (r"\bMes demandes RH\b", "me dəmˈɑ̃d ɛʁˈaʃ"),  # idem « demandes-z-RH »
    (r"\bs'ouvrent\b", "sˈuvʁ"),            # le t final ne se prononce pas
    (r"\bl'IT\b", "lajtˈi"),               # sinon « l » épelé
    (r"\bdéclarez une\b", "deklaʁˈe yn"),  # liaisons facultatives, plus naturelles sans
    (r"\baprès un an\b", "apʁˈɛ ɛ̃n ˈɑ̃"),
    (r"\bnotes\b", "nˈɔt"),                # sinon « notz »
    (r"\bliés à\b", "ljˈe a"),             # liaison facultative, plus naturelle sans
    (r"\bvous ouvrez un\b", "vuz uvʁˈe ɛ̃"), # liaison obligatoire après « vous », pas après « ouvrez »
    (r"\best enregistré\b", "ɛt ɑ̃ʁəʒistʁˈe"),   # sinon « enistré »
    (r"\bouvrez le\b", "uvʁˈe lə"),          # « le » sans accent
    (r"\bpuis envoyez\b", "pyˈi ɑ̃vwajˈe"),  # pas de liaison après « puis »
    (r"\bsuivez ensuite\b", "syivˈe ɑ̃syˈit"),  # liaisons facultatives après -ez : plus naturel sans
    (r"\bconsultez et\b", "kɔ̃syltˈe e"),
    (r"\btéléchargez à\b", "teleʃaʁʒˈe a"),
    (r"\bpartez en\b", "paʁtˈe ɑ̃"),
    (r"\bfait en un\b", "fˈɛ ɑ̃n ɛ̃"),
    (r"\bMail\b", "mˈɛl"),                 # le menu « Mail » se dit « mèl »
    (r"\bIT\b", "ajtˈi"),                  # « Support IT » : « aï-ti », comme on le dit au bureau
]

# Corrections orthographiques pour les voix Piper (pas d'entrée phonétique directe)
SPELL = [
    (r"\bMyWebtel\b", "Maï Ouèbtel"),
    (r"\bWebtel\b", "Ouèbtel"),
]
