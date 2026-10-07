#!/usr/bin/env python3
"""Timestamp-aware video planning for Oldies Radyo.

This module keeps the approved one-take DJ voice intact. It derives scene and
caption timings from the finished voiceover, snaps boundaries to natural
pauses when FFmpeg detects them, and exports a CapCut-ready handoff package.
"""
from __future__ import annotations

import csv
import json
import math
import re
import shutil
import subprocess
from pathlib import Path


def audio_duration(path: Path) -> float:
    probe = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        ],
        check=True, capture_output=True, text=True,
    )
    return float(probe.stdout.strip())

MIN_FINAL_REEL_SECONDS = 10.0


def final_reel_duration(voice_seconds: float) -> float:
    """Never let a finished Reel fall below the 10-second production floor."""
    return max(MIN_FINAL_REEL_SECONDS, float(voice_seconds) + 0.12)


def _clean_script(script: str) -> str:
    text = re.sub(r"\[(?:duraklama|pause)\]", ". ", str(script or ""), flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _words(text: str) -> list[str]:
    return [item for item in re.split(r"\s+", text.strip()) if item]


def _balanced_chunks(script: str, count: int) -> list[str]:
    """Split copy into near-even readable beats without changing the words."""
    clean = _clean_script(script)
    words = _words(clean)
    if not words:
        return [""]
    count = max(1, min(count, len(words)))
    target = len(words) / count
    chunks: list[str] = []
    current: list[str] = []
    remaining_chunks = count
    used = 0

    for index, word in enumerate(words):
        current.append(word)
        used += 1
        remaining_words = len(words) - used
        punctuation = bool(re.search(r"[.!?,;:]$", word))
        desired = target * len(chunks) + target
        reached = used >= round(desired)
        must_leave = remaining_words >= (remaining_chunks - 1)
        if len(chunks) < count - 1 and must_leave and (reached or (punctuation and len(current) >= 4)):
            chunks.append(" ".join(current).strip())
            current = []
            remaining_chunks -= 1

    if current:
        chunks.append(" ".join(current).strip())

    while len(chunks) > count:
        tail = chunks.pop()
        chunks[-1] = f"{chunks[-1]} {tail}".strip()
    return chunks


def detect_pause_centers(audio: Path, *, min_silence: float = 0.16) -> list[float]:
    """Return centers of natural pauses detected by FFmpeg silencedetect."""
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(audio),
            "-af", f"silencedetect=noise=-34dB:d={min_silence}",
            "-f", "null", "-",
        ],
        capture_output=True, text=True,
    )
    log = (proc.stderr or "") + "\n" + (proc.stdout or "")
    starts = [float(x) for x in re.findall(r"silence_start:\s*([0-9.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end:\s*([0-9.]+)", log)]
    centers: list[float] = []
    for start, end in zip(starts, ends):
        if end > start:
            centers.append((start + end) / 2.0)
    return centers


def _snap_boundaries(nominal: list[float], pauses: list[float], duration: float) -> list[float]:
    snapped: list[float] = []
    previous = 0.0
    for point in nominal:
        candidates = [p for p in pauses if previous + 1.15 <= p <= duration - 0.75 and abs(p - point) <= 0.95]
        chosen = min(candidates, key=lambda p: abs(p - point)) if candidates else point
        chosen = max(previous + 1.15, min(chosen, duration - 0.75))
        snapped.append(chosen)
        previous = chosen
    return snapped


def build_timeline(script: str, audio: Path, *, target_scene_seconds: float = 3.2) -> list[dict]:
    duration = audio_duration(audio)
    scene_count = max(4, min(12, int(round(duration / target_scene_seconds))))
    chunks = _balanced_chunks(script, scene_count)
    weights = [max(1, len(_words(chunk))) for chunk in chunks]
    total_weight = sum(weights)

    nominal: list[float] = []
    cumulative = 0
    for weight in weights[:-1]:
        cumulative += weight
        nominal.append(duration * cumulative / total_weight)

    pauses = detect_pause_centers(audio)
    boundaries = _snap_boundaries(nominal, pauses, duration)
    points = [0.0, *boundaries, duration]

    timeline: list[dict] = []
    for index, chunk in enumerate(chunks):
        start = round(points[index], 3)
        end = round(points[index + 1], 3)
        if end - start < 0.7:
            continue
        timeline.append({
            "index": len(timeline) + 1,
            "start": start,
            "end": end,
            "duration": round(end - start, 3),
            "text": chunk,
        })

    if timeline:
        timeline[-1]["end"] = round(duration, 3)
        timeline[-1]["duration"] = round(duration - float(timeline[-1]["start"]), 3)
    return timeline


