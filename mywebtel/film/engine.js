/* MyWebtel — film V6, moteur.
 * Tout est fonction du temps : renderAt(t) (story.js) pose chaque élément ; rien n'est animé par le navigateur,
 * donc le rendu image par image (render.js) est exact et reproductible.
 * Repère du monde (pixels) : x vers la droite, y vers le BAS (le sol est le plan y = 0, « en l'air » = y négatif),
 * z vers le spectateur. Les objets DOM du monde reçoivent une matrice 4×4 (matrix3d) calculée ici ; la même matrice sert
 * à projeter des points à l'écran (curseur, lumières, sol dessiné sur canvas), d'où un calage exact entre les calques.
 */
"use strict";
const TL = window.TL, UI = window.UI || {};
const VW = 1920, VH = 1080, CX = 960, CY = 540;

// ------------------------------------------------------------------ outils numériques
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const seg = (t, a, b) => (b === a ? (t >= b ? 1 : 0) : clamp((t - a) / (b - a)));
const lerp = (a, b, x) => a + (b - a) * x;
const mix3 = (a, b, x) => [lerp(a[0], b[0], x), lerp(a[1], b[1], x), lerp(a[2], b[2], x)];
const E = {
  lin: x => x,
  inQuad: x => x * x, outQuad: x => 1 - (1 - x) * (1 - x),
  inCubic: x => x * x * x, outCubic: x => 1 - Math.pow(1 - x, 3),
  inOutCubic: x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  outQuart: x => 1 - Math.pow(1 - x, 4), inQuart: x => x * x * x * x,
  inOutQuart: x => (x < 0.5 ? 8 * x ** 4 : 1 - Math.pow(-2 * x + 2, 4) / 2),
  inOutQuint: x => (x < 0.5 ? 16 * x ** 5 : 1 - Math.pow(-2 * x + 2, 5) / 2),
  outQuint: x => 1 - Math.pow(1 - x, 5),
  outExpo: x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)), inExpo: x => (x <= 0 ? 0 : Math.pow(2, 10 * x - 10)),
  inOutExpo: x => (x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2),
  inOutSine: x => -(Math.cos(Math.PI * x) - 1) / 2,
  outBack: x => { const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
};
function spring(t, z = 0.72, f = 2.6) {
  if (t <= 0) return 0;
  const w = 2 * Math.PI * f;
  if (z < 1) { const wd = w * Math.sqrt(1 - z * z); return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + (z * w / wd) * Math.sin(wd * t)); }
  return 1 - Math.exp(-w * t) * (1 + w * t);
}
const pulse = (t, t0, d = 1.4) => Math.sin(Math.PI * seg(t, t0, t0 + d));
const bump = (t, a, b, c, d) => seg(t, a, b) * (1 - seg(t, c, d));            // monte de a à b, tient, redescend de c à d
function hash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
function noise1(x, seed = 0) {                                                   // bruit de valeur lissé, déterministe
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  return lerp(hash(i + seed * 57.3), hash(i + 1 + seed * 57.3), u) * 2 - 1;
}

// ------------------------------------------------------------------ voix : instants des mots (timeline.json)
const SC = {}; TL.scenes.forEach(s => { SC[s.id] = s; });
const S0 = id => SC[id].start, S1 = id => SC[id].end;
const segT = (id, i = 0) => SC[id].segs[i].start, segE = (id, i = 0) => SC[id].segs[i].end;
const fold = s => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/’/g, "'");
function W(id, i, word, n = 0) {                       // instant où le n-ième « word » est prononcé dans le segment i
  const k = SC[id].segs[i].words.filter(w => fold(w[0]) === fold(word));
  if (!k[n]) throw new Error("mot absent : " + id + "/" + i + "/" + word + " #" + n);
  return k[n][1];
}
const BEAT = TL.beat, BAR = TL.beat * 4;
const onBar = x => Math.round(x / BAR) * BAR, onBeat = x => Math.round(x / BEAT) * BEAT;

