"""Compare full, unedited Turkish DJ reads; no WordPress or video writes."""

import base64
import json
import os
from pathlib import Path

import requests
from google.auth import default as google_auth_default
from google.auth.transport.requests import Request as GoogleAuthRequest

import worker


OUTPUT = Path("output/full-take-preview")
TEXT = (
    "23 Eylül bin dokuz yüz yetmiş dört. John Lennon, "
    "'Whatever Gets You Thru the Night' şarkısını yayımladı. "
    "Elton John piyanoda ve geri vokalde ona eşlik etti. "
    "Şarkı, Lennon için ABD'deki ilk solo liste birinciliğini getirdi. "
    "Oldies Radyo. Dinle, beğen, paylaş."
)
PROMPT = (
    "Speak Turkish as a warm, relaxed, experienced music radio DJ talking to one listener. "
    "Read the supplied text exactly once, in one continuous take, without extra words. "
    "The date is 23 September 1974, never 1973: say bin dokuz yüz yetmiş dört clearly. "
    "Pronounce the English song title in English, then return to natural Turkish. "
    "Use a small natural pause after the story before the station name. "
    "Say Oldies briefly like Oldiiz, without stretching the vowels. "
    "Finish Dinle, beğen, paylaş as one simple, friendly invitation at the same volume; "
    "do not elongate or shout paylaş. Avoid theatrical emphasis and newsreader cadence."
)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    credentials, detected_project = google_auth_default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(GoogleAuthRequest())
    project = os.getenv("OLDIES_GCP_PROJECT") or detected_project
    if not project:
        raise RuntimeError("No Google Cloud project")
    results = {"script": TEXT, "models": {}}
    for model in ("gemini-2.5-pro-tts", "gemini-3.1-flash-tts-preview"):
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
                    "voice": {"languageCode": "tr-TR", "name": "Charon", "modelName": model},
                    "audioConfig": {"audioEncoding": "MP3"},
                },
                timeout=120,
            )
            response.raise_for_status()
            content = base64.b64decode(response.json()["audioContent"])
            path = OUTPUT / f"John-Lennon-{model}-one-take.mp3"
            path.write_bytes(content)
            results["models"][model] = {
                "file": path.name,
                "duration_seconds": round(worker._audio_duration(path), 2),
            }
        except Exception as exc:
            results["models"][model] = {"error": str(exc)[:300]}
    (OUTPUT / "details.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not any("file" in item for item in results["models"].values()):
        raise RuntimeError("Neither full-take model produced audio")


if __name__ == "__main__":
    main()
