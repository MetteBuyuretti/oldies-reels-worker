"""Complete downloaded Gemini pairs with the installed V3.1 mixer; never publish.

This is a local, resumable post-download step. It makes no browser/API calls and
does not touch Factory production-state, provider receipts, or scheduled tasks.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

SETTINGS = {"duck_db": -4.0, "dj_start_seconds": 1.3,
            "duck_attack_seconds": .1, "duck_release_seconds": .4,
            "post_recovery_groove_seconds": 1.8, "fade_out_seconds": 1.5}
REFERENCE_SHA = "f32b7220d380dd000e16c648cf949990ac333fc578d14bff0c1a8370e6a26ff7"
READY = "DOWNLOADED_AWAITING_AUDIO_VIDEO_QC"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_pair(base, day, slot):
    datetime.strptime(day, "%Y-%m-%d")
    if slot not in {"morning", "evening"}:
        raise ValueError("INVALID_SLOT")
    directory = (Path(base) / day).resolve()
    sources = {}
    for kind in ("music", "video"):
        state_file = directory / f"{slot}-{kind}-five-try.json"
        if not state_file.exists():
            return None
        state = read(state_file)
        if state.get("status") != READY:
            return None
        if (state.get("day"), state.get("slot"), state.get("kind")) != (day, slot, kind):
            raise ValueError("SOURCE_JOB_MISMATCH")
        prompt = directory / f"{slot}-{kind}.txt"
        if sha(prompt) != state.get("prompt_sha256"):
            raise ValueError("PROMPT_CHANGED")
        path = Path(state.get("output_file") or "").resolve()
        if not path.is_relative_to(directory) or not path.is_file() or path.stat().st_size < 30000:
            raise ValueError("SOURCE_OUTSIDE_JOB_OR_MISSING")
        digest = sha(path)
        if digest != str(state.get("output_sha256", "")).lower():
            raise ValueError("SOURCE_HASH_CHANGED")
        attempts = state.get("attempts") or []
        if not 1 <= len(attempts) <= 5 or attempts[-1].get("result") != "MEDIA_DOWNLOADED":
            raise ValueError("DOWNLOAD_RECEIPT_MISSING")
        sources[kind] = {"path": str(path), "sha256": digest}
    return sources


def reuse_report(report_path, sources):
    report = read(report_path)
    # Accept the existing November-11 pilot schema without rewriting its history.
    identity = report.get("sources") or {
        "music": {"sha256": report.get("sha256_music", "")},
        "video": {"sha256": report.get("sha256_video", "")}}
    for kind in ("music", "video"):
        if str(identity.get(kind, {}).get("sha256", "")).lower() != sources[kind]["sha256"]:
            raise ValueError("EXISTING_MASTER_SOURCE_MISMATCH")
    output = Path(report.get("output_mp3") or "")
    if not output.is_file() or sha(output) != str(report.get("output_mp3_sha256", "")).lower():
        raise ValueError("EXISTING_MASTER_CHANGED_NO_RERENDER")
    return {"status": "EXISTING_CANDIDATE_REUSED", "report": str(report_path),
            "mp3": str(output), "sha256": sha(output), "new_render": False,
            "human_listening_pass": report.get("human_listening_pass") is True}


def render_candidate(sources, factory, output, day, slot):
    import numpy as np
    factory, output = Path(factory), Path(output)
    ffmpeg = factory / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
    ffprobe = factory / "tools" / "ffmpeg" / "bin" / "ffprobe.exe"
    if not ffmpeg.is_file() or not ffprobe.is_file():
        raise ValueError("INSTALLED_ENCODER_MISSING")
    reference = factory / "references" / "OldiesRadyo-V3.1-APPROVED-SOUND-REFERENCE.mp3"
    if sha(reference) != REFERENCE_SHA:
        raise ValueError("APPROVED_REFERENCE_CHANGED")
    settings = read(factory / "config" / "settings.json")
    for key, value in SETTINGS.items():
        if not math.isclose(float(settings[key]), value, abs_tol=1e-7):
            raise ValueError("V31_SETTING_CHANGED_" + key)
    sys.path.insert(0, str(factory))
    sys.path.insert(0, str(factory / "src"))
    audio = importlib.import_module("src.audio")
    rate = 48000
    settings["sample_rate"] = rate
    for kind, source in sources.items():
        if sha(source["path"]) != source["sha256"]:
            raise ValueError("SOURCE_CHANGED_BEFORE_RENDER")
        probe = subprocess.run([str(ffprobe), "-v", "error", "-show_streams", "-of", "json", source["path"]],
                               check=True, capture_output=True, text=True, timeout=30)
        streams = json.loads(probe.stdout).get("streams", [])
        if not any(s.get("codec_type") == "audio" for s in streams):
            raise ValueError("SOURCE_AUDIO_STREAM_MISSING")
        if kind == "video" and not any(s.get("codec_type") == "video" for s in streams):
            raise ValueError("DJ_SOURCE_IS_NOT_A_SPEAKING_VIDEO")

    def decode(path):
        result = subprocess.run([str(ffmpeg), "-nostdin", "-v", "error", "-i", str(path),
            "-vn", "-ar", str(rate), "-ac", "2", "-f", "f32le", "-"],
            check=True, capture_output=True, timeout=90)
        return np.frombuffer(result.stdout, dtype="<f4").reshape(-1, 2).copy()

    music, voice = (decode(sources[k]["path"]) for k in ("music", "video"))
    if not 20 <= len(music)/rate <= 180 or not 3 <= len(voice)/rate <= 20:
        raise ValueError("SOURCE_DURATION_OUTSIDE_EXPECTED_RANGE")
    # Numeric activity bounds are not a claim that a listener approved speech.
    width = int(.01 * rate)
    frames = voice[:len(voice)//width*width].reshape(-1, width, 2)
    rms = np.sqrt(np.mean(frames.astype(np.float64)**2, axis=(1, 2)))
    active = np.flatnonzero(rms > 10 ** (-35/20))
    if not len(active):
        raise ValueError("VIDEO_HAS_NO_USABLE_AUDIO")
    start = max(0, int(active[0]*width - .04*rate))
    end = min(len(voice), int((active[-1]+1)*width + .05*rate))
    dj = voice[start:end].copy()
    if not 3 <= len(dj)/rate <= 14:
        raise ValueError("DJ_DURATION_NEEDS_SOURCE_REVIEW")
    fade = min(len(dj), int(.065*rate))
    dj[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)[:, None]
    result, info = audio.mix(music, dj, settings)
    if not 9 <= len(result)/rate <= 20 or abs(float(info["dj_start_seconds"])-1.3) > .01:
        raise ValueError("MIX_TIMING_INVALID")
    wav_part = output.with_suffix(".pending.wav")
    mp3_part = output.with_suffix(".pending.mp3")
    for partial in (wav_part, mp3_part):
        if partial.exists():
            raise ValueError("PARTIAL_OUTPUT_RECONCILIATION_REQUIRED")
    audio.write_wav(wav_part, result.astype(np.float32), rate)
    subprocess.run([str(ffmpeg), "-nostdin", "-v", "error", "-n", "-i", str(wav_part),
                    "-c:a", "libmp3lame", "-b:a", "256k", str(mp3_part)], check=True, timeout=90)
    encoded = decode(mp3_part)
    if any(sha(s["path"]) != s["sha256"] for s in sources.values()):
        raise ValueError("SOURCE_CHANGED_DURING_RENDER")
    peak_db = 20 * math.log10(max(float(audio.true_peak(encoded)), 1e-12))
    if peak_db > -1:
        raise ValueError("ENCODED_MASTER_PEAK_TOO_HIGH")
    loud = subprocess.run([str(ffmpeg), "-nostdin", "-hide_banner", "-i", str(mp3_part),
            "-af", "ebur128=peak=true", "-f", "null", os.devnull],
            capture_output=True, text=True, check=True, timeout=90)
    measures = re.findall(r"I:\s*(-?[\d.]+) LUFS", loud.stderr)
    if not measures or not math.isfinite(float(measures[-1])):
        raise ValueError("LOUDNESS_MEASUREMENT_MISSING")
    # Move only to previously absent paths. An incomplete pair stays reviewable.
    wav, mp3 = output.with_suffix(".wav"), output.with_suffix(".mp3")
    if wav.exists() or mp3.exists():
        raise ValueError("NO_OVERWRITE")
    wav_part.rename(wav)
    mp3_part.rename(mp3)
    return {"status": "V31_CANDIDATE_LISTENING_QC_PENDING", "day": day, "slot": slot,
        "sources": sources, "settings_v31": SETTINGS, "mix_info": info,
        "detected_activity_start_seconds": start/rate, "detected_activity_end_seconds": end/rate,
        "activity_detection_is_not_speech_or_timbre_approval": True,
        "output_mp3": str(mp3), "output_mp3_sha256": sha(mp3), "output_wav": str(wav),
        "duration_seconds": len(encoded)/rate, "output_lufs": float(measures[-1]),
        "true_peak_db": peak_db, "human_listening_pass": False,
        "release_authorized": False, "scheduled_auto_publication": False,
        "created_at": datetime.now(timezone.utc).isoformat()}


def finalize(base, factory, output_dir, day, slot, renderer=render_candidate):
    sources = source_pair(base, day, slot)
    if sources is None:
        return {"status": "WAITING_FOR_BOTH_DOWNLOADS", "new_render": False}
    output_dir = Path(output_dir)
    old_report = output_dir / f"OldiesRadyo-{slot.upper()}-{day.replace('-', '')}-V31-GEMINI-NEW-QC.json"
    if old_report.exists():
        return reuse_report(old_report, sources)
    identity = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()[:16]
    stem = output_dir / f"OldiesRadyo-{slot.upper()}-{day.replace('-', '')}-V31-{identity}"
    report_path = Path(str(stem) + "-QC.json")
    lock_path = Path(base) / day / f"{slot}-v31-finalization.lock"
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return {"status": "FINALIZATION_INFLIGHT_RECONCILE_FIRST", "new_render": False}
    try:
        if report_path.exists():
            return reuse_report(report_path, sources)
        if stem.with_suffix(".mp3").exists() or stem.with_suffix(".wav").exists():
            raise ValueError("ORPHAN_OUTPUT_RECONCILE_FIRST")
        output_dir.mkdir(parents=True, exist_ok=True)
        report = renderer(sources, factory, stem, day, slot)
        with report_path.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
        return {"status": report["status"], "new_render": True, "report": str(report_path),
                "mp3": report["output_mp3"], "human_listening_pass": False}
    finally:
        os.close(fd)
        lock_path.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("day")
    parser.add_argument("slot", choices=["morning", "evening"])
    parser.add_argument("--base", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--factory", type=Path, default=Path(r"C:\Users\METE\Oldies-Jingle-Factory"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(finalize(args.base, args.factory, args.output or args.base.parent/"outputs",
                                  args.day, args.slot), ensure_ascii=False))
    except Exception as error:
        print(json.dumps({"status": "FINALIZATION_BLOCKED", "reason": str(error)}))
        sys.exit(2)
