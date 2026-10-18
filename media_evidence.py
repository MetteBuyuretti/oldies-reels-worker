"""Mechanical evidence from decoded bytes; never a historical or DJ approval."""
from __future__ import annotations

from array import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


class MediaEvidenceError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def probe(path: Path) -> dict:
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams",
                                 "-of", "json", str(path)], capture_output=True,
                                text=True, check=True, timeout=30)
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise MediaEvidenceError("FFprobe could not decode the media") from exc


def inspect_audio(path: Path) -> dict:
    """Decode at most 31 seconds; reject silent or padded full-take narration."""
    data = probe(path)
    tracks = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
    if len(tracks) != 1:
        raise MediaEvidenceError("Exactly one narration audio track required")
    try:
        duration = float(tracks[0].get("duration", data["format"]["duration"]))
        start = float(tracks[0].get("start_time", 0))
        if not math.isfinite(duration) or not 24.88 <= duration <= 30.0 or abs(start) > 0.15:
            raise ValueError("duration/start")
        decoded = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0",
                                  "-t", "31", "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                                 capture_output=True, check=True, timeout=45)
        samples = array("h", decoded.stdout)
        if sys.byteorder != "little":
            samples.byteswap()
        if not samples:
            raise ValueError("empty audio")
        decoded_seconds = len(samples) / 16000
        if abs(duration - decoded_seconds) > 0.15:
            raise ValueError("decoded duration mismatch")
        windows = [samples[i:i + 1600] for i in range(0, len(samples), 1600)]
        rms = [math.sqrt(sum(x * x for x in block) / len(block)) / 32768 for block in windows]
        audible = [level > 10 ** (-45 / 20) for level in rms]
        active = [i for i, value in enumerate(audible) if value]
        longest = current = 0
        for value in audible:
            current = 0 if value else current + 1
            longest = max(longest, current)
        if (not active or sum(audible) / len(audible) < 0.55 or active[0] > 4 or
                len(audible) - 1 - active[-1] > 5 or longest > 15):
            raise MediaEvidenceError("Narration is silent, mostly silent or extended with dead air")
        peak = max(abs(x) for x in samples) / 32768
        clipped = sum(abs(x) >= 32760 for x in samples) / len(samples)
        if clipped > 0.01:
            raise MediaEvidenceError("Narration has excessive digital clipping")
        return {"decoded_seconds": round(decoded_seconds, 4), "audio_start_seconds": start,
                "audio_sha256": sha256(path), "audible_fraction": round(sum(audible) / len(audible), 3),
                "longest_silence_seconds": round(longest / 10, 2),
                "peak_dbfs": round(20 * math.log10(max(peak, 1e-12)), 2),
                "natural_dj_approved": False}
    except (OSError, subprocess.SubprocessError, KeyError, ValueError, TypeError, OverflowError) as exc:
        raise MediaEvidenceError("Narration audio duration/decode evidence invalid") from exc


def inspect_reel(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size < 1024:
        raise MediaEvidenceError("Final MP4 missing or invalid")
    data = probe(path)
    try:
        fmt = data["format"]
        if "mp4" not in fmt["format_name"].split(","):
            raise ValueError("MP4 required")
        videos = [s for s in data["streams"] if s.get("codec_type") == "video"]
        if len(videos) != 1:
            raise ValueError("exactly one video track required")
        video = videos[0]
        seconds = float(fmt["duration"])
        if (not math.isfinite(seconds) or not 25.0 <= seconds <= 30.0 or
                abs(float(video["duration"]) - seconds) > 0.15 or
                abs(float(video.get("start_time", 0))) > 0.15):
            raise ValueError("real video duration must be 25-30s and match the container")
        width, height = int(video["width"]), int(video["height"])
        if width * 16 != height * 9 or width < 720 or height < 1280:
            raise ValueError("9:16 video of at least 720x1280 required")
        if video.get("sample_aspect_ratio") not in (None, "1:1"):
            raise ValueError("square pixels required")
        rotation = int(video.get("tags", {}).get("rotate", 0))
        for side in video.get("side_data_list", []):
            rotation += int(side.get("rotation", 0))
        if rotation % 360:
            raise ValueError("rotated display metadata not supported")
        audio = inspect_audio(path)
        if abs(audio["decoded_seconds"] - seconds) > 0.25:
            raise ValueError("audio/video durations differ")
        try:
            subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(path),
                            "-map", "0:v:0", "-f", "null", "-"],
                           capture_output=True, check=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as exc:
            raise MediaEvidenceError("Final video track failed full-frame decoding") from exc
        return {"status": "MEDIA_TECHNICALLY_VALID", "duration_seconds": seconds,
                "width": width, "height": height, "audio": audio,
                "video_decode_verified": True,
                "media_sha256": sha256(path), "ffprobe": data, "editorial_approved": False}
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise MediaEvidenceError(f"Final MP4 evidence invalid: {exc}") from exc