// ------------------------------------------------------------------ DOM
function h(html) { const d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstElementChild; }
function add(parent, html) { const e = h(html); parent.appendChild(e); return e; }
const q = (root, sel) => root.querySelector(sel);
const qa = (root, sel) => Array.from(root.querySelectorAll(sel));
const setText = (el, s) => { if (el && el.textContent !== s) el.textContent = s; };
const setHTML = (el, s) => { if (el && el.__html !== s) { el.innerHTML = s; el.__html = s; } };
function setValue(el, v, focus) {
  if (!el) return;
  if (el.value !== v) el.value = v;
  if (focus && el.ownerDocument.activeElement !== el) el.focus({ preventScroll: true });
  if (!focus && el.ownerDocument.activeElement === el) el.blur();
}
function opa(el, o) {                                      // opacité + masquage complet sous un seuil
  if (!el) return;
  const v = clamp(o);
  const s = v.toFixed(4);
  if (el.__o !== s) { el.style.opacity = s; el.__o = s; }
  const hide = v <= 0.002;
  if (el.__hid !== hide) { el.style.visibility = hide ? "hidden" : "visible"; el.__hid = hide; }
}
function blur(el, b) { if (!el) return; const s = b > 0.05 ? `blur(${b.toFixed(2)}px)` : "none"; if (el.__b !== s) { el.style.filter = s; el.__b = s; } }
const ICON = {
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18"/>',
  file: '<path d="M14 3H5v18h14V8zM14 3v5h5M8 12h8m-8 4h8"/>',
  pen: '<path d="M4 20l4-1 11-11-3-3L5 16z"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  home: '<path d="M3 11 12 4l9 7M5 10v10h14V10"/>',
  alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7v6m0 3.5v.5"/>',
  doc: '<path d="M14 3H5v18h14V8zM14 3v5h5"/>',
  req: '<path d="M4 5h16v11H9l-5 4zM8 9h8M8 12h5"/>',
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  mail: '<path d="M3 4h18v13H8l-5 4zM7 8h10m-10 5h6"/>',
  shield: '<path d="m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6zm-4 9 3 3 5-5"/>',
  spark: '<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
  lock: '<rect x="5" y="11" width="14" height="10" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  unlock: '<rect x="5" y="11" width="14" height="10" rx="2.5"/><path d="M8 11V8a4 4 0 0 1 7.5-2"/>',
};
const ic = n => `<svg class="i" viewBox="0 0 24 24">${ICON[n]}</svg>`;

// ------------------------------------------------------------------ matrices 4×4 (ordre colonne, comme matrix3d)
const M4 = {
  I: () => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
  mul(a, b) {
    const o = new Array(16);
    for (let c = 0; c < 4; c++) for (let r = 0; r < 4; r++) {
      o[c * 4 + r] = a[r] * b[c * 4] + a[4 + r] * b[c * 4 + 1] + a[8 + r] * b[c * 4 + 2] + a[12 + r] * b[c * 4 + 3];
    }
    return o;
  },
  T: (x, y, z) => [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, x, y, z, 1],
  S: (x, y = x, z = x) => [x, 0, 0, 0, 0, y, 0, 0, 0, 0, z, 0, 0, 0, 0, 1],
  RX(d) { const a = d * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, 0, 0, 0, 1]; },
  RY(d) { const a = d * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [c, 0, -s, 0, 0, 1, 0, 0, s, 0, c, 0, 0, 0, 0, 1]; },
  RZ(d) { const a = d * Math.PI / 180, c = Math.cos(a), s = Math.sin(a); return [c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]; },
  chain(...ms) { return ms.reduce((a, b) => M4.mul(a, b)); },
  apply(m, x, y, z = 0) { return [m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13], m[2] * x + m[6] * y + m[10] * z + m[14]]; },
  css(m) { return "matrix3d(" + m.map(v => (Math.abs(v) < 1e-9 ? 0 : v).toFixed(6)).join(",") + ")"; },
};
const V3 = {
  add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]], sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
  mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s], dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
  len: a => Math.hypot(a[0], a[1], a[2]),
};

