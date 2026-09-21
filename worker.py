#!/usr/bin/env python3
"""Create one zero-cost, approval-only Oldies Radyo Reels draft.

The research path uses only Wikimedia/Wikidata/Wikipedia open data. No OpenAI
or other paid model API is imported or called. Existing Commons -> FFmpeg ->
WordPress DRAFT_REVIEW behavior is preserved.
"""
from __future__ import annotations

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
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

from zero_cost import research_candidates

OUTPUT = Path("output")
WIDTH, HEIGHT, FPS, DURATION = 1080, 1920, 30, 18
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
    draw.rounded_rectangle((72, 1198, 1008, 1256), radius=22, fill=(12, 12, 15, 205))
    accent_font = font(25, True)
    draw.text((104, 1212), accent, font=accent_font, fill=(236, 193, 77, 255))

    title_font, title_lines = fit_text(draw, headline.upper(), 880, 84, 46)
    y = 1300
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
    draw.line((96, 1810, 984, 1810), fill=(255, 255, 255, 95), width=2)
    draw.text((96, 1830), "OLDIES RADYO", font=font(34, True), fill=(236, 193, 77, 255))
    draw.text((790, 1837), "oldiesradyo.com", font=font(22), fill=(245, 245, 245, 230))


def make_scenes(candidate: dict, photos: list[Path], directory: Path) -> list[Path]:
    artist = str(candidate["artist"])
    hook = str(candidate.get("event_headline") or candidate.get("hook") or artist)
    facts = list(candidate.get("facts") or ["", ""])
    while len(facts) < 2:
        facts.append("")
    closing = str(candidate.get("closing_headline") or f"{artist} • OLDIES RADYO")

    scenes = [
        (hook, str(candidate["date_label"]), "OLDIES RADYO • MÜZİK TARİHİNDE BUGÜN"),
        (artist, str(facts[0]), "HİKÂYENİN DETAYI"),
        (closing, str(facts[1]), "OLDIES RADYO • DİNLE • HATIRLA"),
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
        inputs += ["-loop", "1", "-t", "6.6", "-i", str(scene)]

    graph = (
        f"[0:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00050,1.08)':d=198:s={WIDTH}x{HEIGHT}:fps={FPS}[a];"
        f"[1:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00036,1.065)':d=198:s={WIDTH}x{HEIGHT}:fps={FPS}[b];"
        f"[2:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00046,1.075)':d=198:s={WIDTH}x{HEIGHT}:fps={FPS}[c];"
        "[a][b]xfade=transition=fade:duration=0.65:offset=5.75[x];"
        "[x][c]xfade=transition=smoothleft:duration=0.70:offset=11.45[v]"
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
    voiceover = download_voiceover(OUTPUT)
    candidate["voiceover"] = {
        "enabled": bool(voiceover),
        "source": "external_https" if voiceover else "none",
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

    result = upload_draft(candidate, video, bearer, base_url)
    (OUTPUT / "wordpress-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created approval-only zero-cost draft {result.get('draft', {}).get('id', '')}; no live post was made.")


if __name__ == "__main__":
    main()
