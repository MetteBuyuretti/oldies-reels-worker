#!/usr/bin/env python3
"""Research, render and upload one approval-only Oldies Radyo Reels draft."""

from __future__ import annotations

import base64
import json
import os
import re
import subprocess
import textwrap
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

OUTPUT = Path("output")
WIDTH, HEIGHT, FPS, DURATION = 1080, 1920, 30, 18
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


def research_candidate(client: OpenAI, recent_artists: list[str]) -> dict:
    today = datetime.utcnow()
    prompt = f"""
Bugün {today:%d %B %Y}. Oldies Radyo'nun Türkçe Instagram Reels hesabı için
"müzik tarihinde bugün" araştırması yap. 1950'ler-1990'lar pop, rock, soul ve
disco kitlesine uygun 5 aday bul. Yalnızca yabancı, güvenilir HTTPS kaynakları
kullan; Türkçe siteleri ve .tr alan adlarını kullanma. Her iddia için kaynak
sayfası gerçekten o bilgiyi desteklesin. Şu sanatçıları tekrar etme:
{', '.join(recent_artists) if recent_artists else 'yok'}.

Yalnızca JSON dizi döndür. Her öğede şu alanlar olsun:
artist, topic, event_date (YYYY-MM-DD), hook, facts (en az 2 kısa Türkçe bilgi),
sources (en az 2 farklı alan adından tam URL), caption (Türkçe, 80-900 karakter,
sonunda tek soru ve en fazla 5 hashtag), visual_prompt (İngilizce; 9:16 editoryal
arka plan, yazı/logo/kapak görseli ve sanatçının birebir yüzü yok),
instagram_music_title (Instagram uygulamasında aranacak gerçek şarkı),
instagram_music_artist, instagram_music_clip_note (önerilen 10-15 saniyelik bölüm),
score_breakdown: date_relevance 0-30, audience_fit 0-25,
source_confidence 0-20, visual_strength 0-15, freshness 0-10.
Olayın ay ve günü bugünün ay ve günüyle aynı olmalı. Uydurma bilgi verme.
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
        try:
            event_date = datetime.strptime(str(candidate.get("event_date")), "%Y-%m-%d")
        except ValueError:
            continue
        if (
            event_date.strftime("%m-%d") == today.strftime("%m-%d")
            and len(candidate["sources"]) >= 2
            and len(facts) >= 2
            and candidate["score"] >= 80
            and 80 <= len(str(candidate.get("caption", ""))) <= 900
        ):
            accepted.append(candidate)
    if not accepted:
        raise RuntimeError("No candidate passed the source and quality policy")
    return max(accepted, key=lambda item: item["score"])


def generate_background(client: OpenAI, candidate: dict, target: Path) -> None:
    prompt = (
        str(candidate["visual_prompt"])
        + " Vertical 9:16, sophisticated vintage radio editorial art, deep red, black and warm gold, "
          "cinematic grain, strong negative space for large typography, no words, no letters, no logo, "
          "no album artwork, no exact celebrity likeness."
    )
    response = client.images.generate(
        model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2"),
        prompt=prompt,
        size="1024x1536",
        quality="high",
    )
    target.write_bytes(base64.b64decode(response.data[0].b64_json))


def font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


def fit_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, start: int, minimum: int = 40):
    size = start
    while size >= minimum:
        fnt = font(size, True)
        lines = textwrap.wrap(text, width=max(8, int(max_width / (size * 0.58))))
        if all(draw.textbbox((0, 0), line, font=fnt)[2] <= max_width for line in lines):
            return fnt, lines
        size -= 2
    return font(minimum, True), textwrap.wrap(text, width=22)


def make_cards(candidate: dict, directory: Path) -> list[Path]:
    cards = [
        ("BUGÜN MÜZİK TARİHİNDE", datetime.strptime(candidate["event_date"], "%Y-%m-%d").strftime("%d.%m.%Y")),
        (str(candidate["artist"]).upper(), str(candidate["topic"]).upper()),
        (str(candidate["hook"]).upper(), str(candidate["facts"][0])),
        ("SENİN YORUMUN NE?", "@oldiesradyo"),
    ]
    paths = []
    for index, (headline, subline) in enumerate(cards):
        canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((70, 1150, 1010, 1710), radius=24, fill=(10, 8, 9, 218), outline=(221, 180, 64, 230), width=3)
        draw.rectangle((70, 1150, 82, 1710), fill=(204, 32, 44, 255))
        title_font, title_lines = fit_text(draw, headline, 800, 86)
        y = 1220
        for line in title_lines[:3]:
            draw.text((130, y), line, font=title_font, fill=(255, 244, 215, 255))
            y += title_font.size + 14
        sub_font, sub_lines = fit_text(draw, subline, 800, 52, 34)
        y += 18
        for line in sub_lines[:3]:
            draw.text((130, y), line, font=sub_font, fill=(239, 239, 239, 255))
            y += sub_font.size + 10
        draw.text((130, 1645), "OLDIES RADYO", font=font(34, True), fill=(221, 180, 64, 255))
        path = directory / f"card-{index}.png"
        canvas.save(path)
        paths.append(path)
    return paths


def render(background: Path, cards: list[Path], target: Path) -> None:
    inputs = ["-loop", "1", "-i", str(background)]
    for card in cards:
        inputs += ["-loop", "1", "-i", str(card)]
    graph = (
        f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT},"
        f"zoompan=z='min(zoom+0.00035,1.07)':d={DURATION*FPS}:s={WIDTH}x{HEIGHT}:fps={FPS},"
        "eq=brightness=-0.06:saturation=0.9[bg];"
        "[bg][1:v]overlay=enable='between(t,0,4.5)'[v1];"
        "[v1][2:v]overlay=enable='between(t,4.5,9)'[v2];"
        "[v2][3:v]overlay=enable='between(t,9,13.5)'[v3];"
        "[v3][4:v]overlay=enable='between(t,13.5,18)'[v]"
    )
    command = ["ffmpeg", "-y", *inputs, "-filter_complex", graph, "-map", "[v]", "-an", "-t", str(DURATION), "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)]
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
    recent = get_recent_artists(bearer, base_url)
    candidate = research_candidate(client, recent)
    (OUTPUT / "content.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
    background = OUTPUT / "background.png"
    video = OUTPUT / "oldies-reels-draft.mp4"
    generate_background(client, candidate, background)
    cards = make_cards(candidate, OUTPUT)
    render(background, cards, video)
    result = upload_draft(candidate, video, bearer, base_url)
    (OUTPUT / "wordpress-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created approval-only draft {result.get('draft', {}).get('id', '')}; no live post was made.")


if __name__ == "__main__":
    main()