// ------------------------------------------------------------------ caméra « orbite » : une cible, une distance, des angles
// pitch > 0 : regarde vers le bas (90° = vue de dessus, le haut des pages vers le haut de l'écran) ; yaw : tourne
// autour de la verticale ; roll : bascule ; F : distance de perspective (focale), en pixels.
const CAM = { tx: 0, ty: 0, tz: 0, dist: 2000, yaw: 0, pitch: 20, roll: 0, F: 1600 };
const cam = { C: [0, 0, 0], r: [1, 0, 0], d: [0, 1, 0], b: [0, 0, 1], F: 1600, view: M4.I(), rot: M4.I() };
function solveCamera(s) {
  const R = M4.chain(M4.RY(s.yaw), M4.RX(s.pitch), M4.RZ(s.roll));   // repère caméra dans le monde
  const r = M4.apply(R, 1, 0, 0), d = M4.apply(R, 0, 1, 0), b = M4.apply(R, 0, 0, 1);
  const fwd = V3.mul(b, -1);
  const C = V3.sub([s.tx, s.ty, s.tz], V3.mul(fwd, s.dist));
  cam.C = C; cam.r = r; cam.d = d; cam.b = b; cam.F = s.F; cam.rot = R;
  const rows = [r[0], d[0], b[0], 0, r[1], d[1], b[1], 0, r[2], d[2], b[2], 0, 0, 0, 0, 1];
  cam.view = M4.chain(M4.T(CX, CY, s.F), rows, M4.T(-C[0], -C[1], -C[2]));
  return cam;
}
function toCam(P) { const v = V3.sub(P, cam.C); return [V3.dot(cam.r, v), V3.dot(cam.d, v), V3.dot(cam.b, v)]; }
function project(P, near = 30) {                          // -> [x écran, y écran, échelle, profondeur] ou null derrière la caméra
  const c = toCam(P);
  if (c[2] > -near) return null;
  const s = cam.F / -c[2];
  return [CX + c[0] * s, CY + c[1] * s, s, -c[2]];
}
const camState = (o = {}) => Object.assign({}, CAM, o);
function lerpCam(a, b, p) {
  const o = {};
  for (const k of Object.keys(CAM)) o[k] = lerp(a[k], b[k], p);
  return o;
}

// ------------------------------------------------------------------ objets du monde
// Un objet = un élément DOM (enfant de #world) + sa matrice monde. place() calcule la matrice à partir d'une position,
// d'angles et d'une ancre (0..1 dans la largeur/hauteur), l'écrit en CSS et la garde pour projeter des points locaux.
class Obj {
  constructor(el, w, h) { this.el = el; this.w = w; this.h = h; this.M = M4.I(); this.__css = ""; }
  place({ x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1, ax = 0.5, ay = 0.5, flat = false, bill = false, rot = null } = {}) {
    let R;
    if (rot) R = M4.chain(rot, M4.RY(ry), M4.RX(rx), M4.RZ(rz));               // orientation imposée (figée dans le monde)
    else if (bill) R = M4.chain(cam.rot, M4.RY(ry), M4.RX(rx), M4.RZ(rz));          // face à la caméra (+ rotations propres)
    else R = M4.chain(M4.RY(ry), M4.RX(rx + (flat ? 90 : 0)), M4.RZ(rz));       // flat : couché sur le sol, haut vers le nord
    this.M = M4.chain(M4.T(x, y, z), R, M4.S(s), M4.T(-ax * this.w, -ay * this.h, 0));
    return this.setM(this.M);
  }
  setM(m) {
    this.M = m;
    const css = M4.css(m);
    if (css !== this.__css) { this.el.style.transform = css; this.__css = css; }
    return this;
  }
  world(u, v) { return M4.apply(this.M, u, v, 0); }                            // point local (px) -> monde
  screen(u, v) { return project(this.world(u, v)); }
  corners() { return [[0, 0], [this.w, 0], [this.w, this.h], [0, this.h]].map(([u, v]) => this.world(u, v)); }
  visible(margin = 300) {                                                       // à l'écran (approximation par les coins)
    const ps = this.corners().map(p => project(p, 10));
    if (ps.some(p => !p)) return true;
    const xs = ps.map(p => p[0]), ys = ps.map(p => p[1]);
    return !(Math.max(...xs) < -margin || Math.min(...xs) > VW + margin || Math.max(...ys) < -margin || Math.min(...ys) > VH + margin);
  }
}

