"""Read-only Windows probe for existing Jingle files; NO scheduling or sending.

Run on the existing Windows machine under an approved bridge. Do not publish
the output to a public GitHub repository: it is designed for authenticated
telemetry transport to the existing Watchdog and has no credentials.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TASK_NAME = "Oldies Radyo Gemini Jingle"


def read(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def file_status(file_path, expected_job, ffprobe, allowed_directory=None):
    p = Path(file_path) if isinstance(file_path, str) and file_path else None
    if p is None or not p.is_file():
        return {"valid": False, "job_id": expected_job, "reason": "missing"}
    if p.suffix.lower() not in (".m4a", ".wav"):
        return {"valid": False, "job_id": expected_job, "reason": "bad_extension"}
    # The heartbeat JSON must not induce reading arbitrary local files.
    if allowed_directory is not None and not p.resolve().is_relative_to(allowed_directory.resolve()):
        return {"valid": False, "job_id": expected_job, "reason": "outside_capcut_inbox"}
    if p.stat().st_size < 1024:
        return {"valid": False, "job_id": expected_job, "reason": "empty"}
    try:
        result = subprocess.run([ffprobe, "-v", "error", "-select_streams", "a",
                                 "-show_entries", "stream=codec_type:format=duration",
                                 "-of", "json", str(p)],
                                capture_output=True, text=True, timeout=10, check=True)
        info = json.loads(result.stdout)
        has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
        duration = float(info.get("format", {}).get("duration", 0))
        if not has_audio or not math.isfinite(duration):
            raise ValueError("no audio or non-finite duration")
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        observed = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()
        return {"valid": 9.4 <= duration <= 10.6, "job_id": expected_job,
                "duration_seconds": round(duration, 4), "sha256": digest,
                "modified_at": observed}
    except FileNotFoundError:
        return {"valid": False, "job_id": expected_job, "reason": "ffprobe_missing"}
    except (ValueError, OSError, subprocess.SubprocessError):
        return {"valid": False, "job_id": expected_job, "reason": "decode_failure"}

def task_status():
    if sys.platform != "win32":
        return {"enabled": False, "reason": "not_windows"}
    command = ('$t = Get-ScheduledTask -TaskName "' + TASK_NAME + '" -ErrorAction Stop; '
               '$i = Get-ScheduledTaskInfo -TaskName $t.TaskName; '
               '[pscustomobject]@{ enabled=($t.State -ne "Disabled"); '
               'last_result=$i.LastTaskResult; last_run_at=$i.LastRunTime.ToString("o") }'
               ' | ConvertTo-Json -Compress')
    try:
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                                capture_output=True, text=True, timeout=10, check=True)
        return json.loads(result.stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return {"enabled": False, "reason": "task_query_failed"}


def collect(root, ffprobe="ffprobe"):
    state = read(root / "status.json")
    cap = read(root / "capcut-status.json")
    sender = read(root / "heartbeat-send-status.json")
    job_id = str(state.get("job_id") or "")
    prepared = state.get("prepared")
    # Guard against reusing yesterday's CapCut files for a new job.
    matched = (bool(job_id) and isinstance(prepared, dict)
               and prepared.get("m4a") == cap.get("m4a")
               and prepared.get("wav") == cap.get("wav")
               and prepared.get("created_at") == cap.get("created_at"))
    outputs = {}
    if matched:
        outputs = {ext: file_status(cap.get(ext), job_id, ffprobe, root / "capcut-inbox") for ext in ("m4a", "wav")}
    else:
        outputs = {ext: {"valid": False, "job_id": job_id, "reason": "job_file_link_unverified"}
                   for ext in ("m4a", "wav")}
    return {
        # WordPress receiver must add last_successful_received_at server-side.
        # Client acknowledgement is NOT trustworthy remote receipt evidence.
        "client_heartbeat_ack": {"ok": sender.get("ok") is True, "at": sender.get("at", "")},
        "windows_task": task_status(),
        "job": {"id": job_id, "date": str(state.get("date") or ""),
                "status": str(state.get("status") or ""),
                "provider": str(state.get("provider") or "unknown"),
                "fallback_used": state.get("fallback_used") is True,
                "voice_mixed": state.get("voice_mixed") is True,
                "master_verified": state.get("final_master_verified") is True},
        # No stage history exists yet; never fabricate transitions from current status.
        "events": [],
        "outputs": outputs
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: jingle_local_probe.py <existing-jingle-dir> [ffprobe-path]", file=sys.stderr)
        sys.exit(2)
    root = Path(sys.argv[1])
    ffprobe = sys.argv[2] if len(sys.argv) > 2 else "ffprobe"
    print(json.dumps(collect(root, ffprobe), ensure_ascii=False, indent=2))
