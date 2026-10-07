#!/usr/bin/env python3
"""Relevé des bruitages depuis le CODE (motion/audio_collage.py) et comparaison aux événements visuels.

On exécute sfx() en espionnant chaque appel à add(bus, son, t0, gain, pan) : pour chaque son on connaît
la ligne de code, l'instant de départ, l'attaque réelle (10 % du max) et le pic. Contrairement à une
analyse du mixage, rien n'est masqué par la musique.

Avec --events (JSON produit par motion-review/motion_graph.py), chaque bruitage est rapproché de
l'événement visuel le plus proche (départ / pic / contact) et l'écart est donné en images.

Exemples (depuis la racine) :
    python3 .claude/skills/motion-audio-sync/scripts/cue_check.py
    python3 .claude/skills/motion-audio-sync/scripts/cue_check.py --events build/review/motion_00.00_60.00.json --from 4 --to 16
"""
import argparse, inspect, json, os, sys
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--module", default="audio_collage")
    ap.add_argument("--motion-dir", default="motion")
    ap.add_argument("--events", default=None, help="JSON de motion_graph.py")
    ap.add_argument("--from", dest="t_from", type=float, default=0)
    ap.add_argument("--to", dest="t_to", type=float, default=1e9)
    ap.add_argument("--min-gain", type=float, default=0.0, help="ignorer les sons plus faibles")
    ap.add_argument("--fps", type=float, default=30)
    a = ap.parse_args()

    sys.path.insert(0, os.path.abspath(a.motion_dir))
    cwd = os.getcwd()
    os.chdir(os.path.abspath(a.motion_dir))          # le module peut écrire relativement à motion/
    mod = __import__(a.module)
    SR = mod.SR
    cues = []
    real_add = mod.add

    def spy(bus, x, t0, gain=1.0, pan=0.0):
        fr = inspect.stack()[1]
        line = (fr.code_context or ["?"])[0].strip()
        env = np.abs(x if x.ndim == 1 else x.max(1))
        mx = float(env.max()) + 1e-12
        att = int(np.argmax(env >= 0.1 * mx))
        pk = int(np.argmax(env))
        level = 20 * np.log10(mx * gain + 1e-9)
        cues.append(dict(t0=t0, attack=t0 + att / SR, peak=t0 + pk / SR, gain=gain, level_db=level,
                         line=fr.lineno, code=line))
        return real_add(bus, x, t0, gain, pan)

    mod.add = spy
    mod.sfx()
    os.chdir(cwd)
    cues = [c for c in cues if a.t_from <= c["attack"] <= a.t_to and c["gain"] >= a.min_gain]
    cues.sort(key=lambda c: c["attack"])

    events = []
    if a.events:
        with open(a.events) as fh:
            events = json.load(fh).get("events", [])
    print("%-8s %-8s %-7s %-6s  %-44s %s" % ("attaque", "pic", "crête", "ligne", "code",
                                              "événement visuel le plus proche" if events else ""))
    for c in cues:
        near = ""
        if events:
            best = None
            for e in events:
                for k in ("start", "peak", "contact"):
                    d = (c["attack"] - e[k]) * a.fps
                    if best is None or abs(d) < abs(best[0]):
                        best = (d, k, e)
            d, k, e = best
            if abs(d) <= 8:
                flag = "ok" if abs(d) <= 1 else "!!"
                near = "%s %s %.2fs (%+.1f img)" % (flag, {"start": "départ", "peak": "pic", "contact": "contact"}[k],
                                                    e[k], d)
            else:
                near = "—  aucun événement à ±8 images"
        code = c["code"] if len(c["code"]) <= 44 else c["code"][:41] + "..."
        print("%7.3f  %7.3f  %5.1fdB  %5d  %-44s %s" % (c["attack"], c["peak"], c["level_db"], c["line"], code, near))
    print("\n%d bruitages. Attaque = premier passage à 10 %% du max (ce que l'oreille perçoit comme départ)." % len(cues))


if __name__ == "__main__":
    main()
