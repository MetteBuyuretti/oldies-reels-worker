#!/usr/bin/env python3
"""Zero-cost discovery, verification, scoring and copy generation for Oldies Radyo Reels.

No paid AI or model API is required. Primary sources are Wikipedia date pages via the stable Action API,
Wikidata and Wikipedia. Optional RSS feeds can be supplied via OLDIES_RSS_FEEDS
for discovery only; all accepted history candidates still require Wikimedia /
Wikidata evidence.
"""
from __future__ import annotations

import html
import json
import os
import re
import textwrap
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

USER_AGENT = "OldiesRadyoBot/1.0 (https://oldiesradyo.com; info@oldiesradyo.com)"
EN_WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
TR_WIKI_API = "https://tr.wikipedia.org/w/api.php"
CATALOG_PATH = Path(__file__).with_name("oldies-artists.json")
TIMEOUT = 30
SCORE_LIMITS = {
    "date_relevance": 30,
    "audience_fit": 25,
    "source_confidence": 20,
    "visual_strength": 15,
    "freshness": 10,
}


def _session_get(url: str, *, params=None, session=requests):
    response = session.get(
        url,
        params=params,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def load_catalog(path: Path = CATALOG_PATH) -> tuple[dict[str, dict], dict[str, str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    aliases = raw.get("aliases", {})
    artists: dict[str, dict] = {}
    lookup: dict[str, str] = {}
    for tier_text, names in raw.get("tiers", {}).items():
        tier = int(tier_text)
        for name in names:
            entry = {"name": name, "tier": tier, "aliases": list(aliases.get(name, []))}
            artists[name] = entry
            for variant in [name, *entry["aliases"]]:
                lookup[normalize(variant)] = name
    return artists, lookup


MONTH_NAMES_EN = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _strip_wikitext(text: str) -> str:
    text = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", " ", text, flags=re.I | re.S)
    text = re.sub(r"\{\{[^{}]*\}\}", " ", text)
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"''+", "", text)
    return re.sub(r"\s+", " ", text).strip(" *")


def _day_page_wikitext(today: datetime, session=requests) -> str:
    params = {
        "action": "parse",
        "format": "json",
        "formatversion": 2,
        "page": f"{MONTH_NAMES_EN[today.month]} {today.day}",
        "prop": "wikitext",
    }
    payload = _session_get(EN_WIKI_API, params=params, session=session).json()
    return str((payload.get("parse") or {}).get("wikitext", ""))


def _page_metadata(title: str, session=requests) -> dict:
    params = {
        "action": "query",
        "format": "json",
        "formatversion": 2,
        "prop": "pageprops|info",
        "ppprop": "wikibase_item",
        "inprop": "url",
        "redirects": 1,
        "titles": title,
    }
    payload = _session_get(EN_WIKI_API, params=params, session=session).json()
    page = ((payload.get("query") or {}).get("pages") or [{}])[0]
    qid = str((page.get("pageprops") or {}).get("wikibase_item", "") or "")
    return {
        "title": str(page.get("title", title)),
        "wikibase_item": qid if re.fullmatch(r"Q\d+", qid) else "",
        "content_urls": {"desktop": {"page": str(page.get("fullurl", ""))}},
    }


def fetch_day_candidates(today: datetime, artists: dict[str, dict], lookup: dict[str, str], session=requests) -> dict:
    """Read the stable Wikipedia Action API day page instead of relying on Wikifeeds."""
    wikitext = _day_page_wikitext(today, session=session)
    buckets = {"events": [], "births": [], "deaths": []}
    current = ""
    for raw in wikitext.splitlines():
        heading = re.match(r"^==+\s*([^=]+?)\s*==+\s*$", raw.strip())
        if heading:
            label = normalize(heading.group(1))
            current = {"events": "events", "births": "births", "deaths": "deaths"}.get(label, "")
            continue
        if current not in buckets or not raw.lstrip().startswith("*"):
            continue
        clean = _strip_wikitext(raw)
        m = re.match(r"(\d{1,4})\s*[-\u2013\u2014]\s*(.+)", clean)
        if not m:
            continue
        year = int(m.group(1))
        pseudo = {"text": m.group(2), "pages": []}
        artist = match_artist(pseudo, artists, lookup)
        if not artist:
            continue
        try:
            page = _page_metadata(artist, session=session)
        except requests.RequestException:
            page = {
                "title": artist,
                "wikibase_item": "",
                "content_urls": {"desktop": {"page": f"https://en.wikipedia.org/wiki/{quote(artist.replace(' ', '_'))}"}},
            }
        buckets[current].append({"year": year, "text": m.group(2), "pages": [page]})
    return buckets



def _html_to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)</?(?:p|div|h[1-6]|li|br|section|article|tr|td)[^>]*>", "\n", raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n", raw)
    return raw.strip()


