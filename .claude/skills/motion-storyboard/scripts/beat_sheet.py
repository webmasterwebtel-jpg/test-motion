#!/usr/bin/env python3
"""Du brief à la timeline : convertit un découpage en mesures en temps, images et repères de code, et contrôle le rythme.

Entrée : un JSON {bpm, fps, beats_per_bar, target_s?, sequences:[{name, bars, looks?, type?, energy?, note?}]}.
  - bars   : durée en mesures (fractions permises : 3.5)
  - looks  : nombre de visuels présentés dans la séquence (pour la durée de tenue par look)
  - type   : hold (présentation posée), burst (enchaînement rapide, climax), intro, outro, break
  - energy : 1 (calme) à 5 (climax), pour contrôler l'arc d'énergie

Vérifie les préférences du projet (voir motion-direction) : une tenue de look d'au moins ~1,3 s (idéal 2 s) hors burst,
un burst de 4 s maximum, un arc d'énergie qui monte puis redescend, une durée totale conforme à la cible.

Exemples :
    python3 beat_sheet.py --example > build/brief.json          # le film actuel, comme point de départ
    python3 beat_sheet.py build/brief.json
    python3 beat_sheet.py build/brief.json --code               # extraits à coller dans collage.py / audio_collage.py
    python3 beat_sheet.py build/brief.json --plot build/review/timeline.png
"""
import argparse, json, os, sys

EXAMPLE = {
    "bpm": 120, "fps": 30, "beats_per_bar": 4, "target_s": 60,
    "sequences": [
        {"name": "intro", "bars": 2, "looks": 1, "type": "intro", "energy": 2, "note": "pelote, carrés tamponnés, révélation du 1er look"},
        {"name": "pile", "bars": 6, "looks": 6, "type": "hold", "energy": 3, "note": "stickers plaqués, 1 look par mesure"},
        {"name": "zoom", "bars": 6, "looks": 6, "type": "hold", "energy": 3, "note": "pose puis plongée dans les mailles, iris"},
        {"name": "mosaique", "bars": 1.875, "looks": 2, "type": "burst", "energy": 5, "note": "silence 0,5 s, BOOM, 60 carreaux qui se retournent"},
        {"name": "echo", "bars": 1.625, "looks": 1, "type": "hold", "energy": 4, "note": "look en échos riso, fils en orbite, pulsation sur le beat"},
        {"name": "bento", "bars": 2, "looks": 6, "type": "burst", "energy": 4, "note": "grilles qui se réorganisent"},
        {"name": "carrousel", "bars": 8, "looks": 8, "type": "hold", "energy": 4, "note": "cover-flow 3D, 1 tenue par mesure"},
        {"name": "final", "bars": 2.5, "looks": 0, "type": "outro", "energy": 3, "note": "aspiration en pelote, fleur"},
    ],
}

MIN_HOLD, IDEAL_HOLD, MAX_BURST = 1.3, 2.0, 4.0


def load(path):
    with open(path) as fh:
        return json.load(fh)


def plan(brief):
    bpm, fps, bpb = brief["bpm"], brief.get("fps", 30), brief.get("beats_per_bar", 4)
    beat = 60.0 / bpm
    bar = beat * bpb
    t, rows = 0.0, []
    for s in brief["sequences"]:
        dur = s["bars"] * bar
        rows.append(dict(s, start=t, end=t + dur, dur=dur, start_f=round(t * fps), end_f=round((t + dur) * fps),
                         start_bar=t / bar + 1, per_look=(dur / s["looks"]) if s.get("looks") else None))
        t += dur
    return dict(beat=beat, bar=bar, fps=fps, bpb=bpb, total=t, rows=rows)


