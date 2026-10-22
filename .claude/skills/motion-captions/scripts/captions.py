#!/usr/bin/env python3
"""Sous-titres et texte incrusté : cues -> SRT + ASS stylé dans la zone sûre, contrôles de lisibilité, incrustation ffmpeg.

Le film actuel est volontairement sans texte (préférence du projet, voir motion-direction). Cet outil sert aux variantes où
du texte est demandé : accroches, sous-titres d'une voix off, légendes.

Format des cues (JSON) : [{"start": 4.0, "end": 6.0, "text": "Un look par mesure"}, ...]  (secondes ; `\\n` pour forcer un retour)

Sous-commandes :
  build  cues.json  -> écrit .srt et .ass (retours à la ligne automatiques dans la largeur sûre) et contrôle :
                       durée minimale, vitesse de lecture, nombre de lignes, chevauchements, sortie du cadre
  burn   video.mp4 sous.ass -> incruste (image réencodée, son copié)

Exemples :
    python3 captions.py build cues.json --out build/captions/demo --size 64
    python3 captions.py burn output/film.mp4 build/captions/demo.ass --out build/captions/film_sub.mp4 --start 0 --end 10
"""
import argparse, json, os, subprocess, sys

ZONE = dict(left=120, right=192, bottom=672, top=288)    # union TikTok / Reels / Shorts (voir motion-delivery)
CPS_MAX = 17.0                                            # caractères/s : repère courant pour des sous-titres, pas une norme
MIN_DUR = 1.0


def ts_srt(t):
    ms = int(round(t * 1000))
    return "%02d:%02d:%02d,%03d" % (ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000)


def ts_ass(t):
    cs = int(round(t * 100))
    return "%d:%02d:%02d.%02d" % (cs // 360000, cs // 6000 % 60, cs // 100 % 60, cs % 100)


def ass_color(hexa):
    h = hexa.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return "&H00%s%s%s" % (b.upper(), g.upper(), r.upper())      # ASS : AABBGGRR


def font_for(path, size):
    from PIL import ImageFont
    return ImageFont.truetype(path, size)


def ass_font_name(path):
    """Nom que libass sait faire correspondre : le nom complet du fichier (famille + style), pas un nom deviné.
    Les polices du projet déclarent par exemple la famille « Montserrat Thin » pour tous les poids : le gras s'appelle donc
    « Montserrat Thin Black ». Un nom inexact ne produit aucune erreur, libass retombe silencieusement sur une autre police."""
    fam, style = font_for(path, 20).getname()
    return fam if style in ("Regular", "Normal") else "%s %s" % (fam, style)


def libass_ratio(font_file, font_name, size, fonts_dir):
    """Rapport (largeur rendue par libass) / (largeur mesurée par PIL à la même taille nominale).
    libass n'interprète pas « Fontsize » comme PIL (il se base sur la hauteur de cellule de la police) : sans ce facteur,
    les retours à la ligne et les contrôles de largeur sont faux. On le mesure en rendant une ligne de test."""
    import tempfile
    import numpy as np
    sample = "Hamburgefonstivxyz"
    with tempfile.TemporaryDirectory() as d:
        ass = os.path.join(d, "t.ass")
        with open(ass, "w") as f:
            f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\n"
                    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
                    "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
                    "MarginR, MarginV, Encoding\nStyle: T,%s,%d,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1\n\n"
                    "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
                    "Dialogue: 0,0:00:00.00,0:00:02.00,T,,0,0,0,,%s\n" % (font_name, size, sample))
        vf = "ass=%s:fontsdir=%s" % (ass.replace(":", "\\:"), os.path.abspath(fonts_dir).replace(":", "\\:"))
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1", "-vf", vf,
                            "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True)
    if r.returncode or not r.stdout:
        return None
    img = np.frombuffer(r.stdout, np.uint8).reshape(1920, 1080)
    cols = np.nonzero((img > 128).any(axis=0))[0]
    if not len(cols):
        return None
    return (cols[-1] - cols[0] + 1) / font_for(font_file, size).getlength(sample)


