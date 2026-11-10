/* MyWebtel — film de présentation V5 (1920×1080, 30 i/s), sur la vraie interface, voix « Simon » (ElevenLabs).
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
  const PAGES = [["dashboard", "/dashboard"], ["attendance", "/attendance"], ["leaves", "/leaves"], ["absences", "/absences"], ["sign", "/documents"],
                 ["requests", "/hr-requests"], ["content", "/content"], ["mail", "/discussions"], ["support", "/tickets"], ["agent", "/dashboard"]];
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
  // V5 : mélange des trois références de l'utilisateur, aux couleurs de MyWebtel (bleu nuit #06213e, bleu #008ff1,
  // cyan #05daf0) : ouverture cinéma (reportage), cartes et badges ✓ sur fond clair (pub Drive Academy), traits de
  // lumière et montée finale (bande-annonce), avec retenue.
  Object.assign(ICON, {
    pen: '<path d="M4 20l4-1 11-11-3-3L5 16z"/>',
    printer: '<path d="M7 9V3h10v6M7 17H4v-6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v6h-3"/><rect x="7" y="14" width="10" height="7"/>',
    scan: '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3M4 12h16"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  });
  const light = add(stage, `<div id="light"></div>`);
  stage.insertBefore(light, fx);
  const CURSOR = `<svg class="cursor" viewBox="0 0 34 44"><path d="M3 2l26 24H16l7 14-5 2-7-14-8 8z" fill="#fff" stroke="#041b34" stroke-width="2.4" stroke-linejoin="round"/></svg>`;
  const halo = add(stage, `<div class="halo"></div>`);
  stage.insertBefore(halo, view);
  const cur = add(fx, CURSOR), rip = add(fx, `<div class="ripple"></div>`);
  const clock = add(fx, `<div class="note" style="right:70px;bottom:46px;font-size:26px;gap:14px">${ic("clock")}<span style="font-weight:500;color:var(--muted)">Jeudi 15 octobre</span><b class="ct" style="font-variant-numeric:tabular-nums;font-size:30px"></b></div>`);
  // ouverture : les démarches du quotidien
  const TASKS = [["clock", "Pointage", "Commencer ma journée", ["hook", 0, "Pointer"], -560, -250], ["calendar", "Mes congés", "24 jours disponibles", ["hook", 0, "congé"], 480, -280],
                 ["file", "Fiche de paie", "Octobre 2026 · PDF", ["hook", 0, "fiche"], -520, 210], ["pen", "Document à signer", "Avenant au contrat", ["hook", 0, "signer"], 500, 230]];
  const tasks = TASKS.map(([i, a, b]) => add(fx, `<div class="task"><span class="ti">${ic(i)}</span><div>${a}<small>${b}</small></div></div>`));
  const digits = add(fx, `<div class="digits" style="top:330px"></div>`);
  const kinFou = add(fx, `<div class="kin" style="top:600px;color:#eef5ff"></div>`);
  const kinQ = add(fx, `<div class="kin" style="top:500px;color:#fff;font-size:72px"></div>`);
  const spark = add(fx, `<div class="abs" style="left:960px;top:540px;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;background:#fff;box-shadow:0 0 40px 18px rgba(5,218,240,.8)"></div>`);
  const LOGO = "brand/webtel-logo.svg", LW = 960, LH = Math.round(LW * 1224 / 3520);
  const logo = add(fx, `<div class="abs" style="left:${960 - LW / 2}px;top:${470 - LH / 2}px;width:${LW}px;height:${LH}px">
      <img class="lm" src="${LOGO}" style="position:absolute;inset:0;width:100%;clip-path:inset(0 76% 0 0);transform-origin:13% 55%">
      <img class="lt" src="${LOGO}" style="position:absolute;inset:0;width:100%;clip-path:inset(0 0 0 24%)"></div>`);
  const lm = q(logo, ".lm"), lt = q(logo, ".lt");
  const tag = add(fx, `<div class="center tagline" style="top:${470 + LH / 2 + 56}px">MYWEBTEL · ESPACE COLLABORATEUR</div>`);
  // signature : « imprimer, signer, scanner ? Sauf que non. »
  const paper = add(fx, `<div class="layer" style="background:radial-gradient(1400px 900px at 50% 45%, #ffffff 0%, #f1f7fd 70%)"></div>`);
  const kinOld = add(fx, `<div class="kin dark" style="top:430px"><span class="it k1">${ic("printer")}<s>Imprimer</s></span><span class="it k2">${ic("pen")}<s>Signer</s></span><span class="it k3">${ic("scan")}<s>Scanner</s></span></div>`);
  const kinDoc = add(fx, `<div class="kin dark" style="top:300px;font-size:56px">Un <b style="color:var(--blue)">document</b> à signer ?</div>`);
  const kinNon = add(fx, `<div class="kin dark" style="top:600px;font-size:84px"></div>`);
  const mailcard = add(fx, `<div class="mailcard" style="right:70px;top:70px"><div class="from"><i>W</i><div><b style="color:var(--ink)">MyWebtel</b> · à l’instant</div></div>
      <h4>Mywebtel — Votre code de signature</h4><p>Votre code pour signer « Avenant au contrat de travail » est :</p><span class="code">482 913</span>
      <p style="margin-top:10px;font-size:14px">Valable 10 minutes. Ne communiquez ce code à personne.</p></div>`);
  const toast = add(fx, `<div class="toast" style="left:50%;top:60px"><i>✓</i>Signature confirmée. Votre PDF signé est disponible.</div>`);
  const flash = add(fx, `<div class="layer" style="background:#fff"></div>`);
  const checks = {};
  const CHECK = (id, txt) => (checks[id] = add(fx, `<div class="check" style="left:960px;top:982px"><span class="ok">${ic("check")}</span>${txt}</div>`));

  // ------------------------------------------------------------------ chronologie (tout dérive des mots de la voix)
  const T = {};
  T.logo = onBar(W("reveal", 0, "MyWebtel") - 0.4);
  T.tag = W("reveal", 0, "espace");
  T.winIn = W("reveal", 0, "collaborateur") + 0.5;
  T.fou = W("hook", 0, "fou"); T.boulot = W("hook", 0, "Au"); T.ques = segT("hook", 1); T.endroit = W("hook", 1, "endroit");
  // pointage
  T.in = W("pointage", 0, "clic") + 0.05; T.pause = W("pointage", 0, "pause"); T.ret = W("pointage", 0, "retour"); T.out = W("pointage", 0, "départ");
  T.saved = W("pointage", 0, "enregistré"); T.minute = W("pointage", 0, "minute");
  // congés
  T.solde = W("conges", 0, "solde"); T.rights = W("conges", 0, "droits"); T.seniority = W("conges", 0, "d'ancienneté");
  // absences
  T.declare = W("absences", 0, "déclares"); T.proof = W("absences", 0, "justificatif"); T.absSend = W("absences", 0, "et") - 0.05;
  T.rh = W("absences", 0, "RH"); T.reste = W("absences", 0, "reste");
  // signature
  T.doc = W("signature", 0, "document"); T.kImp = W("signature", 0, "l'imprimer"); T.kSig = W("signature", 0, "signer", 1); T.kScan = W("signature", 0, "scanner"); T.non = W("signature", 0, "Sauf");
  T.back = W("signature", 0, "Tu", 0) - 0.1;
  T.open = W("signature", 0, "signes") - 0.1; T.nom = W("signature", 0, "nom"); T.draw = W("signature", 0, "dessines") - 0.15;
  T.code = W("signature", 0, "code"); T.mail = W("signature", 0, "mail"); T.tape = W("signature", 0, "tapes"); T.signed = W("signature", 0, "signé") - 0.1;
  // demandes RH
  T.att = W("demandes", 0, "attestation"); T.question = W("demandes", 0, "question"); T.fill = W("demandes", 0, "demande"); T.clics = W("demandes", 0, "clics");
  T.process = W("demandes", 0, "traitement");
  // contenu
  T.dir = W("contenu", 0, "Direction"); T.rhC = W("contenu", 0, "RH"); T.read = W("contenu", 0, "lis"); T.confirm = W("contenu", 0, "confirmes"); T.lu = W("contenu", 0, "clic");
  // mail et support
  T.chat = W("mail", 0, "échanges"); T.mailSend = W("mail", 0, "Mail") + 0.35; T.tick = W("mail", 0, "support"); T.ticket = W("mail", 0, "ticket"); T.charge = W("mail", 0, "charge");
  // agent
  T.launch = W("agent", 0, "l'agent"); T.ask = T.launch + 0.45; T.askSend = W("agent", 0, "solde") - 0.1;
  T.chips = [W("agent", 0, "solde"), W("agent", 0, "démarche"), W("agent", 0, "souci")];
  T.answer = W("agent", 0, "répond") - 0.1; T.prep = W("agent", 0, "prépare"); T.toi = W("agent", 0, "Toi"); T.okAgent = W("agent", 0, "confirmer") + 0.05;
  T.end = W("fin", 0, "MyWebtel") - 0.8;
  T.final = onBar(W("fin", 0, "MyWebtel") - 0.5) + 0.08;
  // écrans : clic dans le menu sur le mot qui le nomme
  const NAVT = {
    attendance: W("pointage", 0, "matin"), leaves: W("conges", 0, "congés"), absences: W("absences", 0, "absence"), sign: W("signature", 0, "documents") - 0.1,
    requests: W("demandes", 0, "attestation"), content: W("contenu", 0, "notes"), mail: W("mail", 0, "collègues"), support: W("mail", 0, "support"),
    agent: W("agent", 0, "question") - 0.1,
  };
  const NAV = [[0, "dashboard"], [NAVT.attendance, "attendance"], [NAVT.leaves, "leaves"], [NAVT.absences, "absences"], [NAVT.sign, "sign"],
               [NAVT.requests, "requests"], [NAVT.content, "content"], [NAVT.mail, "mail"], [NAVT.support, "support"], [NAVT.agent, "agent"]];
  const URL = Object.fromEntries(PAGES);
  const NAVITEM = { attendance: "attendance", leaves: "leaves", absences: "absences", sign: "documents", requests: "requests", content: "content", mail: "mail", support: "support", agent: "dashboard" };
  // badges ✓ (style Drive Academy) : [id, texte, instant]
  const CHECKS = [["minute", "À la minute près", T.minute], ["anciennete", "Droits ouverts après 1 an d’ancienneté", T.seniority],
                  ["rh", "Les RH s’occupent du reste", T.rh], ["code", "Code de validation par e-mail", T.mail], ["signe", "Document signé", T.signed + 0.35],
                  ["clics", "En deux clics", T.clics], ["lu", "Lecture confirmée", T.lu + 0.35], ["ticket", "Ticket pris en charge", T.charge],
                  ["agent", "Rien n’est envoyé sans ta confirmation", T.okAgent + 0.3]];
  CHECKS.forEach(([id, txt]) => CHECK(id, txt));
  const checkEnd = i => (i + 1 < CHECKS.length ? Math.min(CHECKS[i + 1][2] - 0.2, CHECKS[i][2] + 3.2) : T.end);

  // ------------------------------------------------------------------ caméra
  const WIDE = { cx: 720, cy: (CH + PH) / 2, s: 0.98, rx: 0, ry: 0, y: 0 };
  function frame(o) {
    if (o.s * 1440 >= 1940) o.cx = clamp(o.cx, 960 / o.s + 8, 1440 - 960 / o.s - 8);
    if (o.s * (CH + PH) >= 1100) o.cy = clamp(o.cy, 540 / o.s + (o.s >= 1.6 ? CH : 8), CH + PH - 540 / o.s - 8);
    return o;
  }
  const on = (get, s, extra = {}) => () => { const [x, y] = winPt(get()); return frame(Object.assign({ cx: x, cy: y, s, rx: 0, ry: 0, y: 0 }, extra)); };
  const fixed = o => () => Object.assign({}, WIDE, o);
  const navOut = pg => [NAVT[pg] - 1.0, NAVT[pg] - 0.3, fixed({ s: 0.98, rx: 2, ry: (pg.length % 2 ? 5 : -5) })];
  const navIn = (pg, o = {}) => [NAVT[pg] + 0.25, NAVT[pg] + 1.0, fixed(Object.assign({ s: 1.04, rx: 2, ry: pg.length % 2 ? -4 : 4 }, o))];
  const MOVES = [
    navOut("attendance"), navIn("attendance"),
    [T.in - 0.9, T.in - 0.25, on(() => $("attendance", ".mw-punch-card"), 1.32, { ry: -2 })],
    [T.saved - 0.3, T.saved + 0.5, on(() => F("attendance", "today"), 1.5, { ry: 3 })],
    [T.minute - 0.1, T.minute + 0.6, on(() => F("attendance", "today"), 1.75, { ry: 2 })],
    navOut("leaves"), navIn("leaves"),
    [T.solde - 0.3, T.solde + 0.4, on(() => F("leaves", "metrics"), 1.45)],
    [T.rights - 0.5, T.rights + 0.2, on(() => F("leaves", "seniority"), 1.95)],
    navOut("absences"), navIn("absences"),
    [T.declare - 0.4, T.declare + 0.3, on(() => $("absences", ".mw-two > .mw-card"), 1.35, { cy: 600 })],
    [T.rh - 0.4, T.rh + 0.3, on(() => F("absences", "abs-new"), 1.5, { cy: 380 })],
    [T.back - 0.1, T.back + 0.8, fixed({ s: 0.98, rx: 2, ry: -5 })],
    [NAVT.sign + 0.25, NAVT.sign + 0.9, on(() => $("sign", ".mw-document-row"), 1.3, { cx: 640 })],
    [T.open + 0.05, T.open + 0.7, on(() => F("sign", "sign-dialog"), 1.18, { cy: 470 })],
    [T.draw - 0.35, T.draw + 0.3, on(() => F("sign", "sign-canvas"), 1.4)],
    [T.code - 0.2, T.code + 0.4, on(() => F("sign", "sign-code-block"), 1.4)],
    [T.signed + 0.35, T.signed + 1.1, on(() => $("sign", ".mw-preview"), 1.35, { cy: 430 })],
    navOut("requests"), navIn("requests"),
    [T.att + 1.1, T.att + 1.6, on(() => F("requests", "req-cats"), 1.45, { cy: 560 })],
    [T.process - 0.5, T.process + 0.2, on(() => $("requests", ".mw-filter-panel"), 1.45, { cy: 360 })],
    navOut("content"), navIn("content"),
    [T.dir - 0.4, T.dir + 0.1, on(() => $("content", ".mw-content-toolbar .mw-tabs"), 1.55)],
    [T.read - 0.2, T.read + 0.5, on(() => $("content", ".mw-note-article"), 1.25)],
    [T.confirm - 0.1, T.confirm + 0.5, on(() => F("content", "note-confirm"), 1.55)],
    navOut("mail"), navIn("mail"),
    [T.chat + 0.1, T.chat + 0.6, on(() => $("mail", ".mw-note-article"), 1.35, { cy: 620 })],
    navOut("support"), navIn("support"),
    [T.ticket - 0.2, T.ticket + 0.4, on(() => F("support", "tick-new"), 1.5)],
    navOut("agent"), navIn("agent", { s: 1.0, ry: -3 }),
    [T.ask - 0.2, T.ask + 0.6, on(() => F("agent", "agent-input"), 1.7, { ry: -3 })],
    [T.chips[0] - 0.35, T.chips[0] + 0.3, on(() => F("agent", "agent-chips"), 1.75, { ry: -2 })],
    [T.answer - 0.45, T.answer + 0.3, on(() => F("agent", "agent-a"), 1.8, { ry: -2 })],
    [T.prep - 0.05, T.prep + 0.6, on(() => F("agent", "agent-prep"), 1.8, { ry: -2 })],
    [T.okAgent + 0.6, T.end + 0.4, fixed({ s: 0.88, rx: 7, ry: -9 })],
    [T.end + 0.2, T.end + 1.6, fixed({ s: 0.6, rx: 22, ry: -16, y: 260 })],
  ].sort((a, b) => a[0] - b[0]);
  function cameraAt(t) {
    const c = Object.assign({}, WIDE);
    for (const [a, b, tgt] of MOVES) {
      if (t <= a) break;
      const g = tgt(), p = E.inOutQuint(seg(t, a, b));
      for (const k of Object.keys(c)) c[k] = lerp(c[k], g[k] !== undefined ? g[k] : c[k], p);
    }
    const inn = E.outQuart(seg(t, T.winIn, T.winIn + 1.6));
    c.y += (1 - inn) * 1000; c.rx += (1 - inn) * 28;
    // « Imprimer, signer, scanner » : la fenêtre recule dans le flou pendant le texte
    const away = E.inOutCubic(seg(t, T.doc - 0.25, T.doc + 0.45)) * (1 - E.inOutCubic(seg(t, T.back - 0.1, T.back + 0.6)));
    c.s *= 1 - 0.18 * away; c.y += 120 * away;
    c.ry += 0.6 * Math.sin(t * 0.45); c.rx += 0.4 * Math.sin(t * 0.33 + 1);
    return [c, away];
  }
  function applyCamera(c) {
    world.style.transform = `translate3d(960px,${(540 + c.y).toFixed(2)}px,0) rotateX(${c.rx.toFixed(3)}deg) rotateY(${c.ry.toFixed(3)}deg) scale(${c.s.toFixed(4)}) translate3d(${(-WX - c.cx).toFixed(2)}px,${(-WY - c.cy).toFixed(2)}px,0)`;
  }

  // ------------------------------------------------------------------ curseur : [instant du clic, élément, visible depuis, jusqu'à]
  const nav = (pg, item) => () => F(pg, "nav-" + item);
  const prevPage = pg => NAV[NAV.findIndex(n => n[1] === pg) - 1][1];
  const navClick = pg => [NAVT[pg] - 0.05, nav(prevPage(pg), NAVITEM[pg]), NAVT[pg] - 0.95, NAVT[pg] + 0.3];
  const CLICKS = [
    navClick("attendance"),
    [T.in, () => F("attendance", "punch"), T.in - 0.9, T.out + 0.6], [T.pause, () => F("attendance", "punch"), T.in, T.out + 0.6],
    [T.ret, () => F("attendance", "punch"), T.in, T.out + 0.6], [T.out, () => F("attendance", "punch"), T.in, T.out + 0.6],
    navClick("leaves"), navClick("absences"),
    [T.proof + 0.1, () => F("absences", "abs-upload"), T.proof - 0.6, T.absSend + 0.5], [T.absSend, () => F("absences", "abs-send"), T.proof, T.absSend + 0.5],
    navClick("sign"),
    [T.open, () => F("sign", "sign-open"), T.open - 0.75, T.open + 0.25],
    [T.draw, () => q(F("sign", "sign-tabs"), '[data-sign-mode="draw"]'), T.draw - 0.6, T.draw + 1.3],
    [T.code, () => F("sign", "sign-code-btn"), T.code - 0.6, T.signed + 0.4], [T.tape - 0.15, () => F("sign", "sign-code"), T.code, T.signed + 0.4],
    [T.mail + 0.3, () => F("sign", "sign-consent"), T.code, T.signed + 0.4], [T.signed, () => F("sign", "sign-confirm"), T.code, T.signed + 0.4],
    navClick("requests"),
    [T.fill - 0.2, () => q(F("requests", "req-cats"), "button"), T.fill - 0.8, T.clics + 0.5], [T.clics, () => F("requests", "req-send"), T.fill - 0.2, T.clics + 0.5],
    navClick("content"),
    [T.confirm, () => F("content", "note-check"), T.confirm - 0.7, T.lu + 0.5], [T.lu, () => F("content", "note-btn"), T.confirm, T.lu + 0.5],
    navClick("mail"),
    [T.mailSend, () => F("mail", "mail-send"), T.mailSend - 0.8, T.mailSend + 0.4],
    navClick("support"),
    [T.ticket - 0.1, () => F("support", "tick-send"), T.ticket - 0.8, T.ticket + 0.4],
    [NAVT.agent - 0.05, () => F("dashboard", "nav-dashboard"), NAVT.agent - 0.9, NAVT.agent + 0.2],
    [T.launch, () => F("agent", "agent-launcher"), NAVT.agent + 0.2, T.launch + 0.4],
    [T.askSend, () => F("agent", "agent-send"), T.launch + 0.4, T.askSend + 0.4],
    [T.okAgent, () => F("agent", "agent-confirm"), T.toi, T.okAgent + 0.6],
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

  // ------------------------------------------------------------------ états des écrans (libellés réels)
  function hhmm(m) { m = Math.round(m); return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); }
  function setValue(el, v, focus) {
    if (!el) return;
    if (el.value !== v) el.value = v;
    if (focus && el.ownerDocument.activeElement !== el) el.focus({ preventScroll: true });
    if (!focus && el.ownerDocument.activeElement === el) el.blur();
  }
  // signature dessinée : écriture manuscrite révélée au rythme de la plume, puis le paraphe, sur le vrai canvas
  let sigDrawn = -1;
  function drawSignature(cv, p) {
    const k = Math.round(p * 400);
    if (!cv || k === sigDrawn) return;
    sigDrawn = k;
    const c = cv.getContext("2d"), w = cv.width, hgt = cv.height;
    c.clearRect(0, 0, w, hgt);
    if (p <= 0) return;
    const pt = clamp(p / 0.8), pf = seg(p, 0.8, 1);
    c.save();
    c.translate(w / 2, hgt * 0.56); c.rotate(-0.05);
    c.font = "128px Z003, 'URW Chancery L', cursive";
    c.textAlign = "center"; c.textBaseline = "middle";
    const tw = c.measureText("A. Ndiaye").width;
    c.beginPath(); c.rect(-tw / 2 - 30, -hgt, (tw + 60) * pt, hgt * 2); c.clip();
    c.fillStyle = "#0b2a4d"; c.strokeStyle = "#0b2a4d"; c.lineWidth = 2.2;
    c.fillText("A. Ndiaye", 0, 0); c.strokeText("A. Ndiaye", 0, 0);
    c.restore();
    if (pf > 0) {                                   // paraphe
      c.save(); c.strokeStyle = "#0b2a4d"; c.lineWidth = 5; c.lineCap = "round";
      c.beginPath();
      const n = Math.round(60 * pf);
      for (let i = 0; i <= n; i++) {
        const u = i / 60, x = w * (0.2 + 0.62 * u), y = hgt * (0.86 - 0.06 * Math.sin(Math.PI * u)) - 22 * Math.pow(u, 6);
        i ? c.lineTo(x, y) : c.moveTo(x, y);
      }
      c.stroke(); c.restore();
    }
  }
  function screens(t) {
    // Mon espace : horloge
    const clk = F("dashboard", "clock");
    if (clk) { const s = 7 * 3600 + 28 * 60 + 40 + Math.max(0, Math.floor(t - T.winIn)); clk.innerHTML = `${hhmm(s / 60 - (s % 60) / 60)}<small>:${String(s % 60).padStart(2, "0")}</small>`; }
    // Pointage
    const stage = t < T.in ? 0 : t < T.pause ? 1 : t < T.ret ? 2 : t < T.out ? 3 : 4;
    const badge = F("attendance", "day-badge");
    if (badge) { setText(badge, ["Journée à commencer", "Au travail", "En pause", "Au travail", "Journée terminée"][stage]); badge.className = "mw-badge " + ["amber", "green", "amber", "green", ""][stage]; }
    const steps = F("attendance", "steps");
    if (steps) Array.from(steps.children).forEach((d, i) => { const done = [0, 1, 1, 2, 3][stage], curr = [0, 1, 1, 2, -1][stage]; d.className = i < done ? "complete" : i === curr ? "current" : ""; });
    setText(F("attendance", "punch-label"), ["Commencer ma journée", "Je pars en pause", "Je reviens de pause", "Terminer ma journée", "Journée terminée"][stage]);
    const punch = F("attendance", "punch");
    if (punch) { punch.style.opacity = stage === 4 ? "0.55" : "1"; press(punch, t, [T.in, T.pause, T.ret, T.out].reduce((a, b) => Math.abs(t - b) < Math.abs(t - a) ? b : a)); }
    ["07:28", "12:30", "13:30", "16:34"].forEach((v, i) => {
      const b = F("attendance", "today-" + i);
      setText(b, stage > i ? v : "—");
      if (b) glow(b.parentElement, Math.max(pulse(t, [T.in, T.pause, T.ret, T.out][i] + 0.05, 0.9), pulse(t, T.saved + 0.1 + 0.25 * i, 1.0)));
    });
    // Mes congés
    const met = F("leaves", "metrics");
    if (met) glow(met.firstElementChild, pulse(t, T.solde - 0.1, 1.6));
    glow(F("leaves", "seniority"), pulse(t, T.rights - 0.2, 2.4));
    // Mes absences
    const ab = D("absences");
    if (ab) {
      const [d0, d1] = ab.querySelectorAll('input[type="date"]');
      setValue(d0, t >= T.declare + 0.1 ? "2026-11-16" : ""); setValue(d1, t >= T.declare + 0.35 ? "2026-11-17" : "");
      setText(ab.querySelector('[data-duration="calendar"]'), t >= T.declare + 0.35 ? "2 jours" : "0 jour");
      const up = F("absences", "abs-upload"), got = t >= T.proof + 0.15;
      if (up) { setText(up.querySelector("b"), got ? "certificat-medical.pdf" : "Glissez et déposez votre fichier ici"); setText(up.querySelector("small"), got ? "PDF · 312 Ko · prêt à l’envoi" : "ou cliquez pour parcourir vos fichiers · PDF, JPG ou PNG · 5 Mo maximum"); glow(up, pulse(t, T.proof + 0.1, 1.0)); }
      FR.absences.contentWindow.scrollTo(0, Math.round(110 * E.inOutCubic(seg(t, T.proof + 0.2, T.absSend - 0.15)) * (1 - E.inOutCubic(seg(t, T.absSend + 0.3, T.rh)))));
      press(F("absences", "abs-send"), t, T.absSend);
      const n = F("absences", "abs-new");
      if (n) { n.hidden = t < T.absSend + 0.25; glow(n, Math.max(pulse(t, T.absSend + 0.3, 1.2), pulse(t, T.rh, 1.4))); }
      setText(F("absences", "abs-badge"), t >= T.rh ? "Vérification RH" : "Déclarée");
      const pr = F("absences", "abs-process");
      if (pr) Array.from(pr.children).forEach((s, i) => { s.className = (t >= T.rh ? i === 1 : i === 0) ? "current" : ""; });
    }
    // Signature (gabarit réel + parcours IT11)
    const sg = D("sign");
    if (sg) {
      const row = sg.querySelector(".mw-document-row");
      if (row) glow(row, pulse(t, NAVT.sign + 0.4, 1.4));
      press(F("sign", "sign-open"), t, T.open);
      glow(F("sign", "sign-open"), pulse(t, T.open - 0.4, 0.8));
      const dlg = F("sign", "sign-dialog"), openD = t >= T.open + 0.1 && t < T.signed + 0.3;
      if (dlg) {
        if (openD && !dlg.open) dlg.showModal(); if (!openD && dlg.open) dlg.close();
        const p = E.outCubic(seg(t, T.open + 0.1, T.open + 0.45)) * (1 - E.inCubic(seg(t, T.signed + 0.05, T.signed + 0.3)));
        dlg.style.opacity = p.toFixed(3); dlg.style.transform = `translateY(${(20 * (1 - p)).toFixed(1)}px) scale(${(0.97 + 0.03 * p).toFixed(4)})`;
        if (dlg.ownerDocument.activeElement && dlg.ownerDocument.activeElement.closest && dlg.ownerDocument.activeElement.closest(".mw-sign-close")) dlg.ownerDocument.activeElement.blur();
      }
      const drawMode = t >= T.draw;
      const tabs = F("sign", "sign-tabs");
      if (tabs) tabs.querySelectorAll("button").forEach(b => b.classList.toggle("selected", (b.dataset.signMode === "draw") === drawMode));
      const nm = F("sign", "sign-name-mode"), dm = F("sign", "sign-draw-mode");
      if (nm) nm.hidden = drawMode; if (dm) dm.hidden = !drawMode;
      const r1 = F("sign", "sign-style-1");
      if (r1 && r1.parentElement) glow(r1.parentElement, pulse(t, T.nom - 0.2, 1.0));
      glow(F("sign", "sign-preview"), pulse(t, T.nom - 0.1, 1.1));
      drawSignature(F("sign", "sign-canvas"), E.inOutSine(seg(t, T.draw + 0.15, T.code - 0.35)));
      const cb = F("sign", "sign-code-btn");
      if (cb) { setText(cb, t >= T.code + 0.05 ? "Renvoyer le code" : "Recevoir mon code par e-mail"); press(cb, t, T.code); }
      setValue(F("sign", "sign-code"), t >= T.tape - 0.1 ? "482913".slice(0, Math.round(6 * seg(t, T.tape - 0.1, T.tape + 0.4))) : "", t > T.tape - 0.15 && t < T.tape + 0.5);
      glow(F("sign", "sign-code"), pulse(t, T.tape + 0.35, 0.8));
      const cs = F("sign", "sign-consent");
      if (cs) cs.checked = t >= T.mail + 0.3;
      press(F("sign", "sign-confirm"), t, T.signed);
      const done = t >= T.signed + 0.3;
      const sb = F("sign", "sign-badge");
      if (sb) { setText(sb, done ? "Signé" : "À signer"); sb.className = "mw-badge " + (done ? "green" : "amber"); glow(sb, pulse(t, T.signed + 0.3, 1.0)); }
      const od = F("sign", "sign-on-doc");
      if (od) { setText(od, "A. Ndiaye"); od.style.fontSize = "19px"; }
      if (od) od.style.opacity = E.outCubic(seg(t, T.signed + 0.5, T.signed + 1.1)).toFixed(3);
      const ob = sg.querySelector(".mw-sign-open");
      if (ob) { ob.style.opacity = done ? "0.5" : "1"; }
      glow($("sign", ".mw-preview-stage"), pulse(t, T.signed + 0.6, 1.6));
    }
    // Mes demandes RH
    const cats = F("requests", "req-cats");
    if (cats) { const bs = cats.querySelectorAll("button"); glow(bs[0], Math.max(pulse(t, T.att, 0.9), pulse(t, T.fill - 0.2, 0.8))); glow(bs[1], pulse(t, T.question, 0.9)); }
    setValue(F("requests", "req-subject"), typed("Attestation de salaire", t, T.fill, T.fill + 0.35), t > T.fill - 0.05 && t < T.fill + 0.4);
    setValue(F("requests", "req-desc"), typed("Pour un dossier de location. Merci !", t, T.fill + 0.38, T.clics - 0.12), t > T.fill + 0.35 && t < T.clics);
    press(F("requests", "req-send"), t, T.clics);
    const rn = F("requests", "req-new");
    if (rn) { rn.hidden = t < T.clics + 0.2; glow(rn, Math.max(pulse(t, T.clics + 0.25, 1.0), pulse(t, T.process, 1.2))); }
    const rb = F("requests", "req-badge");
    if (rb) { const ok = t >= T.process; setText(rb, ok ? "En cours" : "Envoyée"); rb.className = "mw-badge" + (ok ? "" : " amber"); }
    // Contenu
    const ctab = D("content") && D("content").querySelectorAll(".mw-content-toolbar .mw-tab");
    if (ctab && ctab.length > 3) [T.dir, T.rhC].forEach((tt, i) => glow(ctab[i + 1], pulse(t, tt - 0.05, 0.8)));
    glow($("content", ".mw-note-body"), pulse(t, T.read - 0.1, 1.2));
    const chk = F("content", "note-check");
    if (chk) chk.checked = t >= T.confirm;
    press(F("content", "note-btn"), t, T.lu);
    const lu = t >= T.lu + 0.1;
    const nr = F("content", "note-read");
    if (nr) { setText(nr, lu ? "✓ Lu" : "● Non lu"); nr.className = "mw-badge " + (lu ? "green" : "blue"); }
    setText(F("content", "note-list-read"), lu ? "✓ Lu" : "● Non lu");
    glow(F("content", "note-confirm"), pulse(t, T.lu + 0.1, 1.2));
    // Mail
    const sent = t >= T.mailSend + 0.1;
    setValue(F("mail", "mail-input"), sent ? "" : typed("C’est confirmé : jeudi à 10 h, en salle de réunion à Ouakam.", t, NAVT.mail + 0.5, T.mailSend - 0.15), t > NAVT.mail + 0.45 && !sent);
    const rep = F("mail", "mail-reply");
    if (rep) { rep.hidden = !sent; rep.style.transform = `translateY(${(14 * (1 - E.outCubic(seg(t, T.mailSend + 0.1, T.mailSend + 0.5)))).toFixed(1)}px)`; }
    press(F("mail", "mail-send"), t, T.mailSend);
    // Support IT
    setValue(F("support", "tick-subject"), typed("Messagerie inaccessible", t, NAVT.support + 0.35, NAVT.support + 0.75), t > NAVT.support + 0.3 && t < NAVT.support + 0.8);
    setValue(F("support", "tick-desc"), typed("Je n’arrive plus à ouvrir ma messagerie depuis ce matin.", t, NAVT.support + 0.8, T.ticket - 0.2), t > NAVT.support + 0.75 && t < T.ticket);
    press(F("support", "tick-send"), t, T.ticket - 0.1);
    const tn = F("support", "tick-new");
    if (tn) { tn.hidden = t < T.ticket + 0.1; glow(tn, Math.max(pulse(t, T.ticket + 0.15, 1.0), pulse(t, T.charge, 1.4))); }
    const tb = F("support", "tick-badge");
    if (tb) { const ok = t >= T.charge; setText(tb, ok ? "Pris en charge" : "Envoyé"); tb.className = "mw-badge" + (ok ? "" : " amber"); }
    // Agent MyWebtel
    const ap = F("agent", "agent-panel"), al = F("agent", "agent-launcher");
    if (ap) {
      const o = E.outCubic(seg(t, T.launch + 0.05, T.launch + 0.45));
      ap.style.opacity = o.toFixed(3); ap.style.transform = `translateY(${(30 * (1 - o)).toFixed(1)}px)`;
      ap.style.visibility = o > 0.01 ? "visible" : "hidden";
      if (al) { al.style.opacity = (1 - o).toFixed(3); press(al, t, T.launch); glow(al, pulse(t, T.launch - 0.6, 0.8)); }
      const qTxt = "Il me reste combien de congés ? Je voudrais poser du 22 au 24 décembre.";
      const asked = t >= T.askSend + 0.1;
      setValue(F("agent", "agent-input"), asked ? "" : typed(qTxt, t, T.ask, T.askSend - 0.15), t > T.ask - 0.05 && !asked);
      const qa = F("agent", "agent-q"), qt = F("agent", "agent-q-text");
      if (qa) qa.hidden = !asked; setText(qt, qTxt);
      press(F("agent", "agent-send"), t, T.askSend);
      const chips = F("agent", "agent-chips");
      if (chips) Array.from(chips.children).forEach((c, i) => glow(c, pulse(t, T.chips[i] - 0.05, 0.8)));
      const aa = F("agent", "agent-a"), at = F("agent", "agent-a-text");
      const aTxt = "Il vous reste 24 jours sur la période du 01/06/2026 au 31/05/2027. J’ai préparé votre demande :";
      if (aa) aa.hidden = t < T.answer;
      setText(at, t < T.answer ? "" : (t < T.answer + 0.35 ? "•••" : typed(aTxt, t, T.answer + 0.35, T.prep - 0.05)));
      const pc = F("agent", "agent-prep");
      if (pc) { pc.hidden = t < T.prep; const e = enter(t, T.prep, 0.6, 16); pc.style.opacity = e.o.toFixed(3); pc.style.transform = `translateY(${e.y.toFixed(1)}px)`; glow(pc, pulse(t, T.prep + 0.1, 1.2)); }
      const pb = F("agent", "agent-prep-badge"), ok = t >= T.okAgent + 0.1;
      if (pb) { setText(pb, ok ? "✓ Demande envoyée" : "À confirmer"); pb.className = "mw-badge " + (ok ? "green" : "amber"); }
      const pa = F("agent", "agent-prep-actions");
      if (pa) pa.style.opacity = ok ? "0.45" : "1";
      press(F("agent", "agent-confirm"), t, T.okAgent);
      glow(F("agent", "agent-confirm"), pulse(t, T.toi, 1.2));
    }
  }
  function pagesAt(t) {
    let ci = 0;
    NAV.forEach((n, i) => { if (t >= n[0]) ci = i; });
    const [tn, id] = NAV[ci];
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

    // ouverture (reportage) : démarches dans la nuit, l'heure qui défile, la question
    const conv = seg(t, T.endroit - 0.2, T.logo - 0.4);
    const scatter = E.inOutCubic(seg(t, T.boulot - 0.1, T.boulot + 0.9)) * (1 - E.inOutCubic(seg(t, T.ques - 0.4, T.ques + 0.3)));
    TASKS.forEach((tk, i) => {
      const t0 = W(...tk[3]) - 0.12, sp = spring(t - t0, 0.7, 2.2), pull = E.inOutCubic(conv), drift = (t - t0) * 9;
      st(tasks[i], { x: 960 - 190 + tk[4] * (0.92 + 0.25 * scatter) * (1 - pull) + Math.sign(tk[4]) * drift * (1 - pull), y: 540 - 46 + tk[5] * (0.95 + 0.25 * scatter) * (1 - pull),
                     s: (1.15 + 0.25 * sp) * (1 - 0.75 * pull) * (1 - 0.15 * scatter), o: clamp(sp * 1.3) * (1 - 0.6 * scatter) * (1 - E.inCubic(seg(conv, 0.55, 1))),
                     blur: 10 * (1 - clamp(sp)) + 8 * pull + 5 * scatter, ry: tk[4] > 0 ? -8 : 8 });
    });
    // l'heure s'emballe (08:00 → 19:30) sur « un temps fou »
    const dg = seg(t, T.boulot, T.fou + 0.3), dgo = E.outCubic(seg(t, T.boulot - 0.1, T.boulot + 0.3)) * (1 - E.inCubic(seg(t, T.ques - 0.5, T.ques)));
    setText(digits, hhmm(480 + 690 * E.inOutCubic(dg)));
    st(digits, { o: 0.95 * dgo, s: 0.96 + 0.04 * dg, blur: 4 * (1 - dgo) });
    const fouTxt = "un temps <b>fou</b>.";
    kinFou.innerHTML = t < T.fou - 0.2 ? "" : fouTxt;
    st(kinFou, { o: E.outCubic(seg(t, T.fou - 0.2, T.fou + 0.2)) * (1 - E.inCubic(seg(t, T.ques - 0.5, T.ques))), y: 20 * (1 - E.outCubic(seg(t, T.fou - 0.2, T.fou + 0.3))) });
    // la question, tapée (pub Drive Academy) ; « même endroit » en cyan
    const qtxt = "Et si tout se faisait au même endroit ?", qn = Math.round(qtxt.length * seg(t, T.ques, T.endroit + 0.45));
    const qs = qtxt.slice(0, qn).replace("même endroit", "<b>même endroit</b>").replace(/même endr?o?i?t?$/, m => `<b>${m}</b>`);
    kinQ.innerHTML = qs + (t > T.ques && t < T.logo - 0.6 && Math.floor(t * 2.5) % 2 === 0 ? '<span class="caret"></span>' : "");
    st(kinQ, { o: seg(t, T.ques - 0.1, T.ques + 0.1) * (1 - E.inCubic(seg(t, T.logo - 0.9, T.logo - 0.4))), s: 1 + 0.03 * seg(t, T.ques, T.logo) });
    const sk = seg(t, T.logo - 1.1, T.logo - 0.05);
    st(spark, { o: Math.sin(Math.PI * sk) * 1.2, s: 0.3 + 2.6 * E.inCubic(sk) });
    st(flash, { o: 0.8 * Math.max(0, 1 - Math.abs(t - T.logo) / 0.35) });

    // fenêtre et caméra
    const winOn = t >= T.winIn - 0.2 && t < S0("fin") + 2.2;
    world.style.display = winOn ? "" : "none";
    let away = 0;
    if (winOn) {
      pagesAt(t); screens(t);
      const [c, aw] = cameraAt(t); away = aw;
      applyCamera(c);
      st(win, { o: 1 - E.inCubic(seg(t, T.end + 0.4, T.end + 1.9)) });
      win.style.filter = t > T.end + 0.3 ? `blur(${(8 * seg(t, T.end + 0.3, T.end + 1.4)).toFixed(2)}px)` : (away > 0.01 ? `blur(${(14 * away).toFixed(2)}px)` : "none");
    }
    // « Imprimer. Signer. Scanner ? » puis « Sauf que non. »
    st(paper, { o: 0.94 * away });
    const kk = [[".k1", T.kImp], [".k2", T.kSig], [".k3", T.kScan]];
    kk.forEach(([sel, tt]) => { const e = q(kinOld, sel), p = E.outCubic(seg(t, tt - 0.15, tt + 0.25)); e.style.opacity = p.toFixed(3); e.style.transform = `translateY(${(18 * (1 - p)).toFixed(1)}px)`; });
    kinOld.style.setProperty("--k", E.inOutCubic(seg(t, T.non + 0.15, T.non + 0.55)).toFixed(3));
    q(kinOld, ".k1 s").style.setProperty("--k", kinOld.style.getPropertyValue("--k"));
    qa(kinOld, "s").forEach(e => e.style.setProperty("--k", E.inOutCubic(seg(t, T.non + 0.15, T.non + 0.55)).toFixed(3)));
    st(kinOld, { o: away * seg(t, T.kImp - 0.3, T.kImp) });
    const de = E.outCubic(seg(t, T.doc - 0.1, T.doc + 0.35));
    st(kinDoc, { o: away * de * (1 - 0.55 * seg(t, T.kImp - 0.2, T.kImp + 0.2)), y: 16 * (1 - de) });
    kinNon.innerHTML = t >= T.non - 0.05 ? "Sauf que <b style=\"color:var(--blue)\">non.</b>" : "";
    st(kinNon, { o: away * E.outCubic(seg(t, T.non - 0.05, T.non + 0.25)), s: 0.92 + 0.08 * E.outBack2(seg(t, T.non - 0.05, T.non + 0.4)) });

    // logo
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
      const fly = E.inOutQuint(seg(t, T.winIn + 0.05, T.winIn + 1.35));
      let tx = 0, ty = 0, sc = 1;
      if (fly > 0 && winOn) {
        const img = $("dashboard", ".mw-brand img");
        const [x, y] = screenOf(img);
        const r = img.getBoundingClientRect();
        probe.style.left = r.left + "px"; probe.style.top = (CH + r.top) + "px";
        const a = probe.getBoundingClientRect();
        probe.style.left = r.right + "px";
        const b = probe.getBoundingClientRect();
        sc = lerp(1, (b.left - a.left) * 1.02 / LW, fly);
        tx = lerp(0, x - 960, fly); ty = lerp(0, y - 470, fly);
      }
      const handoff = seg(t, T.winIn + 1.15, T.winIn + 1.4);
      st(logo, { x: tx, y: ty, s: sc, o: (t >= T.logo - 0.3 ? 1 : 0) * (1 - handoff) });
      st(tag, { c: true, y: ty * 0.9, o: tp * (1 - E.outCubic(seg(t, T.winIn, T.winIn + 0.5))) });
      if (winOn) $("dashboard", ".mw-brand img").style.opacity = handoff.toFixed(3);
    } else {
      const tp = showLogo(T.final, W("fin", 0, "espace"));
      const end = seg(t, S1("fin") - 1.0, S1("fin") - 0.1);
      st(logo, { x: 0, y: 0, o: seg(t, T.final - 0.7, T.final - 0.2) * (1 - end), s: 1 + 0.025 * seg(t, T.final, S1("fin")) });
      st(tag, { c: true, y: 0, o: tp * (1 - end) });
    }
    cursorAt(t);

    // traits de lumière aux changements d'écran (bande-annonce, avec retenue) + halo derrière la fenêtre
    const navTimes = NAV.slice(1).map(n => n[0]);
    let sw = -1; navTimes.forEach(n => { if (t >= n - 0.25 && t < n + 0.45) sw = n; });
    light.innerHTML = sw < 0 ? "" : `<div class="streak" style="left:${(-400 + 2600 * E.inOutCubic(seg(t, sw - 0.25, sw + 0.45))).toFixed(0)}px;opacity:${(0.5 * Math.sin(Math.PI * seg(t, sw - 0.25, sw + 0.45))).toFixed(3)}"></div>`;
    const hOn = winOn ? E.outCubic(seg(t, T.winIn + 0.8, T.winIn + 2.0)) * (1 - seg(t, T.end, T.end + 0.8)) * (1 - away) : 0;
    st(halo, { o: 0.35 * hOn, r: (t * 12) % 360 });
    Object.assign(halo.style, { left: "330px", top: "150px", width: "1260px", height: "800px" });

    // badges ✓
    CHECKS.forEach(([id, , t0], i) => {
      const t1 = checkEnd(i), p = E.outBack2(seg(t, t0, t0 + 0.45)), o = seg(t, t0, t0 + 0.2) * (1 - seg(t, t1 - 0.25, t1));
      st(checks[id], { c: true, o, y: 26 * (1 - clamp(p)), s: 0.94 + 0.06 * clamp(p) });
    });
    // e-mail du code et toast de signature
    const me = E.outCubic(seg(t, T.mail - 0.15, T.mail + 0.35)), mo = 1 - E.inCubic(seg(t, T.signed - 0.3, T.signed));
    st(mailcard, { o: me * mo, y: -40 * (1 - me), x: 30 * (1 - me) });
    const te = E.outCubic(seg(t, T.signed + 0.35, T.signed + 0.75)), tz = 1 - seg(t, T.signed + 2.4, T.signed + 2.8);
    st(toast, { o: te * tz, x: -310, y: -20 * (1 - te) });

    // heure de la journée (pointage)
    const ck = [[T.in, 448], [T.pause, 750], [T.ret, 810], [T.out, 994]];
    let ci = -1; ck.forEach((c, i) => { if (t >= c[0] - 0.05) ci = i; });
    st(clock, { o: E.outCubic(seg(t, T.in - 0.5, T.in - 0.1)) * (1 - seg(t, NAVT.leaves - 0.4, NAVT.leaves)) });
    if (ci >= 0) { const prev = ci ? ck[ci - 1][1] : 448; setText(q(clock, ".ct"), hhmm(lerp(prev, ck[ci][1], E.inOutCubic(seg(t, ck[ci][0] - 0.05, ck[ci][0] + 0.35))))); }
    else setText(q(clock, ".ct"), "07:28");
  };
  E.outBack2 = x => { const c1 = 1.4, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  const qa = (root, sel) => Array.from(root.querySelectorAll(sel));
  // repères exportés pour les bruitages (render.js les écrit dans build/mywebtel/cues.json)
  window.FILM = { duration: TL.duration, T, clicks: CLICKS.map(c => c[0]), nav: NAV.slice(1).map(n => n[0]),
                  tasks: TASKS.map(tk => W(...tk[3]) - 0.12), checks: CHECKS.map(c => c[2]) };
  Promise.all([document.fonts.ready, ...loads]).then(() => {
    const imgs = Array.from(document.images).map(i => i.decode().catch(() => {}));
    Promise.all(imgs).then(() => { window.renderAt(0); window.READY = true; });
  });
})();
