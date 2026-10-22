#!/usr/bin/env python3
"""Compare deux rendus d'un même film (avant / après une modification).

Répond à trois questions : qu'est-ce qui a changé (et où), est-ce que ça a changé ailleurs que prévu,
et le rythme / le son se sont-ils améliorés ?

Sorties (stdout + PNG) :
  - plages de temps où l'image diffère (écart moyen entre images, en % de la plage 0–255) ;
  - tableau comparatif : durée, tenues (nombre, temps cumulé, plus long passage sans tenue), énergie moyenne,
    loudness / crête vraie / LRA, énergie de la 1re image ;
  - une planche « A | B | différence amplifiée » aux instants les plus différents (ou --times) ;
  - une courbe d'énergie superposée (A bleu, B orange).
Les deux vidéos doivent avoir la même cadence. Si les durées diffèrent, la comparaison porte sur la durée commune.

Exemples :
    python3 compare_versions.py output/avant.mp4 output/apres.mp4
    python3 compare_versions.py A.mp4 B.mp4 --times 6 14 28 --expect 10:12     # le changement doit rester dans 10–12 s
"""
import argparse, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "motion-review", "scripts"))
from _common import probe, read_frames, label_font  # noqa: E402

DIFF_THR = 0.5     # % : écart moyen au-dessus duquel une image est dite « différente »
HOLD_THR = 0.8     # % (écart flouté à 0,2 s) : même critère de tenue que motion_graph.py


def runs(mask):
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


def loudness(path):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    if "Summary:" not in err:
        return None
    s = err[err.rfind("Summary:"):]
    g = lambda k: float(re.search(k + r":\s+(-?[\d.]+)", s).group(1))  # noqa: E731
    return dict(I=g("I"), LRA=g("LRA"), TP=g("Peak"))


