#!/usr/bin/env python3
"""Contrôle de livraison d'une vidéo verticale (TikTok, Reels, Shorts) et correction du loudness.

Vérifie : résolution et ratio, i/s, codec, pixel format, faststart, durée, débit, audio (codec,
fréquence, canaux), loudness intégrée, crête vraie, LRA, première image non vide (accroche) et
fin non coupée. Avec --fix, normalise le son en deux passes (loudnorm linéaire) sans réencoder l'image.

Exemples :
    python3 check_delivery.py output/film.mp4                      # profil "social" (TikTok/Reels/Shorts)
    python3 check_delivery.py output/film.mp4 --profile tiktok
    python3 check_delivery.py output/film.mp4 --fix output/film_-14LUFS.mp4 --lufs -14 --tp -1.5
"""
import argparse, json, os, re, subprocess, sys
import numpy as np

PROFILES = {
    # max_dur : durées maximales de publication courantes (à revérifier : elles changent souvent)
    "social": dict(w=1080, h=1920, fps=(24, 60), max_dur=180, lufs=-14.0, lufs_tol=1.5, tp=-1.0),
    "tiktok": dict(w=1080, h=1920, fps=(24, 60), max_dur=600, lufs=-14.0, lufs_tol=1.5, tp=-1.0),
    "reels": dict(w=1080, h=1920, fps=(24, 60), max_dur=180, lufs=-14.0, lufs_tol=1.5, tp=-1.0),
    "shorts": dict(w=1080, h=1920, fps=(24, 60), max_dur=180, lufs=-14.0, lufs_tol=1.5, tp=-1.0),
}


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path]).stdout
    return json.loads(out)


def loudness(path):
    err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    summ = err[err.rfind("Summary:"):]
    get = lambda key: float(re.search(key + r":\s+(-?[\d.]+|-inf)", summ).group(1).replace("-inf", "-99"))  # noqa: E731
    return dict(I=get("I"), LRA=get("LRA"), TP=get("Peak"))


def faststart(path):
    """True si l'atome moov précède mdat (lecture web immédiate)."""
    with open(path, "rb") as f:
        pos, size = 0, os.path.getsize(path)
        while pos < size:
            f.seek(pos)
            hdr = f.read(16)
            if len(hdr) < 8:
                break
            n = int.from_bytes(hdr[:4], "big")
            kind = hdr[4:8].decode("latin-1")
            if n == 1:
                n = int.from_bytes(hdr[8:16], "big")
            if kind == "moov":
                return True
            if kind == "mdat":
                return False
            if n <= 0:
                break
            pos += n
    return None


