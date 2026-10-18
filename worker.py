#!/usr/bin/env python3
"""Create one zero-cost, approval-only Oldies Radyo Reels draft.

Exact-day This Day In Music discovery and independent evidence feed the
existing photo/timeline renderer. The quarantined entry point is preview-only
for both languages and never reads platform credentials or invokes TTS.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import math
import os
import re
import subprocess
import textwrap
import time
from datetime import date, datetime, timezone
from io import BytesIO
from pathlib import Path

import requests


from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from editorial_quality_gate import check_approved_reel, load_approval, FORBIDDEN_VISUAL_TERMS
from source_evidence import check_turkish_script, check_script
from reels_preview import prepare_preview
from zero_cost import research_candidates
from video_factory import build_timeline, export_capcut_package, render_timeline, write_timeline_files

OUTPUT = Path("output")
WIDTH, HEIGHT, FPS, DURATION = 1080, 1920, 30, 15
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "OldiesRadyoBot/1.0 (https://oldiesradyo.com; info@oldiesradyo.com)"
MAX_VIDEO_BYTES = 100 * 1024 * 1024
MAX_VOICEOVER_BYTES = 20 * 1024 * 1024
JOHN_LENNON_APPROVED_SCRIPT = (
    "23 Eylül bin dokuz yüz yetmiş dört. John Lennon, "
    "'Whatever Gets You Thru the Night' şarkısını yayımladı. "
    "Elton John piyanoda ve geri vokalde ona eşlik etti. "
    "Şarkı, Lennon için ABD'deki ilk solo liste birinciliğini getirdi. "
    "Oldies Radyo. Dinle, beğen, paylaş."
)


def scheduled_turkish_voice(day: date) -> str:
    """Use each female DJ voice once per six scheduled days."""
    first_female_day = date(2026, 9, 29)
    if day < first_female_day:
        return "Charon"
    cycle_day = (day - first_female_day).days % 6
    return {0: "Callirrhoe", 3: "Aoede"}.get(cycle_day, "Charon")

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


def image_matches_artist(image: dict, artist: str, music_title: str = "") -> bool:
    """Require explicit music context for names that also label unrelated subjects."""
    title = str(image.get("title", "")).casefold()
    if FORBIDDEN_VISUAL_TERMS.search(title):
        return False
    # A search result is only a possible photo; the TR preview path requires
    # separately documented identity, era and rights before rendering it.
    tokens = re.sub(r"[^\w]+", " ", artist.casefold()).split()
    if not tokens or not all(re.search(r"\b" + re.escape(token) + r"\b", title)
                             for token in tokens if token != "the"):
        return False
    if re.search(r"\b(?:bootleg|crowd|audience)\b", title):
        return False
    if music_title and re.search(r"\b(?:album|single|lp|vinyl|record|sleeve|cover)\b", title):
        normalized = lambda value: re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()
        if normalized(music_title) not in normalized(title):
            return False
    if artist == "Eagles":
        return bool(
            re.search(r"\beagles\b", title)
            and re.search(r"\b(?:band|concert|musicians|rock group|on stage)\b", title)
        )
    return True


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
            if (image and image["title"] not in seen_titles
                    and image_matches_artist(image, str(candidate["artist"]), str(candidate.get("instagram_music_title", "")))):
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

    if len(paths) < 3:
        raise RuntimeError("Three distinct documented artist photos required; no duplicate crop fallback")
    return paths, credits


def font(size: int, bold: bool = False):
    names = (["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"]
             if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"])
    for path in names:
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    raise RuntimeError("A readable Turkish/English font (DejaVu Sans or Windows Arial) is required")


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
    uk_no1 = bool(re.search(r"No\.?1 in the UK|number one (?:album )?in the (?:UK|United Kingdom)", source, re.I))
    # The chart owner confirms both the date and duration for this event.
    if (str(candidate.get("artist")) == "The Rolling Stones"
            and str(candidate.get("instagram_music_title", "")).casefold().replace("’", "'") == "goat's head soup"
            and str(candidate.get("event_date")) == "1973-09-22"):
        weeks, uk_no1 = 2, True
        chart_source = "https://www.officialcharts.com/chart-news/all-the-number-1-albums__7949/"
        sources = candidate.setdefault("sources", [])
        if chart_source not in sources:
            sources.append(chart_source)
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
        fact1 = f"'{title}' {_turkish_record_noun(candidate)}, İngiltere listelerinde 1 numaraya çıktı."
        fact2 = f"Zirvedeki yerini {weeks} hafta korudu." if weeks else "Liste zirvesine yerleşti."
        closing = "MÜZİK TARİHİNDEN BİR SAYFA"
    elif title and re.search(r"\breleased\b", str(candidate.get("source_text", "")), re.I):
        hook = f"{artist.upper()} • {year}"
        object_noun = "şarkısını" if _turkish_record_noun(candidate) == "şarkısı" else "albümünü"
        fact1 = f"{date_text}: {artist}, '{title}' {object_noun} yayımladı."
        fact2 = ("Şarkı daha sonra ABD'de Lennon'a ilk solo liste birinciliğini getirdi."
                 if artist == "John Lennon" and re.search(r"first solo No\.?1 single in the US", str(candidate.get("source_text", "")), re.I)
                 else original_facts[1])
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
    """Use the evidence-linked TR script; never translate discovery prose as fact."""
    return [("tr-TR", check_turkish_script(candidate))]


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


class VoiceoverQualityError(RuntimeError):
    """A draft must not be delivered when its story or timing is unusable."""


def _turkish_number(value: int) -> str:
    ones = ["", "bir", "iki", "üç", "dört", "beş", "altı", "yedi", "sekiz", "dokuz"]
    tens = ["", "on", "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan"]
    if value < 10:
        return ones[value] or "sıfır"
    if value < 100:
        return " ".join(part for part in (tens[value // 10], ones[value % 10]) if part)
    if value < 1000:
        return " ".join(part for part in (
            ("yüz" if value // 100 == 1 else ones[value // 100] + " yüz"),
            _turkish_number(value % 100) if value % 100 else "",
        ) if part)
    if value < 10000:
        return " ".join(part for part in (
            ("bin" if value // 1000 == 1 else ones[value // 1000] + " bin"),
            _turkish_number(value % 1000) if value % 1000 else "",
        ) if part)
    raise VoiceoverQualityError("Unsupported year in Turkish announcement")


def _spoken_turkish_date(event_date: str) -> str:
    try:
        date = datetime.strptime(event_date, "%Y-%m-%d")
    except ValueError as exc:
        raise VoiceoverQualityError("Event date is missing or invalid") from exc
    months = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    return f"{_turkish_number(date.day).capitalize()} {months[date.month]} {_turkish_number(date.year)}"


def build_turkish_gemini_script(candidate: dict) -> str:
    """Compatibility adapter: researched opening/story, with separate closing."""
    from source_evidence import EvidenceError
    try:
        check_turkish_script(candidate)
    except EvidenceError as exc:
        raise VoiceoverQualityError(str(exc)) from exc
    return candidate["story_tr"]["opening"] + " " + candidate["story_tr"]["narrative"]


def turkish_gemini_style_prompt(candidate: dict) -> str:
    artist = re.sub(r"\s+", " ", str(candidate.get("artist", "")).strip())
    title = re.sub(r"\s+", " ", str(candidate.get("instagram_music_title", "")).strip())
    pronunciation = (
        f"{artist} adının sonuna Türkçe ek veya fazladan bir hece getirme. "
        if artist else ""
    )
    if title:
        pronunciation += (
            f"İngilizce şarkı veya albüm adını kendi dilindeki telaffuzuyla "
            f"bir bütün olarak söyle: {title}. Türkçeye dönerken cümleyi doğal sürdür. "
        )
    return (
        "Verilen metni aynen, yalnızca bir kez oku; yeni sözcük veya cümle ekleme. "
        "Deneyimli, sıcak ve canlı bir Türkçe radyo DJ'i gibi dinleyiciye anlat; "
        "haber spikeri tonundan ve tekdüze okumadan kaçın. Türkçe cümleleri doğal "
        f"vurgu ve gramerle söyle. {pronunciation}"
        "Anlaşılır, canlı tempoda yaklaşık dokuz-on saniye; acele edip kelimeleri yutma."
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


def make_timeline_scenes(candidate: dict, photos: list[Path], timeline: list[dict], directory: Path) -> list[Path]:
    """Build one visual beat per voiceover timing while preserving the approved design language."""
    artist = str(candidate.get("artist", "Oldies Radyo")).strip() or "Oldies Radyo"
    title = str(candidate.get("instagram_music_title", "")).strip()
    language = str(candidate.get("reels_language", "tr"))
    paths: list[Path] = []
    for index, item in enumerate(timeline, start=1):
        photo = photos[(index - 1) % len(photos)]
        canvas = cover_photo(photo).convert("RGBA")
        add_gradient(canvas)
        if language == "en":
            accent = "ON THIS DAY IN MUSIC" if index == 1 else ("OLDIES RADYO • MUSIC & MEMORIES" if index == len(timeline) else "THE STORY")
        else:
            accent = "BUGÜN MÜZİK TARİHİNDE" if index == 1 else ("OLDIES RADYO • DİNLE • BEĞEN • PAYLAŞ" if index == len(timeline) else "HİKÂYE DEVAM EDİYOR")
        if candidate.get("photo_disclaimer"):
            accent = str(candidate["photo_disclaimer"])
        if index == 1:
            headline = str(candidate.get("event_headline") or candidate.get("hook") or artist)
        elif title and index % 2 == 0:
            headline = title
        else:
            headline = artist
        subline = textwrap.shorten(str(item.get("text", "")), width=150, placeholder="…")
        draw_text_block(ImageDraw.Draw(canvas), headline, subline, accent)
        path = directory / f"timeline-scene-{index:02d}.jpg"
        canvas.convert("RGB").save(path, "JPEG", quality=95, optimize=True)
        paths.append(path)
    return paths



def build_english_dj_script(candidate: dict) -> str:
    if candidate.get("reels_language") != "en":
        raise VoiceoverQualityError("English narration required")
    return check_script(candidate)


def _google_tts_bytes(
    *,
    text: str,
    language: str,
    voice_name: str,
    project: str,
    token: str,
    ssml: bool = False,
    speaking_rate: float = 1.0,
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
            "input": {"ssml" if ssml else "text": text},
            "voice": {"languageCode": language, "name": voice_name},
            "audioConfig": {"audioEncoding": "MP3", "speakingRate": speaking_rate},
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
    model_name: str = "gemini-2.5-pro-tts",
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
                "modelName": model_name,
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


def _audio_duration(path: Path) -> float:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(probe.stdout.strip())


def _silence_mp3(directory: Path, name: str, seconds: float) -> Path:
    target = directory / name
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", str(seconds),
         "-c:a", "libmp3lame", "-b:a", "192k", str(target)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return target


def synthesize_google_voice(candidate: dict, directory: Path) -> Path | None:
    """Existing opt-in provider; full evidenced script at natural speed, no retries.

    The preview entry point never calls this paid-capable adapter.
    """
    enabled = os.getenv("OLDIES_TTS_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return None
    script = check_script(candidate)
    from google.auth import default as google_auth_default
    from google.auth.transport.requests import Request as GoogleAuthRequest
    credentials, detected = google_auth_default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credentials.refresh(GoogleAuthRequest())
    project = os.getenv("OLDIES_GCP_PROJECT", "").strip() or str(detected or "").strip()
    if not project:
        raise VoiceoverQualityError("Google project missing")
    mode = candidate["reels_language"]
    voice = (os.getenv("OLDIES_GEMINI_TTS_VOICE", "Charon").strip() or "Charon")
    if voice == "auto":
        voice = scheduled_turkish_voice(datetime.now(timezone.utc).date())
    if voice not in {"Charon", "Callirrhoe", "Aoede"}:
        raise VoiceoverQualityError("Approved natural DJ voice required")
    target = directory / "voiceover-google.mp3"
    raw = _gemini_tts_bytes(text=script, prompt=(
        "Warm, experienced radio DJ. Natural conversational speed. Read every word exactly. "
        "No added speech, music or sound effects. A brief natural pause before the station closing."
    ), language="tr-TR" if mode == "tr" else "en-AU", voice_name=voice,
        project=project, token=str(credentials.token), model_name="gemini-2.5-pro-tts")
    target.write_bytes(raw)
    from media_evidence import inspect_audio
    measured = inspect_audio(target)
    candidate["voiceover_duration_seconds"] = measured["decoded_seconds"]
    return target


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
    raise VoiceoverQualityError("Use the evidence-linked 25-30s timeline renderer; silent legacy render disabled")


def publish_delivery_asset(candidate: dict, video: Path) -> str:
    check_approved_reel(candidate, video, load_approval(os.getenv("OLDIES_EDITORIAL_APPROVAL_MANIFEST", "").strip()))
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

    artist_slug = re.sub(r"[^a-z0-9]+", "-", str(candidate.get("artist", "")).lower()).strip("-")[:60] or "oldies"
    event_date = re.sub(r"[^0-9-]", "", str(candidate.get("event_date", ""))) or "undated"
    run_id = re.sub(r"[^0-9]", "", os.getenv("GITHUB_RUN_ID", "")) or str(int(time.time()))
    attempt = re.sub(r"[^0-9]", "", os.getenv("GITHUB_RUN_ATTEMPT", "")) or "1"
    asset_name = f"{event_date}-{artist_slug}-{run_id}-{attempt}.mp4"

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
    check_approved_reel(candidate, video, load_approval(os.getenv("OLDIES_EDITORIAL_APPROVAL_MANIFEST", "").strip()))
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


def publish_facebook_global(candidate: dict, video: Path, bearer: str, base_url: str) -> dict:
    """Deliver one rendered English Reel to the isolated Facebook Global companion."""
    check_approved_reel(candidate, video, load_approval(os.getenv("OLDIES_EDITORIAL_APPROVAL_MANIFEST", "").strip()))
    public_url = publish_delivery_asset(candidate, video)
    if not public_url:
        raise RuntimeError("Facebook Global delivery requires the GitHub reels-delivery asset")

    digest = hashlib.sha256(video.read_bytes()).hexdigest()
    artist = re.sub(r"\s+", " ", str(candidate.get("artist", "")).strip())
    artist_slug = re.sub(r"[^a-z0-9]+", "-", artist.casefold()).strip("-")[:48] or "oldies"
    event_date = re.sub(r"[^0-9-]", "", str(candidate.get("event_date", ""))) or "undated"
    topic_seed = f"{candidate.get('topic', '')}|{candidate.get('event_date', '')}|{artist}"
    topic_key = hashlib.sha256(topic_seed.encode("utf-8")).hexdigest()[:10]
    content_id = f"global-en-{event_date}-{artist_slug}-{topic_key}"[:180]

    title = re.sub(
        r"\s+",
        " ",
        str(candidate.get("event_headline") or candidate.get("hook") or artist or "Oldies Radyo Music History"),
    ).strip()[:120]
    caption = str(candidate.get("caption", "")).strip()
    if "oldiesradyo.com/en/" not in caption:
        caption = (caption + "\n\nMore music history: oldiesradyo.com/en/").strip()

    endpoint = f"{base_url.rstrip('/')}/wp-json/oldies-global/v1/publish-url"
    headers = {
        "Authorization": f"Bearer {bearer}",
        "X-Oldies-Reels-Secret": bearer,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
    }
    payload = {
        "content_id": content_id,
        "video_url": public_url,
        "sha256": digest,
        "caption": caption,
        "title": title,
        "dry_run": False,
    }
    response = requests.post(endpoint, headers=headers, json=payload, timeout=240)
    if response.status_code >= 400:
        raise RuntimeError(f"Facebook Global publish {response.status_code}: {response.text[:700]}")
    try:
        result = response.json()
    except Exception as exc:
        raise RuntimeError(f"Facebook Global returned invalid JSON: {response.text[:500]}") from exc
    if not isinstance(result, dict) or not result.get("success"):
        raise RuntimeError(f"Facebook Global publish did not confirm success: {str(result)[:700]}")
    result["delivery_url"] = public_url
    result["content_id"] = content_id
    return result


def main() -> None:
    language = reel_language()
    override = os.getenv("OLDIES_ZERO_COST_DATE", "").strip()
    today = datetime.strptime(override, "%Y-%m-%d").replace(tzinfo=timezone.utc) if override else datetime.now(timezone.utc)
    root = Path(__file__).resolve().parent
    def render_preview(candidate, photos, voice, target):
        script = check_script(candidate)
        timeline = build_timeline(script, voice)
        scenes = make_timeline_scenes(candidate, photos, timeline, target.parent)
        write_timeline_files(timeline, target.parent)
        render_timeline(scenes=scenes, timeline=timeline, target=target, voiceover=voice,
                        width=WIDTH, height=HEIGHT, fps=FPS, max_video_bytes=MAX_VIDEO_BYTES)
    output = root / "output" / f"{language}-preview"
    result = prepare_preview(root=root, output=output, today=today, language=language,
                             packet_path=os.getenv("OLDIES_EDITORIAL_PACKET", "").strip(),
                             discover=research_candidates, render=render_preview)
    print(json.dumps(result, ensure_ascii=False))
    if not result["video_created"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
