#!/usr/bin/env python3
"""Research, render and upload one approval-only Oldies Radyo Reels draft."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import subprocess
import textwrap
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

OUTPUT = Path("output")
WIDTH, HEIGHT, FPS, DURATION = 1080, 1920, 30, 18
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "OldiesRadyoReelsWorker/2.0 (https://oldiesradyo.com)"
SCORE_LIMITS = {
    "date_relevance": 30,
    "audience_fit": 25,
    "source_confidence": 20,
    "visual_strength": 15,
    "freshness": 10,
}


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment value: {name}")
    return value


def wordpress_request(method: str, path: str, bearer: str, base_url: str, **kwargs):
    endpoint = f"{base_url.rstrip('/')}/?rest_route=/oldies/v1/instagram/reels/{path.lstrip('/')}"
    headers = kwargs.pop("headers", {})
    headers.update({"Authorization": f"Bearer {bearer}", "Accept": "application/json"})
    response = requests.request(method, endpoint, headers=headers, timeout=180, **kwargs)
    if response.status_code >= 400:
        raise RuntimeError(f"WordPress {response.status_code}: {response.text[:700]}")
    return response.json()


def get_recent_artists(bearer: str, base_url: str) -> list[str]:
    data = wordpress_request("GET", "drafts", bearer, base_url)
    return sorted({str(item.get("artist", "")).strip() for item in data.get("drafts", []) if item.get("artist")})[:30]


def extract_json(text: str):
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("["), cleaned.rfind("]")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def valid_foreign_sources(values) -> list[str]:
    result, hosts = [], set()
    for value in values if isinstance(values, list) else []:
        url = str(value).strip()
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or not host or host.endswith(".tr") or host in hosts:
            continue
        hosts.add(host)
        result.append(url)
    return result


def normalized_score(value) -> dict[str, int]:
    value = value if isinstance(value, dict) else {}
    return {key: max(0, min(limit, int(value.get(key, 0)))) for key, limit in SCORE_LIMITS.items()}


def research_candidates(client: OpenAI, recent_artists: list[str]) -> list[dict]:
    today = datetime.now(timezone.utc)
    prompt = f"""
Bugün {today:%d %B %Y}. Oldies Radyo'nun Türkçe Instagram Reels hesabı için
"müzik tarihinde bugün" araştırması yap. 1950'ler-1990'lar pop, rock, soul ve
disco kitlesine uygun 5 aday bul. Yalnızca yabancı, güvenilir HTTPS kaynakları
kullan; Türkçe siteleri ve .tr alan adlarını kullanma. Her iddia için kaynak
sayfası gerçekten o bilgiyi desteklesin. Şu sanatçıları tekrar etme:
{', '.join(recent_artists) if recent_artists else 'yok'}.

