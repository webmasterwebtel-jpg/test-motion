/* MyWebtel — film V6, la vraie interface.
 * Chaque écran vient de l'aperçu PHP réel (build/mywebtel/ui.json, préparé par prep_ui.py, injecté par render.js dans
 * window.UI). Un écran peut exister en plusieurs exemplaires : la tuile posée dans le monde, et des « découpes » qui
 * sortent un composant de la page (carte de pointage, fenêtre de signature…) pour le montrer en gros plan, en relief.
 * Tous les exemplaires reçoivent les mêmes états à chaque image (fonctions pures du temps) : ils restent identiques.
 */
"use strict";
const T = {};                                               // instants du film (remplis par story.js)
const PAGE_URL = { dashboard: "/dashboard", attendance: "/attendance", leaves: "/leaves", absences: "/absences", sign: "/documents",
                   requests: "/hr-requests", content: "/content", mail: "/discussions", support: "/tickets", agent: "/dashboard" };
const PAGE_H = { absences: 1060 };                          // hauteur de fenêtre utile (le bouton d'envoi des absences est plus bas)
const INST = {};                                            // id -> { docs: [doc…], tile: Obj, clips: {nom: Obj} }
const LOADS = [];

function frameFor(id, w = 1440, hgt = PAGE_H[id] || 900) {
  const f = document.createElement("iframe");
  f.setAttribute("scrolling", "no");
  f.style.width = w + "px"; f.style.height = hgt + "px";
  LOADS.push(new Promise(res => f.addEventListener("load", res, { once: true })));
  f.srcdoc = UI[id] || `<body style="font:40px sans-serif;padding:80px">écran « ${id} » absent : lancer prep_ui.py</body>`;
  (INST[id] = INST[id] || { frames: [], clips: {}, rects: {} }).frames.push(f);
  return f;
}
function makeTile(world, id) {
  const hgt = PAGE_H[id] || 900;
  const el = add(world, `<div class="tile" style="height:${hgt}px"><div class="dim"></div></div>`);
  el.insertBefore(frameFor(id, 1440, hgt), el.firstChild);
  const o = new Obj(el, 1440, hgt);
  o.dim = q(el, ".dim");
  INST[id].tile = o;
  return o;
}
// découpe : un rectangle de la page (coordonnées de la page), montré seul ; le rectangle est mesuré après chargement
function makeClip(world, id, name, measure, pad = 0) {
  const el = add(world, `<div class="clip"></div>`);
  const f = frameFor(id);
  el.appendChild(f);
  const o = new Obj(el, 10, 10);
  o.measure = measure; o.pad = pad; o.frame = f; o.page = id;
  INST[id].clips[name] = o;
  return o;
}
function layoutClips() {                                    // après chargement : taille et décalage de chaque découpe
  for (const id of Object.keys(INST)) for (const [name, o] of Object.entries(INST[id].clips)) {
    const r = o.measure(docOf(id));
    const p = o.pad;
    o.rect = { x: r.x - p, y: r.y - p, w: r.w + 2 * p, h: r.h + 2 * p };
    o.w = o.rect.w; o.h = o.rect.h;
    o.el.style.width = o.w + "px"; o.el.style.height = o.h + "px";
    o.frame.style.left = -o.rect.x + "px"; o.frame.style.top = -o.rect.y + "px";
    INST[id].rects[name] = o.rect;
  }
}
const docOf = id => INST[id].frames[0].contentDocument;
const docsOf = id => INST[id].frames.map(f => f.contentDocument);
const rectEl = el => { const r = el.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; };
const byFilm = name => d => rectEl(d.querySelector(`[data-film="${name}"]`));
const bySel = sel => d => rectEl(d.querySelector(sel));

// point d'un élément de la page, à l'écran, dans un exemplaire donné (tuile ou découpe)
function elemPoint(id, el, where = "tile", fx = 0.5, fy = 0.5) {
  if (!el) return null;
  const r = el.getBoundingClientRect();
  let u = r.left + r.width * fx, v = r.top + r.height * fy;
  const o = where === "tile" ? INST[id].tile : INST[id].clips[where];
  if (where !== "tile") { u -= o.rect.x; v -= o.rect.y; }
  return o.screen(u, v);
}
function pagePoint(id, x, y, where = "tile") {             // point (px de la page) -> monde
  const o = where === "tile" ? INST[id].tile : INST[id].clips[where];
  return where === "tile" ? o.world(x, y) : o.world(x - o.rect.x, y - o.rect.y);
}