def frame_stats(path, t):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "%.3f" % t, "-i", path, "-frames:v", "1", "-vf",
                          "scale=108:192", "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.uint8).astype(float)
    return (a.mean(), a.std()) if a.size else (0, 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--profile", default="social", choices=sorted(PROFILES))
    ap.add_argument("--fix", default=None, help="écrit une copie au loudness cible (image copiée telle quelle)")
    ap.add_argument("--lufs", type=float, default=None)
    ap.add_argument("--tp", type=float, default=-1.5, help="plafond de crête vraie visé par --fix (marge pour l'AAC)")
    a = ap.parse_args()
    P = PROFILES[a.profile]
    lufs_target = a.lufs if a.lufs is not None else P["lufs"]

    j = probe(a.video)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    dur = float(j["format"]["duration"])
    res = []

    def check(ok, label, detail, level="ERREUR"):
        res.append(("OK" if ok else level, label, detail))

    num, den = v["r_frame_rate"].split("/")
    fps = float(num) / float(den)
    check(v["width"] == P["w"] and v["height"] == P["h"], "résolution", "%dx%d (attendu %dx%d)" % (v["width"], v["height"], P["w"], P["h"]))
    check(P["fps"][0] <= fps <= P["fps"][1], "cadence", "%.3f i/s" % fps)
    check(v["codec_name"] in ("h264", "hevc"), "codec vidéo", v["codec_name"])
    check(v.get("pix_fmt") == "yuv420p", "pixel format", v.get("pix_fmt", "?") + " (yuv420p = compatible partout)")
    fs = faststart(a.video)
    check(fs is not False, "faststart", "moov en tête" if fs else "moov en fin : ajouter -movflags +faststart", "ATTENTION")
    check(dur <= P["max_dur"], "durée", "%.2f s (max %d s pour ce profil)" % (dur, P["max_dur"]))
    br = float(j["format"].get("bit_rate", 0)) / 1e6
    check(4 <= br <= 25, "débit", "%.1f Mbit/s (4–25 conseillé ; la plateforme réencode de toute façon)" % br,
          "ATTENTION")
    size = os.path.getsize(a.video) / 1e6
    check(size <= 287, "taille", "%.0f Mo" % size, "ATTENTION")
    if au is None:
        check(False, "audio", "aucune piste audio (le son est indispensable sur ces plateformes)", "ATTENTION")
    else:
        check(au["codec_name"] == "aac", "codec audio", au["codec_name"])
        check(int(au["sample_rate"]) in (44100, 48000), "fréquence", au["sample_rate"] + " Hz")
        check(int(au.get("channels", 0)) == 2, "canaux", str(au.get("channels")), "ATTENTION")
        L = loudness(a.video)
        check(abs(L["I"] - lufs_target) <= P["lufs_tol"], "loudness",
              "%.1f LUFS intégrés (cible %.0f ±%.1f)" % (L["I"], lufs_target, P["lufs_tol"]), "ATTENTION")
        check(L["TP"] <= P["tp"], "crête vraie", "%.1f dBTP (max %.1f)" % (L["TP"], P["tp"]), "ATTENTION")
        check(L["LRA"] <= 11, "plage dynamique", "LRA %.1f LU (≤ 11 pour mobile)" % L["LRA"], "ATTENTION")
    m0, s0 = frame_stats(a.video, 0)
    check(s0 > 8 and 12 < m0 < 245, "1re image", "moyenne %.0f, contraste %.0f : %s" % (
        m0, s0, "elle accroche" if s0 > 8 else "image vide / unie : l'accroche des 1res secondes est perdue"), "ATTENTION")
    m1, s1 = frame_stats(a.video, max(dur - 0.05, 0))
    check(m1 > 12 or s1 > 8, "dernière image", "moyenne %.0f, contraste %.0f" % (m1, s1), "ATTENTION")

    print("== %s · profil %s" % (os.path.basename(a.video), a.profile))
    for lvl, label, detail in res:
        print("  %-9s %-17s %s" % (lvl, label, detail))
    bad = [r for r in res if r[0] == "ERREUR"]
    warn = [r for r in res if r[0] == "ATTENTION"]
    print("\n%d erreur(s), %d point(s) d'attention." % (len(bad), len(warn)))

    if a.fix:
        if au is None:
            sys.exit("pas d'audio à corriger")
        # l'encodage AAC fait remonter la crête : on abaisse le plafond jusqu'à passer sous -1 dBTP
        tp = a.tp
        for attempt in range(4):
            print("\nnormalisation en deux passes vers %.1f LUFS / plafond %.1f dBTP…" % (lufs_target, tp))
            f1 = "loudnorm=I=%g:TP=%g:LRA=11:print_format=json" % (lufs_target, tp)
            err = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vn", "-af", f1, "-f", "null", "-"]).stderr
            m = json.loads(err[err.rfind("{"):err.rfind("}") + 1])
            f2 = ("loudnorm=I=%g:TP=%g:LRA=11:measured_I=%s:measured_TP=%s:measured_LRA=%s:measured_thresh=%s:"
                  "offset=%s:linear=true" % (lufs_target, tp, m["input_i"], m["input_tp"], m["input_lra"],
                                             m["input_thresh"], m["target_offset"]))
            r = run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-map", "0:v", "-map", "0:a", "-c:v", "copy",
                     "-af", f2, "-ar", "48000", "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", a.fix])
            if r.returncode:
                sys.exit(r.stderr)
            L2 = loudness(a.fix)
            print("-> %s : %.1f LUFS, crête vraie %.1f dBTP, LRA %.1f" % (a.fix, L2["I"], L2["TP"], L2["LRA"]))
            if L2["TP"] <= -1.0:
                break
            tp -= 0.75
        else:
            print("   crête toujours au-dessus de -1 dBTP : baisser la cible --lufs ou limiter le mix à la source")


if __name__ == "__main__":
    main()
