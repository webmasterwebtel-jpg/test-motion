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
SCENES = [
    dict(id="hook", lead=0.9, segs=[
        ("Pointer, faire sa pause, justifier un retard, retrouver sa fiche de paie…", 0.3),
        ("Au quotidien, tout ça prend du temps.", 0.55),
    ]),
    dict(id="reveal", lead=0.2, segs=[
        ("Avec MyWebtel, votre espace collaborateur,", 0.12, None, 1, "beat"),
        ("tout se fait au même endroit.", 0.7),
    ]),
    dict(id="login", lead=0.3, segs=[
        ("Vous vous connectez avec votre matricule, ou votre adresse e-mail professionnelle.", 0.45),
    ]),
    dict(id="clockin", lead=0.3, segs=[
        ("En arrivant, un clic sur « Activer ma session » :", 0.1),
        ("votre arrivée est enregistrée, à la minute près.", 0.3),
        ("Et le pointage se fait depuis le réseau Webtel.", 0.5, 1.0)   # à 1,08 : entendu « potage »,
    ]),
    dict(id="pause", lead=0.2, segs=[
        ("À midi, vous lancez votre pause.", 0.25),
        ("Au retour, un clic, et vous reprenez.", 0.45),
    ]),
    dict(id="clockout", lead=0.2, segs=[
        ("Le soir, « Terminer ma session » :", 0.1),
        ("votre journée est bouclée.", 0.6),
    ]),
    dict(id="justif", lead=0.2, segs=[
        ("Un oubli ou un retard ?", 0.2),
        ("Vous justifiez votre pointage en quelques secondes, avec un motif et, si besoin, une pièce jointe.", 0.55),
    ]),
    dict(id="absences", lead=0.2, segs=[
        ("Pour une absence ou un congé, vous choisissez vos dates, vous ajoutez votre justificatif,", 0.12),
        ("et vous suivez le statut de votre demande.", 0.55),
    ]),
    dict(id="ticket", lead=0.2, segs=[
        ("Un problème technique ?", 0.15),
        ("Vous créez un ticket, et vous suivez sa prise en charge.", 0.55),
    ]),
    dict(id="docsrh", lead=0.2, segs=[
        ("Vos documents RH, comme vos fiches de paie, sont disponibles à tout moment.", 0.15),
        ("Et vous seul y avez accès.", 0.5),
    ]),
    dict(id="docs", lead=0.2, segs=[
        ("Les documents de l'entreprise, eux, sont toujours à jour, et à portée de main.", 0.7),
    ]),
    dict(id="signature", lead=0.4, segs=[
        ("MyWebtel.", 0.3, None, 1, "bar"),
        ("Votre espace collaborateur.", 0.5),
    ]),
]

OVERRIDES = [
    (r"\bTout Webtel\b", "tu wɛbtˈɛl"),      # sans accent sur « tout » (sinon « Souvez-vous »)
    (r"\bMyWebtel\b", "mˈaj wɛbtˈɛl"),     # « maï-ouèb-tèl » (seul : « Ma web telle » avec majwˈɛbtɛl)
    (r"\bWebtel\b", "wɛbtˈɛl"),            # accent final à la française (sinon « webtail »)
    (r"\bmanagers?\b", "manadʒˈœʁ"),       # le nom, pas le verbe « manager »
    (r"\brôles?\b", "ʁˈol"),               # o bref (sinon entendu « roule »)
]

# Corrections orthographiques pour les voix Piper (pas d'entrée phonétique directe)
SPELL = [
    (r"\bMyWebtel\b", "Maï Ouèbtel"),
    (r"\bWebtel\b", "Ouèbtel"),
]
