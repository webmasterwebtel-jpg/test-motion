"""Voix off V5 : voix « Simon » d'ElevenLabs, segment par segment, avec le texte voisin pour une prosodie continue.

voice/script_v5.json : [id, texte attendu, texte envoyé]. Le texte envoyé force la prononciation française quand le
modèle hésite (« scanné » pour le verbe scanner, « plu » pour « t'as plus qu'à »).
Sorties : build/mywebtel/voice/<id>.mp3 et <id>.json (horodatage par caractère, renvoyé par ElevenLabs).
La clé est injectée par le proxy de l'environnement (en-tête xi-api-key) : elle n'apparaît ni ici ni dans le dépôt.
Usage : python3 mywebtel/voice/eleven_gen.py [id ...]   (sans argument : tout ; un segment déjà généré n'est pas refait
sauf s'il est nommé)."""
import json, sys, base64, urllib.request, os
HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "..", "..", "build", "mywebtel", "voice")
os.makedirs(D, exist_ok=True)
rows = json.load(open(f"{HERE}/script_v5.json", encoding="utf-8"))
only = set(sys.argv[1:])
VOICE = "mvhJVdVoTWVUtL4keT7W"   # Simon
for k, (sid, shown, spoken) in enumerate(rows):
    if (only and sid not in only) or (not only and os.path.exists(f"{D}/{sid}.mp3")):
        continue
    body = {"text": spoken, "model_id": "eleven_multilingual_v2", "language_code": "fr",
            "previous_text": rows[k - 1][2] if k else None, "next_text": rows[k + 1][2] if k + 1 < len(rows) else None,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.2, "use_speaker_boost": True, "speed": 1.0}}
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128",
                                 data=json.dumps(body).encode(), headers={"xi-api-key": "proxy-injected", "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=120))
    open(f"{D}/{sid}.mp3", "wb").write(base64.b64decode(d["audio_base64"]))
    json.dump(d["alignment"], open(f"{D}/{sid}.json", "w"), ensure_ascii=False)
    print(sid, round(d["alignment"]["character_end_times_seconds"][-1], 2))