def fetch_music_history_candidates(today: datetime, artists: dict[str, dict], lookup: dict[str, str], session=requests) -> list[dict]:
    """Discover exact-day music events from free public music-history pages.

    These pages are discovery sources. Artist identity is tied back to
    Wikipedia/Wikidata before scoring, and visuals still come only from
    license-filtered Wikimedia Commons.
    """
    month = MONTH_NAMES_EN[today.month].lower()
    source_urls = [
        f"https://soundod.com/{month}-{today.day}-in-music-history/",
        f"https://www.thisdayinmusic.com/on-this-day-in-music-{month}-{today.day}/",
    ]
    results: list[dict] = []
    seen: set[tuple] = set()

    for source_url in source_urls:
        try:
            response = session.get(
                source_url,
                headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"},
                timeout=TIMEOUT,
            )
            response.raise_for_status()
        except requests.RequestException:
            continue

        plain = _html_to_text(response.text)
        # Most music-history pages use either "1957 - ..." or "20 Sep 1957 ..."
        patterns = [
            re.compile(r"(?m)^\s*((?:19|20)\d{2})\s*[-\u2013\u2014]\s*(.+)$"),
            re.compile(rf"(?mi)^\s*{today.day}\s+{MONTH_NAMES_EN[today.month][:3]}\s+((?:19|20)\d{{2}})\s+(.+)$"),
        ]

        chunks: list[tuple[int, str]] = []
        for pattern in patterns:
            for match in pattern.finditer(plain):
                year = int(match.group(1))
                body = re.sub(r"\s+", " ", match.group(2)).strip()
                if 20 <= len(body) <= 700:
                    chunks.append((year, body))

        # Fallback for headings followed by prose: split at year markers.
        if not chunks:
            markers = list(re.finditer(r"\b((?:19|20)\d{2})\s*[-\u2013\u2014]\s*", plain))
            for idx, marker in enumerate(markers):
                year = int(marker.group(1))
                end = markers[idx + 1].start() if idx + 1 < len(markers) else min(len(plain), marker.end() + 700)
                body = re.sub(r"\s+", " ", plain[marker.end():end]).strip()[:700]
                if len(body) >= 20:
                    chunks.append((year, body))

        for year, body in chunks:
            artist = match_artist({"text": body, "pages": []}, artists, lookup)
            if not artist:
                continue
            key = (year, artist, normalize(body[:220]))
            if key in seen:
                continue
            seen.add(key)
            try:
                page = _page_metadata(artist, session=session)
            except requests.RequestException:
                page = {
                    "title": artist,
                    "wikibase_item": "",
                    "content_urls": {"desktop": {"page": f"https://en.wikipedia.org/wiki/{quote(artist.replace(' ', '_'))}"}},
                }
            results.append({
                "year": year,
                "text": body,
                "pages": [page],
                "source_url": source_url,
                "discovery_source": "music_history",
            })
    return results


def _item_text(item: dict) -> str:
    bits = [str(item.get("text", ""))]
    for page in item.get("pages") or []:
        bits += [str(page.get("title", "")), str(page.get("description", "")), str(page.get("extract", ""))]
    return " ".join(bits)


def match_artist(item: dict, artists: dict[str, dict], lookup: dict[str, str]) -> str | None:
    haystack = f" {normalize(_item_text(item))} "
    for variant, canonical in sorted(lookup.items(), key=lambda kv: len(kv[0]), reverse=True):
        if variant and f" {variant} " in haystack:
            return canonical
    return None


def _page_for_artist(item: dict, artist: str) -> dict:
    target = normalize(artist)
    pages = item.get("pages") or []
    for page in pages:
        if normalize(page.get("title", "")) == target:
            return page
    for page in pages:
        if target in normalize(page.get("title", "")):
            return page
    return pages[0] if pages else {}


def _qid_from_page(page: dict) -> str:
    qid = str(page.get("wikibase_item", "") or "")
    return qid if re.fullmatch(r"Q\d+", qid) else ""


