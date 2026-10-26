#!/usr/bin/env python3
"""Prépare les vrais écrans MyWebtel pour le film, à partir de l'aperçu HTML issu du PHP (APERCU-MYWEBTEL.html).

L'aperçu (archive « MYWEBTEL_fichiers_retrouves_PARTIEL », PHP du 14/10/2026) contient le rendu réel de 9 écrans :
Mon espace, Pointage, Mes congés, Mes absences, Mes documents, Signature, Mes demandes RH, Contenu, Mon profil.
On garde leur HTML et leur CSS tels quels, avec seulement :
  - les scripts retirés et les transitions CSS coupées (rendu image par image reproductible) ;
  - des données de démonstration plus parlantes que « Compte TEST » (noms, textes de notes, documents, demandes) ;
  - la coquille « transmise à au service RH » corrigée ;
  - deux entrées de menu, « Mail » et « Support IT », que l'utilisateur a demandé de montrer mais qui sont absentes
    de l'aperçu : leurs écrans sont composés avec les composants et les classes de la plateforme (mw-*).
Des attributs data-film repèrent les éléments que le film anime.

Les écrans sont internes à Webtel : la sortie va dans build/ (non versionné), jamais dans le dépôt.
Usage : python3 mywebtel/prep_ui.py chemin/vers/APERCU-MYWEBTEL.html  ->  build/mywebtel/ui.json
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "build", "mywebtel")
SVG = '<svg class="mw-icon " viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>'
ICON_MAIL = SVG.format('<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>')
ICON_SUPPORT = SVG.format('<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/><path d="M19 20a4 4 0 0 1-4 2h-2"/>')
ICON_DOC = SVG.format('<path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8m-8 4h8"/>')
ICON_SEND = SVG.format('<path d="M21 3 10 14M21 3l-7 18-4-7-7-4z"/>')
ICON_CHEV = SVG.format('<path d="m9 6 6 6-6 6"/>')
ICON_UPLOAD = SVG.format('<path d="M7 18a5 5 0 1 1 1-9.9A6 6 0 0 1 19 10a4 4 0 0 1 0 8M12 12v9m-3-6 3-3 3 3"/>')
ICON_LOCK = SVG.format('<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>')

NOTE_TITLE = "Organisation de la fin d’année"
NOTE_BODY = ("Bonjour à toutes et à tous.<br />\nLes bureaux de Ouakam et de Sacré-Cœur 3 fermeront à 13 h le 31 décembre.<br />\n"
             "Merci d’envoyer vos demandes de congés de fin d’année avant le 30 novembre.")
FREEZE = "<style>*,*:before,*:after{transition:none!important;animation:none!important;caret-color:transparent!important}</style>"


def load_pages(path):
    s = open(path, encoding="utf-8").read()
    i = s.index("const pages=") + len("const pages=")
    pages, _ = json.JSONDecoder().raw_decode(s, i)
    return pages


def common(h, active=None):
    h = re.sub(r"<script.*?</script>", "", h, flags=re.S)
    h = h.replace("</head>", FREEZE + "</head>")
    h = h.replace("Compte TEST", "Aïssatou Ndiaye").replace('<span class="mw-avatar">CT</span>', '<span class="mw-avatar">AN</span>')
    h = h.replace('aria-label="Mon compte">CT</a>', 'aria-label="Mon compte">AN</a>')
    h = h.replace("transmise à au service RH", "transmise au service RH")
    h = h.replace("RH-TEST-001", "RH-2026-011")
    # menu : Mail et Support IT après Contenu
    extra = (f'<a href="/mail" data-film="nav-mail">{ICON_MAIL}<span>Mail</span></a>'
             f'<a href="/support" data-film="nav-support">{ICON_SUPPORT}<span>Support IT</span></a>')
    h = re.sub(r'(<a href="/content"[^>]*>.*?</a>)', lambda m: m.group(1) + extra, h, count=1, flags=re.S)
    for href, key in (("/dashboard?personal=1", "dashboard"), ("/attendance", "attendance"), ("/leaves", "leaves"), ("/absences", "absences"),
                      ("/documents", "documents"), ("/hr-requests", "requests"), ("/content", "content")):
        h = h.replace(f'<a href="{href}"', f'<a data-film="nav-{key}" href="{href}"', 1)
    if active:                                       # page composée : déplacer l'état actif du menu
        h = re.sub(r'(<a data-film="nav-[a-z]+" href="[^"]+") class="active" aria-current="page">(.*?)<span class="mw-nav-glow"></span></a>',
                   r'\1>\2</a>', h, count=1, flags=re.S)
        h = h.replace(f'<a href="/{active}" data-film="nav-{"mail" if active == "mail" else "support"}">',
                      f'<a href="/{active}" data-film="nav-{"mail" if active == "mail" else "support"}" class="active" aria-current="page">')
        h = re.sub(rf'(data-film="nav-{"mail" if active == "mail" else "support"}" class="active" aria-current="page">.*?</span>)</a>',
                   r'\1<span class="mw-nav-glow"></span></a>', h, count=1, flags=re.S)
    return h


def main_of(h):
    return h.index('<main id="mw-main"'), h.index("</main>") + len("</main>")


def set_main(h, new):
    a, b = main_of(h)
    return h[:a] + new + h[b:]


def set_title(h, title, doc_title):
    h = re.sub(r"(<header class=\"mw-topbar\">.*?</button>)<h1>.*?</h1>", lambda m: m.group(1) + f"<h1>{title}</h1>", h, count=1, flags=re.S)
    return re.sub(r"<title>.*?</title>", f"<title>{doc_title} · MyWebtel</title>", h, count=1)


def req_hooks(h):
    """Repères du film dans « Mes demandes RH » (servent aussi à l'écran Support IT, bâti sur le même modèle)."""
    h = h.replace("Texte de démonstration pour les tests internes.", "Attestation demandée pour un dossier bancaire.")
    new_req = (f'<details class="mw-request-detail" data-status="pending" data-film="req-new"><summary><span class="mw-tile">{ICON_DOC}</span><span><b>Attestation de salaire</b>'
               f'<small>RH-2026-014 · 26/10/2026</small></span><span class="mw-badge amber" data-film="req-badge">Envoyée</span>{ICON_CHEV}</summary></details>')
    h = h.replace('<details class="mw-request-detail" data-status="pending">', new_req + '<details class="mw-request-detail" data-status="pending">', 1)
    h = h.replace('<div class="mw-category-choices">', '<div class="mw-category-choices" data-film="req-cats">')
    h = h.replace('<input name="subject"', '<input data-film="req-subject" name="subject"').replace('<textarea name="description"', '<textarea data-film="req-desc" name="description"')
    return re.sub(r'<button class="mw-button">(<svg.*?</svg>)Envoyer la demande</button>', r'<button class="mw-button" data-film="req-send">\1Envoyer la demande</button>', h, count=1, flags=re.S)


def build(pages):
    ui = {}
    # --- Mon espace
    h = common(pages["dashboard"])
    h = h.replace("Bonjour <em>Compte.</em>", "Bonjour <em>Aïssatou.</em>")
    h = h.replace("<time data-live-clock>18:08<small>:10</small></time>", '<time data-live-clock data-film="clock">07:28<small>:40</small></time>')
    h = re.sub(r"(<h3>Organisation de la fin d’année</h3><p>).*?(</p>)", lambda m: m.group(1) + NOTE_BODY.replace("<br />\n", " ") + m.group(2), h, count=1, flags=re.S)
    h = h.replace('<a class="mw-button mw-wide" href="/attendance">', '<a class="mw-button mw-wide" data-film="open-attendance" href="/attendance">')
    ui["dashboard"] = h
    # --- Pointage : repères pour les quatre états
    h = common(pages["attendance"])
    h = h.replace('<span class="mw-badge amber">Journée à commencer</span>', '<span class="mw-badge amber" data-film="day-badge">Journée à commencer</span>')
    h = h.replace('<div class="mw-timeline">', '<div class="mw-timeline" data-film="steps">')
    h = re.sub(r'<button class="mw-button mw-wide">(<svg.*?</svg>)Commencer ma journée</button>',
               r'<button class="mw-button mw-wide" data-film="punch">\1<span data-film="punch-label">Commencer ma journée</span></button>', h, count=1, flags=re.S)
    for k, label in enumerate(["Début de journée", "Pause", "Retour de pause", "Fin de journée"]):
        h = re.sub(rf'(<span>{label}</span>)<b>—</b>', rf'\1<b data-film="today-{k}">—</b>', h, count=1)
    h = h.replace('<section class="mw-card mw-today">', '<section class="mw-card mw-today" data-film="today">')
    ui["attendance"] = h
    # --- Mes congés
    h = common(pages["leaves"])
    h = h.replace('<span class="mw-hint">', '<span class="mw-hint" data-film="seniority">', 1)
    h = h.replace('<p class="mw-muted">Vous avez au moins un an d’ancienneté.', '<p class="mw-muted" data-film="seniority-text">Vous avez au moins un an d’ancienneté.')
    h = h.replace('<div class="mw-leave-metrics">', '<div class="mw-leave-metrics" data-film="metrics">')
    ui["leaves"] = h
    # --- Mes absences : suivi rempli (une déclaration en vérification, une traitée)
    h = common(pages["absences"])
    items = (f'<details class="mw-request-detail" data-status="pending" data-film="abs-new"><summary><span class="mw-tile">{ICON_DOC}</span><span><b>Arrêt maladie ordinaire</b>'
             f'<small>AB-2026-007 · du 20/10/2026 au 21/10/2026 · certificat-medical.pdf</small></span><span class="mw-badge amber" data-film="abs-badge">Déclarée</span>{ICON_CHEV}</summary></details>'
             f'<details class="mw-request-detail" data-status="done"><summary><span class="mw-tile">{ICON_DOC}</span><span><b>Permission exceptionnelle - Déménagement</b>'
             f'<small>AB-2026-003 · le 02/09/2026</small></span><span class="mw-badge green">Traitée</span>{ICON_CHEV}</summary></details>')
    h = h.replace('<div class="mw-empty"><div class="mw-empty-illustration">', items + '<div class="mw-empty" data-film="abs-empty" hidden><div class="mw-empty-illustration">', 1)
    h = h.replace('<div class="mw-process">', '<div class="mw-process" data-film="abs-process">')
    h = h.replace('<span class="mw-upload">', '<span class="mw-upload" data-film="abs-upload">', 1)
    h = re.sub(r'<button class="mw-button">(<svg.*?</svg>)Envoyer la déclaration</button>', r'<button class="mw-button" data-film="abs-send">\1Envoyer la déclaration</button>', h, count=1, flags=re.S)
    ui["absences"] = h
    # --- Mes documents : documents du contrat, dont un qui vient d'arriver
    h = common(pages["documents"])
    row = re.search(r'<article class="mw-document-row selected".*?</article>', h, re.S).group(0)
    def doc_row(title, badge, date, film=None, selected=False):
        r = row.replace("Décompte de prestation — Septembre 2026", title).replace(">Décompte de prestation<", f">{badge}<").replace("Émis le 15/10/2026", f"Émis le {date}")
        if not selected:
            r = r.replace('class="mw-document-row selected"', 'class="mw-document-row"')
        return r.replace("<article ", f'<article data-film="{film}" ', 1) if film else r
    rows = (doc_row("Avenant au contrat de travail", "Contrat", "26/10/2026", "doc-new", True) + doc_row("Décompte de prestation — Septembre 2026", "Décompte de prestation", "15/10/2026", "doc-old")
            + doc_row("Attestation de travail", "Attestation", "02/10/2026") + doc_row("Contrat de travail — CDI", "Contrat", "05/01/2025"))
    h = h.replace(row, rows, 1)
    h = re.sub(r"<h3>Décompte de prestation — Septembre 2026</h3>(<p class=\"mw-muted\">.*?)Émis le 15/10/2026",
               lambda m: "<h3>Avenant au contrat de travail</h3>" + m.group(1) + "Émis le 26/10/2026", h, count=1, flags=re.S)
    h = re.sub(r'<b>DOCUMENT DE DÉMONSTRATION</b><hr>.*?</div>',
               '<b>AVENANT AU CONTRAT DE TRAVAIL</b><hr><p style="color:#5d7898">Webtel · Aïssatou Ndiaye</p>'
               + "".join(f'<i style="display:block;height:7px;margin:9px 0;border-radius:4px;background:#e3eaf3;width:{w}%"></i>' for w in (92, 84, 96, 70, 88, 64, 90, 76))
               + '</div>', h, count=1, flags=re.S)
    h = h.replace("<b>Aïssatou Ndiaye</b><time>15/10/2026 18:08</time><p>Votre document est disponible.</p>",
                  "<b>Service RH</b><time>26/10/2026 09:12</time><p>Votre avenant est disponible. Bonne lecture !</p>")
    h = h.replace('<article class="mw-comment"><span class="mw-avatar">C</span>', '<article class="mw-comment"><span class="mw-avatar">R</span>')
    h = h.replace('<div class="mw-tabs mw-document-categories">', '<div class="mw-tabs mw-document-categories" data-film="doc-tabs">')
    h = h.replace('<section class="mw-confidential">', '<section class="mw-confidential" data-film="doc-lock">')
    ui["documents"] = h
    # --- Mes demandes RH
    h = req_hooks(common(pages["requests"]))
    ui["requests"] = h
    # --- Contenu
    h = common(pages["content"])
    h = h.replace("<p>Aïssatou Ndiaye · 15/10/2026</p>", "<p>Direction générale · 15/10/2026</p>", 1).replace("<p>Aïssatou Ndiaye · 15/10/2026</p>", "<p>Équipe IT · 14/10/2026</p>", 1)
    h = h.replace("Par <b>Aïssatou Ndiaye</b>", "Par <b>la Direction générale</b>")
    h = re.sub(r'<div class="mw-note-body">.*?</div>', f'<div class="mw-note-body">{NOTE_BODY}</div>', h, count=1, flags=re.S)
    h = h.replace('<span class="mw-badge blue">● Non lu</span>', '<span class="mw-badge blue" data-film="note-read">● Non lu</span>', 1)
    h = h.replace('<label class="mw-check"><input type="checkbox" required>', '<label class="mw-check"><input type="checkbox" data-film="note-check" required>')
    h = re.sub(r'(<div class="mw-reading-confirm">)', r'<div class="mw-reading-confirm" data-film="note-confirm">', h, count=1)
    h = re.sub(r'<button class="mw-button">Confirmer ma lecture</button>', '<button class="mw-button" data-film="note-btn">Confirmer ma lecture</button>', h, count=1)
    h = h.replace('class="selected"><span>DIRECTION<small>● Non lu</small>', 'class="selected"><span>DIRECTION<small data-film="note-list-read">● Non lu</small>', 1)
    ui["content"] = h
    # --- Mail (écran composé avec les composants de la plateforme : liste et article de « Contenu », échanges de « Mes documents »)
    h = common(pages["content"], active="mail")
    h = set_title(h, "Mail", "Mail")
    convs = [("Moussa Diallo", "ÉQUIPE COMMERCIALE", "Réunion client de jeudi", "09:42", True), ("Service RH", "RH", "Votre attestation est prête", "Hier", False),
             ("Fatou Sarr", "SUPPORT", "Planning de la semaine", "Lundi", False)]
    lst = "".join(f'<a href="/mail" class="{"selected" if sel else ""}"><span>{tag}<small>{"● 1 nouveau" if sel else ""}</small></span><h3>{subj}</h3><p>{who} · {when}</p></a>'
                  for who, tag, subj, when, sel in convs)
    msgs = (f'<article class="mw-comment"><span class="mw-avatar">MD</span><div><b>Moussa Diallo</b><time>09:42</time><p>Bonjour Aïssatou, tu peux me confirmer l’heure de la réunion de jeudi ?</p></div></article>'
            f'<article class="mw-comment" data-film="mail-reply" style="flex-direction:row-reverse;text-align:right"><span class="mw-avatar">AN</span><div><b>Aïssatou Ndiaye</b><time>09:44</time><p data-film="mail-reply-text">C’est confirmé : jeudi à 10 h, en salle de réunion à Ouakam.</p></div></article>')
    mail_main = (f'<main id="mw-main" class="mw-canvas" tabindex="-1"><section class="mw-card mw-blog"><h1>Messagerie interne</h1><p class="mw-muted">Vos échanges avec les collègues de Webtel, au sein de MyWebtel.</p>'
                 f'<div class="mw-content-toolbar"><label class="mw-search"><svg class="mw-icon " viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg><input type="search" placeholder="Rechercher une conversation…"></label>'
                 f'<div class="mw-tabs"><button class="mw-tab selected">Toutes</button><button class="mw-tab">Non lues</button><button class="mw-tab">Équipes</button></div></div>'
                 f'<div class="mw-blog-layout"><nav class="mw-note-list" aria-label="Conversations">{lst}</nav>'
                 f'<article class="mw-note-article mw-comments" style="display:flex;flex-direction:column"><div class="mw-note-meta"><span class="mw-badge blue">DISCUSSION</span><span class="mw-badge green">● En ligne</span></div>'
                 f'<h2>Réunion client de jeudi</h2><p class="mw-note-byline">Avec <b>Moussa Diallo</b> · Équipe commerciale</p>'
                 f'<div class="mw-note-body" style="display:flex;flex-direction:column;gap:14px">{msgs}</div>'
                 f'<div class="mw-comment-compose" style="margin-top:auto"><textarea placeholder="Écrire un message…" aria-label="Message" data-film="mail-input"></textarea>'
                 f'<button class="mw-button" aria-label="Envoyer" data-film="mail-send">{ICON_SEND}</button></div></article></div></section></main>')
    ui["mail"] = set_main(h, mail_main)
    # --- Support IT (écran composé sur le modèle de « Mes demandes RH »)
    h = req_hooks(common(pages["requests"], active="support"))
    h = set_title(h, "Support IT", "Support IT")
    a, b = main_of(h)
    m = h[a:b]
    m = m.replace("<h2>Vos démarches RH</h2><p>Adressez une demande et suivez son traitement depuis votre espace.</p>",
                  "<h2>Support informatique</h2><p>Signalez un problème technique et suivez la prise en charge de votre ticket.</p>")
    m = m.replace("<h2>Nouvelle demande</h2>", "<h2>Nouveau ticket</h2>").replace("<h2>Mes demandes</h2>", "<h2>Mes tickets</h2>")
    for old, new in (("Attestation</button>", "Messagerie</button>"), ("Question RH</button>", "Matériel</button>"), ("Modification du dossier</button>", "Accès et mot de passe</button>"), ("Autre demande</button>", "Autre</button>")):
        m = m.replace(old, new, 1)
    m = re.sub(r"<select name=\"category\" data-request-select>.*?</select>", '<select name="category"><option>Messagerie</option><option>Matériel</option><option>Accès et mot de passe</option><option>Autre</option></select>', m, flags=re.S)
    m = m.replace("Ex. : Demande d’attestation de travail", "Ex. : Imprimante hors service").replace("Précisez votre demande, les informations nécessaires, la période concernée…", "Décrivez le problème : ce qui se passe, depuis quand, sur quel poste…")
    m = m.replace("Envoyer la demande</button>", "Envoyer le ticket</button>").replace("Cette demande sera transmise au service RH.", "Ce ticket sera transmis à l’équipe informatique.")
    m = m.replace('data-filter="done" aria-pressed="false">Traitées', 'data-filter="done" aria-pressed="false">Résolus').replace(">Toutes<", ">Tous<", 1)
    m = re.sub(r'<details class="mw-request-detail" data-status="pending" data-film="req-new">.*?</details>',
               f'<details class="mw-request-detail" data-status="pending" data-film="tick-new"><summary><span class="mw-tile">{ICON_SUPPORT}</span><span><b>Messagerie inaccessible</b>'
               f'<small>IT-2026-031 · 26/10/2026</small></span><span class="mw-badge amber" data-film="tick-badge">Envoyé</span>{ICON_CHEV}</summary></details>', m, count=1, flags=re.S)
    m = re.sub(r'<details class="mw-request-detail" data-status="pending"><summary>.*?</details>',
               f'<details class="mw-request-detail" data-status="done"><summary><span class="mw-tile">{ICON_SUPPORT}</span><span><b>Écran du poste 12</b>'
               f'<small>IT-2026-024 · 08/10/2026</small></span><span class="mw-badge green">Résolu</span>{ICON_CHEV}</summary></details>', m, count=1, flags=re.S)
    m = m.replace('data-film="req-subject"', 'data-film="tick-subject"').replace('data-film="req-desc"', 'data-film="tick-desc"').replace('data-film="req-send"', 'data-film="tick-send"').replace('data-film="req-cats"', 'data-film="tick-cats"')
    m = m.replace("Attestation demandée pour un dossier bancaire.", "Écran remplacé le 9 octobre.")
    ui["support"] = h[:a] + m + h[b:]
    return ui


def main():
    ui = build(load_pages(sys.argv[1]))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "ui.json"), "w", encoding="utf-8") as f:
        json.dump(ui, f, ensure_ascii=False)
    os.makedirs(os.path.join(OUT, "ui"), exist_ok=True)
    for k, v in ui.items():                          # copies lisibles, pour contrôle
        open(os.path.join(OUT, "ui", k + ".html"), "w", encoding="utf-8").write(v)
    print("-> build/mywebtel/ui.json :", ", ".join(ui))


if __name__ == "__main__":
    main()
