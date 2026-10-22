/* MyWebtel — film de présentation (1920×1080, 30 i/s).
 * Toute l'image est une fonction du temps : renderAt(t) pose chaque élément. Aucune animation CSS automatique,
 * donc le rendu image par image (render.js) est exact et reproductible.
 * Les instants viennent de window.TL (build/mywebtel/timeline.json, produit par vo.py) : l'image suit la voix.
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
    outExpo: x => x >= 1 ? 1 : 1 - Math.pow(2, -10 * x), inOutSine: x => -(Math.cos(Math.PI * x) - 1) / 2,
    outBack: (x, s = 1.0) => { x -= 1; return 1 + (s + 1) * x * x * x + s * x * x; },
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
  const partT = (id, i, k) => SC[id].segs[i].parts[k];
  // instant approximatif d'un mot dans un segment (proportionnel aux caractères ; ±0,15 s)
  function wordT(id, i, needle) {
    const s = SC[id].segs[i], k = s.text.toLowerCase().indexOf(needle.toLowerCase());
    if (k < 0) throw new Error("mot absent : " + needle);
    return s.start + (s.end - s.start) * (k / s.text.length);
  }
  // pseudo-hasard reproductible
  function rng(seed) { let s = seed >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }

  const ICON = {
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    file: '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
    inbox: '<path d="M3 13l3-8h12l3 8v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 13h5l1 3h6l1-3h5"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.5 3.4-5.5 6.5-5.5s5.7 2 6.5 5.5"/><circle cx="17" cy="9" r="2.8"/><path d="M17 14.5c2.4.3 4 1.9 4.6 4.5"/>',
    megaphone: '<path d="M3 11v2a1 1 0 0 0 1 1h3l6 4V6L7 10H4a1 1 0 0 0-1 1z"/><path d="M17 9a4 4 0 0 1 0 6"/>',
    sliders: '<path d="M4 7h10M18 7h2M4 17h4M12 17h8"/><circle cx="16" cy="7" r="2"/><circle cx="10" cy="17" r="2"/>',
    lock: '<rect x="5" y="11" width="14" height="10" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    download: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    message: '<path d="M4 5h16v11H9l-5 4z"/>',
    eye: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    bell: '<path d="M6 16v-5a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    home: '<path d="M4 11l8-7 8 7v9a1 1 0 0 1-1 1h-5v-6h-4v6H5a1 1 0 0 1-1-1z"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v4h4M12 7v5l3 2"/>',
    send: '<path d="M21 3L10 14M21 3l-7 18-4-7-7-4z"/>',
    login: '<path d="M10 17l5-5-5-5M15 12H3M14 4h5a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-5"/>',
    logout: '<path d="M14 7l5 5-5 5M19 12H8M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5"/>',
    coffee: '<path d="M4 9h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M16 10h2a2.5 2.5 0 0 1 0 5h-2M8 3v3M12 3v3"/>',
    back: '<path d="M9 14l-5-5 5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-2"/>',
    briefcase: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2M3 13h18"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4.5 4.5-7 8-7s7 2.5 8 7"/>',
    building: '<rect x="4" y="3" width="16" height="18" rx="1.5"/><path d="M8 7h2M14 7h2M8 11h2M14 11h2M8 15h2M14 15h2M10 21v-3h4v3"/>',
    heart: '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    server: '<rect x="4" y="4" width="16" height="7" rx="1.5"/><rect x="4" y="13" width="16" height="7" rx="1.5"/><path d="M8 7.5h.01M8 16.5h.01"/>',
    paperclip: '<path d="M20 11.5l-8.2 8.2a5 5 0 0 1-7.1-7.1l8.5-8.5a3.5 3.5 0 0 1 5 5L9.7 17.6a2 2 0 0 1-2.8-2.8L14.5 7"/>',
    mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/>',
    table: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M3 14h18M9 4v16"/>',
    pen: '<path d="M4 20l4-1 11-11-3-3L5 16z"/>',
    phone: '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    printer: '<path d="M7 9V3h10v6M7 17H4v-6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v6h-3"/><rect x="7" y="14" width="10" height="7"/>',
    archive: '<rect x="3" y="4" width="18" height="5" rx="1"/><path d="M5 9v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9M10 13h4"/>',
    key: '<circle cx="8" cy="15" r="4"/><path d="M11 12l9-9M17 6l3 3"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.2 3 14.8 0 18M12 3c-3 3.2-3 14.8 0 18"/>',
    chevron: '<path d="M9 6l6 6-6 6"/>',
  };
  const ic = (n, cls = "") => `<svg class="i ${cls}" viewBox="0 0 24 24">${ICON[n]}</svg>`;
  function h(html) { const d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstElementChild; }
  function add(parent, html) { const e = h(html); parent.appendChild(e); return e; }
  const q = (root, sel) => root.querySelector(sel);
  // pose d'un élément : o opacité, x/y translation, s échelle, r rotation, rx/ry rotation 3D, p perspective, blur
  function st(el, o) {
    const tr = [];
    if (o.c) tr.push("translate(-50%,-50%)");
    if (o.x || o.y) tr.push(`translate3d(${(o.x || 0).toFixed(2)}px,${(o.y || 0).toFixed(2)}px,0)`);
    if (o.p) tr.push(`perspective(${o.p}px)`);
    if (o.rx) tr.push(`rotateX(${o.rx.toFixed(3)}deg)`);
    if (o.ry) tr.push(`rotateY(${o.ry.toFixed(3)}deg)`);
    if (o.r) tr.push(`rotate(${o.r.toFixed(3)}deg)`);
    if (o.s !== undefined && o.s !== 1) tr.push(`scale(${o.s.toFixed(4)})`);
    el.style.transform = tr.join(" ");
    if (o.o !== undefined) { const v = clamp(o.o); el.style.opacity = v.toFixed(4); el.style.visibility = v <= 0.002 ? "hidden" : "visible"; }
    if (o.blur !== undefined) el.style.filter = o.blur > 0.05 ? `blur(${o.blur.toFixed(2)}px)` : "none";
  }
  // display (et non visibility) : un enfant en « visibility: visible » resterait affiché dans une scène masquée
  const show = (el, on) => { el.style.display = on ? "block" : "none"; };
  // apparition standard : montée douce + fondu (ease out expo), sortie : fondu court
  function enter(t, t0, dur = 0.7, dy = 26) { const p = E.outExpo(seg(t, t0, t0 + dur)); return { o: clamp(p * 1.4), y: (1 - p) * dy }; }

  // ------------------------------------------------------------------ composants d'interface
  const AV = ["#112d50", "#2b6a8f", "#16784a", "#7a4e9b", "#a0522d", "#b42318", "#3b5bdb", "#0f766e"];
  const avatar = (txt, size, k) => `<div class="av" style="width:${size}px;height:${size}px;font-size:${size * 0.38}px;background:${AV[k % AV.length]}">${txt}</div>`;
  const navItems = [["home", "Tableau de bord"], ["clock", "Pointage"], ["calendar", "Congés"], ["file", "Documents"],
                    ["users", "Collaborateurs"], ["megaphone", "Contenu"], ["inbox", "Devis entrants"], ["history", "Historique"], ["sliders", "Réglages"]];
  function tilesHTML(cls = "") {
    return `<div class="grid6 ${cls}">
      <div class="tile" data-m="pointage"><h4>${ic("clock")}Ma journée</h4><span class="pill p-green"><span class="dot"></span>Session de travail active</span>
        <div style="display:flex;gap:26px;margin-top:6px"><div><div class="sub">Arrivée</div><div class="big">08:00</div></div><div><div class="sub">Départ</div><div class="big muted">—</div></div></div></div>
      <div class="tile" data-m="conges"><h4>${ic("calendar")}Congés</h4><div class="big">20 jours</div><div class="sub">Solde disponible</div><div class="bar"><i style="width:83%"></i></div></div>
      <div class="tile" data-m="documents"><h4>${ic("file")}Documents</h4><div style="font-weight:600;font-size:17px">Fiche de paie · Octobre</div><span class="pill p-sel" style="align-self:flex-start">Nouveau</span></div>
      <div class="tile" data-m="annonces"><h4>${ic("megaphone")}Annonces</h4><div style="font-weight:600;font-size:17px">Horaires de fin d'année</div><div class="sub">Direction · il y a 2 h</div></div>
      <div class="tile" data-m="devis"><h4>${ic("inbox")}Devis entrants</h4><div class="big">3</div><div class="sub">demandes en cours</div></div>
      <div class="tile" data-m="equipe"><h4>${ic("users")}Collaborateurs</h4><div style="display:flex">${[0, 1, 2, 3, 4].map(k => `<div style="margin-left:${k ? -10 : 0}px;border:2px solid #fff;border-radius:50%">${avatar("ABCDE"[k], 38, k)}</div>`).join("")}</div><div class="sub">12 présents aujourd'hui</div></div>
      ${cls ? "" : `<div class="tile wide"><div style="flex:1.4"><h4>${ic("clock")}Présences de la semaine</h4><div class="chart">${[["Lun", 82], ["Mar", 94], ["Mer", 88], ["Jeu", 76], ["Ven", 91]].map(([d, v]) => `<div><i class="${d === "Mer" ? "today" : ""}" style="height:${Math.round(v * 1.1)}px"></i>${d}</div>`).join("")}</div></div>
        <div style="flex:1;border-left:1px solid var(--line);padding-left:28px"><h4>${ic("calendar")}À venir</h4>${[["Validation des congés", "2 demandes"], ["Note RH à lire", "Aujourd'hui"], ["Devis à rappeler", "Jeudi"]].map(([a, b]) => `<div class="row" style="justify-content:space-between;padding:7px 0;font-size:14px"><span style="font-weight:600">${a}</span><span class="muted">${b}</span></div>`).join("")}</div></div>`}
    </div>`;
  }
  function dashboardHTML() {
    return `<div class="app">
      <aside class="side"><div class="brand"><div class="bm">W</div>MyWebtel</div>
        ${navItems.map(([i, l], k) => `<div class="nav ${k === 0 ? "on" : ""}">${ic(i)}${l}</div>`).join("")}</aside>
      <section class="main"><div class="top"><div><div class="hello">Bonjour Aïssatou</div><div class="muted" style="margin-top:4px">Mercredi 22 octobre · WTL-00041</div></div>
        <div style="display:flex;align-items:center;gap:14px"><div style="font-size:22px;color:var(--muted)">${ic("bell")}</div>${avatar("AN", 42, 1)}</div></div>
        ${tilesHTML()}</section></div>`;
  }
  function phoneDashHTML() {
    return `<div class="fill" style="padding:56px 22px 22px;display:flex;flex-direction:column;gap:14px;font-size:14px">
      <div style="display:flex;align-items:center;justify-content:space-between"><div style="display:flex;align-items:center;gap:10px;font-weight:700;font-size:17px"><div class="bm" style="width:34px;height:34px;border-radius:10px;font-size:19px">W</div>MyWebtel</div>${avatar("AN", 34, 1)}</div>
      <div class="hello" style="font-size:26px">Bonjour Aïssatou</div>
      ${tilesHTML("phone-tiles")}</div>`;
  }
  function tabletDashHTML() {
    return `<div class="fill" style="padding:40px 30px;display:flex;flex-direction:column;gap:18px;font-size:14px">
      <div style="display:flex;align-items:center;justify-content:space-between"><div style="display:flex;align-items:center;gap:12px;font-weight:700;font-size:19px"><div class="bm" style="width:38px;height:38px;border-radius:11px;font-size:21px">W</div>MyWebtel</div>${avatar("AN", 38, 1)}</div>
      <div class="hello">Bonjour Aïssatou</div>${tilesHTML("tablet-tiles")}</div>`;
  }
  const extraCSS = `
    .phone-tiles { grid-template-columns: 1fr; gap: 12px; } .phone-tiles .tile { min-height: 0; padding: 16px; }
    .phone-tiles .tile:nth-child(n+5) { display: none; } .phone-tiles .big { font-size: 28px; }
    .tablet-tiles { grid-template-columns: 1fr 1fr; gap: 14px; } .tablet-tiles .tile { min-height: 150px; }
    .cursor { position: absolute; left: 0; top: 0; width: 34px; height: 44px; z-index: 50; filter: drop-shadow(0 4px 8px rgba(0,0,0,.25)); }
    .ripple { position: absolute; width: 90px; height: 90px; margin: -45px 0 0 -45px; border-radius: 50%; border: 3px solid rgba(17,45,80,.55); z-index: 49; }
    .row { display: flex; align-items: center; gap: 16px; }
    .sw { width: 52px; height: 30px; border-radius: 99px; background: #cfd7e2; position: relative; flex: none; }
    .sw i { position: absolute; top: 3px; left: 3px; width: 24px; height: 24px; border-radius: 50%; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,.2); }
  `;
  document.head.appendChild(h(`<style>${extraCSS}</style>`));
  const CURSOR = `<svg class="cursor" viewBox="0 0 34 44"><path d="M3 2l26 24H16l7 14-5 2-7-14-8 8z" fill="#fff" stroke="#061427" stroke-width="2.4" stroke-linejoin="round"/></svg>`;
  // centre d'un élément dans le repère de l'écran (transformations de caméra comprises)
  function centerOf(el) { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; }
  // curseur (posé dans la scène, hors caméra) qui va de (x0,y0) à (x1,y1) entre t0 et t1, puis clique à tc
  function cursorAt(el, rip, t, t0, t1, x0, y0, x1, y1, tc) {
    const p = E.inOutCubic(seg(t, t0, t1));
    const press = tc ? Math.max(0, 1 - Math.abs(t - tc) / 0.12) : 0;
    const x = lerp(x0, x1, p), y = lerp(y0, y1, p);
    st(el, { x: x - 3, y: y - 2, s: 1 - 0.12 * press, o: seg(t, t0 - 0.3, t0) });
    if (rip) ripple(rip, t, tc, x, y);
  }
  function ripple(rip, t, tc, x, y) {
    const r = tc ? seg(t, tc, tc + 0.55) : 0;
    st(rip, { x, y, s: 0.3 + 0.9 * E.outCubic(r), o: r > 0 && r < 1 ? (1 - r) * 0.9 : 0 });
  }

  // ------------------------------------------------------------------ scènes
  const scenes = [];
  function scene(id, build, anim, bg) {
    const el = add(stage, `<div class="scene" data-id="${id}" style="${bg ? "background:" + bg : ""}"></div>`);
    const cam = add(el, `<div class="layer cam"></div>`);
    const ctx = build(cam, el) || {};
    scenes.push({ id, el, cam, ctx, anim });
  }
  // fondu enchaîné : visible de a-fin à b+fout
  const vis = (t, a, b, fin = 0.5, fout = 0.5) => Math.min(seg(t, a - fin / 2, a + fin / 2), 1 - seg(t, b - fout / 2, b + fout / 2));
  const drift = (t, a, b, amt = 0.03) => 1 + amt * E.inOutSine(seg(t, a, b));
  const NIGHT = "radial-gradient(1300px 900px at 50% 46%, #10305a 0%, #0a1f3a 38%, #061427 72%)";
  const PAPER = "radial-gradient(1400px 900px at 50% 40%, #ffffff 0%, #f4f7fb 60%, #edf2f8 100%)";

  // ---------- 1. ouverture : les démarches éparpillées (fond nuit)
  scene("hook", (cam) => {
    const big = [["clock", "Pointage", "Arrivée · 08:02", 210, 230], ["calendar", "Congés", "Demande du 21 au 24 déc.", 1130, 190],
                 ["file", "Fiche de paie", "Octobre 2026 · PDF", 300, 690], ["inbox", "Demande de devis", "Reçue par e-mail", 1120, 680]];
    const cards = big.map(([i, a, b, x, y]) => add(cam, `<div class="glass abs" style="left:${x}px;top:${y}px"><div class="ic">${ic(i)}</div><div><div class="t1">${a}</div><div class="t2">${b}</div></div></div>`));
    const labels = [["mail", "E-mail"], ["table", "Tableur"], ["bell", "Relance"], ["pen", "Signature"], ["file", "Formulaire"], ["megaphone", "Note de service"],
      ["paperclip", "Justificatif"], ["check", "Validation"], ["phone", "Appel"], ["calendar", "Planning"], ["clock", "Rappel"], ["key", "Mot de passe"],
      ["printer", "Impression"], ["archive", "Classeur"], ["message", "Message"], ["users", "Réunion"], ["file", "Version 2"], ["file", "Version finale"],
      ["mail", "Pièce jointe"], ["table", "Export"], ["history", "Relance n°2"], ["paperclip", "Scan"], ["pen", "Brouillon"], ["inbox", "Accusé de réception"],
      ["file", "Attestation"], ["message", "Commentaire"], ["send", "Transfert"], ["clock", "Badge"], ["calendar", "Agenda"], ["table", "Récapitulatif"],
      ["mail", "Copie"], ["check", "À valider"], ["archive", "Archive"], ["bell", "Rappel"], ["file", "Contrat"], ["send", "Envoi"]];
    const R = rng(7), minis = [];
    labels.forEach(([i, l], k) => {
      let x, y, tries = 0;
      do { x = 60 + R() * 1660; y = 50 + R() * 960; tries++; }
      while (tries < 400 && ((x > 560 && x < 1300 && y > 380 && y < 660)
             || big.some(b => x > b[3] - 230 && x < b[3] + 520 && y > b[4] - 70 && y < b[4] + 150)
             || minis.some(m => Math.abs(m.x - x) < 230 && Math.abs(m.y - y) < 62)));
      minis.push({ el: add(cam, `<div class="mini abs" style="left:${x}px;top:${y}px">${ic(i)}${l}</div>`), x, y, d: R() * 0.25, ph: R() * 6.28 });
    });
    return { cards, big, minis };
  }, (t, s) => {
    const c = s.ctx, sc = SC.hook;
    // le fond nuit reste jusqu'à la révélation du logo (scène suivante)
    const alive = t < S0("reveal") + 6;
    show(s.el, alive);
    if (!alive) return;
    s.cam.style.transform = `scale(${drift(t, 0, 15, 0.04)})`;
    const conv = E.inCubic(seg(t, 11.6, 14.1));             // tout converge vers le centre pendant la question
    c.cards.forEach((el, k) => {
      const a = enter(t, segT("hook", k) - 0.12, 0.9, 30);
      const fx = Math.sin(t * 0.6 + k * 1.7) * 6, fy = Math.cos(t * 0.5 + k) * 5;
      const [, , , x, y] = c.big[k];
      const dx = (960 - (x + 240)) * conv, dy = (540 - (y + 65)) * conv;
      st(el, { x: fx + dx, y: a.y + fy + dy, s: (1 - 0.92 * conv) * lerp(0.96, 1, a.o), o: a.o * (1 - 0.25 * seg(t, 8.2, 9.5)) * (1 - seg(t, 13.2, 14.1)) });
    });
    c.minis.forEach((m, k) => {
      const t0 = segT("hook", 4) - 0.05 + k * 0.045 + m.d;
      const p = E.outExpo(seg(t, t0, t0 + 0.6));
      const fx = Math.sin(t * 0.7 + m.ph) * 8, fy = Math.cos(t * 0.6 + m.ph) * 6;
      const dx = (960 - m.x) * conv, dy = (540 - m.y) * conv;
      st(m.el, { x: fx + dx, y: fy + dy + (1 - p) * 14, s: lerp(0.85, 1, p) * (1 - 0.92 * conv), o: p * 0.85 * (1 - seg(t, 13.0, 14.0)) });
    });
  }, NIGHT);

  // ---------- 2. révélation : le point devient la marque, l'iris ouvre sur le blanc
  scene("reveal", (cam, el) => {
    const glow = add(cam, `<div class="center" style="width:420px;height:420px;border-radius:50%;background:radial-gradient(circle, rgba(120,170,255,.45) 0%, rgba(120,170,255,0) 65%)"></div>`);
    const iris = add(el, `<div class="center" style="width:200px;height:200px;border-radius:50%;background:${PAPER.replace("radial-gradient(1400px 900px at 50% 40%,", "radial-gradient(circle,")}"></div>`);
    el.appendChild(cam);                                   // la caméra passe au-dessus de l'iris
    const lock = add(cam, `<div class="center" style="display:flex;align-items:center;gap:36px"><div class="bm">W</div><div class="wmw" style="overflow:hidden"><div class="wordmark">My<b>Webtel</b></div></div></div>`);
    const eyebrow = add(cam, `<div class="center eyebrow" style="margin-top:118px">Intranet · Webtel</div>`);
    return { glow, iris, lock, bm: q(lock, ".bm"), wmw: q(lock, ".wmw"), wm: q(lock, ".wordmark"), eyebrow };
  }, (t, s) => {
    const c = s.ctx, a = S0("reveal"), logo = segT("reveal", 1);
    const alive = t > a + 1.6 && t < S1("reveal") + 0.8;
    show(s.el, alive);
    if (!alive) return;
    s.el.style.background = "transparent";
    if (!c.ww) c.ww = c.wm.getBoundingClientRect().width;  // largeur du mot (après chargement des polices)
    // point lumineux puis carré de marque (avant le logo, sur fond nuit)
    const pre = E.outExpo(seg(t, a + 2.0, a + 3.0));
    const pulse = 1 + 0.025 * Math.sin((t - a) * 3.2) * (1 - seg(t, logo - 0.2, logo));
    const pop = spring(t - logo, 0.62, 2.4);
    const bmScale = t < logo ? lerp(0.08, 0.62, pre) * pulse : lerp(0.62, 1, pop);
    st(c.glow, { c: true, s: lerp(0.4, 1.1, pre) + 0.4 * seg(t, logo, logo + 0.6), o: pre * (1 - seg(t, logo + 0.1, logo + 0.7)) });
    // iris : le blanc s'ouvre depuis la marque
    const ir = E.outCubic(seg(t, logo + 0.02, logo + 0.85));
    st(c.iris, { c: true, s: ir * 24, o: t >= logo ? 1 : 0 });
    // le mot glisse depuis la marque
    const wr = E.outExpo(seg(t, logo + 0.25, logo + 1.15));
    const gap = 36;
    c.wmw.style.width = (c.ww * wr).toFixed(1) + "px";
    const out = E.inCubic(seg(t, S1("reveal") - 0.55, S1("reveal") + 0.1));
    // la marque reste au centre pendant que le mot se déroule, puis l'ensemble se recentre
    st(c.lock, { c: true, x: (gap + c.ww * wr) / 2 * (1 - wr), y: -36 * out, s: 1 - 0.06 * out, o: (t < logo ? pre : 1) * (1 - out) });
    c.bm.style.transform = `scale(${bmScale.toFixed(4)})`;
    // sur la nuit : carré blanc, W marine ; au logo, inversion sur le blanc qui s'ouvre
    c.bm.style.background = t < logo ? "#ffffff" : "var(--navy)";
    c.bm.style.color = t < logo ? `rgba(17,45,80,${seg(t, a + 2.8, a + 3.6).toFixed(3)})` : "#fff";
    c.bm.style.boxShadow = t < logo ? `0 0 ${60 * pre}px rgba(160,200,255,${0.55 * pre})` : "none";
    c.wm.style.color = "var(--ink)";
    const eb = enter(t, segT("reveal", 2) - 0.1, 0.8, 14);
    st(c.eyebrow, { c: true, y: eb.y - 36 * out, o: eb.o * (1 - out) });
  }, null);

  // ---------- 3. vision : tout est réuni (ordinateur + modules)
  scene("vision", (cam) => {
    const lap = add(cam, `<div class="laptop" style="left:290px;top:96px;transform-origin:670px 900px"><div class="lid"><div class="scr">${dashboardHTML()}</div></div><div class="base"></div></div>`);
    const mods = [["users", "Collaborateurs", "collaborateurs", 46, 250], ["clock", "Horaires", "horaires", 46, 470], ["calendar", "Congés", "congés", 46, 690],
                  ["file", "Documents", "documents", 1574, 250], ["megaphone", "Annonces", "annonces", 1574, 470], ["inbox", "Devis", "devis", 1574, 690]];
    const tiles = mods.map(([i, l, w, x, y]) => ({ el: add(cam, `<div class="card abs" style="left:${x}px;top:${y}px;width:300px;padding:20px 22px;display:flex;align-items:center;gap:16px;border-radius:20px"><div style="width:50px;height:50px;border-radius:14px;background:var(--sel-soft);color:var(--navy);display:grid;place-items:center;font-size:26px">${ic(i)}</div><div style="font-weight:600;font-size:22px">${l}</div></div>`), w, x, y }));
    return { lap, tiles, dashTiles: Array.from(lap.querySelectorAll(".tile")) };
  }, (t, s) => {
    const c = s.ctx, a = S0("vision"), b = S1("vision");
    const v = vis(t, a, b, 0.9, 0.7);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a - 0.5, b + 0.5, 0.025)})`;
    const rise = E.outExpo(seg(t, a - 0.35, a + 1.2));
    const zoomOut = E.inOutCubic(seg(t, b - 0.7, b + 0.35));
    st(c.lap, { y: (1 - rise) * 520 - 40 * zoomOut, p: 2400, rx: 14 * (1 - rise), s: 0.82 + 0.03 * rise + 0.5 * zoomOut, o: rise });
    const join = segT("vision", 1);
    c.tiles.forEach((m, k) => {
      const t0 = wordT("vision", 0, m.w) - 0.1;
      const e = enter(t, t0, 0.7, 22);
      const f = E.inOutCubic(seg(t, join + k * 0.06, join + 0.75 + k * 0.06));
      const dx = (960 - (m.x + 150)) * f, dy = (520 - (m.y + 45)) * f;
      st(m.el, { x: dx, y: e.y + dy, s: 1 - 0.65 * f, o: e.o * (1 - seg(t, join + 0.45 + k * 0.06, join + 0.8 + k * 0.06)) });
    });
    // les cases du tableau de bord s'allument quand les modules arrivent
    c.dashTiles.forEach((el, k) => {
      const g = Math.max(0, 1 - Math.abs(t - (join + 0.75 + k * 0.07)) / 0.45);
      el.style.boxShadow = g > 0 ? `0 0 0 ${3 * g}px rgba(31,95,174,${0.55 * g})` : "none";
    });
  }, PAPER);

  // ---------- 4. rôles : chacun son espace
  const ROLES = [
    ["user", "Salarié", "Son espace personnel", [[1, "Pointage"], [1, "Demandes de congé"], [1, "Documents personnels"], [1, "Annonces"], [0, "Dossiers des collègues"]]],
    ["briefcase", "Manager", "Son équipe", [[1, "Suivi de l'équipe"], [1, "Validation des congés"], [1, "Devis entrants"], [1, "Commentaires"], [0, "Règles globales"]]],
    ["heart", "RH", "Le personnel", [[1, "Dossiers RH"], [1, "Alertes de pointage"], [1, "Fiches de paie"], [1, "Notes internes"], [0, "Comptes et rôles"]]],
    ["building", "Direction", "Vue d'ensemble", [[1, "Indicateurs globaux"], [1, "Validation finale"], [1, "Journal des décisions"], [1, "Devis du groupe"], [1, "Communications"]]],
    ["server", "Administrateur", "Les réglages", [[1, "Comptes et rôles"], [1, "Horaires"], [1, "Accès"], [1, "Sites"], [0, "Validations métier"]]],
  ];
  const ROLE_WORDS = ["salarié", "manager", "rh", "direction", "administrateur"];
  scene("roles", (cam) => {
    const cards = ROLES.map(([i, name, desc, perms], k) => add(cam, `<div class="card abs" style="left:${154 + k * 328}px;top:300px;width:300px;padding:28px 24px;border-radius:26px">
      <div style="width:64px;height:64px;border-radius:20px;background:var(--sel-soft);color:var(--navy);display:grid;place-items:center;font-size:32px">${ic(i)}</div>
      <div class="display" style="font-weight:700;font-size:31px;margin-top:20px">${name}</div><div class="muted" style="font-size:17px;margin-top:4px">${desc}</div>
      <div class="perms" style="margin-top:22px;display:flex;flex-direction:column;gap:12px">${perms.map(([ok, l]) => `<div class="row" style="gap:10px;font-size:16px;font-weight:500;color:${ok ? "var(--ink)" : "var(--muted)"}"><span style="font-size:19px;color:${ok ? "var(--green)" : "#9aa6b5"}">${ic(ok ? "check" : "lock")}</span>${l}</div>`).join("")}</div></div>`));
    return { cards, rows: cards.map(c => Array.from(c.querySelectorAll(".perms .row"))) };
  }, (t, s) => {
    const c = s.ctx, a = S0("roles"), b = S1("roles");
    const v = vis(t, a, b, 0.7, 0.7);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a, b + 0.5, 0.03)})`;
    const perm = segT("roles", 2) - 0.1;
    c.cards.forEach((el, k) => {
      const e = enter(t, segT("roles", 0) + 0.05 + k * 0.09, 0.9, 40);
      const wt = wordT("roles", 1, ROLE_WORDS[k]);
      const hi = Math.max(0, 1 - Math.abs(t - (wt + 0.25)) / 0.55);
      st(el, { y: e.y - 14 * E.inOutSine(hi), o: e.o });
      el.style.borderColor = hi > 0.02 ? `rgba(17,45,80,${0.25 + 0.6 * hi})` : "var(--line)";
      el.style.boxShadow = `0 ${24 + 16 * hi}px ${70 + 30 * hi}px rgba(17,45,80,${0.10 + 0.08 * hi})`;
      c.rows[k].forEach((r, j) => { const p = enter(t, perm + k * 0.12 + j * 0.06, 0.6, 10); st(r, { y: p.y, o: p.o }); });
    });
  }, PAPER);

  // ---------- 5. pointage : la journée en quatre gestes
  const POINT = [["login", "Arrivée", "08:00", "Pointer la pause"], ["coffee", "Pause", "12:30", "Retour de pause"], ["back", "Retour", "13:30", "Pointer le départ"], ["logout", "Départ", "17:00", "Journée terminée"]];
  scene("pointage", (cam) => {
    const ph = add(cam, `<div class="phone" style="left:430px;top:90px"><div class="scr"><div class="fill" style="padding:62px 26px 26px;display:flex;flex-direction:column;gap:18px">
      <div style="display:flex;align-items:center;justify-content:space-between"><div style="display:flex;align-items:center;gap:10px;font-weight:700;font-size:17px"><div class="bm" style="width:34px;height:34px;border-radius:10px;font-size:19px">W</div>MyWebtel</div><span class="muted" style="font-size:14px">WTL-00041</span></div>
      <div><div class="hello" style="font-size:36px">Ma journée</div><div class="muted" style="margin-top:4px;font-size:16px">Mercredi 22 octobre</div></div>
      <span class="pill p-grey st-pill" style="align-self:flex-start;font-size:15px"><span class="dot"></span><span class="st-txt">Session de travail inactive</span></span>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px"><div class="card" style="box-shadow:none;border-radius:16px;padding:16px"><div class="muted" style="font-size:14px">Arrivée</div><div class="display m-in" style="font-size:32px;font-weight:700;margin-top:4px">—</div></div>
        <div class="card" style="box-shadow:none;border-radius:16px;padding:16px"><div class="muted" style="font-size:14px">Départ</div><div class="display m-out" style="font-size:32px;font-weight:700;margin-top:4px">—</div></div></div>
      <div class="card" style="box-shadow:none;border-radius:16px;padding:16px 18px;display:flex;flex-direction:column;gap:12px;font-size:16px">
        <div class="row" style="justify-content:space-between"><span class="muted">Mon horaire</span><span style="font-weight:600">08:00 – 17:00</span></div>
        <div class="row" style="justify-content:space-between"><span class="muted">Pause</span><span style="font-weight:600">1 heure</span></div>
        <div class="row" style="justify-content:space-between"><span class="muted">Site</span><span style="font-weight:600">Sacré-Cœur 3</span></div></div>
      <div class="btn ph-btn" style="height:64px;font-size:18px;margin-top:auto">Pointer l'arrivée</div>
      <div class="muted" style="font-size:13px;text-align:center">La déconnexion ne termine jamais votre session de travail.</div></div></div></div>`);
    const tl = add(cam, `<div class="card abs" style="left:1030px;top:180px;width:520px;padding:30px 32px;border-radius:26px"><div class="display" style="font-weight:700;font-size:28px;margin-bottom:20px">Aujourd'hui</div>
      ${POINT.map(([i, l, h]) => `<div class="row ev" style="padding:14px 0;border-top:1px solid var(--line)"><div class="evi" style="width:48px;height:48px;border-radius:14px;background:#eef2f7;color:var(--muted);display:grid;place-items:center;font-size:23px">${ic(i)}</div><div style="flex:1;font-weight:600;font-size:20px">${l}</div><div class="display evh" style="font-weight:700;font-size:24px;color:#b8c2cf">${h}</div></div>`).join("")}</div>`);
    const alert = add(cam, `<div class="card abs" style="left:1030px;top:150px;width:560px;padding:24px 26px;border-radius:24px"><div class="row" style="gap:14px"><div style="width:48px;height:48px;border-radius:14px;background:var(--red-soft);color:var(--red);display:grid;place-items:center;font-size:24px">${ic("bell")}</div><div style="flex:1"><div style="font-weight:700;font-size:20px">Alerte RH · 18:00</div><div class="muted" style="font-size:15px">Récapitulatif de fin de journée</div></div></div>
      <div style="margin-top:18px;display:flex;flex-direction:column;gap:10px"><div class="row" style="justify-content:space-between;font-size:17px"><span>Retard de plus de 30 min</span><span class="pill p-amber">1 collaborateur</span></div><div class="row" style="justify-content:space-between;font-size:17px"><span>Pointage incomplet</span><span class="pill p-red">2 collaborateurs</span></div></div></div>`);
    const hist = add(cam, `<div class="card abs" style="left:1030px;top:470px;width:560px;padding:24px 26px;border-radius:24px"><div class="row" style="gap:12px;margin-bottom:14px"><span style="font-size:22px;color:var(--navy)">${ic("history")}</span><div style="font-weight:700;font-size:20px">Historique</div></div>
      ${[["Correction demandée", "Retour 13:42 → 13:30", "13:45"], ["Justificatif ajouté", "Réunion client", "13:46"], ["Correction validée par les RH", "Version initiale conservée", "14:10"]].map(([a, b, h]) => `<div class="row hrow" style="padding:11px 0;border-top:1px solid var(--line)"><span style="width:10px;height:10px;border-radius:50%;background:var(--navy)"></span><div style="flex:1"><div style="font-weight:600;font-size:17px">${a}</div><div class="muted" style="font-size:15px">${b}</div></div><span class="muted" style="font-size:15px">${h}</span></div>`).join("")}</div>`);
    return { ph, tl, alert, hist, evs: Array.from(tl.querySelectorAll(".ev")), hrows: Array.from(hist.querySelectorAll(".hrow")),
      btn: q(ph, ".ph-btn"), pill: q(ph, ".st-pill"), pillTxt: q(ph, ".st-txt"), mIn: q(ph, ".m-in"), mOut: q(ph, ".m-out") };
  }, (t, s) => {
    const c = s.ctx, a = S0("pointage"), b = S1("pointage");
    const v = vis(t, a, b, 0.7, 0.7);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a, b + 0.5, 0.025)})`;
    const e = enter(t, a + 0.1, 1.0, 60);
    const alertT = wordT("pointage", 2, "les RH") - 0.15;
    const toLeft = E.inOutCubic(seg(t, alertT - 0.5, alertT + 0.4));
    st(c.ph, { y: e.y, x: -110 * toLeft, o: e.o });
    // les quatre gestes
    const taps = [0, 1, 2, 3].map(k => partT("pointage", 1, k) - 0.08);
    let step = -1; taps.forEach((tk, k) => { if (t >= tk) step = k; });
    const lastTap = step >= 0 ? taps[step] : -9;
    if (!c.rip) c.rip = add(s.el, `<div class="ripple"></div>`);
    const [bx, by] = centerOf(c.btn);
    ripple(c.rip, t, step >= 0 ? lastTap : 0, bx, by);
    c.btn.textContent = step < 0 ? "Pointer l'arrivée" : POINT[step][3];
    c.btn.style.background = step >= 3 ? "#7c8ba0" : "var(--navy)";
    c.btn.style.transform = `scale(${(1 - 0.04 * Math.max(0, 1 - Math.abs(t - lastTap) / 0.12)).toFixed(4)})`;
    const active = step >= 0 && step < 3;
    c.pill.className = "pill st-pill " + (step < 0 ? "p-grey" : step >= 3 ? "p-sel" : step === 1 ? "p-amber" : "p-green");
    c.pillTxt.textContent = step < 0 ? "Session de travail inactive" : step === 1 ? "En pause" : step >= 3 ? "Journée terminée" : "Session de travail active";
    c.mIn.textContent = step >= 0 ? "08:00" : "—";
    c.mOut.textContent = step >= 3 ? "17:00" : "—";
    // la frise du jour
    const tlE = enter(t, a + 0.35, 1.0, 40);
    st(c.tl, { y: tlE.y - 30 * toLeft, x: 90 * toLeft, s: 1 - 0.1 * toLeft, o: tlE.o * (1 - toLeft) });
    c.evs.forEach((ev, k) => {
      const on = t >= taps[k] + 0.08;
      const icn = q(ev, ".evi"), hh = q(ev, ".evh");
      icn.style.background = on ? "var(--navy)" : "#eef2f7"; icn.style.color = on ? "#fff" : "var(--muted)";
      hh.style.color = on ? "var(--ink)" : "#b8c2cf";
      const pop = on ? Math.max(0, 1 - (t - taps[k] - 0.08) / 0.35) : 0;
      icn.style.transform = `scale(${(1 + 0.12 * pop).toFixed(3)})`;
    });
    // alerte RH puis historique
    const al = enter(t, alertT, 0.8, -30);
    st(c.alert, { y: al.y, o: al.o });
    const ht = segT("pointage", 3) - 0.1;
    const hi = enter(t, ht, 0.8, 30);
    st(c.hist, { y: hi.y, o: hi.o });
    c.hrows.forEach((r, k) => { const p = enter(t, ht + 0.25 + k * 0.35, 0.6, 10); st(r, { y: p.y, o: p.o }); });
  }, PAPER);

  // ---------- 6. congés : dates, motif, justificatif, circuit, solde
  scene("conges", (cam) => {
    const days = []; // décembre 2026 : commence un mardi
    for (let k = 0; k < 1; k++) days.push("");
    for (let d = 1; d <= 31; d++) days.push(d);
    const win = add(cam, `<div class="card abs" style="left:300px;top:170px;width:1320px;height:720px;border-radius:30px;padding:38px 44px;display:flex;flex-direction:column;gap:26px">
      <div class="row" style="justify-content:space-between"><div class="display" style="font-weight:700;font-size:36px">Nouvelle demande de congé</div><span class="pill p-grey">Brouillon</span></div>
      <div style="display:flex;gap:44px;flex:1">
        <div style="width:560px"><div class="row" style="justify-content:space-between;margin-bottom:16px"><div style="font-weight:700;font-size:21px">Décembre 2026</div><div class="muted" style="font-size:15px">Jours ouvrables</div></div>
          <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:8px;text-align:center">${["L", "M", "M", "J", "V", "S", "D"].map(d => `<div class="muted" style="font-size:14px;font-weight:600;padding-bottom:4px">${d}</div>`).join("")}
          ${days.map(d => `<div class="day" data-d="${d}" style="height:54px;border-radius:14px;display:grid;place-items:center;font-size:18px;font-weight:500;${d === "" ? "" : "background:#f3f6fa"}">${d}</div>`).join("")}</div></div>
        <div style="flex:1;display:flex;flex-direction:column;gap:20px">
          <div><div class="muted" style="font-size:15px;font-weight:600;margin-bottom:8px">Période</div><div class="per" style="border:1px solid var(--line);border-radius:14px;padding:16px 18px;font-size:19px;font-weight:600;min-height:58px"></div></div>
          <div><div class="muted" style="font-size:15px;font-weight:600;margin-bottom:8px">Motif</div><div class="mot" style="border:1px solid var(--line);border-radius:14px;padding:16px 18px;font-size:19px;min-height:58px"></div></div>
          <div><div class="muted" style="font-size:15px;font-weight:600;margin-bottom:8px">Justificatif</div><div style="border:1.5px dashed #c5cfdb;border-radius:14px;padding:14px 18px;min-height:64px;display:flex;align-items:center"><span class="chip pill p-sel" style="font-size:16px">${ic("paperclip")} justificatif.pdf</span></div></div>
          <div class="btn send" style="height:60px;font-size:18px;margin-top:auto">Envoyer la demande</div></div></div></div>`);
    const flow = add(cam, `<div class="abs" style="left:1210px;top:200px;width:560px;display:flex;flex-direction:column;gap:0">
      ${[["user", "Vous", "Demande envoyée"], ["briefcase", "Votre manager", "Validée"], ["building", "Direction", "Validée si nécessaire"]].map(([i, a, b], k) => `<div class="node card" style="padding:22px 24px;border-radius:22px;display:flex;align-items:center;gap:18px;margin-top:${k ? 56 : 0}px;position:relative">
        <div style="width:56px;height:56px;border-radius:16px;background:var(--sel-soft);color:var(--navy);display:grid;place-items:center;font-size:28px">${ic(i)}</div><div style="flex:1"><div style="font-weight:700;font-size:22px">${a}</div><div class="muted nst" style="font-size:16px">${k ? "En attente" : b}</div></div>
        <div class="ok" style="width:40px;height:40px;border-radius:50%;background:var(--green);color:#fff;display:grid;place-items:center;font-size:22px">${ic("check")}</div>
        ${k ? `<div class="link" style="position:absolute;left:51px;top:-56px;width:4px;height:56px;background:#d6dee9;border-radius:2px"><i style="display:block;width:100%;background:var(--navy);border-radius:2px"></i></div>` : ""}</div>`).join("")}</div>`);
    const sold = add(cam, `<div class="card abs" style="left:1210px;top:700px;width:560px;padding:26px 28px;border-radius:24px;display:flex;align-items:center;gap:26px">
      <svg width="132" height="132" viewBox="0 0 132 132"><circle cx="66" cy="66" r="56" fill="none" stroke="#e7edf4" stroke-width="12"/><circle class="ring" cx="66" cy="66" r="56" fill="none" stroke="var(--navy)" stroke-width="12" stroke-linecap="round" transform="rotate(-90 66 66)" stroke-dasharray="351.9" stroke-dashoffset="0"/></svg>
      <div><div class="muted" style="font-size:16px;font-weight:600">Solde de congés</div><div class="display" style="font-weight:700;font-size:58px;line-height:1.05"><span class="num">24</span> <span style="font-size:30px">jours</span></div><div class="muted" style="font-size:15px">Période du 1er juin 2026 au 31 mai 2027</div></div></div>`);
    return { win, flow, sold, days: Array.from(win.querySelectorAll(".day")), per: q(win, ".per"), mot: q(win, ".mot"), chip: q(win, ".chip"), send: q(win, ".send"),
      nodes: Array.from(flow.querySelectorAll(".node")), ring: q(sold, ".ring"), num: q(sold, ".num") };
  }, (t, s) => {
    const c = s.ctx, a = S0("conges"), b = S1("conges");
    const v = vis(t, a, b, 0.7, 0.7);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a, b + 0.5, 0.025)})`;
    const e = enter(t, a + 0.1, 1.0, 50);
    const flowT = segT("conges", 2) - 0.25;
    const aside = E.inOutCubic(seg(t, flowT - 0.3, flowT + 0.6));
    st(c.win, { y: e.y, x: -250 * aside, s: 1 - 0.26 * aside, o: e.o });
    c.win.style.transformOrigin = "0% 50%";
    // dates 21 → 24 décembre
    const tDates = wordT("conges", 1, "dates") - 0.2;
    c.days.forEach(d => {
      const n = +d.dataset.d;
      if (n >= 21 && n <= 24) {
        const on = t >= tDates + (n - 21) * 0.12;
        d.style.background = on ? "var(--navy)" : "#f3f6fa"; d.style.color = on ? "#fff" : "var(--ink)";
      }
    });
    c.per.textContent = t >= tDates + 0.4 ? "Du 21 au 24 décembre · 4 jours" : "";
    const tMot = wordT("conges", 1, "motif") - 0.1;
    const motif = "Congés annuels";
    c.mot.textContent = motif.slice(0, Math.floor(clamp((t - tMot) / 0.6) * motif.length));
    const tJ = wordT("conges", 1, "justificatif") - 0.05;
    const cj = enter(t, tJ, 0.5, -16);
    st(c.chip, { y: cj.y, o: cj.o });
    const pressT = flowT - 0.35;
    c.send.style.transform = `scale(${(1 - 0.04 * Math.max(0, 1 - Math.abs(t - pressT) / 0.12)).toFixed(4)})`;
    // circuit de validation
    c.nodes.forEach((n, k) => {
      const ne = enter(t, flowT + 0.15 + k * 0.18, 0.7, 24);
      st(n, { y: ne.y, o: ne.o });
      const okT = flowT + 0.5 + k * 0.85;
      const ok = q(n, ".ok"), pk = spring(t - okT, 0.6, 3);
      st(ok, { s: t >= okT ? pk : 0, o: t >= okT ? 1 : 0 });
      if (k) {
        q(n, ".nst").textContent = t >= okT ? (k === 1 ? "Validée" : "Validée si nécessaire") : "En attente";
        q(n, ".link i").style.height = (100 * E.inOutCubic(seg(t, okT - 0.7, okT - 0.05))).toFixed(1) + "%";
      }
    });
    // solde
    const soldT = segT("conges", 3) - 0.1;
    const se = enter(t, soldT, 0.8, 30);
    st(c.sold, { y: se.y, o: se.o });
    const dec = E.inOutCubic(seg(t, soldT + 0.6, soldT + 1.8));
    c.num.textContent = String(Math.round(24 - 4 * dec));
    c.ring.setAttribute("stroke-dashoffset", (351.9 * (4 / 24) * dec).toFixed(2));
    st(c.flow, { y: -90 * E.inOutCubic(seg(t, soldT - 0.3, soldT + 0.5)) });
  }, PAPER);

  // ---------- 7. documents : à vous seul
  scene("documents", (cam) => {
    const list = add(cam, `<div class="card abs" style="left:250px;top:200px;width:720px;padding:32px 34px;border-radius:28px">
      <div class="row" style="justify-content:space-between;margin-bottom:20px"><div class="display" style="font-weight:700;font-size:32px">Mes documents</div><span class="pill p-green">${ic("lock")} Visible uniquement par vous</span></div>
      ${[["Fiche de paie · Octobre 2026", "PDF · publié par les RH", 1], ["Fiche de paie · Septembre 2026", "PDF", 0], ["Décompte de salaire · 2026", "PDF", 0], ["Contrat de travail", "PDF", 0], ["Attestation de travail", "PDF", 0]].map(([a, b, n], k) => `<div class="row drow" style="padding:16px 14px;border-radius:16px;margin:2px 0"><div style="width:48px;height:48px;border-radius:14px;background:var(--sel-soft);color:var(--navy);display:grid;place-items:center;font-size:24px">${ic("file")}</div><div style="flex:1"><div style="font-weight:600;font-size:19px">${a}</div><div class="muted" style="font-size:15px">${b}</div></div>${n ? `<span class="pill p-sel">Nouveau</span>` : `<span class="muted" style="font-size:22px">${ic("chevron")}</span>`}</div>`).join("")}</div>`);
    const prev = add(cam, `<div class="card abs" style="left:1030px;top:130px;width:640px;height:820px;padding:34px;border-radius:28px;display:flex;flex-direction:column;gap:16px">
      <div class="row" style="justify-content:space-between"><div style="font-weight:700;font-size:21px">${ic("eye")} Aperçu</div><div class="row" style="gap:10px"><div class="dl btn" style="height:44px;padding:0 18px;font-size:16px;display:flex;gap:8px;align-items:center">${ic("download")}<span class="dlt">Télécharger</span></div></div></div>
      <div style="height:6px;border-radius:99px;background:#e9eef5;overflow:hidden"><i class="pb" style="display:block;height:100%;width:0;background:var(--green)"></i></div>
      <div style="flex:1;border:1px solid var(--line);border-radius:16px;padding:30px 32px;display:flex;flex-direction:column;gap:14px;background:#fff">
        <div class="row" style="justify-content:space-between"><div class="row" style="gap:10px;font-weight:700;font-size:20px"><div class="bm" style="width:34px;height:34px;border-radius:10px;font-size:18px">W</div>Webtel</div><div class="muted" style="font-size:15px">Octobre 2026</div></div>
        <div class="display" style="font-weight:700;font-size:28px;margin-top:8px">Fiche de paie</div>
        ${[90, 72, 84, 60, 78, 66, 88, 54].map((w, k) => `<div class="row" style="justify-content:space-between"><i style="display:block;height:12px;width:${w * 3}px;border-radius:6px;background:#e6ecf3"></i><i style="display:block;height:12px;width:${70 + (k * 17) % 40}px;border-radius:6px;background:#dbe3ed"></i></div>`).join("")}
        <div style="margin-top:auto;border-top:2px solid var(--line);padding-top:16px" class="row"><div style="flex:1;font-weight:700;font-size:18px">Net à payer</div><i style="display:block;height:16px;width:140px;border-radius:8px;background:var(--navy);opacity:.85"></i></div></div></div>`);
    const com = add(cam, `<div class="card abs" style="left:250px;top:800px;width:690px;padding:18px 20px;border-radius:22px;display:flex;align-items:center;gap:14px">${avatar("AN", 44, 1)}<div style="flex:1"><div style="font-weight:600;font-size:16px">Aïssatou N.</div><div class="ctxt" style="font-size:17px;min-height:24px"></div></div><span style="font-size:24px;color:var(--navy)">${ic("message")}</span></div>`);
    return { list, prev, com, rows: Array.from(list.querySelectorAll(".drow")), dl: q(prev, ".dl"), dlt: q(prev, ".dlt"), pb: q(prev, ".pb"), ctxt: q(com, ".ctxt") };
  }, (t, s) => {
    const c = s.ctx, a = S0("documents"), b = S1("documents");
    const v = vis(t, a, b, 0.7, 0.7);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a, b + 0.5, 0.025)})`;
    const e = enter(t, a + 0.1, 1.0, 50);
    const [tp, td, tc] = [0, 1, 2].map(k => partT("documents", 1, k));
    const slide = E.inOutCubic(seg(t, tp - 0.45, tp + 0.4));
    st(c.list, { y: e.y, x: 260 * (1 - slide) - 30 * slide, o: e.o });
    c.rows.forEach((r, k) => { const p = enter(t, a + 0.4 + k * 0.08, 0.6, 12); st(r, { y: p.y, o: p.o }); r.style.background = k === 0 && t > tp - 0.3 ? "var(--sel-soft)" : "transparent"; });
    const pe = enter(t, tp - 0.15, 0.8, 0);
    st(c.prev, { x: 120 * (1 - E.outExpo(seg(t, tp - 0.15, tp + 0.8))), o: pe.o });
    const press = Math.max(0, 1 - Math.abs(t - (td - 0.05)) / 0.12);
    c.dl.style.transform = `scale(${(1 - 0.05 * press).toFixed(3)})`;
    const prog = E.inOutCubic(seg(t, td, td + 0.7));
    c.pb.style.width = (100 * prog).toFixed(1) + "%";
    c.dlt.textContent = prog >= 1 ? "Téléchargé" : "Télécharger";
    c.dl.style.background = prog >= 1 ? "var(--green)" : "var(--navy)";
    const ce = enter(t, tc - 0.15, 0.7, 24);
    st(c.com, { y: ce.y - 70 * 0, o: ce.o });
    const msg = "Merci, bien reçu.";
    c.ctxt.textContent = msg.slice(0, Math.floor(clamp((t - tc - 0.2) / 0.7) * msg.length));
  }, PAPER);

  // ---------- 8. annonces : chacun confirme sa lecture
  scene("annonces", (cam) => {
    const back = add(cam, `<div class="card abs" style="left:520px;top:150px;width:880px;padding:28px 32px;border-radius:26px;opacity:.9">
      <div class="row" style="gap:14px">${avatar("RH", 46, 2)}<div><div style="font-weight:700;font-size:18px">Ressources humaines</div><div class="muted" style="font-size:15px">Note interne · hier</div></div></div>
      <div style="font-weight:700;font-size:22px;margin-top:16px">Rappel : justificatifs d'absence</div></div>`);
    const post = add(cam, `<div class="card abs" style="left:460px;top:290px;width:1000px;padding:34px 38px;border-radius:30px">
      <div class="row" style="gap:16px">${avatar("D", 54, 0)}<div style="flex:1"><div style="font-weight:700;font-size:20px">Direction</div><div class="muted" style="font-size:16px">Note interne · il y a 2 h</div></div><span class="pill p-sel">${ic("megaphone")} Pour tous</span></div>
      <div class="display" style="font-weight:700;font-size:38px;margin-top:22px">Horaires de fin d'année</div>
      <div style="display:flex;flex-direction:column;gap:12px;margin-top:20px">${[94, 88, 70].map(w => `<i style="display:block;height:14px;width:${w}%;border-radius:7px;background:#e6ecf3"></i>`).join("")}</div>
      <div class="row" style="margin-top:30px;justify-content:space-between"><div class="lu btn" style="height:58px;padding:0 26px;font-size:18px;display:flex;gap:10px;align-items:center"><span class="luic" style="font-size:22px">${ic("check")}</span><span class="lut">Marquer comme lu</span></div>
        <div style="text-align:right"><div class="row" style="justify-content:flex-end;gap:0" >${[0, 1, 2, 3, 4, 5, 6].map(k => `<div class="rav" style="margin-left:-10px;border:2px solid #fff;border-radius:50%">${avatar("ABCDEFG"[k], 36, k + 2)}</div>`).join("")}</div>
        <div style="font-size:17px;font-weight:600;margin-top:8px">Lu par <span class="cnt">31</span> / 42</div></div></div>
      <div style="height:8px;border-radius:99px;background:#e9eef5;overflow:hidden;margin-top:16px"><i class="rb" style="display:block;height:100%;background:var(--green);border-radius:99px;width:74%"></i></div></div>`);
    return { back, post, lu: q(post, ".lu"), lut: q(post, ".lut"), cnt: q(post, ".cnt"), rb: q(post, ".rb"), ravs: Array.from(post.querySelectorAll(".rav")) };
  }, (t, s) => {
    const c = s.ctx, a = S0("annonces"), b = S1("annonces");
    const v = vis(t, a, b, 0.7, 0.7);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a, b + 0.5, 0.03)})`;
    const be = enter(t, a - 0.1, 0.9, 30), pe = enter(t, a + 0.25, 1.0, 50);   // pas d'écran vide après les documents
    st(c.back, { y: be.y, s: 0.94, o: be.o * 0.9 });
    st(c.post, { y: pe.y, o: pe.o });
    const tClick = wordT("annonces", 1, "clic") - 0.05;
    if (!c.cur) { c.cur = add(s.el, CURSOR); c.rip = add(s.el, `<div class="ripple"></div>`); }
    const [lx, ly] = centerOf(c.lu);
    cursorAt(c.cur, c.rip, t, tClick - 1.3, tClick - 0.15, 1560, 1010, lx - 40, ly + 4, tClick);
    const done = t >= tClick;
    c.lu.style.background = done ? "var(--green)" : "var(--navy)";
    c.lut.textContent = done ? "Lu" : "Marquer comme lu";
    c.lu.style.transform = `scale(${(1 - 0.05 * Math.max(0, 1 - Math.abs(t - tClick) / 0.12)).toFixed(3)})`;
    const grow = E.inOutCubic(seg(t, tClick + 0.15, tClick + 1.9));
    const n = done ? 32 + Math.round(10 * grow) : 31;
    c.cnt.textContent = String(n);
    c.rb.style.width = (100 * n / 42).toFixed(1) + "%";
    c.ravs.forEach((r, k) => { r.style.opacity = k < 4 + Math.round(3 * grow) + (done ? 0 : -1) ? 1 : 0.35; });
  }, PAPER);

  // ---------- 9. devis : du site du groupe à la clôture
  scene("devis", (cam) => {
    const site = add(cam, `<div class="card abs" style="left:150px;top:190px;width:740px;height:640px;border-radius:24px;overflow:hidden">
      <div style="height:54px;background:#eef2f7;display:flex;align-items:center;gap:10px;padding:0 20px">${["#e5e9ef", "#e5e9ef", "#e5e9ef"].map(cl => `<i style="width:13px;height:13px;border-radius:50%;background:#cfd7e2;display:block"></i>`).join("")}<div style="flex:1;margin-left:14px;height:32px;border-radius:10px;background:#fff;display:flex;align-items:center;gap:8px;padding:0 14px;color:var(--muted);font-size:15px">${ic("globe")} Site du groupe · Demande de devis</div></div>
      <div style="padding:34px 40px;display:flex;flex-direction:column;gap:16px"><div class="display" style="font-weight:700;font-size:32px">Demander un devis</div>
        ${[["Nom", "Mariama Ndiaye"], ["Entreprise", "Atelier Sahel"], ["Service souhaité", "Création de site web"]].map(([l, v]) => `<div><div class="muted" style="font-size:14px;font-weight:600;margin-bottom:6px">${l}</div><div style="border:1px solid var(--line);border-radius:12px;padding:12px 14px;font-size:17px">${v}</div></div>`).join("")}
        <div class="sbtn btn" style="height:56px;font-size:18px;margin-top:6px">Envoyer la demande</div></div></div>`);
    const env = add(cam, `<div class="abs" style="left:0;top:0;width:86px;height:86px;border-radius:24px;background:var(--navy);color:#fff;display:grid;place-items:center;font-size:40px;box-shadow:0 20px 40px rgba(17,45,80,.3)">${ic("mail")}</div>`);
    const inbox = add(cam, `<div class="card abs" style="left:1030px;top:170px;width:740px;padding:30px 32px;border-radius:28px">
      <div class="row" style="justify-content:space-between;margin-bottom:16px"><div class="row" style="gap:12px"><div class="bm" style="width:40px;height:40px;border-radius:12px;font-size:22px">W</div><div class="display" style="font-weight:700;font-size:30px">Devis entrants</div></div><span class="muted" style="font-size:15px">MyWebtel</span></div>
      <div class="new row" style="padding:16px;border-radius:18px;background:var(--sel-soft);gap:14px"><div style="width:48px;height:48px;border-radius:14px;background:#fff;color:var(--navy);display:grid;place-items:center;font-size:24px">${ic("inbox")}</div><div style="flex:1"><div style="font-weight:700;font-size:19px">Atelier Sahel · Création de site web</div><div class="muted" style="font-size:15px">Site du groupe · à l'instant</div></div><span class="stat pill p-sel">Nouveau</span></div>
      ${[["Studio Teranga · Maintenance", "Site du groupe · hier", "p-amber", "En cours"], ["Cabinet Diallo · Hébergement", "Site du groupe · lundi", "p-green", "Clôturé"]].map(([a, b, cl, st]) => `<div class="row" style="padding:16px;gap:14px;border-top:1px solid var(--line)"><div style="width:48px;height:48px;border-radius:14px;background:#f3f6fa;color:var(--muted);display:grid;place-items:center;font-size:24px">${ic("inbox")}</div><div style="flex:1"><div style="font-weight:600;font-size:18px">${a}</div><div class="muted" style="font-size:15px">${b}</div></div><span class="pill ${cl}">${st}</span></div>`).join("")}
      <div class="detail" style="margin-top:14px;border-top:1px solid var(--line);padding-top:18px;display:grid;grid-template-columns:1fr 1fr;gap:12px 24px">
        ${[["Site émetteur", "Site du groupe"], ["Reçue le", "22 octobre · 09:41"], ["Service", "Création de site web"], ["Responsable", "Manager commercial"]].map(([l, v]) => `<div class="dt"><div class="muted" style="font-size:14px;font-weight:600">${l}</div><div style="font-weight:600;font-size:17px;margin-top:2px">${v}</div></div>`).join("")}
        <div class="dt" style="grid-column:1 / span 2" ><div class="muted" style="font-size:14px;font-weight:600">Historique</div><div class="hist" style="font-size:16px;margin-top:4px"></div></div></div></div>`);
    return { site, env, inbox, sbtn: q(site, ".sbtn"), nw: q(inbox, ".new"), stat: q(inbox, ".stat"), dts: Array.from(inbox.querySelectorAll(".dt")), hist: q(inbox, ".hist") };
  }, (t, s) => {
    const c = s.ctx, a = S0("devis"), b = S1("devis");
    const v = vis(t, a, b, 0.7, 0.7);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a, b + 0.5, 0.025)})`;
    const se = enter(t, a + 0.05, 1.0, 50), ie = enter(t, a + 0.35, 1.0, 50);
    const sendT = wordT("devis", 0, "arrive") - 0.6;
    const away = E.inOutCubic(seg(t, segT("devis", 1) - 0.8, segT("devis", 1)));
    st(c.site, { y: se.y, x: -60 * away, s: 1 - 0.05 * away, o: se.o * (1 - 0.65 * away) });
    st(c.inbox, { y: ie.y, x: -320 * away, s: 1 + 0.06 * away, o: ie.o });
    c.sbtn.style.transform = `scale(${(1 - 0.04 * Math.max(0, 1 - Math.abs(t - sendT) / 0.12)).toFixed(3)})`;
    // l'enveloppe vole du formulaire à la boîte MyWebtel
    const f = seg(t, sendT + 0.05, sendT + 1.05), fe = E.inOutCubic(f);
    const x = lerp(470, 1240, fe), y = lerp(720, 330, fe) - Math.sin(Math.PI * fe) * 170;
    st(c.env, { x: x - 43, y: y - 43, s: 0.6 + 0.4 * Math.sin(Math.PI * Math.min(f * 1.2, 1)), r: -8 + 16 * fe, o: f > 0 && f < 1 ? 1 : 0 });
    const arrive = sendT + 1.0;
    const ne = E.outExpo(seg(t, arrive, arrive + 0.6));
    st(c.nw, { y: (1 - ne) * -16, o: t >= arrive ? ne : 0 });
    // statuts au rythme de la voix
    const [t1, t2, t3] = [1, 2, 3].map(k => segT("devis", k));
    const states = [["p-sel", "Nouveau"], ["p-navy", "Pris en charge"], ["p-amber", "En cours"], ["p-green", "Clôturé"]];
    const sIdx = t >= t3 ? 3 : t >= t2 ? 2 : t >= t1 ? 1 : 0;
    c.stat.className = "stat pill " + states[sIdx][0];
    c.stat.textContent = states[sIdx][1];
    const lastS = [0, t1, t2, t3][sIdx];
    c.stat.style.transform = `scale(${(1 + 0.1 * Math.max(0, 1 - (t - lastS) / 0.3) * (sIdx > 0)).toFixed(3)})`;
    // détail du dossier : rien ne se perd
    c.dts.forEach((d, k) => { const p = enter(t, t1 + 0.1 + k * 0.12, 0.6, 10); st(d, { y: p.y, o: p.o }); });
    const h = ["Pris en charge · 09:52", "Appel au client · 10:20", "Devis envoyé · 11:05", "Clôturé · 16:30"];
    c.hist.textContent = h.slice(0, sIdx >= 1 ? sIdx + (sIdx === 3 ? 1 : 0) : 0).join("   ·   ");
  }, PAPER);

  // ---------- 10. réglages : quelques clics, et la session qui se ferme
  scene("reglages", (cam) => {
    const panel = add(cam, `<div class="card abs" style="left:260px;top:150px;width:1400px;height:780px;border-radius:30px;display:flex;overflow:hidden;border:none">
      <div style="width:300px;background:#f6f8fb;border-right:1px solid var(--line);padding:32px 22px;display:flex;flex-direction:column;gap:6px">
        <div class="row" style="gap:12px;font-weight:700;font-size:20px;margin:0 8px 22px"><div class="bm" style="width:38px;height:38px;border-radius:11px;font-size:21px">W</div>Réglages</div>
        ${[["users", "Comptes"], ["key", "Rôles"], ["clock", "Horaires"], ["lock", "Accès"], ["globe", "Sites"], ["bell", "Notifications"]].map(([i, l], k) => `<div class="nav snav" style="font-size:17px">${ic(i)}${l}</div>`).join("")}</div>
      <div style="flex:1;padding:36px 40px;display:grid;grid-template-columns:1fr 1fr;gap:22px">
        <div class="blk card" style="box-shadow:none;padding:24px;border-radius:22px"><div style="font-weight:700;font-size:20px;margin-bottom:14px">Comptes</div>
          ${[["Aïssatou N.", "Active"], ["Ibrahima S.", "Active"], ["Nouveau collaborateur", "En attente"]].map(([n, s2], k) => `<div class="row" style="padding:9px 0">${avatar(n[0], 38, k + 1)}<div style="flex:1;font-size:17px;font-weight:600">${n}</div><div class="sw ${k === 2 ? "sw-new" : "sw-on"}"><i></i></div></div>`).join("")}</div>
        <div class="blk card" style="box-shadow:none;padding:24px;border-radius:22px"><div style="font-weight:700;font-size:20px;margin-bottom:14px">Rôles</div>
          ${[["Aïssatou N.", "Salarié"], ["Ibrahima S.", "Manager"], ["Fatou D.", "RH"]].map(([n, r], k) => `<div class="row" style="padding:9px 0"><div style="flex:1;font-size:17px;font-weight:600">${n}</div><span class="pill p-sel ${k === 0 ? "role0" : ""}">${r}</span></div>`).join("")}</div>
        <div class="blk card" style="box-shadow:none;padding:24px;border-radius:22px"><div style="font-weight:700;font-size:20px;margin-bottom:14px">Horaires</div>
          <div class="row" style="padding:9px 0;justify-content:space-between;font-size:17px"><span>Équipe Ouakam</span><span class="pill p-grey hor" style="font-size:16px">07:30 – 16:30</span></div>
          <div class="row" style="padding:9px 0;justify-content:space-between;font-size:17px"><span>Équipe Sacré-Cœur 3</span><span class="pill p-grey" style="font-size:16px">08:00 – 17:00</span></div>
          <div class="row" style="padding:9px 0;justify-content:space-between;font-size:17px"><span>Pause</span><span class="pill p-grey" style="font-size:16px">1 heure</span></div></div>
        <div class="blk card" style="box-shadow:none;padding:24px;border-radius:22px"><div style="font-weight:700;font-size:20px;margin-bottom:14px">Accès</div>
          ${[["Documents RH", 1], ["Devis entrants", 1], ["Réglages globaux", 0]].map(([l, on], k) => `<div class="row" style="padding:9px 0"><div style="flex:1;font-size:17px;font-weight:600">${l}</div><div class="sw ${on ? "sw-on" : ""} ${k === 1 ? "acc1" : ""}"><i></i></div></div>`).join("")}</div></div></div>`);
    const sess = add(cam, `<div class="center" style="display:flex;flex-direction:column;align-items:center;gap:26px">
      <div style="position:relative;width:300px;height:300px"><svg width="300" height="300" viewBox="0 0 300 300" style="position:absolute;inset:0"><circle cx="150" cy="150" r="130" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="14"/><circle class="sring" cx="150" cy="150" r="130" fill="none" stroke="#fff" stroke-width="14" stroke-linecap="round" transform="rotate(-90 150 150)" stroke-dasharray="816.8" stroke-dashoffset="0"/></svg>
        <div class="stime display" style="position:absolute;inset:0;display:grid;place-items:center;color:#fff;font-weight:700;font-size:64px">15:00</div>
        <div class="slock" style="position:absolute;inset:0;display:grid;place-items:center;color:#fff;font-size:120px">${ic("lock")}</div></div>
      <div class="scap" style="color:rgba(255,255,255,.8);font-size:26px;font-weight:600;letter-spacing:.01em">Session fermée</div></div>`);
    return { panel, sess, blks: Array.from(panel.querySelectorAll(".blk")), snav: Array.from(panel.querySelectorAll(".snav")),
      swNew: q(panel, ".sw-new"), role0: q(panel, ".role0"), hor: q(panel, ".hor"), acc1: q(panel, ".acc1"), sws: Array.from(panel.querySelectorAll(".sw")),
      sring: q(sess, ".sring"), stime: q(sess, ".stime"), slock: q(sess, ".slock"), scap: q(sess, ".scap") };
  }, (t, s) => {
    const c = s.ctx, a = S0("reglages"), b = S1("reglages");
    const v = vis(t, a, b, 0.7, 0.7);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a, b + 0.5, 0.025)})`;
    const e = enter(t, a + 0.05, 1.0, 50);
    const sessT = segT("reglages", 2) - 0.2;
    const fade = E.inOutCubic(seg(t, sessT, sessT + 0.8));
    st(c.panel, { y: e.y, s: 1 - 0.08 * fade, o: e.o * (1 - 0.92 * fade), blur: 10 * fade });
    // sections mises en valeur au rythme de l'énumération
    const words = ["comptes", "rôles", "horaires", "accès"];
    c.blks.forEach((bl, k) => {
      const wt = wordT("reglages", 0, words[k]);
      const hi = Math.max(0, 1 - Math.abs(t - (wt + 0.2)) / 0.5);
      bl.style.boxShadow = hi > 0.01 ? `0 0 0 ${3 * hi}px rgba(31,95,174,${0.6 * hi})` : "none";
      bl.style.transform = `translateY(${(-6 * E.inOutSine(hi)).toFixed(2)}px)`;
      c.snav[k].className = "nav snav" + (hi > 0.3 ? " on" : "");
    });
    // quelques clics
    const k0 = segT("reglages", 1) + 0.45;
    if (!c.cur) { c.cur = add(s.el, CURSOR); c.rip = add(s.el, `<div class="ripple"></div>`); }
    const clicks = [[k0, ...centerOf(c.swNew)], [k0 + 0.85, ...centerOf(c.role0)], [k0 + 1.7, ...centerOf(c.hor)]];
    const ci = clicks.reduce((acc, ck, k) => t >= ck[0] - 0.75 ? k : acc, 0);
    const prevC = clicks[Math.max(ci - 1, 0)], cc = clicks[ci];
    cursorAt(c.cur, c.rip, t, cc[0] - 0.75, cc[0] - 0.1, ci ? prevC[1] : 1300, ci ? prevC[2] : 1000, cc[1], cc[2], cc[0]);
    c.cur.style.opacity = (seg(t, k0 - 1.0, k0 - 0.7) * (1 - fade)).toFixed(3);
    const on1 = t >= clicks[0][0];
    c.swNew.style.background = on1 ? "var(--green)" : "#cfd7e2"; q(c.swNew, "i").style.left = on1 ? "25px" : "3px";
    c.sws.forEach(sw => { if (sw.classList.contains("sw-on")) { sw.style.background = "var(--green)"; q(sw, "i").style.left = "25px"; } });
    c.role0.textContent = t >= clicks[1][0] ? "Manager" : "Salarié";
    c.role0.className = "pill role0 " + (t >= clicks[1][0] ? "p-navy" : "p-sel");
    c.hor.textContent = t >= clicks[2][0] ? "08:00 – 17:00" : "07:30 – 16:30";
    // session : 15 minutes en accéléré, puis le cadenas se ferme
    const se2 = enter(t, sessT + 0.3, 0.8, 20);
    st(c.sess, { c: true, y: se2.y, o: se2.o });
    const cd = seg(t, sessT + 0.6, sessT + 2.6);
    const secs = Math.round(900 * (1 - E.inOutSine(cd)));
    c.stime.textContent = `${String(Math.floor(secs / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`;
    c.sring.setAttribute("stroke-dashoffset", (816.8 * E.inOutSine(cd)).toFixed(1));
    const lk = seg(t, sessT + 2.65, sessT + 3.1);
    st(c.stime, { o: 1 - lk });
    st(c.slock, { s: lerp(0.6, 1, spring(t - sessT - 2.65, 0.65, 2.6)), o: lk });
    st(c.scap, { o: seg(t, sessT + 2.9, sessT + 3.4) });
  }, NIGHT);

  // ---------- 11. partout : ordinateur, tablette, smartphone
  scene("partout", (cam) => {
    const lap = add(cam, `<div class="laptop" style="left:290px;top:120px;transform-origin:670px 450px"><div class="lid"><div class="scr">${dashboardHTML()}</div></div><div class="base"></div></div>`);
    const tab = add(cam, `<div class="tablet" style="left:110px;top:240px;transform-origin:350px 470px"><div class="scr">${tabletDashHTML()}</div></div>`);
    const ph = add(cam, `<div class="phone" style="left:1440px;top:250px;transform-origin:215px 450px"><div class="scr">${phoneDashHTML()}</div></div>`);
    return { lap, tab, ph };
  }, (t, s) => {
    const c = s.ctx, a = S0("partout"), b = S1("partout");
    const v = vis(t, a, b, 0.7, 0.9);
    show(s.el, v > 0.001);
    if (v <= 0.001) return;
    s.el.style.opacity = v;
    s.cam.style.transform = `scale(${drift(t, a, b + 0.8, 0.05)})`;
    const out = E.inCubic(seg(t, b - 0.6, b + 0.4));
    const [to, tt, ts] = ["ordinateur", "tablette", "smartphone"].map(w => wordT("partout", 0, w) - 0.15);
    const lo = enter(t, Math.min(to, a + 0.15), 1.0, 80), lt = enter(t, tt, 1.0, 80), lp = enter(t, ts, 1.0, 80);
    st(c.lap, { y: lo.y + 30 * out, s: 0.66 * (1 - 0.1 * out), o: lo.o * (1 - out) });
    st(c.tab, { y: lt.y + 30 * out, x: 30 * out, s: 0.62 * (1 - 0.1 * out), o: lt.o * (1 - out) });
    st(c.ph, { y: lp.y + 30 * out, x: -30 * out, s: 0.68 * (1 - 0.1 * out), o: lp.o * (1 - out) });
  }, PAPER);

  // ---------- 12. signature
  scene("signature", (cam) => {
    const lock = add(cam, `<div class="center" style="display:flex;align-items:center;gap:36px"><div class="bm">W</div><div class="wmw" style="overflow:hidden"><div class="wordmark">My<b>Webtel</b></div></div></div>`);
    const url = add(cam, `<div class="center" style="margin-top:122px;font-size:28px;font-weight:500;color:var(--muted);letter-spacing:.02em">mywebtel.com</div>`);
    return { lock, bm: q(lock, ".bm"), wmw: q(lock, ".wmw"), wm: q(lock, ".wordmark"), url };
  }, (t, s) => {
    const c = s.ctx, a = S0("signature"), b = S1("signature"), logo = segT("signature", 0);
    const alive = t > a - 0.3;
    show(s.el, alive);
    if (!alive) return;
    if (!c.ww) c.ww = c.wm.getBoundingClientRect().width;
    s.el.style.opacity = E.inOutSine(seg(t, a - 0.3, a + 0.35)).toFixed(3);   // fondu enchaîné, pas de coupe sèche
    const pre = E.outExpo(seg(t, a + 0.1, logo - 0.1));
    const pop = spring(t - logo, 0.62, 2.4);
    const bmS = t < logo ? lerp(0.5, 0.8, pre) : lerp(0.8, 1, pop);
    c.bm.style.transform = `scale(${bmS.toFixed(4)})`;
    const wr = E.outExpo(seg(t, logo + 0.2, logo + 1.1));
    c.wmw.style.width = (c.ww * wr).toFixed(1) + "px";
    const end = seg(t, b - 0.9, b - 0.05);
    st(c.lock, { c: true, x: (36 + c.ww * wr) / 2 * (1 - wr), o: pre * (1 - end), s: 1 + 0.02 * seg(t, logo, b) });
    const ue = enter(t, segT("signature", 1) + 0.2, 0.9, 12);
    st(c.url, { c: true, y: ue.y, o: ue.o * (1 - end) });
  }, PAPER);

  // ------------------------------------------------------------------ rendu
  window.renderAt = function (t) {
    for (const s of scenes) s.anim(t, s);
    window.__t = t;
  };
  window.FILM = { scenes: scenes.map(s => s.id), duration: TL.duration };
  document.fonts.ready.then(() => { window.renderAt(0); window.READY = true; });
})();
