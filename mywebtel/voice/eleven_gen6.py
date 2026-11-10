#!/usr/bin/env python3
"""Voix off V6 : voix « Simon » d'ElevenLabs, modèle eleven_v4, plusieurs prises par phrase.

voice/script_v6.json : [id, texte affiché, texte envoyé]. Le texte envoyé force la prononciation française :
« scanné » (scanner), « plu » (t'as plus qu'à), et supprime les liaisons fautives que le modèle faisait
(« tu arrive : un clic », « tu la déclare avec », « tu signe avec », « tu la pose à », « s'ouvre après », « t'a une »),
sans changer le son voulu. Chaque prise est ensuite notée par voice_check.py (deux transcriptions et une reconnaissance
phonétique) et la meilleure est retenue par vo_eleven.py.

Sorties : build/mywebtel/voice6/t<prise>/<id>.mp3 et <id>.json (horodatage par caractère renvoyé par ElevenLabs).
La clé est injectée par le proxy de l'environnement (en-tête xi-api-key) : elle n'apparaît ni ici ni dans le dépôt.
Usage : python3 mywebtel/voice/eleven_gen6.py --takes 1,2,3 [id ...]   (une prise déjà générée n'est pas refaite,
sauf avec --force)."""
import argparse, base64, json, os, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "build", "mywebtel", "voice6")
VOICE = "mvhJVdVoTWVUtL4keT7W"   # Simon (choisi par l'utilisateur le 10/11/2026)
MODEL = "eleven_v4"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.8, "style": 0.2, "use_speaker_boost": True, "speed": 1.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--takes", default="1")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--variant", default="", help="b : graphies de secours (script_v6b.json -> voice6b), « Mèl », « MyWebtèl »")
    a = ap.parse_args()
    rows = json.load(open(os.path.join(HERE, "script_v6%s.json" % a.variant), encoding="utf-8"))
    for take in [int(x) for x in a.takes.split(",")]:
        d = os.path.join(OUT + a.variant, "t%d" % take)
        os.makedirs(d, exist_ok=True)
        for k, (sid, shown, spoken) in enumerate(rows):
            if a.ids and sid not in a.ids:
                continue
            if os.path.exists(os.path.join(d, sid + ".mp3")) and not a.force:
                continue
            body = {"text": spoken, "model_id": MODEL, "language_code": "fr", "voice_settings": SETTINGS,
                    "seed": 7919 * take + k,
                    "previous_text": rows[k - 1][2] if k else None, "next_text": rows[k + 1][2] if k + 1 < len(rows) else None}
            req = urllib.request.Request(
                "https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps?output_format=mp3_44100_128" % VOICE,
                data=json.dumps(body).encode(), headers={"xi-api-key": "proxy-injected", "Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=180))
            open(os.path.join(d, sid + ".mp3"), "wb").write(base64.b64decode(r["audio_base64"]))
            json.dump(r["alignment"], open(os.path.join(d, sid + ".json"), "w"), ensure_ascii=False)
            print("prise %d  %-10s %5.2f s" % (take, sid, r["alignment"]["character_end_times_seconds"][-1]))


if __name__ == "__main__":
    main()