def stats(path, g, fps):
    n = len(g)
    energy = np.zeros(n)
    energy[1:] = np.abs(g[1:] - g[:-1]).mean(axis=(1, 2)) / 255 * 100
    k = max(int(round(fps * 0.2)), 1)
    gb = ndimage.gaussian_filter(g, (0, 2, 2))
    calm = np.zeros(n)
    calm[k:] = np.abs(gb[k:] - gb[:-k]).mean(axis=(1, 2)) / 255 * 100
    calm[:k] = calm[k] if n > k else 0
    calm = ndimage.median_filter(calm, 3)
    holds = [(i, j) for i, j in runs(calm < HOLD_THR) if (j - i) / fps >= 0.5]
    gaps, prev = [], 0
    for i, j in holds + [(n, n)]:
        gaps.append(i - prev)
        prev = j
    return dict(energy=energy, holds=holds, hold_time=sum(j - i for i, j in holds) / fps,
                worst_gap=max(gaps) / fps if gaps else 0, mean_energy=float(energy.mean()),
                first=float(g[0].std()), loud=loudness(path))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--times", type=float, nargs="+", help="instants de la planche (défaut : les 6 plus différents)")
    ap.add_argument("--expect", default=None, help="plage(s) où le changement est attendu, ex. 10:12,20:22")
    ap.add_argument("--out", default=os.path.join("build", "review", "compare.png"))
    a = ap.parse_args()

    Wa, Ha, fa, da = probe(a.a)
    Wb, Hb, fb, db = probe(a.b)
    if abs(fa - fb) > 0.01 or (Wa, Ha) != (Wb, Hb):
        sys.exit("formats différents : %dx%d @%.2f contre %dx%d @%.2f" % (Wa, Ha, fa, Wb, Hb, fb))
    fps, dur = fa, min(da, db)
    w = 120
    h = int(round(w * Ha / Wa))
    ga = read_frames(a.a, 0, dur, w, h, gray=True).astype(np.float32)
    gb = read_frames(a.b, 0, dur, w, h, gray=True).astype(np.float32)
    n = min(len(ga), len(gb))
    ga, gb = ga[:n], gb[:n]
    diff = np.abs(ga - gb).mean(axis=(1, 2)) / 255 * 100
    sa, sb = stats(a.a, ga, fps), stats(a.b, gb, fps)

    print("== A = %s · B = %s · %d images à %g i/s" % (os.path.basename(a.a), os.path.basename(a.b), n, fps))
    if abs(da - db) > 1 / fps:
        print("durées différentes : A %.2f s, B %.2f s (comparaison sur %.2f s)" % (da, db, dur))
    spans = [(i / fps, j / fps) for i, j in runs(ndimage.binary_closing(diff > DIFF_THR, iterations=int(fps * 0.1)))]
    print("\nIMAGE : %d plage(s) différente(s) (écart moyen > %.1f %%), %.1f %% des images au total" % (
        len(spans), DIFF_THR, 100 * (diff > DIFF_THR).mean()))
    for s0, s1 in spans[:25]:
        seg = diff[int(s0 * fps):int(s1 * fps)]
        print("  %6.2f → %6.2f s  (%.2f s, écart moyen %.1f %%, max %.1f %%)" % (s0, s1, s1 - s0, seg.mean(), seg.max()))
    if len(spans) > 25:
        print("  … %d autres" % (len(spans) - 25))
    if a.expect:
        exp = [tuple(float(x) for x in r.split(":")) for r in a.expect.split(",")]
        outside = [(s0, s1) for s0, s1 in spans if not any(s0 >= e0 - 0.2 and s1 <= e1 + 0.2 for e0, e1 in exp)]
        missing = [e for e in exp if not any(s1 > e[0] and s0 < e[1] for s0, s1 in spans)]
        print("\nATTENDU : %s" % a.expect)
        print("  changements HORS de la plage attendue : %s" % (", ".join("%.2f–%.2f s" % s for s in outside) or "aucun ✔"))
        print("  plages attendues SANS changement visible : %s" % (", ".join("%g–%g s" % e for e in missing) or "aucune ✔"))

    def row(label, va, vb, fmt, better=None):
        d = vb - va
        mark = ""
        if better and abs(d) > 0.02 * max(abs(va), abs(vb), 1e-9):      # sous 2 % : bruit de mesure
            mark = "  ↑ mieux" if (d > 0) == (better == "up") else "  ↓ moins bien"
        print("  %-30s %12s %12s %s%s" % (label, fmt % va, fmt % vb, "(%+.2f)" % d if abs(d) > 1e-9 else "", mark))

    print("\n%-32s %12s %12s" % ("RYTHME ET SON", "A", "B"))
    row("tenues lisibles (nombre)", len(sa["holds"]), len(sb["holds"]), "%d")
    row("tenues, temps cumulé (s)", sa["hold_time"], sb["hold_time"], "%.1f")
    row("plus long passage sans tenue (s)", sa["worst_gap"], sb["worst_gap"], "%.1f", "down")
    row("énergie moyenne (%)", sa["mean_energy"], sb["mean_energy"], "%.2f")
    row("contraste de la 1re image", sa["first"], sb["first"], "%.1f", "up")
    if sa["loud"] and sb["loud"]:
        row("loudness (LUFS)", sa["loud"]["I"], sb["loud"]["I"], "%.1f")
        row("crête vraie (dBTP)", sa["loud"]["TP"], sb["loud"]["TP"], "%.1f", "down")
        row("plage dynamique LRA (LU)", sa["loud"]["LRA"], sb["loud"]["LRA"], "%.1f")

    # planche
    if a.times:
        times = a.times
    else:
        order, times = np.argsort(-diff), []
        for i in order:
            if diff[i] <= DIFF_THR:
                break
            if all(abs(i / fps - t) > 0.5 for t in times):
                times.append(i / fps)
            if len(times) == 6:
                break
        times.sort()
    if times:
        tw, th = 200, int(200 * Ha / Wa)
        pad, lab = 6, 20
        sheet = Image.new("RGB", (pad + 3 * (tw + pad), pad + len(times) * (th + lab + pad)), (24, 24, 24))
        d = ImageDraw.Draw(sheet)
        f = label_font(13)
        for r, t in enumerate(times):
            raw = []
            for p in (a.a, a.b):
                x = read_frames(p, max(t - 0.001, 0), t + 1.0 / fps, tw, th)
                raw.append(x[0])
            df = np.abs(raw[0].astype(np.float32) - raw[1].astype(np.float32)).max(axis=2)
            heat = np.clip(df * 3, 0, 255).astype(np.uint8)
            heat_rgb = np.stack([heat, heat * 0 + 40, 255 - heat], -1).astype(np.uint8)
            for c, (im, name) in enumerate(((raw[0], "A"), (raw[1], "B"), (heat_rgb, "écart ×3"))):
                x0, y0 = pad + c * (tw + pad), pad + r * (th + lab + pad)
                sheet.paste(Image.fromarray(im), (x0, y0))
                d.text((x0 + 2, y0 + th + 3), "%s · %.2f s" % (name, t), fill=(225, 225, 225), font=f)
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        sheet.save(a.out)
        print("\nplanche : %s" % a.out)

    # courbe d'énergie superposée
    cw, ch = 1000, 220
    img = Image.new("RGB", (cw + 60, ch + 40), (250, 250, 248))
    d = ImageDraw.Draw(img)
    f = label_font(12)
    vmax = max(8.0, float(np.percentile(np.concatenate([sa["energy"], sb["energy"]]), 99)))
    X = lambda i: 50 + i / max(n - 1, 1) * cw  # noqa: E731
    Y = lambda v: 10 + ch - min(v / vmax, 1) * ch  # noqa: E731
    for e, col in ((sa["energy"], (60, 110, 220)), (sb["energy"], (240, 130, 30))):
        d.line([(X(i), Y(v)) for i, v in enumerate(e)], fill=col, width=1)
    for s0, s1 in spans:
        d.rectangle([X(s0 * fps), ch + 14, X(s1 * fps), ch + 20], fill=(210, 50, 50))
    for s in range(0, int(dur) + 1, 5):
        d.text((X(s * fps) - 6, ch + 22), "%ds" % s, fill=(90, 90, 90), font=f)
    d.text((54, 12), "énergie de mouvement : A bleu, B orange · barre rouge = image différente", fill=(40, 40, 40), font=f)
    curve = os.path.splitext(a.out)[0] + "_energie.png"
    img.save(curve)
    print("courbes : %s" % curve)


if __name__ == "__main__":
    main()
