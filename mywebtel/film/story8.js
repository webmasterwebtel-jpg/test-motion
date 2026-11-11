/* MyWebtel — film V8, façon présentation Apple.
 * Retour de l'utilisateur sur la V7 : « toujours pas ça ; pourquoi ce battement boom boom de l'écran en permanence ? ;
 * le mock-up de l'ordinateur n'est pas bien fait ; garde la voix et fais une refonte complète, digne d'une présentation
 * Apple ». La V8 : fond sombre, un appareil à la fois sur une scène unique, mouvements lents et continus (aucune
 * pulsation, aucune secousse, aucun éclair), appareils en volume (ordinateur portable refait : écran, charnière, clavier,
 * pavé tactile), typographie sobre (titre + mot clé en dégradé), gros plans sur la vraie interface.
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
  const grade = add(stage, `<div id="grade"><div class="vignette"></div><div class="grain"></div></div>`);
  const [vign, grain] = grade.children;
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
    cg: w("conges", "congés"), soldeW: w("conges", "solde"), rights: w("conges", "droits"), seniority: w("conges", "d'ancienneté"),
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
  T.logo = segT("reveal"); T.final = segT("fin");
  T.solde = T.soldeW + 0.75;                                 // le compteur démarre quand la caméra est arrivée sur le solde
  T.nonEnd = Math.ceil((T.nonW + 0.2) / BAR) * BAR;          // retour de la musique après « Sauf que non »
  T.drawEnd = T.code - 0.3; T.consent = T.mail + 0.32; T.fileIn = T.proof + 0.55;
  T.ask = T.launch + 0.6; T.askSend = T.chips[0] - 0.12; T.agentSent = T.okAgent + 0.95; T.beamSupport = T.chips[2];
  T.mailType = T.chat + 0.5; T.mailSend = Math.max(T.mailW + 0.42, T.mailType + 0.9); T.tickType = T.tick + 0.3;
  const S = id => SC[id].start;
  // fenêtres des scènes (un appareil à la fois) : [entrée, sortie]
  const WIN = {
    hero: [T.logo + 0.85, S("pointage") - 0.25], P1: [S("pointage") - 0.2, S("conges") - 0.25], L2: [S("conges") - 0.2, S("absences") - 0.25],
    T3: [S("absences") - 0.2, S("signature") - 0.25], old: [S("signature") + 0.1, T.nonEnd - 0.12], L4: [T.nonEnd - 0.2, S("demandes") - 0.25],
    P5: [S("demandes") - 0.2, S("contenu") - 0.25], T6: [S("contenu") - 0.2, S("mail") - 0.25], L7: [S("mail") - 0.2, T.souci - 0.45],
    P7: [T.souci - 0.4, S("agent") - 0.25], L8: [S("agent") - 0.2, T.final - 0.6], fin: [T.final - 0.15, TL.duration + 5],
  };

  // ------------------------------------------------------------------ appareils en volume
  const lay = (cls, n, step) => Array.from({ length: n }, (_, i) => `<div class="lay ${cls}" style="transform:translateZ(${(-(i + 1) * step).toFixed(1)}px)"></div>`).join("");
  const KEYS_ROWS = [["fn", Array(14).fill(1)], ["", [...Array(13).fill(1), 1.6]], ["", [1.6, ...Array(12).fill(1), 1]], ["", [1.9, ...Array(11).fill(1), 1.9]],
                     ["", [2.4, ...Array(10).fill(1), 2.4]], ["", [1.1, 1.1, 1.1, 1.4, 6.2, 1.4, 1.1, 1.1, 1.1, 1.1]]];
  const KB = KEYS_ROWS.map(([c, ks]) => `<div class="row ${c}">${ks.map(f => `<i class="key" style="flex:${f}"></i>`).join("")}</div>`).join("");
  const SCR = `<div class="scr" style="transform:translateZ(.6px)"><div class="glass"></div><div class="sheen"></div><div class="off"></div></div>`;
  const DEV = [];
  function device(kind, page, extra = "") {
    const html = {
      phone: `<div class="d3 ph8">${lay("edge", 8, 1.5)}<div class="face"></div>${SCR}<div class="island" style="transform:translateZ(1.2px)"></div></div>`,
      tablet: `<div class="d3 tb8">${lay("edge", 7, 1.5)}<div class="face"></div>${SCR}<div class="cam" style="transform:translateZ(1.2px)"></div></div>`,
      laptop: `<div class="d3 lid8"><div class="lay back" style="transform:translateZ(-11px)"></div>${lay("edge", 3, 2.8)}<div class="face"></div>${SCR}<div class="cam" style="transform:translateZ(1.2px)"></div></div>`,
    }[kind];
    const el = add(world, html);
    const [ow, oh, sx, sy, sw, sh] = { phone: [430, 884, 20, 20, 390, 844], tablet: [880, 1240, 30, 30, 820, 1180], laptop: [1500, 968, 30, 28, 1440, 900] }[kind];
    const scr = q(el, ".scr");
    const f = frameFor(page, sw, sh);
    scr.insertBefore(f, scr.firstChild);
    if (extra) scr.insertAdjacentHTML("beforeend", extra);
    const d = { kind, page, el, obj: new Obj(el, ow, oh), frame: f, sx, sy, sw, sh, scr, sheen: q(scr, ".sheen"), off: q(scr, ".off") };
    if (kind === "laptop") d.base = new Obj(add(world, `<div class="d3 base8">${lay("side", 8, 3)}<div class="deck"></div><div class="hinge" style="transform:translateZ(.6px)"></div>
      <div class="well" style="transform:translateZ(.6px)">${KB}</div><div class="grille" style="left:38px;transform:translateZ(.6px)"></div><div class="grille" style="right:38px;transform:translateZ(.6px)"></div>
      <div class="pad" style="transform:translateZ(.6px)"></div><div class="lip" style="transform:translateZ(.6px)"></div></div>`), 1500, 1010);
    opa(d.off, 0); opa(d.sheen, 0);
    DEV.push(d);
    return d;
  }
  // pose : x, y, z = centre de l'appareil (portable : milieu de la charnière) ; lean = inclinaison de l'écran (12 = ouvert, -88 = fermé)
  function pose(d, { x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1, lean = 12, o = 1, bl = 0 } = {}) {
    opa(d.el, o); blur(d.el, bl);
    if (d.base) { opa(d.base.el, o); blur(d.base.el, bl); }
    if (o <= 0.002) return;
    const G = M4.chain(M4.T(x, y, z), M4.RY(ry), M4.RX(rx), M4.RZ(rz), M4.S(s));
    if (d.kind === "laptop") {
      d.obj.setM(M4.chain(G, M4.RX(lean), M4.T(-750, -968, 0)));
      d.base.setM(M4.chain(G, M4.RX(90), M4.T(-750, 0, 0)));
    } else d.obj.setM(M4.chain(G, M4.T(-d.obj.w / 2, -d.obj.h / 2, 0)));
  }
  const docD = d => d.frame.contentDocument;
  const scrPt = (d, u, v) => d.obj.world(d.sx + u, d.sy + v);
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
  const P4 = device("phone", "dashboard", `<div class="notif" style="z-index:7"><i>W</i><div><b>MyWebtel · Votre code de signature</b><span>Code pour « Avenant au contrat » : <strong>482 913</strong></span></div></div>`);
  const P5 = device("phone", "requests");
  const T6 = device("tablet", "content");
  const L7 = device("laptop", "mail");
  const P7 = device("phone", "support");
  const L8 = device("laptop", "agent");
  const notif = q(P4.scr, ".notif");
  // composants sortis de l'écran : fenêtre de signature, panneau de l'agent
  const DLG = makeClip(world, "sign", "dialog", d => { const g = d.querySelector(film("sign-dialog")); g.showModal(); const r = rectEl(g); g.close(); return r; }, 0);
  const PNL = makeClip(world, "agent", "panel", byFilm("agent-panel"), 0);
  const dlgGlow = new Obj(add(world, `<div class="aiglow"></div>`), 10, 10), pnlGlow = new Obj(add(world, `<div class="aiglow"></div>`), 10, 10);
  function liftClip(c, glow, d, a, lift, t, hue = 0) {       // a : 0..1 (sorti de l'écran), lueur animée derrière
    opa(glow.el, 0.75 * a);
    if (!c.rect || a <= 0.001) return;
    const r = c.rect;
    c.setM(M4.chain(d.obj.M, M4.T(d.sx + r.x, d.sy + r.y, lift * a), M4.T(r.w / 2, r.h / 2, 0), M4.S(1 + 0.05 * a), M4.T(-r.w / 2, -r.h / 2, 0)));
    glow.w = r.w + 70; glow.h = r.h + 70; glow.el.style.width = glow.w + "px"; glow.el.style.height = glow.h + "px";
    glow.el.style.background = `conic-gradient(from ${((t * 50 + hue) % 360).toFixed(1)}deg, #05daf0, #008ff1, #7fe9ff, #0b5fd8, #05daf0)`;
    glow.setM(M4.chain(d.obj.M, M4.T(d.sx + r.x - 35, d.sy + r.y - 35, lift * a - 16)));
  }

  // ------------------------------------------------------------------ accessoires
  const rule = new Obj(add(world, `<div class="rule"><div style="display:flex;align-items:center;gap:16px;font:600 30px Inter;color:#08264b">${ic("calendar")} Ancienneté</div>
    <div class="bar"><div class="fill"></div><div class="knob">${ic("lock")}</div></div><div class="ticks"><span>Arrivée</span><span>6 mois</span><b>1 an</b></div></div>`), 980, 270);
  const ruleFill = q(rule.el, ".fill"), ruleKnob = q(rule.el, ".knob");
  const pdf = new Obj(add(world, `<div class="pdf"><span class="tag">PDF</span><div class="l" style="width:90%"></div><div class="l"></div><div class="l" style="width:70%"></div><div class="l" style="width:84%"></div><b>certificat-medical.pdf</b></div>`), 300, 380);
  const paper = new Obj(add(world, `<div class="paper8"><h5>AVENANT AU CONTRAT DE TRAVAIL</h5><div class="l" style="width:62%;margin-top:16px"></div>
    <div class="l" style="margin-top:40px"></div><div class="l"></div><div class="l" style="width:88%"></div><div class="l"></div><div class="l" style="width:76%"></div>
    <div class="l" style="margin-top:40px"></div><div class="l" style="width:92%"></div><div class="l" style="width:64%"></div>
    <svg viewBox="0 0 400 140" style="position:absolute;left:270px;top:620px;width:300px;overflow:visible"><path class="ink" d="M10 90 C 40 20, 70 20, 60 80 S 110 120, 130 60 S 170 10, 190 70 S 230 110, 250 60 C 262 30, 285 34, 292 78 S 330 100, 390 50" fill="none" stroke="#0b2a4d" stroke-width="7" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>
    <div class="scan"></div></div>`), 620, 820);
  const paperInk = q(paper.el, ".ink"), paperScan = q(paper.el, ".scan");
  const SRC = [["calendar", "Mes congés", "24 jours disponibles"], ["req", "Démarches RH", "Demande préparée"], ["shield", "Support IT", "Tickets"]]
    .map(([i, a, b]) => new Obj(add(world, `<div class="chip8"><span class="ic">${ic(i)}</span><div>${a}<small>${b}</small></div></div>`), 470, 104));

  // ------------------------------------------------------------------ HUD : logo, textes, curseur, toucher
  const logoHud = add(hud, `<img src="brand/webtel-logo-white.svg" style="width:900px;transform-origin:0 0">`);
  const tagHud = add(hud, `<div class="tagline" style="color:#9fc3e6">MYWEBTEL · ESPACE COLLABORATEUR</div>`);
  const subHud = add(hud, `<div class="subline" style="color:rgba(235,244,255,.86)">Pointage<i>·</i>Congés<i>·</i>Absences<i>·</i>Signature<i>·</i>Demandes RH<i>·</i>Agent IA</div>`);
  [logoHud, tagHud, subHud].forEach(e => opa(e, 0));
  const TXT = [];
  // texte : kind = eyebrow | head | cap ; pos {x, y, align} (y = haut du bloc, sauf cap : centre) ; words : [[html, instant]…]
  function text(kind, html, t0, t1, pos, opt = {}) {
    const inner = opt.words ? opt.words.map(([hh]) => { const br = hh.endsWith("<br>"); return `<span class="wd">${br ? hh.slice(0, -4) : hh}</span>${br ? "<br>" : ""}`; }).join(opt.sep === undefined ? " " : opt.sep) : html;
    const el = add(hud, `<div class="${kind} ${opt.cls || ""}">${inner}</div>`);
    opa(el, 0);
    TXT.push({ el, kind, t0, t1, pos, words: opt.words ? qa(el, ".wd").map((e, i) => [e, opt.words[i][1]]) : null, strike: opt.strike });
  }
  const CURSOR = `<svg class="cursor" viewBox="0 0 34 44"><path d="M3 2l26 24H16l7 14-5 2-7-14-8 8z" fill="#fff" stroke="#041b34" stroke-width="2.4" stroke-linejoin="round"/></svg>`;
  const cur = add(hud, CURSOR), rip = add(hud, `<div class="ripple"></div>`), touch = add(hud, `<div class="touch"></div>`);

  window.FILM = { duration: TL.duration, T };
  Promise.all([document.fonts.ready, ...LOADS]).then(() => {
    layoutClips();
    setup();
    const imgs = Array.from(document.images).map(i => i.decode().catch(() => {}));
    Promise.all(imgs).then(() => { window.renderAt(0); window.READY = true; });
  });

  // ------------------------------------------------------------------ poses de repos et caméra
  const REST = {
    heroL: { x: 0, y: 380, z: 0 }, heroT: { x: -1260, y: 80, z: 360, ry: 26, s: 0.82 }, heroP: { x: 1220, y: 150, z: 460, ry: -26, s: 0.9 },
    phone: { x: 0, y: 0, z: 0, ry: 15 }, tablet: { x: 0, y: 0, z: 0, ry: -13 }, laptop: { x: 0, y: 420, z: 0, ry: -7 },
    P4: { x: 840, y: 150, z: 640, ry: -18 },
  };
  let KEYS = [], CLICKS = [];
  const look = (P, zoom, o = {}) => camState(Object.assign({ tx: P[0], ty: P[1], tz: P[2], dist: F0 / zoom, yaw: 0, pitch: 3, roll: 0, F: F0 }, o));
  const side = (P, sx, zoom, sy = 540) => [P[0] - (sx - CX) / zoom, P[1] - (sy - CY) / zoom, P[2]];   // P apparaît en (sx, sy) à l'écran
  function setup() {
    for (const o of DEV) pose(o, { o: 0 });
    const k = (t, s, ease = E.inOutCubic) => KEYS.push([t, s, ease]);
    const hold = t => k(t, Object.assign({}, KEYS[KEYS.length - 1][1]), E.inOutSine);
    const at = (d, ps, u, v) => { pose(d, Object.assign({}, ps, { o: 1 })); const P = scrPt(d, u, v); pose(d, { o: 0 }); return P; };
    const LP = { pitch: 8 };
    // accroche et drop : logo, puis l'ordinateur qui s'ouvre entre la tablette et le téléphone
    const heroC = [0, -120, 200];
    k(0, look(heroC, 0.5, { pitch: 7 }));
    k(T.logo + 1.2, look(heroC, 0.5, { pitch: 7, yaw: -4 }), E.inOutSine);
    k(WIN.hero[1], look(heroC, 0.55, { pitch: 7, yaw: 3 }), E.inOutSine);
    // pointage (téléphone à gauche, texte à droite)
    const p1 = at(P1, REST.phone, 195, 420), p1b = at(P1, REST.phone, 195, 600);
    k(WIN.P1[0] + 0.9, look(side(p1, 470, 1.12), 1.12, { yaw: -3 }));
    k(T.in - 0.2, look(side(p1, 470, 1.4), 1.4, { yaw: -1 }));
    k(T.out + 0.3, look(side(p1, 470, 1.46), 1.46, { yaw: 2 }), E.inOutSine);
    k(T.saved + 0.5, look(side(p1b, 470, 1.5), 1.5, { yaw: -1 }));
    k(WIN.P1[1], look(side(p1b, 470, 1.56), 1.56, { yaw: 2 }), E.inOutSine);
    // congés (portable à droite, texte à gauche, puis gros plan)
    const l2 = at(L2, REST.laptop, 720, 450), l2m = at(L2, REST.laptop, 470, 262), l2s = at(L2, REST.laptop, 900, 330);
    k(WIN.L2[0] + 0.9, look(side(l2, 1260, 0.7, 500), 0.7, { pitch: 8, yaw: 5 }));
    hold(T.soldeW + 0.1);
    k(T.solde - 0.1, look(l2m, 2.05, { pitch: 5, yaw: -2 }));
    k(T.rights - 0.45, look(l2m, 2.15, { pitch: 5, yaw: 2 }), E.inOutSine);
    k(T.rights + 0.35, look([l2s[0], l2s[1] + 40, l2s[2] + 130], 1.35, { pitch: 5, yaw: 3 }));
    k(WIN.L2[1], look([l2s[0], l2s[1] + 40, l2s[2] + 130], 1.42, { pitch: 5, yaw: -2 }), E.inOutSine);
    // absences (tablette à droite, texte à gauche)
    const t3 = at(T3, REST.tablet, 410, 590), t3u = at(T3, REST.tablet, 505, 760), t3l = at(T3, REST.tablet, 505, 950);
    k(WIN.T3[0] + 0.9, look(side(t3, 1300, 0.82), 0.82, { yaw: 3 }));
    k(T.declare - 0.1, look(side(t3u, 1250, 1.28), 1.28, { yaw: 2 }));
    k(T.absSend + 0.2, look(side(t3u, 1250, 1.33), 1.33, { yaw: -1 }), E.inOutSine);
    k(T.rh + 0.2, look(side(t3l, 1250, 1.3), 1.3, { yaw: 2 }));
    k(WIN.T3[1], look(side(t3l, 1250, 1.35), 1.35, { yaw: -2 }), E.inOutSine);
    // signature : d'abord les mots et la feuille, puis le portable
    k(WIN.old[0] + 0.6, look([0, -60, 300], 0.62, { pitch: 3, yaw: -3 }));
    k(WIN.old[1], look([0, -60, 300], 0.68, { pitch: 3, yaw: 3 }), E.inOutSine);
    const l4row = at(L4, REST.laptop, 640, 345), l4dlg = at(L4, REST.laptop, 720, 450), l4pv = at(L4, REST.laptop, 1200, 480);
    k(T.nonEnd + 0.8, look(l4row, 1.25, LP));
    k(T.recv + 0.6, look(l4row, 1.7, { pitch: 5, yaw: -2 }));
    k(T.open + 0.05, look(l4row, 1.75, { pitch: 5, yaw: 2 }), E.inOutSine);
    const l4d = [l4dlg[0], l4dlg[1], l4dlg[2] + 170];
    k(T.nom - 0.1, look(side(l4d, 1200, 1.2), 1.2, { pitch: 4, yaw: -2 }));
    k(T.code - 0.25, look(side(l4d, 1200, 1.25), 1.25, { pitch: 4, yaw: 1 }), E.inOutSine);
    k(T.mail + 0.2, look([l4dlg[0] + 330, l4dlg[1] - 10, l4dlg[2] + 300], 0.95, { pitch: 4, yaw: -4 }));
    k(T.signed - 0.05, look([l4dlg[0] + 330, l4dlg[1] - 10, l4dlg[2] + 300], 0.97, { pitch: 4, yaw: 2 }), E.inOutSine);
    k(T.signed + 0.7, look([l4pv[0] - 200, l4pv[1], l4pv[2]], 1.6, { pitch: 5, yaw: -2 }));
    k(WIN.L4[1], look([l4pv[0] - 200, l4pv[1], l4pv[2]], 1.66, { pitch: 5, yaw: 2 }), E.inOutSine);
    // demandes RH (téléphone)
    const p5 = at(P5, REST.phone, 195, 360), p5b = at(P5, REST.phone, 195, 560);
    k(WIN.P5[0] + 0.9, look(side(p5, 470, 1.15), 1.15, { yaw: -3 }));
    k(T.fill - 0.2, look(side(p5b, 470, 1.45), 1.45, { yaw: -1 }));
    k(T.process + 0.2, look(side(p5, 470, 1.45), 1.45, { yaw: 2 }));
    k(WIN.P5[1], look(side(p5, 470, 1.5), 1.5, { yaw: -2 }), E.inOutSine);
    // contenu (tablette)
    const t6 = at(T6, REST.tablet, 410, 590), t6n = at(T6, REST.tablet, 600, 700);
    k(WIN.T6[0] + 0.9, look(side(t6, 1300, 0.84), 0.84, { yaw: 3 }));
    k(T.read - 0.1, look(side(t6n, 1290, 1.28), 1.28, { yaw: 2 }));
    k(WIN.T6[1], look(side(t6n, 1290, 1.34), 1.34, { yaw: -2 }), E.inOutSine);
    // mail (portable) puis support (téléphone)
    const l7 = at(L7, REST.laptop, 720, 450), l7c = at(L7, REST.laptop, 1010, 560);
    k(WIN.L7[0] + 0.9, look(side(l7, 1260, 0.7, 500), 0.7, { pitch: 8, yaw: 5 }));
    hold(T.chat + 0.1);
    k(T.mailType + 0.1, look(l7c, 1.45, { pitch: 5, yaw: -2 }));
    k(WIN.L7[1], look(l7c, 1.5, { pitch: 5, yaw: 2 }), E.inOutSine);
    const p7 = at(P7, REST.phone, 195, 420), p7b = at(P7, REST.phone, 195, 560);
    k(WIN.P7[0] + 0.9, look(side(p7, 470, 1.18), 1.18, { yaw: -3 }));
    k(T.tickType + 0.1, look(side(p7b, 470, 1.42), 1.42, { yaw: -1 }));
    k(T.ticket + 0.5, look(side(p7, 470, 1.42), 1.42, { yaw: 2 }));
    k(WIN.P7[1], look(side(p7, 470, 1.47), 1.47, { yaw: -1 }), E.inOutSine);
    // agent (portable, puis le panneau sorti de l'écran à droite, les sources à gauche)
    const l8 = at(L8, REST.laptop, 720, 450), l8p = at(L8, REST.laptop, 1177, 489);
    k(WIN.L8[0] + 0.9, look(side(l8, 1260, 0.7, 500), 0.7, { pitch: 8, yaw: 5 }));
    hold(T.launch - 0.1);
    k(T.launch + 0.8, look(side([l8p[0], l8p[1], l8p[2] + 170], 1330, 1.2), 1.2, { pitch: 4, yaw: -3 }));
    k(T.answer - 0.1, look(side([l8p[0], l8p[1], l8p[2] + 170], 1330, 1.24), 1.24, { pitch: 4, yaw: 2 }), E.inOutSine);
    k(T.answer + 0.6, look(side([l8p[0], l8p[1] + 150, l8p[2] + 170], 1330, 1.42), 1.42, { pitch: 4, yaw: -1 }));
    k(T.okAgent + 0.5, look(side([l8p[0], l8p[1] + 150, l8p[2] + 170], 1330, 1.46), 1.46, { pitch: 4, yaw: 1 }), E.inOutSine);
    k(WIN.L8[1] + 0.3, look(side(l8, 960, 0.62, 500), 0.62, { pitch: 8, yaw: -2 }));
    // fin : les trois appareils et le logo
    k(T.final + 0.9, look(heroC, 0.5, { pitch: 7, yaw: -4 }));
    k(TL.duration, look(heroC, 0.55, { pitch: 7, yaw: 3 }), E.inOutSine);
    KEYS.sort((a, b) => a[0] - b[0]);

    // ---------------------------------------------------------------- textes
    const C = { x: CX, y: 440, align: "center" }, R = (y = 400) => ({ x: 1030, y, align: "left" }), Lf = (y = 400) => ({ x: 120, y, align: "left" });
    const cap = (y = 978, x = CX) => ({ x, y, align: "center" });
    const hw = (wd, n = 0) => w("hook", wd, n);
    // accroche
    text("head xl", "Pointer.", 0.05, hw("poser") - 0.12, C);
    text("head xl", "Poser un <b>congé.</b>", hw("poser") - 0.05, hw("retrouver") - 0.12, C);
    text("head xl", "Ta <b>fiche de paie.</b>", hw("retrouver") - 0.05, hw("signer") - 0.12, C);
    text("head xl", "Signer un <b>document.</b>", hw("signer") - 0.05, hw("Au") - 0.12, C);
    text("head xl", "", hw("Au") - 0.02, segT("hook", 1) - 0.2, C, { words: [["Tout", hw("tout")], ["ça", hw("ça")], ["prend", hw("prend")], ["un", hw("un", 2)], ["temps", hw("temps")], ["<b>fou.</b>", hw("fou")]] });
    text("head", "", segT("hook", 1) - 0.05, T.logo - 0.35, { x: CX, y: 400, align: "center" },
         { words: [["Et", W("hook", 1, "Et")], ["si", W("hook", 1, "si")], ["tout", W("hook", 1, "tout")], ["se", W("hook", 1, "se")], ["faisait<br>", W("hook", 1, "faisait")],
                   ["<b>au</b>", W("hook", 1, "au")], ["<b>même</b>", W("hook", 1, "même")], ["<b>endroit</b>", W("hook", 1, "endroit")], ["?", W("hook", 1, "endroit") + 0.3]] });
    // pointage
    text("eyebrow", "Pointage", WIN.P1[0] + 0.5, WIN.P1[1], R(388));
    text("head", "Un <b>clic.</b>", T.in - 0.08, T.pause - 0.3, R(440));
    text("head", "", T.pause - 0.08, T.saved - 0.15, R(440), { words: [["Pause.<br>", T.pause - 0.05], ["Retour.<br>", T.ret - 0.05], ["<b>Départ.</b>", T.out - 0.05]], sep: "" });
    text("head", "À la <b>minute</b><br><b>près.</b>", w("pointage", "à") - 0.08, WIN.P1[1], R(440));
    // congés
    text("eyebrow", "Mes congés", WIN.L2[0] + 0.5, T.soldeW + 0.35, Lf(388));
    text("head", "Ton <b>solde</b><br>est là.", T.cg + 0.25, T.soldeW + 0.35, Lf(440));
    text("cap", "Tes droits s’ouvrent après <b>1 an d’ancienneté</b>", T.rights + 0.1, WIN.L2[1], cap());
    // absences
    text("eyebrow", "Mes absences", WIN.T3[0] + 0.5, WIN.T3[1], Lf(388));
    text("head", "Une absence ?", T.abs - 0.1, T.declare - 0.2, Lf(440));
    text("head", "Avec ton<br><b>justificatif.</b>", T.declare - 0.08, T.rh - 0.25, Lf(440));
    text("head md", "Les RH s’occupent<br><b>du reste.</b>", T.rh - 0.08, WIN.T3[1], Lf(440));
    // signature : l'ancienne méthode (mots à gauche, feuille à droite)
    text("eyebrow", "Un document à signer ?", WIN.old[0] + 0.3, WIN.old[1], { x: 250, y: 300, align: "left" });
    text("head", "", T.kImp - 0.1, WIN.old[1], { x: 250, y: 356, align: "left" },
         { words: [["<s>Imprimer.</s><br>", T.kImp - 0.05], ["<s>Signer.</s><br>", T.kSig - 0.05], ["<s>Scanner ?</s>", T.kScan - 0.05]], sep: "", strike: T.non + 0.05 });
    text("head", "Sauf que <b>non.</b>", T.non - 0.05, WIN.old[1], { x: 250, y: 720, align: "left" });
    text("cap", "Reçu directement dans <b>« Mes documents »</b>", T.recv - 0.05, T.open + 0.15, cap());
    text("cap", "Tu signes avec <b>ton nom</b>…", T.nom - 0.5, T.draw + 0.1, cap(560, 400));
    text("cap", "…ou tu la <b>dessines</b>", T.draw + 0.2, T.code - 0.15, cap(560, 400));
    text("cap", "Un <b>code</b> arrive par mail", T.code - 0.05, T.signed - 0.1, cap(1010, 700));
    text("cap", "Document <b>signé</b>", T.signed + 0.35, WIN.L4[1], cap());
    // demandes
    text("eyebrow", "Mes demandes RH", WIN.P5[0] + 0.5, WIN.P5[1], R(388));
    text("head md", "Une attestation ?<br>Une question ?", T.att - 0.08, w("demandes", "en") - 0.25, R(440));
    text("head", "En <b>deux</b><br><b>clics.</b>", w("demandes", "en") - 0.08, WIN.P5[1], R(440));
    // contenu
    text("eyebrow", "Contenu", WIN.T6[0] + 0.5, WIN.T6[1], Lf(388));
    text("head md", "Les notes de<br>la Direction<br>et des RH.", T.notes - 0.08, T.confirm - 0.25, Lf(440));
    text("head", "Confirmé<br>en <b>un clic.</b>", T.confirm - 0.08, WIN.T6[1], Lf(440));
    // mail, support
    text("eyebrow", "Mail", WIN.L7[0] + 0.5, T.mailType - 0.1, Lf(388));
    text("head", "Échange<br>avec tes<br><b>collègues.</b>", T.coll - 0.45, T.mailType - 0.1, Lf(440));
    text("eyebrow", "Support IT", WIN.P7[0] + 0.5, WIN.P7[1], R(388));
    text("head md", "Un souci<br>technique ?", T.souci - 0.05, w("mail", "prend") - 0.25, R(440));
    text("head md", "Ton ticket est<br><b>pris en charge.</b>", w("mail", "prend") - 0.08, WIN.P7[1], R(440));
    // agent
    text("eyebrow", "Agent MyWebtel", WIN.L8[0] + 0.5, T.launch + 0.2, Lf(388));
    text("head", "Une <b>question ?</b>", T.q - 0.4, T.launch + 0.2, Lf(440));
    text("cap", "Il te <b>répond</b>", T.answer, T.prep - 0.15, cap(990, 520));
    text("cap", "Il <b>prépare</b> même ta demande", T.prep - 0.05, T.toi - 0.15, cap(990, 520));
    text("cap", "Toi, tu n’as plus qu’à <b>confirmer</b>", T.toi - 0.05, WIN.L8[1], cap(990, 520));

    // ---------------------------------------------------------------- gestes
    const E2 = (d, sel) => () => elPt(d, sel);
    const cp = (c, id, sel) => () => { const el = docOf(id).querySelector(sel); if (!el || !c.rect) return null; const r = el.getBoundingClientRect(); return c.screen(r.left + r.width / 2 - c.rect.x, r.top + r.height / 2 - c.rect.y); };
    CLICKS = [
      [T.in, E2(P1, film("punch")), T.in - 0.5, T.out + 0.35, "touch"], [T.pause, E2(P1, film("punch")), T.in, T.out + 0.35, "touch"],
      [T.ret, E2(P1, film("punch")), T.in, T.out + 0.35, "touch"], [T.out, E2(P1, film("punch")), T.in, T.out + 0.35, "touch"],
      [T.absSend, E2(T3, film("abs-send")), T.absSend - 0.6, T.absSend + 0.4, "touch"],
      [T.open, E2(L4, film("sign-open")), T.open - 0.75, T.open + 0.3, "mouse"],
      [T.draw, cp(DLG, "sign", '[data-film="sign-tabs"] [data-sign-mode="draw"]'), T.draw - 0.6, T.draw + 1.1, "mouse"],
      [T.code, cp(DLG, "sign", film("sign-code-btn")), T.code - 0.6, T.signed + 0.35, "mouse"], [T.tape - 0.15, cp(DLG, "sign", film("sign-code")), T.code, T.signed + 0.35, "mouse"],
      [T.consent, cp(DLG, "sign", film("sign-consent")), T.code, T.signed + 0.35, "mouse"], [T.signed, cp(DLG, "sign", film("sign-confirm")), T.code, T.signed + 0.35, "mouse"],
      [T.fill - 0.2, E2(P5, film("req-cats") + " button"), T.fill - 0.7, T.clics + 0.45, "touch"], [T.clics, E2(P5, film("req-send")), T.fill - 0.2, T.clics + 0.45, "touch"],
      [T.confirm, E2(T6, film("note-check")), T.confirm - 0.6, T.lu + 0.4, "touch"], [T.lu, E2(T6, film("note-btn")), T.confirm, T.lu + 0.4, "touch"],
      [T.mailSend, E2(L7, film("mail-send")), T.mailSend - 0.7, T.mailSend + 0.35, "mouse"],
      [T.ticket - 0.1, E2(P7, film("tick-send")), T.ticket - 0.7, T.ticket + 0.35, "touch"],
      [T.askSend, cp(PNL, "agent", film("agent-send")), T.askSend - 0.7, T.askSend + 0.3, "mouse"],
      [T.okAgent, cp(PNL, "agent", film("agent-confirm")), T.toi - 0.1, T.okAgent + 0.5, "mouse"],
    ].sort((a, b) => a[0] - b[0]);
    window.FILM = { duration: TL.duration, T, clicks: CLICKS.map(c => c[0]), touches: CLICKS.filter(c => c[4] === "touch").map(c => c[0]),
                    moves: Object.entries(WIN).filter(([n]) => n !== "hero" && n !== "fin" && n !== "old").map(([, v]) => v[0]), texts: TXT.filter(x => x.kind !== "eyebrow").map(x => x.t0) };
  }

  function cameraAt(t) {
    let i = 0;
    while (i < KEYS.length - 1 && KEYS[i + 1][0] <= t) i++;
    if (i >= KEYS.length - 1) return Object.assign({}, KEYS[KEYS.length - 1][1]);
    const [t0, s0] = KEYS[i], [t1, s1, ease] = KEYS[i + 1];
    const s = lerpCam(s0, s1, ease(seg(t, t0, t1)));
    s.yaw += 0.5 * noise1(t * 0.19, 1); s.pitch += 0.3 * noise1(t * 0.17, 2);       // dérive très lente, jamais de battement
    return s;
  }

  // ------------------------------------------------------------------ fond sombre, lumière douce sous l'appareil
  function background(t) {
    bg.globalAlpha = 1; bg.globalCompositeOperation = "source-over";
    const g = bg.createRadialGradient(CX, 470, 0, CX, 470, 1250);
    g.addColorStop(0, "#0c1d33"); g.addColorStop(0.55, "#050d18"); g.addColorStop(1, "#010306");
    bg.fillStyle = g; bg.fillRect(0, 0, VW, VH);
    bg.globalCompositeOperation = "lighter";
    for (let k2 = 0; k2 < 3; k2++) {                          // deux ou trois lueurs qui dérivent lentement
      const x = CX + 760 * Math.sin(t * 0.07 + k2 * 2.1), y = 420 + 300 * Math.sin(t * 0.05 + k2 * 1.3), r = 700;
      const rg = bg.createRadialGradient(x, y, 0, x, y, r);
      rg.addColorStop(0, k2 % 2 ? "rgba(5,218,240,.055)" : "rgba(0,120,255,.075)"); rg.addColorStop(1, "rgba(0,0,0,0)");
      bg.fillStyle = rg; bg.fillRect(x - r, y - r, 2 * r, 2 * r);
    }
    bg.globalCompositeOperation = "source-over";
  }
  function pool(P, wdt, a) {                                  // lumière de l'écran qui se répand sous l'appareil
    const p = project(P, 20); if (!p || a < 0.01) return;
    const rx = wdt * p[2], ry = rx * 0.16;
    bg.save(); bg.translate(p[0], p[1]); bg.scale(1, ry / rx);
    const rg = bg.createRadialGradient(0, 0, 0, 0, 0, rx);
    rg.addColorStop(0, `rgba(120,190,255,${(0.16 * a).toFixed(3)})`); rg.addColorStop(1, "rgba(120,190,255,0)");
    bg.globalCompositeOperation = "lighter"; bg.fillStyle = rg; bg.fillRect(-rx, -rx, 2 * rx, 2 * rx); bg.restore();
    bg.globalCompositeOperation = "source-over";
  }
  function thread(A, B, lift, p, alpha, color = "rgba(95,212,255,1)", width = 3) {
    if (p <= 0 || alpha < 0.01) return;
    const n = 40, pts = [];
    for (let i = 0; i <= n * p; i++) { const u = i / n; const pr = project([lerp(A[0], B[0], u), lerp(A[1], B[1], u) - lift * Math.sin(Math.PI * u), lerp(A[2], B[2], u)], 20); if (pr) pts.push(pr); }
    if (pts.length < 2) return;
    fx.globalCompositeOperation = "lighter"; fx.globalAlpha = alpha; fx.strokeStyle = color; fx.lineWidth = width; fx.shadowColor = color; fx.shadowBlur = 18;
    fx.beginPath(); pts.forEach((q2, i) => (i ? fx.lineTo(q2[0], q2[1]) : fx.moveTo(q2[0], q2[1]))); fx.stroke();
    const e = pts[pts.length - 1]; fx.drawImage(sprite("rgba(210,245,255,1)"), e[0] - 22, e[1] - 22, 44, 44);
    fx.shadowBlur = 0; fx.globalCompositeOperation = "source-over";
  }

  function cursorAt(t) {
    let k2 = -1;
    for (let i = 0; i < CLICKS.length; i++) if (t >= CLICKS[i][2] - 0.25 && t <= CLICKS[i][3] + 0.25 && (k2 < 0 || CLICKS[i][0] <= t + 0.75)) k2 = i;
    if (k2 < 0) { opa(cur, 0); opa(rip, 0); opa(touch, 0); return; }
    const [tc, get, v0, v1, mode] = CLICKS[k2];
    const p1 = get();
    if (!p1) { opa(cur, 0); opa(rip, 0); opa(touch, 0); return; }
    let p0 = [p1[0] + 150, p1[1] + 120];
    if (k2 > 0 && CLICKS[k2 - 1][3] >= v0 - 0.3 && CLICKS[k2 - 1][0] < tc) { const pp = CLICKS[k2 - 1][1](); if (pp) p0 = pp; }
    const p = E.inOutCubic(seg(t, Math.max(v0, tc - 0.6), tc - 0.06));
    const x = lerp(p0[0], p1[0], p), y = lerp(p0[1], p1[1], p);
    const vis = Math.min(seg(t, v0 - 0.2, v0), 1 - seg(t, v1, v1 + 0.2));
    const pr = Math.max(0, 1 - Math.abs(t - tc) / 0.1);
    if (mode === "touch") {
      opa(cur, 0);
      touch.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) scale(${(1 - 0.25 * pr).toFixed(3)})`;
      opa(touch, vis * (0.3 + 0.7 * Math.max(pr, seg(t, tc - 0.3, tc) * (1 - seg(t, tc + 0.05, tc + 0.3)))));
    } else {
      opa(touch, 0);
      cur.style.transform = `translate(${(x - 3).toFixed(1)}px,${(y - 2).toFixed(1)}px) scale(${(1 - 0.14 * pr).toFixed(3)})`;
      opa(cur, vis);
    }
    const r = seg(t, tc, tc + 0.5);
    rip.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) scale(${(0.3 + 1.0 * E.outCubic(r)).toFixed(3)})`;
    opa(rip, r > 0 && r < 1 ? (1 - r) * 0.8 : 0);
  }

  // entrée / sortie d'un appareil dans sa fenêtre : il arrive de la droite et du fond, repart vers la gauche
  function stageDev(d, name, rest, t, extra = {}) {
    const [a, b] = WIN[name];
    if (t < a - 0.05 || t > b + 0.65) { pose(d, { o: 0 }); return 0; }
    const p = E.outQuart(seg(t, a, a + 1.0)), qx = E.inCubic(seg(t, b, b + 0.6));
    const o = clamp(seg(t, a, a + 0.3)) * (1 - seg(t, b + 0.2, b + 0.6));
    pose(d, Object.assign({}, rest, { x: (rest.x || 0) + 1000 * (1 - p) - 800 * qx, z: (rest.z || 0) - 700 * (1 - p) - 500 * qx,
                                      ry: (rest.ry || 0) - 34 * (1 - p) + 24 * qx, o, bl: 9 * (1 - clamp(seg(t, a, a + 0.6))) + 8 * qx }, extra));
    const sh = seg(t, a + 0.35, a + 1.45);                    // reflet qui balaie le verre à l'arrivée
    opa(d.sheen, sh > 0 && sh < 1 ? 1 : 0);
    if (sh > 0 && sh < 1) d.sheen.style.transform = `translateX(${lerp(-110, 110, E.inOutSine(sh)).toFixed(1)}%)`;
    pool(d.kind === "laptop" ? [rest.x || 0, (rest.y || 0) + 40, 500] : [rest.x || 0, (rest.y || 0) + d.obj.h / 2 + 30, 0], d.kind === "laptop" ? 1100 : 600, o * (1 - qx));
    return o;
  }

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

    // ---------------- logo (drop et fin), puis l'ordinateur s'ouvre entre la tablette et le téléphone
    const fin = t >= T.final - 0.3;
    const t0 = fin ? T.final : T.logo, tg = fin ? T.finTag : T.tag;
    const lgOn = (t >= T.logo - 0.1 && t < WIN.hero[1] + 0.5) || fin;
    if (lgOn) {
      const inn = E.outCubic(seg(t, t0 - 0.05, t0 + 0.7)), up = E.inOutCubic(seg(t, t0 + 0.75, t0 + 1.65));
      const wd = lerp(900, 430, up), hg = wd * 1224 / 3520, cy = lerp(500, 118, up);
      logoHud.style.transform = `translate(${(CX - wd / 2).toFixed(1)}px,${(cy - hg / 2).toFixed(1)}px) scale(${(wd / 900 * (0.94 + 0.06 * inn)).toFixed(4)})`;
      const out = fin ? 0 : seg(t, WIN.hero[1], WIN.hero[1] + 0.45);
      opa(logoHud, inn * (1 - out)); blur(logoHud, 14 * (1 - inn));
      const ta = E.outCubic(seg(t, tg - 0.15, tg + 0.5));
      tagHud.style.transform = `translate(${(CX - tagHud.offsetWidth / 2).toFixed(1)}px,${(lerp(660, 205, up) + 14 * (1 - ta)).toFixed(1)}px)`;
      tagHud.style.letterSpacing = (0.36 + 0.2 * (1 - ta)).toFixed(3) + "em";
      opa(tagHud, ta * (1 - out));
      const sa = fin ? E.outCubic(seg(t, T.finTag + 0.7, T.finTag + 1.5)) : 0;
      opa(subHud, sa);
      if (fin) subHud.style.transform = `translate(${(CX - subHud.offsetWidth / 2).toFixed(1)}px,${(1004 + 10 * (1 - sa)).toFixed(1)}px)`;
      const gl = Math.sin(Math.PI * seg(t, t0 - 0.1, t0 + 1.6));         // halo doux derrière le logo
      if (gl > 0.01) { const rg = bg.createRadialGradient(CX, cy, 0, CX, cy, 760); rg.addColorStop(0, `rgba(40,150,255,${(0.28 * gl).toFixed(3)})`); rg.addColorStop(1, "rgba(0,0,0,0)");
        bg.globalCompositeOperation = "lighter"; bg.fillStyle = rg; bg.fillRect(0, 0, VW, VH); bg.globalCompositeOperation = "source-over"; }
    } else { opa(logoHud, 0); opa(tagHud, 0); opa(subHud, 0); }
    {
      const name = fin ? "fin" : "hero", a = WIN[name][0], b = WIN[name][1];
      const on = t > a - 0.05 && t < b + 0.65;
      const ex = fin ? 0 : E.inCubic(seg(t, b, b + 0.6));
      [[H.L, "heroL", 0], [H.T, "heroT", 0.35], [H.P, "heroP", 0.5]].forEach(([d, k2, dl]) => {
        if (!on) { pose(d, { o: 0 }); return; }
        const p = E.outQuart(seg(t, a + dl, a + dl + 1.1)), r = REST[k2];
        const o = clamp(seg(t, a + dl, a + dl + 0.35)) * (1 - seg(t, b + 0.2, b + 0.6) * (fin ? 0 : 1));
        const open = E.inOutCubic(seg(t, a + 0.15, a + 1.5));
        pose(d, Object.assign({}, r, { x: r.x + (d === H.L ? 0 : Math.sign(r.x) * 700 * (1 - p)) - 800 * ex, y: r.y + (d === H.L ? 260 * (1 - p) : 0), z: (r.z || 0) - (d === H.L ? 500 : 300) * (1 - p) - 500 * ex,
                                       ry: (r.ry || 0) * (0.5 + 0.5 * p) + 24 * ex, lean: lerp(-86, 12, open), o, bl: 8 * (1 - clamp(seg(t, a + dl, a + dl + 0.6))) + 8 * ex }));
        if (d === H.L) opa(d.off, 1 - E.outCubic(seg(open, 0.35, 0.95)));
      });
      if (on) pool([0, 430, 520], 1500, clamp(seg(t, a + 0.4, a + 1.4)) * (1 - ex));
    }

    // ---------------- pointage
    if (stageDev(P1, "P1", REST.phone, t)) scrollD(P1, 150 * E.inOutCubic(seg(t, T.saved - 0.3, T.saved + 0.4)));
    // congés
    {
      const o = stageDev(L2, "L2", REST.laptop, t);
      const ra = o ? seg(t, T.rights - 0.1, T.rights + 0.35) * (1 - seg(t, WIN.L2[1] - 0.1, WIN.L2[1] + 0.3)) : 0;
      opa(rule.el, ra);
      if (ra > 0.01) {
        const P = scrPt(L2, 900, 480), e = E.outCubic(seg(t, T.rights - 0.1, T.rights + 0.6));
        rule.setM(M4.chain(L2.obj.M, M4.T(L2.sx + 900, L2.sy + 480, 60 + 190 * e), M4.S(1.02), M4.T(-490, -135, 0)));
        const f = E.inOutCubic(seg(t, T.rights + 0.2, T.seniority + 0.2));
        ruleFill.style.width = (100 * f).toFixed(1) + "%"; ruleKnob.style.left = (100 * f).toFixed(1) + "%";
        setHTML(ruleKnob, ic(t >= T.seniority + 0.15 ? "unlock" : "lock")); ruleKnob.style.color = t >= T.seniority + 0.15 ? "#129266" : "#008ff1";
      }
    }
    // absences
    {
      const o = stageDev(T3, "T3", REST.tablet, t);
      if (o) scrollD(T3, 130 * E.inOutCubic(seg(t, T.absSend + 0.2, T.rh)));
      const pa = o ? seg(t, T.proof - 0.25, T.proof + 0.05) * (1 - seg(t, T.fileIn, T.fileIn + 0.12)) : 0;
      opa(pdf.el, pa);
      if (pa > 0.01) {
        const up = docD(T3).querySelector(film("abs-upload")).getBoundingClientRect();
        const P1w = scrPt(T3, up.left + up.width / 2, up.top + up.height / 2), P2w = [P1w[0] - 1250, P1w[1] - 420, P1w[2] + 600];
        const f = E.inOutCubic(seg(t, T.proof - 0.25, T.fileIn));
        const Pp = mix3(P2w, [P1w[0], P1w[1], P1w[2] + 40], f);
        pdf.place({ x: Pp[0], y: Pp[1], z: Pp[2], rz: -14 * (1 - f), ry: 26 * (1 - f) - 13, s: 1.2 - 0.6 * f });
      }
    }
    // signature : la feuille (imprimer, signer, scanner), puis le portable, la fenêtre sortie, le téléphone avec le code
    {
      const [a, b] = WIN.old;
      const pa = clamp(seg(t, a + 0.2, a + 0.7)) * (1 - seg(t, b - 0.05, b + 0.3));
      opa(paper.el, pa);
      if (pa > 0.01) {
        const p = E.outQuart(seg(t, a + 0.2, a + 1.2)), ex = E.inCubic(seg(t, b - 0.05, b + 0.3));
        paper.place({ x: 620 + 500 * (1 - p), y: -60 - 200 * ex, z: 280 - 500 * (1 - p) + 500 * ex, ry: -16 - 20 * (1 - p), rz: 3, s: 1.05 });
        blur(paper.el, 8 * (1 - clamp(seg(t, a + 0.2, a + 0.7))) + 10 * ex);
        const out = E.outCubic(seg(t, T.kImp - 0.35, T.kImp + 0.4));
        paper.el.style.clipPath = `inset(0 0 ${(100 * (1 - out) * 0.92).toFixed(1)}% 0)`;
        paperInk.style.strokeDashoffset = (1 - E.inOutSine(seg(t, T.kSig - 0.1, T.kSig + 0.5))).toFixed(3);
        const sc = seg(t, T.kScan - 0.1, T.kScan + 0.6);
        paperScan.style.top = lerp(-80, 820, sc).toFixed(0) + "px"; paperScan.style.opacity = (sc > 0 && sc < 1 ? 1 : 0).toFixed(2);
        pool([620, 420, 280], 520, pa * 0.8);
      }
      const o = stageDev(L4, "L4", REST.laptop, t);
      const pIn = E.outQuart(seg(t, T.code - 0.15, T.code + 0.8)), pOut = E.inCubic(seg(t, T.signed + 0.45, T.signed + 0.95));
      const po = o ? clamp(seg(t, T.code - 0.15, T.code + 0.2)) * (1 - seg(t, T.signed + 0.6, T.signed + 0.95)) : 0;
      pose(P4, Object.assign({}, REST.P4, { x: REST.P4.x + 900 * (1 - pIn) + 900 * pOut, z: REST.P4.z - 300 * (1 - pIn), ry: REST.P4.ry - 30 * (1 - pIn), o: po, bl: 8 * (1 - clamp(seg(t, T.code - 0.15, T.code + 0.4))) }));
      const nIn = E.outCubic(seg(t, T.mail - 0.15, T.mail + 0.35));
      notif.style.transform = `translateY(${(-150 * (1 - nIn)).toFixed(1)}px)`; notif.style.opacity = nIn.toFixed(2);
      const up = E.outCubic(seg(t, T.open + 0.12, T.open + 0.8)), down = E.inOutCubic(seg(t, T.signed + 0.05, T.signed + 0.45));
      const av = o ? up * (1 - down) : 0;
      opa(DLG.el, o && t > T.open + 0.1 && t < T.signed + 0.47 ? clamp(seg(t, T.open + 0.1, T.open + 0.2)) * (1 - seg(t, T.signed + 0.4, T.signed + 0.47)) : 0);
      liftClip(DLG, dlgGlow, L4, av, 170, t);
      // lueur de la plume, balayage de lumière sur le document signé
      const pp = penPoint(E.inOutSine(seg(t, T.draw + 0.15, T.drawEnd)));
      if (o && pp && t < T.drawEnd && DLG.rect) {
        const cv = docOf("sign").querySelector(film("sign-canvas"));
        if (cv) { const r = cv.getBoundingClientRect(); const Pw = DLG.world(r.left + pp[0] * r.width - DLG.rect.x, r.top + pp[1] * r.height - DLG.rect.y);
          fx.globalCompositeOperation = "lighter"; dot3(fx, Pw, 26, "rgba(95,212,255,1)", 0.85); fx.globalCompositeOperation = "source-over"; }
      }
      const pv = docD(L4).querySelector(".mw-preview-stage");
      if (o && pv) {
        const q2 = pv.getBoundingClientRect(), p = seg(t, T.signed + 0.55, T.signed + 1.35);
        if (p > 0 && p < 1) { const v = lerp(q2.top - 30, q2.bottom + 30, p);
          fx.globalCompositeOperation = "lighter"; line3(fx, scrPt(L4, q2.left, v), scrPt(L4, q2.right, v), { color: "rgba(95,212,255,1)", width: 8, alpha: Math.sin(Math.PI * p), glow: 36 }); fx.globalCompositeOperation = "source-over"; }
      }
    }
    // demandes
    if (stageDev(P5, "P5", REST.phone, t)) scrollD(P5, 200 * E.inOutCubic(seg(t, T.fill - 0.6, T.fill - 0.1)) + 360 * E.inOutCubic(seg(t, T.clics + 0.35, T.process - 0.05)));
    // contenu
    stageDev(T6, "T6", REST.tablet, t);
    // mail, support
    stageDev(L7, "L7", REST.laptop, t);
    if (stageDev(P7, "P7", REST.phone, t)) scrollD(P7, 200 * E.inOutCubic(seg(t, T.tickType - 0.4, T.tickType)) + 360 * E.inOutCubic(seg(t, T.ticket + 0.2, T.charge - 0.05)));
    // agent : le panneau sort de l'écran avec une lueur vivante, les sources apparaissent à gauche, reliées par des fils de lumière
    {
      const o = stageDev(L8, "L8", REST.laptop, t);
      const up = E.outCubic(seg(t, T.launch - 0.05, T.launch + 0.8)), down = E.inOutCubic(seg(t, WIN.L8[1] - 0.2, WIN.L8[1] + 0.3));
      const av = o ? up * (1 - down) : 0;
      opa(PNL.el, o && t > T.launch - 0.07 ? clamp(seg(t, T.launch - 0.07, T.launch + 0.05)) * (1 - seg(t, WIN.L8[1] + 0.2, WIN.L8[1] + 0.35)) : 0);
      liftClip(PNL, pnlGlow, L8, av, 170, t, 120);
      SRC.forEach((ob, i) => {
        const tb = T.chips[i], a = o ? seg(t, tb - 0.3, tb + 0.05) * (1 - seg(t, WIN.L8[1] - 0.3, WIN.L8[1])) : 0;
        opa(ob.el, a);
        if (a < 0.01 || !PNL.rect) return;
        const p = E.outQuart(seg(t, tb - 0.3, tb + 0.5));
        const B = PNL.world(-330, 215 + 165 * i);
        ob.place({ x: B[0] - 120 * (1 - p), y: B[1], z: B[2] + 40, ry: 8, s: 0.95 });
        blur(ob.el, 8 * (1 - clamp(seg(t, tb - 0.3, tb + 0.2))));
        const A = PNL.world(20, 250 + 120 * i), ba = seg(t, tb, tb + 0.25) * (1 - seg(t, T.answer + 0.4, T.answer + 1.0));
        thread([B[0] + 224, B[1], B[2] + 40], A, 30, E.inOutCubic(seg(t, tb, tb + 0.5)), 0.9 * ba);
      });
    }

    // ---------------- accroche : cadran fin pendant « un temps fou »
    {
      const a0 = w("hook", "Au"), a1 = segT("hook", 1);
      const da = seg(t, a0 - 0.1, a0 + 0.4) * (1 - seg(t, a1 - 0.5, a1 - 0.15));
      if (da > 0.01) {
        const dg = E.inOutCubic(seg(t, a0, w("hook", "fou") + 0.5)), r0 = 400, cy = 512;
        fx.globalCompositeOperation = "lighter"; fx.lineCap = "round";
        for (let k2 = 0; k2 < 60; k2++) {
          const ang = k2 / 60 * Math.PI * 2 - Math.PI / 2, len = k2 % 5 ? 12 : 30;
          fx.globalAlpha = da * (k2 % 5 ? 0.28 : 0.6); fx.strokeStyle = "#cfe9ff"; fx.lineWidth = k2 % 5 ? 2 : 3;
          fx.beginPath(); fx.moveTo(CX + Math.cos(ang) * r0, cy + Math.sin(ang) * r0); fx.lineTo(CX + Math.cos(ang) * (r0 - len), cy + Math.sin(ang) * (r0 - len)); fx.stroke();
        }
        const hm = -Math.PI / 2 + dg * Math.PI * 2 * 11.5, hh2 = -Math.PI / 2 + (8 + 11.5 * dg) / 12 * Math.PI * 2;
        fx.globalAlpha = da * 0.5; fx.strokeStyle = "#5fd4ff"; fx.lineWidth = 3;
        fx.beginPath(); fx.moveTo(CX + Math.cos(hm) * 300, cy + Math.sin(hm) * 300); fx.lineTo(CX + Math.cos(hm) * 372, cy + Math.sin(hm) * 372); fx.stroke();
        fx.lineWidth = 5; fx.beginPath(); fx.moveTo(CX + Math.cos(hh2) * 330, cy + Math.sin(hh2) * 330); fx.lineTo(CX + Math.cos(hh2) * 372, cy + Math.sin(hh2) * 372); fx.stroke();
        fx.globalCompositeOperation = "source-over";
      }
    }

    // ---------------- textes : apparition douce, ligne à ligne ou mot à mot
    TXT.forEach(x => {
      if (t < x.t0 - 0.05 || t > x.t1 + 0.4) { opa(x.el, 0); return; }
      const pin = E.outCubic(seg(t, x.t0, x.t0 + 0.6)), pout = E.inOutCubic(seg(t, x.t1, x.t1 + 0.35));
      const wd = x.el.offsetWidth, hg = x.el.offsetHeight;
      const x0 = x.pos.align === "center" ? x.pos.x - wd / 2 : x.pos.x;
      const y0 = x.kind.startsWith("cap") ? x.pos.y - hg / 2 : (x.pos.align === "center" ? x.pos.y - hg / 2 + 100 : x.pos.y);
      x.el.style.transform = `translate(${x0.toFixed(1)}px,${(y0 + (x.words ? 0 : 22 * (1 - pin)) - 12 * pout).toFixed(1)}px)`;
      opa(x.el, (x.words ? clamp(seg(t, x.t0, x.t0 + 0.1)) : pin) * (1 - pout));
      blur(x.el, (x.words ? 0 : 8 * (1 - pin)) + 6 * pout);
      if (x.words) x.words.forEach(([e, tw]) => {
        const p = E.outCubic(seg(t, tw, tw + 0.5));
        e.style.opacity = p.toFixed(3); e.style.transform = `translateY(${(20 * (1 - p)).toFixed(1)}px)`; e.style.filter = p < 0.99 ? `blur(${(7 * (1 - p)).toFixed(1)}px)` : "none";
      });
      if (x.strike !== undefined) { const kk = E.inOutCubic(seg(t, x.strike, x.strike + 0.45)); qa(x.el, "s").forEach((e, i) => e.style.setProperty("--k", clamp(kk * 1.3 - i * 0.12).toFixed(3))); x.el.style.color = `rgba(245,247,250,${(1 - 0.55 * kk).toFixed(3)})`; }
    });
    cursorAt(t);
    opa(vign, 0.55);
    const fr = Math.round(t * 30);
    grain.style.transform = `translate(${(hash(fr) * 64 - 32).toFixed(0)}px,${(hash(fr + 7) * 64 - 32).toFixed(0)}px)`;
    opa(grain, 0.16);
  };
})();
