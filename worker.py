#!/usr/bin/env python3
"""Create one zero-cost, approval-only Oldies Radyo Reels draft.

The research path uses only Wikimedia/Wikidata/Wikipedia open data. No OpenAI
or other paid model API is imported or called. Existing Commons -> FFmpeg ->
WordPress DRAFT_REVIEW behavior is preserved.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import subprocess
import textwrap
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import requests
from google.auth import default as google_auth_default
from google.auth.transport.requests import Request as GoogleAuthRequest
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from zero_cost import research_candidates

OUTPUT = Path("output")
WIDTH, HEIGHT, FPS, DURATION = 1080, 1920, 30, 15
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "OldiesRadyoBot/1.0 (https://oldiesradyo.com; info@oldiesradyo.com)"
MAX_VIDEO_BYTES = 100 * 1024 * 1024
MAX_VOICEOVER_BYTES = 20 * 1024 * 1024

ALLOWED_LICENSE_MARKERS = (
    "public domain", "cc0", "cc by", "cc-by", "cc by-sa", "cc-by-sa",
    "creative commons attribution", "creative commons cc0",
)
FORBIDDEN_LICENSE_MARKERS = ("noncommercial", "no derivatives", "cc by-nc", "cc-by-nc", "cc by-nd", "cc-by-nd")


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment value: {name}")
    return value


def wordpress_request(method: str, path: str, bearer: str, base_url: str, **kwargs):
    endpoint = f"{base_url.rstrip('/')}/wp-json/oldies/v1/instagram/reels/{path.lstrip('/')}"
    headers = kwargs.pop("headers", {})
    headers.update({"X-Oldies-Reels-Secret": bearer, "Accept": "application/json", "User-Agent": USER_AGENT})
    response = None
    for attempt in range(4):
        for value in (kwargs.get("files") or {}).values():
            handle = value[1] if isinstance(value, tuple) and len(value) > 1 else value
            if hasattr(handle, "seek"):
                handle.seek(0)
        response = requests.request(method, endpoint, headers=headers, timeout=180, **kwargs)
        if response.status_code < 400:
            return response.json()
        if response.status_code == 429:
            try:
                error_payload = response.json()
            except Exception:
                error_payload = {}
            if isinstance(error_payload, dict) and error_payload.get("code") == "daily_draft_limit":
                print("WordPress daily draft limit already satisfied; no additional draft created.")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "daily_draft_limit",
                    "message": str(error_payload.get("message", "Daily draft limit reached.")),
                }
        if response.status_code not in {429, 502, 503, 504} or attempt == 3:
            break
        delay = 15 * (2**attempt)
        print(f"WordPress temporarily returned {response.status_code}; retrying in {delay}s")
        time.sleep(delay)
    raise RuntimeError(f"WordPress {response.status_code}: {response.text[:700]}")


def get_draft_state(bearer: str, base_url: str) -> dict:
    """Read the review queue once, before spending time on research/render."""
    try:
        data = wordpress_request("GET", "drafts", bearer, base_url)
    except Exception as exc:
        print(f"Draft preflight unavailable; continuing safely: {exc}")
        return {"recent_artists": [], "daily_limit_reached": False}

    drafts = [item for item in data.get("drafts", []) if isinstance(item, dict)]
    recent_artists = sorted({
        str(item.get("artist", "")).strip()
        for item in drafts
        if item.get("artist")
    })[:50]

    policy = data.get("content_policy") if isinstance(data.get("content_policy"), dict) else {}
    try:
        daily_limit = max(1, int(policy.get("maximum_daily_drafts", 1)))
    except (TypeError, ValueError):
        daily_limit = 1
    utc_today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_count = sum(
        1 for item in drafts
        if str(item.get("created_at", "")).startswith(utc_today)
    )
    reached = today_count >= daily_limit
    print(f"Draft preflight: {today_count}/{daily_limit} draft(s) for {utc_today}")
    return {"recent_artists": recent_artists, "daily_limit_reached": reached}


def clean_meta(value) -> str:
    raw = value.get("value", "") if isinstance(value, dict) else str(value or "")
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def license_allowed(license_name: str, usage_terms: str = "") -> bool:
    value = f"{license_name} {usage_terms}".casefold()
    if any(marker in value for marker in FORBIDDEN_LICENSE_MARKERS):
        return False
    return any(marker in value for marker in ALLOWED_LICENSE_MARKERS)


def commons_search(query: str) -> list[dict]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f'intitle:"{query}" filetype:bitmap',
        "gsrnamespace": 6,
        "gsrlimit": 25,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": 1800,
    }
    response = requests.get(COMMONS_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=45)
    response.raise_for_status()
    return list(response.json().get("query", {}).get("pages", {}).values())


def usable_image(page: dict) -> dict | None:
    info = (page.get("imageinfo") or [{}])[0]
    meta = info.get("extmetadata") or {}
    license_name = clean_meta(meta.get("LicenseShortName"))
    usage_terms = clean_meta(meta.get("UsageTerms"))
    if not str(info.get("mime", "")).startswith("image/"):
        return None
    if max(int(info.get("width", 0)), int(info.get("height", 0))) < 1080:
        return None
    if not license_allowed(license_name, usage_terms):
        return None
    url = info.get("thumburl") or info.get("url", "")
    if not str(url).startswith("https://"):
        return None
    return {
        "title": page.get("title", ""),
        "url": url,
        "description_url": info.get("descriptionurl", ""),
        "license": license_name or usage_terms,
        "creator": clean_meta(meta.get("Artist")) or "Unknown",
        "credit": clean_meta(meta.get("Credit")),
        "width": int(info.get("width", 0)),
        "height": int(info.get("height", 0)),
    }


def image_priority(image: dict, artist: str, event_year: int) -> tuple[int, int, int, int, str]:
    title = re.sub(r"^file:", "", str(image.get("title", "")), flags=re.I).casefold()
    artist_name = artist.casefold()
    group_terms = (" and ", " with ", " & ", " group", " band", " members", "family")
    group_penalty = sum(term in title for term in group_terms)
    exact_name = int(title.startswith(artist_name))
    portrait_shape = int(int(image.get("height", 0)) >= int(image.get("width", 0)) * 0.85)

    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", title)]
    if years:
        distance = min(abs(y - event_year) for y in years)
        if distance <= 2:
            period_score = 6
        elif distance <= 5:
            period_score = 5
        elif distance <= 10:
            period_score = 3
        elif distance <= 20:
            period_score = 1
        else:
            period_score = -4
    else:
        period_score = 0

    return (-group_penalty, period_score, exact_name, portrait_shape, title)


def download_commons_photos(candidate: dict, directory: Path) -> tuple[list[Path], list[dict]]:
    paths, credits, seen_titles, seen_hashes = [], [], set(), set()
    artist_query = re.sub(r"^the\s+", "", str(candidate["artist"]), flags=re.I).strip()
    event_year = int(str(candidate.get("event_date", "0"))[:4] or 0)

    # Search the event period first. General artist searches are fallbacks.
    queries = [
        f"{artist_query} {event_year}" if event_year else artist_query,
        f"{artist_query} {max(1900, event_year - 2)}" if event_year else artist_query,
        artist_query,
        f"{artist_query} portrait",
    ]

    for query in queries:
        choices = []
        for page in commons_search(str(query)):
            image = usable_image(page)
            if image and image["title"] not in seen_titles:
                choices.append(image)
        choices.sort(key=lambda image: image_priority(image, artist_query, event_year), reverse=True)

        for image in choices:
            response = requests.get(image["url"], headers={"User-Agent": USER_AGENT}, timeout=90)
            response.raise_for_status()
            digest = hashlib.sha256(response.content).hexdigest()
            if digest in seen_hashes:
                continue
            try:
                opened = Image.open(BytesIO(response.content))
                opened.verify()
                opened = Image.open(BytesIO(response.content)).convert("RGB")
            except Exception:
                continue
            path = directory / f"photo-{len(paths) + 1}.jpg"
            opened.save(path, "JPEG", quality=94, optimize=True)
            paths.append(path)
            credits.append(image)
            seen_titles.add(image["title"])
            seen_hashes.add(digest)
            if len(paths) == 3:
                break
        if len(paths) == 3:
            break

    if len(paths) != 3:
        raise RuntimeError(f"Three different licensed artist photos were required; only {len(paths)} were found")
    return paths, credits


def font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, minimum: int = 38):
    for size in range(start, minimum - 1, -2):
        fnt = font(size, True)
        lines = textwrap.wrap(text, width=max(8, int(max_width / (size * 0.57))))
        if len(lines) <= 4 and all(draw.textbbox((0, 0), line, font=fnt)[2] <= max_width for line in lines):
            return fnt, lines
    return font(minimum, True), textwrap.wrap(text, width=25)[:4]


def cover_photo(path: Path) -> Image.Image:
    photo = Image.open(path).convert("RGB")
    canvas = ImageOps.fit(photo, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
    canvas = ImageEnhance.Contrast(canvas).enhance(1.06)
    return ImageEnhance.Color(canvas).enhance(0.92)


def add_gradient(canvas: Image.Image) -> None:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(HEIGHT):
        top_alpha = int(max(0, 95 * (1 - y / 500)))
        bottom_alpha = int(max(0, 238 * ((y - 760) / (HEIGHT - 760))))
        alpha = max(top_alpha, min(238, bottom_alpha))
        draw.line((0, y, WIDTH, y), fill=(7, 7, 9, alpha))
    canvas.alpha_composite(overlay)


def draw_text_block(draw: ImageDraw.ImageDraw, headline: str, subline: str, accent: str) -> None:
    # Editorial lower-third: restrained, readable and consistent across eras.
    # Keep the bottom ~280 px clear for Instagram/Reels interface overlays.
    draw.rounded_rectangle((72, 900, 1008, 958), radius=22, fill=(12, 12, 15, 205))
    accent_font = font(25, True)
    draw.text((104, 914), accent, font=accent_font, fill=(236, 193, 77, 255))

    title_font, title_lines = fit_text(draw, headline.upper(), 880, 82, 44)
    y = 1006
    for line in title_lines[:3]:
        draw.text(
            (96, y), line, font=title_font,
            fill=(255, 249, 236, 255),
            stroke_width=2, stroke_fill=(0, 0, 0, 190),
        )
        y += title_font.size + 9

    # Fine gold rule separates headline and detail.
    y += 10
    draw.rounded_rectangle((96, y, 306, y + 6), radius=3, fill=(236, 193, 77, 245))
    y += 28

    sub_font, sub_lines = fit_text(draw, subline, 872, 43, 31)
    for line in sub_lines[:4]:
        draw.text((98, y), line, font=sub_font, fill=(238, 235, 227, 255))
        y += sub_font.size + 7

    # Consistent brand signature, clear but not ad-like.
    draw.line((96, 1600, 984, 1600), fill=(255, 255, 255, 95), width=2)
    draw.text((96, 1620), "OLDIES RADYO", font=font(34, True), fill=(236, 193, 77, 255))
    draw.text((790, 1627), "oldiesradyo.com", font=font(22), fill=(245, 245, 245, 230))



def reel_language() -> str:
    value = os.getenv("OLDIES_REELS_LANGUAGE", "tr").strip().lower()
    if value not in {"tr", "en"}:
        raise RuntimeError("OLDIES_REELS_LANGUAGE must be 'tr' or 'en'")
    return value


def _number_word_to_int(word: str) -> int | None:
    return {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }.get(word.casefold())


def _event_chart_details(candidate: dict) -> tuple[int | None, bool]:
    source = re.sub(r"\s+", " ", str(candidate.get("source_text", "")).strip())
    weeks = None
    for pattern in (
        r"([a-z]+)-week run at No\.?1 in the UK",
        r"first of ([a-z]+) consecutive weeks",
        r"for ([a-z]+) consecutive weeks",
    ):
        match = re.search(pattern, source, re.I)
        if match:
            weeks = _number_word_to_int(match.group(1))
            break
    uk_no1 = bool(re.search(r"No\.?1 in the UK|number one in the UK", source, re.I))
    return weeks, uk_no1


def turkish_display_copy(candidate: dict) -> dict:
    artist = re.sub(r"\s+", " ", str(candidate.get("artist", "")).strip())
    title = re.sub(r"\s+", " ", str(candidate.get("instagram_music_title", "")).strip())
    event_date = str(candidate.get("event_date", "")).strip()
    kind = str(candidate.get("kind", "events"))
    original_facts = list(candidate.get("facts") or ["", ""])
    while len(original_facts) < 2:
        original_facts.append("")

    try:
        parsed = datetime.strptime(event_date, "%Y-%m-%d")
        month_names = ["", "OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN", "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK"]
        date_text = f"{parsed.day} {month_names[parsed.month]} {parsed.year}"
        year = str(parsed.year)
    except ValueError:
        date_text = event_date.upper()
        year = event_date[:4]

    weeks, uk_no1 = _event_chart_details(candidate)

    if kind == "births":
        hook = f"{artist.upper()} • {year}"
        fact1 = f"{artist}, {year} yılında bugün doğdu."
        fact2 = original_facts[1] or "Müziğiyle bir dönemin hafızasında yer etti."
        closing = "MÜZİĞİN HAFIZASINDA"
    elif kind == "deaths":
        hook = f"{artist.upper()} • HATIRLIYORUZ"
        fact1 = f"{artist}, {year} yılında bugün hayatını kaybetti."
        fact2 = original_facts[1] or "Şarkıları yıllar sonra da dinlenmeye devam ediyor."
        closing = "ŞARKILARI YAŞAMAYA DEVAM EDİYOR"
    elif title and uk_no1:
        hook = f"{artist.upper()} • {year}"
        fact1 = f"'{title}', İngiltere listelerinde 1 numaraya çıktı."
        fact2 = f"Zirvedeki yerini {weeks} hafta korudu." if weeks else "Liste zirvesine yerleşti."
        closing = "MÜZİK TARİHİNDEN BİR SAYFA"
    elif title:
        hook = f"{artist.upper()} • {year}"
        fact1 = original_facts[0] or f"{artist} için müzik tarihinde önemli bir gündü."
        fact2 = original_facts[1] or f"Öne çıkan kayıt: '{title}'."
        closing = "MÜZİK TARİHİNDEN BİR SAYFA"
    else:
        hook = f"{artist.upper()} • {year}"
        fact1 = original_facts[0]
        fact2 = original_facts[1]
        closing = "MÜZİK TARİHİNDEN BİR SAYFA"

    caption = (
        f"Bugün müzik tarihinde: {artist}. {fact1} {fact2}\n\n"
        "Müziğin altın yılları ve unutulmayan hikâyeler Oldies Radyo'da. "
        "#OldiesRadyo #MuzikTarihindeBugun"
    )
    return {
        "date_label": f"{date_text} • MÜZİK TARİHİNDE",
        "hook": hook,
        "event_headline": hook,
        "closing_headline": closing,
        "facts": [fact1, fact2],
        "caption": caption[:900],
    }


def english_display_copy(candidate: dict) -> dict:
    artist = re.sub(r"\s+", " ", str(candidate.get("artist", "")).strip())
    event_date = str(candidate.get("event_date", "")).strip()
    kind = str(candidate.get("kind", "events"))
    title = re.sub(r"\s+", " ", str(candidate.get("instagram_music_title", "")).strip())
    source = re.sub(r"\s+", " ", str(candidate.get("source_text", "")).strip())

    try:
        parsed = datetime.strptime(event_date, "%Y-%m-%d")
        date_text = parsed.strftime("%b %d, %Y").upper()
        year = parsed.strftime("%Y")
    except ValueError:
        date_text = event_date.upper()
        year = event_date[:4]

    weeks, uk_no1 = _event_chart_details(candidate)

    if kind == "births":
        hook = f"{artist.upper()} • {year}"
        fact1 = f"{artist} was born on this day in {year}."
        fact2 = "A voice from the golden years, remembered on Oldies Radyo."
        closing = "A NAME THAT STILL RESONATES"
    elif kind == "deaths":
        hook = f"REMEMBERING {artist.upper()}"
        fact1 = f"{artist} passed away on this day in {year}."
        fact2 = "The records remain, and so do the memories."
        closing = "THE MUSIC LIVES ON"
    elif title and uk_no1:
        hook = f"{artist.upper()} • {year}"
        fact1 = f"'{title}' reached No.1 in the UK."
        fact2 = f"It stayed on top for {weeks} consecutive weeks." if weeks else "It became a UK chart-topper."
        closing = "A PAGE FROM MUSIC HISTORY"
    elif title:
        hook = f"{artist.upper()} • {year}"
        fact1 = textwrap.shorten(source, width=116, placeholder="...") if source else f"{artist} made music history with '{title}'."
        fact2 = f"One of the records remembered from {year}."
        closing = "A PAGE FROM MUSIC HISTORY"
    else:
        hook = f"{artist.upper()} • {year}"
        fact1 = textwrap.shorten(source, width=116, placeholder="...") if source else f"{artist} made music history on this day."
        fact2 = "Another story from the golden years of music."
        closing = "A PAGE FROM MUSIC HISTORY"

    caption = (
        f"On this day in music history: {artist}. {fact1} {fact2}\n\n"
        "Great records, unforgettable names and the stories behind them — Oldies Radyo. "
        "#OldiesRadyo #OnThisDayInMusic"
    )
    return {
        "date_label": f"{date_text} • MUSIC HISTORY",
        "hook": hook,
        "event_headline": hook,
        "closing_headline": closing,
        "facts": [fact1, fact2],
        "caption": caption[:900],
    }


def apply_reel_language(candidate: dict, language: str) -> dict:
    localized = dict(candidate)
    localized.update(english_display_copy(candidate) if language == "en" else turkish_display_copy(candidate))
    localized["reels_language"] = language
    return localized


def build_turkish_dj_parts(candidate: dict) -> list[tuple[str, str]]:
    """Return language-tagged speech parts so English titles are never read with Turkish phonetics."""
    artist = re.sub(r"\s+", " ", str(candidate.get("artist", "")).strip())
    title = re.sub(r"\s+", " ", str(candidate.get("instagram_music_title", "")).strip())
    event_date = str(candidate.get("event_date", "")).strip()
    year = event_date[:4] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", event_date) else ""
    weeks, uk_no1 = _event_chart_details(candidate)

    tr_numbers = {
        1: "bir", 2: "iki", 3: "üç", 4: "dört", 5: "beş",
        6: "altı", 7: "yedi", 8: "sekiz", 9: "dokuz", 10: "on",
    }

    if title and uk_no1:
        before = f"{year}'ye gidiyoruz. {artist} imzalı kayıt"
        after = "İngiltere'de bir numaraya çıktı."
        if weeks:
            after += f" {tr_numbers.get(weeks, str(weeks)).capitalize()} hafta zirvede kaldı."
        after += " Oldies Radyo."
        return [("tr-TR", before), ("en-AU", title), ("tr-TR", after)]

    facts = list(candidate.get("facts") or ["", ""])
    while len(facts) < 2:
        facts.append("")
    spoken = re.sub(
        r"\s+",
        " ",
        f"Bugün müzik tarihinde. {facts[0]} {facts[1]} Oldies Radyo.",
    ).strip()

    if not title:
        return [("tr-TR", spoken)]

    pattern = re.compile(r"['\"‘’“”]?" + re.escape(title) + r"['\"‘’“”]?", re.I)
    match = pattern.search(spoken)
    if not match:
        return [("tr-TR", spoken)]

    before = spoken[:match.start()].strip()
    after = spoken[match.end():].strip()
    parts: list[tuple[str, str]] = []
    if before:
        parts.append(("tr-TR", before))
    parts.append(("en-AU", title))
    if after:
        parts.append(("tr-TR", after))
    return parts


def build_turkish_dj_script(candidate: dict) -> str:
    return " ".join(text for _, text in build_turkish_dj_parts(candidate)).strip()


def turkish_genitive(name: str) -> str:
    """Add a simple Turkish genitive suffix to proper names: Sinatra'nın, Elvis'in."""
    clean = name.strip()
    lowered = clean.casefold()
    last_vowel = next((ch for ch in reversed(lowered) if ch in "aeıioöuü"), "a")
    suffix = "ın" if last_vowel in "aı" else "in" if last_vowel in "ei" else "un" if last_vowel in "ou" else "ün"
    buffer = "n" if lowered and lowered[-1] in "aeıioöuü" else ""
    return f"{clean}'{buffer}{suffix}"


def _turkish_record_noun(candidate: dict) -> str:
    source = re.sub(r"\s+", " ", str(candidate.get("source_text", "")).strip()).casefold()
    if "album" in source or "lp" in source:
        return "albümü"
    if "single" in source or "song" in source:
        return "şarkısı"
    return "kaydı"


def _turkish_period_context(year: str, artist: str) -> str:
    try:
        numeric_year = int(year)
    except (TypeError, ValueError):
        return ""
    if 1955 <= numeric_year <= 1962 and "sinatra" in artist.casefold():
        return "Rock'n roll döneminde, Sinatra için büyük başarı."
    return ""


def build_turkish_gemini_script(candidate: dict) -> str:
    """Short, factual Turkish DJ copy: event, standout detail, context, natural sign-off."""
    artist = re.sub(r"\s+", " ", str(candidate.get("artist", "")).strip())
    title = re.sub(r"\s+", " ", str(candidate.get("instagram_music_title", "")).strip())
    event_date = str(candidate.get("event_date", "")).strip()
    year = event_date[:4] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", event_date) else ""
    kind = str(candidate.get("kind", "events"))
    weeks, uk_no1 = _event_chart_details(candidate)
    tr_numbers = {
        1: "bir", 2: "iki", 3: "üç", 4: "dört", 5: "beş",
        6: "altı", 7: "yedi", 8: "sekiz", 9: "dokuz", 10: "on",
    }

    if kind == "births":
        return (
            f"{year}... {artist} bugün doğdu. "
            "Sonrası müzik tarihi. Oldies Radyo."
        )

    if kind == "deaths":
        return (
            f"Bugün {artist}'ı hatırlıyoruz. "
            f"{year}'da bugün aramızdan ayrıldı. "
            "Şarkıları hâlâ bizimle... Oldies Radyo."
        )

    if title and uk_no1:
        noun = _turkish_record_noun(candidate)
        weeks_text = tr_numbers.get(weeks, str(weeks)) if weeks else ""
        context = _turkish_period_context(year, artist)
        if weeks:
            script = (
                f"{year}... {turkish_genitive(artist)} {title} {noun} İngiltere'de bir numara. "
                f"Üstelik {weeks_text} hafta boyunca. "
            )
        else:
            script = (
                f"{year}... {turkish_genitive(artist)} {title} {noun} İngiltere'de bir numara. "
            )
        if context:
            script += context + " "
        return script + "Oldies Radyo."

    if title:
        noun = _turkish_record_noun(candidate)
        return (
            f"{year}... {artist}. {title} {noun}. "
            "O günün kaydı, bugünün hatırası... Oldies Radyo."
        )

    return (
        f"{year}... Bugün {artist} için müzik tarihinde önemli bir gün. "
        "Kısa bir not, iyi bir şarkı... Oldies Radyo."
    )



def turkish_gemini_style_prompt() -> str:
    return (
        "Türkçe konuşan deneyimli ve sevilen bir radyo DJ'i gibi oku. "
        "Ses sıcak, içten, güler yüzlü ve canlı olsun; dinleyiciye sevdiği bir plağın ilginç bir ayrıntısını "
        "heyecanla anlatıyormuş gibi konuş. Reklam spikeri, haber spikeri veya fragman sesi gibi olma. "
        "Doğal iniş çıkışlar, küçük nefesler ve mikro duraklamalar bırak; metni kusursuz bir makine gibi okuma. "
        "Sanatçı ve İngilizce şarkı ya da albüm adlarını rahat ve doğal İngilizce telaffuz et, sonra Türkçeye "
        "aynı ses karakteriyle akıcı biçimde dön. Şaşırtıcı bir sayı veya başarı varsa keyifli, hafif bir heyecan ver. "
        "Son iki kelime olan Oldies Radyo'yu slogan gibi bağırma; gülümseyen, sıcak ve doğal bir imza gibi bitir."
    )



def make_scenes(candidate: dict, photos: list[Path], directory: Path) -> list[Path]:
    artist = str(candidate["artist"])
    hook = str(candidate.get("event_headline") or candidate.get("hook") or artist)
    facts = list(candidate.get("facts") or ["", ""])
    while len(facts) < 2:
        facts.append("")
    closing = str(candidate.get("closing_headline") or f"{artist} • OLDIES RADYO")
    language = str(candidate.get("reels_language", "tr"))

    if language == "en":
        accents = (
            "ON THIS DAY IN MUSIC",
            "THE STORY",
            "OLDIES RADYO • MUSIC & MEMORIES",
        )
    else:
        accents = (
            "BUGÜN MÜZİK TARİHİNDE",
            "O GÜN NE OLDU?",
            "OLDIES RADYO • MÜZİĞİN HAFIZASI",
        )

    scenes = [
        (hook, str(candidate["date_label"]), accents[0]),
        (artist, str(facts[0]), accents[1]),
        (closing, str(facts[1]), accents[2]),
    ]

    paths = []
    for index, (photo, content) in enumerate(zip(photos, scenes), start=1):
        canvas = cover_photo(photo).convert("RGBA")
        add_gradient(canvas)
        draw_text_block(ImageDraw.Draw(canvas), *content)
        path = directory / f"scene-{index}.jpg"
        canvas.convert("RGB").save(path, "JPEG", quality=95, optimize=True)
        paths.append(path)
    return paths




def build_english_dj_script(candidate: dict) -> str:
    """Create a short factual English radio-DJ link from verified candidate fields."""
    artist = re.sub(r"\s+", " ", str(candidate.get("artist", "")).strip())
    event_date = str(candidate.get("event_date", "")).strip()
    year = event_date[:4] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", event_date) else ""
    kind = str(candidate.get("kind", "events"))
    title = re.sub(r"\s+", " ", str(candidate.get("instagram_music_title", "")).strip())

    if kind == "births":
        script = (
            f"Born on this day in {year}: {artist}. "
            "Another voice from the golden years of music, remembered here on Oldies Radyo. "
            "And there's more great music ahead."
        )
    elif kind == "deaths":
        script = (
            f"Remembering {artist}, who left us on this day in {year}. "
            "The music lives on — right here on Oldies Radyo. "
            "And there's more great music ahead."
        )
    elif title:
        script = (
            f"On this day in {year}, {artist} made music history with '{title}'. "
            "You're with Oldies Radyo — keeping the great records and their stories alive. "
            "And there's more great music ahead."
        )
    else:
        script = (
            f"On this day in {year}, {artist} made music history. "
            "You're with Oldies Radyo — another story from the golden years of music. "
            "And there's more great music ahead."
        )
    return re.sub(r"\s+", " ", script).strip()


def _google_tts_bytes(
    *,
    text: str,
    language: str,
    voice_name: str,
    project: str,
    token: str,
) -> bytes:
    response = requests.post(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        headers={
            "Authorization": f"Bearer {token}",
            "x-goog-user-project": project,
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
        },
        json={
            "input": {"text": text},
            "voice": {"languageCode": language, "name": voice_name},
            "audioConfig": {"audioEncoding": "MP3"},
        },
        timeout=90,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Google TTS {response.status_code}: {response.text[:700]}")
    audio_content = str(response.json().get("audioContent", "")).strip()
    if not audio_content:
        raise RuntimeError("Google TTS returned no audio content")
    return base64.b64decode(audio_content)


def _gemini_tts_bytes(
    *,
    text: str,
    prompt: str,
    language: str,
    voice_name: str,
    project: str,
    token: str,
) -> bytes:
    response = requests.post(
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        headers={
            "Authorization": f"Bearer {token}",
            "x-goog-user-project": project,
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
        },
        json={
            "input": {"prompt": prompt, "text": text},
            "voice": {
                "languageCode": language,
                "name": voice_name,
                "modelName": "gemini-2.5-flash-tts",
            },
            "audioConfig": {"audioEncoding": "MP3"},
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"Gemini TTS {response.status_code}: {response.text[:700]}")
    audio_content = str(response.json().get("audioContent", "")).strip()
    if not audio_content:
        raise RuntimeError("Gemini TTS returned no audio content")
    return base64.b64decode(audio_content)


def _join_tts_segments(paths: list[Path], target: Path) -> None:
    if len(paths) == 1:
        target.write_bytes(paths[0].read_bytes())
        return

    inputs: list[str] = []
    filters: list[str] = []
    labels: list[str] = []
    for index, path in enumerate(paths):
        inputs += ["-i", str(path)]
        label = f"a{index}"
        labels.append(f"[{label}]")
        filters.append(
            f"[{index}:a]aresample=48000,"
            f"aformat=sample_fmts=fltp:channel_layouts=mono[{label}]"
        )
    graph = ";".join(filters) + ";" + "".join(labels) + f"concat=n={len(paths)}:v=0:a=1[out]"
    subprocess.run(
        [
            "ffmpeg", "-y", *inputs,
            "-filter_complex", graph,
            "-map", "[out]",
            "-c:a", "libmp3lame", "-b:a", "192k",
            str(target),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def synthesize_google_voice(candidate: dict, directory: Path) -> Path | None:
    """Use expressive Gemini Flash for Turkish; keep Chirp 3 HD as safe fallback."""
    enabled = os.getenv("OLDIES_TTS_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return None

    mode = str(candidate.get("reels_language") or reel_language())
    project = os.getenv("OLDIES_GCP_PROJECT", "").strip()
    credentials, detected_project = google_auth_default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(GoogleAuthRequest())
    project = project or str(detected_project or "").strip()
    if not project:
        raise RuntimeError("Google TTS is enabled but no Google Cloud project was resolved")
    token = str(credentials.token)

    # Turkish: one expressive Gemini Flash request per Reel. This keeps cost predictable
    # and lets the same voice naturally handle Turkish plus English artist/title names.
    engine = os.getenv("OLDIES_TTS_ENGINE", "auto").strip().lower() or "auto"
    fallback_enabled = os.getenv("OLDIES_TTS_FALLBACK", "true").strip().lower() in {"1", "true", "yes", "on"}
    if mode == "tr" and engine in {"auto", "gemini", "gemini_flash"}:
        gemini_voice = os.getenv("OLDIES_GEMINI_TTS_VOICE", "Charon").strip() or "Charon"
        script = build_turkish_gemini_script(candidate)
        try:
            raw = _gemini_tts_bytes(
                text=script,
                prompt=turkish_gemini_style_prompt(),
                language="tr-TR",
                voice_name=gemini_voice,
                project=project,
                token=token,
            )
            path = directory / "voiceover-google.mp3"
            path.write_bytes(raw)
            if path.stat().st_size <= 0 or path.stat().st_size > MAX_VOICEOVER_BYTES:
                raise RuntimeError("Generated Gemini voiceover failed size validation")
            candidate["dj_script_tr"] = script
            candidate["tts_voice"] = gemini_voice
            candidate["tts_language"] = "tr-TR"
            candidate["tts_engine"] = "gemini-2.5-flash-tts"
            print(f"Gemini Flash TTS ready: {gemini_voice} ({path.stat().st_size} bytes)")
            return path
        except Exception as exc:
            if not fallback_enabled:
                raise
            print(f"Gemini Flash TTS unavailable; falling back to Chirp 3 HD: {exc}")

    main_default_language = "en-AU" if mode == "en" else "tr-TR"
    main_default_voice = "en-AU-Chirp3-HD-Charon" if mode == "en" else "tr-TR-Chirp3-HD-Charon"
    main_language = os.getenv("OLDIES_TTS_LANGUAGE", "").strip() or main_default_language
    main_voice = os.getenv("OLDIES_TTS_VOICE", "").strip() or main_default_voice
    title_voice = os.getenv("OLDIES_TTS_TITLE_VOICE", "").strip() or "en-AU-Chirp3-HD-Charon"

    if mode == "en":
        parts = [("en-AU", build_english_dj_script(candidate))]
    else:
        parts = build_turkish_dj_parts(candidate)

    segment_paths: list[Path] = []
    for index, (segment_language, text) in enumerate(parts):
        voice = title_voice if segment_language.startswith("en-") and mode == "tr" else main_voice
        language = segment_language if segment_language.startswith("en-") and mode == "tr" else main_language
        raw = _google_tts_bytes(
            text=text,
            language=language,
            voice_name=voice,
            project=project,
            token=token,
        )
        segment = directory / f"voiceover-segment-{index}.mp3"
        segment.write_bytes(raw)
        segment_paths.append(segment)

    path = directory / "voiceover-google.mp3"
    _join_tts_segments(segment_paths, path)
    if path.stat().st_size <= 0 or path.stat().st_size > MAX_VOICEOVER_BYTES:
        raise RuntimeError("Generated Google voiceover failed size validation")

    script = build_english_dj_script(candidate) if mode == "en" else build_turkish_dj_script(candidate)
    candidate["dj_script_en" if mode == "en" else "dj_script_tr"] = script
    candidate["tts_voice"] = main_voice
    candidate["tts_language"] = main_language
    candidate["tts_engine"] = "chirp3-hd"
    if mode == "tr" and any(lang.startswith("en-") for lang, _ in parts):
        candidate["tts_title_voice"] = title_voice
        candidate["tts_title_language"] = "en-AU"
    print(f"Chirp 3 HD ready: {main_voice} ({path.stat().st_size} bytes, segments={len(parts)})")
    return path



def download_voiceover(directory: Path) -> Path | None:
    """Fetch an optional external voiceover without changing the zero-cost default path."""
    url = os.getenv("OLDIES_VOICEOVER_URL", "").strip()
    if not url:
        return None
    if not url.startswith("https://"):
        raise RuntimeError("OLDIES_VOICEOVER_URL must use HTTPS")

    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=90, stream=True)
    response.raise_for_status()
    content_type = str(response.headers.get("content-type", "")).split(";", 1)[0].strip().lower()
    allowed_types = {
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mp4": ".m4a",
        "audio/aac": ".aac",
        "video/mp4": ".mp4",
        "application/octet-stream": ".bin",
    }
    suffix = allowed_types.get(content_type)
    if suffix is None:
        raise RuntimeError(f"Unsupported voiceover content type: {content_type or 'unknown'}")

    declared = response.headers.get("content-length")
    if declared and int(declared) > MAX_VOICEOVER_BYTES:
        raise RuntimeError("Voiceover exceeds 20 MB limit")

    path = directory / f"voiceover-input{suffix}"
    total = 0
    with path.open("wb") as handle:
        for chunk in response.iter_content(chunk_size=1024 * 256):
            if not chunk:
                continue
            total += len(chunk)
            if total > MAX_VOICEOVER_BYTES:
                path.unlink(missing_ok=True)
                raise RuntimeError("Voiceover exceeds 20 MB limit")
            handle.write(chunk)

    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0 or not probe.stdout.strip():
        path.unlink(missing_ok=True)
        raise RuntimeError("Voiceover URL did not contain a readable audio stream")

    print(f"Voiceover ready: {path.name} ({total} bytes, codec={probe.stdout.strip()})")
    return path


def render(scenes: list[Path], target: Path, voiceover: Path | None = None) -> None:
    inputs = []
    for scene in scenes:
        inputs += ["-loop", "1", "-t", "5.5", "-i", str(scene)]

    graph = (
        f"[0:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00050,1.08)':d=165:s={WIDTH}x{HEIGHT}:fps={FPS}[a];"
        f"[1:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00036,1.065)':d=165:s={WIDTH}x{HEIGHT}:fps={FPS}[b];"
        f"[2:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00046,1.075)':d=165:s={WIDTH}x{HEIGHT}:fps={FPS}[c];"
        "[a][b]xfade=transition=fade:duration=0.55:offset=4.95[x];"
        "[x][c]xfade=transition=smoothleft:duration=0.55:offset=9.90[v]"
    )
    if voiceover:
        inputs += ["-i", str(voiceover)]
        graph += (
            ";[3:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            "highpass=f=70,lowpass=f=16000,"
            "acompressor=threshold=-20dB:ratio=3:attack=10:release=120:makeup=2,"
            "loudnorm=I=-16:TP=-1.0:LRA=7,apad[voice]"
        )
        command = [
            "ffmpeg", "-y", *inputs, "-filter_complex", graph,
            "-map", "[v]", "-map", "[voice]",
            "-t", str(DURATION), "-r", str(FPS),
            "-c:v", "libx264", "-preset", "medium",
            "-crf", "24", "-maxrate", "2200k", "-bufsize", "4400k",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", str(target),
        ]
    else:
        command = [
            "ffmpeg", "-y", *inputs, "-filter_complex", graph, "-map", "[v]", "-an",
            "-t", str(DURATION), "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
            "-crf", "24", "-maxrate", "2200k", "-bufsize", "4400k",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
        ]
    subprocess.run(command, check=True)
    if not target.exists() or target.stat().st_size <= 0 or target.stat().st_size > MAX_VIDEO_BYTES:
        raise RuntimeError("Rendered MP4 failed size validation")




def cleanup_delivery_assets(api: str, headers: dict, release: dict, retention_days: int = 10) -> None:
    """Delete public delivery assets older than the retention window."""
    release_id = release.get("id")
    if not release_id:
        return
    response = requests.get(
        f"{api}/releases/{release_id}/assets",
        headers=headers,
        params={"per_page": 100},
        timeout=30,
    )
    if response.status_code != 200:
        print(f"Delivery cleanup skipped: GitHub returned {response.status_code}")
        return

    cutoff = time.time() - max(1, retention_days) * 86400
    deleted = 0
    assets = response.json()
    for asset in assets if isinstance(assets, list) else []:
        created_at = str(asset.get("created_at", ""))
        asset_id = asset.get("id")
        if not created_at or not asset_id:
            continue
        try:
            created_ts = datetime.fromisoformat(created_at.replace("Z", "+00:00")).timestamp()
        except ValueError:
            continue
        if created_ts >= cutoff:
            continue
        deleted_response = requests.delete(
            f"{api}/releases/assets/{asset_id}",
            headers=headers,
            timeout=30,
        )
        if deleted_response.status_code == 204:
            deleted += 1
    print(f"Delivery cleanup: removed {deleted} asset(s) older than {retention_days} days")


def publish_delivery_asset(candidate: dict, video: Path) -> str:
    """Upload the rendered MP4 as a public GitHub Release asset.

    WordPress then receives only the HTTPS URL, avoiding large multipart
    uploads through the WordPress.com REST edge.
    """
    token = os.getenv("GITHUB_TOKEN", "").strip()
    repository = os.getenv("GITHUB_REPOSITORY", "").strip()
    if not token or not repository:
        return ""

    api = f"https://api.github.com/repos/{repository}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "oldies-reels-worker",
    }
    tag = "reels-delivery"
    response = requests.get(f"{api}/releases/tags/{tag}", headers=headers, timeout=30)
    if response.status_code == 404:
        target = os.getenv("GITHUB_REF_NAME", "zero-cost-final-implementation").strip() or "zero-cost-final-implementation"
        response = requests.post(
            f"{api}/releases",
            headers=headers,
            json={
                "tag_name": tag,
                "target_commitish": target,
                "name": "Oldies Reels Delivery",
                "body": "Automated delivery assets for WordPress DRAFT_REVIEW. No live social publishing.",
                "draft": False,
                "prerelease": False,
            },
            timeout=30,
        )
    if response.status_code not in (200, 201):
        raise RuntimeError(f"GitHub delivery release failed: {response.status_code} {response.text[:500]}")
    release = response.json()
    cleanup_delivery_assets(api, headers, release, retention_days=10)

    artist_slug = re.sub(r"[^a-z0-9]+", "-", str(candidate.get("artist", "")).lower()).strip("-")[:60] or "oldies"
    event_date = re.sub(r"[^0-9-]", "", str(candidate.get("event_date", ""))) or "undated"
    run_id = re.sub(r"[^0-9]", "", os.getenv("GITHUB_RUN_ID", "")) or str(int(time.time()))
    attempt = re.sub(r"[^0-9]", "", os.getenv("GITHUB_RUN_ATTEMPT", "")) or "1"
    language = re.sub(r"[^a-z]", "", str(candidate.get("reels_language", "tr")).lower()) or "tr"\n    asset_name = f"{event_date}-{artist_slug}-{language}-{run_id}-{attempt}.mp4"

    upload_url = str(release.get("upload_url", "")).split("{", 1)[0]
    if not upload_url:
        raise RuntimeError("GitHub delivery release has no upload URL")
    upload_headers = dict(headers)
    upload_headers["Content-Type"] = "video/mp4"
    with video.open("rb") as handle:
        uploaded = requests.post(
            upload_url,
            headers=upload_headers,
            params={"name": asset_name},
            data=handle,
            timeout=180,
        )
    if uploaded.status_code != 201:
        raise RuntimeError(f"GitHub delivery asset upload failed: {uploaded.status_code} {uploaded.text[:500]}")
    public_url = str(uploaded.json().get("browser_download_url", "")).strip()
    if not public_url.startswith("https://"):
        raise RuntimeError("GitHub delivery asset returned no public HTTPS URL")
    print(f"Delivery asset ready: {public_url}")
    return public_url

def proxy_draft_request(data: dict, bearer: str):
    proxy_url = os.getenv("OLDIES_DRAFT_PROXY_URL", "").strip()
    if not proxy_url:
        return None
    headers = {
        "Authorization": f"Bearer {bearer}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    response = None
    for attempt in range(4):
        response = requests.post(proxy_url, headers=headers, json=data, timeout=90)
        if response.status_code < 400:
            return response.json()
        if response.status_code == 429:
            try:
                error_payload = response.json()
            except Exception:
                error_payload = {}
            if isinstance(error_payload, dict) and error_payload.get("code") == "daily_draft_limit":
                print("WordPress daily draft limit already satisfied; no additional draft created.")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "daily_draft_limit",
                    "message": str(error_payload.get("message", "Daily draft limit reached.")),
                }
        if response.status_code not in {429, 502, 503, 504} or attempt == 3:
            break
        delay = 10 * (2**attempt)
        print(f"Draft proxy temporarily returned {response.status_code}; retrying in {delay}s")
        time.sleep(delay)
    raise RuntimeError(f"Draft proxy {response.status_code}: {response.text[:700]}")


def upload_draft(candidate: dict, video: Path, bearer: str, base_url: str):
    data = {
        "artist": candidate["artist"],
        "topic": candidate["topic"],
        "event_date": candidate["event_date"],
        "caption": candidate["caption"],
        "sources": json.dumps(candidate["sources"], ensure_ascii=False),
        "facts": json.dumps(candidate["facts"], ensure_ascii=False),
        "score_breakdown": json.dumps(candidate["score_breakdown"]),
        "audio_title": str(candidate.get("instagram_music_title", "")),
        "audio_artist": str(candidate.get("instagram_music_artist", "")),
        "audio_clip_note": str(candidate.get("instagram_music_clip_note", "")),
    }
    public_url = publish_delivery_asset(candidate, video)
    if public_url:
        data["video_url"] = public_url
        return wordpress_request("PUT", "drafts", bearer, base_url, data=data)
    with video.open("rb") as handle:
        return wordpress_request("POST", "drafts", bearer, base_url, data=data, files={"reel_video": (video.name, handle, "video/mp4")})


def main() -> None:
    bearer = require_env("OLDIES_WP_BEARER")
    base_url = require_env("OLDIES_WP_BASE_URL")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    override = os.getenv("OLDIES_ZERO_COST_DATE", "").strip()
    today = datetime.strptime(override, "%Y-%m-%d").replace(tzinfo=timezone.utc) if override else datetime.now(timezone.utc)
    draft_state = get_draft_state(bearer, base_url)
    if draft_state["daily_limit_reached"]:
        print("Daily DRAFT_REVIEW quota is already satisfied; exiting successfully without rendering another Reel.")
        return
    candidates = research_candidates(draft_state["recent_artists"], today=today)
    candidate = None
    photos, credits = [], []
    photo_errors = []
    for option in candidates:
        for old_photo in OUTPUT.glob("photo-*.jpg"):
            old_photo.unlink()
        try:
            print(f"Trying zero-cost visual candidate: {option['artist']} (score={option['score']})")
            photos, credits = download_commons_photos(option, OUTPUT)
            candidate = option
            break
        except Exception as exc:
            photo_errors.append(f"{option.get('artist', 'Unknown')}: {exc}")
            print(f"Skipping visual candidate: {photo_errors[-1]}")
    if candidate is None:
        raise RuntimeError("No zero-cost candidate had three usable licensed photos. " + " | ".join(photo_errors))
    candidate["image_credits"] = credits
    candidate["pipeline"] = "zero-cost-v1"
    candidate = apply_reel_language(candidate, reel_language())
    voiceover = download_voiceover(OUTPUT)
    voiceover_source = "external_https" if voiceover else "none"
    if not voiceover:
        voiceover = synthesize_google_voice(candidate, OUTPUT)
        if voiceover:
            voiceover_source = str(candidate.get("tts_engine") or "google_tts")
    candidate["voiceover"] = {
        "enabled": bool(voiceover),
        "source": voiceover_source,
    }
    (OUTPUT / "content.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
    video = OUTPUT / "oldies-reels-draft.mp4"
    render(make_scenes(candidate, photos, OUTPUT), video, voiceover=voiceover)

    preview_only = os.getenv("OLDIES_PREVIEW_ONLY", "").strip().lower() in {"1", "true", "yes", "on"}
    if preview_only:
        result = {"success": True, "preview_only": True, "voiceover": bool(voiceover)}
        (OUTPUT / "wordpress-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Preview-only render completed; WordPress draft upload was intentionally skipped.")
        return

    if candidate.get("reels_language") == "en":
        result = {
            "success": True,
            "facebook_global_ready": True,
            "upload_skipped": "facebook_global_delivery_not_connected_in_this_worker",
        }
        (OUTPUT / "wordpress-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("English Global Reel rendered successfully; TR Instagram review upload was intentionally skipped.")
        return

    result = upload_draft(candidate, video, bearer, base_url)
    (OUTPUT / "wordpress-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created approval-only zero-cost draft {result.get('draft', {}).get('id', '')}; no live post was made.")


if __name__ == "__main__":
    main()