// ------------------------------------------------------------------ états de l'interface (repris de la V5, libellés réels)
function glowEl(el, a, color = "5,218,240") {
  if (!el) return;
  const s = a > 0.01 ? `0 0 0 ${(2 + 2 * a).toFixed(1)}px rgba(${color},${(0.9 * a).toFixed(3)}), 0 0 ${(30 * a).toFixed(0)}px rgba(0,143,241,${(0.5 * a).toFixed(3)})` : "";
  if (el.__g !== s) { el.style.boxShadow = s; el.__g = s; }
}
function press(el, t, tc) { if (el) { const s = `scale(${(1 - 0.05 * Math.max(0, 1 - Math.abs(t - tc) / 0.12)).toFixed(4)})`; if (el.__p !== s) { el.style.transform = s; el.__p = s; } } }
const hhmm = m => { m = Math.round(m); return String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0"); };
const typed = (txt, t, t0, t1) => txt.slice(0, Math.round(txt.length * seg(t, t0, t1)));

function drawSignature(cv, p) {                             // signature manuscrite révélée au rythme de la plume, puis le paraphe
  if (!cv) return;
  const k = Math.round(p * 400);
  if (cv.__k === k) return;
  cv.__k = k;
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
  if (pf > 0) {
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
// position de la plume (0..1 de la largeur/hauteur du canvas) pour la lueur qui suit le tracé
function penPoint(p) {
  if (p <= 0 || p >= 1) return null;
  if (p < 0.8) { const u = p / 0.8; return [0.5 + (u - 0.5) * 0.62, 0.56 + 0.08 * Math.sin(u * 40)]; }
  const u = (p - 0.8) / 0.2; return [0.2 + 0.62 * u, 0.86 - 0.06 * Math.sin(Math.PI * u)];
}

const STATE = {
  dashboard(d, t) {
    const clk = d.F("clock");
    if (clk) { const s = 7 * 3600 + 26 * 60 + 12 + Math.max(0, Math.floor(t - 12)); setHTML(clk, `${hhmm(s / 60 - (s % 60) / 60)}<small>:${String(s % 60).padStart(2, "0")}</small>`); }
  },
  attendance(d, t) {
    const stage = t < T.in ? 0 : t < T.pause ? 1 : t < T.ret ? 2 : t < T.out ? 3 : 4;
    const badge = d.F("day-badge");
    if (badge) { setText(badge, ["Journée à commencer", "Au travail", "En pause", "Au travail", "Journée terminée"][stage]); badge.className = "mw-badge " + ["amber", "green", "amber", "green", ""][stage]; }
    const steps = d.F("steps");
    if (steps) Array.from(steps.children).forEach((x, i) => { const done = [0, 1, 1, 2, 3][stage], curr = [0, 1, 1, 2, -1][stage]; x.className = i < done ? "complete" : i === curr ? "current" : ""; });
    setText(d.F("punch-label"), ["Commencer ma journée", "Je pars en pause", "Je reviens de pause", "Terminer ma journée", "Journée terminée"][stage]);
    const punch = d.F("punch");
    if (punch) { punch.style.opacity = stage === 4 ? "0.55" : "1"; press(punch, t, [T.in, T.pause, T.ret, T.out].reduce((a, b) => (Math.abs(t - b) < Math.abs(t - a) ? b : a))); }
    ["07:28", "12:30", "13:30", "16:34"].forEach((v, i) => {
      const b = d.F("today-" + i);
      setText(b, stage > i ? v : "—");
      if (b) glowEl(b.parentElement, Math.max(pulse(t, [T.in, T.pause, T.ret, T.out][i] + 0.05, 0.9), pulse(t, T.saved + 0.1 + 0.22 * i, 1.0)));
    });
  },
  leaves(d, t) {
    const met = d.F("metrics");
    if (met) {
      glowEl(met.firstElementChild, pulse(t, T.solde - 0.1, 1.8));
      const big = met.firstElementChild.querySelector("b");                   // <b>24 <small>jours</small></b> : on ne touche qu'au nombre
      const tn = big && big.firstChild && big.firstChild.nodeType === 3 ? big.firstChild : null;
      if (tn) { const v = Math.round(24 * E.outCubic(seg(t, T.solde - 0.25, T.solde + 0.75))) + " "; if (tn.nodeValue !== v) tn.nodeValue = v; }
    }
    glowEl(d.F("seniority"), pulse(t, T.rights - 0.2, 2.6));
  },
  absences(d, t) {
    const [d0, d1] = d.all('input[type="date"]');
    setValue(d0, t >= T.declare + 0.1 ? "2026-11-16" : ""); setValue(d1, t >= T.declare + 0.35 ? "2026-11-17" : "");
    setText(d.$('[data-duration="calendar"]'), t >= T.declare + 0.35 ? "2 jours" : "0 jour");
    const up = d.F("abs-upload"), got = t >= T.fileIn;
    if (up) {
      setText(up.querySelector("b"), got ? "certificat-medical.pdf" : "Glissez et déposez votre fichier ici");
      setText(up.querySelector("small"), got ? "PDF · 312 Ko · prêt à l’envoi" : "ou cliquez pour parcourir vos fichiers · PDF, JPG ou PNG · 5 Mo maximum");
      glowEl(up, Math.max(pulse(t, T.fileIn - 0.25, 0.9), 0.8 * bump(t, T.proof - 0.3, T.proof, T.fileIn, T.fileIn + 0.2)));
    }
    press(d.F("abs-send"), t, T.absSend);
    glowEl(d.F("abs-send"), pulse(t, T.absSend - 0.5, 0.7));
    const n = d.F("abs-new");
    if (n) { n.hidden = t < T.absSend + 0.2; glowEl(n, Math.max(pulse(t, T.absSend + 0.25, 1.2), pulse(t, T.rh, 1.6))); }
    setText(d.F("abs-badge"), t >= T.rh ? "Vérification RH" : "Déclarée");
    const pr = d.F("abs-process");
    if (pr) Array.from(pr.children).forEach((s, i) => { s.className = (t >= T.rh ? i === 1 : i === 0) ? "current" : ""; });
  },
  sign(d, t) {
    const row = d.$(".mw-document-row");
    if (row) glowEl(row, Math.max(pulse(t, T.recv, 1.6), 0));
    press(d.F("sign-open"), t, T.open);
    glowEl(d.F("sign-open"), pulse(t, T.open - 0.45, 0.8));
    const dlg = d.F("sign-dialog"), openD = t >= T.open + 0.08 && t < T.signed + 0.32;
    if (dlg) {
      if (openD && !dlg.open) dlg.showModal(); if (!openD && dlg.open) dlg.close();
      const p = E.outCubic(seg(t, T.open + 0.08, T.open + 0.4)) * (1 - E.inCubic(seg(t, T.signed + 0.05, T.signed + 0.32)));
      dlg.style.opacity = p.toFixed(3); dlg.style.transform = `translateY(${(20 * (1 - p)).toFixed(1)}px) scale(${(0.97 + 0.03 * p).toFixed(4)})`;
      const ae = dlg.ownerDocument.activeElement;
      if (ae && ae.closest && ae.closest(".mw-sign-close")) ae.blur();
    }
    const drawMode = t >= T.draw;
    const tabs = d.F("sign-tabs");
    if (tabs) tabs.querySelectorAll("button").forEach(b => b.classList.toggle("selected", (b.dataset.signMode === "draw") === drawMode));
    const nm = d.F("sign-name-mode"), dm = d.F("sign-draw-mode");
    if (nm) nm.hidden = drawMode; if (dm) dm.hidden = !drawMode;
    const r1 = d.F("sign-style-1");
    if (r1 && r1.parentElement) glowEl(r1.parentElement, pulse(t, T.nom - 0.2, 1.0));
    glowEl(d.F("sign-preview"), pulse(t, T.nom - 0.1, 1.1));
    drawSignature(d.F("sign-canvas"), E.inOutSine(seg(t, T.draw + 0.15, T.drawEnd)));
    const cb = d.F("sign-code-btn");
    if (cb) { setText(cb, t >= T.code + 0.05 ? "Renvoyer le code" : "Recevoir mon code par e-mail"); press(cb, t, T.code); }
    setValue(d.F("sign-code"), t >= T.tape - 0.1 ? "482913".slice(0, Math.round(6 * seg(t, T.tape - 0.1, T.tape + 0.45))) : "", t > T.tape - 0.15 && t < T.tape + 0.5);
    glowEl(d.F("sign-code"), pulse(t, T.tape + 0.35, 0.8));
    const cs = d.F("sign-consent");
    if (cs) cs.checked = t >= T.consent;
    press(d.F("sign-confirm"), t, T.signed);
    const done = t >= T.signed + 0.3;
    const sb = d.F("sign-badge");
    if (sb) { setText(sb, done ? "Signé" : "À signer"); sb.className = "mw-badge " + (done ? "green" : "amber"); glowEl(sb, Math.max(pulse(t, T.signed + 0.3, 1.0), pulse(t, T.recv + 0.2, 1.2))); }
    const od = d.F("sign-on-doc");
    if (od) { setText(od, "A. Ndiaye"); od.style.fontSize = "19px"; od.style.opacity = E.outCubic(seg(t, T.signed + 0.5, T.signed + 1.1)).toFixed(3); }
    const ob = d.$(".mw-sign-open");
    if (ob) ob.style.opacity = done ? "0.5" : "1";
    glowEl(d.$(".mw-preview-stage"), pulse(t, T.signed + 0.6, 1.6));
  },
  requests(d, t) {
    const cats = d.F("req-cats");
    if (cats) { const bs = cats.querySelectorAll("button"); glowEl(bs[0], Math.max(pulse(t, T.att - 0.05, 0.9), pulse(t, T.fill - 0.2, 0.8))); glowEl(bs[1], pulse(t, T.question - 0.05, 0.9)); }
    setValue(d.F("req-subject"), typed("Attestation de salaire", t, T.fill, T.fill + 0.35), t > T.fill - 0.05 && t < T.fill + 0.4);
    setValue(d.F("req-desc"), typed("Pour un dossier de location. Merci !", t, T.fill + 0.38, T.clics - 0.12), t > T.fill + 0.35 && t < T.clics);
    press(d.F("req-send"), t, T.clics);
    const rn = d.F("req-new");
    if (rn) { rn.hidden = t < T.clics + 0.2; glowEl(rn, Math.max(pulse(t, T.clics + 0.25, 1.0), pulse(t, T.process, 1.2), pulse(t, T.agentSent, 1.6))); }
    const rb = d.F("req-badge");
    if (rb) { const ok = t >= T.process; setText(rb, ok ? "En cours" : "Envoyée"); rb.className = "mw-badge" + (ok ? "" : " amber"); }
  },
  content(d, t) {
    const ctab = d.all(".mw-content-toolbar .mw-tab");
    if (ctab.length > 3) [T.dir, T.rhC].forEach((tt, i) => glowEl(ctab[i + 1], pulse(t, tt - 0.05, 0.8)));
    glowEl(d.$(".mw-note-body"), pulse(t, T.read - 0.1, 1.2));
    const chk = d.F("note-check");
    if (chk) chk.checked = t >= T.confirm;
    press(d.F("note-btn"), t, T.lu);
    const lu = t >= T.lu + 0.1;
    const nr = d.F("note-read");
    if (nr) { setText(nr, lu ? "✓ Lu" : "● Non lu"); nr.className = "mw-badge " + (lu ? "green" : "blue"); }
    setText(d.F("note-list-read"), lu ? "✓ Lu" : "● Non lu");
    glowEl(d.F("note-confirm"), pulse(t, T.lu + 0.1, 1.2));
  },
  mail(d, t) {
    const sent = t >= T.mailSend + 0.1;
    setValue(d.F("mail-input"), sent ? "" : typed("C’est confirmé : jeudi à 10 h, en salle de réunion à Ouakam.", t, T.mailType, T.mailSend - 0.15), t > T.mailType - 0.05 && !sent);
    const rep = d.F("mail-reply");
    if (rep) { rep.hidden = !sent; rep.style.transform = `translateY(${(14 * (1 - E.outCubic(seg(t, T.mailSend + 0.1, T.mailSend + 0.5)))).toFixed(1)}px)`; }
    press(d.F("mail-send"), t, T.mailSend);
  },
  support(d, t) {
    setValue(d.F("tick-subject"), typed("Messagerie inaccessible", t, T.tickType, T.tickType + 0.4), t > T.tickType - 0.05 && t < T.tickType + 0.45);
    setValue(d.F("tick-desc"), typed("Je n’arrive plus à ouvrir ma messagerie depuis ce matin.", t, T.tickType + 0.45, T.ticket - 0.2), t > T.tickType + 0.4 && t < T.ticket);
    press(d.F("tick-send"), t, T.ticket - 0.1);
    const tn = d.F("tick-new");
    if (tn) { tn.hidden = t < T.ticket + 0.1; glowEl(tn, Math.max(pulse(t, T.ticket + 0.15, 1.0), pulse(t, T.charge, 1.4), pulse(t, T.beamSupport, 1.4))); }
    const tb = d.F("tick-badge");
    if (tb) { const ok = t >= T.charge; setText(tb, ok ? "Pris en charge" : "Envoyé"); tb.className = "mw-badge" + (ok ? "" : " amber"); }
  },
  agent(d, t) {
    const ap = d.F("agent-panel"), al = d.F("agent-launcher");
    if (!ap) return;
    ap.style.opacity = "1"; ap.style.visibility = "visible"; ap.style.transform = "none";
    if (al) al.style.opacity = "0";
    const qTxt = "Il me reste combien de congés ? Je voudrais poser du 22 au 24 décembre.";
    const asked = t >= T.askSend + 0.1;
    setValue(d.F("agent-input"), asked ? "" : typed(qTxt, t, T.ask, T.askSend - 0.15), t > T.ask - 0.05 && !asked);
    const qa2 = d.F("agent-q"), qt = d.F("agent-q-text");
    if (qa2) qa2.hidden = !asked; setText(qt, qTxt);
    press(d.F("agent-send"), t, T.askSend);
    const chips = d.F("agent-chips");
    if (chips) Array.from(chips.children).forEach((c, i) => glowEl(c, pulse(t, T.chips[i] - 0.05, 0.9)));
    const aa = d.F("agent-a"), at = d.F("agent-a-text");
    const aTxt = "Il vous reste 24 jours sur la période du 01/06/2026 au 31/05/2027. J’ai préparé votre demande :";
    if (aa) aa.hidden = t < T.answer;
    setText(at, t < T.answer ? "" : t < T.answer + 0.35 ? "•••" : typed(aTxt, t, T.answer + 0.35, T.prep - 0.05));
    const pc = d.F("agent-prep");
    if (pc) { pc.hidden = t < T.prep; const p = E.outExpo(seg(t, T.prep, T.prep + 0.6)); pc.style.opacity = clamp(p * 1.4).toFixed(3); pc.style.transform = `translateY(${(16 * (1 - p)).toFixed(1)}px)`; glowEl(pc, pulse(t, T.prep + 0.1, 1.2)); }
    const pb = d.F("agent-prep-badge"), ok = t >= T.okAgent + 0.1;
    if (pb) { setText(pb, ok ? "✓ Demande envoyée" : "À confirmer"); pb.className = "mw-badge " + (ok ? "green" : "amber"); }
    const pa = d.F("agent-prep-actions");
    if (pa) pa.style.opacity = ok ? "0.45" : "1";
    press(d.F("agent-confirm"), t, T.okAgent);
    glowEl(d.F("agent-confirm"), pulse(t, T.toi, 1.2));
  },
};
function applyStates(t) {
  for (const id of Object.keys(INST)) {
    const fn = STATE[id];
    if (!fn) continue;
    for (const f of INST[id].frames) {
      const doc = f.contentDocument;
      if (!doc) continue;
      const d = { doc, F: n => doc.querySelector(`[data-film="${n}"]`), $: s => doc.querySelector(s), all: s => Array.from(doc.querySelectorAll(s)) };
      fn(d, t);
    }
  }
}