def wrap(text, font, max_w):
    out = []
    for para in text.split("\\n"):
        line = ""
        for word in para.split():
            trial = (line + " " + word).strip()
            if font.getlength(trial) <= max_w or not line:
                line = trial
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def build(a):
    with open(a.cues) as fh:
        cues = json.load(fh)
    avail = 1080 - ZONE["left"] - ZONE["right"]
    a.font_name = a.font_name or ass_font_name(a.font_file)
    ratio = libass_ratio(a.font_file, a.font_name, a.size, os.path.dirname(a.font_file) or ".")
    if ratio is None:
        print("  ! impossible de mesurer le rendu libass : largeurs estimées avec PIL (peut couper trop tôt ou trop tard)")
        ratio = 1.0
    font = font_for(a.font_file, max(int(round(a.size * ratio)), 8))      # PIL à la taille *réellement rendue*
    avail -= 2 * a.outline
    issues, rows = [], []
    prev_end = -1
    for i, c in enumerate(cues, 1):
        lines = wrap(c["text"], font, avail)
        width = max(font.getlength(l) for l in lines)
        dur = c["end"] - c["start"]
        words = len(c["text"].split())
        cps = len(c["text"].replace("\\n", " ")) / max(dur, 1e-6)
        if dur < MIN_DUR:
            issues.append("cue %d : %.2f s (< %.1f s) — trop courte pour être lue" % (i, dur, MIN_DUR))
        need = 0.5 + 0.3 * words
        if dur < need - 1e-9:
            issues.append("cue %d : %.2f s pour %d mot(s), il en faut ≥ %.1f s (0,5 s + 0,3 s par mot)" % (i, dur, words, need))
        if cps > CPS_MAX:
            issues.append("cue %d : %.0f caractères/s (> %.0f) — trop rapide" % (i, cps, CPS_MAX))
        if len(lines) > 2:
            issues.append("cue %d : %d lignes (> 2) — raccourcir le texte ou baisser --size" % (i, len(lines)))
        if width > avail + 1:
            issues.append("cue %d : un mot dépasse la largeur sûre (%.0f > %d px) — baisser --size" % (i, width, avail))
        if c["start"] < prev_end - 1e-9:
            issues.append("cue %d : chevauche la précédente (%.2f < %.2f)" % (i, c["start"], prev_end))
        prev_end = max(prev_end, c["end"])
        rows.append((c, lines))
    block_h = max(len(l) for _, l in rows) * a.size * ratio * 1.25
    bottom_y = 1920 - a.margin_v
    if bottom_y > 1920 - ZONE["bottom"]:
        issues.append("--margin-v %d : le texte descend dans la zone masquée par l'interface (bas ≥ y %d)" % (a.margin_v, 1920 - ZONE["bottom"]))
    if bottom_y - block_h < ZONE["top"]:
        issues.append("le bloc de texte monte dans la zone du haut (< y %d)" % ZONE["top"])

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out + ".srt", "w") as f:
        for i, (c, lines) in enumerate(rows, 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, ts_srt(c["start"]), ts_srt(c["end"]), "\n".join(lines)))
    anim = "{\\fad(90,90)\\fscx85\\fscy85\\t(0,160,\\fscx100\\fscy100)}" if a.anim == "pop" else "{\\fad(90,90)}"
    with open(a.out + ".ass", "w") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n")
        f.write("[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
                "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write("Style: Cap,%s,%d,%s,&H000000FF,%s,&H80000000,0,0,0,0,100,100,0,0,1,%g,2,2,%d,%d,%d,1\n\n" % (
            a.font_name, a.size, ass_color(a.color), ass_color(a.outline_color), a.outline, ZONE["left"], ZONE["right"], a.margin_v))
        f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for c, lines in rows:
            f.write("Dialogue: 0,%s,%s,Cap,,0,0,0,,%s%s\n" % (ts_ass(c["start"]), ts_ass(c["end"]), anim, "\\N".join(lines)))
    print("%d cue(s) -> %s.srt, %s.ass (largeur sûre %d px, police « %s » taille %d, échelle libass x%.2f)" % (
        len(rows), a.out, a.out, avail, a.font_name, a.size, ratio))
    for m in issues:
        print("  ✗ " + m)
    if not issues:
        print("  ✔ durées, vitesse de lecture, lignes et zone sûre : aucun problème")
    sys.exit(1 if issues else 0)


def burn(a):
    fontsdir = os.path.abspath(a.fonts_dir)
    vf = "ass=%s:fontsdir=%s" % (a.ass.replace("\\", "/").replace(":", "\\:"), fontsdir.replace(":", "\\:"))
    # -ss APRÈS -i (côté sortie) : le filtre voit les horodatages d'origine, donc les cues gardent leur temps d'origine.
    # Avec -ss avant -i, les horodatages repartent de 0 et tous les sous-titres arriveraient trop tard.
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", a.video, "-vf", vf]
    if a.start:
        cmd += ["-ss", str(a.start)]
    if a.end:
        cmd += ["-t", str(a.end - (a.start or 0))]
    cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "copy",
            "-movflags", "+faststart", a.out]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr)
    print("->", a.out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("cues")
    b.add_argument("--out", default=os.path.join("build", "captions", "captions"))
    b.add_argument("--size", type=int, default=88, help="taille ASS (le rendu est ~0,65x plus petit que la même taille en PIL/CSS)")
    b.add_argument("--font-name", default=None, help="défaut : déduit de --font-file (voir ass_font_name)")
    b.add_argument("--font-file", default=os.path.join("assets", "fonts", "Montserrat-Black.ttf"))
    b.add_argument("--color", default="#FFFFFF")
    b.add_argument("--outline-color", default="#111111")
    b.add_argument("--outline", type=float, default=6)
    b.add_argument("--margin-v", type=int, default=700, help="distance du bas (px) ; 700 = juste au-dessus de la zone d'interface (672)")
    b.add_argument("--anim", choices=["pop", "fade"], default="pop")
    u = sub.add_parser("burn")
    u.add_argument("video")
    u.add_argument("ass")
    u.add_argument("--out", required=True)
    u.add_argument("--fonts-dir", default=os.path.join("assets", "fonts"))
    u.add_argument("--start", type=float, default=0)
    u.add_argument("--end", type=float, default=0)
    a = ap.parse_args()
    build(a) if a.cmd == "build" else burn(a)


if __name__ == "__main__":
    main()
