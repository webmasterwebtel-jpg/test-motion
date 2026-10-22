"""Texte de la voix off MyWebtel, découpé en scènes et en segments.

Chaque segment est synthétisé séparément : on connaît donc l'instant exact où il commence, ce qui sert à caler l'image
sur la parole (un mot énuméré = un segment). `gap` est le silence après le segment (s), `speed` la vitesse Kokoro.
Les scènes commencent sur la grille des temps (100 BPM, 1 temps = 0,6 s) ; `lead` = délai entre le début de la scène
et la première parole.

Règles d'écriture (motion-timing, recherche de rythme) : phrases courtes, une idée par plan, ~130–140 mots/min,
respirations franches entre les idées. Le contenu ne reprend que des fonctions décrites dans le dossier fonctionnel.
"""

BPM = 100
BEAT = 60.0 / BPM          # 0,6 s = 18 images à 30 i/s
VOICE = "ff_siwis"
SPEED = 0.94

# (texte, gap après en secondes[, vitesse ou None[, nombre de parties à repérer[, calage "beat" ou "bar"]]])
# Les énumérations sont dites d'un seul tenant (prosodie naturelle) ; leurs mots sont retrouvés par les micro-silences.
SCENES = [
    dict(id="hook", lead=1.2, segs=[
        ("Pointer son arrivée.", 0.32),
        ("Demander un congé.", 0.32),
        ("Retrouver sa fiche de paie.", 0.32),
        ("Suivre un devis.", 0.75),
        ("Chaque jour, des dizaines de petites démarches.", 0.9),
    ]),
    dict(id="reveal", lead=0.3, segs=[
        ("Et si tout se faisait au même endroit ?", 1.0),
        ("MyWebtel.", 0.45, 0.9, 1, "bar"),     # révélation sur le premier temps : silence « keynote » avant le logo
        ("L'intranet, version Webtel.", 1.0),
    ]),
    dict(id="vision", lead=0.6, segs=[
        ("Collaborateurs, horaires, congés, documents, annonces et devis :", 0.25),
        ("tout est réuni sur une seule plateforme.", 0.9),
    ]),
    dict(id="roles", lead=0.3, segs=[
        ("Et chacun n'y voit que ce qui le concerne.", 0.6),
        ("Salarié, manager, RH, direction, administrateur :", 0.25),
        ("chaque rôle a son espace, et ses propres droits.", 1.0),
    ]),
    dict(id="pointage", lead=0.6, segs=[
        ("Votre journée commence d'un geste.", 0.55),
        ("Arrivée, pause, retour, départ.", 0.7, 0.84, 4),
        ("En cas d'oubli ou de retard, les RH sont prévenues en fin de journée.", 0.4),
        ("Et chaque correction garde son historique.", 1.0),
    ]),
    dict(id="conges", lead=0.6, segs=[
        ("Besoin de congés ?", 0.4),
        ("Choisissez vos dates, indiquez le motif, ajoutez un justificatif.", 0.55),
        ("La demande suit le bon circuit de validation,", 0.25),
        ("et votre solde s'actualise, tout seul.", 1.0),
    ]),
    dict(id="documents", lead=0.6, segs=[
        ("Vos fiches de paie et vos documents RH vous attendent, à vous seul.", 0.5),
        ("Prévisualisez, téléchargez, commentez.", 1.0, 0.86, 3),
    ]),
    dict(id="annonces", lead=0.6, segs=[
        ("Les notes de la direction et des RH sont publiées pour tous.", 0.45),
        ("Chacun confirme sa lecture d'un simple clic.", 1.0),
    ]),
    dict(id="devis", lead=0.6, segs=[
        ("Chaque demande de devis venue des sites du groupe arrive directement dans MyWebtel.", 0.5),
        ("On la prend en charge,", 0.2),
        ("on la suit,", 0.2),
        ("on la clôture.", 0.45),
        ("Rien ne se perd.", 1.0),
    ]),
    dict(id="reglages", lead=0.6, segs=[
        ("Les comptes, les rôles, les horaires, les accès :", 0.25),
        ("tout se règle en quelques clics, par l'équipe informatique.", 0.5),
        ("Après quinze minutes d'inactivité, la session se ferme d'elle-même.", 1.0),
    ]),
    dict(id="partout", lead=0.6, segs=[
        ("Sur ordinateur, tablette ou smartphone, MyWebtel vous accompagne partout.", 1.1),
    ]),
    dict(id="signature", lead=0.6, segs=[
        ("MyWebtel.", 0.5, 0.9, 1, "bar"),      # logo final sur le premier temps (accord de résolution)
        ("Tout Webtel, au même endroit.", 0.0),
    ]),
]
TAIL = 3.6        # musique seule après la dernière phrase (s)

# corrections de prononciation (phonèmes Kokoro / espeak français), vérifiées par transcription (asr.py)
OVERRIDES = [
    (r"\bTout Webtel\b", "tu wɛbtˈɛl"),      # sans accent sur « tout » (sinon « Souvez-vous »)
    (r"\bMyWebtel\b", "mˈaj wɛbtˈɛl"),     # « maï-ouèb-tèl » (seul : « Ma web telle » avec majwˈɛbtɛl)
    (r"\bWebtel\b", "wɛbtˈɛl"),            # accent final à la française (sinon « webtail »)
    (r"\bmanagers?\b", "manadʒˈœʁ"),       # le nom, pas le verbe « manager »
    (r"\brôles?\b", "ʁˈol"),               # o bref (sinon entendu « roule »)
]
