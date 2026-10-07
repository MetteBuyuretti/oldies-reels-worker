"""English DJ narration and fail-closed audio gates for Facebook Global only."""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path


def build_dj_script(candidate: dict) -> str:
    artist = re.sub(r"\s+", " ", str(candidate.get("artist", ""))).strip()
    year = str(candidate.get("event_date", ""))[:4]
    title = re.sub(r"\s+", " ", str(candidate.get("instagram_music_title", ""))).strip()
    if not artist or not re.fullmatch(r"\d{4}", year):
        raise RuntimeError("Facebook DJ copy requires an artist and verified event year")
    kind = candidate.get("kind", "events")
    if kind == "births":
        story = f"Born on this day in {year}: {artist}. A familiar name from the golden years of music."
    elif kind == "deaths":
        story = f"Remembering {artist}, who left us on this day in {year}. The records and the memories live on."
    else:
        # Prefer a complete, short sourced sentence; never read a truncated caption.
        source = re.sub(r"\s+", " ", str(candidate.get("source_text", ""))).strip()
        first = re.split(r"(?<=[.!?])\s+(?=[A-Z])", source, maxsplit=1)[0]
        if first and artist.casefold() in first.casefold() and 12 <= len(first.split()) <= 28:
            story = first.rstrip(".!?") + "."
        elif title:
            story = f"On this day in {year}, {artist} made music history with '{title}'."
        else:
            story = f"On this day in {year}, {artist} made music history. Another moment from the golden years of music."
    script = f"{story} Oldies Radyo. Great records, great stories."
    if len(script.split()) > 38 or re.search(r"[çğıöşüÇĞİÖŞÜ]", script):
        raise RuntimeError("Facebook DJ script must be short and English")
    return script


def synthesize_dj(candidate: dict, directory: Path, project: str, token: str, synthesize) -> Path:
    script = build_dj_script(candidate)
    prompt = (
        "Speak in English as a warm, experienced music radio DJ talking to one listener. "
        "Friendly, conversational, relaxed confidence, lively natural phrasing; never a newsreader "
        "or robotic announcer. Start directly with the story. Read the supplied script exactly once "
        "in one continuous take, approximately twelve to fourteen seconds, with clear words. "
        "Pause briefly before the station name. Pronounce Oldies Radyo as Oldeez Radio, "
        "without stretching vowels. No music, singing, sound effects or added words."
    )
    # Reuse the existing authenticated Gemini TTS call and account. No new service or key.
    raw = synthesize(text=script, prompt=prompt, language="en-US", voice_name="Charon",
                     project=project, token=token, model_name="gemini-2.5-pro-tts")
    if not raw or len(raw) > 20 * 1024 * 1024:
        raise RuntimeError("Facebook English DJ TTS returned invalid audio bytes")
    path = directory / "voiceover-facebook-en.mp3"
    path.write_bytes(raw)
    try:
        qc = inspect_audio(path)
        if not 9.5 <= qc["duration_seconds"] <= 14.4:
            raise RuntimeError(f"Facebook DJ narration must fit 15 seconds: {qc['duration_seconds']:.2f}s")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    candidate.update(dj_script_en=script, tts_language="en-US", tts_voice="Charon",
                     tts_engine="gemini-2.5-pro-tts-facebook-dj",
                     voiceover_duration_seconds=qc["duration_seconds"])
    print(f"English DJ voice-over generated: Charon, {qc['duration_seconds']:.2f}s")
    return path


def inspect_audio(path: Path) -> dict:
    if not path.is_file() or not path.stat().st_size:
        raise RuntimeError("Silent publish blocked: audio file is missing or empty")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-count_packets", "-show_streams", "-show_format", "-of", "json", str(path)],
        check=True, capture_output=True, text=True, timeout=60,
    )
    data = json.loads(probe.stdout)
    audio = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    if not audio or int(audio[0].get("nb_read_packets") or 0) <= 0:
        raise RuntimeError("Silent publish blocked: no populated audio stream (audio:0kB)")
    duration = float(audio[0].get("duration") or data.get("format", {}).get("duration") or 0)
    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError("Silent publish blocked: invalid audio duration")
    decoded = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, timeout=60,
    )
    mean = re.search(r"mean_volume:\s*([-\d.]+) dB", decoded.stderr)
    peak = re.search(r"max_volume:\s*([-\d.]+) dB", decoded.stderr)
    if (decoded.returncode or not mean or not peak
            or float(mean.group(1)) <= -60 or float(peak.group(1)) <= -50):
        raise RuntimeError("Silent publish blocked: audio cannot be decoded or contains no audible signal")
    return {"audio_stream_detected": True, "audio_packets": int(audio[0]["nb_read_packets"]),
            "audio_codec": audio[0]["codec_name"], "duration_seconds": round(duration, 3),
            "mean_volume_db": float(mean.group(1)), "max_volume_db": float(peak.group(1)),
            "streams": data["streams"]}


def require_voiceover(candidate: dict, voiceover: Path | None) -> None:
    if (not voiceover or not str(candidate.get("tts_language", "")).startswith("en-")
            or not candidate.get("dj_script_en")):
        raise RuntimeError("Silent publish blocked: generated English DJ voice-over is mandatory")
    inspect_audio(voiceover)


def validate_media(video: Path, candidate: dict) -> dict:
    if (not candidate.get("voiceover", {}).get("enabled")
            or not str(candidate.get("tts_language", "")).startswith("en-")
            or not candidate.get("dj_script_en")):
        raise RuntimeError("Silent publish blocked: English DJ voice-over metadata is missing")
    qc = inspect_audio(video)
    visual = next((s for s in qc.pop("streams") if s.get("codec_type") == "video"), {})
    width, height = int(visual.get("width", 0)), int(visual.get("height", 0))
    if not width or width * 16 != height * 9:
        raise RuntimeError("Facebook Global MP4 must retain the 9:16 visual template")
    duration = float(visual.get("duration") or qc["duration_seconds"])
    if not 10 <= duration <= 15.5:
        raise RuntimeError(f"Facebook Global MP4 must fit a 10–15-second Reel: {duration:.2f}s")
    qc.update(width=width, height=height, video_duration_seconds=duration,
              silent_publish_blocked=True, background_music_added=False)
    print(f"Audio stream detected: {qc['audio_codec']}, {qc['audio_packets']} packets; silent publish blocked")
    return qc
