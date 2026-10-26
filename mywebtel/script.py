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
VOICE = "ff_siwis:0.8,af_heart:0.2"   # timbre français, 20 % de la voix la plus naturelle de Kokoro (NISQA-TTS 4,84 contre 4,64)
SPEED = 1.08
TAIL = 3.0

# (texte, gap après en secondes[, vitesse ou None[, inutilisé[, calage "beat" ou "bar"]]])
# V3 (26/10) : les modules demandés par l'utilisateur, avec les libellés réels de la plateforme (aperçu PHP du 14/10).
SCENES = [
    dict(id="hook", lead=0.9, segs=[
        ("Votre journée, vos démarches, vos échanges…", 0.25),
        ("Tout passe désormais par un seul endroit.", 0.5),
    ]),
    dict(id="reveal", lead=0.2, segs=[
        ("MyWebtel, votre espace collaborateur.", 0.6, None, 1, "bar"),
    ]),
    dict(id="pointage", lead=0.3, segs=[
        ("Le matin, vous commencez votre journée en un clic.", 0.2),
        ("Votre pause, votre retour, votre départ :", 0.1),
        ("tout est enregistré, à la minute près.", 0.5),
    ]),
    dict(id="conges", lead=0.2, segs=[
        ("Côté congés, la règle est simple :", 0.1),
        ("vos droits s'ouvrent après un an d'ancienneté.", 0.5),
    ]),
    dict(id="absences", lead=0.2, segs=[
        ("Dans « Mes absences », vous déclarez une absence avec son justificatif,", 0.1),
        ("et vous suivez sa vérification par les RH.", 0.5),
    ]),
    dict(id="documents", lead=0.2, segs=[
        ("« Mes documents », c'est l'endroit où vous recevez tous les documents liés à votre contrat.", 0.5),
    ]),
    dict(id="demarches", lead=0.2, segs=[
        ("Une démarche RH ?", 0.15),
        ("Dans « Mes demandes RH », vous choisissez le type de demande, vous remplissez le formulaire,", 0.1),
        ("et vous suivez son traitement au même endroit.", 0.5),
    ]),
    dict(id="contenu", lead=0.2, segs=[
        ("Dans « Contenu », vous lisez les notes de la Direction, des RH et de l'IT,", 0.1),
        ("et vous confirmez votre lecture.", 0.45),
    ]),
    dict(id="mail", lead=0.2, segs=[
        ("Avec « Mail », vous échangez avec vos collègues, en interne.", 0.45),
    ]),
    dict(id="support", lead=0.2, segs=[
        ("Un souci technique ?", 0.15),
        ("Dans « Support IT », vous ouvrez un ticket, et l'équipe informatique le prend en charge.", 0.6),
    ]),
    dict(id="signature", lead=0.4, segs=[
        ("MyWebtel.", 0.3, None, 1, "bar"),
        ("Tout Webtel, au même endroit.", 0.5),
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
    (r"\bMail\b", "mˈɛl"),                 # le menu « Mail » se dit « mèl »
    (r"\bIT\b", "ajtˈi"),                  # « Support IT » : « aï-ti », comme on le dit au bureau
]

# Corrections orthographiques pour les voix Piper (pas d'entrée phonétique directe)
SPELL = [
    (r"\bMyWebtel\b", "Maï Ouèbtel"),
    (r"\bWebtel\b", "Ouèbtel"),
]
