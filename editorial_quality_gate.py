"""Fail-closed OLDIES RADYO quality evidence gate, before any external video delivery.

This guard is intentionally stricter than the current generator. It does not
pretend that a metadata label proves an image authentic: independent reviewer
evidence must be tied to the exact final MP4 SHA-256. No network/API calls.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from source_evidence import (EvidenceError, check_historical_sources, check_script,
                             https_host, packet_sha256)


class EditorialGateError(RuntimeError):
    pass


FORBIDDEN_VISUAL_TERMS = re.compile(
    r"\b(statue|statues|sculpture|monument|waxwork|wax\s+figure|painting|drawing|"
    r"illustration|cartoon|animal|eagle\s+bird|logo|figurine|idol|religious\s+symbol|"
    r"madonna\s+and\s+child|virgin\s+mary|heykel|balmumu|köpek|kedi)\b", re.I
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
    try:
        proc = run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration,format_name:stream=codec_type,duration",
            "-of", "json", str(path),
        ], capture_output=True, text=True, check=True, timeout=30)
        data = json.loads(proc.stdout)
        if "mp4" not in data["format"]["format_name"].split(","):
            raise ValueError("Not an MP4 container")
        streams = [s for s in data["streams"] if s["codec_type"] == "video"]
        secs = float(data["format"]["duration"])
        # A 10s visual track with 27s of audio/metadata is not a 27s Reel.
        if (not streams or not math.isfinite(secs) or secs <= 0 or
                abs(float(streams[0]["duration"]) - secs) > 0.15):
            raise ValueError("Invalid or mismatched video duration")
        return secs
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, TypeError) as exc:
        raise EditorialGateError("MP4 duration cannot be independently measured") from exc


def _host(url: str) -> str:
    return (urlsplit(str(url)).hostname or "").casefold().removeprefix("www.")


def check_media_duration(video: Path) -> dict:
    from media_evidence import MediaEvidenceError, inspect_reel
    try:
        return inspect_reel(video)
    except MediaEvidenceError as exc:
        raise EditorialGateError(str(exc)) from exc


def check_photo_evidence(candidate: dict) -> list[dict]:
    """Reject metadata omissions/substitutes before selecting any photo for a TR render."""
    photos = candidate.get("image_credits") or []
    if len(photos) < 3:
        raise EditorialGateError("At least three documented artist photos required")
    artist = str(candidate.get("artist") or "").strip()
    hashes = [photo.get("asset_sha256") for photo in photos]
    if len(set(hashes)) != len(hashes):
        raise EditorialGateError("Three distinct photo assets required; crop/duplicate fallback forbidden")
    try:
        event_year = date.fromisoformat(candidate["event_date"]).year
    except (KeyError, ValueError, TypeError) as exc:
        raise EditorialGateError("Photo event date required") from exc
    territories = set(candidate.get("target_territories") or [])
    if not territories:
        raise EditorialGateError("Intended photo-use territories must be explicit")
    for i, photo in enumerate(photos, 1):
        if str(photo.get("review_status") or "").startswith("REJECTED"):
            raise EditorialGateError(f"Photo {i} was rejected by asset review; select another photo/event")
        label = " ".join(str(photo.get(x, "")) for x in
                         ("title", "description", "description_url", "event_context", "era_context"))
        if FORBIDDEN_VISUAL_TERMS.search(label):
            raise EditorialGateError(f"Forbidden photo substitute at photo {i}")
        if (photo.get("media_type") != "photograph" or not artist or
                photo.get("identity") != artist or not https_host(photo.get("identity_source_url", ""))):
            raise EditorialGateError(f"Photo {i} artist identity/photograph proof missing")
        license_url = str(photo.get("license_url") or "")
        permitted = {"CC BY 4.0": "https://creativecommons.org/licenses/by/4.0/",
                     "CC BY-SA 4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
                     "CC BY 3.0": "https://creativecommons.org/licenses/by/3.0/",
                     "CC BY-SA 3.0": "https://creativecommons.org/licenses/by-sa/3.0/",
                     "CC0": "https://creativecommons.org/publicdomain/zero/1.0/"}
        pd = (photo.get("license") == "Public domain" and
              https_host(photo.get("rights_source_url", "")) in {"commons.wikimedia.org", "loc.gov"} and
              len(str(photo.get("rights_basis") or "")) >= 30 and
              license_url == "https://creativecommons.org/publicdomain/mark/1.0/")
        if (not pd and permitted.get(photo.get("license")) != license_url) or not license_url:
            raise EditorialGateError(f"Photo {i} license/rights proof missing or unverified")
        if (not https_host(photo.get("description_url", "")) or
                not https_host(photo.get("rights_source_url", "")) or
                not https_host(photo.get("url", "")) or
                not str(photo.get("creator") or "").strip() or photo.get("creator") == "Unknown"):
            raise EditorialGateError(f"Photo {i} source/creator/license evidence missing")
        try:
            year = int(photo["capture_year"])
            resolution = min(int(photo["width"]), int(photo["height"]))
        except (KeyError, ValueError, TypeError) as exc:
            raise EditorialGateError(f"Photo {i} era/resolution proof missing") from exc
        difference = abs(year - event_year)
        if difference > 2:
            raise EditorialGateError(f"Photo {i} is outside the event era")
        if difference and len(str(photo.get("same_year_research") or "")) < 30:
            raise EditorialGateError(f"Photo {i} needs documented event-year search before fallback")
        if difference == 2:
            exception = photo.get("era_exception_review") or {}
            if (exception.get("status") != "APPROVED" or not exception.get("reviewer") or
                    exception.get("asset_sha256") != photo["asset_sha256"] or
                    exception.get("event_date") != candidate["event_date"] or
                    len(str(exception.get("necessity_and_appearance_evidence") or "")) < 60):
                raise EditorialGateError(f"Photo {i} needs independent event-specific +/-2 review")
        covered = set(photo.get("rights_territories") or [])
        if not ("worldwide" in covered or territories <= covered):
            raise EditorialGateError(f"Photo {i} rights do not cover intended territories")
        if photo.get("license") == "Public domain" and (not covered or
                len(str(photo.get("rights_basis") or "")) < 60):
            raise EditorialGateError(f"Photo {i} public-domain territory/basis evidence incomplete")
        if (not 1900 <= year <= date.today().year or resolution < 800 or
                len(str(photo.get("era_context") or "")) < 20 or
                len(str(photo.get("event_context") or "")) < 20 or
                not https_host(photo.get("era_source_url", "")) or
                not re.fullmatch(r"[0-9a-f]{64}", str(photo.get("asset_sha256", "")))):
            raise EditorialGateError(f"Photo {i} era/context/asset hash proof missing")
    return photos


def check_approved_reel(candidate: dict, video: Path, approval: dict) -> dict:
    """Both channels require the same independently reviewed, hash-bound packet.

    A manifest remains a trust boundary: the producer must never author it.
    Mechanical PASS is not source verification, listening or owner approval.
    """
    media = check_media_duration(video)
    try:
        script = check_script(candidate)
    except EvidenceError as exc:
        raise EditorialGateError(str(exc)) from exc
    photos = check_photo_evidence(candidate)
    if approval.get("candidate_sha256") != packet_sha256(candidate):
        raise EditorialGateError("Independent review not bound to exact source/script/photo packet")
    required = ("historical_sources_verified", "script_facts_verified", "natural_dj_voice_verified",
                "opening_narrative_closing_verified", "photo_rights_identity_era_verified",
                "subtitles_sync_readability_verified", "full_video_watched", "full_audio_listened")
    for field in required:
        if approval.get(field) is not True:
            raise EditorialGateError(f"Independent review missing: {field}")
    if (approval.get("status") != "APPROVED" or not str(approval.get("reviewer") or "").strip() or
            approval.get("reviewer") == candidate.get("producer") or
            approval.get("media_sha256") != media["media_sha256"]):
        raise EditorialGateError("Independent review not bound to this exact final MP4/DJ narration")
    reviews = approval.get("visual_evidence") or []
    if len(reviews) != len(photos):
        raise EditorialGateError("Each distinct photo needs independent visual evidence")
    for photo, review in zip(photos, reviews, strict=True):
        if (review.get("asset_sha256") != photo["asset_sha256"] or
                any(review.get(field) is not True for field in
                    ("artist_confirmed", "event_context_confirmed", "era_confirmed", "rights_confirmed")) or
                not https_host(review.get("evidence_url", ""))):
            raise EditorialGateError("Photo identity/era/rights review not bound to the asset bytes")
    rate = len(script.split()) * 60 / media["audio"]["decoded_seconds"]
    if not 90 <= rate <= 195:
        raise EditorialGateError("Narration word rate is outside the natural DJ review range")
    return {**media, "status": "PASS", "editorial_approved": True,
            "photo_count": len(photos), "words_per_minute": round(rate, 1)}


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
