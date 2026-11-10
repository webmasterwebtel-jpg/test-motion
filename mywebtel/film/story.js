/* MyWebtel — film V6, mise en scène.
 * Une seule caméra, un seul monde (esprit des trois références de l'utilisateur : survol de carte, travelling de ville,
 * travelling de cinéma) :
 *   I.  Nuit (ouverture façon reportage) : les démarches flottent dans le noir, l'heure s'emballe, des fils de lumière
 *       les rassemblent en un anneau ; le logo naît dans l'anneau, la caméra le traverse.
 *   II. Jour (façon pub produit) : le monde MyWebtel, un plan dont chaque quartier est une vraie page de l'interface.
 *       La caméra vole de page en page ; à chaque fonction, le composant utile sort de la page, en relief, et on s'en sert.
 *   III. Fin (façon bande-annonce) : la nuit retombe, le plan s'illumine, le logo revient sur le premier temps.
 * Tous les instants viennent des mots de la voix (timeline.json) et de la grille à 100 BPM.
 */
(function () {
  "use strict";
  const stage = document.getElementById("stage");
  const mkCanvas = id => { const c = add(stage, `<canvas class="layer" id="${id}" width="${VW}" height="${VH}"></canvas>`); return [c, c.getContext("2d")]; };
  const [bgc, bg] = mkCanvas("floor");
  const viewport = add(stage, `<div id="viewport"></div>`);
  const world = add(viewport, `<div id="world"></div>`);
  const [fxc, fx] = mkCanvas("light");
  const hud = add(stage, `<div id="hud"></div>`);
  const grade = add(stage, `<div id="grade"><div class="vignette"></div><div class="grain"></div><div class="bars" style="top:0"></div><div class="bars" style="bottom:0;top:auto"></div><div class="flash"></div></div>`);
  const [vign, grain, barTop, barBot, flash] = grade.children;

  // grain de film (bruit fixe, décalé à chaque image)
  { const c = document.createElement("canvas"); c.width = c.height = 256; const g = c.getContext("2d"), im = g.createImageData(256, 256);
    for (let i = 0; i < im.data.length; i += 4) { const v = Math.floor(hash(i * 0.37) * 255); im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    g.putImageData(im, 0, 0); grain.style.backgroundImage = `url(${c.toDataURL()})`; }

  // ------------------------------------------------------------------ instants (mots de la voix)
  Object.assign(T, {
    pointer: W("hook", 0, "Pointer"), conge: W("hook", 0, "congé"), fiche: W("hook", 0, "fiche"), signerH: W("hook", 0, "signer"),
    boulot: W("hook", 0, "Au"), temps: W("hook", 0, "temps"), fou: W("hook", 0, "fou"),
    ques: segT("hook", 1), meme: W("hook", 1, "même"), endroit: W("hook", 1, "endroit"),
    brand: W("reveal", 0, "MyWebtel"), tag: W("reveal", 0, "espace"),
    matin: W("pointage", 0, "matin"), in: W("pointage", 0, "clic") + 0.04, pause: W("pointage", 0, "pause"), ret: W("pointage", 0, "retour"),
    out: W("pointage", 0, "départ"), saved: W("pointage", 0, "enregistré"), minute: W("pointage", 0, "minute"),
    cg: W("conges", 0, "congés"), solde: W("conges", 0, "solde"), rights: W("conges", 0, "droits"), seniority: W("conges", 0, "d'ancienneté"),
    abs: W("absences", 0, "absence"), declare: W("absences", 0, "déclares"), proof: W("absences", 0, "justificatif"),
    absSend: W("absences", 0, "et") - 0.04, rh: W("absences", 0, "RH"), reste: W("absences", 0, "reste"),
    doc: W("signature", 0, "document"), kImp: W("signature", 0, "l'imprimer"), kSig: W("signature", 0, "signer", 1), kScan: W("signature", 0, "scanner"),
    non: W("signature", 0, "Sauf"), nonW: W("signature", 0, "non"), recv: W("signature", 0, "reçois"), docs: W("signature", 0, "documents"),
    open: W("signature", 0, "signes") - 0.08, nom: W("signature", 0, "nom"), draw: W("signature", 0, "dessines") - 0.12,
    code: W("signature", 0, "code"), mail: W("signature", 0, "mail"), tape: W("signature", 0, "tapes"), signed: W("signature", 0, "signé") - 0.08,
    att: W("demandes", 0, "attestation"), question: W("demandes", 0, "question"), fill: W("demandes", 0, "demande"), clics: W("demandes", 0, "clics"),
    process: W("demandes", 0, "traitement"),
    notes: W("contenu", 0, "notes"), dir: W("contenu", 0, "Direction"), rhC: W("contenu", 0, "RH"), read: W("contenu", 0, "lis"),
    confirm: W("contenu", 0, "confirmes"), lu: W("contenu", 0, "clic"),
    coll: W("mail", 0, "collègues"), chat: W("mail", 0, "échanges"), mailW: W("mail", 0, "Mail"), souci: W("mail", 0, "souci"),
    tick: W("mail", 0, "support"), ticket: W("mail", 0, "ticket"), charge: W("mail", 0, "charge"),
    q: W("agent", 0, "question"), launch: W("agent", 0, "l'agent"), chips: [W("agent", 0, "solde"), W("agent", 0, "démarche"), W("agent", 0, "souci")],
    answer: W("agent", 0, "répond") - 0.1, prep: W("agent", 0, "prépare"), toi: W("agent", 0, "Toi"), okAgent: W("agent", 0, "confirmer") + 0.05,
    finBrand: W("fin", 0, "MyWebtel"), finTag: W("fin", 0, "espace"),
  });
  T.logo = onBar(T.brand - 0.35);                         // le logo tombe sur un premier temps, juste avant « MyWebtel »
  T.dive = Math.max(T.logo + 1.9, W("reveal", 0, "collaborateur") + 0.35);
  T.day = onBar(T.dive + 0.62);                            // éclair : on sort de l'anneau, au-dessus du monde, sur un premier temps
  T.dive = Math.min(T.dive, T.day - 0.5);
  T.nonEnd = T.nonW + 0.32;
  T.drawEnd = T.code - 0.3;
  T.consent = T.mail + 0.32;
  T.fileIn = T.proof + 0.55;
  T.ask = T.launch + 0.5; T.askSend = T.chips[0] - 0.12;
  T.agentSent = T.okAgent + 1.0;
  T.beamSupport = T.chips[2];
  T.mailType = T.chat - 0.05; T.mailSend = T.mailW + 0.42;
  T.tickType = T.tick + 0.3;
  T.final = onBar(T.finBrand - 0.4) + 0.06;
  T.end = T.final - 1.7;
  T.dusk = T.q - 1.1;

  // ------------------------------------------------------------------ le monde MyWebtel : un plan de vraies pages
  const SX = 1440 + 560, SZ = 900 + 600;
  const MAP = {                                            // [colonne, rangée] ; le nord (rangée 0) est en haut
    absences: [-1, -1], sign: [0, -1], requests: [1, -1],
    leaves: [-1, 0], dashboard: [0, 0], content: [1, 0],
    attendance: [-1, 1], support: [0, 1], mail: [1, 1],
  };
  const LABEL = { dashboard: ["home", "Mon espace"], attendance: ["clock", "Pointage"], leaves: ["calendar", "Mes congés"], absences: ["alert", "Mes absences"],
                  sign: ["doc", "Mes documents"], requests: ["req", "Mes demandes RH"], content: ["grid", "Contenu"], mail: ["mail", "Mail"], support: ["shield", "Support IT"] };
  const TILE = {};
  const pos = id => [MAP[id][0] * SX, 0, MAP[id][1] * SZ];
  for (const id of Object.keys(MAP)) TILE[id] = makeTile(world, id);
  const labels = {};
  for (const id of Object.keys(MAP)) labels[id] = new Obj(add(world, `<div class="label"><span class="ic">${ic(LABEL[id][0])}</span>${LABEL[id][1]}</div>`), 420, 98);
  // composants sortis de leur page (découpes mesurées au chargement)
  const CL = {
    punch: makeClip(world, "attendance", "punch", bySel(".mw-punch-card"), 0),
    today: makeClip(world, "attendance", "today", byFilm("today"), 0),
    metric: makeClip(world, "leaves", "metric", d => rectEl(d.querySelector('[data-film="metrics"]').firstElementChild), 0),
    senior: makeClip(world, "leaves", "senior", byFilm("seniority"), 4),
    absForm: makeClip(world, "absences", "absForm", bySel(".mw-two > .mw-card"), 0),
    docRow: makeClip(world, "sign", "docRow", bySel(".mw-document-row"), 6),
    dialog: makeClip(world, "sign", "dialog", d => { const g = d.querySelector('[data-film="sign-dialog"]'); g.showModal(); const r = rectEl(g); g.close(); return r; }, 0),
    reqForm: makeClip(world, "requests", "reqForm", d => rectEl(d.querySelector('[data-film="req-cats"]').closest(".mw-card")), 0),
    note: makeClip(world, "content", "note", bySel(".mw-note-article"), 0),
    agent: makeClip(world, "agent", "agent", byFilm("agent-panel"), 0),
  };
  const halos = {}, shadows = {};
  for (const k of Object.keys(CL)) {
    halos[k] = new Obj(add(world, `<div class="halo"></div>`), 10, 10);
    shadows[k] = new Obj(add(world, `<div class="shadow"></div>`), 10, 10);
  }
  // instant d'apparition / de retour de chaque découpe : [montée, retour, hauteur, échelle]
  const LIFT = {};

  // ------------------------------------------------------------------ objets de l'ouverture (nuit)
  const TASKS = [["clock", "Pointage", "Commencer ma journée", "pointer", [-760, -430, 1500], 16],
                 ["calendar", "Mes congés", "24 jours disponibles", "conge", [760, -560, 700], -16],
                 ["file", "Fiche de paie", "Octobre 2026 · PDF", "fiche", [-700, -250, -60], 14],
                 ["pen", "Document à signer", "Avenant au contrat", "signerH", [720, -330, -760], -14]];
  const tasks = TASKS.map(([i, a, b]) => new Obj(add(world, `<div class="task"><span class="ic">${ic(i)}</span><div>${a}<small>${b}</small></div></div>`), 640, 126));
  const digits = new Obj(add(world, `<div class="big">08:00</div>`), 760, 300);
  const quest = new Obj(add(world, `<div class="kw night"></div>`), 1700, 120);
  const P0 = [0, -360, -2300];                              // point de convergence : l'anneau, puis le logo
  // logo réel (vectorisé) : marque bleue + mot en blanc sur la nuit, avec un léger relief (couches décalées)
  const LW = 1000, LH = Math.round(LW * 1224 / 3520);
  const LOGO_LAYERS = 10;
  const logoEl = add(world, `<div style="width:${LW}px;height:${LH}px;transform-style:preserve-3d"></div>`);
  for (let i = LOGO_LAYERS; i >= 0; i--) {                 // relief : couches bleu profond, puis la face (variante blanche du vrai logo)
    logoEl.appendChild(h(`<img src="brand/webtel-logo-${i ? "depth" : "white"}.svg" style="position:absolute;inset:0;width:100%;transform:translateZ(${-i * 2.4}px)">`));
  }
  const logo = new Obj(logoEl, LW, LH);
  const tagEl = add(world, `<div class="tagline">${"MYWEBTEL · ESPACE COLLABORATEUR".split("").map(c => `<span>${c === " " ? "&nbsp;" : c}</span>`).join("")}</div>`);
  const tagline = new Obj(tagEl, 1000, 50);
  const subEl = add(world, `<div class="subline">Pointage<i>·</i>Congés<i>·</i>Absences<i>·</i>Signature<i>·</i>Demandes RH<i>·</i>Agent IA</div>`);
  const subline = new Obj(subEl, 1200, 50);

  // ------------------------------------------------------------------ objets du jour
  // mots clés (tapés mot à mot sur la voix ; le mot fort en bleu)
  function kw(html, w = 1400, night = false) {
    const el = add(world, `<div class="kw${night ? " night" : ""}">${html}</div>`);
    opa(el, 0);
    return Object.assign(new Obj(el, w, 120), { words: qa(el, "span") });
  }
  const K = {
    clic: kw(`<span>un</span><span><b>clic.</b></span>`, 520),
    minute: kw(`<span>à</span><span>la</span><span><b>minute</b></span><span><b>près.</b></span>`, 900),
    deux: kw(`<span>en</span><span><b>deux</b></span><span><b>clics.</b></span>`, 780),
    lu: kw(`<span>en</span><span><b>un</b></span><span><b>clic.</b></span>`, 520),
  };
  const ruleEl = add(world, `<div class="rule"><div style="display:flex;align-items:center;gap:16px;font:600 30px Inter;color:#08264b">${ic("calendar")} Ancienneté</div>
    <div class="bar"><div class="fill"></div><div class="knob">${ic("lock")}</div></div><div class="ticks"><span>Arrivée</span><span>6 mois</span><b>1 an</b></div></div>`);
  const rule = new Obj(ruleEl, 980, 270);
  const ruleFill = q(ruleEl, ".fill"), ruleKnob = q(ruleEl, ".knob");
  const pdf = new Obj(add(world, `<div class="pdf"><span class="tag">PDF</span><div class="l" style="width:90%"></div><div class="l"></div><div class="l" style="width:70%"></div><div class="l" style="width:84%"></div><b>certificat-medical.pdf</b></div>`), 300, 380);
  // signature, l'ancienne méthode : une seule composition (mots à gauche, feuille à droite, « Sauf que non. » dessous),
  // figée dans le monde face à la caméra ; sur « non. », elle vole en éclats (copies de la composition finale).
  const SIG_W = 1640, SIG_H = 1100;
  const sigScene = fin => `<div style="position:absolute;left:0;top:0;width:${SIG_W}px;height:${SIG_H}px;border-radius:44px;background:linear-gradient(160deg,rgba(255,255,255,.97),rgba(238,245,253,.95));box-shadow:0 60px 140px rgba(4,27,52,.28),inset 0 0 0 2px rgba(255,255,255,.9),inset 0 0 0 3px rgba(0,143,241,.10)">
    <div class="kw" style="position:absolute;left:70px;top:210px;font-size:96px"><span class="w0"><b>Imprimer.</b></span></div>
    <div class="kw" style="position:absolute;left:70px;top:350px;font-size:96px"><span class="w1"><b>Signer.</b></span></div>
    <div class="kw" style="position:absolute;left:70px;top:490px;font-size:96px"><span class="w2"><b>Scanner</b></span><span class="w3">?</span></div>
    <div class="kw" style="position:absolute;left:70px;top:740px;font-size:118px"><span class="w4">Sauf</span><span class="w5">que</span><span class="w6"><b>non.</b></span></div>
    <div class="paper" style="position:absolute;left:830px;top:50px"><h5>AVENANT AU CONTRAT DE TRAVAIL</h5><div class="l" style="width:62%;margin-top:18px"></div>
      <div class="l" style="margin-top:46px"></div><div class="l"></div><div class="l" style="width:88%"></div><div class="l"></div><div class="l" style="width:76%"></div>
      <div class="l" style="margin-top:46px"></div><div class="l" style="width:92%"></div><div class="l" style="width:64%"></div>
      <svg viewBox="0 0 400 140" style="position:absolute;left:330px;top:760px;width:360px;overflow:visible"><path class="ink" d="M10 90 C 40 20, 70 20, 60 80 S 110 120, 130 60 S 170 10, 190 70 S 230 110, 250 60 C 262 30, 285 34, 292 78 S 330 100, 390 50" fill="none" stroke="#0b2a4d" stroke-width="7" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${fin ? 0 : 1}"/></svg>
      ${fin ? "" : '<div class="scan"></div>'}</div></div>`;
  const sigSet = new Obj(add(world, `<div style="width:${SIG_W}px;height:${SIG_H}px">${sigScene(false)}</div>`), SIG_W, SIG_H);
  const sigWords = [0, 1, 2, 3, 4, 5, 6].map(i => q(sigSet.el, ".w" + i));
  const sigPaper = q(sigSet.el, ".paper"), paperInk = q(sigSet.el, ".ink"), paperScan = q(sigSet.el, ".scan");
  const SHARDS = [];
  {
    const cols = 7, rows = 5, pts = [];
    for (let j = 0; j <= rows; j++) for (let i = 0; i <= cols; i++) {
      const jx = i > 0 && i < cols ? (hash(i * 13 + j * 7) - 0.5) * 150 : 0, jy = j > 0 && j < rows ? (hash(i * 5 + j * 17) - 0.5) * 140 : 0;
      pts.push([i * SIG_W / cols + jx, j * SIG_H / rows + jy]);
    }
    const P = (i, j) => pts[j * (cols + 1) + i];
    for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) {
      const a2 = P(i, j), b2 = P(i + 1, j), c = P(i + 1, j + 1), d2 = P(i, j + 1);
      for (const tri of (hash(i + j * 9) > 0.5 ? [[a2, b2, c], [a2, c, d2]] : [[a2, b2, d2], [b2, c, d2]])) {
        const bx = Math.floor(Math.min(...tri.map(p => p[0]))), by = Math.floor(Math.min(...tri.map(p => p[1])));
        const bw = Math.ceil(Math.max(...tri.map(p => p[0]))) - bx, bh = Math.ceil(Math.max(...tri.map(p => p[1]))) - by;
        const el = add(world, `<div class="shard" style="width:${bw}px;height:${bh}px;clip-path:polygon(${tri.map(p => (p[0] - bx).toFixed(0) + "px " + (p[1] - by).toFixed(0) + "px").join(",")})"><div style="position:absolute;left:${-bx}px;top:${-by}px">${sigScene(true)}</div></div>`);
        const cx = (tri[0][0] + tri[1][0] + tri[2][0]) / 3, cy = (tri[0][1] + tri[1][1] + tri[2][1]) / 3;
        SHARDS.push({ o: new Obj(el, bw, bh), bx, by, cx, cy, r: hash(cx * 0.13 + cy * 0.29), r2: hash(cx * 0.71 + cy * 0.17) });
      }
    }
  }
  let SIGP = [0, -400, 0], SIGROT = M4.I(), SIGS = 0.5;
  const mailCard = new Obj(add(world, `<div class="mailcard"><div class="from"><i>W</i><div><b style="color:#08264b">MyWebtel</b> · à l’instant</div></div>
    <h4>Votre code de signature</h4><p>Votre code pour signer « Avenant au contrat de travail » :</p>
    <div class="code">${"482913".split("").map(c => `<span>${c}</span>`).join("")}</div><p style="margin-top:16px;font-size:20px">Valable 10 minutes. Ne communiquez ce code à personne.</p></div>`), 780, 470);
  const mailDigits = qa(mailCard.el, ".code span");
  const orb = new Obj(add(world, `<div class="orb">${ic("spark")}</div>`), 300, 300);
  const sentCard = new Obj(add(world, `<div class="label" style="font-size:34px"><span class="ic">${ic("calendar")}</span>Congés · 22 → 24/12</div>`), 520, 98);

  // ------------------------------------------------------------------ HUD : curseur, pastilles ✓
  const CURSOR = `<svg class="cursor" viewBox="0 0 34 44"><path d="M3 2l26 24H16l7 14-5 2-7-14-8 8z" fill="#fff" stroke="#041b34" stroke-width="2.4" stroke-linejoin="round"/></svg>`;
  const cur = add(hud, CURSOR), rip = add(hud, `<div class="ripple"></div>`);
  const CHECKS = [];
  const check = (txt, t0, t1) => { CHECKS.push({ el: add(hud, `<div class="check"><span class="ok">${ic("check")}</span>${txt}</div>`), t0, t1 }); };

  // ------------------------------------------------------------------ chargement
  window.FILM = { duration: TL.duration, T };
  Promise.all([document.fonts.ready, ...LOADS]).then(() => {
    layoutClips();
    setup();
    const imgs = Array.from(document.images).map(i => i.decode().catch(() => {}));
    Promise.all(imgs).then(() => { window.renderAt(0); window.READY = true; });
  });

  // ------------------------------------------------------------------ cadrages
  // cible et distance pour qu'un rectangle d'une page (px de la page) remplisse l'écran ; lift : hauteur au-dessus du sol
  function frameRect(id, r, { fill = 0.86, pitch = 90, yaw = 0, roll = 0, lift = 0, F = 1600, dx = 0, dz = 0, s = 1 } = {}) {
    const P = TILE[id].world(r.x + r.w / 2, r.y + r.h / 2);
    const dist = F * Math.max((r.w * s) / (VW * fill), (r.h * s) / (VH * fill));
    return camState({ tx: P[0] + dx, ty: -lift, tz: P[2] + dz, dist, pitch, yaw, roll, F });
  }
  const R = (id, name) => INST[id].rects[name];
  const FULL = id => ({ x: 0, y: 0, w: 1440, h: PAGE_H[id] || 900 });
  const elRect = (id, sel) => rectEl(docOf(id).querySelector(sel));
  const fRect = (id, name) => elRect(id, `[data-film="${name}"]`);
  const union = (...rs) => { const x0 = Math.min(...rs.map(r => r.x)), y0 = Math.min(...rs.map(r => r.y)), x1 = Math.max(...rs.map(r => r.x + r.w)), y1 = Math.max(...rs.map(r => r.y + r.h)); return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 }; };
  const grow = (r, dx, dy = dx) => ({ x: r.x - dx, y: r.y - dy, w: r.w + 2 * dx, h: r.h + 2 * dy });

  let KEYS = [];                                            // [instant, état caméra, courbe, arc]
  let CLICKS = [];
  function setup() {
    for (const o of Object.values(K)) { o.w = o.el.offsetWidth; o.h = o.el.offsetHeight; }   // largeur réelle des mots clés
    // tuiles, étiquettes
    for (const id of Object.keys(MAP)) {
      const [x, , z] = pos(id);
      TILE[id].place({ x, y: 0, z, flat: true });
    }
    // levées des composants : [début, fin, hauteur, échelle]
    Object.assign(LIFT, {
      punch: [T.in - 0.75, T.saved - 0.15, 150, 1.0], today: [T.saved - 0.35, T.cg - 1.0, 150, 1.0],
      metric: [T.solde - 0.55, T.rights - 0.25, 150, 1.0], senior: [T.rights - 0.45, T.abs - 1.0, 150, 1.0],
      absForm: [T.declare - 0.7, T.absSend + 0.45, 120, 1.0],
      docRow: [T.recv - 0.35, T.open + 0.15, 150, 1.0], dialog: [T.open + 0.12, T.signed + 0.35, 170, 1.0],
      reqForm: [T.att - 0.5, T.clics + 0.45, 120, 1.0], note: [T.read - 0.5, T.lu + 1.1, 130, 1.0],
      agent: [T.launch - 0.1, T.end + 0.6, 0, 1.0],
    });
    // pastilles ✓ (façon pub produit, en haut à gauche)
    check("Enregistré à la minute près", T.minute + 0.1, T.cg - 1.2);
    check("Droits ouverts après 1 an d’ancienneté", T.seniority + 0.2, T.abs - 1.0);
    check("Les RH s’occupent du reste", T.rh + 0.1, T.doc - 1.0);
    check("Document signé", T.signed + 0.45, T.att - 1.2);
    check("Envoyée en deux clics", T.clics + 0.35, T.notes - 1.2);
    check("Lecture confirmée", T.lu + 0.3, T.coll - 1.2);
    check("Ticket pris en charge", T.charge + 0.1, T.q - 0.6);
    check("Rien n’est envoyé sans ta confirmation", T.okAgent + 0.35, T.end + 0.2);

    // ---------------------------------------------------------------- caméra
    const night0 = camState({ tx: 0, ty: -330, tz: 2900, dist: 1700, pitch: 3, yaw: 0, F: 1500 });
    const night1 = camState({ tx: 0, ty: -340, tz: -560, dist: 1700, pitch: 2, yaw: 0, F: 1500 });
    const nightLogo = camState({ tx: P0[0], ty: P0[1], tz: P0[2], dist: 1750, pitch: 0, yaw: 0, F: 1500 });
    const through = camState({ tx: P0[0], ty: P0[1], tz: P0[2] - 2600, dist: 300, pitch: 0, yaw: 0, F: 1100 });
    const over = camState({ tx: 0, ty: 0, tz: 260, dist: 8200, pitch: 57, yaw: -14, F: 1600 });
    const over2 = camState({ tx: -300, ty: 0, tz: 500, dist: 7000, pitch: 62, yaw: -8, F: 1600 });
    const at = (id, r, o = {}) => frameRect(id, r, o);
    const dlgR = R("sign", "dialog");
    const preview = elRect("sign", ".mw-preview-stage");
    const k = (t, s, ease = E.inOutCubic, arc = 0) => KEYS.push([t, s, ease, arc]);
    // I. nuit : travelling avant, entre les démarches, jusqu'à l'anneau
    k(0, night0);
    k(T.endroit + 0.3, night1, E.inOutSine);
    k(T.logo - 0.2, nightLogo, E.inOutCubic);
    k(T.dive - 0.05, camState(Object.assign({}, nightLogo, { dist: 1550 })), E.lin);
    k(T.day - 0.02, through, E.inExpo);
    // II. jour : au-dessus du monde, puis plongée vers le pointage
    k(T.day, over, E.lin);
    k(T.matin - 0.5, over2, E.outCubic);
    const RR = (x, y, w, h) => ({ x, y, w, h });
    k(T.in - 0.45, at("attendance", RR(250, 200, 820, 540), { fill: 0.86, lift: 150, pitch: 82, yaw: -4 }), E.inOutQuart);
    k(T.out + 0.2, at("attendance", RR(250, 200, 820, 540), { fill: 0.84, lift: 150, pitch: 86, yaw: 2 }), E.inOutSine);
    k(T.saved + 0.15, at("attendance", RR(260, 230, 1170, 390), { fill: 0.86, lift: 150, pitch: 84, yaw: -2 }), E.inOutCubic);
    k(T.minute + 1.0, at("attendance", RR(260, 230, 1170, 390), { fill: 0.84, lift: 150, pitch: 86, yaw: 1 }), E.inOutSine);
    // vols de page en page : on monte, on traverse le plan, on redescend
    const fly = (t0, t1, s1) => { k(t0, Object.assign({}, KEYS[KEYS.length - 1][1]), E.inOutSine); k(t1, s1, E.inOutQuart, 2.1); };
    fly(T.cg - 1.35, T.cg - 0.05, at("leaves", RR(250, 90, 820, 300), { fill: 0.86, lift: 150, pitch: 80, yaw: 3 }));
    k(T.rights - 0.45, at("leaves", RR(250, 90, 820, 300), { fill: 0.84, lift: 150, pitch: 84, yaw: -2 }), E.inOutSine);
    k(T.rights + 0.25, at("leaves", RR(400, 100, 1010, 500), { fill: 0.88, lift: 150, pitch: 80, yaw: -3 }), E.inOutCubic);
    k(T.seniority + 1.2, at("leaves", RR(400, 100, 1010, 500), { fill: 0.86, lift: 150, pitch: 84, yaw: 2 }), E.inOutSine);
    fly(T.abs - 1.3, T.abs - 0.05, at("absences", RR(270, 200, 1000, 760), { fill: 0.9, lift: 120, pitch: 80, yaw: -3 }));
    k(T.absSend + 0.25, at("absences", RR(270, 200, 1000, 760), { fill: 0.88, lift: 120, pitch: 84, yaw: 2 }), E.inOutSine);
    k(T.rh - 0.05, at("absences", RR(840, 110, 580, 520), { fill: 0.8, pitch: 80, yaw: -2 }), E.inOutCubic);
    k(T.reste + 0.6, at("absences", RR(840, 110, 580, 520), { fill: 0.78, pitch: 84, yaw: 1 }), E.inOutSine);
    // signature : la composition d'abord (plan large et incliné), puis la vraie page
    fly(T.doc - 1.2, T.doc + 0.05, at("sign", FULL("sign"), { fill: 1.05, pitch: 58, yaw: 0, dz: 520 }));
    k(T.nonEnd + 0.45, at("sign", FULL("sign"), { fill: 1.0, pitch: 60, yaw: 0, dz: 480 }), E.inOutSine);
    k(T.recv + 0.05, at("sign", RR(270, 260, 1140, 500), { fill: 0.9, lift: 150, pitch: 82, yaw: -3 }), E.inOutQuart);
    k(T.open + 0.1, at("sign", RR(270, 260, 1140, 500), { fill: 0.88, lift: 150, pitch: 85, yaw: 2 }), E.inOutSine);
    k(T.nom - 0.1, at("sign", dlgR, { fill: 0.8, lift: 170, pitch: 84, yaw: -2 }), E.inOutCubic);
    k(T.code - 0.2, at("sign", dlgR, { fill: 0.8, lift: 170, pitch: 86, yaw: 1 }), E.inOutSine);
    k(T.mail + 0.15, at("sign", RR(450, 40, 1400, 820), { fill: 0.92, lift: 170, pitch: 84, yaw: -1 }), E.inOutCubic);
    k(T.signed - 0.05, at("sign", RR(450, 40, 1400, 820), { fill: 0.9, lift: 170, pitch: 86, yaw: 1 }), E.inOutSine);
    k(T.signed + 0.75, at("sign", grow(preview, 90), { fill: 0.8, pitch: 82, yaw: 2 }), E.inOutCubic);
    k(T.att - 1.25, at("sign", grow(preview, 90), { fill: 0.78, pitch: 86, yaw: -1 }), E.inOutSine);
    fly(T.att - 1.2, T.att - 0.1, at("requests", RR(270, 200, 1110, 720), { fill: 0.9, lift: 120, pitch: 80, yaw: 3 }));
    k(T.clics + 0.3, at("requests", RR(270, 200, 1110, 720), { fill: 0.88, lift: 120, pitch: 85, yaw: -2 }), E.inOutSine);
    k(T.process - 0.25, at("requests", RR(840, 200, 590, 500), { fill: 0.8, pitch: 82, yaw: 2 }), E.inOutCubic);
    k(T.notes - 1.3, at("requests", RR(840, 200, 590, 500), { fill: 0.78, pitch: 85, yaw: -1 }), E.inOutSine);
    fly(T.notes - 1.25, T.notes - 0.05, at("content", RR(280, 180, 1130, 420), { fill: 0.9, pitch: 78, yaw: -2 }));
    k(T.read - 0.45, at("content", RR(280, 180, 1130, 420), { fill: 0.88, pitch: 84, yaw: 2 }), E.inOutSine);
    k(T.read + 0.2, at("content", RR(150, 250, 1250, 610), { fill: 0.9, lift: 130, pitch: 82, yaw: -2 }), E.inOutCubic);
    k(T.lu + 0.9, at("content", RR(150, 250, 1250, 610), { fill: 0.88, lift: 130, pitch: 86, yaw: 1 }), E.inOutSine);
    fly(T.coll - 1.25, T.coll - 0.05, at("mail", RR(620, 250, 790, 610), { fill: 0.86, pitch: 80, yaw: 2 }));
    k(T.souci - 0.3, at("mail", RR(620, 250, 790, 610), { fill: 0.84, pitch: 85, yaw: -1 }), E.inOutSine);
    fly(T.souci - 0.25, T.tick + 0.1, at("support", RR(270, 200, 1150, 720), { fill: 0.9, pitch: 80, yaw: -2 }));
    k(T.charge + 0.5, at("support", RR(270, 200, 1150, 720), { fill: 0.88, pitch: 85, yaw: 1 }), E.inOutSine);
    // agent : on s'élève au-dessus du plan, l'agent apparaît au-dessus de tout
    const AG = [0, -1250, 260];
    const agentView = camState({ tx: AG[0], ty: AG[1] + 300, tz: AG[2] + 300, dist: 5200, pitch: 52, yaw: -6, F: 1600 });
    const agentClose = camState({ tx: AG[0] + 40, ty: AG[1] + 40, tz: AG[2], dist: 1450, pitch: 36, yaw: -3, F: 1600 });
    const agentClose2 = camState({ tx: AG[0] + 60, ty: AG[1] + 170, tz: AG[2], dist: 1250, pitch: 36, yaw: 2, F: 1600 });
    k(T.q - 0.2, agentView, E.inOutQuart, 0.6);
    k(T.launch - 0.1, camState(Object.assign({}, agentView, { dist: 4600, yaw: -2 })), E.inOutSine);
    k(T.ask + 0.35, agentClose, E.inOutCubic);
    k(T.chips[0] - 0.1, camState(Object.assign({}, agentView, { dist: 4300, yaw: 4, pitch: 55 })), E.inOutCubic);
    k(T.chips[2] + 0.9, camState(Object.assign({}, agentView, { dist: 4100, yaw: 8, pitch: 56 })), E.inOutSine);
    k(T.answer + 0.15, agentClose2, E.inOutCubic);
    k(T.okAgent + 0.35, camState(Object.assign({}, agentClose2, { dist: 1200, yaw: -1 })), E.inOutSine);
    k(T.agentSent + 0.2, camState(Object.assign({}, agentView, { dist: 4300, yaw: 6, pitch: 54 })), E.inOutCubic);
    // III. fin : la nuit retombe, le plan s'illumine, le logo revient
    const finalView = camState({ tx: 0, ty: -1010, tz: -600, dist: 2500, pitch: 12, yaw: 0, F: 1500 });
    k(T.end, camState(Object.assign({}, agentView, { dist: 5600, yaw: 10, pitch: 50 })), E.inOutSine);
    k(T.final + 0.05, finalView, E.inOutQuart);
    k(TL.duration, camState(Object.assign({}, finalView, { dist: 2350 })), E.outCubic);
    KEYS.sort((a, b) => a[0] - b[0]);
    {                                                     // pose de la composition « imprimer, signer, scanner » : face à la caméra prévue
      const c0 = solveCamera(cameraAt(T.kScan, true));
      const fwd = V3.mul(c0.b, -1), D = 1250;
      SIGP = V3.add(c0.C, V3.mul(fwd, D)); SIGROT = c0.rot.slice(); SIGS = (VW * 0.86) / SIG_W * D / c0.F;
    }

    // ---------------------------------------------------------------- clics : [instant, point écran(), visible de, à]
    const P = (id, name, where) => () => elemPoint(id, docOf(id).querySelector(`[data-film="${name}"]`), where);
    const Ps = (id, sel, where) => () => elemPoint(id, docOf(id).querySelector(sel), where);
    CLICKS = [
      [T.in, P("attendance", "punch", "punch"), T.in - 0.75, T.out + 0.6], [T.pause, P("attendance", "punch", "punch"), T.in, T.out + 0.6],
      [T.ret, P("attendance", "punch", "punch"), T.in, T.out + 0.6], [T.out, P("attendance", "punch", "punch"), T.in, T.out + 0.6],
      [T.absSend, P("absences", "abs-send", "absForm"), T.absSend - 0.8, T.absSend + 0.45],
      [T.open, P("sign", "sign-open", "tile"), T.open - 0.8, T.open + 0.3],
      [T.draw, () => elemPoint("sign", docOf("sign").querySelector('[data-film="sign-tabs"] [data-sign-mode="draw"]'), "dialog"), T.draw - 0.6, T.draw + 1.2],
      [T.code, P("sign", "sign-code-btn", "dialog"), T.code - 0.7, T.signed + 0.4], [T.tape - 0.15, P("sign", "sign-code", "dialog"), T.code, T.signed + 0.4],
      [T.consent, P("sign", "sign-consent", "dialog"), T.code, T.signed + 0.4], [T.signed, P("sign", "sign-confirm", "dialog"), T.code, T.signed + 0.4],
      [T.fill - 0.2, () => elemPoint("requests", docOf("requests").querySelector('[data-film="req-cats"] button'), "reqForm"), T.fill - 0.8, T.clics + 0.5],
      [T.clics, P("requests", "req-send", "reqForm"), T.fill - 0.2, T.clics + 0.5],
      [T.confirm, P("content", "note-check", "note"), T.confirm - 0.7, T.lu + 0.5], [T.lu, P("content", "note-btn", "note"), T.confirm, T.lu + 0.5],
      [T.mailSend, P("mail", "mail-send", "tile"), T.mailSend - 0.8, T.mailSend + 0.4],
      [T.ticket - 0.1, P("support", "tick-send", "tile"), T.ticket - 0.8, T.ticket + 0.4],
      [T.askSend, P("agent", "agent-send", "agent"), T.askSend - 0.7, T.askSend + 0.35],
      [T.okAgent, P("agent", "agent-confirm", "agent"), T.toi - 0.1, T.okAgent + 0.6],
    ].sort((a, b) => a[0] - b[0]);
    window.FILM = { duration: TL.duration, T, clicks: CLICKS.map(c => c[0]), flights: FLIGHTS(), checks: CHECKS.map(c => c.t0),
                    lifts: Object.values(LIFT).map(v => v[0]), tileDelays: Object.keys(MAP).map(id => Math.hypot(pos(id)[0], pos(id)[2]) / 5200).sort((a, b) => a - b) };
  }
  const FLIGHTS = () => KEYS.map((k, i) => (k[3] > 0 ? [KEYS[i - 1][0], k[0]] : null)).filter(Boolean);

  // ------------------------------------------------------------------ caméra à l'instant t
  function cameraAt(t, still = false) {
    let i = 0;
    while (i < KEYS.length - 1 && KEYS[i + 1][0] <= t) i++;
    if (i >= KEYS.length - 1) return Object.assign({}, KEYS[KEYS.length - 1][1]);
    const [t0, s0] = KEYS[i], [t1, s1, ease, arc] = KEYS[i + 1];
    const p = ease(seg(t, t0, t1));
    const s = lerpCam(s0, s1, p);
    if (arc) {                                             // vol : on prend de la hauteur et on s'incline au milieu du trajet
      const b = Math.sin(Math.PI * seg(t, t0, t1));
      s.dist *= 1 + (arc - 1) * b;
      s.pitch = lerp(s.pitch, 58, 0.55 * b);
    }
    // respiration de caméra (très légère, façon prise de vue)
    if (!still) { s.yaw += 0.35 * noise1(t * 0.31, 1); s.pitch += 0.25 * noise1(t * 0.27, 2); s.roll += 0.18 * noise1(t * 0.23, 3); }
    return s;
  }

  // ------------------------------------------------------------------ dessin du sol et des lumières
  const DAY = t => E.inOutCubic(seg(t, T.day - 0.05, T.day + 0.25)) * (1 - E.inOutCubic(seg(t, T.dusk, T.dusk + 1.6)));
  const DIM = t => (t < T.day ? 0 : 0.2 * E.inOutCubic(seg(t, T.dusk, T.dusk + 1.6)) + 0.3 * E.inOutCubic(seg(t, T.end, T.final)));
  function floor(t, day) {
    const g = bg.createLinearGradient(0, 0, 0, VH);
    const top = day > 0.5 ? [lerp(10, 244, day), lerp(36, 248, day), lerp(66, 253, day)] : [lerp(4, 244, day), lerp(20, 248, day), lerp(40, 253, day)];
    const bot = [lerp(2, 230, day), lerp(12, 239, day), lerp(28, 249, day)];
    g.addColorStop(0, `rgb(${top.map(Math.round)})`); g.addColorStop(1, `rgb(${bot.map(Math.round)})`);
    bg.globalAlpha = 1; bg.fillStyle = g; bg.fillRect(0, 0, VW, VH);
    // halo d'horizon (nuit)
    if (day < 0.95) {
      const hz = project([cam.C[0], 0, cam.C[2] - 60000]);
      const y = hz ? hz[1] : -400;
      const rg = bg.createRadialGradient(CX, y, 0, CX, y, 1400);
      rg.addColorStop(0, `rgba(5,218,240,${(0.22 * (1 - day)).toFixed(3)})`); rg.addColorStop(0.4, `rgba(0,143,241,${(0.08 * (1 - day)).toFixed(3)})`); rg.addColorStop(1, "rgba(0,0,0,0)");
      bg.fillStyle = rg; bg.fillRect(0, 0, VW, VH);
    }
    // grille du sol (s'efface au loin)
    const step = 400, N = 26, col = day > 0.5 ? "0,110,220" : "5,218,240";
    const base = lerp(0.16, 0.085, day);
    bg.lineWidth = 1.4; bg.shadowBlur = 0;
    const cx0 = Math.round(cam.C[0] / step) * step, cz0 = Math.round(cam.C[2] / step) * step;
    for (let dir = 0; dir < 2; dir++) for (let i = -N; i <= N; i++) {
      for (let j = -N; j < N; j += 2) {
        const a = dir ? [cx0 + i * step, 0, cz0 + j * step] : [cx0 + j * step, 0, cz0 + i * step];
        const b = dir ? [cx0 + i * step, 0, cz0 + (j + 2) * step] : [cx0 + (j + 2) * step, 0, cz0 + i * step];
        const mid = [(a[0] + b[0]) / 2, 0, (a[2] + b[2]) / 2];
        const dd = Math.hypot(mid[0] - cam.C[0], mid[2] - cam.C[2], cam.C[1]);
        const al = base * clamp(1 - dd / 13000);
        if (al < 0.004) continue;
        line3(bg, a, b, { color: `rgba(${col},1)`, width: 1.4, alpha: al });
      }
    }
    bg.globalAlpha = 1;
    // ombres portées des tuiles (jour)
    if (day > 0.05) for (const id of Object.keys(TILE)) {
      const o = TILE[id];
      if (o.__alpha < 0.02 || !o.__vis) continue;
      const pts = [[30, 50], [1470, 50], [1470, o.h + 60], [30, o.h + 60]].map(([u, v]) => o.world(u, v));
      poly3(bg, pts, { fill: "rgba(8,38,75,1)", alpha: 0.16 * day * o.__alpha, filter: "blur(26px)" });
    }
  }

  // particules (poussière de lumière) : positions fixes autour du trajet, déterministes
  const DUST = Array.from({ length: 260 }, (_, i) => [lerp(-3200, 3200, hash(i * 1.7)), lerp(-1600, -60, hash(i * 2.3)), lerp(-4200, 4200, hash(i * 3.1)), hash(i * 4.9)]);
  function particles(t, alpha) {
    if (alpha < 0.01) return;
    fx.globalCompositeOperation = "lighter";
    for (const [x, y, z, r] of DUST) {
      const P = [x + 40 * noise1(t * 0.2 + r * 10, 4), y + 30 * noise1(t * 0.17 + r * 7, 5), z];
      dot3(fx, P, 5 + 9 * r, "rgba(140,235,255,1)", alpha * (0.25 + 0.6 * r) * (0.6 + 0.4 * Math.sin(t * 1.3 + r * 20)));
    }
    fx.globalCompositeOperation = "source-over";
  }
  // anneau de lumière (point de convergence)
  function ring(t, P, radius, alpha, spin = 0) {
    if (alpha < 0.01) return;
    fx.globalCompositeOperation = "lighter";
    const pts = 140;
    const ptsAt = (rad, a0 = 0, a1 = Math.PI * 2, n = pts) => Array.from({ length: n + 1 }, (_, i) => {
      const a = a0 + (a1 - a0) * i / n;
      return V3.add(P, V3.add(V3.mul(cam.r, Math.cos(a) * rad), V3.mul(cam.d, Math.sin(a) * rad)));
    });
    const stroke = (arr, color, width, al, glow) => {
      const ps = arr.map(p => project(p, 20)).filter(Boolean);
      if (ps.length < 2) return;
      fx.globalAlpha = al; fx.strokeStyle = color; fx.lineWidth = width; fx.shadowColor = color; fx.shadowBlur = glow;
      fx.beginPath(); ps.forEach((p, i) => (i ? fx.lineTo(p[0], p[1]) : fx.moveTo(p[0], p[1]))); fx.stroke();
    };
    stroke(ptsAt(radius), "rgba(5,218,240,1)", 6, alpha, 40);
    stroke(ptsAt(radius * 1.04), "rgba(0,143,241,1)", 2, alpha * 0.7, 20);
    for (let k = 0; k < 4; k++) {                          // arcs qui tournent
      const a0 = spin * (k % 2 ? -1 : 1) + k * 1.6;
      stroke(ptsAt(radius * (0.86 + 0.06 * k), a0, a0 + 1.1 + 0.3 * k, 40), "rgba(190,250,255,1)", 3, alpha * 0.8, 24);
    }
    fx.shadowBlur = 0; fx.globalCompositeOperation = "source-over";
  }
  // fil de lumière (courbe 3D) entre deux points, dessiné jusqu'à p
  function thread(A, B, lift, p, alpha, color = "rgba(5,218,240,1)", width = 4) {
    if (p <= 0 || alpha < 0.01) return;
    const n = 40, pts = [];
    for (let i = 0; i <= n * p; i++) {
      const u = i / n;
      const P = [lerp(A[0], B[0], u), lerp(A[1], B[1], u) - lift * Math.sin(Math.PI * u), lerp(A[2], B[2], u)];
      const pr = project(P, 20); if (pr) pts.push(pr);
    }
    if (pts.length < 2) return;
    fx.globalCompositeOperation = "lighter";
    fx.globalAlpha = alpha; fx.strokeStyle = color; fx.lineWidth = width; fx.shadowColor = color; fx.shadowBlur = 22;
    fx.beginPath(); pts.forEach((q2, i) => (i ? fx.lineTo(q2[0], q2[1]) : fx.moveTo(q2[0], q2[1]))); fx.stroke();
    const e = pts[pts.length - 1];
    fx.globalAlpha = alpha; fx.drawImage(sprite("rgba(200,250,255,1)"), e[0] - 26, e[1] - 26, 52, 52);
    fx.shadowBlur = 0; fx.globalCompositeOperation = "source-over";
  }
  // contour lumineux d'une tuile
  function tileGlow(id, a, color = "5,218,240") {
    if (a < 0.01) return;
    const o = TILE[id];
    fx.globalCompositeOperation = "lighter";
    poly3(fx, o.corners(), { stroke: `rgba(${color},1)`, width: 5, alpha: a, glow: 30 });
    fx.globalCompositeOperation = "source-over";
  }
  // balayage lumineux d'un rectangle (page qui « s'allume »)
  function sweep(id, p, a = 1) {
    if (p <= 0 || p >= 1) return;
    const o = TILE[id], v = lerp(-60, o.h + 60, p);
    fx.globalCompositeOperation = "lighter";
    line3(fx, o.world(0, v), o.world(1440, v), { color: "rgba(5,218,240,1)", width: 6, alpha: a * Math.sin(Math.PI * p), glow: 40 });
    fx.globalCompositeOperation = "source-over";
  }

  // ------------------------------------------------------------------ mots clés : apparition mot à mot
  function kwShow(o, t, times, tEnd, place) {
    const vis = t > times[0] - 0.3 && t < tEnd + 0.4;
    if (!vis) { opa(o.el, 0); return; }
    opa(o.el, 1 - seg(t, tEnd, tEnd + 0.35));
    o.place(place);
    o.words.forEach((w, i) => {
      const p = E.outCubic(seg(t, times[Math.min(i, times.length - 1)] - 0.08, times[Math.min(i, times.length - 1)] + 0.32));
      const s = `translateY(${(26 * (1 - p)).toFixed(1)}px)`;
      if (w.__t !== s) { w.style.transform = s; w.__t = s; }
      w.style.opacity = p.toFixed(3); blur(w, 10 * (1 - p));
    });
  }
  // point du monde au bord d'une découpe levée (pour y accrocher un mot clé)
  const besideClip = (name, side = "right", gap = 70, lift = 150) => {
    const o = CL[name], r = o.rect, id = o.page;
    const u = side === "right" ? r.x + r.w + gap : side === "left" ? r.x - gap : r.x + r.w / 2;
    const v = side === "below" ? r.y + r.h + gap : side === "above" ? r.y - gap : r.y + r.h / 2;
    const P = TILE[id].world(u, v);
    return { x: P[0], y: -lift - 20, z: P[2], flat: true, ax: side === "left" ? 1 : side === "right" ? 0 : 0.5 };
  };

  // ------------------------------------------------------------------ curseur
  let lastPt = null;
  function cursorAt(t) {
    let k = -1;
    for (let i = 0; i < CLICKS.length; i++) if (t >= CLICKS[i][2] - 0.25 && t <= CLICKS[i][3] + 0.25 && (k < 0 || CLICKS[i][0] <= t + 0.75)) k = i;
    if (k < 0) { opa(cur, 0); opa(rip, 0); return; }
    const [tc, get, v0, v1] = CLICKS[k];
    const p1 = get();
    if (!p1) { opa(cur, 0); opa(rip, 0); return; }
    let p0 = [p1[0] + 170, p1[1] + 130];
    if (k > 0 && CLICKS[k - 1][3] >= v0 - 0.3 && CLICKS[k - 1][0] < tc) { const pp = CLICKS[k - 1][1](); if (pp) p0 = pp; }
    const p = E.inOutCubic(seg(t, Math.max(v0, tc - 0.7), tc - 0.08));
    const press2 = Math.max(0, 1 - Math.abs(t - tc) / 0.1);
    const x = lerp(p0[0], p1[0], p), y = lerp(p0[1], p1[1], p);
    cur.style.transform = `translate(${(x - 3).toFixed(1)}px,${(y - 2).toFixed(1)}px) scale(${(1 - 0.14 * press2).toFixed(3)})`;
    opa(cur, Math.min(seg(t, v0 - 0.25, v0), 1 - seg(t, v1, v1 + 0.25)));
    const r = seg(t, tc, tc + 0.5);
    rip.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) scale(${(0.3 + 0.9 * E.outCubic(r)).toFixed(3)})`;
    opa(rip, r > 0 && r < 1 ? (1 - r) * 0.9 : 0);
  }

  // ------------------------------------------------------------------ levée d'un composant
  function liftClip(name, t) {
    const o = CL[name], [t0, t1, L, sc] = LIFT[name], id = o.page;
    const up = E.outBack(seg(t, t0, t0 + 0.55)), down = E.inOutCubic(seg(t, t1 - 0.4, t1));
    const a = clamp(up) * (1 - down);
    const on = t > t0 - 0.05 && t < t1 + 0.05;
    opa(o.el, on ? clamp(seg(t, t0 - 0.05, t0 + 0.08)) * (1 - seg(t, t1 - 0.06, t1)) : 0);
    opa(halos[name].el, on ? 0.55 * a : 0); opa(shadows[name].el, on ? 0.5 * a : 0);
    if (!on) return 0;
    const r = o.rect;
    const P = TILE[id].world(r.x + r.w / 2, r.y + r.h / 2);
    const lift = (up * (1 - down)) * L;
    o.place({ x: P[0], y: -lift, z: P[2], flat: true, s: 1 + 0.03 * a * sc });
    const hh = halos[name]; hh.w = r.w + 70; hh.h = r.h + 70; hh.el.style.width = hh.w + "px"; hh.el.style.height = hh.h + "px";
    hh.place({ x: P[0], y: -lift + 8, z: P[2], flat: true, rz: (t * 40) % 360 * 0 });
    const sh = shadows[name]; sh.w = r.w; sh.h = r.h; sh.el.style.width = sh.w + "px"; sh.el.style.height = sh.h + "px";
    sh.place({ x: P[0] + lift * 0.18, y: -2, z: P[2] + lift * 0.3, flat: true });
    return a;
  }

  // ------------------------------------------------------------------ image à l'instant t
  window.renderAt = function (t) {
    applyStates(t);
    const s = cameraAt(t);
    solveCamera(s);
    viewport.style.perspective = s.F.toFixed(1) + "px";
    const css = M4.css(cam.view);
    if (world.__css !== css) { world.style.transform = css; world.__css = css; }
    const day = DAY(t);
    const nightAct = t < T.day;

    // ---------------- tuiles du plan : elles s'allument une à une à l'arrivée au-dessus du monde
    const center = [0, 0, 0];
    for (const id of Object.keys(TILE)) {
      const o = TILE[id], [x, , z] = pos(id);
      const delay = Math.hypot(x, z) / 5200;
      const a = nightAct ? 0 : E.outCubic(seg(t, T.day + 0.05 + delay, T.day + 0.65 + delay));
      o.__alpha = a; o.__vis = a > 0.01 && o.visible(200);
      opa(o.el, o.__vis ? a : 0);
      if (o.__vis) o.place({ x, y: 40 * (1 - a), z, flat: true });
      opa(o.dim, DIM(t));
      const lb = labels[id];
      const la = a * clamp((cam.C[1] < -2600 ? 1 : 0) + seg(-cam.C[1], 2600, 3600)) * (1 - seg(t, T.end + 0.6, T.final));
      opa(lb.el, la);
      if (la > 0.01) lb.place({ x: x - 360, y: -260, z: z - 620, bill: true, s: 2.3 });
    }

    // ---------------- composants levés
    for (const name of Object.keys(CL)) if (name !== "agent") liftClip(name, t);

    // ---------------- calques 2D
    bg.setTransform(1, 0, 0, 1, 0, 0); fx.setTransform(1, 0, 0, 1, 0, 0);
    fx.clearRect(0, 0, VW, VH);
    floor(t, day);
    particles(t, (1 - day) * (nightAct ? 1 : 0.6) + 0.12 * day * (1 - seg(t, T.day, T.day + 2)));

    // ---------------- I. nuit
    // trait de lumière anamorphique sur l'horizon (dès la première image), qui s'efface quand les démarches arrivent
    const st0 = (1 - seg(t, T.boulot, T.ques)) * (nightAct ? 1 : 0);
    if (st0 > 0.01) {
      const hz = project([cam.C[0], 0, cam.C[2] - 60000]);
      const y = hz ? clamp(hz[1], 200, 880) : 520, x = CX + 260 * Math.sin(t * 0.35);
      fx.globalCompositeOperation = "lighter";
      const g2 = fx.createLinearGradient(x - 980, 0, x + 980, 0);
      g2.addColorStop(0, "rgba(5,218,240,0)"); g2.addColorStop(0.5, `rgba(150,240,255,${(0.75 * st0).toFixed(3)})`); g2.addColorStop(1, "rgba(5,218,240,0)");
      fx.globalAlpha = 1; fx.fillStyle = g2; fx.fillRect(x - 980, y - 2.5, 1960, 5);
      fx.drawImage(sprite("rgba(170,245,255,1)", 128), x - 160, y - 160, 320, 320);
      const g3 = fx.createRadialGradient(x, y, 0, x, y, 520); g3.addColorStop(0, `rgba(0,143,241,${(0.25 * st0).toFixed(3)})`); g3.addColorStop(1, "rgba(0,143,241,0)");
      fx.fillStyle = g3; fx.fillRect(x - 520, y - 520, 1040, 1040);
      fx.globalCompositeOperation = "source-over";
    }
    const nightProps = t < T.day + 0.1;
    TASKS.forEach((tk, i) => {
      const o = tasks[i], t0 = T[tk[3]] - 0.15;
      const pull = E.inOutCubic(seg(t, T.meme - 0.5, T.logo - 0.55));
      const a = nightProps ? E.outCubic(seg(t, t0, t0 + 0.6)) * (1 - E.inCubic(seg(pull, 0.6, 1))) : 0;
      opa(o.el, a);
      if (a <= 0.01) return;
      const Pp = mix3(tk[4], P0, E.inCubic(pull));
      o.place({ x: Pp[0], y: Pp[1], z: Pp[2], ry: tk[5] * (1 - pull), s: (0.9 + 0.1 * E.outBack(seg(t, t0, t0 + 0.7))) * (1 - 0.7 * pull) });
      blur(o.el, 14 * (1 - E.outCubic(seg(t, t0, t0 + 0.5))) + 6 * pull);
      if (pull > 0) thread(tk[4], P0, 220 * (i % 2 ? 1 : -1), clamp(pull * 1.6), 0.9 * (1 - seg(pull, 0.75, 1)));
    });
    // l'heure s'emballe : 08:00 -> 19:30 sur « un temps fou »
    const dg = E.inOutCubic(seg(t, T.boulot - 0.1, T.fou + 0.35));
    const da = nightProps ? E.outCubic(seg(t, T.boulot - 0.3, T.boulot + 0.2)) * (1 - E.inCubic(seg(t, T.ques - 0.45, T.ques + 0.1))) : 0;
    opa(digits.el, da);
    if (da > 0.01) {
      setText(digits.el, hhmm(480 + 690 * dg));
      digits.place({ x: 0, y: -520, z: -1300, bill: true, s: 1.0 + 0.08 * dg });
      blur(digits.el, 3 * (1 - da));
      // anneaux de graduations qui défilent (tunnel du temps)
      fx.globalCompositeOperation = "lighter";
      for (let r = 0; r < 5; r++) {
        const zc = -400 - r * 650, rad = 980;
        for (let k2 = 0; k2 < 60; k2++) {
          const ang = k2 / 60 * Math.PI * 2 + dg * 6 * (r % 2 ? -1 : 1);
          const len = k2 % 5 ? 30 : 80;
          const A = [Math.cos(ang) * rad, -520 + Math.sin(ang) * rad, zc], B = [Math.cos(ang) * (rad - len), -520 + Math.sin(ang) * (rad - len), zc];
          line3(fx, A, B, { color: "rgba(5,218,240,1)", width: k2 % 5 ? 2 : 4, alpha: da * 0.55 });
        }
      }
      fx.globalCompositeOperation = "source-over";
    }
    // « Et si tout se faisait au même endroit ? »
    const qTxt = "Et si tout se faisait au même endroit ?";
    const qa2 = nightProps ? seg(t, T.ques - 0.1, T.ques + 0.15) * (1 - E.inOutCubic(seg(t, T.endroit + 0.8, T.endroit + 1.5))) : 0;
    opa(quest.el, qa2);
    if (qa2 > 0.01) {
      const words = qTxt.split(" "), wts = SC.hook.segs[1].words.map(w => w[1]);
      setHTML(quest.el, words.map((w, i) => {
        const p = E.outCubic(seg(t, (wts[i] || T.endroit) - 0.06, (wts[i] || T.endroit) + 0.26));
        const inner = i >= 5 && i <= 6 ? `<b>${w}</b>` : w;
        return `<span style="opacity:${p.toFixed(2)};filter:blur(${(8 * (1 - p)).toFixed(1)}px);transform:translateY(${(20 * (1 - p)).toFixed(0)}px)">${inner}</span>`;
      }).join(""));
      quest.place({ x: 0, y: -360, z: -1750, bill: true, s: 1.0 });
    }
    // anneau, puis logo
    const ringA = nightProps ? E.outCubic(seg(t, T.meme, T.endroit + 0.6)) * (1 - seg(t, T.day - 0.25, T.day)) : 0;
    const flare = Math.exp(-Math.pow((t - T.logo) / 0.18, 2));
    ring(t, P0, 520 + 140 * E.outExpo(seg(t, T.logo, T.logo + 0.6)), ringA * (0.85 + 0.6 * flare), t * 1.4);
    if (ringA > 0.01) {                                   // particules aspirées par l'anneau
      fx.globalCompositeOperation = "lighter";
      for (let i = 0; i < 90; i++) {
        const ph = (t * (0.25 + 0.2 * hash(i)) + hash(i * 3)) % 1, ang = hash(i * 7) * 6.283 + t * (0.6 + hash(i));
        const rad = lerp(1300, 540, ph);
        const P = V3.add(P0, V3.add(V3.mul(cam.r, Math.cos(ang) * rad), V3.mul(cam.d, Math.sin(ang) * rad)));
        dot3(fx, P, 7, "rgba(160,240,255,1)", ringA * 0.7 * Math.sin(Math.PI * ph));
      }
      fx.globalCompositeOperation = "source-over";
    }
    const la = nightProps ? E.outCubic(seg(t, T.logo - 0.06, T.logo + 0.4)) : 0;
    const finalA = E.outCubic(seg(t, T.final - 0.08, T.final + 0.5));
    if (la > 0.01 || finalA > 0.01) {
      const fin = finalA > 0.01;
      const PL = fin ? [0, -1050, -600] : P0;
      const sc = fin ? 0.95 + 0.05 * E.outCubic(seg(t, T.final, T.final + 3)) : 0.82 + 0.18 * E.outExpo(seg(t, T.logo - 0.06, T.logo + 0.7));
      logo.place({ x: PL[0], y: PL[1] - 30, z: PL[2], bill: true, s: sc });
      opa(logo.el, fin ? finalA : la);
      blur(logo.el, fin ? 10 * (1 - finalA) : 10 * (1 - la));
      const tg = fin ? T.finTag : T.tag;
      tagline.place({ x: PL[0], y: PL[1] + 250, z: PL[2], bill: true, s: 1 });
      opa(tagline.el, (fin ? finalA : la) * seg(t, tg - 0.3, tg));
      qa(tagEl, "span").forEach((sp, i) => {
        const p = E.outCubic(seg(t, tg - 0.25 + i * 0.022, tg + 0.2 + i * 0.022));
        sp.style.opacity = p.toFixed(2); sp.style.transform = `translateY(${(-30 * (1 - p)).toFixed(1)}px)`; sp.style.filter = `blur(${(6 * (1 - p)).toFixed(1)}px)`;
      });
      opa(subline.el, fin ? seg(t, T.finTag + 0.5, T.finTag + 1.3) : 0);
      if (fin) subline.place({ x: PL[0], y: PL[1] + 360, z: PL[2], bill: true, s: 1 });
      if (fin) ring(t, PL, 700 + 60 * E.outExpo(seg(t, T.final, T.final + 0.8)), finalA * 0.55 * (1 - 0.6 * seg(t, T.final + 1, T.final + 4)), t * 0.8);
    } else { opa(logo.el, 0); opa(tagline.el, 0); opa(subline.el, 0); }

    // ---------------- II. jour : arrivée au-dessus du plan
    for (const id of Object.keys(TILE)) {
      const [x, , z] = pos(id), delay = Math.hypot(x, z) / 5200;
      sweep(id, seg(t, T.day + 0.05 + delay, T.day + 0.9 + delay), 0.8);
    }
    // chemins lumineux pendant les vols (d'une page à l'autre, sur le sol)
    for (const [t1, , , arcK] of KEYS) {
      if (!arcK) continue;
      const i = KEYS.findIndex(k2 => k2[0] === t1), t0 = KEYS[i - 1][0];
      if (t < t0 - 0.1 || t > t1 + 0.6) continue;
      const A = [KEYS[i - 1][1].tx, 0, KEYS[i - 1][1].tz], B = [KEYS[i][1].tx, 0, KEYS[i][1].tz];
      thread(A, B, 0, E.inOutCubic(seg(t, t0, t1)), 0.75 * (1 - seg(t, t1, t1 + 0.6)) * day, "rgba(0,143,241,1)", 6);
    }

    // pointage : mots clés et horloge
    kwShow(K.clic, t, [T.in - 0.1, T.in + 0.1], T.pause - 0.3, besideClip("punch", "below", 70));
    kwShow(K.minute, t, [W("pointage", 0, "à", 0), W("pointage", 0, "la", 1), T.minute, T.minute + 0.2], T.cg - 1.3, besideClip("today", "left", 60));
    // congés : la règle d'ancienneté
    const ra = bump(t, T.rights - 0.2, T.rights + 0.3, T.abs - 1.4, T.abs - 1.0);
    opa(rule.el, ra);
    if (ra > 0.01) {
      const P = TILE.leaves.world(900, 430);
      rule.place({ x: P[0], y: -170, z: P[2], flat: true, s: 1 });
      const f = E.inOutCubic(seg(t, T.rights + 0.1, T.seniority + 0.15));
      ruleFill.style.width = (100 * f).toFixed(1) + "%"; ruleKnob.style.left = (100 * f).toFixed(1) + "%";
      setHTML(ruleKnob, ic(t >= T.seniority + 0.1 ? "unlock" : "lock"));
      ruleKnob.style.color = t >= T.seniority + 0.1 ? "#129266" : "#008ff1";
    }
    // absences : le justificatif arrive en volant dans la zone de dépôt
    const pa = bump(t, T.proof - 0.25, T.proof + 0.05, T.fileIn, T.fileIn + 0.12);
    opa(pdf.el, pa);
    if (pa > 0.01) {
      const up = fRect("absences", "abs-upload"), P1 = TILE.absences.world(up.x + up.w / 2, up.y + up.h / 2), P2 = TILE.absences.world(up.x + up.w + 900, up.y - 200);
      const f = E.inOutCubic(seg(t, T.proof - 0.25, T.fileIn));
      const Pp = mix3([P2[0], -700, P2[2]], [P1[0], -130, P1[2]], f);
      pdf.place({ x: Pp[0], y: Pp[1], z: Pp[2], flat: true, rz: 14 * (1 - f), s: 1 - 0.35 * f });
    }
    // signature : imprimer, signer, scanner… sauf que non (la composition, puis ses éclats)
    const sp = bump(t, T.kImp - 0.6, T.kImp - 0.15, T.nonEnd - 0.01, T.nonEnd);
    opa(sigSet.el, sp);
    const sigM = (off = [0, 0, 0], cx = SIG_W / 2, cy = SIG_H / 2, Rt = M4.I(), bx = 0, by = 0) =>
      M4.chain(M4.T(...SIGP), SIGROT, M4.S(SIGS), M4.T(off[0] / SIGS, off[1] / SIGS, off[2] / SIGS), M4.T(cx - SIG_W / 2, cy - SIG_H / 2, 0), Rt, M4.T(-cx + bx, -cy + by, 0));
    if (sp > 0.01) {
      const rise = E.outCubic(seg(t, T.kImp - 0.6, T.kImp + 0.2));
      sigSet.setM(sigM([0, 120 * (1 - rise), -200 * (1 - rise)]));
      const out = E.outCubic(seg(t, T.kImp - 0.45, T.kImp + 0.45));
      sigPaper.style.clipPath = `inset(0 0 ${(100 * (1 - out)).toFixed(1)}% 0)`;
      sigPaper.style.transform = `translateY(${(-60 * (1 - out)).toFixed(1)}px)`;
      paperInk.style.strokeDashoffset = (1 - E.inOutSine(seg(t, T.kSig - 0.1, T.kSig + 0.6))).toFixed(3);
      const sc = seg(t, T.kScan - 0.1, T.kScan + 0.7);
      paperScan.style.top = lerp(-90, 1000, sc).toFixed(0) + "px"; paperScan.style.opacity = (sc > 0 && sc < 1 ? 1 : 0).toFixed(2);
      const wt = [T.kImp, T.kSig, T.kScan, T.kScan + 0.3, T.non, T.non + 0.14, T.nonW];
      sigWords.forEach((w, i) => {
        const p = E.outCubic(seg(t, wt[i] - 0.08, wt[i] + 0.3));
        w.style.opacity = p.toFixed(3); w.style.transform = `translateY(${(26 * (1 - p)).toFixed(1)}px)`; blur(w, 10 * (1 - p));
      });
    }
    const shatter = seg(t, T.nonEnd, T.nonEnd + 1.35);
    for (const sh of SHARDS) {
      const on = shatter > 0 && shatter < 1;
      opa(sh.o.el, on ? 1 - E.inCubic(shatter) : 0);
      if (!on) continue;
      const f = E.outCubic(shatter), dx = (sh.cx - SIG_W / 2) / (SIG_W / 2), dy = (sh.cy - SIG_H / 2) / (SIG_H / 2);
      const off = [dx * 900 * f * (0.5 + sh.r), dy * 620 * f * (0.5 + sh.r2) + 300 * f * f, 380 * f * (0.2 + sh.r)];
      const Rt = M4.chain(M4.RX(420 * f * (sh.r - 0.5)), M4.RY(480 * f * (sh.r2 - 0.5)), M4.RZ(300 * f * (sh.r - sh.r2)));
      sh.o.setM(sigM(off, sh.cx, sh.cy, Rt, sh.bx, sh.by));
      blur(sh.o.el, 3 * f);
    }
    // e-mail du code
    const ma = bump(t, T.mail - 0.2, T.mail + 0.25, T.signed - 0.2, T.signed + 0.1);
    opa(mailCard.el, ma);
    if (ma > 0.01) {
      const r = R("sign", "dialog"), P = TILE.sign.world(r.x + r.w + 470, r.y + 300);
      const f = E.outCubic(seg(t, T.mail - 0.2, T.mail + 0.45));
      mailCard.place({ x: P[0] + 600 * (1 - f), y: -260 - 120 * (1 - f), z: P[2] - 200 * (1 - f), flat: true, rz: 6 * (1 - f) });
      mailDigits.forEach((d2, i) => { const on = t >= T.tape - 0.1 + i * 0.075 && t < T.signed; d2.style.background = on ? "#008ff1" : "#eef6ff"; d2.style.color = on ? "#fff" : "#008ff1"; });
    }
    // lueur de la plume sur la signature dessinée
    const penP = penPoint(E.inOutSine(seg(t, T.draw + 0.15, T.drawEnd)));
    if (penP && t < T.drawEnd) {
      const cv = docOf("sign").querySelector('[data-film="sign-canvas"]');
      if (cv) {
        const r = cv.getBoundingClientRect(), o = CL.dialog;
        const Pw = o.world(r.left + penP[0] * r.width - o.rect.x, r.top + penP[1] * r.height - o.rect.y);
        fx.globalCompositeOperation = "lighter"; dot3(fx, Pw, 34, "rgba(5,218,240,1)", 0.9); fx.globalCompositeOperation = "source-over";
      }
    }
    // signé : balayage de lumière sur l'aperçu du document
    {
      const r = elRect("sign", ".mw-preview-stage"), p = seg(t, T.signed + 0.5, T.signed + 1.3);
      if (p > 0 && p < 1) {
        const v = lerp(r.y - 40, r.y + r.h + 40, p);
        fx.globalCompositeOperation = "lighter";
        line3(fx, TILE.sign.world(r.x, v), TILE.sign.world(r.x + r.w, v), { color: "rgba(5,218,240,1)", width: 8, alpha: Math.sin(Math.PI * p), glow: 40 });
        fx.globalCompositeOperation = "source-over";
      }
    }
    // demandes, contenu, support : mots clés
    kwShow(K.deux, t, [W("demandes", 0, "en"), W("demandes", 0, "deux"), T.clics], T.process - 0.35, besideClip("reqForm", "right", 110, 120));
    kwShow(K.lu, t, [W("contenu", 0, "en", 0), W("contenu", 0, "un", 0), T.lu], T.coll - 1.3, besideClip("note", "left", 60, 130));
    // ---------------- agent : orbe, panneau, faisceaux vers les pages
    const agA = bump(t, T.q - 0.4, T.q + 0.3, T.end + 0.3, T.end + 0.9);
    const AGP = [0, -1250, 260], ORB = [AGP[0] - 560, AGP[1] - 120, AGP[2] + 10];
    opa(orb.el, agA);
    if (agA > 0.01) {
      const br = 1 + 0.05 * Math.sin(t * 5);
      orb.place({ x: ORB[0], y: ORB[1], z: ORB[2], bill: true, rz: 8 * Math.sin(t * 0.9), s: (0.5 + 0.5 * E.outBack(seg(t, T.q - 0.4, T.q + 0.35))) * br });
      ring(t, ORB, 230, agA * 0.8, t * 2.2);
      fx.globalCompositeOperation = "lighter";
      for (let i = 0; i < 70; i++) {
        const ang = hash(i * 3.3) * 6.283 + t * (0.8 + hash(i)), rad = 260 + 120 * hash(i * 5.1);
        const P = V3.add(ORB, V3.add(V3.mul(cam.r, Math.cos(ang) * rad), V3.mul(cam.d, Math.sin(ang) * rad * 0.9)));
        dot3(fx, P, 7, "rgba(160,240,255,1)", agA * 0.6);
      }
      fx.globalCompositeOperation = "source-over";
    }
    const pnl = CL.agent, pa2 = bump(t, T.launch - 0.1, T.launch + 0.45, T.end + 0.2, T.end + 0.8);
    opa(pnl.el, pa2); opa(halos.agent.el, 0.5 * pa2); opa(shadows.agent.el, 0);
    if (pa2 > 0.01) {
      const f = E.outBack(seg(t, T.launch - 0.1, T.launch + 0.6)), g = E.outCubic(seg(t, T.launch - 0.1, T.launch + 0.5));
      const Pp = mix3(ORB, [AGP[0] + 60, AGP[1], AGP[2]], g);
      pnl.place({ x: Pp[0], y: Pp[1], z: Pp[2], bill: true, s: 0.2 + 0.8 * f });
      const hh = halos.agent; hh.w = pnl.w + 90; hh.h = pnl.h + 90; hh.el.style.width = hh.w + "px"; hh.el.style.height = hh.h + "px";
      hh.place({ x: Pp[0] - cam.b[0] * 20, y: Pp[1] - cam.b[1] * 20, z: Pp[2] - cam.b[2] * 20, bill: true, s: 0.2 + 0.8 * f });
    }
    const beams = [["leaves", T.chips[0]], ["requests", T.chips[1]], ["support", T.chips[2]]];
    beams.forEach(([id, tb]) => {
      const p = E.inOutCubic(seg(t, tb - 0.1, tb + 0.45)), a = bump(t, tb - 0.1, tb + 0.1, T.answer, T.answer + 0.5);
      thread([AGP[0] + 60, AGP[1] + 300, AGP[2]], pos(id), -300, p, a, "rgba(5,218,240,1)", 5);
      tileGlow(id, a * seg(t, tb + 0.3, tb + 0.5) * (0.6 + 0.4 * Math.sin(t * 8)));
    });
    // la demande confirmée descend vers « Mes demandes RH »
    const sc2 = bump(t, T.okAgent + 0.05, T.okAgent + 0.25, T.agentSent - 0.1, T.agentSent + 0.2);
    opa(sentCard.el, sc2);
    if (sc2 > 0.01) {
      const f = E.inOutCubic(seg(t, T.okAgent + 0.05, T.agentSent));
      const A = [AGP[0] + 60, AGP[1] + 200, AGP[2]], B = V3.add(pos("requests"), [0, -120, 0]);
      const Pp = [lerp(A[0], B[0], f), lerp(A[1], B[1], f) - 500 * Math.sin(Math.PI * f), lerp(A[2], B[2], f)];
      sentCard.place({ x: Pp[0], y: Pp[1], z: Pp[2], bill: true, s: 1.4 - 0.4 * f });
      thread(A, Pp, 0, 1, 0.6 * sc2, "rgba(5,218,240,1)", 4);
    }
    tileGlow("requests", pulse(t, T.agentSent - 0.1, 1.2));

    // ---------------- III. fin : le plan s'illumine
    const fa = seg(t, T.end + 0.2, T.final);
    if (fa > 0) for (const id of Object.keys(TILE)) tileGlow(id, 0.75 * fa * (0.7 + 0.3 * Math.sin(t * 2 + MAP[id][0] * 2 + MAP[id][1])));
    particles(t, 0.8 * seg(t, T.end, T.final + 1));

    // ---------------- HUD
    cursorAt(t);
    CHECKS.forEach(c => {
      const p = E.outBack(seg(t, c.t0, c.t0 + 0.45)), o = seg(t, c.t0, c.t0 + 0.2) * (1 - seg(t, c.t1 - 0.25, c.t1));
      opa(c.el, o);
      if (o > 0.002) c.el.style.transform = `translate(${(84 - 40 * (1 - clamp(p))).toFixed(1)}px, 80px)`;
    });
    // étalonnage : bandes cinéma (nuit), éclairs, vignette, grain
    const bars = 1 - E.inOutCubic(seg(t, T.logo + 0.3, T.logo + 1.3));
    barTop.style.transform = `translateY(${(-140 * (1 - bars)).toFixed(1)}px)`; barBot.style.transform = `translateY(${(140 * (1 - bars)).toFixed(1)}px)`;
    const fl = Math.max(0.55 * Math.exp(-Math.pow((t - T.logo) / 0.14, 2)), Math.exp(-Math.pow((t - T.day + 0.02) / 0.16, 2)),
                        0.45 * Math.exp(-Math.pow((t - T.nonEnd - 0.05) / 0.12, 2)), 0.22 * Math.exp(-Math.pow((t - T.final) / 0.16, 2)));
    opa(flash, fl);
    opa(vign, 0.35 + 0.65 * (1 - day));
    const fr = Math.round(t * 30);
    grain.style.transform = `translate(${(hash(fr) * 64 - 32).toFixed(0)}px,${(hash(fr + 7) * 64 - 32).toFixed(0)}px)`;
    opa(grain, 0.55 - 0.25 * day);
  };
})();