def check(brief, p):
    msgs = []
    tgt = brief.get("target_s")
    if tgt and abs(p["total"] - tgt) > 0.05:
        msgs.append(("!", "durée totale %.2f s ≠ cible %.2f s (%+.1f mesures)" % (p["total"], tgt, (tgt - p["total"]) / p["bar"])))
    for r in p["rows"]:
        kind = r.get("type", "hold")
        if r["per_look"] is not None:
            if kind in ("hold", "intro", "outro") and r["per_look"] < MIN_HOLD:
                msgs.append(("!", "%s : %.2f s par look (< %.1f s) — trop rapide pour lire le produit" % (r["name"], r["per_look"], MIN_HOLD)))
            elif kind == "hold" and r["per_look"] < IDEAL_HOLD - 0.01:
                msgs.append(("~", "%s : %.2f s par look (idéal du projet : %.0f s)" % (r["name"], r["per_look"], IDEAL_HOLD)))
        if kind == "burst" and r["dur"] > MAX_BURST + 0.01:
            msgs.append(("!", "%s : burst de %.1f s (> %.0f s) — fatigue, ajouter une respiration" % (r["name"], r["dur"], MAX_BURST)))
        frac = (r["start"] / p["beat"]) % 1
        if min(frac, 1 - frac) > 1e-6:
            half = abs(frac - 0.5) < 1e-6
            msgs.append(("~" if half else "!", "%s démarre %s (%.3f temps)" % (
                r["name"], "sur une croche (demi-temps) : correct si voulu" if half else "entre les croches : hors grille",
                r["start"] / p["beat"])))
        if abs(r["start_f"] / p["fps"] - r["start"]) > 0.5 / p["fps"] + 1e-9:
            msgs.append(("~", "%s : début arrondi à l'image (%.3f → %.3f s)" % (r["name"], r["start"], r["start_f"] / p["fps"])))
    e = [r["energy"] for r in p["rows"] if "energy" in r]
    if len(e) >= 4:
        if len(set(e)) == 1:
            msgs.append(("!", "énergie plate (%d partout) : pas d'arc, le film paraîtra monotone" % e[0]))
        else:
            peak = e.index(max(e))
            if peak == 0 or peak == len(e) - 1:
                msgs.append(("~", "le pic d'énergie est à une extrémité : prévoir une montée, un sommet, puis une résolution"))
        for i in range(len(e) - 2):
            if e[i] >= 4 and e[i + 1] >= 4 and e[i + 2] >= 4:
                msgs.append(("~", "3 séquences d'énergie ≥ 4 de suite (%s…) : prévoir une respiration" % p["rows"][i]["name"]))
                break
    first = p["rows"][0]
    msgs.append(("i", "accroche : la 1re séquence (%s) doit montrer quelque chose dès l'image 0 (pas de papier vide)" % first["name"]))
    return msgs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief", nargs="?")
    ap.add_argument("--example", action="store_true", help="imprime le brief du film actuel")
    ap.add_argument("--code", action="store_true", help="extraits de code (SECTIONS, MARKS)")
    ap.add_argument("--plot", default=None, help="PNG de la timeline")
    a = ap.parse_args()
    if a.example:
        print(json.dumps(EXAMPLE, indent=1, ensure_ascii=False))
        return
    if not a.brief:
        ap.error("fichier de brief requis (ou --example)")
    brief = load(a.brief)
    p = plan(brief)
    print("%g BPM · %d i/s · 1 temps = %.3f s (%g images) · 1 mesure = %.3f s (%g images) · total %.2f s = %.2f mesures\n" % (
        brief["bpm"], p["fps"], p["beat"], p["beat"] * p["fps"], p["bar"], p["bar"] * p["fps"], p["total"], p["total"] / p["bar"]))
    print("%-12s %-6s %8s %8s %8s %8s %9s %9s  %s" % ("séquence", "type", "début s", "fin s", "durée", "mesures", "images", "par look", "énergie"))
    for r in p["rows"]:
        print("%-12s %-6s %8.2f %8.2f %7.2fs %8g %4d-%-4d %9s  %s" % (
            r["name"], r.get("type", "hold"), r["start"], r["end"], r["dur"], r["bars"], r["start_f"], r["end_f"],
            ("%.2f s" % r["per_look"]) if r["per_look"] else "-", "█" * r.get("energy", 0)))
    msgs = check(brief, p)
    print("\nCONTRÔLES")
    for lvl, m in msgs:
        print("  %s %s" % ({"!": "✗", "~": "△", "i": "·"}[lvl], m))
    if not any(l == "!" for l, _ in msgs):
        print("  aucun blocage")
    if a.code:
        print("\n# --- collage.py : début de chaque séquence (s) ---")
        print("SECTIONS_T = {%s}" % ", ".join("%r: (%.3f, %.3f)" % (r["name"], r["start"], r["end"]) for r in p["rows"]))
        print("# --- audio_collage.py : repères (s) ---")
        print("SECTIONS_T = %s   # même contenu : à coller IDENTIQUE dans les deux fichiers (voir timeline_check.py)" % "{...}")
    if a.plot:
        from PIL import Image, ImageDraw, ImageFont
        W, H, left = 1400, 200, 20
        img = Image.new("RGB", (W, H), (250, 250, 248))
        d = ImageDraw.Draw(img)
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except OSError:
            f = ImageFont.load_default()
        k = (W - 2 * left) / p["total"]
        pal = {"hold": (170, 205, 245), "burst": (245, 170, 150), "intro": (200, 230, 190), "outro": (200, 230, 190), "break": (230, 230, 230)}
        for b in range(int(p["total"] / p["bar"]) + 1):
            x = left + b * p["bar"] * k
            d.line([x, 30, x, 150], fill=(215, 215, 215))
        for r in p["rows"]:
            x0, x1 = left + r["start"] * k, left + r["end"] * k
            h = 40 + 14 * r.get("energy", 2)
            d.rectangle([x0, 150 - h, x1 - 2, 150], fill=pal.get(r.get("type", "hold"), (200, 200, 200)))
            d.text((x0 + 4, 154), r["name"], fill=(40, 40, 40), font=f)
            d.text((x0 + 4, 168), "%.1f–%.1f s" % (r["start"], r["end"]), fill=(110, 110, 110), font=f)
        d.text((left, 8), "timeline : une colonne = une mesure ; hauteur = énergie ; bleu hold, rouge burst, vert intro/outro", fill=(40, 40, 40), font=f)
        os.makedirs(os.path.dirname(a.plot) or ".", exist_ok=True)
        img.save(a.plot)
        print("\n->", a.plot)
    sys.exit(1 if any(l == "!" for l, _ in msgs) else 0)


if __name__ == "__main__":
    main()
