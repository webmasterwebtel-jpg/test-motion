/* MyWebtel — film de présentation V3 (1920×1080, 30 i/s), sur la vraie interface.
 * Toute l'image est une fonction du temps : renderAt(t) pose chaque élément. Aucune animation automatique (les
 * transitions CSS des pages sont coupées par prep_ui.py), donc le rendu image par image est exact et reproductible.
 *
 * La page de la fenêtre est la vraie interface MyWebtel : chaque écran est une iframe dont le HTML vient de l'aperçu
 * PHP réel (build/mywebtel/ui.json, préparé par prep_ui.py et injecté par render.js dans window.UI). Le film ne fait
 * que remplir les champs, cocher, changer les états et les libellés réels, comme le ferait un utilisateur.
 * Les instants viennent de window.TL (timeline.json, mots datés) : chaque geste tombe sur le mot prononcé.
 */
(function () {
  "use strict";
  const TL = window.TL, UI = window.UI || {};
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
  function spring(t, z = 0.72, f = 2.6) {
    if (t <= 0) return 0;
    const w = 2 * Math.PI * f;
    if (z < 1) { const wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + z * w / wd * Math.sin(wd * t)); }
    return 1 - Math.exp(-w * t) * (1 + w * t);
  }
  const SC = {}; TL.scenes.forEach(s => { SC[s.id] = s; });
  const S0 = id => SC[id].start, S1 = id => SC[id].end;
  const segT = (id, i) => SC[id].segs[i].start, segE = (id, i) => SC[id].segs[i].end;
  function W(id, i, word, n = 0) {                    // instant où un mot est prononcé (alignement de vo.py)
    const k = SC[id].segs[i].words.filter(w => w[0].toLowerCase() === word.toLowerCase());
    if (!k[n]) throw new Error("mot absent : " + id + "/" + i + "/" + word);
    return k[n][1];
  }
  const typed = (txt, t, t0, t1) => txt.slice(0, Math.round(txt.length * seg(t, t0, t1)));
  const ICON = {
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    chat: '<path d="M3 4h18v13H8l-5 4zM7 8h10m-10 5h6"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    file: '<path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8m-8 4h8"/>',
    lock: '<rect x="5" y="11" width="14" height="10" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18m-13 5 3 3 5-5"/>',
  };
  const ic = n => `<svg class="i" viewBox="0 0 24 24">${ICON[n]}</svg>`;
  function h(html) { const d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstElementChild; }
  function add(parent, html) { const e = h(html); parent.appendChild(e); return e; }
  const q = (root, sel) => root.querySelector(sel);
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
  const setText = (el, s) => { if (el && el.textContent !== s) el.textContent = s; };
  const BAR = TL.beat * 4, onBar = x => Math.round(x / BAR) * BAR;

  // ------------------------------------------------------------------ décor
  const bg = add(stage, `<div id="bg"></div>`);
  const glowA = add(bg, `<div class="glow" style="width:1100px;height:800px;left:-200px;top:-260px;background:rgba(0,143,241,.16)"></div>`);
  const glowB = add(bg, `<div class="glow" style="width:1000px;height:760px;right:-220px;bottom:-300px;background:rgba(5,218,240,.10)"></div>`);
  const bgNight = add(stage, `<div id="bgNight"></div>`);
  const view = add(stage, `<div id="view"></div>`);
  const world = add(view, `<div id="world"></div>`);
  const fx = add(stage, `<div class="layer" id="fx"></div>`);

  // ------------------------------------------------------------------ fenêtre : la vraie interface, un écran par iframe
  const WX = 240, WY = 64, CH = 52, PH = 900;
  const win = add(world, `<div class="win"><div class="chrome"><i class="d"></i><i class="d"></i><i class="d"></i>
    <div class="url">${ic("lock")}<span class="u">mywebtel.com/dashboard</span></div></div><div class="probe"></div></div>`);
  const urlEl = q(win, ".u"), probe = q(win, ".probe");
  const PAGES = [["dashboard", "/dashboard"], ["attendance", "/attendance"], ["leaves", "/leaves"], ["absences", "/absences"], ["documents", "/documents"],
                 ["requests", "/hr-requests"], ["content", "/content"], ["mail", "/mail"], ["support", "/support"]];
  const FR = {}, loads = [];
  PAGES.forEach(([k]) => {
    const f = document.createElement("iframe");
    f.className = "pg"; f.setAttribute("scrolling", "no");
    loads.push(new Promise(res => f.addEventListener("load", res, { once: true })));
    f.srcdoc = UI[k] || `<body style="font:30px sans-serif;padding:60px">écran « ${k} » absent : lancer prep_ui.py</body>`;
    win.appendChild(f); FR[k] = f;
  });
  const D = k => FR[k].contentDocument;
  const F = (k, name) => D(k).querySelector(`[data-film="${name}"]`);
  const $ = (k, sel) => D(k).querySelector(sel);
  // position dans la fenêtre (repère de la caméra) et à l'écran (curseur), y compris défilement de la page
  function winPt(el) {
    if (!el) return [720, 476];
    const r = el.getBoundingClientRect();
    if (!r.width && el.__w) return el.__w;
    return (el.__w = [r.left + r.width / 2, CH + r.top + r.height / 2]);
  }
  function screenOf(el) {
    const [x, y] = winPt(el);
    probe.style.left = (x - 1) + "px"; probe.style.top = (y - 1) + "px";
    const r = probe.getBoundingClientRect();
    return [r.left + r.width / 2, r.top + r.height / 2];
  }
  // mise en valeur d'un élément de l'interface (halo cyan, couleur de la plateforme)
  function glow(el, a) {
    if (!el) return;
    el.style.boxShadow = a > 0.01 ? `0 0 0 ${(2 + 2 * a).toFixed(1)}px rgba(5,218,240,${(0.9 * a).toFixed(3)}), 0 0 ${(26 * a).toFixed(0)}px rgba(0,143,241,${(0.45 * a).toFixed(3)})` : "";
  }
  const pulse = (t, t0, d = 1.4) => Math.sin(Math.PI * seg(t, t0, t0 + d));

  // ------------------------------------------------------------------ calques de film
  const CURSOR = `<svg class="cursor" viewBox="0 0 34 44"><path d="M3 2l26 24H16l7 14-5 2-7-14-8 8z" fill="#fff" stroke="#041b34" stroke-width="2.4" stroke-linejoin="round"/></svg>`;
  const cur = add(fx, CURSOR), rip = add(fx, `<div class="ripple"></div>`);
  const clock = add(fx, `<div class="note" style="right:70px;bottom:46px;font-size:26px;gap:14px">${ic("clock")}<span style="font-weight:500;color:var(--muted)">Jeudi 15 octobre</span><b class="ct" style="font-variant-numeric:tabular-nums;font-size:30px"></b></div>`);
  const TASKS = [["clock", "Pointage", "Commencer ma journée", ["hook", 0, "Pointer"], -560, -250], ["calendar", "Mes congés", "24 jours disponibles", ["hook", 0, "congé"], 470, -290],
                 ["file", "Mes documents", "Avenant au contrat", ["hook", 0, "document"], -500, 220], ["mail", "Mail", "Réunion client de jeudi", ["hook", 0, "collègue"], 500, 235]];
  const tasks = TASKS.map(([i, a, b]) => add(fx, `<div class="task"><span class="ti">${ic(i)}</span><div>${a}<small>${b}</small></div></div>`));
  const spark = add(fx, `<div class="abs" style="left:960px;top:540px;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;background:#fff;box-shadow:0 0 40px 18px rgba(5,218,240,.8)"></div>`);
  const LOGO = "brand/webtel-logo.svg", LW = 960, LH = Math.round(LW * 1224 / 3520);
  const logo = add(fx, `<div class="abs" style="left:${960 - LW / 2}px;top:${470 - LH / 2}px;width:${LW}px;height:${LH}px">
      <img class="lm" src="${LOGO}" style="position:absolute;inset:0;width:100%;clip-path:inset(0 76% 0 0);transform-origin:13% 55%">
      <img class="lt" src="${LOGO}" style="position:absolute;inset:0;width:100%;clip-path:inset(0 0 0 24%)"></div>`);
  const lm = q(logo, ".lm"), lt = q(logo, ".lt");
  const tag = add(fx, `<div class="center tagline" style="top:${470 + LH / 2 + 56}px">MYWEBTEL · ESPACE COLLABORATEUR</div>`);
  const flash = add(fx, `<div class="layer" style="background:#fff"></div>`);

  // ------------------------------------------------------------------ chronologie (tout dérive des mots de la voix)
  // V4 : chaque écran s'ouvre quand la voix prononce son nom, chaque geste tombe sur son mot, et l'image se pose
  // après chaque résultat (respirations du texte) pour qu'on ait le temps de lire.
  const T = {};
  T.logo = onBar(W("reveal", 0, "MyWebtel") - 0.4);
  T.tag = W("reveal", 0, "espace");
  T.winIn = W("reveal", 1, "tout") - 0.4;
  T.dIntro = W("dashboard", 0, "Mon"); T.dPoint = W("dashboard", 1, "pointage"); T.dSolde = W("dashboard", 1, "solde");
  T.dDocs = W("dashboard", 1, "documents"); T.dNote = W("dashboard", 1, "note");
  T.in = W("pointage", 1, "commencez") + 0.2;            // « Commencer ma journée »
  T.pause = W("pointage", 2, "pause");                   // « Je pars en pause »
  T.ret = W("pointage", 2, "revenez");                   // « Je reviens de pause »
  T.out = W("pointage", 3, "terminez") + 0.15;           // « Terminer ma journée »
  T.saved = W("pointage", 4, "horaire"); T.minute = W("pointage", 4, "minute");
  T.solde = W("conges", 0, "solde"); T.rights = W("conges", 1, "droits"); T.seniority = W("conges", 1, "d'ancienneté");
  T.declare = W("absences", 0, "déclarer"); T.proof = W("absences", 0, "justificatif");
  T.absSend = segE("absences", 0) + 0.05; T.verif = W("absences", 1, "vérifient"); T.follow = W("absences", 1, "suivez");
  T.receive = W("documents", 0, "recevez"); T.contract = W("documents", 0, "contrat");
  T.tabC = W("documents", 1, "contrats"); T.tabAv = W("documents", 1, "avenants"); T.tabAt = W("documents", 1, "attestations");
  T.consult = W("documents", 2, "consultez"); T.dl = W("documents", 2, "téléchargez");
  T.type = W("demarches", 1, "type"); T.fill = W("demarches", 1, "décrivez"); T.reqSend = W("demarches", 1, "envoyez") + 0.1;
  T.track = W("demarches", 2, "suivez"); T.process = W("demarches", 2, "traitement");
  T.steps = [W("demarches", 2, "étape", 0), W("demarches", 2, "par"), W("demarches", 2, "étape", 1)];
  T.dir = W("contenu", 0, "Direction"); T.rh = W("contenu", 0, "RH"); T.it = W("contenu", 0, "l'IT");
  T.read = W("contenu", 1, "lecture"); T.confirm = W("contenu", 1, "confirmez");
  T.chat = W("mail", 0, "échangez"); T.mailSend = W("mail", 0, "directement") + 0.1; T.direct = W("mail", 0, "MyWebtel");
  T.ticket = W("support", 1, "ticket") + 0.05; T.charge = W("support", 1, "prend");
  T.end = S0("signature") - 0.2;
  T.final = onBar(W("signature", 0, "MyWebtel") - 0.5) + 0.08;
  const NAVT = {                                         // clic dans le menu : sur le nom de l'écran prononcé
    attendance: W("pointage", 0, "pointage"), leaves: W("conges", 0, "congés"), absences: W("absences", 0, "absences"),
    documents: W("documents", 0, "documents", 0), requests: W("demarches", 0, "demandes"), content: W("contenu", 0, "Contenu"),
    mail: W("mail", 0, "Mail"), support: W("support", 0, "Support"),
  };
  T.tickType = NAVT.support + 0.7;
  const NAV = [[0, "dashboard"], [NAVT.attendance, "attendance"], [NAVT.leaves, "leaves"], [NAVT.absences, "absences"], [NAVT.documents, "documents"],
               [NAVT.requests, "requests"], [NAVT.content, "content"], [NAVT.mail, "mail"], [NAVT.support, "support"]];
  const URL = Object.fromEntries(PAGES);

  // ------------------------------------------------------------------ caméra
  const WIDE = { cx: 720, cy: (CH + PH) / 2, s: 0.98, rx: 0, ry: 0, y: 0 };
  function frame(o) {                                    // gros plan : jamais les bords de la fenêtre
    if (o.s * 1440 >= 1940) o.cx = clamp(o.cx, 960 / o.s + 8, 1440 - 960 / o.s - 8);
    if (o.s * (CH + PH) >= 1100) o.cy = clamp(o.cy, 540 / o.s + (o.s >= 1.6 ? CH : 8), CH + PH - 540 / o.s - 8);   // gros plan serré : sans la barre d'adresse
    return o;
  }
  const on = (get, s, extra = {}) => () => { const [x, y] = winPt(get()); return frame(Object.assign({ cx: x, cy: y, s, rx: 0, ry: 0, y: 0 }, extra)); };
  const fixed = o => () => Object.assign({}, WIDE, o);
  // avant chaque clic de menu, la caméra recule : on voit la barre latérale et le curseur qui va cliquer
  const navOut = pg => [NAVT[pg] - 1.1, NAVT[pg] - 0.35, fixed({ s: 0.98, rx: 2, ry: (pg.length % 2 ? 5 : -5) })];
  const navIn = (pg, o = {}) => [NAVT[pg] + 0.25, NAVT[pg] + 1.1, fixed(Object.assign({ s: 1.04, rx: 2, ry: pg.length % 2 ? -4 : 4 }, o))];
  const MOVES = [
    [T.dIntro - 0.3, T.dIntro + 0.7, fixed({ s: 1.05, rx: 2, ry: -4 })],
    [T.dPoint - 0.35, T.dPoint + 0.35, on(() => $("dashboard", ".mw-home-clock"), 1.4, { ry: -2 })],
    [T.dSolde - 0.3, T.dSolde + 0.35, on(() => $("dashboard", ".mw-kpis a"), 1.75, { ry: 2 })],
    [T.dDocs - 0.3, T.dDocs + 0.35, on(() => $("dashboard", ".mw-dashboard-bottom .mw-card"), 1.5, { ry: -2 })],
    [T.dNote - 0.3, T.dNote + 0.4, on(() => $("dashboard", ".mw-home-note"), 1.4, { ry: 2 })],
    navOut("attendance"),
    navIn("attendance"),
    [T.in - 1.0, T.in - 0.3, on(() => $("attendance", ".mw-punch-card"), 1.32, { ry: -2 })],
    [T.saved - 0.3, T.saved + 0.5, on(() => F("attendance", "today"), 1.5, { ry: 3 })],
    [T.minute - 0.1, T.minute + 0.6, on(() => F("attendance", "today"), 1.8, { ry: 2 })],
    navOut("leaves"),
    navIn("leaves"),
    [T.solde - 0.3, T.solde + 0.4, on(() => F("leaves", "metrics"), 1.45)],
    [T.rights - 0.6, T.rights + 0.2, on(() => F("leaves", "seniority"), 2.0)],
    [T.seniority + 0.1, T.seniority + 0.7, on(() => F("leaves", "seniority-text"), 1.7)],
    navOut("absences"),
    navIn("absences"),
    [T.declare - 0.3, T.declare + 0.4, on(() => $("absences", ".mw-two > .mw-card"), 1.35, { cy: 600 })],
    [T.verif - 0.4, T.verif + 0.3, on(() => F("absences", "abs-new"), 1.55, { cy: 380 })],
    navOut("documents"),
    navIn("documents"),
    [T.receive - 0.3, T.receive + 0.4, on(() => F("documents", "doc-new"), 1.5)],
    [T.tabC - 0.4, T.tabC + 0.2, on(() => F("documents", "doc-tabs"), 1.55, { cy: 430 })],
    [T.consult - 0.3, T.consult + 0.4, on(() => $("documents", ".mw-preview"), 1.42)],
    navOut("requests"),
    navIn("requests"),
    [T.type - 0.4, T.type + 0.2, on(() => F("requests", "req-cats"), 1.45, { cy: 560 })],
    [T.track - 0.3, T.track + 0.4, on(() => $("requests", ".mw-filter-panel"), 1.45, { cy: 360 })],
    navOut("content"),
    navIn("content"),
    [T.dir - 0.5, T.dir, on(() => $("content", ".mw-content-toolbar .mw-tabs"), 1.55)],
    [T.read - 0.3, T.read + 0.5, on(() => $("content", ".mw-note-article"), 1.25)],
    [T.confirm - 0.2, T.confirm + 0.4, on(() => F("content", "note-confirm"), 1.55)],
    navOut("mail"),
    navIn("mail"),
    [T.chat - 0.4, T.chat + 0.3, on(() => $("mail", ".mw-note-article"), 1.35, { cy: 620 })],
    [T.direct - 0.3, T.direct + 0.6, fixed({ s: 1.02, rx: 3, ry: 5 })],
    navOut("support"),
    navIn("support"),
    [T.tickType - 0.1, T.tickType + 0.5, on(() => $("support", ".mw-two > .mw-card"), 1.3, { cy: 600 })],
    [T.ticket + 0.3, T.ticket + 1.0, on(() => F("support", "tick-new"), 1.55)],
    [T.charge + 0.8, T.end + 0.4, fixed({ s: 0.86, rx: 8, ry: -10 })],
    [T.end + 0.2, T.end + 1.6, fixed({ s: 0.6, rx: 22, ry: -16, y: 260 })],
  ].sort((a, b) => a[0] - b[0]);
  function cameraAt(t) {
    const c = Object.assign({}, WIDE);
    for (const [a, b, tgt] of MOVES) {
      if (t <= a) break;
      const g = tgt(), p = E.inOutQuint(seg(t, a, b));
      for (const k of Object.keys(c)) c[k] = lerp(c[k], g[k] !== undefined ? g[k] : c[k], p);
    }
    const inn = E.outQuart(seg(t, T.winIn, T.winIn + 1.6));           // la fenêtre monte du bas, inclinée
    c.y += (1 - inn) * 1000; c.rx += (1 - inn) * 28;
    c.ry += 0.6 * Math.sin(t * 0.45); c.rx += 0.4 * Math.sin(t * 0.33 + 1);   // respiration très légère
    return c;
  }
  function applyCamera(c) {
    world.style.transform = `translate3d(960px,${(540 + c.y).toFixed(2)}px,0) rotateX(${c.rx.toFixed(3)}deg) rotateY(${c.ry.toFixed(3)}deg) scale(${c.s.toFixed(4)}) translate3d(${(-WX - c.cx).toFixed(2)}px,${(-WY - c.cy).toFixed(2)}px,0)`;
  }

  // ------------------------------------------------------------------ curseur : [instant du clic, élément, visible depuis, jusqu'à]
  const nav = (pg, item) => () => F(pg, "nav-" + item);
  const navClick = (from, pg, item) => [NAVT[pg] - 0.05, nav(from, item || pg), NAVT[pg] - 1.0, NAVT[pg] + 0.3];
  const docTab = cat => () => q(F("documents", "doc-tabs"), `[data-doc-category="${cat}"]`);
  const CLICKS = [
    navClick("dashboard", "attendance"),
    [T.in, () => F("attendance", "punch"), T.in - 0.9, T.out + 0.6],
    [T.pause, () => F("attendance", "punch"), T.in, T.out + 0.6],
    [T.ret, () => F("attendance", "punch"), T.in, T.out + 0.6],
    [T.out, () => F("attendance", "punch"), T.in, T.out + 0.6],
    navClick("attendance", "leaves"),
    navClick("leaves", "absences"),
    [T.proof + 0.1, () => F("absences", "abs-upload"), T.proof - 0.7, T.absSend + 0.5],
    [T.absSend, () => F("absences", "abs-send"), T.proof, T.absSend + 0.5],
    navClick("absences", "documents"),
    [T.tabC, docTab("contrat"), T.tabC - 0.7, T.consult + 0.4],
    [T.tabAt, docTab("attestation"), T.tabC, T.consult + 0.4],
    [T.consult, () => q(F("documents", "doc-new"), ".mw-icon-button"), T.tabC, T.dl + 0.5],
    [T.dl, () => $("documents", ".mw-preview-actions .mw-button"), T.consult, T.dl + 0.5],
    navClick("documents", "requests"),
    [T.type, () => q(F("requests", "req-cats"), "button"), T.type - 0.7, T.reqSend + 0.5],
    [T.fill - 0.2, () => F("requests", "req-subject"), T.type, T.reqSend + 0.5],
    [T.reqSend, () => F("requests", "req-send"), T.type, T.reqSend + 0.5],
    navClick("requests", "content"),
    [T.confirm, () => F("content", "note-check"), T.confirm - 0.7, T.confirm + 1.1],
    [T.confirm + 0.6, () => F("content", "note-btn"), T.confirm, T.confirm + 1.1],
    navClick("content", "mail"),
    [T.chat - 0.35, () => F("mail", "mail-input"), T.chat - 1.0, T.mailSend + 0.5],
    [T.mailSend, () => F("mail", "mail-send"), T.chat - 0.35, T.mailSend + 0.5],
    navClick("mail", "support"),
    [T.tickType, () => F("support", "tick-subject"), T.tickType - 0.6, T.ticket + 0.5],
    [T.ticket, () => F("support", "tick-send"), T.tickType, T.ticket + 0.5],
  ].sort((a, b) => a[0] - b[0]);
  function cursorAt(t) {
    let k = -1;
    for (let i = 0; i < CLICKS.length; i++) if (t >= CLICKS[i][2] - 0.25 && t <= CLICKS[i][3] + 0.25 && (k < 0 || CLICKS[i][0] <= t + 0.75)) k = i;
    if (k < 0) { st(cur, { o: 0 }); st(rip, { o: 0 }); return; }
    const [tc, get, v0, v1] = CLICKS[k];
    const [x1, y1] = screenOf(get());
    let x0 = x1 + 160, y0 = y1 + 120;
    if (k > 0 && CLICKS[k - 1][3] >= v0 - 0.3 && CLICKS[k - 1][0] < tc) { const p = screenOf(CLICKS[k - 1][1]()); x0 = p[0]; y0 = p[1]; }
    const p = E.inOutCubic(seg(t, Math.max(v0, tc - 0.7), tc - 0.08));
    const press = Math.max(0, 1 - Math.abs(t - tc) / 0.1);
    const x = lerp(x0, x1, p), y = lerp(y0, y1, p);
    st(cur, { x: x - 3, y: y - 2, s: 1 - 0.14 * press, o: Math.min(seg(t, v0 - 0.25, v0), 1 - seg(t, v1, v1 + 0.25)) });
    const r = seg(t, tc, tc + 0.5);
    st(rip, { x, y, s: 0.3 + 0.9 * E.outCubic(r), o: r > 0 && r < 1 ? (1 - r) * 0.9 : 0 });
  }
  const press = (el, t, tc) => { if (el) el.style.transform = `scale(${(1 - 0.04 * Math.max(0, 1 - Math.abs(t - tc) / 0.12)).toFixed(4)})`; };

  // ------------------------------------------------------------------ états des écrans (libellés réels du PHP)
  function hhmm(m) { m = Math.round(m); return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }
  function setValue(el, v, focus) {
    if (!el) return;
    if (el.value !== v) el.value = v;
    if (focus && el.ownerDocument.activeElement !== el) el.focus({ preventScroll: true });
    if (!focus && el.ownerDocument.activeElement === el) el.blur();
  }
  function screens(t) {
    // Mon espace : l'horloge en direct
    const clk = F("dashboard", "clock");
    if (clk) { const s = 7 * 3600 + 28 * 60 + 40 + Math.max(0, Math.floor(t - T.winIn)); clk.innerHTML = `${hhmm(s / 60 - (s % 60) / 60)}<small>:${String(s % 60).padStart(2, "0")}</small>`; }
    glow($("dashboard", ".mw-home-clock"), pulse(t, T.dPoint - 0.1, 1.3));
    glow($("dashboard", ".mw-kpis a"), pulse(t, T.dSolde - 0.1, 1.2));
    glow($("dashboard", ".mw-dashboard-bottom .mw-card"), pulse(t, T.dDocs - 0.1, 1.2));
    glow($("dashboard", ".mw-home-note"), pulse(t, T.dNote - 0.1, 1.4));
    // Pointage : À commencer → Au travail → En pause → Au travail → Journée terminée
    const stage = t < T.in ? 0 : t < T.pause ? 1 : t < T.ret ? 2 : t < T.out ? 3 : 4;
    const badge = F("attendance", "day-badge");
    if (badge) {
      setText(badge, ["Journée à commencer", "Au travail", "En pause", "Au travail", "Journée terminée"][stage]);
      badge.className = "mw-badge " + ["amber", "green", "amber", "green", ""][stage];
    }
    const steps = F("attendance", "steps");
    if (steps) Array.from(steps.children).forEach((d, i) => {
      const done = [0, 1, 1, 2, 3][stage], curr = [0, 1, 1, 2, -1][stage];
      d.className = i < done ? "complete" : i === curr ? "current" : "";
    });
    setText(F("attendance", "punch-label"), ["Commencer ma journée", "Je pars en pause", "Je reviens de pause", "Terminer ma journée", "Journée terminée"][stage]);
    const punch = F("attendance", "punch");
    if (punch) { punch.style.opacity = stage === 4 ? "0.55" : "1"; press(punch, t, [T.in, T.pause, T.ret, T.out].reduce((a, b) => Math.abs(t - b) < Math.abs(t - a) ? b : a)); }
    ["07:28", "12:30", "13:30", "16:34"].forEach((v, i) => {
      const b = F("attendance", "today-" + i);
      setText(b, stage > i ? v : "—");
      if (b) glow(b.parentElement, Math.max(pulse(t, [T.in, T.pause, T.ret, T.out][i] + 0.05, 0.9), pulse(t, T.saved + 0.15 + 0.3 * i, 1.0)));
    });
    // Mes congés : le solde, puis la règle d'ancienneté
    const met = F("leaves", "metrics");
    if (met) glow(met.firstElementChild, pulse(t, T.solde - 0.1, 1.6));
    glow(F("leaves", "seniority"), pulse(t, T.rights - 0.2, 2.2));
    glow(F("leaves", "seniority-text"), pulse(t, T.seniority, 1.6));
    // Mes absences : déclaration avec justificatif, puis vérification RH
    const ab = D("absences");
    if (ab) {
      const [d0, d1] = ab.querySelectorAll('input[type="date"]');
      setValue(d0, t >= T.declare + 0.15 ? "2026-10-20" : ""); setValue(d1, t >= T.declare + 0.45 ? "2026-10-21" : "");
      setText(ab.querySelector('[data-duration="calendar"]'), t >= T.declare + 0.45 ? "2 jours" : "0 jour");
      const up = F("absences", "abs-upload"), got = t >= T.proof + 0.15;
      if (up) { setText(up.querySelector("b"), got ? "certificat-medical.pdf" : "Glissez et déposez votre fichier ici"); setText(up.querySelector("small"), got ? "PDF · 312 Ko · prêt à l’envoi" : "ou cliquez pour parcourir vos fichiers · PDF, JPG ou PNG · 5 Mo maximum"); glow(up, pulse(t, T.proof + 0.1, 1.0)); }
      FR.absences.contentWindow.scrollTo(0, Math.round(110 * E.inOutCubic(seg(t, T.proof + 0.3, T.absSend - 0.2)) * (1 - E.inOutCubic(seg(t, T.absSend + 0.3, T.follow)))));
      press(F("absences", "abs-send"), t, T.absSend);
      const n = F("absences", "abs-new");
      if (n) { n.hidden = t < T.absSend + 0.25; glow(n, pulse(t, T.absSend + 0.3, 1.4)); }
      const nb = F("absences", "abs-badge");
      if (nb) setText(nb, t >= T.verif ? "Vérification RH" : "Déclarée");
      if (n) glow(n, Math.max(pulse(t, T.absSend + 0.3, 1.2), pulse(t, T.follow, 1.2)));
      const pr = F("absences", "abs-process");
      if (pr) Array.from(pr.children).forEach((s, i) => { s.className = (t >= T.verif ? i === 1 : i === 0) ? "current" : ""; });
    }
    // Mes documents : un document arrive, puis le filtre « Contrats »
    const dn = F("documents", "doc-new");
    if (dn) { dn.hidden = t < T.receive - 0.1; glow(dn, pulse(t, T.receive - 0.05, 1.5)); }
    const arrived = t >= T.receive - 0.1, pv = $("documents", ".mw-preview");      // l'aperçu suit le document sélectionné
    if (pv) {
      setText(pv.querySelector("h3"), arrived ? "Avenant au contrat de travail" : "Décompte de prestation — Septembre 2026");
      setText(pv.querySelector(".mw-preview-stage b"), arrived ? "AVENANT AU CONTRAT DE TRAVAIL" : "DÉCOMPTE DE PRESTATION");
      const old = F("documents", "doc-old");
      if (old) old.classList.toggle("selected", !arrived);
    }
    const tabs = F("documents", "doc-tabs");
    if (tabs) {                                          // Tous → Contrats → Attestations → Tous
      const cat = t >= T.consult - 0.05 ? "all" : t >= T.tabAt ? "attestation" : t >= T.tabC ? "contrat" : "all";
      tabs.querySelectorAll("button").forEach(b => b.classList.toggle("selected", b.dataset.docCategory === cat));
      D("documents").querySelectorAll(".mw-document-row").forEach(r => {
        const h3 = r.querySelector("h3").textContent;
        if (r === dn) { r.hidden = t < T.receive - 0.1 || (cat === "attestation"); return; }
        r.hidden = cat === "contrat" ? !/contrat/i.test(h3) : cat === "attestation" ? !/attestation/i.test(h3) : false;
      });
      if (dn) glow(dn, Math.max(pulse(t, T.receive - 0.05, 1.5), pulse(t, T.tabAv - 0.1, 0.9), pulse(t, T.consult, 1.0)));
    }
    glow($("documents", ".mw-preview"), pulse(t, T.consult + 0.1, 1.4));
    const dlb = $("documents", ".mw-preview-actions .mw-button");
    if (dlb) { press(dlb, t, T.dl); glow(dlb, pulse(t, T.dl, 1.0)); }
    // Mes demandes RH : type, formulaire, envoi, suivi
    const cats = F("requests", "req-cats");
    if (cats) glow(cats.querySelector("button"), pulse(t, T.type, 1.0));
    setValue(F("requests", "req-subject"), typed("Attestation de salaire", t, T.fill - 0.2, T.fill + 0.4), t > T.fill - 0.25 && t < T.fill + 0.5);
    setValue(F("requests", "req-desc"), typed("Pour un dossier de location. Merci !", t, T.fill + 0.5, T.reqSend - 0.2), t > T.fill + 0.45 && t < T.reqSend);
    press(F("requests", "req-send"), t, T.reqSend);
    const rn = F("requests", "req-new");
    if (rn) { rn.hidden = t < T.reqSend + 0.2; glow(rn, pulse(t, T.reqSend + 0.25, 1.4)); }
    const rb = F("requests", "req-badge");
    if (rb) { const on = t >= T.process; setText(rb, on ? "En cours" : "Envoyée"); rb.className = "mw-badge" + (on ? "" : " amber"); }
    const rtabs = $("requests", ".mw-filter-panel .mw-tabs");            // « étape par étape » : En attente, En cours, Traitées
    if (rtabs) Array.from(rtabs.children).slice(1).forEach((b, i) => glow(b, pulse(t, T.steps[i] - 0.05, 0.6)));
    // Contenu : Direction, RH, IT, puis confirmation de lecture
    const ctab = D("content") && D("content").querySelectorAll(".mw-content-toolbar .mw-tab");
    if (ctab && ctab.length > 3) [T.dir, T.rh, T.it].forEach((tt, i) => glow(ctab[i + 1], pulse(t, tt - 0.05, 0.7)));
    const chk = F("content", "note-check");
    if (chk) chk.checked = t >= T.confirm;
    press(F("content", "note-btn"), t, T.confirm + 0.6);
    const lu = t >= T.confirm + 0.7;
    const nr = F("content", "note-read");
    if (nr) { setText(nr, lu ? "✓ Lu" : "● Non lu"); nr.className = "mw-badge " + (lu ? "green" : "blue"); }
    setText(F("content", "note-list-read"), lu ? "✓ Lu" : "● Non lu");
    glow(F("content", "note-confirm"), pulse(t, T.confirm + 0.7, 1.2));
    glow($("content", ".mw-note-body"), pulse(t, T.read - 0.1, 1.2));
    // Mail : réponse tapée puis envoyée
    const sent = t >= T.mailSend + 0.1;
    setValue(F("mail", "mail-input"), sent ? "" : typed("C’est confirmé : jeudi à 10 h, en salle de réunion à Ouakam.", t, T.chat - 0.3, T.mailSend - 0.15), t > T.chat - 0.35 && !sent);
    const rep = F("mail", "mail-reply");
    if (rep) { rep.hidden = !sent; rep.style.transform = `translateY(${(14 * (1 - E.outCubic(seg(t, T.mailSend + 0.1, T.mailSend + 0.5)))).toFixed(1)}px)`; }
    press(F("mail", "mail-send"), t, T.mailSend);
    // Support IT : ticket ouvert puis pris en charge
    setValue(F("support", "tick-subject"), typed("Messagerie inaccessible", t, T.tickType + 0.05, T.tickType + 0.7), t > T.tickType && t < T.tickType + 0.75);
    setValue(F("support", "tick-desc"), typed("Je n’arrive plus à ouvrir ma messagerie depuis ce matin.", t, T.tickType + 0.8, T.ticket - 0.2), t > T.tickType + 0.75 && t < T.ticket);
    press(F("support", "tick-send"), t, T.ticket);
    const tn = F("support", "tick-new");
    if (tn) { tn.hidden = t < T.ticket + 0.2; glow(tn, Math.max(pulse(t, T.ticket + 0.25, 1.2), pulse(t, T.charge, 1.4))); }
    const tb = F("support", "tick-badge");
    if (tb) { const on = t >= T.charge; setText(tb, on ? "Pris en charge" : "Envoyé"); tb.className = "mw-badge" + (on ? "" : " amber"); }
  }
  function pagesAt(t) {
    let ci = 0;
    NAV.forEach((n, i) => { if (t >= n[0]) ci = i; });
    const [tn, id] = NAV[ci];
    // un clic de menu : l'écran suivant s'affiche aussitôt, comme dans l'application (la barre latérale ne bouge pas) ;
    // seul le contenu principal arrive en léger fondu, sans superposer deux écrans
    const p = ci ? 0.35 + 0.65 * E.outCubic(seg(t, tn, tn + 0.3)) : 1;
    PAGES.forEach(([k]) => { FR[k].style.visibility = k === id ? "visible" : "hidden"; });
    const main = $(id, ".mw-main-wrap");
    if (main) { main.style.opacity = p.toFixed(3); main.style.transform = p < 1 ? `translateY(${(14 * (1 - p)).toFixed(1)}px)` : ""; }
    setText(urlEl, "mywebtel.com" + URL[id]);
  }

  // ------------------------------------------------------------------ film
  window.renderAt = function (t) {
    const day = E.inOutCubic(seg(t, T.logo - 0.1, T.logo + 0.7));
    st(bgNight, { o: 1 - day });
    st(glowA, { x: 60 * Math.sin(t * 0.12), y: 40 * Math.cos(t * 0.1) });
    st(glowB, { x: -50 * Math.sin(t * 0.09), y: 30 * Math.sin(t * 0.14) });

    // ouverture : les démarches apparaissent sur les mots, puis convergent vers un point de lumière
    const conv = seg(t, W("hook", 1, "temps") - 0.1, T.logo - 0.4);
    TASKS.forEach((tk, i) => {
      const t0 = W(...tk[3]) - 0.12, sp = spring(t - t0, 0.7, 2.2), pull = E.inOutCubic(conv), drift = (t - t0) * 9;
      st(tasks[i], { x: 960 - 190 + tk[4] * 0.92 * (1 - pull) + Math.sign(tk[4]) * drift * (1 - pull), y: 540 - 46 + tk[5] * 0.95 * (1 - pull),
                     s: (1.15 + 0.25 * sp) * (1 - 0.75 * pull), o: clamp(sp * 1.3) * (1 - E.inCubic(seg(conv, 0.55, 1))),
                     blur: 10 * (1 - clamp(sp)) + 8 * pull, ry: tk[4] > 0 ? -8 : 8 });
    });
    const sk = seg(t, T.logo - 1.2, T.logo - 0.05);
    st(spark, { o: Math.sin(Math.PI * sk) * 1.2, s: 0.3 + 2.6 * E.inCubic(sk) });
    st(flash, { o: 0.8 * Math.max(0, 1 - Math.abs(t - T.logo) / 0.35) });

    // fenêtre et caméra (avant le logo : son vol lit la position du logo de la barre latérale)
    const winOn = t >= T.winIn - 0.2 && t < S0("signature") + 2.2;
    world.style.display = winOn ? "" : "none";
    if (winOn) {
      pagesAt(t); screens(t); applyCamera(cameraAt(t));
      st(win, { o: 1 - E.inCubic(seg(t, T.end + 0.4, T.end + 1.9)) });
      win.style.filter = t > T.end + 0.3 ? `blur(${(8 * seg(t, T.end + 0.3, T.end + 1.4)).toFixed(2)}px)` : "none";
    }

    // logo : la marque tourne et se pose sur le premier temps, le mot se dévoile
    const showLogo = (tl, tg) => {
      const pm = spring(t - (tl - 0.08), 0.62, 2.0), wt = E.outExpo(seg(t, tl + 0.12, tl + 0.95));
      st(lm, { s: 0.6 + 0.4 * pm, r: -40 * (1 - clamp(pm)), o: clamp(pm * 1.6) });
      lt.style.clipPath = `inset(0 ${(76 * (1 - wt)).toFixed(2)}% 0 24%)`;
      st(lt, { x: -24 * (1 - wt), o: 1 });
      const tp = E.outCubic(seg(t, tg - 0.1, tg + 0.9));
      tag.style.letterSpacing = (0.32 + 0.3 * (1 - tp)).toFixed(3) + "em";
      return tp;
    };
    if (t < T.end) {
      const tp = showLogo(T.logo, T.tag);
      // à l'entrée de la fenêtre, le logo vole jusqu'à celui de la barre latérale (vraie interface)
      const fly = E.inOutQuint(seg(t, T.winIn + 0.05, T.winIn + 1.35));
      let tx = 0, ty = 0, sc = 1;
      if (fly > 0 && winOn) {
        const img = $("dashboard", ".mw-brand img");
        const [x, y] = screenOf(img);
        const r = img.getBoundingClientRect();
        probe.style.left = (r.left) + "px"; probe.style.top = (CH + r.top) + "px";
        const a = probe.getBoundingClientRect();
        probe.style.left = (r.right) + "px";
        const b = probe.getBoundingClientRect();
        const wScreen = b.left - a.left;
        sc = lerp(1, wScreen * 1.02 / LW, fly);
        tx = lerp(0, x - 960, fly); ty = lerp(0, y - 470, fly);
      }
      const handoff = seg(t, T.winIn + 1.15, T.winIn + 1.4);
      st(logo, { x: tx, y: ty, s: sc, o: (t >= T.logo - 0.3 ? 1 : 0) * (1 - handoff) });
      if (winOn) $("dashboard", ".mw-brand img").style.opacity = handoff.toFixed(3);   // le logo de la barre prend le relais
      st(tag, { c: true, y: ty * 0.9, o: tp * (1 - E.outCubic(seg(t, T.winIn, T.winIn + 0.5))) });
    } else {
      const tl2 = T.final, tp = showLogo(tl2, W("signature", 1, "espace"));
      const end = seg(t, S1("signature") - 1.0, S1("signature") - 0.1);
      st(logo, { x: 0, y: 0, o: seg(t, tl2 - 0.7, tl2 - 0.2) * (1 - end), s: 1 + 0.025 * seg(t, tl2, S1("signature")) });
      st(tag, { c: true, y: 0, o: tp * (1 - end) });
    }
    cursorAt(t);

    // heure de la journée (film) pendant le pointage
    const ck = [[T.in, 448], [T.pause, 750], [T.ret, 810], [T.out, 994]];
    let ci = -1; ck.forEach((c, i) => { if (t >= c[0] - 0.05) ci = i; });
    st(clock, { o: E.outCubic(seg(t, T.in - 0.5, T.in - 0.1)) * (1 - seg(t, NAVT.leaves - 0.4, NAVT.leaves)) });
    if (ci >= 0) { const prev = ci ? ck[ci - 1][1] : 448; setText(q(clock, ".ct"), hhmm(lerp(prev, ck[ci][1], E.inOutCubic(seg(t, ck[ci][0] - 0.05, ck[ci][0] + 0.35))))); }
    else setText(q(clock, ".ct"), "07:28");
  };
  // repères exportés pour les bruitages (render.js les écrit dans build/mywebtel/cues.json)
  window.FILM = { duration: TL.duration, T, clicks: CLICKS.map(c => c[0]), nav: NAV.slice(1).map(n => n[0]),
                  tasks: TASKS.map(tk => W(...tk[3]) - 0.12) };
  Promise.all([document.fonts.ready, ...loads]).then(() => {
    const imgs = Array.from(document.images).map(i => i.decode().catch(() => {}));
    Promise.all(imgs).then(() => { window.renderAt(0); window.READY = true; });
  });
})();
