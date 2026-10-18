"""Offline structural checks for human-researched history packets.

Snapshots and hashes make evidence auditable, not true by declaration. A separate
human review bound to the complete packet and final media remains mandatory.
No URL is fetched and no reviewer approval is created here.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from urllib.parse import urlsplit


class EvidenceError(RuntimeError):
    pass


# Deliberately small, maintainable list. New authorities require source review.
# uDiscover and TDIM share an owner and cannot corroborate one another.
AUTHORITIES = frozenset({"davidbowie.com", "thebeatles.com", "officialcharts.com",
                         "billboard.com", "loc.gov", "grammy.com", "rockhall.com",
                         "johnlennon.com", "jimihendrix.com", "elvis.com",
                         "beegees.com", "rollingstone.com", "nme.com"})
MONTHS = ("", "january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december")


def https_host(url: str) -> str:
    try:
        parts = urlsplit(str(url))
        if (parts.scheme != "https" or not parts.hostname or parts.username or
                parts.password or parts.port not in (None, 443) or parts.fragment):
            return ""
        return parts.hostname.casefold().removeprefix("www.")
    except ValueError:
        return ""


def daily_url(day: date) -> str:
    return f"https://www.thisdayinmusic.com/on-this-day-in-music-{MONTHS[day.month]}-{day.day}/"


def packet_sha256(candidate: dict) -> str:
    return hashlib.sha256(json.dumps(candidate, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_historical_sources(candidate: dict) -> dict:
    """Check exact-day discovery, independent authority and per-script fact links.

    Each document contains a short retained excerpt, URL, retrieval timestamp and
    hash. Each fact names its exact excerpt and Turkish narrative span. A human
    must still compare the original source, translation and event interpretation.
    """
    try:
        event = date.fromisoformat(candidate["event_date"])
        research = date.fromisoformat(candidate["research_date"])
    except (KeyError, ValueError, TypeError) as exc:
        raise EvidenceError("Valid event_date and research_date are required") from exc
    if not 1950 <= event.year <= 1990:
        raise EvidenceError("Event must be in 1950-1990")
    if (event.month, event.day) != (research.month, research.day):
        raise EvidenceError("Event is not on the requested calendar day")
    primary = candidate.get("primary_evidence") or {}
    expected = urlsplit(daily_url(event)).path
    if (https_host(primary.get("url", "")) != "thisdayinmusic.com" or
            urlsplit(str(primary.get("url", ""))).path != expected or
            urlsplit(str(primary.get("url", ""))).query):
        raise EvidenceError("Exact This Day In Music daily page is required")
    artist = str(candidate.get("artist") or "").strip()
    if not artist:
        raise EvidenceError("Artist identity is required")

    def document(row):
        if not isinstance(row, dict) or not https_host(row.get("url", "")):
            raise EvidenceError("Source document needs an HTTPS URL")
        text = row.get("text", "")
        if not isinstance(text, str) or len(text.strip()) < 20 or row.get("sha256") != text_sha256(text):
            raise EvidenceError("Source excerpt missing or hash mismatch")
        try:
            stamp = datetime.fromisoformat(row["retrieved_at"].replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                raise ValueError("timezone missing")
        except (KeyError, ValueError, AttributeError, TypeError) as exc:
            raise EvidenceError("Source retrieval timestamp is required") from exc
        return text

    primary_text = document(primary)
    if (primary.get("event_date") != event.isoformat() or
            primary.get("artist") != artist or artist.casefold() not in primary_text.casefold()):
        raise EvidenceError("Daily page excerpt must identify this artist and event date")
    documents = candidate.get("source_documents") or []
    by_url = {}
    for row in documents:
        document(row)
        host = https_host(row["url"])
        if host not in AUTHORITIES or urlsplit(row["url"]).path in ("", "/"):
            raise EvidenceError("Independent authoritative event source required; generic/secondary URLs forbidden")
        if row["url"] in by_url:
            raise EvidenceError("Duplicate source document")
        by_url[row["url"]] = row
    facts = candidate.get("verified_facts") or []
    if not 2 <= len(facts) <= 4:
        raise EvidenceError("At least two event-specific facts with independent cited evidence required")
    spans, kinds = set(), set()
    for row in facts:
        if not isinstance(row, dict):
            raise EvidenceError("Fact must be an evidence record")
        doc = by_url.get(row.get("url"))
        span = str(row.get("script_span") or "").strip()
        excerpt = str(row.get("source_excerpt") or "").strip()
        if (not doc or len(excerpt) < 15 or excerpt not in doc["text"] or
                len(span.split()) < 6 or span.casefold() in spans):
            raise EvidenceError("Each distinct script fact needs an exact independent source excerpt")
        if row.get("event_date") != event.isoformat() or row.get("artist") != artist:
            raise EvidenceError("Fact date/artist conflicts with selected event (including chart dates)")
        if row.get("kind") not in {"event_date", "detail"}:
            raise EvidenceError("Fact kind must be event_date or detail")
        kinds.add(row["kind"])
        spans.add(span.casefold())
    if "event_date" not in kinds:
        raise EvidenceError("Exact event date must be independently corroborated")
    return {"status": "EVIDENCE_STRUCTURALLY_VALID", "fact_count": len(facts),
            "packet_sha256": packet_sha256(candidate), "human_fact_review_required": True}


def check_script(candidate: dict) -> str:
    check_historical_sources(candidate)
    language = candidate.get("reels_language")
    if language not in {"tr", "en"}:
        raise EvidenceError("Narration language must be tr or en")
    story = candidate.get(f"story_{language}") or {}
    opening = str(story.get("opening") or "").strip()
    narrative = str(story.get("narrative") or "").strip()
    closing = ("Oldies Radyo. Dinle, beğen, paylaş." if language == "tr" else
               "Oldies Radyo. Timeless music. Listen, enjoy, share.")
    if story.get("closing") != closing or not 5 <= len(opening.split()) <= 16:
        raise EvidenceError("DJ opening and exact station closing required")
    expected = " ".join(row["script_span"].strip() for row in candidate["verified_facts"])
    if narrative != expected:
        raise EvidenceError("Narrative contains unsupported text outside independently sourced facts")
    script = " ".join((opening, narrative, closing))
    if candidate.get(f"dj_script_{language}") != script:
        raise EvidenceError("Script must match the evidence-linked opening/narrative/closing")
    if not 45 <= len(script.split()) <= 85:
        raise EvidenceError("DJ story too short or long; 45-85 words required before voice timing review")
    language_text = script
    for name in (candidate.get("artist"), candidate.get("instagram_music_title")):
        if name:
            language_text = language_text.replace(str(name), "")
    if language == "tr" and re.search(r"\b(the|was|were|released|recorded|today|listen|share|on this day)\b", language_text, re.I):
        raise EvidenceError("English language leakage in Turkish narrative")
    if language == "en" and re.search(r"\b(bugün|tarihinde|şarkı|albüm|dinle|beğen|paylaş)\b", language_text, re.I):
        raise EvidenceError("Turkish language leakage in English narrative")
    weak = ("müziğin altın yılları", "müzik tarihinde kayda geçen", "şarkıları hâlâ dinlenmeye")
    if any(term in script.casefold() for term in weak):
        raise EvidenceError("DJ story is vague/generic")
    return script


def check_turkish_script(candidate: dict) -> str:
    if candidate.get("reels_language") != "tr":
        raise EvidenceError("Turkish narration required")
    return check_script(candidate)