Yalnızca JSON dizi döndür. Her öğede şu alanlar olsun:
artist, topic, event_date (YYYY-MM-DD), date_label (ör. "2 EYLÜL 1946'DA DOĞDU"),
hook, facts (en az 2 kısa Türkçe bilgi), sources (en az 2 farklı alan adından tam
URL), caption (Türkçe, 80-900 karakter, sonunda tek soru ve en fazla 5 hashtag),
image_search_queries (Wikimedia Commons'ta sanatçının farklı dönem/ortamlardaki
gerçek fotoğraflarını bulmak için İngilizce 3 farklı kısa arama; sadece sanatçı
adı + yıl, konser, portre gibi sözcükler), instagram_music_title (Instagram
uygulamasında aranacak gerçek şarkı), instagram_music_artist,
instagram_music_clip_note (önerilen 10-15 saniyelik bölüm), score_breakdown:
date_relevance 0-30, audience_fit 0-25, source_confidence 0-20,
visual_strength 0-15, freshness 0-10.
Olayın ay ve günü bugünün ay ve günüyle aynı olmalı. date_label olayın anlamını
açıkça söylemeli; tarihi tek başına yazma. Sanatçı veya grup tanınabilir olmalı
ve Wikimedia Commons'ta en az üç farklı gerçek fotoğrafı bulunabilmeli. Uydurma
bilgi verme.
"""
    response = client.responses.create(
        model=os.getenv("OPENAI_RESEARCH_MODEL", "gpt-5.4"),
        tools=[{"type": "web_search"}],
        input=prompt,
    )
    candidates = extract_json(response.output_text)
    accepted = []
    for candidate in candidates if isinstance(candidates, list) else []:
        candidate["sources"] = valid_foreign_sources(candidate.get("sources"))
        candidate["score_breakdown"] = normalized_score(candidate.get("score_breakdown"))
        candidate["score"] = sum(candidate["score_breakdown"].values())
        facts = candidate.get("facts") if isinstance(candidate.get("facts"), list) else []
        queries = candidate.get("image_search_queries") if isinstance(candidate.get("image_search_queries"), list) else []
        try:
            event_date = datetime.strptime(str(candidate.get("event_date")), "%Y-%m-%d")
        except ValueError:
            continue
        if (
            event_date.strftime("%m-%d") == today.strftime("%m-%d")
            and len(candidate["sources"]) >= 2
            and len(facts) >= 2
            and len(queries) >= 3
            and candidate["score"] >= 80
            and 80 <= len(str(candidate.get("caption", ""))) <= 900
        ):
            accepted.append(candidate)
    if not accepted:
        raise RuntimeError("No candidate passed the source and quality policy")
    return sorted(accepted, key=lambda item: item["score"], reverse=True)


def clean_meta(value) -> str:
    raw = value.get("value", "") if isinstance(value, dict) else str(value or "")
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def commons_search(query: str) -> list[dict]:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{query} filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": 20,
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
    if max(int(info.get("width", 0)), int(info.get("height", 0))) < 320:
        return None
    return {
        "title": page.get("title", ""),
        "url": info.get("thumburl") or info.get("url", ""),
        "description_url": info.get("descriptionurl", ""),
        "license": license_name or usage_terms,
        "creator": clean_meta(meta.get("Artist")) or "Unknown",
        "credit": clean_meta(meta.get("Credit")),
    }


def download_commons_photos(candidate: dict, directory: Path) -> tuple[list[Path], list[dict]]:
    paths, credits, seen_titles, seen_hashes = [], [], set(), set()
    queries = list(candidate["image_search_queries"][:3]) + [str(candidate["artist"])]
    for query in queries:
        choices = []
        for page in commons_search(str(query)):
            image = usable_image(page)
            if image and image["title"] not in seen_titles:
                choices.append(image)
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
        raise RuntimeError(f"Three different artist photos were required; only {len(paths)} were found")
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
    draw.rounded_rectangle((72, 1260, 1008, 1305), radius=16, fill=(204, 34, 43, 245))
    draw.text((104, 1266), accent, font=font(27, True), fill=(255, 246, 221, 255))
    title_font, title_lines = fit_text(draw, headline.upper(), 870, 88)
    y = 1342
    for line in title_lines:
        draw.text((96, y), line, font=title_font, fill=(255, 248, 231, 255), stroke_width=1, stroke_fill=(0, 0, 0, 170))
        y += title_font.size + 10
    sub_font, sub_lines = fit_text(draw, subline, 870, 45, 32)
    y += 12
    for line in sub_lines[:3]:
        draw.text((98, y), line, font=sub_font, fill=(232, 229, 222, 255))
        y += sub_font.size + 8
    draw.text((96, 1833), "OLDIES RADYO", font=font(30, True), fill=(232, 187, 61, 255))
    draw.text((790, 1833), "@oldiesradyo", font=font(25), fill=(245, 245, 245, 235))


def make_scenes(candidate: dict, photos: list[Path], directory: Path) -> list[Path]:
    scenes = [
        (str(candidate["artist"]), str(candidate["date_label"]), "BUGÜN MÜZİK TARİHİNDE"),
        (str(candidate["hook"]), str(candidate["facts"][0]), "BİR DÖNEME DAMGA VURDU"),
        ("SENİN FAVORİN HANGİSİ?", str(candidate["facts"][1]), "HATIRLIYORUZ • DİNLİYORUZ"),
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


def render(scenes: list[Path], target: Path) -> None:
    inputs = []
    for scene in scenes:
        inputs += ["-loop", "1", "-t", "6.5", "-i", str(scene)]
    graph = (
        f"[0:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00045,1.075)':d=195:s={WIDTH}x{HEIGHT}:fps={FPS}[a];"
        f"[1:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00040,1.07)':d=195:s={WIDTH}x{HEIGHT}:fps={FPS}[b];"
        f"[2:v]scale={WIDTH}:{HEIGHT},zoompan=z='min(zoom+0.00045,1.075)':d=195:s={WIDTH}x{HEIGHT}:fps={FPS}[c];"
        "[a][b]xfade=transition=fade:duration=0.75:offset=5.75[x];"
        "[x][c]xfade=transition=fade:duration=0.75:offset=11.5[v]"
    )
    command = [
        "ffmpeg", "-y", *inputs, "-filter_complex", graph, "-map", "[v]", "-an",
        "-t", str(DURATION), "-r", str(FPS), "-c:v", "libx264", "-preset", "medium",
        "-crf", "19", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target),
    ]
    subprocess.run(command, check=True)


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
    with video.open("rb") as handle:
        return wordpress_request("POST", "drafts", bearer, base_url, data=data, files={"reel_video": (video.name, handle, "video/mp4")})


def main() -> None:
    api_key = require_env("OPENAI_API_KEY")
    bearer = require_env("OLDIES_WP_BEARER")
    base_url = require_env("OLDIES_WP_BASE_URL")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    client = OpenAI(api_key=api_key)
    candidates = research_candidates(client, get_recent_artists(bearer, base_url))
    candidate = None
    photos, credits = [], []
    photo_errors = []
    for option in candidates:
        for old_photo in OUTPUT.glob("photo-*.jpg"):
            old_photo.unlink()
        try:
            print(f"Trying visual candidate: {option['artist']}")
            photos, credits = download_commons_photos(option, OUTPUT)
            candidate = option
            break
        except Exception as exc:
            photo_errors.append(f"{option.get('artist', 'Unknown')}: {exc}")
            print(f"Skipping visual candidate: {photo_errors[-1]}")
    if candidate is None:
        raise RuntimeError("No candidate had three usable photos. " + " | ".join(photo_errors))
    candidate["image_credits"] = credits
    (OUTPUT / "content.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
    video = OUTPUT / "oldies-reels-draft.mp4"
    render(make_scenes(candidate, photos, OUTPUT), video)
    result = upload_draft(candidate, video, bearer, base_url)
    (OUTPUT / "wordpress-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created approval-only draft {result.get('draft', {}).get('id', '')}; no live post was made.")


if __name__ == "__main__":
    main()