// ------------------------------------------------------------------ dessin 3D sur canvas (sol, lumières, particules)
function clipSeg(a, b, near = 40) {                       // segment en repère caméra, coupé au plan proche
  if (a[2] > -near && b[2] > -near) return null;
  if (a[2] > -near) { const k = (-near - b[2]) / (a[2] - b[2]); a = [lerp(b[0], a[0], k), lerp(b[1], a[1], k), -near]; }
  else if (b[2] > -near) { const k = (-near - a[2]) / (b[2] - a[2]); b = [lerp(a[0], b[0], k), lerp(a[1], b[1], k), -near]; }
  return [a, b];
}
const scr = c => { const s = cam.F / -c[2]; return [CX + c[0] * s, CY + c[1] * s, s]; };
function line3(ctx, A, B, { color = "#fff", width = 2, alpha = 1, glow = 0 } = {}) {
  const s = clipSeg(toCam(A), toCam(B));
  if (!s) return;
  const p = scr(s[0]), q2 = scr(s[1]);
  ctx.globalAlpha = alpha; ctx.strokeStyle = color; ctx.lineWidth = width;
  if (glow) { ctx.shadowColor = color; ctx.shadowBlur = glow; } else ctx.shadowBlur = 0;
  ctx.beginPath(); ctx.moveTo(p[0], p[1]); ctx.lineTo(q2[0], q2[1]); ctx.stroke();
}
function poly3(ctx, pts, { fill = null, stroke = null, width = 2, alpha = 1, glow = 0, filter = "none" } = {}) {
  const ps = pts.map(P => project(P, 20));
  if (ps.some(p => !p)) return;
  ctx.globalAlpha = alpha; ctx.filter = filter;
  ctx.beginPath(); ps.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  if (glow) { ctx.shadowColor = stroke || fill; ctx.shadowBlur = glow; } else ctx.shadowBlur = 0;
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = width; ctx.stroke(); }
  ctx.filter = "none";
}
const SPRITES = {};
function sprite(color, size = 64) {                       // tache lumineuse radiale (mise en cache)
  const k = color + size;
  if (SPRITES[k]) return SPRITES[k];
  const c = document.createElement("canvas"); c.width = c.height = size;
  const g = c.getContext("2d"), grd = g.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  grd.addColorStop(0, color); grd.addColorStop(0.25, color.replace(/[\d.]+\)$/, "0.55)")); grd.addColorStop(1, color.replace(/[\d.]+\)$/, "0)"));
  g.fillStyle = grd; g.fillRect(0, 0, size, size);
  return (SPRITES[k] = c);
}
function dot3(ctx, P, radius, color, alpha = 1) {        // point lumineux à la bonne taille perspective
  const p = project(P, 20);
  if (!p) return;
  const r = radius * p[2];
  if (r < 0.3 || p[0] < -r || p[0] > VW + r || p[1] < -r || p[1] > VH + r) return;
  ctx.globalAlpha = alpha;
  ctx.drawImage(sprite(color), p[0] - r, p[1] - r, 2 * r, 2 * r);
}
