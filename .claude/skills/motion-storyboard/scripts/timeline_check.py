#!/usr/bin/env python3
"""Contrôle de cohérence de la timeline écrite DEUX fois : motion/collage.py (image) et motion/audio_collage.py (son).

C'est la première cause de désynchronisation du projet : un temps modifié d'un seul côté. Ce script ne rend rien
(quelques secondes) et vérifie, directement sur le code :
  1. les constantes qui doivent être identiques dans les deux fichiers (PILE, ZOOM, ZOOM_IN, carrousel, décalage du final) ;
  2. les repères musicaux (MARKS) par rapport aux sections de l'image ;
  3. que chaque événement visuel annoncé par collage.py a bien un bruitage à proximité (il instrumente add()).

Exemple (depuis la racine) :
    python3 .claude/skills/motion-storyboard/scripts/timeline_check.py
    python3 .claude/skills/motion-storyboard/scripts/timeline_check.py --window 0.15 --verbose
Code de sortie : 0 si tout est cohérent, 1 sinon.
"""
import argparse, inspect, os, sys
import numpy as np

OK, KO, NB = "✔", "✗", "·"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--motion-dir", default="motion")
    ap.add_argument("--before", type=float, default=0.2, help="un bruitage peut précéder l'événement de cette durée (s)")
    ap.add_argument("--after", type=float, default=0.4, help="... ou le suivre de cette durée (s)")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    md = os.path.abspath(a.motion_dir)
    sys.path.insert(0, md)
    os.chdir(md)
    import collage as C
    import audio_collage as AC

    bad = 0

    def line(ok, msg):
        nonlocal bad
        bad += 0 if ok else 1
        print("  %s %s" % (OK if ok else KO, msg))

    print("1. CONSTANTES COMMUNES (image ↔ son)")
    pile_img = [(ta, kind) for ta, _i, kind in C.PILE[1:]]
    line(pile_img == [tuple(x) for x in AC.PILE], "PILE : %s" % ("identique" if pile_img == [tuple(x) for x in AC.PILE]
         else "image %s ≠ son %s" % (pile_img, AC.PILE)))
    zimg = [s[0] for s in C.ZOOM]
    line(zimg == list(AC.ZOOM), "ZOOM (débuts) : %s" % ("identiques" if zimg == list(AC.ZOOM) else "image %s ≠ son %s" % (zimg, AC.ZOOM)))
    durs = {s[1] for s in C.ZOOM}
    line(durs == {2.0}, "ZOOM durée par plan : %s s (audio_collage suppose 2,0 s en dur)" % sorted(durs))
    line(abs(C.ZOOM_IN - AC.ZOOM_IN) < 1e-9, "ZOOM_IN : image %.2f / son %.2f" % (C.ZOOM_IN, AC.ZOOM_IN))
    line((C.C0, C.CSTEP, C.CEND) == (AC.CAR0, AC.CSTEP, AC.CEND), "carrousel (début, pas, fin) : image %s / son %s" % (
        (C.C0, C.CSTEP, C.CEND), (AC.CAR0, AC.CSTEP, AC.CEND)))
    line(C.FIN_SHIFT == AC.FIN, "décalage du final : image %g / son %g" % (C.FIN_SHIFT, AC.FIN))
    line(abs(C.DURATION - AC.A.DUR) < 1e-9, "durée du film : image %g s / son %g s" % (C.DURATION, AC.A.DUR))

    print("\n2. REPÈRES MUSICAUX (MARKS) ↔ SECTIONS DE L'IMAGE")
    M = AC.MARKS
    boom = C.WOW[0][0] + C.WOW_SHIFT
    line(abs(M["cut"] - boom) < 1e-9, "silence : MARKS.cut %.2f = début de la mosaïque %.2f" % (M["cut"], boom))
    line(abs(M["back"] - (boom + 0.5)) < 1e-9, "BOOM : MARKS.back %.2f = silence + 0,5 s (%.2f)" % (M["back"], boom + 0.5))
    line(abs(M["drop"] - C.BENTO[0][0]) < 1e-9, "drop : MARKS.drop %.2f = début du bento %.2f" % (M["drop"], C.BENTO[0][0]))
    line(abs(M["end"] - C.CEND) < 1e-9, "fin : MARKS.end %.2f = fin du carrousel %.2f" % (M["end"], C.CEND))
    line(abs(M["start"] - C.PILE[1][0]) < 1e-9, "départ : MARKS.start %.2f = 1re entrée de la pile %.2f" % (M["start"], C.PILE[1][0]))
    for name in ("build", "roll", "restart", "hats2", "climax"):
        print("  %s MARKS.%s = %.2f s : repère purement musical, rien à comparer à l'image (à vérifier à l'oreille)" % (NB, name, M[name]))
    onbeat = [(k, v) for k, v in M.items() if abs(v / 0.5 - round(v / 0.5)) > 1e-6]
    line(not onbeat, "repères musicaux sur la grille de croches (0,25 s) : %s" % (", ".join("%s=%.3f" % kv for kv in onbeat) or "tous"))

    print("\n3. BRUITAGES PRÉSENTS AUTOUR DE CHAQUE ÉVÉNEMENT VISUEL (fenêtre -%.2f / +%.2f s)" % (a.before, a.after))
    cues, real_add = [], AC.add

    def spy(bus, x, t0, gain=1.0, pan=0.0):
        env = np.abs(x if x.ndim == 1 else x.max(1))
        att = int(np.argmax(env >= 0.1 * (env.max() + 1e-12)))
        fr = inspect.stack()[1]
        cues.append((t0 + att / AC.SR, fr.lineno, (fr.code_context or ["?"])[0].strip()))
        return real_add(bus, x, t0, gain, pan)

    AC.add = spy
    AC.sfx()
    times = sorted(c[0] for c in cues)
    events = []
    for k, (ta, _i, kind) in enumerate(C.PILE):
        if k:
            events.append(("pile %d (%s)" % (k, kind), ta))
    for k, (st, du, _i, _d) in enumerate(C.ZOOM):
        events.append(("zoom %d : pose" % (k + 1), st))
        events.append(("zoom %d : plongée" % (k + 1), st + du - C.ZOOM_IN))
    events.append(("BOOM mosaïque", boom + 0.5))
    for k, (tb, _l, _c) in enumerate(C.BENTO):
        events.append(("bento %d" % (k + 1), tb))
    for k in range(1, int((C.CEND - C.C0) / C.CSTEP)):
        events.append(("carrousel cran %d" % k, C.C0 + k * C.CSTEP))
    events.append(("BOOM final (fleur)", C.FIN_SHIFT + 38.0))
    miss = []
    for name, t in events:
        near = [x for x in times if t - a.before <= x <= t + a.after]
        if not near:
            miss.append((name, t))
        elif a.verbose:
            print("  %s %-22s %6.2f s : %d son(s), le plus proche à %+.0f ms" % (
                OK, name, t, len(near), 1000 * min((x - t for x in near), key=abs)))
    line(not miss, "%d événements, %d sans bruitage%s" % (len(events), len(miss), "" if not miss else " : " + ", ".join(
        "%s (%.2f s)" % m for m in miss)))
    quiet = [(round(x, 2)) for x in times if not any(abs(x - t) <= 1.0 for _n, t in events)]
    print("  %s %d bruitages sans événement visuel annoncé à ±1 s (ex. : %s) — normal pour l'intro, les risers et les accents" % (
        NB, len(quiet), ", ".join("%.2f" % q for q in quiet[:8])))

    print("\n%s" % ("TIMELINE COHÉRENTE" if not bad else "%d INCOHÉRENCE(S) : corriger du côté qui n'a pas été mis à jour" % bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
