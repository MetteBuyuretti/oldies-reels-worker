"""Isolated John Lennon DJ voice audition; never contacts WordPress."""

import json
import os
from pathlib import Path

from google.auth import default as google_auth_default
from google.auth.transport.requests import Request as GoogleAuthRequest

import worker


OUTPUT = Path("output/dj-voice-preview")
SOURCE = "https://www.johnlennon.com/music/singles/whatever-gets-you-thru-the-night/"
CANDIDATE = {
    "artist": "John Lennon",
    "kind": "events",
    "event_date": "1974-09-23",
    "instagram_music_title": "Whatever Gets You Thru the Night",
    "source_text": (
        "John Lennon released the single Whatever Gets You Thru the Night "
        "on September 23, 1974. It later became his first solo No.1 single in the US."
    ),
    "sources": [SOURCE],
}


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    story = worker.build_turkish_gemini_script(CANDIDATE)
    voices = [voice.strip() for voice in os.getenv("OLDIES_PREVIEW_VOICES", "Charon,Fenrir").split(",") if voice.strip()]
    credentials, detected_project = google_auth_default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(GoogleAuthRequest())
    project = os.getenv("OLDIES_GCP_PROJECT") or detected_project
    if not project:
        raise RuntimeError("No Google Cloud project for voice preview")

    clips = [
        ("story", story, worker.turkish_gemini_style_prompt(CANDIDATE)),
        ("station", "Oldies Radyo.",
         "Bir Türk radyo DJ'inin sıcak istasyon imzası gibi yalnızca 'Oldies Radyo' de. "
         "Oldies sözcüğünü 'Oldiiz' diye söyle. Haber spikeri tonu kullanma."),
        ("cta", "Dinle, beğen, paylaş.",
         "Sıcak bir Türk radyo DJ'i gibi yalnızca 'Dinle, beğen, paylaş' de. "
         "Üç sözcüğü tek nefeste, akıcı günlük konuşma temposuyla söyle. "
         "Virgüllerde uzun durma, hiçbir kelimeyi uzatma veya dramatik vurgulama. "
         "Gülümseyen, sade bir kapanış olsun; yaklaşık iki saniye."),
    ]
    results = {"script": story, "source": SOURCE, "voices": {}}
    errors = []
    for voice in voices:
        try:
            parts = []
            durations = {}
            for label, text, prompt in clips:
                audio = worker._gemini_tts_bytes(
                    text=text, prompt=prompt, language="tr-TR", voice_name=voice,
                    project=project, token=str(credentials.token),
                )
                part = OUTPUT / f"{voice}-{label}.mp3"
                part.write_bytes(audio)
                parts.append(part)
                durations[label] = round(worker._audio_duration(part), 2)
            pause1 = worker._silence_mp3(OUTPUT, f"{voice}-pause-story.mp3", 0.9)
            pause2 = worker._silence_mp3(OUTPUT, f"{voice}-pause-station.mp3", 0.35)
            combined = OUTPUT / f"John-Lennon-{voice}-DJ-preview.mp3"
            worker._join_tts_segments([parts[0], pause1, parts[1], pause2, parts[2]], combined)
            results["voices"][voice] = {
                "file": combined.name,
                "duration_seconds": round(worker._audio_duration(combined), 2),
                "segment_durations": durations,
            }
        except Exception as exc:
            errors.append(f"{voice}: {exc}")
            results["voices"][voice] = {"error": str(exc)}
    (OUTPUT / "preview-details.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if errors:
        raise RuntimeError("; ".join(errors))


if __name__ == "__main__":
    main()
