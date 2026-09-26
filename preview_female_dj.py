"""Audition two female Turkish one-take DJ voices without publishing."""
import base64
import json
import os
from pathlib import Path

import requests
from google.auth import default as google_auth_default
from google.auth.transport.requests import Request as GoogleAuthRequest

import worker

OUTPUT = Path("output/female-dj-preview")
TEXT = worker.JOHN_LENNON_APPROVED_SCRIPT
PROMPT = (
    "Speak natural Istanbul Turkish as a warm, relaxed, experienced music radio DJ "
    "talking to one listener. Read the supplied text exactly once in one continuous take. "
    "The date is 23 September 1974, never 1973; say bin dokuz yüz yetmiş dört clearly. "
    "Pronounce the English song title in English, then return to natural Turkish. "
    "Use a short natural pause after the story. Say Oldies briefly like Oldiiz. "
    "Finish Dinle, beğen, paylaş as a light, friendly invitation at even volume. "
    "Avoid theatrical emphasis, newsreader cadence, drawn-out vowels and shouting."
)

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    credentials, detected_project = google_auth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(GoogleAuthRequest())
    project = os.getenv("OLDIES_GCP_PROJECT") or detected_project
    if not project:
        raise RuntimeError("No Google Cloud project")
    results = {}
    for voice in ("Callirrhoe", "Aoede"):
        try:
            response = requests.post(
                "https://texttospeech.googleapis.com/v1/text:synthesize",
                headers={
                    "Authorization": f"Bearer {credentials.token}",
                    "x-goog-user-project": project,
                    "Content-Type": "application/json; charset=utf-8",
                },
                json={
                    "input": {"prompt": PROMPT, "text": TEXT},
                    "voice": {"languageCode": "tr-TR", "name": voice, "modelName": "gemini-2.5-pro-tts"},
                    "audioConfig": {"audioEncoding": "MP3"},
                },
                timeout=120,
            )
            response.raise_for_status()
            path = OUTPUT / f"John-Lennon-female-{voice}.mp3"
            path.write_bytes(base64.b64decode(response.json()["audioContent"]))
            results[voice] = {"file": path.name, "duration_seconds": round(worker._audio_duration(path), 2)}
        except Exception as exc:
            results[voice] = {"error": str(exc)[:300]}
    (OUTPUT / "details.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not any("file" in result for result in results.values()):
        raise RuntimeError("No female voice audition produced audio")

if __name__ == "__main__":
    main()
