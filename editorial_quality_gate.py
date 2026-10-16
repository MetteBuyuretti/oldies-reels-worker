"""Fail-closed OLDIES RADYO quality evidence gate, before any external video delivery.

This guard is intentionally stricter than the current generator. It does not
pretend that a metadata label proves an image authentic: independent reviewer
evidence must be tied to the exact final MP4 SHA-256. No network/API calls.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


class EditorialGateError(RuntimeError):
    pass


FORBIDDEN_VISUAL_TERMS = re.compile(
    r"\b(statue|statues|sculpture|monument|waxwork|wax\s+figure|painting|drawing|"
    r"illustration|cartoon|animal|eagle\s+bird|logo|figurine|idol|religious\s+symbol)\b", re.I
)
WEAK_STORY_PHRASES = (
    "müzik tarihinde kayda geçen bir gelişme yaşandı",
    "şarkıları hâlâ dinlenmeye devam ediyor",
    "müziğin altın yılları",
    "another great story from the golden years",
)
MIN_REEL_SECONDS = 25.0
MAX_REEL_SECONDS = 30.0


def media_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duration_seconds(path: Path, *, run=subprocess.run) -> float:
    proc = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ], capture_output=True, text=True, check=True, timeout=30)
    try:
        return float(proc.stdout.strip())
    except (ValueError, TypeError) as exc:
        raise EditorialGateError("MP4 duration cannot be independently measured") from exc


def _host(url: str) -> str:
    return (urlsplit(str(url)).hostname or "").casefold().removeprefix("www.")


def check_approved_reel(candidate: dict, video: Path, approval: dict, *, measured_duration: float | None = None) -> dict:
    """Verify independent human-review manifest and basic source/asset evidence.

    This code is not a substitute for an actual historical fact review.
    The approval must be authored independently, not by the worker/LLM.
    """
    if not video.is_file() or video.stat().st_size < 1024:
        raise EditorialGateError("Final MP4 missing or invalid")
    secs = duration_seconds(video) if measured_duration is None else float(measured_duration)
    if not MIN_REEL_SECONDS <= secs <= MAX_REEL_SECONDS:
        raise EditorialGateError(f"Final MP4 duration {secs:.3f}s is not 25-30s")

    event = str(candidate.get("event_date") or "")
    try:
        day = date.fromisoformat(event)
    except ValueError as exc:
        raise EditorialGateError("Invalid event date") from exc
    if not 1950 <= day.year <= 1999:
        raise EditorialGateError("Event outside approved 1950-1999 period")

    sources = list(candidate.get("sources") or [])
    expected = f"/on-this-day-in-music-{day.strftime('%B').lower()}-{day.day}/"
    if not any(_host(u) == "thisdayinmusic.com" and expected in urlsplit(str(u)).path.lower() for u in sources):
        raise EditorialGateError("Event not sourced from the exact day's This Day in Music page")

    proofs = list(approval.get("fact_evidence") or [])
    independent = [
        row for row in proofs if isinstance(row, dict)
        and str(row.get("claim", "")).strip()
        and str(row.get("url", "")).startswith("https://")
        and _host(row.get("url")) not in ("thisdayinmusic.com", "wikipedia.org", "en.wikipedia.org",
                                          "tr.wikipedia.org", "wikidata.org")
    ]
    if len(independent) < 2 or len({row["claim"].casefold() for row in independent}) < 2:
        raise EditorialGateError("At least two distinct details need independent cited evidence")

    script = str(candidate.get("dj_script_tr") if candidate.get("reels_language") != "en" else
                 candidate.get("dj_script_en") or "").strip()
    script = re.sub(r"\s+", " ", script)
    if len(script.split()) < 45 or any(s in script.casefold() for s in WEAK_STORY_PHRASES):
        raise EditorialGateError("DJ story too short or generic for a 25-30s documentary-style Reel")
    closing = ("Oldies Radyo. Timeless music. Listen, enjoy, share." if candidate.get("reels_language") == "en"
               else "Oldies Radyo. Dinle, beğen, paylaş.")
    if closing.casefold() not in script.casefold():
        raise EditorialGateError("Approved station closing is missing")

    photos = list(candidate.get("image_credits") or [])
    checked = list(approval.get("visual_evidence") or [])
    if len(photos) < 3 or len(checked) != len(photos):
        raise EditorialGateError("At least three photos must be independently reviewed")
    artist = str(candidate.get("artist") or "").casefold()
    if not artist:
        raise EditorialGateError("Artist identity missing")
    for i, (photo, review) in enumerate(zip(photos, checked, strict=True)):
        label = " ".join(str(photo.get(x, "")) for x in ("title", "description_url"))
        if FORBIDDEN_VISUAL_TERMS.search(label):
            raise EditorialGateError(f"Forbidden statue/illustration/photo substitute at photo {i + 1}")
        if not str(photo.get("license", "")).strip() or not str(photo.get("description_url", "")).startswith("https://"):
            raise EditorialGateError(f"Image {i + 1} has no license/source proof")
        if min(int(photo.get("width", 0)), int(photo.get("height", 0))) < 800:
            raise EditorialGateError(f"Image {i + 1} lacks suitable source resolution")
        if review.get("artist_confirmed") is not True or review.get("event_context_confirmed") is not True:
            raise EditorialGateError(f"Actual artist/event context is not verified for photo {i + 1}")
        if not str(review.get("evidence_url") or "").startswith("https://"):
            raise EditorialGateError(f"Image {i + 1} lacks reviewer evidence URL")
    digest = media_sha256(video)
    if (approval.get("status") != "APPROVED" or str(approval.get("reviewer", "")).strip() == ""
            or approval.get("media_sha256") != digest):
        raise EditorialGateError("Independent review not bound to this exact final MP4")
    return {"status": "PASS", "duration_seconds": round(secs, 3), "media_sha256": digest,
            "photo_count": len(photos), "independent_claims": len(independent)}


def load_approval(path: str) -> dict:
    if not path:
        raise EditorialGateError("No external reviewer approval manifest; delivery prohibited")
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        raise EditorialGateError("Editorial reviewer approval manifest missing/invalid") from exc
    if not isinstance(data, dict):
        raise EditorialGateError("Editorial approval must be a JSON object")
    return data
