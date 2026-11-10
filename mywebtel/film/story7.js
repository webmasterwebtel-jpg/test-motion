/* MyWebtel — film V7, mise en scène rythmée.
 * Retour de l'utilisateur sur la V6 : « un peu fade, on voit mal les interfaces, trop long, pas de musique entraînante,
 * il manque des mock-ups téléphone, tablette et PC ». La V7 garde la voix et montre chaque fonction sur un appareil
 * (vraie interface responsive : mise en page mobile sur le téléphone, tablette sur la tablette), en grand, avec un montage
 * calé sur une musique électro-pop à 120 BPM : mots clés qui claquent sur les temps, fouets de caméra entre les scènes,
 * drops sur les deux logos.
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
  const grade = add(stage, `<div id="grade"><div class="vignette"></div><div class="grain"></div><div class="flash"></div></div>`);
  const [vign, grain, flash] = grade.children;
  { const c = document.createElement("canvas"); c.width = c.height = 256; const g = c.getContext("2d"), im = g.createImageData(256, 256);
    for (let i = 0; i < im.data.length; i += 4) { const v = Math.floor(hash(i * 0.37) * 255); im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; }
    g.putImageData(im, 0, 0); grain.style.backgroundImage = `url(${c.toDataURL()})`; }
  const F0 = 1500;

  // ------------------------------------------------------------------ instants (mots de la voix)
  const w = (id, word, n = 0) => W(id, 0, word, n);
  Object.assign(T, {
    tag: w("reveal", "espace"),
    matin: w("pointage", "matin"), in: w("pointage", "clic") + 0.04, pause: w("pointage", "pause"), ret: w("pointage", "retour"),
    out: w("pointage", "départ"), saved: w("pointage", "enregistré"), minute: w("pointage", "minute"),
    cg: w("conges", "congés"), solde: w("conges", "solde"), rights: w("conges", "droits"), seniority: w("conges", "d'ancienneté"),
    abs: w("absences", "absence"), declare: w("absences", "déclares"), proof: w("absences", "justificatif"),
    absSend: w("absences", "et") - 0.04, rh: w("absences", "RH"),
    doc: w("signature", "document"), kImp: w("signature", "l'imprimer"), kSig: w("signature", "signer", 1), kScan: w("signature", "scanner"),
    non: w("signature", "Sauf"), nonW: w("signature", "non"), recv: w("signature", "reçois"), docs: w("signature", "documents"),
    open: w("signature", "signes") - 0.08, nom: w("signature", "nom"), draw: w("signature", "dessines") - 0.12,
    code: w("signature", "code"), mail: w("signature", "mail"), tape: w("signature", "tapes"), signed: w("signature", "signé") - 0.08,
    att: w("demandes", "attestation"), question: w("demandes", "question"), fill: w("demandes", "demande"), clics: w("demandes", "clics"),
    process: w("demandes", "traitement"),
    notes: w("contenu", "notes"), dir: w("contenu", "Direction"), rhC: w("contenu", "RH"), read: w("contenu", "lis"), confirm: w("contenu", "confirmes"),
    lu: w("contenu", "clic"),
    coll: w("mail", "collègues"), chat: w("mail", "échanges"), mailW: w("mail", "Mail"), souci: w("mail", "souci"),
    tick: w("mail", "support"), ticket: w("mail", "ticket"), charge: w("mail", "charge"),
    q: w("agent", "question"), launch: w("agent", "l'agent"), chips: [w("agent", "solde"), w("agent", "démarche"), w("agent", "souci")],
    answer: w("agent", "répond") - 0.1, prep: w("agent", "prépare"), toi: w("agent", "Toi"), okAgent: w("agent", "confirmer") + 0.05,
    finTag: w("fin", "espace"),
  });
  T.logo = segT("reveal"); T.final = segT("fin");                   // deux drops, sur un premier temps
  T.nonEnd = Math.ceil((T.nonW + 0.2) / BAR) * BAR;                  // les éclats tombent sur le retour du groove
  T.drawEnd = T.code - 0.3; T.consent = T.mail + 0.32; T.fileIn = T.proof + 0.55;
  T.ask = T.launch + 0.5; T.askSend = T.chips[0] - 0.12; T.agentSent = T.okAgent + 0.95; T.beamSupport = T.chips[2];
  T.mailType = T.chat - 0.05; T.mailSend = T.mailW + 0.42; T.tickType = T.tick + 0.3;
  const S = id => SC[id].start;
  // sections musicales (écrites par music7.py dans timeline.json) : pulsations de l'image sur la grosse caisse
  const MUS = (TL.music && TL.music.sections) || [];
  const kickOn = t => { const s = MUS[Math.floor(t / BAR)]; return s === "intro" || s === "drop" || s === "groove" || (s === "build" && (t % BAR) < 3 * BEAT); };
  const kickEnv = t => (kickOn(t) ? Math.exp(-((t % BEAT) / 0.11)) : 0);

  // ------------------------------------------------------------------ appareils (vraie interface dans chaque écran)
  const ST = { hero: 0, pt: 3600, cg: 7600, abs: 11800, sig: 16000, req: 20200, cnt: 23800, mail: 27600, agent: 32000, fin: 36800 };
  const DEV = [];
  function device(kind, page, extra = "") {
    const html = {
      phone: `<div class="dev phone"><div class="scr"></div><div class="island"></div><div class="btn" style="left:-5px;top:190px;height:70px"></div><div class="btn" style="left:-5px;top:280px;height:70px"></div><div class="btn" style="right:-5px;top:240px;height:110px"></div></div>`,
      tablet: `<div class="dev tablet"><div class="scr"></div><div class="cam"></div></div>`,
      laptop: `<div class="dev lid"><div class="scr"></div><div class="cam"></div></div>`,
    }[kind];
    const el = add(world, html);
    const size = { phone: [430, 884, 20, 20, 390, 844], tablet: [880, 1240, 30, 30, 820, 1180], laptop: [1530, 990, 45, 42, 1440, 900] }[kind];
    const [ow, oh, sx, sy, sw, sh] = size;
    const scr = q(el, ".scr");
    const f = frameFor(page, sw, sh);
    scr.appendChild(f);
    if (extra) scr.insertAdjacentHTML("beforeend", extra);
    const d = { kind, page, el, obj: new Obj(el, ow, oh), frame: f, sx, sy, sw, sh, scr };
    if (kind === "laptop") d.base = new Obj(add(world, `<div class="dev base"><div class="kb"></div><div class="pad"></div></div>`), 1800, 1060);
    DEV.push(d);
    return d;
  }
  // pose : x, y, z = centre de l'appareil (portable : charnière) ; ry/rx/rz en degrés ; s échelle
  function pose(d, { x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1, lean = 12, o = 1 } = {}) {
    opa(d.el, o); if (d.base) opa(d.base.el, o);
    if (o <= 0.002) return;
    const G = M4.chain(M4.T(x, y, z), M4.RY(ry), M4.RX(rx), M4.RZ(rz), M4.S(s));
    if (d.kind === "laptop") {
      d.obj.setM(M4.chain(G, M4.RX(lean), M4.T(-765, -990, 0)));
      d.base.setM(M4.chain(G, M4.RX(90), M4.T(-900, 0, 0)));
    } else d.obj.setM(M4.chain(G, M4.T(-d.obj.w / 2, -d.obj.h / 2, 0)));
  }
  const docD = d => d.frame.contentDocument;
  const scrPt = (d, u, v) => d.obj.world(d.sx + u, d.sy + v);                 // point de l'écran (px de la page) -> monde
  function elPt(d, sel, fx2 = 0.5, fy = 0.5) {
    const el = typeof sel === "string" ? docD(d).querySelector(sel) : sel;
    if (!el) return null;
    const r = el.getBoundingClientRect();
    if (!r.width && !r.height) return null;
    return project(scrPt(d, r.left + r.width * fx2, r.top + r.height * fy));
  }
  const film = n => `[data-film="${n}"]`;
  const scrollD = (d, y) => { const w2 = d.frame.contentWindow; if (w2 && Math.abs(w2.scrollY - y) > 0.5) w2.scrollTo(0, Math.round(y)); };

  const H = { L: device("laptop", "dashboard"), T: device("tablet", "dashboard"), P: device("phone", "dashboard") };
  const P1 = device("phone", "attendance");
  const L2 = device("laptop", "leaves");
  const T3 = device("tablet", "absences");
  const L4 = device("laptop", "sign");
  const P4 = device("phone", "dashboard", `<div class="notif"><i>W</i><div><b>MyWebtel · Votre code de signature</b><span>Code pour « Avenant au contrat » : <strong>482 913</strong></span></div></div>`);
  const P5 = device("phone", "requests");
  const T6 = device("tablet", "content");
  const L7 = device("laptop", "mail");
  const P7 = device("phone", "support");
  const L8 = device("laptop", "agent");
  const notif = q(P4.scr, ".notif");
  // fenêtre de signature sortie de l'écran du portable (copie de la page, découpée)
  const DLG = makeClip(world, "sign", "dialog", d => { const g = d.querySelector(film("sign-dialog")); g.showModal(); const r = rectEl(g); g.close(); return r; }, 0);
  const dlgHalo = new Obj(add(world, `<div class="halo"></div>`), 10, 10);

  // ------------------------------------------------------------------ logo, cartes, papier, éclats
  const LW = 1100, LH = Math.round(LW * 1224 / 3520);
  const logoEl = add(world, `<div style="width:${LW}px;height:${LH}px;transform-style:preserve-3d"></div>`);
  for (let i = 8; i >= 0; i--) logoEl.appendChild(h(`<img src="brand/webtel-logo${i ? "-depth" : ""}.svg" style="position:absolute;inset:0;width:100%;transform:translateZ(${-i * 2.6}px)${i ? ";filter:brightness(1.9) saturate(.35)" : ""}">`));
  const logo = new Obj(logoEl, LW, LH);
  const tagEl = add(world, `<div class="tagline" style="color:#3b5f86">${"MYWEBTEL · ESPACE COLLABORATEUR".split("").map(c => `<span>${c === " " ? "&nbsp;" : c}</span>`).join("")}</div>`);
  const tagline = new Obj(tagEl, 1000, 50);
  const subEl = add(world, `<div class="subline" style="color:#08264b">Pointage<i style="color:#008ff1">·</i>Congés<i style="color:#008ff1">·</i>Absences<i style="color:#008ff1">·</i>Signature<i style="color:#008ff1">·</i>Demandes RH<i style="color:#008ff1">·</i>Agent IA</div>`);
  const subline = new Obj(subEl, 1200, 50);
  const rule = new Obj(add(world, `<div class="rule"><div style="display:flex;align-items:center;gap:16px;font:600 30px Inter;color:#08264b">${ic("calendar")} Ancienneté</div>
    <div class="bar"><div class="fill"></div><div class="knob">${ic("lock")}</div></div><div class="ticks"><span>Arrivée</span><span>6 mois</span><b>1 an</b></div></div>`), 980, 270);
  const ruleFill = q(rule.el, ".fill"), ruleKnob = q(rule.el, ".knob");
  const pdf = new Obj(add(world, `<div class="pdf"><span class="tag">PDF</span><div class="l" style="width:90%"></div><div class="l"></div><div class="l" style="width:70%"></div><div class="l" style="width:84%"></div><b>certificat-medical.pdf</b></div>`), 300, 380);
  const orb = new Obj(add(world, `<div class="orb">${ic("spark")}</div>`), 300, 300);
  const SRC = [["calendar", "Mes congés", "24 jours disponibles"], ["req", "Démarches RH", "Demande préparée"], ["shield", "Support IT", "Tickets"]]
    .map(([i, a, b]) => new Obj(add(world, `<div class="src"><span class="ic">${ic(i)}</span><div>${a}<small>${b}</small></div></div>`), 470, 108));
  const SIG_W = 1640, SIG_H = 1100;
  const sigScene = fin => `<div style="position:absolute;left:0;top:0;width:${SIG_W}px;height:${SIG_H}px;border-radius:44px;background:linear-gradient(160deg,rgba(255,255,255,.98),rgba(236,244,253,.96));box-shadow:0 60px 140px rgba(4,27,52,.30),inset 0 0 0 2px rgba(255,255,255,.9)">
    <div class="kw" style="position:absolute;left:70px;top:58px;font-size:70px;color:#3b5576"><span class="w7">Un</span><span class="w8"><b>document</b></span><span class="w9">à</span><span class="w10">signer ?</span></div>
    <div class="kw" style="position:absolute;left:70px;top:190px;font-size:104px"><span class="w0"><b>Imprimer.</b></span></div>
    <div class="kw" style="position:absolute;left:70px;top:340px;font-size:104px"><span class="w1"><b>Signer.</b></span></div>
    <div class="kw" style="position:absolute;left:70px;top:490px;font-size:104px"><span class="w2"><b>Scanner</b></span><span class="w3">?</span></div>
    <div class="kw" style="position:absolute;left:70px;top:740px;font-size:126px"><span class="w4">Sauf</span><span class="w5">que</span><span class="w6"><b>non.</b></span></div>
    <div class="paper" style="position:absolute;left:830px;top:50px"><h5>AVENANT AU CONTRAT DE TRAVAIL</h5><div class="l" style="width:62%;margin-top:18px"></div>
      <div class="l" style="margin-top:46px"></div><div class="l"></div><div class="l" style="width:88%"></div><div class="l"></div><div class="l" style="width:76%"></div>
      <div class="l" style="margin-top:46px"></div><div class="l" style="width:92%"></div><div class="l" style="width:64%"></div>
      <svg viewBox="0 0 400 140" style="position:absolute;left:330px;top:760px;width:360px;overflow:visible"><path class="ink" d="M10 90 C 40 20, 70 20, 60 80 S 110 120, 130 60 S 170 10, 190 70 S 230 110, 250 60 C 262 30, 285 34, 292 78 S 330 100, 390 50" fill="none" stroke="#0b2a4d" stroke-width="7" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="${fin ? 0 : 1}"/></svg>
      ${fin ? "" : '<div class="scan"></div>'}</div></div>`;
  const sigSet = new Obj(add(world, `<div style="width:${SIG_W}px;height:${SIG_H}px">${sigScene(false)}</div>`), SIG_W, SIG_H);
  const sigWords = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(i => q(sigSet.el, ".w" + i));
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

  // ------------------------------------------------------------------ HUD : mots qui claquent, curseur, toucher, pastilles
  const SLAMS = [];
  function slam(html, t0, t1, { x = CX, y = CY, align = "center", cls = "", s = 1 } = {}) {
    const el = add(hud, `<div class="slam ${cls}">${html}</div>`);
    opa(el, 0);
    SLAMS.push({ el, t0, t1, x, y, align, s });
  }
  const CURSOR = `<svg class="cursor" viewBox="0 0 34 44"><path d="M3 2l26 24H16l7 14-5 2-7-14-8 8z" fill="#fff" stroke="#041b34" stroke-width="2.4" stroke-linejoin="round"/></svg>`;
  const cur = add(hud, CURSOR), rip = add(hud, `<div class="ripple"></div>`), touch = add(hud, `<div class="touch"></div>`);
  const subHud = add(hud, `<div class="subline" style="color:#08264b;font-weight:600">Pointage<i style="color:#008ff1">·</i>Congés<i style="color:#008ff1">·</i>Absences<i style="color:#008ff1">·</i>Signature<i style="color:#008ff1">·</i>Demandes RH<i style="color:#008ff1">·</i>Agent IA</div>`);
  opa(subHud, 0);
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

  let KEYS = [], CLICKS = [];
  const look = (P, zoom, o = {}) => camState(Object.assign({ tx: P[0], ty: P[1], tz: P[2], dist: F0 / zoom, yaw: 0, pitch: 3, roll: 0, F: F0 }, o));
  // poses fixes de chaque scène (le centre de l'appareil, en coordonnées monde)
  const POSE = {
    heroL: { x: 0, y: 330, z: 0 }, heroT: { x: -1260, y: 60, z: 380, ry: 26, s: 0.82 }, heroP: { x: 1220, y: 140, z: 480, ry: -26, s: 0.9 },
    P1: { x: ST.pt - 330, y: 0, z: 0, ry: 14 },
    L2: { x: ST.cg, y: 420, z: 0 },
    T3: { x: ST.abs + 330, y: 0, z: 0, ry: -12 },
    L4: { x: ST.sig, y: 420, z: 0 }, P4: { x: ST.sig + 860, y: 120, z: 640, ry: -18 },
    P5: { x: ST.req - 330, y: 0, z: 0, ry: 14 },
    T6: { x: ST.cnt + 330, y: 0, z: 0, ry: -12 },
    L7: { x: ST.mail - 700, y: 420, z: 0, ry: 10 }, P7: { x: ST.mail + 1500, y: 40, z: 300, ry: -16 },
    L8: { x: ST.agent, y: 420, z: 0 },
  };
  function setup() {
    for (const o of DEV) pose(o, { o: 0 });
    const k = (t, s, ease = E.inOutCubic) => KEYS.push([t, s, ease]);
    const whip = (tArrive, s) => { k(tArrive - 0.55, Object.assign({}, KEYS[KEYS.length - 1][1]), E.inOutSine); k(tArrive, s, E.inOutExpo); };
    // repères écran -> monde : on pose provisoirement chaque appareil pour calculer les cadrages
    const at = (d, ps, u, v) => { pose(d, Object.assign({}, ps, { o: 1 })); const P = scrPt(d, u, v); pose(d, { o: 0 }); return P; };
    // I. accroche (typographie) puis drop : le logo et les trois appareils
    const heroC = [0, -190, 300];
    k(0, look([0, -180, 300], 0.62, { pitch: 0 }));
    k(T.logo - 0.3, look([0, -180, 300], 0.66, { pitch: 0 }), E.inOutSine);
    k(T.logo + 0.9, look(heroC, 0.52, { pitch: 2, yaw: -3 }), E.outCubic);
    k(S("pointage") - 0.2, look(heroC, 0.5, { pitch: 3, yaw: 4 }), E.inOutSine);
    // II. pointage : le téléphone (gros plans sur le bouton puis sur « Aujourd'hui »)
    const sh = (P, px, zoom, dy = 0) => [P[0] + px / zoom, P[1] + dy, P[2]];      // décale la cible de px pixels écran
    const p1 = at(P1, POSE.P1, 195, 420), p1b = at(P1, POSE.P1, 195, 600);
    whip(S("pointage") + 0.35, look(sh(p1, 300, 1.15), 1.15, { yaw: -4 }));
    k(T.in - 0.25, look(sh(p1, 330, 1.5), 1.5, { yaw: -2 }), E.inOutCubic);
    k(T.out + 0.3, look(sh(p1, 330, 1.55), 1.55, { yaw: 2 }), E.inOutSine);
    k(T.saved + 0.4, look(sh(p1b, 330, 1.6), 1.6, { yaw: -2 }), E.inOutCubic);
    k(S("conges") - 0.2, look(sh(p1b, 330, 1.66), 1.66, { yaw: 3 }), E.inOutSine);
    // congés : le portable, gros plan sur le solde puis sur la règle d'ancienneté
    const l2 = at(L2, POSE.L2, 720, 450), l2m = at(L2, POSE.L2, 470, 262), l2s = at(L2, POSE.L2, 900, 300);
    whip(S("conges") + 0.35, look([l2[0], l2[1] - 40, l2[2]], 0.9, { pitch: 6 }));
    k(T.solde - 0.3, look(l2m, 2.1, { pitch: 3, yaw: -3 }), E.inOutCubic);
    k(T.rights - 0.4, look(l2m, 2.2, { pitch: 3, yaw: 2 }), E.inOutSine);
    k(T.rights + 0.25, look([l2s[0], l2s[1] + 60, l2s[2] + 130], 1.35, { pitch: 3, yaw: 4 }), E.inOutCubic);
    k(S("absences") - 0.2, look([l2s[0], l2s[1] + 60, l2s[2] + 130], 1.42, { pitch: 3, yaw: -2 }), E.inOutSine);
    // absences : la tablette (formulaire, justificatif, puis le suivi)
    const t3 = at(T3, POSE.T3, 410, 590), t3u = at(T3, POSE.T3, 505, 760), t3l = at(T3, POSE.T3, 505, 950);
    whip(S("absences") + 0.35, look(sh(t3, -330, 0.95), 0.95, { yaw: 3 }));
    k(T.declare - 0.2, look(sh(t3u, -300, 1.35), 1.35, { yaw: 2 }), E.inOutCubic);
    k(T.absSend + 0.2, look(sh(t3u, -300, 1.4), 1.4, { yaw: -2 }), E.inOutSine);
    k(T.rh + 0.1, look(sh(t3l, -300, 1.35), 1.35, { yaw: 2 }), E.inOutCubic);
    k(S("signature") - 0.2, look(sh(t3l, -300, 1.4), 1.4, { yaw: -2 }), E.inOutSine);
    // signature : composition « imprimer, signer, scanner », éclats, puis le portable et le téléphone
    const l4 = at(L4, POSE.L4, 720, 450), l4row = at(L4, POSE.L4, 620, 340), l4dlg = at(L4, POSE.L4, 720, 450);
    whip(S("signature") + 0.35, look([l4[0], l4[1] - 40, l4[2] + 900], 0.9, { pitch: 2 }));
    k(T.nonEnd, look([l4[0], l4[1] - 40, l4[2] + 900], 0.95, { pitch: 2, yaw: 1 }), E.inOutSine);
    k(T.recv + 0.3, look(l4row, 1.75, { pitch: 3, yaw: -3 }), E.inOutCubic);
    k(T.open + 0.05, look(l4row, 1.8, { pitch: 3, yaw: 2 }), E.inOutSine);
    k(T.nom - 0.1, look([l4dlg[0], l4dlg[1], l4dlg[2] + 170], 1.25, { pitch: 3, yaw: -2 }), E.inOutCubic);
    k(T.code - 0.25, look([l4dlg[0], l4dlg[1], l4dlg[2] + 170], 1.3, { pitch: 3, yaw: 1 }), E.inOutSine);
    k(T.mail + 0.2, look([l4dlg[0] + 330, l4dlg[1] - 10, l4dlg[2] + 300], 0.95, { pitch: 3, yaw: -4 }), E.inOutCubic);
    k(T.signed - 0.05, look([l4dlg[0] + 330, l4dlg[1] - 10, l4dlg[2] + 300], 0.97, { pitch: 3, yaw: 2 }), E.inOutSine);
    const l4pv = at(L4, POSE.L4, 1200, 480);
    k(T.signed + 0.6, look([l4pv[0] - 220, l4pv[1], l4pv[2]], 1.6, { pitch: 3, yaw: -2 }), E.inOutCubic);
    k(S("demandes") - 0.2, look([l4pv[0] - 220, l4pv[1], l4pv[2]], 1.66, { pitch: 3, yaw: 2 }), E.inOutSine);
    // demandes RH : le téléphone
    const p5 = at(P5, POSE.P5, 195, 360), p5b = at(P5, POSE.P5, 195, 560);
    whip(S("demandes") + 0.35, look(sh(p5, 300, 1.2), 1.2, { yaw: -4 }));
    k(T.fill - 0.2, look(sh(p5b, 330, 1.5), 1.5, { yaw: -2 }), E.inOutCubic);
    k(T.process + 0.2, look(sh(p5, 330, 1.5), 1.5, { yaw: 2 }), E.inOutCubic);
    k(S("contenu") - 0.2, look(sh(p5, 330, 1.56), 1.56, { yaw: -2 }), E.inOutSine);
    // contenu : la tablette
    const t6 = at(T6, POSE.T6, 410, 590), t6n = at(T6, POSE.T6, 600, 700);
    whip(S("contenu") + 0.35, look(sh(t6, -380, 1.0), 1.0, { yaw: 3 }));
    k(T.read - 0.2, look(sh(t6n, -480, 1.35), 1.35, { yaw: 2 }), E.inOutCubic);
    k(S("mail") - 0.2, look(sh(t6n, -480, 1.4), 1.4, { yaw: -2 }), E.inOutSine);
    // mail et support : le portable puis le téléphone
    const l7 = at(L7, POSE.L7, 1010, 560), p7 = at(P7, POSE.P7, 195, 460);
    whip(S("mail") + 0.35, look(l7, 1.45, { yaw: 5, pitch: 3 }));
    k(T.souci - 0.3, look(l7, 1.5, { yaw: 2, pitch: 3 }), E.inOutSine);
    k(T.tick + 0.1, look(sh(p7, -300, 1.35), 1.35, { yaw: -5, pitch: 2 }), E.inOutExpo);
    k(S("agent") - 0.2, look(sh(p7, -300, 1.4), 1.4, { yaw: -2, pitch: 2 }), E.inOutSine);
    // agent : le portable dans la nuit, l'étincelle, les sources
    const l8 = at(L8, POSE.L8, 720, 450), l8p = at(L8, POSE.L8, 1177, 480);
    whip(S("agent") + 0.35, look([l8[0], l8[1] - 60, l8[2]], 0.6, { pitch: 3 }));
    k(T.launch - 0.1, look([l8[0], l8[1] - 60, l8[2]], 0.64, { pitch: 3, yaw: -2 }), E.inOutSine);
    k(T.ask + 0.3, look([l8p[0] - 90, l8p[1] + 200, l8p[2] + 100], 1.75, { pitch: 3, yaw: -4 }), E.inOutCubic);
    k(T.chips[0] - 0.1, look([l8[0], l8[1] - 60, l8[2]], 0.56, { pitch: 3, yaw: 3 }), E.inOutCubic);
    k(T.answer - 0.15, look([l8[0], l8[1] - 60, l8[2]], 0.58, { pitch: 3, yaw: -3 }), E.inOutSine);
    k(T.answer + 0.35, look([l8p[0] - 90, l8p[1] + 120, l8p[2] + 100], 1.7, { pitch: 3, yaw: -2 }), E.inOutCubic);
    k(T.okAgent + 0.3, look([l8p[0] - 90, l8p[1] + 120, l8p[2] + 100], 1.76, { pitch: 3, yaw: 2 }), E.inOutSine);
    k(T.final - 0.6, look([l8[0], l8[1] - 60, l8[2] - 400], 0.45, { pitch: 3, yaw: 6 }), E.inOutQuart);
    // III. drop final : les trois appareils et le logo
    const finC = [ST.fin, -190, 300];
    k(T.final - 0.05, look(finC, 0.3, { pitch: 0 }), E.inExpo);
    k(T.final + 0.9, look(finC, 0.52, { pitch: 2, yaw: -4 }), E.outExpo);
    k(TL.duration, look(finC, 0.55, { pitch: 3, yaw: 4 }), E.inOutSine);
    KEYS.sort((a, b) => a[0] - b[0]);

    // mots qui claquent (HUD) : [html, début, fin, options]
    const ink = { cls: "ink" };
    slam(`<span class="tile">${ic("clock")}</span>Pointer.`, 0.0, w("hook", "poser") - 0.06);
    slam(`<span class="tile">${ic("calendar")}</span>Poser un <b>congé.</b>`, w("hook", "poser") - 0.06, w("hook", "retrouver") - 0.06);
    slam(`<span class="tile">${ic("file")}</span>Ta <b>fiche de paie.</b>`, w("hook", "retrouver") - 0.06, w("hook", "signer") - 0.06);
    slam(`<span class="tile">${ic("pen")}</span>Signer un <b>document.</b>`, w("hook", "signer") - 0.06, w("hook", "Au") - 0.06);
    slam(`Un temps <b>fou.</b>`, w("hook", "temps") - 0.06, SC.hook.segs[1].start - 0.15, { y: 760 });
    slam(`Et si tout se faisait`, SC.hook.segs[1].start - 0.05, T.logo - 0.12, { y: 470, cls: "sm" });
    slam(`au <b>même endroit ?</b>`, W("hook", 1, "même") - 0.06, T.logo - 0.12, { y: 610, cls: "sm" });
    slam(`Un <b>clic.</b>`, T.in - 0.05, T.pause - 0.12, { x: 1140, align: "left", cls: "vv" });
    slam(`<b>Pause.</b>`, T.pause - 0.05, T.ret - 0.08, { x: 1140, align: "left", cls: "vv" });
    slam(`<b>Retour.</b>`, T.ret - 0.05, T.out - 0.08, { x: 1140, align: "left", cls: "vv" });
    slam(`<b>Départ.</b>`, T.out - 0.05, T.saved - 0.2, { x: 1140, align: "left", cls: "vv" });
    slam(`À la <b>minute</b><br><b>près.</b>`, w("pointage", "à") - 0.05, S("conges") - 0.25, { x: 1140, y: 520, align: "left", cls: "vv" });
    slam(`+ <b>justificatif</b>`, T.proof - 0.05, T.rh - 0.2, { x: 120, y: 470, align: "left", cls: "sm" });
    slam(`Les RH<br><b>s’en occupent.</b>`, T.rh - 0.05, S("signature") - 0.25, { x: 120, y: 470, align: "left", cls: "sm" });
    slam(`<b>Signé.</b>`, T.signed + 0.05, S("demandes") - 0.25, Object.assign({ x: 140, y: 860, align: "left" }, ink));
    slam(`En <b>deux</b><br><b>clics.</b>`, w("demandes", "en") - 0.05, S("contenu") - 0.25, { x: 1140, y: 500, align: "left", cls: "vv" });
    slam(`En <b>un clic.</b>`, w("contenu", "en") - 0.05, S("mail") - 0.25, Object.assign({ x: 120, y: 520, align: "left" }, ink));
    slam(`Pris en<br><b>charge.</b>`, w("mail", "prend") - 0.05, S("agent") - 0.25, { x: 140, y: 520, align: "left" });
    // pastilles ✓
    check("Enregistré à la minute près", T.minute + 0.1, S("conges") - 0.25);
    check("Droits ouverts après 1 an d’ancienneté", T.seniority + 0.2, S("absences") - 0.25);
    check("Document signé", T.signed + 0.45, S("demandes") - 0.25);
    check("Rien n’est envoyé sans ta confirmation", T.okAgent + 0.35, T.final - 0.7);

    // gestes : [instant, point écran(), visible de, à, mode] (mode : souris ou doigt)
    const E2 = (d, sel, fx2, fy) => () => elPt(d, sel, fx2, fy);
    CLICKS = [
      [T.in, E2(P1, film("punch")), T.in - 0.5, T.out + 0.35, "touch"], [T.pause, E2(P1, film("punch")), T.in, T.out + 0.35, "touch"],
      [T.ret, E2(P1, film("punch")), T.in, T.out + 0.35, "touch"], [T.out, E2(P1, film("punch")), T.in, T.out + 0.35, "touch"],
      [T.absSend, E2(T3, film("abs-send")), T.absSend - 0.6, T.absSend + 0.4, "touch"],
      [T.open, E2(L4, film("sign-open")), T.open - 0.75, T.open + 0.3, "mouse"],
      [T.draw, () => dlgPt('[data-film="sign-tabs"] [data-sign-mode="draw"]'), T.draw - 0.6, T.draw + 1.1, "mouse"],
      [T.code, () => dlgPt(film("sign-code-btn")), T.code - 0.6, T.signed + 0.35, "mouse"], [T.tape - 0.15, () => dlgPt(film("sign-code")), T.code, T.signed + 0.35, "mouse"],
      [T.consent, () => dlgPt(film("sign-consent")), T.code, T.signed + 0.35, "mouse"], [T.signed, () => dlgPt(film("sign-confirm")), T.code, T.signed + 0.35, "mouse"],
      [T.fill - 0.2, E2(P5, film("req-cats") + " button"), T.fill - 0.7, T.clics + 0.45, "touch"], [T.clics, E2(P5, film("req-send")), T.fill - 0.2, T.clics + 0.45, "touch"],
      [T.confirm, E2(T6, film("note-check")), T.confirm - 0.6, T.lu + 0.4, "touch"], [T.lu, E2(T6, film("note-btn")), T.confirm, T.lu + 0.4, "touch"],
      [T.mailSend, E2(L7, film("mail-send")), T.mailSend - 0.7, T.mailSend + 0.35, "mouse"],
      [T.ticket - 0.1, E2(P7, film("tick-send")), T.ticket - 0.7, T.ticket + 0.35, "touch"],
      [T.askSend, E2(L8, film("agent-send")), T.askSend - 0.7, T.askSend + 0.3, "mouse"],
      [T.okAgent, E2(L8, film("agent-confirm")), T.toi - 0.1, T.okAgent + 0.5, "mouse"],
    ].sort((a, b) => a[0] - b[0]);
    window.FILM = { duration: TL.duration, T, clicks: CLICKS.map(c => c[0]), touches: CLICKS.filter(c => c[4] === "touch").map(c => c[0]),
                    whips: KEYS.filter(k2 => k2[2] === E.inOutExpo).map(k2 => k2[0]), slams: SLAMS.map(s2 => s2.t0), checks: CHECKS.map(c => c.t0) };
  }
  function dlgPt(sel) {                                     // point d'un élément de la fenêtre de signature sortie de l'écran
    const el = docOf("sign").querySelector(sel);
    if (!el || !DLG.rect) return null;
    const r = el.getBoundingClientRect();
    return DLG.screen(r.left + r.width / 2 - DLG.rect.x, r.top + r.height / 2 - DLG.rect.y);
  }

  function cameraAt(t) {
    let i = 0;
    while (i < KEYS.length - 1 && KEYS[i + 1][0] <= t) i++;
    if (i >= KEYS.length - 1) return Object.assign({}, KEYS[KEYS.length - 1][1]);
    const [t0, s0] = KEYS[i], [t1, s1, ease] = KEYS[i + 1];
    const s = lerpCam(s0, s1, ease(seg(t, t0, t1)));
    s.yaw += 0.4 * noise1(t * 0.31, 1); s.pitch += 0.3 * noise1(t * 0.27, 2); s.roll += 0.25 * noise1(t * 0.23, 3);
    const kb = kickEnv(t);                                    // la caméra respire sur la grosse caisse
    s.dist *= 1 - 0.006 * kb;
    for (const td of [T.logo, T.nonEnd, T.final]) {           // secousse brève sur les trois impacts
      const u = t - td;
      if (u > 0 && u < 0.6) { const a = Math.exp(-u / 0.12); s.yaw += 0.9 * a * Math.sin(u * 61); s.pitch += 0.7 * a * Math.sin(u * 47 + 1); s.roll += 0.6 * a * Math.sin(u * 53 + 2); }
    }
    return s;
  }

  // ------------------------------------------------------------------ fond : couleur de la scène, taches de lumière, grille de points
  const PAL = {
    navy: [[4, 27, 52], [8, 46, 86], [5, 218, 240]],
    light: [[236, 244, 252], [255, 255, 255], [0, 143, 241]],
    vivid: [[0, 120, 230], [5, 200, 240], [255, 255, 255]],
  };
  const BGSEQ = [[0, "navy"], [T.logo - 0.4, "light"], [S("pointage") + 0.1, "vivid"], [S("conges") + 0.1, "light"], [S("absences") + 0.1, "navy"],
                 [S("signature") + 0.1, "light"], [S("demandes") + 0.1, "vivid"], [S("contenu") + 0.1, "light"], [S("mail") + 0.1, "navy"],
                 [T.final - 0.4, "light"]];
  function palAt(t) {
    let i = 0; while (i < BGSEQ.length - 1 && BGSEQ[i + 1][0] <= t) i++;
    const cur2 = PAL[BGSEQ[i][1]];
    if (i === 0) return [cur2, BGSEQ[i][1]];
    const prev = PAL[BGSEQ[i - 1][1]], p = E.inOutCubic(seg(t, BGSEQ[i][0], BGSEQ[i][0] + 0.3));
    return [cur2.map((c, k2) => c.map((v, j) => lerp(prev[k2][j], v, p))), BGSEQ[i][1]];
  }
  function background(t) {
    const [[a, b, glowc], name] = palAt(t);
    const g = bg.createLinearGradient(0, 0, VW, VH);
    g.addColorStop(0, `rgb(${a.map(Math.round)})`); g.addColorStop(1, `rgb(${b.map(Math.round)})`);
    bg.globalAlpha = 1; bg.fillStyle = g; bg.fillRect(0, 0, VW, VH);
    const off = -cam.C[0] * 0.08;                            // parallaxe : le fond file pendant les fouets
    bg.globalCompositeOperation = name === "light" ? "source-over" : "lighter";
    for (let k2 = 0; k2 < 4; k2++) {
      const x = ((k2 * 610 + off * (0.6 + 0.2 * k2) + 200 * Math.sin(t * 0.3 + k2)) % (VW + 1200) + VW + 1200) % (VW + 1200) - 600;
      const y = 300 + 420 * Math.sin(t * 0.21 + k2 * 1.7);
      const r = 520 + 120 * k2;
      const rg = bg.createRadialGradient(x, y, 0, x, y, r);
      const al = (name === "light" ? 0.10 : 0.16) * (1 + 0.6 * kickEnv(t));
      rg.addColorStop(0, `rgba(${glowc.map(Math.round)},${al.toFixed(3)})`); rg.addColorStop(1, `rgba(${glowc.map(Math.round)},0)`);
      bg.fillStyle = rg; bg.fillRect(x - r, y - r, 2 * r, 2 * r);
    }
    bg.globalCompositeOperation = "source-over";
    // grille de points
    const step = 46, ox = ((off % step) + step) % step;
    bg.fillStyle = name === "light" ? "rgba(0,110,220,.10)" : "rgba(255,255,255,.10)";
    for (let y = 18; y < VH; y += step) for (let x = ox - step; x < VW + step; x += step) bg.fillRect(x, y, 2.4, 2.4);
  }
  // anneau lumineux (repris de la V6) et fils
  function ring2(P, radius, alpha, spin, color = "rgba(5,218,240,1)") {
    if (alpha < 0.01) return;
    fx.globalCompositeOperation = "lighter";
    const ptsAt = (rad, a0 = 0, a1 = Math.PI * 2, n = 140) => Array.from({ length: n + 1 }, (_, i) => {
      const a = a0 + (a1 - a0) * i / n; return V3.add(P, V3.add(V3.mul(cam.r, Math.cos(a) * rad), V3.mul(cam.d, Math.sin(a) * rad)));
    });
    const stroke = (arr, col, width, al, glow) => {
      const ps = arr.map(p => project(p, 20)).filter(Boolean); if (ps.length < 2) return;
      fx.globalAlpha = al; fx.strokeStyle = col; fx.lineWidth = width; fx.shadowColor = col; fx.shadowBlur = glow;
      fx.beginPath(); ps.forEach((p, i) => (i ? fx.lineTo(p[0], p[1]) : fx.moveTo(p[0], p[1]))); fx.stroke();
    };
    stroke(ptsAt(radius), color, 7, alpha, 40);
    for (let k2 = 0; k2 < 3; k2++) { const a0 = spin * (k2 % 2 ? -1 : 1) + k2 * 2.1; stroke(ptsAt(radius * (0.9 + 0.05 * k2), a0, a0 + 1.2, 40), "rgba(200,250,255,1)", 3, alpha * 0.8, 20); }
    fx.shadowBlur = 0; fx.globalCompositeOperation = "source-over";
  }
  function thread(A, B, lift, p, alpha, color = "rgba(5,218,240,1)", width = 5) {
    if (p <= 0 || alpha < 0.01) return;
    const n = 40, pts = [];
    for (let i = 0; i <= n * p; i++) { const u = i / n; const pr = project([lerp(A[0], B[0], u), lerp(A[1], B[1], u) - lift * Math.sin(Math.PI * u), lerp(A[2], B[2], u)], 20); if (pr) pts.push(pr); }
    if (pts.length < 2) return;
    fx.globalCompositeOperation = "lighter"; fx.globalAlpha = alpha; fx.strokeStyle = color; fx.lineWidth = width; fx.shadowColor = color; fx.shadowBlur = 24;
    fx.beginPath(); pts.forEach((q2, i) => (i ? fx.lineTo(q2[0], q2[1]) : fx.moveTo(q2[0], q2[1]))); fx.stroke();
    const e = pts[pts.length - 1]; fx.drawImage(sprite("rgba(210,250,255,1)"), e[0] - 30, e[1] - 30, 60, 60);
    fx.shadowBlur = 0; fx.globalCompositeOperation = "source-over";
  }

  // ------------------------------------------------------------------ curseur et doigt
  function cursorAt(t) {
    let k2 = -1;
    for (let i = 0; i < CLICKS.length; i++) if (t >= CLICKS[i][2] - 0.25 && t <= CLICKS[i][3] + 0.25 && (k2 < 0 || CLICKS[i][0] <= t + 0.75)) k2 = i;
    if (k2 < 0) { opa(cur, 0); opa(rip, 0); opa(touch, 0); return; }
    const [tc, get, v0, v1, mode] = CLICKS[k2];
    const p1 = get();
    if (!p1) { opa(cur, 0); opa(rip, 0); opa(touch, 0); return; }
    let p0 = [p1[0] + 170, p1[1] + 130];
    if (k2 > 0 && CLICKS[k2 - 1][3] >= v0 - 0.3 && CLICKS[k2 - 1][0] < tc) { const pp = CLICKS[k2 - 1][1](); if (pp) p0 = pp; }
    const p = E.inOutCubic(seg(t, Math.max(v0, tc - 0.6), tc - 0.06));
    const x = lerp(p0[0], p1[0], p), y = lerp(p0[1], p1[1], p);
    const vis = Math.min(seg(t, v0 - 0.2, v0), 1 - seg(t, v1, v1 + 0.2));
    const pr = Math.max(0, 1 - Math.abs(t - tc) / 0.1);
    if (mode === "touch") {
      opa(cur, 0);
      touch.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) scale(${(1 - 0.25 * pr).toFixed(3)})`;
      opa(touch, vis * (0.35 + 0.65 * Math.max(pr, seg(t, tc - 0.3, tc) * (1 - seg(t, tc + 0.05, tc + 0.3)))));
    } else {
      opa(touch, 0);
      cur.style.transform = `translate(${(x - 3).toFixed(1)}px,${(y - 2).toFixed(1)}px) scale(${(1 - 0.14 * pr).toFixed(3)})`;
      opa(cur, vis);
    }
    const r = seg(t, tc, tc + 0.5);
    rip.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) scale(${(0.3 + 1.1 * E.outCubic(r)).toFixed(3)})`;
    opa(rip, r > 0 && r < 1 ? (1 - r) * 0.9 : 0);
  }

  // ------------------------------------------------------------------ image à l'instant t
  const vis = (t, a, b) => t > a - 0.7 && t < b + 0.7;
  window.renderAt = function (t) {
    applyStates(t);
    const s = cameraAt(t);
    solveCamera(s);
    viewport.style.perspective = s.F.toFixed(1) + "px";
    const css = M4.css(cam.view);
    if (world.__css !== css) { world.style.transform = css; world.__css = css; }
    bg.setTransform(1, 0, 0, 1, 0, 0); fx.setTransform(1, 0, 0, 1, 0, 0);
    fx.clearRect(0, 0, VW, VH);
    background(t);
    const kb = kickEnv(t);
    const bump = 1 + 0.008 * kb;

    // ---------------- drop : les trois appareils montent autour du logo (puis reviennent pour la fin)
    const heroOn = (t >= T.logo + 0.3 && t < S("pointage") + 0.7) || t >= T.final - 0.1;
    const heroX = t >= T.final - 0.1 ? ST.fin : 0;
    const ent = t >= T.final - 0.1 ? T.final + 0.55 : T.logo + 0.5;
    [[H.L, "heroL", 0], [H.T, "heroT", 0.1], [H.P, "heroP", 0.18]].forEach(([d, k2, dl]) => {
      if (!heroOn) { pose(d, { o: 0 }); return; }
      const p = E.outBack(seg(t, ent + dl, ent + dl + 0.7)), ps = POSE[k2];
      pose(d, Object.assign({}, ps, { x: ps.x + heroX, y: ps.y + 1300 * (1 - p), rx: -25 * (1 - p), ry: (ps.ry || 0) * (0.4 + 0.6 * p), s: (ps.s || 1) * bump, o: clamp(seg(t, ent + dl - 0.05, ent + dl + 0.15)) }));
    });
    // logo : il claque sur le drop, puis se range au-dessus des appareils
    const logoOn = (t >= T.logo - 0.05 && t < S("pointage") + 0.6) || t >= T.final - 0.05;
    if (logoOn) {
      const t0 = t >= T.final - 0.05 ? T.final : T.logo, X = t >= T.final - 0.05 ? ST.fin : 0, tg = t >= T.final - 0.05 ? T.finTag : T.tag;
      const sl = E.outBack(seg(t, t0 - 0.03, t0 + 0.35)), up = E.inOutCubic(seg(t, t0 + 0.35, t0 + 0.95));
      logo.place({ x: X, y: lerp(-180, -1000, up), z: lerp(900, 380, up), bill: true, s: (1.6 - 0.6 * sl) * lerp(1, 0.72, up) });
      opa(logo.el, clamp(seg(t, t0 - 0.05, t0 + 0.05))); blur(logo.el, 12 * (1 - clamp(sl)));
      tagline.place({ x: X, y: -810, z: 380, bill: true, s: 1 });
      opa(tagline.el, seg(t, tg - 0.25, tg));
      qa(tagEl, "span").forEach((sp, i) => { const p = E.outCubic(seg(t, tg - 0.2 + i * 0.02, tg + 0.2 + i * 0.02)); sp.style.opacity = p.toFixed(2); sp.style.transform = `translateY(${(-26 * (1 - p)).toFixed(1)}px)`; });
      const fin = t >= T.final - 0.05;
      opa(subEl, 0);
      opa(subHud, fin ? seg(t, T.finTag + 0.6, T.finTag + 1.3) : 0);
      if (fin) subHud.style.transform = `translate(${(CX - subHud.offsetWidth / 2).toFixed(1)}px, ${(1000 - 12 * (1 - seg(t, T.finTag + 0.6, T.finTag + 1.3))).toFixed(1)}px)`;
      ring2([X, -180, 900], 520 + 900 * E.outExpo(seg(t, t0, t0 + 0.9)), 0.9 * (1 - seg(t, t0 + 0.1, t0 + 0.9)), t * 2);
    } else { opa(logo.el, 0); opa(tagline.el, 0); opa(subEl, 0); opa(subHud, 0); }

    // ---------------- pointage (téléphone)
    if (vis(t, S("pointage"), S("conges"))) {
      pose(P1, Object.assign({}, POSE.P1, { s: bump, ry: POSE.P1.ry + 4 * Math.sin(t * 0.6) }));
      scrollD(P1, 150 * E.inOutCubic(seg(t, T.saved - 0.3, T.saved + 0.4)));
    } else pose(P1, { o: 0 });
    // congés (portable) + frise d'ancienneté
    if (vis(t, S("conges"), S("absences"))) {
      pose(L2, Object.assign({}, POSE.L2, { s: bump }));
      const ra = bump2(t, T.rights - 0.2, T.rights + 0.25, S("absences") - 0.4, S("absences"));
      opa(rule.el, ra);
      if (ra > 0.01) {
        const P = scrPt(L2, 900, 470);
        rule.place({ x: P[0], y: P[1] + 40 * (1 - E.outBack(seg(t, T.rights - 0.2, T.rights + 0.3))), z: P[2] + 260, s: 1.05 });
        const f = E.inOutCubic(seg(t, T.rights + 0.1, T.seniority + 0.15));
        ruleFill.style.width = (100 * f).toFixed(1) + "%"; ruleKnob.style.left = (100 * f).toFixed(1) + "%";
        setHTML(ruleKnob, ic(t >= T.seniority + 0.1 ? "unlock" : "lock")); ruleKnob.style.color = t >= T.seniority + 0.1 ? "#129266" : "#008ff1";
      }
    } else { pose(L2, { o: 0 }); opa(rule.el, 0); }
    // absences (tablette) + justificatif qui arrive en volant
    if (vis(t, S("absences"), S("signature"))) {
      pose(T3, Object.assign({}, POSE.T3, { s: bump, ry: POSE.T3.ry - 3 * Math.sin(t * 0.6) }));
      scrollD(T3, 130 * E.inOutCubic(seg(t, T.absSend + 0.2, T.rh - 0.05)));
      const pa = bump2(t, T.proof - 0.25, T.proof + 0.05, T.fileIn, T.fileIn + 0.12);
      opa(pdf.el, pa);
      if (pa > 0.01) {
        const up = docD(T3).querySelector(film("abs-upload")).getBoundingClientRect();
        const P1w = scrPt(T3, up.left + up.width / 2, up.top + up.height / 2), P2w = [P1w[0] - 1300, P1w[1] - 500, P1w[2] + 700];
        const f = E.inOutCubic(seg(t, T.proof - 0.25, T.fileIn));
        const Pp = mix3(P2w, [P1w[0], P1w[1], P1w[2] + 40], f);
        pdf.place({ x: Pp[0], y: Pp[1], z: Pp[2], rz: -16 * (1 - f), ry: 30 * (1 - f), s: 1.2 - 0.6 * f });
      }
    } else { pose(T3, { o: 0 }); opa(pdf.el, 0); }
    // signature : composition, éclats, portable, fenêtre sortie, téléphone avec le code
    const sigOn = vis(t, S("signature"), S("demandes"));
    if (sigOn) {
      pose(L4, Object.assign({}, POSE.L4, { s: bump, o: clamp(seg(t, T.nonEnd - 0.1, T.nonEnd + 0.05)) }));
      const pIn = E.outBack(seg(t, T.code - 0.15, T.code + 0.45)), pOut = E.inCubic(seg(t, T.signed + 0.5, T.signed + 0.9));
      pose(P4, Object.assign({}, POSE.P4, { x: POSE.P4.x + 1200 * (1 - pIn) + 1400 * pOut, ry: POSE.P4.ry - 30 * (1 - pIn), s: bump, o: pIn > 0.001 && pOut < 0.999 ? 1 : 0 }));
      const nIn = E.outBack(seg(t, T.mail - 0.1, T.mail + 0.3));
      notif.style.transform = `translateY(${(-160 * (1 - nIn)).toFixed(1)}px)`; notif.style.opacity = clamp(nIn * 1.5).toFixed(2);
      // fenêtre de signature : sort de l'écran du portable
      const up = E.outBack(seg(t, T.open + 0.12, T.open + 0.6)), down = E.inOutCubic(seg(t, T.signed + 0.05, T.signed + 0.4));
      const a = clamp(up) * (1 - down);
      opa(DLG.el, t > T.open + 0.1 && t < T.signed + 0.42 ? clamp(seg(t, T.open + 0.1, T.open + 0.2)) * (1 - seg(t, T.signed + 0.35, T.signed + 0.42)) : 0);
      opa(dlgHalo.el, 0.55 * a);
      if (DLG.rect && a > 0.001) {
        const r = DLG.rect;
        DLG.setM(M4.chain(L4.obj.M, M4.T(L4.sx + r.x, L4.sy + r.y, 170 * a), M4.T(r.w / 2, r.h / 2, 0), M4.S(1 + 0.06 * a), M4.T(-r.w / 2, -r.h / 2, 0)));
        dlgHalo.w = r.w + 80; dlgHalo.h = r.h + 80; dlgHalo.el.style.width = dlgHalo.w + "px"; dlgHalo.el.style.height = dlgHalo.h + "px";
        dlgHalo.setM(M4.chain(L4.obj.M, M4.T(L4.sx + r.x - 40, L4.sy + r.y - 40, 150 * a)));
      }
    } else { pose(L4, { o: 0 }); pose(P4, { o: 0 }); opa(DLG.el, 0); opa(dlgHalo.el, 0); }
    // la composition et ses éclats
    const sp = bump2(t, S("signature") + 0.15, S("signature") + 0.45, T.nonEnd - 0.01, T.nonEnd);
    opa(sigSet.el, sp);
    const SIGP = [ST.sig, -180, 1150], SIGS = 0.62;
    const sigM = (off = [0, 0, 0], cx = SIG_W / 2, cy = SIG_H / 2, Rt = M4.I(), bx = 0, by = 0) =>
      M4.chain(M4.T(...SIGP), M4.S(SIGS), M4.T(off[0] / SIGS, off[1] / SIGS, off[2] / SIGS), M4.T(cx - SIG_W / 2, cy - SIG_H / 2, 0), Rt, M4.T(-cx + bx, -cy + by, 0));
    if (sp > 0.01) {
      const rise = E.outBack(seg(t, S("signature") + 0.15, S("signature") + 0.75));
      sigSet.setM(M4.chain(sigM([0, 160 * (1 - rise), 0]), M4.T(SIG_W / 2, SIG_H / 2, 0), M4.S(0.9 + 0.1 * rise + 0.01 * kb), M4.T(-SIG_W / 2, -SIG_H / 2, 0)));
      const out = E.outCubic(seg(t, T.kImp - 0.4, T.kImp + 0.35));
      sigPaper.style.clipPath = `inset(0 0 ${(100 * (1 - out)).toFixed(1)}% 0)`;
      paperInk.style.strokeDashoffset = (1 - E.inOutSine(seg(t, T.kSig - 0.1, T.kSig + 0.5))).toFixed(3);
      const sc = seg(t, T.kScan - 0.1, T.kScan + 0.6);
      paperScan.style.top = lerp(-90, 1000, sc).toFixed(0) + "px"; paperScan.style.opacity = (sc > 0 && sc < 1 ? 1 : 0).toFixed(2);
      const wt = [T.kImp, T.kSig, T.kScan, T.kScan + 0.25, T.non, T.non + 0.12, T.nonW, w("signature", "Un") , T.doc, w("signature", "à"), w("signature", "signer")];
      sigWords.forEach((wd, i) => { const p = E.outBack(seg(t, wt[i] - 0.06, wt[i] + 0.22)); wd.style.opacity = clamp(p * 1.4).toFixed(3); wd.style.transform = `translateY(${(30 * (1 - p)).toFixed(1)}px) scale(${(1.25 - 0.25 * clamp(p)).toFixed(3)})`; blur(wd, 12 * (1 - clamp(p))); });
    }
    const shatter = seg(t, T.nonEnd, T.nonEnd + 1.0);
    for (const sh of SHARDS) {
      const on = shatter > 0 && shatter < 1;
      opa(sh.o.el, on ? 1 - E.inCubic(shatter) : 0);
      if (!on) continue;
      const f = E.outCubic(shatter), dx = (sh.cx - SIG_W / 2) / (SIG_W / 2), dy = (sh.cy - SIG_H / 2) / (SIG_H / 2);
      const off = [dx * 1100 * f * (0.5 + sh.r), dy * 760 * f * (0.5 + sh.r2) + 300 * f * f, 700 * f * (0.2 + sh.r)];
      const Rt = M4.chain(M4.RX(420 * f * (sh.r - 0.5)), M4.RY(480 * f * (sh.r2 - 0.5)), M4.RZ(300 * f * (sh.r - sh.r2)));
      sh.o.setM(sigM(off, sh.cx, sh.cy, Rt, sh.bx, sh.by));
      blur(sh.o.el, 3 * f);
    }
    // lueur de la plume
    {
      const pp = penPoint(E.inOutSine(seg(t, T.draw + 0.15, T.drawEnd)));
      if (pp && t < T.drawEnd && DLG.rect) {
        const cv = docOf("sign").querySelector(film("sign-canvas"));
        if (cv) { const r = cv.getBoundingClientRect(); const Pw = DLG.world(r.left + pp[0] * r.width - DLG.rect.x, r.top + pp[1] * r.height - DLG.rect.y);
          fx.globalCompositeOperation = "lighter"; dot3(fx, Pw, 30, "rgba(5,218,240,1)", 0.9); fx.globalCompositeOperation = "source-over"; }
      }
      const r = docD(L4).querySelector(".mw-preview-stage");
      if (r && sigOn) {
        const q2 = r.getBoundingClientRect(), p = seg(t, T.signed + 0.5, T.signed + 1.2);
        if (p > 0 && p < 1) { const v = lerp(q2.top - 30, q2.bottom + 30, p);
          fx.globalCompositeOperation = "lighter"; line3(fx, scrPt(L4, q2.left, v), scrPt(L4, q2.right, v), { color: "rgba(5,218,240,1)", width: 9, alpha: Math.sin(Math.PI * p), glow: 40 }); fx.globalCompositeOperation = "source-over"; }
      }
    }
    // demandes (téléphone) : on descend jusqu'au formulaire, puis jusqu'à la liste
    if (vis(t, S("demandes"), S("contenu"))) {
      pose(P5, Object.assign({}, POSE.P5, { s: bump, ry: POSE.P5.ry + 4 * Math.sin(t * 0.6) }));
      scrollD(P5, 200 * E.inOutCubic(seg(t, T.fill - 0.6, T.fill - 0.1)) + 360 * E.inOutCubic(seg(t, T.clics + 0.35, T.process - 0.05)));
    } else pose(P5, { o: 0 });
    // contenu (tablette)
    if (vis(t, S("contenu"), S("mail"))) pose(T6, Object.assign({}, POSE.T6, { s: bump, ry: POSE.T6.ry - 3 * Math.sin(t * 0.6) }));
    else pose(T6, { o: 0 });
    // mail (portable) et support (téléphone)
    if (vis(t, S("mail"), S("agent"))) {
      pose(L7, Object.assign({}, POSE.L7, { s: bump }));
      const pin = E.outBack(seg(t, T.souci - 0.4, T.souci + 0.2));
      pose(P7, Object.assign({}, POSE.P7, { y: POSE.P7.y + 1200 * (1 - pin), s: bump, o: pin > 0.001 ? 1 : 0 }));
      scrollD(P7, 200 * E.inOutCubic(seg(t, T.tickType - 0.4, T.tickType)) + 360 * E.inOutCubic(seg(t, T.ticket + 0.2, T.charge - 0.05)));
    } else { pose(L7, { o: 0 }); pose(P7, { o: 0 }); }
    // agent : portable dans la nuit, étincelle, sources reliées par des faisceaux
    const agOn = vis(t, S("agent"), T.final);
    if (agOn) {
      pose(L8, Object.assign({}, POSE.L8, { s: bump }));
      const ORB = [ST.agent - 1180, -760, 500];
      const oa = bump2(t, T.q - 0.4, T.q + 0.3, T.final - 0.8, T.final - 0.3);
      opa(orb.el, oa);
      if (oa > 0.01) {
        orb.place({ x: ORB[0], y: ORB[1], z: ORB[2], bill: true, rz: 8 * Math.sin(t), s: (0.5 + 0.5 * E.outBack(seg(t, T.q - 0.4, T.q + 0.35))) * (1 + 0.05 * Math.sin(t * 5)) });
        ring2(ORB, 230, oa * 0.8, t * 2.2);
      }
      const SRCP = [[ST.agent - 1150, -60, 300], [ST.agent + 1150, -520, 300], [ST.agent + 1150, 240, 300]];
      SRC.forEach((o, i) => {
        const tb = T.chips[i], a = bump2(t, tb - 0.35, tb, T.final - 0.8, T.final - 0.3);
        opa(o.el, a);
        if (a < 0.01) return;
        const p = E.outBack(seg(t, tb - 0.35, tb + 0.15));
        o.place({ x: SRCP[i][0], y: SRCP[i][1] + 80 * (1 - p), z: SRCP[i][2], bill: true, s: 1.25 * (0.6 + 0.4 * p) });
        const A = scrPt(L8, 1180, 300 + 150 * i), ba = bump2(t, tb - 0.05, tb + 0.2, T.answer + 0.2, T.answer + 0.6);
        thread(A, SRCP[i], 120 * (i === 1 ? 1 : -1), E.inOutCubic(seg(t, tb - 0.05, tb + 0.4)), ba);
      });
    } else { pose(L8, { o: 0 }); opa(orb.el, 0); SRC.forEach(o => opa(o.el, 0)); }

    // ---------------- accroche : l'heure qui s'emballe, le tunnel de la montée
    if (t < T.logo + 0.2) {
      const dg = E.inOutCubic(seg(t, w("hook", "Au"), w("hook", "fou") + 0.3));
      const da = bump2(t, w("hook", "Au") - 0.15, w("hook", "Au") + 0.1, SC.hook.segs[1].start - 0.3, SC.hook.segs[1].start);
      if (da > 0.01) {
        const r0 = 330;
        fx.globalCompositeOperation = "lighter";
        for (let k2 = 0; k2 < 60; k2++) {
          const ang = k2 / 60 * Math.PI * 2 - Math.PI / 2, len = k2 % 5 ? 18 : 44;
          fx.globalAlpha = da * (k2 % 5 ? 0.45 : 0.9); fx.strokeStyle = "rgba(5,218,240,1)"; fx.lineWidth = k2 % 5 ? 3 : 6;
          fx.beginPath(); fx.moveTo(CX + Math.cos(ang) * r0, 400 + Math.sin(ang) * r0); fx.lineTo(CX + Math.cos(ang) * (r0 - len), 400 + Math.sin(ang) * (r0 - len)); fx.stroke();
        }
        const hand = -Math.PI / 2 + dg * Math.PI * 2 * 11.5 / 12 * 6;
        fx.globalAlpha = da; fx.lineWidth = 8; fx.shadowColor = "#05daf0"; fx.shadowBlur = 30;
        fx.beginPath(); fx.moveTo(CX, 400); fx.lineTo(CX + Math.cos(hand) * 250, 400 + Math.sin(hand) * 250); fx.stroke();
        fx.shadowBlur = 0; fx.font = "700 150px InterDisplay"; fx.textAlign = "center"; fx.fillStyle = "#fff"; fx.globalAlpha = da;
        fx.fillText(hhmm(480 + 690 * dg), CX, 455);
        fx.globalCompositeOperation = "source-over";
      }
      const bu = seg(t, T.logo - 2 * BAR, T.logo);                     // montée : anneaux qui accélèrent vers le centre
      if (bu > 0 && t < T.logo) {
        fx.globalCompositeOperation = "lighter";
        for (let k2 = 0; k2 < 8; k2++) {
          const ph = (k2 / 8 + t * (0.4 + 1.6 * bu)) % 1, rr = 60 + 1400 * Math.pow(ph, 2.2);
          fx.globalAlpha = (0.15 + 0.5 * bu) * (1 - ph); fx.strokeStyle = "rgba(5,218,240,1)"; fx.lineWidth = 3 + 6 * ph;
          fx.beginPath(); fx.arc(CX, CY, rr, 0, Math.PI * 2); fx.stroke();
        }
        fx.globalCompositeOperation = "source-over";
      }
    }

    // ---------------- HUD : mots qui claquent sur les temps
    SLAMS.forEach(sl => {
      if (t < sl.t0 - 0.05 || t > sl.t1 + 0.25) { opa(sl.el, 0); return; }
      const pin = E.outBack(seg(t, sl.t0, sl.t0 + 0.18)), pout = E.inCubic(seg(t, sl.t1, sl.t1 + 0.18));
      const sc = (1.35 - 0.35 * clamp(pin)) * (1 + 0.15 * pout) * (1 + 0.012 * kb);
      const wdt = sl.el.offsetWidth, hgt = sl.el.offsetHeight;
      const x0 = sl.align === "left" ? sl.x : sl.align === "right" ? sl.x - wdt : sl.x - wdt / 2;
      sl.el.style.transformOrigin = sl.align === "left" ? "0% 50%" : "50% 50%";
      sl.el.style.transform = `translate(${x0.toFixed(1)}px,${(sl.y - hgt / 2 - 40 * pout).toFixed(1)}px) scale(${sc.toFixed(4)})`;
      opa(sl.el, clamp(seg(t, sl.t0 - 0.02, sl.t0 + 0.08)) * (1 - pout));
      blur(sl.el, 14 * (1 - clamp(pin)) + 10 * pout);
    });
    cursorAt(t);
    CHECKS.forEach(c => {
      const p = E.outBack(seg(t, c.t0, c.t0 + 0.4)), o = seg(t, c.t0, c.t0 + 0.15) * (1 - seg(t, c.t1 - 0.2, c.t1));
      opa(c.el, o);
      if (o > 0.002) c.el.style.transform = `translate(${(84 - 40 * (1 - clamp(p))).toFixed(1)}px, 80px)`;
    });
    // étalonnage : éclairs sur les drops et les éclats, vignette, grain
    const fl = Math.max(0.55 * Math.exp(-Math.pow((t - T.logo) / 0.14, 2)), 0.55 * Math.exp(-Math.pow((t - T.final) / 0.14, 2)),
                        0.5 * Math.exp(-Math.pow((t - T.nonEnd) / 0.08, 2)));
    opa(flash, fl);
    const [, name] = palAt(t);
    opa(vign, name === "light" ? 0.25 : 0.7);
    const fr = Math.round(t * 30);
    grain.style.transform = `translate(${(hash(fr) * 64 - 32).toFixed(0)}px,${(hash(fr + 7) * 64 - 32).toFixed(0)}px)`;
    opa(grain, name === "light" ? 0.25 : 0.45);
  };
  function bump2(t, a, b, c, d) { return seg(t, a, b) * (1 - seg(t, c, d)); }
})();
