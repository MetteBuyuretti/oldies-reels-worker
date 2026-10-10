"""Jingle service checks used by the existing OLDIES WATCHDOG, not a second scheduler.

Input: authenticated, read-only telemetry JSON from the existing Jingle/WordPress
pipeline. No generation, publication, retries or credential mutation happens here.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, time, timedelta, timezone

SERVICE = "service:jingle-factory"
STAGES = ("GENERATING", "DOWNLOADED", "CAPCUT_READY", "COMPLETE")
ERRORS = {"AUTH_REQUIRED", "ERROR", "CAPCUT_PREP_FAILED", "LAUNCHER_ERROR"}
TIMEZONE = timezone(timedelta(hours=3))  # Turkey UTC+03 year-round; no tzdata dependency


def parsed(value):
    if not isinstance(value, str) or not value:
        raise ValueError("missing time")
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if instant.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return instant.astimezone(timezone.utc)


def issue(reason, incident):
    return {"path": SERVICE, "name": "Jingle Factory", "reason": reason,
            "run_id": str(incident or "unknown")[:90], "url": ""}


def status_url():
    return os.environ.get("OLDIES_JINGLE_STATUS_URL", "").strip()


def fetch_status(url, token, timeout=8):
    # No URL, token or sensitive server path is ever included in issue text.
    if not url.startswith("https://") or not token:
        raise ValueError("authenticated HTTPS telemetry source required")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "oldies-watchdog-jingle/1.0",
    })
    with opener.open(req, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError("telemetry HTTP response not OK")
        content = response.read(65537)
    if len(content) > 65536:
        raise ValueError("telemetry response too large")
    return json.loads(content.decode("utf-8-sig"))


def output_valid(file, job_id, now, duration_target, tolerance):
    if not isinstance(file, dict):
        return False
    if file.get("valid") is not True or file.get("job_id") != job_id:
        return False
    if not isinstance(file.get("sha256"), str) or len(file["sha256"]) != 64:
        return False
    if not isinstance(file.get("duration_seconds"), (float, int)):
        return False
    if abs(file["duration_seconds"] - duration_target) > tolerance:
        return False
    try:
        modified = parsed(file["modified_at"])
    except (ValueError, TypeError):
        return False
    age = (now - modified).total_seconds()
    return -300 <= age <= 172800


def evaluate(payload, now, cfg):
    """Return (findings, report). Missing evidence never becomes production success."""
    if not isinstance(payload, dict):
        return [issue("jingle_telemetry_invalid", "data")], "INVALID TELEMETRY"
    findings, detail = [], []
    hours = float(cfg.get("heartbeat_timeout_hours", 2))
    received = payload.get("last_successful_received_at")
    try:
        last = parsed(received)
        age = (now - last).total_seconds() / 3600
        if age < -0.0833:
            findings.append(issue("jingle_heartbeat_clock_invalid", "clock"))
        elif age > hours:
            findings.append(issue("jingle_heartbeat_stale", last.strftime("%Y%m%dT%H%M")))
        detail.append(f"heartbeat age: {age:.2f}h")
    except (ValueError, TypeError):
        findings.append(issue("jingle_heartbeat_unverified", "receipt"))
        detail.append("no verified server receipt")

    task = payload.get("windows_task", {})
    if not isinstance(task, dict) or task.get("enabled") is not True:
        findings.append(issue("jingle_task_not_verified", "scheduler"))
    elif task.get("last_result") not in (0, "0"):
        findings.append(issue("jingle_task_failed", str(task.get("last_run_at") or "unknown")))
    detail.append("Windows schedule: " + ("enabled" if isinstance(task, dict) and task.get("enabled") is True else "unverified"))

    job = payload.get("job")
    if not isinstance(job, dict) or not str(job.get("id", "")).strip():
        findings.append(issue("jingle_job_missing", "daily"))
        return findings, "; ".join(detail + ["no current job"])
    jid = str(job["id"])[:90]
    status = str(job.get("status", "")).upper()
    job_date = job.get("date", "")
    fallback = job.get("fallback_used") is True
    provider = str(job.get("provider", "unknown"))
    detail.append(f"job: {jid}, status: {status}, provider: " + ("LOCAL_FALLBACK" if fallback else provider))
    if status in ERRORS:
        findings.append(issue("jingle_" + status.lower(), jid))
    elif status not in STAGES and status not in ("PROMPT_SYNCED", "PROMPT_READY", "NO_PROMPT", "EMPTY_PROMPT"):
        findings.append(issue("jingle_unknown_stage", jid))

    trace = payload.get("events")
    trace_ok = isinstance(trace, list) and len(trace) > 0
    previous = -1
    observed = []
    if trace_ok:
        for event in trace:
            if not isinstance(event, dict) or event.get("job_id") != jid:
                trace_ok = False
                break
            current = str(event.get("status", "")).upper()
            if current in STAGES:
                i = STAGES.index(current)
                if i < previous or i > previous + 1:
                    trace_ok = False
                    break
                previous = i
                if current not in observed:
                    observed.append(current)
            elif current not in ERRORS and current not in ("PROMPT_READY", "PROMPT_SYNCED"):
                trace_ok = False
                break
    if not trace_ok:
        findings.append(issue("jingle_stage_trace_unverified", jid))

    if status in ("CAPCUT_READY", "COMPLETE"):
        outputs = payload.get("outputs", {})
        target = float(cfg.get("audio_target_seconds", 10))
        tolerance = float(cfg.get("audio_tolerance_seconds", .6))
        pair_ok = isinstance(outputs, dict) and all(
            output_valid(outputs.get(ext), jid, now, target, tolerance) for ext in ("m4a", "wav"))
        if not pair_ok:
            findings.append(issue("jingle_audio_invalid_or_stale", jid))
        detail.append("M4A/WAV: " + ("verified" if pair_ok else "NOT VERIFIED"))
    else:
        pair_ok = False

    final_ok = (status == "COMPLETE" and trace_ok and observed == list(STAGES)
                and pair_ok and job.get("voice_mixed") is True
                and job.get("master_verified") is True and not fallback)
    if status == "COMPLETE" and not final_ok:
        findings.append(issue("jingle_complete_not_proven", jid))
    if fallback:
        detail.append("LOCAL FALLBACK — not Gemini production success")

    # The known Windows schedule is 12:40 Europe/Istanbul; never assume success
    # merely because its Task Scheduler exit code is zero.
    local_now = now.astimezone(TIMEZONE)
    expected = datetime.combine(local_now.date(), time.fromisoformat(
        cfg.get("daily_scheduled_local_time", "12:40")), tzinfo=TIMEZONE)
    deadline = expected + timedelta(hours=float(cfg.get("daily_grace_hours", 2)))
    if local_now > deadline and (job_date != local_now.date().isoformat() or not final_ok):
        findings.append(issue("jingle_daily_incomplete", local_now.date().isoformat()))

    detail.append("MASTER: " + ("VERIFIED" if final_ok else "NOT VERIFIED"))
    return findings, "; ".join(detail)


def audit(cfg, now):
    """Get current telemetry if configured; otherwise report the setup gap."""
    if not cfg.get("enabled", False):
        return [], "DISABLED — no Jingle health monitoring", False
    url = status_url()
    token = os.environ.get("OLDIES_JINGLE_STATUS_TOKEN", "")
    if not url or not token:
        return [], "NOT CONNECTED — authenticated telemetry bridge/secret missing; NOT MONITORED", False
    try:
        telemetry = fetch_status(url, token)
        findings, description = evaluate(telemetry, now, cfg)
        return findings, description, True
    except (ValueError, TypeError, urllib.error.URLError, TimeoutError, OSError):
        return [issue("jingle_telemetry_unavailable", "connection")], "Telemetry unavailable; no health success inferred", True