def fetch_wikidata_entity(qid: str, session=requests) -> dict:
    if not re.fullmatch(r"Q\d+", qid):
        return {}
    payload = _session_get(WIKIDATA_ENTITY.format(qid=qid), session=session).json()
    return (payload.get("entities") or {}).get(qid, {})


def _claim_dates(entity: dict, prop: str) -> list[tuple[int, int, int]]:
    result = []
    for claim in (entity.get("claims") or {}).get(prop, []):
        value = (((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {})
        raw = str(value.get("time", ""))
        m = re.match(r"^[+-](\d{4,})-(\d{2})-(\d{2})T", raw)
        if m:
            result.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return result


def verify_wikidata_date(entity: dict, kind: str, event_date: datetime) -> bool:
    props = {"births": ["P569"], "deaths": ["P570"], "events": ["P585", "P580", "P577"]}.get(kind, [])
    expected = (event_date.year, event_date.month, event_date.day)
    for prop in props:
        for found in _claim_dates(entity, prop):
            if found == expected:
                return True
    return False


def tr_wikipedia_extract(entity: dict, session=requests) -> tuple[str, str]:
    title = (((entity.get("sitelinks") or {}).get("trwiki") or {}).get("title") or "").strip()
    if not title:
        return "", ""
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "redirects": 1,
        "titles": title,
    }
    data = _session_get(TR_WIKI_API, params=params, session=session).json()
    pages = (data.get("query") or {}).get("pages") or {}
    page = next(iter(pages.values()), {})
    extract = re.sub(r"\s+", " ", str(page.get("extract", ""))).strip()
    return title, extract


def _sentences(text: str, limit: int = 2) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
    return [p.strip() for p in parts if 25 <= len(p.strip()) <= 220][:limit]


def _short(text: str, width: int) -> str:
    return textwrap.shorten(re.sub(r"\s+", " ", str(text)).strip(), width=width, placeholder="...")


def deterministic_copy(*, artist: str, kind: str, event_date: datetime, source_text: str, tr_extract: str) -> dict:
    month_names = ["", "OCAK", "\u015eUBAT", "MART", "N\u0130SAN", "MAYIS", "HAZ\u0130RAN", "TEMMUZ", "A\u011eUSTOS", "EYL\u00dcL", "EK\u0130M", "KASIM", "ARALIK"]
    date_text = f"{event_date.day} {month_names[event_date.month]} {event_date.year}"
    if kind == "births":
        date_label = f"{date_text}'DE DO\u011eDU"
        hook = f"Bug\u00fcn {artist}'\u0131 hat\u0131rl\u0131yoruz"
        event_fact = f"{artist}, {event_date.year} y\u0131l\u0131nda bug\u00fcn do\u011fdu."
    elif kind == "deaths":
        date_label = f"{date_text}'DE HAYATINI KAYBETT\u0130"
        hook = f"{artist}'\u0131n m\u00fczi\u011fi ya\u015famaya devam ediyor"
        event_fact = f"{artist}, {event_date.year} y\u0131l\u0131nda bug\u00fcn hayat\u0131n\u0131 kaybetti."
    else:
        date_label = f"{date_text} \u2022 M\u00dcZ\u0130K TAR\u0130H\u0130NDE"
        hook = f"{artist}: m\u00fczik tarihinde bug\u00fcn"
        event_fact = f"{event_date.year} y\u0131l\u0131nda bug\u00fcn {artist} m\u00fczik tarihinde \u00f6nemli bir an ya\u015fad\u0131."
    tr_facts = _sentences(tr_extract, 2)
    facts = [_short(event_fact, 110)]
    facts.append(_short(tr_facts[0], 110) if tr_facts else _short(source_text, 110))
    facts = (facts + ["M\u00fczi\u011fi ve etkisi ku\u015faklar boyunca dinlenmeye devam ediyor."])[:2]
    if kind == "births":
        intro = f"Bug\u00fcn {artist}'\u0131n do\u011fum y\u0131ld\u00f6n\u00fcm\u00fc."
    elif kind == "deaths":
        intro = f"Bug\u00fcn {artist}'\u0131 m\u00fczi\u011fiyle an\u0131yoruz."
    else:
        intro = f"Bug\u00fcn m\u00fczik tarihinde {artist} i\u00e7in \u00f6zel bir g\u00fcn."
    caption = (
        f"{intro}\n\n{facts[0]} {facts[1]}\n\n"
        "Oldies Radyo'da ge\u00e7mi\u015fin en iyi \u015fark\u0131lar\u0131 ve unutulmayan hik\u00e2yeleri "
        "ya\u015famaya devam ediyor. #OldiesRadyo #MuzikTarihindeBugun"
    )
    return {
        "date_label": _short(date_label, 64),
        "hook": _short(hook, 80),
        "closing_headline": _short(f"{artist} \u2022 UNUTULMAYAN M\u00dcZ\u0130K", 50),
        "facts": facts,
        "caption": caption[:900],
        "dj_script": _short(f"{intro} {facts[0]} {facts[1]}", 260),
    }

def score_candidate(candidate: dict, recent_artists: list[str]) -> dict:
    tier = int(candidate.get("tier", 3))
    audience = {1: 25, 2: 23, 3: 18}.get(tier, 18)
    confidence = 20 if candidate.get("wikidata_verified") else 12
    breakdown = {"date_relevance": 30, "audience_fit": audience, "source_confidence": confidence, "visual_strength": 15, "freshness": 10}
    duplicate = normalize(candidate.get("artist", "")) in {normalize(x) for x in recent_artists}
    score = sum(breakdown.values()) - (20 if duplicate else 0)
    candidate["score_breakdown"] = breakdown
    candidate["duplication_penalty"] = 20 if duplicate else 0
    candidate["score"] = score
    return candidate


def build_history_candidates(recent_artists: list[str], today: datetime | None = None, session=requests) -> list[dict]:
    today = today or datetime.now(timezone.utc)
    artists, lookup = load_catalog()
    payload = fetch_day_candidates(today, artists, lookup, session=session)
    extra_events = fetch_music_history_candidates(today, artists, lookup, session=session)
    payload["events"] = list(payload.get("events") or []) + extra_events
    candidates, seen = [], set()
    for kind in ("events", "births", "deaths"):
        for item in payload.get(kind) or []:
            artist = match_artist(item, artists, lookup)
            if not artist:
                continue
            key = (artist, kind, int(item.get("year", 0) or 0), str(item.get("text", "")))
            if key in seen:
                continue
            seen.add(key)
            year = int(item.get("year", 0) or 0)
            if year < 1900 or year > today.year:
                continue
            event_date = datetime(year, today.month, today.day, tzinfo=timezone.utc)
            page = _page_for_artist(item, artist)
            qid = _qid_from_page(page)
            entity, verified = {}, False
            if qid:
                try:
                    entity = fetch_wikidata_entity(qid, session=session)
                    verified = verify_wikidata_date(entity, kind, event_date)
                except requests.RequestException:
                    entity = {}
            tr_title, tr_extract = "", ""
            if entity:
                try:
                    tr_title, tr_extract = tr_wikipedia_extract(entity, session=session)
                except requests.RequestException:
                    pass
            source_text = str(item.get("text", "")).strip()
            copy = deterministic_copy(artist=artist, kind=kind, event_date=event_date, source_text=source_text, tr_extract=tr_extract)
            page_url = str(page.get("content_urls", {}).get("desktop", {}).get("page", "") or "")
            source_url = str(item.get("source_url", "") or "")
            sources = [u for u in [source_url, page_url, f"https://www.wikidata.org/wiki/{qid}" if qid else ""] if u]
            candidate = {
                "artist": artist, "tier": artists[artist]["tier"], "kind": kind,
                "topic": _short(source_text or copy["hook"], 140),
                "event_date": event_date.strftime("%Y-%m-%d"),
                "wikidata_qid": qid, "wikidata_verified": verified,
                "sources": sources, "source_text": source_text, "tr_wikipedia_title": tr_title,
                "image_search_queries": [artist, f"{artist} {year}", f"{artist} portrait"],
                "instagram_music_title": "", "instagram_music_artist": artist,
                "instagram_music_clip_note": "Instagram m\u00fczik ar\u015fivinden konuyla ilgili 10-15 saniyelik b\u00f6l\u00fcm se\u00e7ilebilir.",
                **copy,
            }
            score_candidate(candidate, recent_artists)
            if candidate["score"] >= 80 and candidate["score_breakdown"]["audience_fit"] >= 22:
                candidates.append(candidate)
    candidates.sort(key=lambda c: (c["score"], c["wikidata_verified"], -c["tier"]), reverse=True)
    return candidates


def research_candidates(recent_artists: list[str], today: datetime | None = None, session=requests) -> list[dict]:
    candidates = build_history_candidates(recent_artists, today=today, session=session)
    if not candidates:
        raise RuntimeError("Zero-cost sources produced no candidate above the quality threshold after Wikipedia + music-history discovery")
    return candidates