def _srt_time(seconds: float) -> str:
    milliseconds = int(round(max(0.0, seconds) * 1000))
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def write_srt(timeline: list[dict], path: Path) -> None:
    blocks: list[str] = []
    for item in timeline:
        blocks.append(
            f"{item['index']}\n{_srt_time(float(item['start']))} --> {_srt_time(float(item['end']))}\n"
            f"{item['text']}\n"
        )
    path.write_text("\n".join(blocks), encoding="utf-8")


def write_timeline_files(timeline: list[dict], directory: Path) -> tuple[Path, Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "timeline.json"
    csv_path = directory / "timeline.csv"
    srt_path = directory / "captions.srt"
    json_path.write_text(json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=["index", "start", "end", "duration", "text"])
        writer.writeheader()
        writer.writerows(timeline)
    write_srt(timeline, srt_path)
    return json_path, csv_path, srt_path


def export_capcut_package(
    *,
    timeline: list[dict],
    voiceover: Path,
    scenes: list[Path],
    output_dir: Path,
) -> Path:
    """Create an editor-neutral package that CapCut can ingest quickly."""
    package = output_dir / "capcut-package"
    package.mkdir(parents=True, exist_ok=True)
    audio_target = package / f"voiceover{voiceover.suffix.lower()}"
    shutil.copy2(voiceover, audio_target)

    scene_dir = package / "scenes"
    scene_dir.mkdir(exist_ok=True)
    for index, scene in enumerate(scenes, start=1):
        shutil.copy2(scene, scene_dir / f"{index:02d}_{scene.name}")

    write_timeline_files(timeline, package)
    (package / "IMPORT.txt").write_text(
        "OLDIES RADYO - CAPCUT HANDOFF\n"
        "1) Import voiceover and all files in scenes/.\n"
        "2) Import captions.srt as captions.\n"
        "3) timeline.csv gives exact scene start/end times.\n"
        "4) The automatic MP4 is already rendered; use CapCut only for optional final music/FX polish.\n",
        encoding="utf-8",
    )
    return package


def render_timeline(
    *,
    scenes: list[Path],
    timeline: list[dict],
    target: Path,
    voiceover: Path,
    width: int,
    height: int,
    fps: int,
    max_video_bytes: int,
) -> None:
    if not scenes or not timeline:
        raise RuntimeError("Timeline render requires scenes and timing data")
    if len(scenes) != len(timeline):
        raise RuntimeError("Scene count must match timeline count")

    transition = 0.28
    inputs: list[str] = []
    filters: list[str] = []
    for index, (scene, item) in enumerate(zip(scenes, timeline)):
        intended = float(item["duration"])
        source_duration = intended + (transition if index < len(scenes) - 1 else 0.0)
        frames = max(2, math.ceil(source_duration * fps))
        inputs += ["-loop", "1", "-t", f"{source_duration:.3f}", "-i", str(scene)]
        zoom = "0.00042" if index % 2 == 0 else "0.00030"
        filters.append(
            f"[{index}:v]scale={width}:{height},"
            f"zoompan=z='min(zoom+{zoom},1.075)':d={frames}:s={width}x{height}:fps={fps},"
            f"setsar=1[v{index}]"
        )

    current = "v0"
    elapsed = float(timeline[0]["duration"])
    transitions = ("fade", "smoothleft", "smoothright")
    for index in range(1, len(scenes)):
        out = f"x{index}"
        transition_name = transitions[(index - 1) % len(transitions)]
        filters.append(
            f"[{current}][v{index}]xfade=transition={transition_name}:"
            f"duration={transition:.2f}:offset={elapsed:.3f}[{out}]"
        )
        current = out
        elapsed += float(timeline[index]["duration"])

    voice_seconds = audio_duration(voiceover)
    total_duration = final_reel_duration(voice_seconds)
    visual_duration = sum(float(item["duration"]) for item in timeline)
    hold_seconds = max(0.0, total_duration - visual_duration)
    output_video = current
    if hold_seconds > 0.01:
        output_video = "vfinal"
        filters.append(
            f"[{current}]tpad=stop_mode=clone:stop_duration={hold_seconds:.3f}[{output_video}]"
        )

    audio_index = len(scenes)
    inputs += ["-i", str(voiceover)]
    filters.append(
        f"[{audio_index}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
        "highpass=f=70,lowpass=f=16000,"
        "acompressor=threshold=-20dB:ratio=3:attack=10:release=120:makeup=2,"
        "loudnorm=I=-16:TP=-1.0:LRA=7,apad[voice]"
    )
    command = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filters),
        "-map", f"[{output_video}]", "-map", "[voice]",
        "-t", f"{total_duration:.3f}", "-r", str(fps),
        "-c:v", "libx264", "-preset", "medium",
        "-crf", "24", "-maxrate", "2200k", "-bufsize", "4400k",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(target),
    ]
    subprocess.run(command, check=True)
    if not target.exists() or target.stat().st_size <= 0 or target.stat().st_size > max_video_bytes:
        raise RuntimeError("Timestamp-aware MP4 failed size validation")
