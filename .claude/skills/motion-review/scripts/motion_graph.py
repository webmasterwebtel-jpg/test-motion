#!/usr/bin/env python3
"""Courbe d'énergie de mouvement image par image, superposée à l'enveloppe d'attaques du son.

Donne des « yeux » sur le rythme sans regarder la vidéo :
  - énergie visuelle  = différence moyenne entre images successives (en % de la plage 0–255) ;
  - attaques audio    = flux spectral (bruitages, kicks) ramené à une valeur par image ;
  - tenues            = passages calmes assez longs pour lire l'image (grain, tremblé stop-motion
                        et flottements légers tolérés) ;
  - surcharges        = passages agités trop longs (fatigue, illisible) ;
  - synchro           = décalage (en images) entre chaque impact visuel et l'attaque sonore la plus proche.

Sorties : un PNG (une ligne par tranche de --row secondes) + un rapport texte (stdout) + un JSON.

Exemples :
    python3 motion_graph.py output/film.mp4 --bpm 120
    python3 motion_graph.py output/film.mp4 --start 28 --end 39 --bpm 120 --marks "28:Mosaïque,35:Bento"
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import probe, read_frames, has_audio, read_audio, onset_envelope, peaks, label_font  # noqa: E402

HOLD_THR = 0.8      # % (écart flouté à 0,2 s) : en dessous, l'image est « posée » et lisible
BUSY_THR = 4.0      # % : moyenne glissante sur 1 s au-dessus = agitation forte
HIT_THR = 3.0       # % : pic minimal pour compter un impact visuel
BURST_THR = 1.2     # % : seuil d'une « bouffée » de mouvement
SYNC_WIN = 4        # images : fenêtre de recherche de l'attaque sonore autour d'un impact


def runs(mask):
    """[(début, fin)) des suites de True."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None)
    ap.add_argument("--bpm", type=float, default=None, help="trace la grille des temps et mesures")
    ap.add_argument("--offset", type=float, default=0.0, help="temps du premier temps fort (s)")
    ap.add_argument("--marks", default="", help='repères de sections "4:Pile,16:Zoom"')
    ap.add_argument("--min-hold", type=float, default=0.5, help="durée minimale d'une tenue (s)")
    ap.add_argument("--row", type=float, default=10.0, help="secondes par ligne du graphique")
    ap.add_argument("--px", type=int, default=150, help="pixels par seconde")
    ap.add_argument("--out", default=None, help="chemin du PNG (le JSON est écrit à côté)")
    a = ap.parse_args()

    W, H, fps, dur = probe(a.video)
    end = min(a.end if a.end is not None else dur, dur)
    w = 120
    h = int(round(w * H / W))
    g = read_frames(a.video, a.start, end, w, h, gray=True).astype(np.float32)
    n = len(g)
    t = a.start + np.arange(n) / fps
    energy = np.zeros(n)
    energy[1:] = np.abs(g[1:] - g[:-1]).mean(axis=(1, 2)) / 255 * 100
    # immobilité « perçue » : écart entre images floutées distantes de 0,2 s — le grain, le tremblé
    # stop-motion et les micro-flottements disparaissent, un vrai déplacement reste
    k = max(int(round(fps * 0.2)), 1)
    gb = ndimage.gaussian_filter(g, (0, 2, 2))
    calm = np.zeros(n)
    calm[k:] = np.abs(gb[k:] - gb[:-k]).mean(axis=(1, 2)) / 255 * 100
    calm[:k] = calm[k] if n > k else 0
    calm = ndimage.median_filter(calm, 3)
    busy = ndimage.uniform_filter1d(energy, int(round(fps)))

    audio = None
    if has_audio(a.video):
        sr = int(round(fps * 735))                        # 22050 Hz à 30 i/s : un bloc par image
        x = read_audio(a.video, sr, a.start, end)
        audio = onset_envelope(x, sr, int(round(sr / fps)))[:n]
        audio = np.pad(audio, (0, n - len(audio)))

    # --- tenues, surcharges, impacts
    holds = [(i, j) for i, j in runs(calm < HOLD_THR) if (j - i) / fps >= a.min_hold]
    busys = [(i, j) for i, j in runs(busy > BUSY_THR) if (j - i) / fps >= 2.5]
    # événements visuels : une « bouffée » de mouvement = départ, pic de vitesse, contact (arrêt net)
    events = []
    for i, j in runs(ndimage.binary_closing(energy > BURST_THR, iterations=1)):
        if j - i < 1:
            continue
        pk = i + int(np.argmax(energy[i:j]))
        if energy[pk] < HIT_THR:
            continue
        ct = pk
        while ct + 1 < j and energy[ct + 1] > 0.35 * energy[pk]:
            ct += 1
        events.append(dict(start=i, peak=pk, contact=ct, end=j, cut=bool((j - i) <= 2)))
    onsets = peaks(audio, 0.2, 2) if audio is not None else []
    for e in events:
        # un son peut légitimement marquer le départ (kick, whoosh), le pic de vitesse ou le contact (claque)
        e["marked"] = [k for k in ("start", "peak", "contact") if any(abs(o - e[k]) <= 1 for o in onsets)]
        near = [o for o in onsets if e["start"] - SYNC_WIN <= o <= e["contact"] + SYNC_WIN]
        if near:
            o = max(near, key=lambda o: audio[o])
            e["onset"] = o
            e["d_contact"] = o - e["contact"]                 # >0 : le son arrive après le contact
        c = e["contact"]
        e["hard_stop"] = bool(c + 2 < n and energy[c + 2] < 0.4 * energy[e["peak"]])
    hits = [e["contact"] for e in events]
    gaps, prev = [], 0                                     # plus long passage sans tenue
    for i, j in holds + [(n, n)]:
        gaps.append((prev, i))
        prev = j
    worst_gap = max(gaps, key=lambda ab: ab[1] - ab[0]) if gaps else (0, 0)

    # --- rapport
    def ts(i):
        return "%.2f" % t[min(i, n - 1)]
    print("== %s  [%.2f–%.2f s, %d images à %g i/s]" % (os.path.basename(a.video), a.start, end, n, fps))
    print("énergie moyenne %.2f %% · médiane %.2f %% · max %.1f %% (image %s s)"
          % (energy.mean(), np.median(energy), energy.max(), ts(int(energy.argmax()))))
    hold_time = sum(j - i for i, j in holds) / fps
    print("\nTENUES (calme ≥ %.1f s) : %d, %.1f s au total (%.0f %% du passage)"
          % (a.min_hold, len(holds), hold_time, 100 * hold_time / max(n / fps, 1e-6)))
    for i, j in holds:
        print("  %s → %s s  (%.2f s)" % (ts(i), ts(j - 1), (j - i) / fps))
    print("  plus long passage sans tenue : %s → %s s (%.1f s)"
          % (ts(worst_gap[0]), ts(worst_gap[1] - 1), (worst_gap[1] - worst_gap[0]) / fps))
    print("\nSURCHARGES (agitation > %.0f %% sur ≥ 2,5 s) : %d" % (BUSY_THR, len(busys)))
    for i, j in busys:
        print("  %s → %s s  (%.1f s, moyenne %.1f %%)" % (ts(i), ts(j - 1), (j - i) / fps, energy[i:j].mean()))
    print("\nÉVÉNEMENTS VISUELS : %d (dont %d coupes/flashs)" % (len(events), sum(e["cut"] for e in events)))
    if audio is not None and events:
        marked = [e for e in events if e["marked"]]
        print("  synchro : %d/%d événements ont une attaque sonore (±1 image) sur leur départ, pic ou contact"
              % (len(marked), len(events)))
        for e in events:
            if not e["marked"]:
                extra = (" ; attaque la plus forte à %s s (%+d image(s) / contact)" % (ts(e["onset"]), e["d_contact"])
                         if "onset" in e else " ; aucun son marquant à ±%d images" % SYNC_WIN)
                print("  ! %s s (pic %s, contact %s) : son décalé ou absent%s"
                      % (ts(e["start"]), ts(e["peak"]), ts(e["contact"]), extra))
        mute = [e for e in events if e["hard_stop"] and "contact" not in e["marked"]]
        if mute:
            print("  arrêts nets sans son au contact (un bruitage à cet instant donnerait du poids) : "
                  + ", ".join("%s s" % ts(e["contact"]) for e in mute))
    if a.bpm and events:
        beat = 60.0 / a.bpm
        ph = [((t[e["contact"]] - a.offset) / beat) % 1 for e in events]
        ph = [p if p < 0.5 else p - 1 for p in ph]
        on = sum(abs(p) * beat * fps <= 1.5 for p in ph)
        print("  calage sur la grille %g BPM : %d/%d contacts à ±1,5 image d'un temps" % (a.bpm, on, len(events)))

    # --- graphique
    marks = []
    for m in filter(None, a.marks.split(",")):
        tt, _, lab = m.partition(":")
        marks.append((float(tt), lab))
    row_s, px = a.row, a.px
    nrows = int(np.ceil((end - a.start) / row_s))
    rh, top, left = 170, 26, 44
    img = Image.new("RGB", (left + int(row_s * px) + 12, top + nrows * rh + 30), (250, 250, 248))
    d = ImageDraw.Draw(img)
    f = label_font(12)
    vmax = max(8.0, float(np.percentile(energy, 99)))
    d.text((left, 6), "énergie de mouvement (bleu, haut) · attaques audio (orange, bas) · tenues (vert) · "
           "impacts (rouge) · échelle haute %.0f %%" % vmax, fill=(40, 40, 40), font=f)
    for r in range(nrows):
        t0 = a.start + r * row_s
        y0 = top + r * rh
        mid = y0 + 95
        X = lambda tt: left + (tt - t0) * px  # noqa: E731
        d.line([left, mid, left + row_s * px, mid], fill=(180, 180, 180))
        for i, j in holds:
            if t[j - 1] >= t0 and t[i] < t0 + row_s:
                d.rectangle([X(max(t[i], t0)), y0 + 8, X(min(t[j - 1], t0 + row_s)), mid], fill=(214, 240, 214))
        for i, j in busys:
            if t[j - 1] >= t0 and t[i] < t0 + row_s:
                d.rectangle([X(max(t[i], t0)), y0 + 4, X(min(t[j - 1], t0 + row_s)), y0 + 8], fill=(225, 60, 60))
        if a.bpm:
            beat = 60.0 / a.bpm
            k0 = int(np.ceil((t0 - a.offset) / beat))
            k = k0
            while a.offset + k * beat <= t0 + row_s:
                xx = X(a.offset + k * beat)
                d.line([xx, y0 + 8, xx, y0 + rh - 22], fill=(150, 150, 150) if k % 4 == 0 else (225, 225, 225))
                k += 1
        sel = (t >= t0) & (t < t0 + row_s)
        idx = np.nonzero(sel)[0]
        if len(idx) > 1:
            pts = [(X(t[i]), mid - min(energy[i] / vmax, 1) * 85) for i in idx]
            d.polygon([(pts[0][0], mid)] + pts + [(pts[-1][0], mid)], fill=(90, 140, 230))
            if audio is not None:
                pts = [(X(t[i]), mid + audio[i] * 50) for i in idx]
                d.line(pts, fill=(240, 130, 30), width=1)
        for i in hits:
            if sel[i]:
                d.line([X(t[i]), y0 + 10, X(t[i]), y0 + 18], fill=(220, 30, 30), width=2)
        for i in onsets:
            if sel[i]:
                d.line([X(t[i]), mid + 52, X(t[i]), mid + 58], fill=(240, 130, 30), width=2)
        for tt, lab in marks:
            if t0 <= tt < t0 + row_s:
                d.line([X(tt), y0 + 4, X(tt), y0 + rh - 22], fill=(30, 30, 30), width=2)
                d.text((X(tt) + 3, y0 + 20), lab, fill=(30, 30, 30), font=f)
        s = int(np.ceil(t0))
        while s <= t0 + row_s:
            d.text((X(s) - 6, y0 + rh - 20), "%ds" % s, fill=(90, 90, 90), font=f)
            s += 1
    out = a.out or os.path.join("build", "review", "motion_%05.2f_%05.2f.png" % (a.start, end))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    img.save(out)
    rep = dict(video=a.video, start=a.start, end=end, fps=fps,
               holds=[[round(t[i], 3), round(t[j - 1], 3)] for i, j in holds],
               busy=[[round(t[i], 3), round(t[j - 1], 3)] for i, j in busys],
               hits=[round(t[i], 3) for i in hits],
               events=[{k: (round(float(t[v]), 3) if k in ("start", "peak", "contact", "end", "onset") and v < n
                            else v) for k, v in e.items()} for e in events],
               energy=[round(float(e), 3) for e in energy])
    with open(os.path.splitext(out)[0] + ".json", "w") as fh:
        json.dump(rep, fh)
    print("\n->", out, "(+ .json)")


if __name__ == "__main__":
    main()
