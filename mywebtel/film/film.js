/* MyWebtel — film de présentation V2 (1920×1080, 30 i/s).
 * Toute l'image est une fonction du temps : renderAt(t) pose chaque élément. Aucune animation CSS automatique,
 * donc le rendu image par image (render.js) est exact et reproductible.
 * Les instants viennent de window.TL (build/mywebtel/timeline.json, produit par vo.py) : chaque geste tombe sur le mot
 * prononcé (mots datés par alignement).
 *
 * Mise en scène : une seule fenêtre de l'application, suivie par une caméra 3D d'un bout à l'autre (pas de coupe).
 * Les écrans reprennent le code réel (webtel-intra-clean : globals.css, login, tableau de bord, AttendanceCard) et
 * ses libellés ; les modules ajoutés (pause, justification, absences, tickets, documents) suivent la même charte.
 */
(function () {
  "use strict";
  const TL = window.TL;
  const stage = document.getElementById("stage");

  // ------------------------------------------------------------------ outils
  const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
  const seg = (t, a, b) => clamp((t - a) / (b - a));
  const lerp = (a, b, x) => a + (b - a) * x;
  const E = {
    outCubic: x => 1 - Math.pow(1 - x, 3), inCubic: x => x * x * x,
    inOutCubic: x => x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2,
    inOutQuint: x => x < 0.5 ? 16 * x ** 5 : 1 - Math.pow(-2 * x + 2, 5) / 2,
    outExpo: x => x >= 1 ? 1 : 1 - Math.pow(2, -10 * x), inOutSine: x => -(Math.cos(Math.PI * x) - 1) / 2,
    outQuart: x => 1 - Math.pow(1 - x, 4),
  };
  function spring(t, z = 0.72, f = 2.6) {            // ressort ferme (dépassement ≈ 4 %), t en secondes
    if (t <= 0) return 0;
    const w = 2 * Math.PI * f;
    if (z < 1) { const wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + z * w / wd * Math.sin(wd * t)); }
    return 1 - Math.exp(-w * t) * (1 + w * t);
  }
  const SC = {}; TL.scenes.forEach(s => { SC[s.id] = s; });
  const S0 = id => SC[id].start, S1 = id => SC[id].end;
  const segT = (id, i) => SC[id].segs[i].start;
  const segE = (id, i) => SC[id].segs[i].end;
  // instant où un mot est prononcé (alignement de vo.py) ; n = occurrence
  function W(id, i, word, n = 0) {
    const ws = SC[id].segs[i].words, k = ws.filter(w => w[0].toLowerCase() === word.toLowerCase());
    if (!k[n]) throw new Error("mot absent : " + id + "/" + i + "/" + word);
    return k[n][1];
  }
  const typed = (txt, t, t0, t1) => txt.slice(0, Math.round(txt.length * seg(t, t0, t1)));

  const ICON = {
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    lock: '<rect x="5" y="11" width="14" height="10" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>',
    download: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    coffee: '<path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M16 10h2a2.5 2.5 0 0 1 0 5h-2M8 3v3M12 3v3"/>',
    pen: '<path d="M4 20l4-1 11-11-3-3L5 16z"/>',
    ticket: '<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z"/><path d="M14 6v12" stroke-dasharray="2 2.5"/>',
    folder: '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    paperclip: '<path d="M20 11.5l-8.2 8.2a5 5 0 0 1-7.1-7.1l8.5-8.5a3.5 3.5 0 0 1 5 5L9.7 17.6a2 2 0 0 1-2.8-2.8L14.5 7"/>',
    chevron: '<path d="M9 6l6 6-6 6"/>', down: '<path d="M6 9l6 6 6-6"/>', left: '<path d="M15 6l-6 6 6 6"/>',
    wifi: '<path d="M2 9a15 15 0 0 1 20 0M5.5 12.5a10 10 0 0 1 13 0M9 16a5 5 0 0 1 6 0"/><circle cx="12" cy="19.5" r="1" fill="currentColor"/>',
    shield: '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>',
  };
  const ic = n => `<svg class="i" viewBox="0 0 24 24">${ICON[n]}</svg>`;
  function h(html) { const d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstElementChild; }
  function add(parent, html) { const e = h(html); parent.appendChild(e); return e; }
  const q = (root, sel) => root.querySelector(sel);
  const qa = (root, sel) => Array.from(root.querySelectorAll(sel));
  // pose d'un élément : o opacité, x/y translation, s échelle, r rotation, rx/ry rotation 3D, blur
  function st(el, o) {
    const tr = [];
    if (o.c) tr.push("translate(-50%,-50%)");
    if (o.x || o.y) tr.push(`translate3d(${(o.x || 0).toFixed(2)}px,${(o.y || 0).toFixed(2)}px,0)`);
    if (o.rx) tr.push(`rotateX(${o.rx.toFixed(3)}deg)`);
    if (o.ry) tr.push(`rotateY(${o.ry.toFixed(3)}deg)`);
    if (o.r) tr.push(`rotate(${o.r.toFixed(3)}deg)`);
    if (o.s !== undefined && o.s !== 1) tr.push(`scale(${o.s.toFixed(4)})`);
    el.style.transform = tr.join(" ");
    if (o.o !== undefined) { const v = clamp(o.o); el.style.opacity = v.toFixed(4); el.style.display = v <= 0.002 ? "none" : ""; }
    if (o.blur !== undefined) el.style.filter = o.blur > 0.05 ? `blur(${o.blur.toFixed(2)}px)` : "none";
  }
  function enter(t, t0, dur = 0.7, dy = 26) { const p = E.outExpo(seg(t, t0, t0 + dur)); return { o: clamp(p * 1.4), y: (1 - p) * dy, p }; }
  const setText = (el, s) => { if (el.textContent !== s) el.textContent = s; };
  const setHTML = (el, s) => { if (el.__h !== s) { el.innerHTML = s; el.__h = s; } };
  const cls = (el, c, on) => el.classList.toggle(c, !!on);

  // ------------------------------------------------------------------ décor
  const bg = add(stage, `<div id="bg"></div>`);
  const glowA = add(bg, `<div class="glow" style="width:1100px;height:800px;left:-200px;top:-260px;background:rgba(26,146,248,.16)"></div>`);
  const glowB = add(bg, `<div class="glow" style="width:1000px;height:760px;right:-220px;bottom:-300px;background:rgba(17,45,80,.10)"></div>`);
  const bgNight = add(stage, `<div id="bgNight"></div>`);
  const view = add(stage, `<div id="view"></div>`);
  const world = add(view, `<div id="world"></div>`);
  const fx = add(stage, `<div class="layer" id="fx"></div>`);         // calques de film, au-dessus de la caméra

  // ------------------------------------------------------------------ fenêtre et pages de l'application
  const LOGO = "brand/webtel-logo.svg";
  const WX = 240, WY = 150, WH = 780;                                  // fenêtre 1440×780, centrée
  const win = add(world, `<div class="win" style="top:${WY}px;height:${WH}px"><div class="chrome"><i class="d"></i><i class="d"></i><i class="d"></i>
    <div class="url">${ic("lock")}<span class="u">mywebtel.com/login</span></div></div><div class="page"></div></div>`);
  const page = q(win, ".page"), urlEl = q(win, ".u");
  const TOP = `<div class="topbar"><div class="brand"><img src="${LOGO}" alt="Webtel"><span class="sep"></span><div><strong>MyWebtel</strong><div class="muted" style="font-size:14px">WTL-00001</div></div></div>
    <div class="topactions"><span>Aïssatou Ndiaye</span><span class="logout">Déconnexion</span></div></div>`;
  const P = {};
  // connexion (app/login/page.tsx), avec le logo et la mention de l'espace collaborateur
  P.login = add(page, `<div class="app"><div style="position:absolute;inset:0;display:grid;place-items:center"><section class="cardL">
      <img class="llogo" src="${LOGO}" style="width:236px;display:block;margin:0 auto 10px">
      <div class="eyebrow" style="text-align:center;margin-bottom:26px;color:var(--slate)">MYWEBTEL · ESPACE COLLABORATEUR</div>
      <p class="lead">Connectez-vous avec votre matricule ou votre adresse e-mail professionnelle.</p>
      <label class="label lid">Matricule ou adresse e-mail</label><div class="input fid"><span class="v"></span></div>
      <label class="label">Mot de passe</label><div class="input fpw"><span class="v"></span></div>
      <div class="btn bsub">Se connecter</div>
      <p class="small">La connexion à MyWebtel ne démarre pas automatiquement votre session de travail.</p></section></div></div>`);
  // tableau de bord (app/dashboard/page.tsx + components/AttendanceCard.tsx)
  P.dash = add(page, `<div class="app"><main class="shell">${TOP}<div class="grid">
      <section class="panel day"><h2>Ma journée</h2>
        <div class="notice danger anom" style="display:flex;align-items:center;gap:12px"><span style="flex:1"><b>Pointage incomplet</b> · mardi 20 octobre : départ non pointé.</span><span class="logout bjus" style="font-weight:700;color:var(--navy)">Justifier</span></div>
        <div class="status"><span class="dot"></span><span class="stx">Session de travail inactive</span></div>
        <div class="times">${["Arrivée", "Pause", "Retour", "Départ"].map(l => `<div class="metric"><span class="muted">${l}</span><b>—</b></div>`).join("")}</div>
        <div class="notice success msg">Pointage enregistré.</div>
        <div class="btnrow"><div class="btn ghost bpause">Commencer ma pause</div><div class="btn bmain">Activer ma session</div></div>
        <p class="small">La déconnexion de MyWebtel ne termine jamais automatiquement votre session de travail.</p></section>
      <section class="panel"><h2>Mon espace</h2><p class="muted" style="margin-bottom:16px">Vos démarches au quotidien.</p><div class="secondaryGrid">
        ${[["calendar", "Congés et absences", "Demandes et suivi"], ["pen", "Justifications", "Oublis et retards de pointage"], ["ticket", "Tickets", "Une demande d'assistance"],
           ["lock", "Documents RH", "Fiches de paie, attestations"], ["folder", "Documents", "Documents de l'entreprise"]].map(([i, a, b]) =>
           `<div class="secondary"><span class="ico">${ic(i)}</span><div><strong>${a}</strong><span class="muted" style="font-size:14px">${b}</span></div><span class="chev">${ic("chevron")}</span></div>`).join("")}
      </div></section></div></main>
      <div class="modalBack"></div>
      <div class="modal"><h2 style="font-size:24px;margin-bottom:6px">Justifier un pointage</h2><p class="muted" style="margin-bottom:22px">Mardi 20 octobre · départ non pointé</p>
        <label class="label">Motif</label><div class="input select fmot"><span class="v" style="color:var(--muted)">Choisir un motif</span>${ic("down")}</div>
        <label class="label">Commentaire</label><div class="input fcom" style="min-height:84px;white-space:normal"><span class="v"></span></div>
        <label class="label">Pièce jointe <span class="muted" style="font-weight:400">(facultatif)</span></label>
        <div style="margin-bottom:22px"><span class="chip fpj">${ic("paperclip")} Ajouter un fichier</span></div>
        <div class="btn bsend">Envoyer la justification</div></div></div>`);
  // congés et absences
  const NOV = (() => { let s = ["L", "M", "M", "J", "V", "S", "D"].map(d => `<span class="wd">${d}</span>`).join(""); for (let i = 0; i < 6; i++) s += "<span></span>"; for (let d = 1; d <= 30; d++) s += `<span data-d="${d}">${d}</span>`; return s; })();
  const PAGE = (title, body) => `<div class="app"><main class="shell">${TOP}<div class="back">${ic("left")} Mon espace</div><div class="h1">${title}</div>${body}</main></div>`;
  P.abs = add(page, PAGE("Congés et absences", `<div class="grid">
      <section class="panel"><h2 style="margin-bottom:16px">Nouvelle demande</h2>
        <div class="seg2"><div class="sc">Congé</div><div class="sa">Absence</div></div>
        <label class="label">Dates</label><div class="cal"><div class="hd"><span>Novembre 2026</span><span class="muted ctx" style="font-weight:400"></span></div><div class="days">${NOV}</div></div>
        <label class="label">Justificatif</label><div style="margin-bottom:22px"><span class="chip ajus">${ic("paperclip")} Ajouter un justificatif</span></div>
        <div class="btn bdem">Envoyer la demande</div></section>
      <section class="panel"><h2 style="margin-bottom:6px">Mes demandes</h2><div class="list">
        <div class="item nreq" style="flex-wrap:wrap"><span class="ico" style="width:40px;height:40px;border-radius:12px;background:#eef4fb;display:grid;place-items:center;color:var(--navy);font-size:20px">${ic("calendar")}</span>
          <div style="flex:1"><strong>Absence</strong><div class="muted" style="font-size:14px">Du 3 au 5 novembre · 3 jours</div></div><span class="pill amber rst"><span class="dot" style="background:#d08a12"></span>En attente</span>
          <div class="track" style="width:100%"><i class="ok">${ic("check")}</i>Envoyée<b></b><i class="now"></i>En cours de validation<b></b><i></i>Réponse</div></div>
        <div class="item"><span class="ico" style="width:40px;height:40px;border-radius:12px;background:#eef4fb;display:grid;place-items:center;color:var(--navy);font-size:20px">${ic("calendar")}</span>
          <div style="flex:1"><strong>Congé</strong><div class="muted" style="font-size:14px">Du 10 au 14 août · 5 jours</div></div><span class="pill green">${ic("check")} Validée</span></div>
      </div></section></div>`));
  // tickets
  P.tick = add(page, PAGE("Tickets", `<div class="grid">
      <section class="panel"><h2 style="margin-bottom:16px">Nouveau ticket</h2>
        <label class="label">Objet</label><div class="input fobj"><span class="v"></span></div>
        <label class="label">Description</label><div class="input fdes" style="min-height:120px;white-space:normal"><span class="v"></span></div>
        <div class="btn btik">Créer le ticket</div></section>
      <section class="panel"><h2 style="margin-bottom:6px">Mes tickets</h2><div class="list">
        <div class="item ntik"><span class="ico" style="width:40px;height:40px;border-radius:12px;background:#eef4fb;display:grid;place-items:center;color:var(--navy);font-size:20px">${ic("ticket")}</span>
          <div style="flex:1"><strong>Pas d'accès à la messagerie</strong><div class="muted tby" style="font-size:14px">Ticket n° 142 · à l'instant</div></div><span class="pill grey tst">Ouvert</span></div>
        <div class="item"><span class="ico" style="width:40px;height:40px;border-radius:12px;background:#eef4fb;display:grid;place-items:center;color:var(--navy);font-size:20px">${ic("ticket")}</span>
          <div style="flex:1"><strong>Écran du poste 12</strong><div class="muted" style="font-size:14px">Ticket n° 131 · 8 octobre</div></div><span class="pill green">${ic("check")} Résolu</span></div>
      </div></section></div>`));
  // documents RH
  const RHROWS = [["Fiche de paie", "Octobre 2026"], ["Fiche de paie", "Septembre 2026"], ["Fiche de paie", "Août 2026"], ["Attestation de travail", "Juin 2026"], ["Contrat de travail", "Janvier 2024"]];
  P.rh = add(page, PAGE(`Documents RH <span class="pill green rhlock" style="font-size:15px;vertical-align:middle;margin-left:12px">${ic("lock")} Visible uniquement par vous</span>`,
    `<div class="grid"><section class="panel"><div class="list">${RHROWS.map(([a, b], k) => `<div class="item rhrow" style="border-radius:12px;padding:14px 12px"><span class="chip file" style="padding:0;border:0;background:none"><span class="pdf">PDF</span></span>
        <div style="flex:1"><strong>${a}</strong><div class="muted" style="font-size:14px">${b}</div></div><span class="logout" style="display:inline-flex;gap:8px;align-items:center">${ic("download")} <span class="dl">Télécharger</span></span></div>`).join("")}</div></section>
      <section class="panel prev" style="padding:20px"><div class="muted" style="font-size:14px;margin-bottom:12px">Aperçu</div>
        <div style="border:1px solid var(--line);border-radius:12px;padding:22px;height:470px;display:flex;flex-direction:column;gap:12px;position:relative">
          <div style="display:flex;justify-content:space-between;align-items:center"><img src="${LOGO}" style="height:30px"><span class="muted" style="font-size:13px">Octobre 2026</span></div>
          <div style="font-weight:800;font-size:18px;margin:8px 0">Bulletin de paie</div>
          ${[92, 70, 84, 60, 76, 66, 88, 54, 72].map((w, k) => `<div style="display:flex;justify-content:space-between"><i style="display:block;height:10px;width:${w * 2.2}px;border-radius:5px;background:#e6ecf3"></i><i style="display:block;height:10px;width:${50 + (k * 17) % 40}px;border-radius:5px;background:#dbe3ed"></i></div>`).join("")}
          <div style="margin-top:auto;border-top:2px solid var(--line);padding-top:14px;display:flex;justify-content:space-between;align-items:center"><b>Net à payer</b><i style="display:block;height:14px;width:120px;border-radius:7px;background:var(--navy);opacity:.85"></i></div>
          <div class="dlbar" style="position:absolute;left:22px;right:22px;bottom:-12px;height:6px;border-radius:3px;background:#e9eef5;overflow:hidden"><i style="display:block;height:100%;width:0;background:var(--green)"></i></div>
        </div></section></div>`));
  // documents de l'entreprise
  const DOCS = [["Règlement intérieur", "PDF", "Mis à jour le 2 octobre"], ["Charte informatique", "PDF", "Mis à jour le 14 octobre"], ["Livret d'accueil", "PDF", "Mis à jour le 6 octobre"],
                ["Procédure de pointage", "PDF", "Mis à jour le 20 octobre"], ["Note de service : horaires de fin d'année", "PDF", "Mis à jour le 22 octobre"], ["Organigramme", "PDF", "Mis à jour le 1er octobre"]];
  P.docs = add(page, PAGE("Documents", `<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:18px">${DOCS.map(([a, f, d]) => `<div class="doc">
      <div style="display:flex;justify-content:space-between;align-items:flex-start"><span class="ft" style="background:#e8f2fe;color:#0f5fae">${f}</span><span class="pill green upd" style="font-size:12px">${ic("check")} À jour</span></div>
      <strong style="font-size:17px;line-height:1.3;min-height:44px">${a}</strong><span class="muted" style="font-size:14px">${d}</span></div>`).join("")}</div>`));
  const ORDER = ["login", "dash", "abs", "tick", "rh", "docs"];

  // téléphone : la même page « Ma journée », hors du réseau Webtel (message réel d'AttendanceCard)
  const phone = add(world, `<div class="phone" style="left:1700px;top:120px"><div class="scr"><div class="app" style="padding:56px 18px 18px;font-size:15px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:22px"><img src="${LOGO}" style="height:30px"></div>
      <section class="panel" style="padding:20px"><h2>Ma journée</h2><div class="status" style="margin:10px 0 16px"><span class="dot"></span>Session de travail inactive</div>
        <div class="times" style="grid-template-columns:1fr 1fr;margin:12px 0"><div class="metric"><span class="muted">Arrivée</span><b>—</b></div><div class="metric"><span class="muted">Départ</span><b>—</b></div></div>
        <div class="notice">Pointage indisponible : vous devez être connecté au réseau Webtel.</div>
        <div class="btn busy">Activer ma session</div></section></div></div></div>`);

  // ------------------------------------------------------------------ calques de film
  const CURSOR = `<svg class="cursor" viewBox="0 0 34 44"><path d="M3 2l26 24H16l7 14-5 2-7-14-8 8z" fill="#fff" stroke="#061427" stroke-width="2.4" stroke-linejoin="round"/></svg>`;
  const cur = add(fx, CURSOR), rip = add(fx, `<div class="ripple"></div>`);
  const clock = add(fx, `<div class="note clock" style="left:70px;top:46px;font-size:26px;gap:14px">${ic("clock")}<span class="cd" style="font-weight:500;color:var(--muted)"></span><b class="ct" style="font-variant-numeric:tabular-nums;font-size:30px"></b></div>`);
  const noteOffice = add(fx, `<div class="note" style="left:0;top:0">${ic("wifi")}<span>Au bureau, sur le réseau Webtel</span><span style="color:var(--green)">${ic("check")}</span></div>`);
  const notePhone = add(fx, `<div class="note" style="left:0;top:0">${ic("wifi")}<span>Hors du réseau</span><span style="color:var(--red)">${ic("x")}</span></div>`);
  // ouverture : les démarches du quotidien
  const TASKS = [["clock", "Pointer", "Arrivée · 08:02", "Pointer", -560, -250], ["coffee", "Faire sa pause", "12:31 – 13:29", "pause", 470, -300],
                 ["pen", "Justifier un retard", "Mardi 20 octobre", "justifier", -480, 210], ["file", "Fiche de paie", "Octobre 2026 · PDF", "fiche", 520, 230]];
  const tasks = TASKS.map(([i, a, b]) => add(fx, `<div class="task"><span class="ti">${ic(i)}</span><div>${a}<small>${b}</small></div></div>`));
  const ring = add(fx, `<svg class="abs" style="left:810px;top:390px;width:300px;height:300px" viewBox="0 0 300 300">
      <circle cx="150" cy="150" r="130" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="3"/>
      <circle class="arc" cx="150" cy="150" r="130" fill="none" stroke="#1a92f8" stroke-width="3" stroke-linecap="round" stroke-dasharray="817" stroke-dashoffset="817" transform="rotate(-90 150 150)"/>
      <line class="hand" x1="150" y1="150" x2="150" y2="48" stroke="#eef3fa" stroke-width="5" stroke-linecap="round"/>
      <line class="hand2" x1="150" y1="150" x2="150" y2="84" stroke="#eef3fa" stroke-width="7" stroke-linecap="round"/><circle cx="150" cy="150" r="8" fill="#eef3fa"/></svg>`);
  const spark = add(fx, `<div class="abs" style="left:960px;top:540px;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;background:#fff;box-shadow:0 0 40px 18px rgba(120,190,255,.8)"></div>`);
  // logo animé : la marque (cercle et combiné) et le mot, découpés dans le même SVG
  const LW = 960, LH = Math.round(LW * 1224 / 3520);
  const logo = add(fx, `<div class="abs" style="left:${960 - LW / 2}px;top:${470 - LH / 2}px;width:${LW}px;height:${LH}px">
      <img class="lm" src="${LOGO}" style="position:absolute;inset:0;width:100%;clip-path:inset(0 76% 0 0)">
      <img class="lt" src="${LOGO}" style="position:absolute;inset:0;width:100%;clip-path:inset(0 0 0 24%)"></div>`);
  const lm = q(logo, ".lm"), lt = q(logo, ".lt");
  const tag = add(fx, `<div class="center tagline" style="top:${470 + LH / 2 + 56}px">MYWEBTEL · ESPACE COLLABORATEUR</div>`);
  const flash = add(fx, `<div class="layer" style="background:#fff"></div>`);

  // éléments de l'application utilisés par l'animation
  const D = {
    fid: q(P.login, ".fid"), fpw: q(P.login, ".fpw"), bsub: q(P.login, ".bsub"), lid: q(P.login, ".lid"), llogo: q(P.login, ".llogo"),
    day: q(P.dash, ".day"), anom: q(P.dash, ".anom"), bjus: q(P.dash, ".bjus"), status: q(P.dash, ".status"), stx: q(P.dash, ".stx"),
    metrics: qa(P.dash, ".times .metric"), msg: q(P.dash, ".msg"), bpause: q(P.dash, ".bpause"), bmain: q(P.dash, ".bmain"), brow: q(P.dash, ".btnrow"),
    tiles: qa(P.dash, ".secondary"), mback: q(P.dash, ".modalBack"), modal: q(P.dash, ".modal"), fmot: q(P.dash, ".fmot"), fcom: q(P.dash, ".fcom"),
    fpj: q(P.dash, ".fpj"), bsend: q(P.dash, ".bsend"),
    sc: q(P.abs, ".sc"), sa: q(P.abs, ".sa"), days: qa(P.abs, ".days [data-d]"), ctx: q(P.abs, ".ctx"), ajus: q(P.abs, ".ajus"), bdem: q(P.abs, ".bdem"),
    nreq: q(P.abs, ".nreq"), rst: q(P.abs, ".rst"), absPanel: qa(P.abs, ".panel"),
    fobj: q(P.tick, ".fobj"), fdes: q(P.tick, ".fdes"), btik: q(P.tick, ".btik"), ntik: q(P.tick, ".ntik"), tst: q(P.tick, ".tst"), tby: q(P.tick, ".tby"), tickPanel: qa(P.tick, ".panel"),
    rhrows: qa(P.rh, ".rhrow"), prev: q(P.rh, ".prev"), rhlock: q(P.rh, ".rhlock"), dl: q(P.rh, ".dl"), dlbar: q(P.rh, ".dlbar i"),
    docs: qa(P.docs, ".doc"), upd: qa(P.docs, ".upd"),
  };
  // position d'un élément dans le repère de la fenêtre (mise en page, sans les transformations de caméra)
  // (un élément masqué garde sa dernière position connue : la caméra et le curseur ne sautent pas)
  function posIn(el) {
    if (!el.offsetParent) return el.__pos || [720, WH / 2];
    let x = 0, y = 0, e = el;
    while (e && e !== win) { x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; }
    return (el.__pos = [x + el.offsetWidth / 2, y + el.offsetHeight / 2]);
  }
  const centerOf = el => {
    const r = el.getBoundingClientRect();
    if (!r.width) return el.__ctr || [960, 540];
    return (el.__ctr = [r.left + r.width / 2, r.top + r.height / 2]);
  };

  // ------------------------------------------------------------------ chronologie (tout dérive des mots de la voix)
  const T = {};
  const BAR = TL.beat * 4, onBar = x => Math.round(x / BAR) * BAR;   // les deux logos tombent sur un premier temps
  T.logo = onBar(W("reveal", 0, "MyWebtel") - 0.4);
  T.tag = W("reveal", 0, "espace");
  T.same = W("reveal", 1, "même");
  T.winIn = T.same - 0.55;
  T.typeId = W("login", 0, "matricule") - 0.15;
  T.mail = W("login", 0, "e-mail");
  T.login = segE("login", 0) - 0.15;
  T.dash = T.login + 0.55;
  T.act = W("clockin", 0, "Activer") + 0.3;
  T.arr = W("clockin", 1, "arrivée");
  T.minute = W("clockin", 1, "minute");
  T.net = segT("clockin", 2) - 0.1;
  T.netEnd = S1("clockin") - 0.35;
  T.noon = S0("pause") - 0.1;
  T.pause = W("pause", 0, "lancez") + 0.15;
  T.ret = W("pause", 1, "retour") - 0.05;
  T.resume = W("pause", 1, "clic") + 0.2;
  T.eve = S0("clockout") - 0.1;
  T.end = W("clockout", 0, "Terminer") + 0.45;
  T.closed = W("clockout", 1, "bouclée");
  T.anom = S0("justif") - 0.1;
  T.jus = W("justif", 1, "justifiez") + 0.15;
  T.motif = W("justif", 1, "motif");
  T.pj = W("justif", 1, "pièce");
  T.jsend = segE("justif", 1) + 0.25;
  T.absTile = S0("absences") - 0.2;
  T.abs = T.absTile + 0.35;
  T.absType = W("absences", 0, "absence") + 0.05;
  T.dates = W("absences", 0, "dates") - 0.15;
  T.ajus = W("absences", 0, "justificatif");
  T.dem = segE("absences", 0) + 0.05;
  T.statut = W("absences", 1, "statut");
  T.tick = S0("ticket") - 0.05;
  T.tobj = segT("ticket", 0) + 0.1;
  T.tcreate = W("ticket", 1, "ticket") + 0.1;
  T.tcharge = W("ticket", 1, "prise");
  T.rh = S0("docsrh") - 0.05;
  T.payslip = W("docsrh", 0, "fiches");
  T.dlT = W("docsrh", 0, "disponibles");
  T.seul = W("docsrh", 1, "seul");
  T.docs = S0("docs") - 0.05;
  T.ajour = W("docs", 0, "toujours");
  T.main = W("docs", 0, "portée");
  T.out = S0("signature") - 0.2;
  T.logo2 = W("signature", 0, "MyWebtel");
  T.tag2 = W("signature", 1, "espace");
  T.final = onBar(T.logo2 - 0.5) + 0.08;   // la marque se pose sur le premier temps, le mot se dévoile sur la voix
  // navigation de la fenêtre : [instant, page, adresse]
  const NAV = [[0, "login", "mywebtel.com/login"], [T.dash, "dash", "mywebtel.com/tableau-de-bord"], [T.abs, "abs", "mywebtel.com/conges-absences"],
               [T.tick, "tick", "mywebtel.com/tickets"], [T.rh, "rh", "mywebtel.com/documents-rh"], [T.docs, "docs", "mywebtel.com/documents"]];

  // ------------------------------------------------------------------ caméra
  // état : cx, cy = point de la fenêtre au centre de l'écran, s = échelle, rx/ry = rotation 3D, y = décalage vertical (px écran)
  const WIDE = { cx: 720, cy: WH / 2, s: 0.98, rx: 0, ry: 0, y: 0 };
  // gros plan : si la fenêtre peut couvrir l'écran à cette échelle, on ne montre pas ses bords
  function frame(o) {
    if (o.s * 1440 >= 1940) o.cx = clamp(o.cx, 960 / o.s + 8, 1440 - 960 / o.s - 8);
    if (o.s * WH >= 1100) o.cy = clamp(o.cy, 540 / o.s - 52 + 8, WH - 540 / o.s - 8);
    return o;
  }
  const on = (el, s, extra = {}) => () => { const [x, y] = posIn(el); return frame(Object.assign({ cx: x, cy: y, s, rx: 0, ry: 0, y: 0 }, extra)); };
  const fixed = o => () => Object.assign({}, WIDE, o);
  // [début, fin, cible] : chaque mouvement part de l'état atteint au mouvement précédent
  const MOVES = [
    [T.winIn - 0.1, T.winIn + 1.5, () => { const [x, y] = posIn(D.llogo); return { cx: 720, cy: y + 150, s: 1.3, rx: 0, ry: 0, y: 0 }; }],
    [T.typeId - 0.6, T.typeId + 0.4, on(D.fid, 1.42, { cy: posIn(D.fid)[1] + 60 })],
    [T.login + 0.2, T.dash + 0.7, fixed({ rx: 4, ry: -7, s: 0.94 })],
    [T.act - 1.6, T.act - 0.6, on(D.day, 1.32, { rx: 1, ry: -3 })],
    [T.minute - 0.3, T.minute + 0.6, on(D.metrics[0], 1.75, { cx: posIn(D.metrics[0])[0] + 120 })],
    [T.net - 0.15, T.net + 0.9, fixed({ cx: 980, s: 0.8, ry: 9, rx: 3 })],
    [T.netEnd, T.netEnd + 0.8, on(D.day, 1.32, { rx: 1, ry: -3 })],
    [T.pause - 1.0, T.pause - 0.3, on(D.brow, 1.6, { cy: posIn(D.brow)[1] - 90 })],
    [T.closed - 0.1, T.closed + 1.0, fixed({ rx: 3, ry: 6, s: 0.96 })],
    [T.anom + 0.1, T.anom + 0.9, on(D.anom, 1.55)],
    [T.jus + 0.15, T.jus + 0.9, () => { const [x, y] = posIn(D.modal); return { cx: x, cy: y + 30, s: 1.22, rx: 0, ry: 0, y: 0 }; }],
    [T.jsend + 0.5, T.abs + 0.5, fixed({ s: 0.95, ry: -5, rx: 2 })],
    [T.absType - 0.5, T.absType + 0.2, on(D.absPanel[0], 1.18, { cy: posIn(D.absPanel[0])[1] + 20 })],
    [T.statut - 0.7, T.statut + 0.1, on(D.absPanel[1], 1.5)],
    [T.tick + 0.3, T.tick + 1.1, on(D.tickPanel[0], 1.25)],
    [T.tcreate + 0.1, T.tcreate + 0.8, on(D.tickPanel[1], 1.5)],
    [T.rh + 0.1, T.rh + 0.9, fixed({ s: 1.02, ry: -4, rx: 2 })],
    [T.seul - 0.35, T.seul + 0.35, on(D.rhlock, 1.9)],
    [T.docs - 0.25, T.docs + 0.75, fixed({ s: 1.05, rx: 2, ry: 4, cy: WH / 2 + 20 })],
    [T.main - 0.1, T.out + 0.4, fixed({ s: 0.84, rx: 8, ry: -10 })],
    [T.out + 0.2, T.out + 1.6, fixed({ s: 0.6, rx: 22, ry: -16, y: 260 })],
  ];
  function cameraAt(t) {
    let c = Object.assign({}, WIDE);
    for (const [a, b, tgt] of MOVES) {
      if (t <= a) break;
      const g = tgt(), p = E.inOutQuint(seg(t, a, b));
      for (const k of Object.keys(c)) c[k] = lerp(c[k], g[k] !== undefined ? g[k] : c[k], p);
    }
    // entrée de la fenêtre (révélation) : elle monte du bas, inclinée
    const inn = E.outQuart(seg(t, T.winIn, T.winIn + 1.6));
    c.y += (1 - inn) * 1000; c.rx += (1 - inn) * 28;
    // respiration de caméra, très légère
    c.ry += 0.6 * Math.sin(t * 0.45); c.rx += 0.4 * Math.sin(t * 0.33 + 1);
    return c;
  }
  function applyCamera(c) {
    world.style.transform = `translate3d(960px,${(540 + c.y).toFixed(2)}px,0) rotateX(${c.rx.toFixed(3)}deg) rotateY(${c.ry.toFixed(3)}deg) scale(${c.s.toFixed(4)}) translate3d(${(-WX - c.cx).toFixed(2)}px,${(-WY - c.cy).toFixed(2)}px,0)`;
  }

  // ------------------------------------------------------------------ curseur
  // clics : [instant du clic, élément (fonction), visible depuis, visible jusqu'à]
  const CLICKS = [
    [T.login - 0.3, () => D.bsub, T.login - 1.4, T.login + 0.3],
    [T.act, () => D.bmain, T.act - 1.0, T.act + 0.9],
    [T.pause, () => D.bpause, T.pause - 0.9, T.pause + 0.5],
    [T.resume, () => D.bmain, T.resume - 0.9, T.resume + 0.5],
    [T.end, () => D.bmain, T.end - 0.9, T.end + 0.7],
    [T.jus, () => D.bjus, T.jus - 0.9, T.jus + 0.4],
    [T.motif, () => D.fmot, T.motif - 0.8, T.motif + 0.3],
    [T.pj, () => D.fpj, T.pj - 0.7, T.pj + 0.3],
    [T.jsend, () => D.bsend, T.jsend - 0.6, T.jsend + 0.4],
    [T.absTile, () => D.tiles[0], T.absTile - 0.7, T.absTile + 0.3],
    [T.absType, () => D.sa, T.absType - 0.6, T.absType + 0.3],
    [T.dates, () => D.days[2], T.dates - 0.6, T.dates + 0.1],
    [T.dates + 0.45, () => D.days[4], T.dates, T.dates + 0.6],
    [T.ajus, () => D.ajus, T.ajus - 0.5, T.ajus + 0.3],
    [T.dem, () => D.bdem, T.dem - 0.5, T.dem + 0.5],
    [T.tcreate, () => D.btik, T.tcreate - 0.8, T.tcreate + 0.4],
    [T.payslip, () => D.rhrows[0], T.payslip - 0.7, T.payslip + 0.3],
    [T.dlT, () => D.dl, T.dlT - 0.6, T.dlT + 0.6],
  ];
  function cursorAt(t) {
    let k = -1;
    for (let i = 0; i < CLICKS.length; i++) if (t >= CLICKS[i][2] - 0.25 && t <= CLICKS[i][3] + 0.25) k = i;
    if (k < 0) { st(cur, { o: 0 }); st(rip, { o: 0 }); return; }
    const [tc, get, v0, v1] = CLICKS[k];
    const [x1, y1] = centerOf(get());
    let x0 = x1 + 160, y0 = y1 + 120;
    if (k > 0 && CLICKS[k - 1][3] >= v0 - 0.3) { const p = centerOf(CLICKS[k - 1][1]()); x0 = p[0]; y0 = p[1]; }
    const p = E.inOutCubic(seg(t, Math.max(v0, tc - 0.75), tc - 0.08));
    const press = Math.max(0, 1 - Math.abs(t - tc) / 0.1);
    const x = lerp(x0, x1, p), y = lerp(y0, y1, p);
    st(cur, { x: x - 3, y: y - 2, s: 1 - 0.14 * press, o: Math.min(seg(t, v0 - 0.25, v0), 1 - seg(t, v1, v1 + 0.25)) });
    const r = seg(t, tc, tc + 0.5);
    st(rip, { x, y, s: 0.3 + 0.9 * E.outCubic(r), o: r > 0 && r < 1 ? (1 - r) * 0.9 : 0 });
  }
  // appui visuel d'un bouton au clic
  const pressOf = (t, tc) => 1 - 0.035 * Math.max(0, 1 - Math.abs(t - tc) / 0.12);

  // ------------------------------------------------------------------ états de l'application
  function hhmm(m) { m = Math.round(m); return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }
  function appState(t) {
    // pages
    let cur = 0;
    NAV.forEach((n, i) => { if (t >= n[0]) cur = i; });
    ORDER.forEach(id => { P[id].style.display = "none"; });
    const [tn, id, url] = NAV[cur];
    // l'ancienne page s'efface vite, la nouvelle glisse ensuite (pas de superposition des deux écrans)
    const tr = E.outCubic(seg(t, tn + 0.16, tn + 0.6)), out = E.inOutSine(seg(t, tn, tn + 0.16));
    st(P[id], { o: cur ? tr : 1, x: cur ? (1 - tr) * 50 : 0 });
    if (cur && out < 1) { const prev = NAV[cur - 1][1]; P[prev].style.display = ""; st(P[prev], { o: 1 - out, x: -30 * out }); }
    setText(urlEl, url);

    // connexion
    const id1 = typed("WTL-00001", t, T.typeId, T.typeId + 0.65);
    setHTML(q(D.fid, ".v"), id1 + (t > T.typeId - 0.3 && t < T.typeId + 1.1 ? '<span class="caret"></span>' : ""));
    cls(D.fid, "focus", t > T.typeId - 0.3 && t < T.typeId + 1.1);
    D.lid.style.color = t > T.mail - 0.1 && t < T.mail + 1.0 ? "#0f5fae" : "";
    const pw0 = T.typeId + 1.1;
    setHTML(q(D.fpw, ".v"), "•".repeat(Math.round(10 * seg(t, pw0, pw0 + 0.6))) + (t > pw0 - 0.1 && t < T.login ? '<span class="caret"></span>' : ""));
    cls(D.fpw, "focus", t > pw0 - 0.1 && t < T.login);
    const busyL = t >= T.login - 0.3;
    setText(D.bsub, busyL ? "Connexion…" : "Se connecter"); cls(D.bsub, "busy", busyL);
    st(D.bsub, { s: pressOf(t, T.login - 0.3) });

    // tableau de bord : la journée
    const nextDay = t >= T.anom;
    let status = "Session de travail inactive", sc = "", times = ["—", "—", "—", "—"];
    let main = "Activer ma session", pauseBtn = false, msg = false, busy = false;
    if (!nextDay) {
      if (t >= T.act) { status = "Session de travail active"; sc = "active"; times[0] = "08:02"; main = "Terminer ma session"; pauseBtn = true; }
      if (t >= T.act && t < T.act + 0.45) { busy = true; status = "Session de travail inactive"; sc = ""; times[0] = "—"; pauseBtn = false; main = "Activer ma session"; }
      msg = t >= T.act + 0.45 && t < T.noon;
      if (t >= T.pause) { status = "En pause"; sc = "pause"; times[1] = "12:31"; main = "Reprendre ma session"; pauseBtn = false; }
      if (t >= T.resume) { status = "Session de travail active"; sc = "active"; times[2] = "13:29"; main = "Terminer ma session"; pauseBtn = false; }
      if (t >= T.end) { status = "Journée terminée"; sc = "done"; times[3] = "17:46"; msg = true; }
    } else {
      status = "Session de travail active"; sc = "active"; times = ["08:05", "—", "—", "—"]; main = "Terminer ma session"; pauseBtn = true;
    }
    setText(D.stx, status);
    D.status.className = "status " + sc;
    D.metrics.forEach((m, i) => setText(q(m, "b"), times[i]));
    setText(D.bmain, busy ? "Enregistrement…" : main); cls(D.bmain, "busy", busy);
    D.bpause.style.display = pauseBtn ? "" : "none";
    D.brow.style.gridTemplateColumns = pauseBtn ? "1fr 1fr" : "1fr";
    D.brow.style.display = t >= T.end && !nextDay ? "none" : "grid";
    D.msg.style.display = msg && !nextDay ? "" : "none";
    st(D.bmain, { s: Math.min(pressOf(t, T.act), pressOf(t, T.resume), pressOf(t, T.end)) });
    st(D.bpause, { s: pressOf(t, T.pause) });
    // halo sur la valeur qui vient de changer
    const halo = (el, t0) => { const p = seg(t, t0, t0 + 1.1); el.style.boxShadow = p > 0 && p < 1 ? `0 0 0 ${(3 + 6 * p).toFixed(1)}px rgba(26,146,248,${(0.45 * (1 - p)).toFixed(3)})` : "none"; };
    halo(D.metrics[0], T.act + 0.45); halo(D.metrics[1], T.pause); halo(D.metrics[2], T.resume); halo(D.metrics[3], T.end);
    if (t > T.minute - 0.2 && t < T.minute + 1.6 && !nextDay) D.metrics[0].style.boxShadow = `0 0 0 3px rgba(26,146,248,${(0.6 * Math.sin(Math.PI * seg(t, T.minute - 0.2, T.minute + 1.6))).toFixed(3)})`;
    // anomalie et justification
    D.anom.style.display = nextDay ? "flex" : "none";
    const sent = t >= T.jsend + 0.25;
    D.anom.className = "notice anom " + (sent ? "" : "danger");
    setHTML(D.anom.firstElementChild, sent ? "<b>Justification envoyée</b> · mardi 20 octobre : en attente de validation." : "<b>Pointage incomplet</b> · mardi 20 octobre : départ non pointé.");
    D.bjus.style.display = sent ? "none" : "";
    st(D.bjus, { s: pressOf(t, T.jus) });
    const mo = E.outCubic(seg(t, T.jus + 0.1, T.jus + 0.5)) * (1 - seg(t, T.jsend + 0.15, T.jsend + 0.45));
    st(D.mback, { o: mo });
    st(D.modal, { o: mo, y: (1 - mo) * 40, s: 0.96 + 0.04 * mo });
    const mot = t >= T.motif + 0.05;
    setHTML(q(D.fmot, ".v"), mot ? "Oubli de pointage" : "Choisir un motif");
    q(D.fmot, ".v").style.color = mot ? "var(--ink)" : "var(--muted)";
    cls(D.fmot, "focus", t > T.motif - 0.1 && t < T.motif + 0.5);
    const c0 = T.motif + 0.35, com = "Départ à 17 h 40, j'ai oublié de pointer.";
    setHTML(q(D.fcom, ".v"), typed(com, t, c0, c0 + 1.0) + (t > c0 - 0.1 && t < T.pj - 0.2 ? '<span class="caret"></span>' : ""));
    cls(D.fcom, "focus", t > c0 - 0.1 && t < T.pj - 0.2);
    setHTML(D.fpj, t >= T.pj + 0.05 ? '<span class="pdf">PDF</span> attestation-sortie.pdf' : `${ic("paperclip")} Ajouter un fichier`);
    cls(D.fpj, "file", t >= T.pj + 0.05);
    st(D.bsend, { s: pressOf(t, T.jsend) });
    D.tiles.forEach((tl, i) => { tl.style.boxShadow = i === 0 && t > T.absTile - 0.4 && t < T.abs ? "0 0 0 3px rgba(26,146,248,.35)" : "none"; });

    // congés et absences
    const absOn = t >= T.absType;
    cls(D.sa, "on", absOn); cls(D.sc, "on", false);
    const d0 = t >= T.dates, d1 = t >= T.dates + 0.45;
    D.days.forEach(d => { const n = +d.dataset.d; d.className = (n === 3 && d0) || (n === 5 && d1) ? "sel" : (n === 4 && d1 ? "mid" : ""); });
    setText(D.ctx, d1 ? "Du 3 au 5 novembre" : "");
    setHTML(D.ajus, t >= T.ajus + 0.05 ? '<span class="pdf">PDF</span> justificatif-absence.pdf' : `${ic("paperclip")} Ajouter un justificatif`);
    cls(D.ajus, "file", t >= T.ajus + 0.05);
    const dBusy = t >= T.dem && t < T.dem + 0.4;
    setText(D.bdem, dBusy ? "Envoi…" : "Envoyer la demande"); cls(D.bdem, "busy", dBusy);
    st(D.bdem, { s: pressOf(t, T.dem) });
    const nr = enter(t, T.dem + 0.4, 0.7, -18);
    st(D.nreq, { o: nr.o, y: nr.y });
    D.nreq.style.background = t > T.statut - 0.2 && t < T.statut + 1.2 ? "#f4f8fe" : "";
    qa(D.nreq, ".track i.now").forEach(i => { i.style.boxShadow = `0 0 0 ${(4 * (0.5 + 0.5 * Math.sin(t * 6))).toFixed(1)}px rgba(208,138,18,.25)`; });

    // tickets
    const o0 = T.tobj, objT = "Pas d'accès à la messagerie";
    setHTML(q(D.fobj, ".v"), typed(objT, t, o0, o0 + 0.8) + (t > o0 - 0.1 && t < o0 + 0.9 ? '<span class="caret"></span>' : ""));
    cls(D.fobj, "focus", t > o0 - 0.1 && t < o0 + 0.9);
    const de0 = o0 + 0.95, desT = "Depuis ce matin, la messagerie refuse mon mot de passe.";
    setHTML(q(D.fdes, ".v"), typed(desT, t, de0, T.tcreate - 0.35) + (t > de0 - 0.1 && t < T.tcreate - 0.2 ? '<span class="caret"></span>' : ""));
    cls(D.fdes, "focus", t > de0 - 0.1 && t < T.tcreate - 0.2);
    st(D.btik, { s: pressOf(t, T.tcreate) });
    const nt = enter(t, T.tcreate + 0.3, 0.7, -18);
    st(D.ntik, { o: nt.o, y: nt.y });
    const charge = t >= T.tcharge + 0.1;
    D.tst.className = "pill tst " + (charge ? "blue" : "grey");
    setHTML(D.tst, charge ? `${ic("check")} Pris en charge` : "Ouvert");
    setText(D.tby, charge ? "Ticket n° 142 · pris en charge par l'équipe IT" : "Ticket n° 142 · à l'instant");
    st(D.tst, { s: 1 + 0.08 * Math.sin(Math.PI * seg(t, T.tcharge + 0.1, T.tcharge + 0.5)) });

    // documents RH
    D.rhrows.forEach((r, i) => { r.style.background = i === 0 && t >= T.payslip ? "#eef4fb" : ""; });
    const pv = enter(t, T.payslip + 0.1, 0.8, 0);
    st(D.prev, { o: pv.o, x: (1 - pv.p) * 40 });
    const dlp = seg(t, T.dlT + 0.05, T.dlT + 0.85);
    D.dlbar.style.width = (100 * E.inOutSine(dlp)).toFixed(1) + "%";
    setText(D.dl, dlp >= 1 ? "Téléchargé" : (dlp > 0 ? "Téléchargement…" : "Télécharger"));
    st(D.rhlock, { s: 1 + 0.12 * Math.sin(Math.PI * seg(t, T.seul - 0.1, T.seul + 0.5)) });

    // documents de l'entreprise
    D.docs.forEach((d, i) => { const e = enter(t, T.docs + 0.25 + i * 0.09, 0.8, 30); st(d, { o: e.o, y: e.y }); });
    D.upd.forEach((u, i) => { const p = seg(t, T.ajour + i * 0.08, T.ajour + i * 0.08 + 0.5); st(u, { s: 1 + 0.12 * Math.sin(Math.PI * p) }); });
  }

  // ------------------------------------------------------------------ film
  window.renderAt = function (t) {
    // fond : nuit pour l'ouverture, puis lumière ; légère dérive des halos
    const day = E.inOutCubic(seg(t, T.logo - 0.1, T.logo + 0.7)) * (1 - E.inOutCubic(seg(t, S1("signature") + 5, S1("signature") + 6)));
    st(bgNight, { o: 1 - day });
    bg.style.background = "radial-gradient(1500px 1000px at 50% 42%, #ffffff 0%, #f4f8fd 55%, #e9f1fa 100%)";
    st(glowA, { x: 60 * Math.sin(t * 0.12), y: 40 * Math.cos(t * 0.1) });
    st(glowB, { x: -50 * Math.sin(t * 0.09), y: 30 * Math.sin(t * 0.14) });

    // ouverture : les démarches apparaissent sur les mots, puis le temps file
    const hookOut = seg(t, segT("hook", 1) + 1.2, T.logo - 0.15);
    TASKS.forEach((tk, i) => {
      const t0 = W("hook", 0, tk[3]) - 0.12;
      const sp = spring(t - t0, 0.7, 2.2);
      const pull = E.inCubic(hookOut);
      const drift = (t - t0) * 9;
      st(tasks[i], { x: 960 - 190 + tk[4] * 0.92 * (1 - pull) + Math.sign(tk[4]) * drift * (1 - pull), y: 540 - 46 + tk[5] * 0.95 * (1 - pull), s: (1.15 + 0.25 * sp) * (1 - 0.7 * pull),
                     o: clamp(sp * 1.3) * (1 - E.inCubic(seg(hookOut, 0.5, 1))), blur: 10 * (1 - clamp(sp)) + 6 * pull, ry: tk[4] > 0 ? -8 : 8 });
    });
    const r0 = segT("hook", 1), rp = seg(t, r0 - 0.2, r0 + 0.6);
    st(ring, { o: E.outCubic(rp) * (1 - E.inCubic(hookOut)), s: (0.8 + 0.2 * E.outCubic(rp)) * (1 - 0.6 * E.inCubic(hookOut)) });
    const spin = Math.max(0, t - r0);
    q(ring, ".hand").setAttribute("transform", `rotate(${(spin * 900 * (1 + spin * 0.6)) % 360} 150 150)`);
    q(ring, ".hand2").setAttribute("transform", `rotate(${(spin * 75 * (1 + spin * 0.6)) % 360} 150 150)`);
    q(ring, ".arc").setAttribute("stroke-dashoffset", (817 * (1 - clamp(spin / 2.2))).toFixed(1));
    const sk = seg(t, T.logo - 0.7, T.logo - 0.05);
    st(spark, { o: Math.sin(Math.PI * sk), s: 0.3 + 2.2 * sk });
    st(flash, { o: 0.85 * Math.max(0, 1 - Math.abs(t - T.logo) / 0.35) });

    // fenêtre et caméra
    const winOn = t >= T.winIn - 0.2 && t < S0("signature") + 2.2;
    world.style.display = winOn ? "" : "none";
    if (winOn) {
      appState(t);
      applyCamera(cameraAt(t));
      st(win, { o: 1 - E.inCubic(seg(t, T.out + 0.4, T.out + 1.9)) });
      win.style.filter = t > T.out + 0.3 ? `blur(${(8 * seg(t, T.out + 0.3, T.out + 1.4)).toFixed(2)}px)` : "none";
      // téléphone hors réseau, à côté de l'ordinateur
      const ph = E.inOutQuint(seg(t, T.net, T.net + 0.9)) * (1 - E.inOutQuint(seg(t, T.netEnd, T.netEnd + 0.7)));
      st(phone, { o: clamp(ph * 2), x: (1 - ph) * 700, ry: -10 * (1 - ph) });
    }
    // logo : la marque tourne et se pose, puis le mot se dévoile ; à « au même endroit », il rejoint la carte de connexion
    const showLogo = (tl, tg, tOut) => {
      const pm = spring(t - (tl - 0.08), 0.62, 2.0), wt = E.outExpo(seg(t, tl + 0.12, tl + 0.95));
      lm.style.clipPath = "inset(0 76% 0 0)";
      st(lm, { s: 0.6 + 0.4 * pm, r: -40 * (1 - clamp(pm)), o: clamp(pm * 1.6) });
      lm.style.transformOrigin = "13% 55%";
      lt.style.clipPath = `inset(0 ${(76 * (1 - wt)).toFixed(2)}% 0 24%)`;
      st(lt, { x: -24 * (1 - wt), o: 1 });
      const tp = E.outCubic(seg(t, tg - 0.1, tg + 0.9));
      tag.style.letterSpacing = (0.32 + 0.3 * (1 - tp)).toFixed(3) + "em";
      return { tp, out: tOut };
    };
    if (t < T.out) {
      const L = showLogo(T.logo, T.tag);
      // vol vers le logo de la carte de connexion
      const fly = E.inOutQuint(seg(t, T.winIn + 0.05, T.winIn + 1.35));
      let tx = 0, ty = 0, sc = 1;
      if (fly > 0) {
        const r = D.llogo.getBoundingClientRect();
        sc = lerp(1, r.width / LW, fly);
        tx = lerp(0, r.left + r.width / 2 - 960, fly); ty = lerp(0, r.top + r.height / 2 - 470, fly);
      }
      const handoff = seg(t, T.winIn + 1.25, T.winIn + 1.4);
      st(logo, { x: tx, y: ty, s: sc, o: (t >= T.logo - 0.3 ? 1 : 0) * (1 - handoff) });
      st(tag, { c: true, y: ty * 0.9, o: L.tp * (1 - E.outCubic(seg(t, T.winIn, T.winIn + 0.5))) });
      D.llogo.style.opacity = handoff.toFixed(3);
    } else {
      const tl2 = T.final;
      const L = showLogo(tl2, T.tag2);
      const end = seg(t, S1("signature") - 1.0, S1("signature") - 0.1);
      st(logo, { o: seg(t, tl2 - 0.7, tl2 - 0.2) * (1 - end), s: 1 + 0.025 * seg(t, tl2, S1("signature")) });
      st(tag, { c: true, o: L.tp * (1 - end) });
      D.llogo.style.opacity = 1;
    }

    cursorAt(t);

    // heure de la journée (film) : arrivée, pause, retour, départ
    const ck = [[T.dash, "Lundi 19 octobre", 482], [T.noon, "Lundi 19 octobre", 751], [T.ret, "Lundi 19 octobre", 809], [T.eve, "Lundi 19 octobre", 1066], [T.anom, "Mercredi 21 octobre", 485]];
    let ci = -1; ck.forEach((c, i) => { if (t >= c[0]) ci = i; });
    const ckOn = ci >= 0 && t < T.absTile;
    st(clock, { o: ckOn ? E.outCubic(seg(t, T.dash, T.dash + 0.5)) * (1 - seg(t, T.absTile - 0.4, T.absTile)) : 0 });
    if (ckOn) {
      const prev = ci > 0 && ci < 4 ? ck[ci - 1][2] : ck[ci][2] - 1;
      const m = lerp(prev, ck[ci][2], E.inOutCubic(seg(t, ck[ci][0], ck[ci][0] + 0.7)));
      setText(q(clock, ".cd"), ck[ci][1]); setText(q(clock, ".ct"), hhmm(m));
    }
    // annotations réseau (sous l'ordinateur et sous le téléphone)
    const nn = seg(t, T.net + 0.5, T.net + 1.0) * (1 - seg(t, T.netEnd - 0.2, T.netEnd + 0.2));
    st(noteOffice, { x: 470, y: 950, o: nn }); st(notePhone, { x: 1460, y: 950, o: nn });
  };
  // repères exportés pour les bruitages (render.js les écrit dans build/mywebtel/cues.json)
  window.FILM = { duration: TL.duration, T, clicks: CLICKS.map(c => c[0]), nav: NAV.slice(1).map(n => n[0]),
                  tasks: TASKS.map(tk => W("hook", 0, tk[3]) - 0.12), docs: DOCS.map((d, i) => T.docs + 0.25 + i * 0.09) };
  document.fonts.ready.then(() => {
    const imgs = Array.from(document.images).map(i => i.decode().catch(() => {}));
    Promise.all(imgs).then(() => { window.renderAt(0); window.READY = true; });
  });
})();
