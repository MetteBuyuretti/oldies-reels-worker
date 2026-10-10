# OLDIES WATCHDOG — Jingle Factory service integration (10 October 2026)

Status: **TEST/REVIEW ONLY**. This is part of the existing hourly
`.github/workflows/oldies-watchdog.yml`. No new schedule or publisher is created.

## Verified infrastructure and boundary

- Existing Windows task: `Oldies Radyo Gemini Jingle`, observed daily at 12:40 Europe/Istanbul.
- Current sender: `send_jingle_heartbeat.ps1` POSTs to
  `/wp-json/oldies-command-center/v1/jingle-heartbeat`; the protected
  WordPress receiver currently stores only the **latest** heartbeat.
- Local `heartbeat-send-status.json` is a *client acknowledgement*, not
  independent evidence of the WordPress server's **latest successful receipt**.
- `capcut-status.json` can show a 10-second **music-preparation asset**;
  it is not proof of a voice-mixed approved MASTER.
- `gemini_jingle.js` uses `COMPLETE` to mean completed web download and
  CapCut preparation. The Watchdog intentionally requires a separate
  `master_verified: true` and `voice_mixed: true` before saying
  **MASTER VERIFIED**, so it will not inflate this success.
- Separate `Oldies-Jingle-Factory` Python/API flow remains unaffected.
  Its 48/48 tests do not establish real live MASTER success.

## Staged architecture (zero new schedules)

Existing Windows/Gemini + CapCut -> existing authenticated WordPress
heartbeat -> **pending authenticated read-only telemetry relay** ->
existing hourly GitHub `watchdog.py` -> existing deduplicated
GitHub Issues -> OLDIES MASTER STATUS devir report.

**Not yet connected:** WordPress currently offers a POST receiver rather
than an authenticated, read-only JSON telemetry feed for GitHub.
Never put the heartbeat sender's shared secret, credentials or Windows
paths in a public repository. Do not make an unauthenticated endpoint
to solve this. The GitHub Action must not invent green health while the
relay is unconnected: summary must show `NOT MONITORED`.

Only after a reviewed, tested, authenticated and read-only relay exists,
configure these GitHub Actions **repository secrets**:
- `OLDIES_JINGLE_STATUS_URL`: HTTPS read-only endpoint returning the schema below.
- `OLDIES_JINGLE_STATUS_TOKEN`: a *separate limited-scope read-only token*,
  **not** the existing heartbeat POST key.

Workflow step must pass these as environment variables on the main-branch
audit job only. Do not expose them in PR tests or Issue content. A URL
redirect, plaintext URL, missing auth, invalid data or timeout cannot
be treated as success.

## Expected sanitized telemetry contract

```json
{
  "last_successful_received_at": "2026-10-10T09:15:00Z",
  "windows_task": {
    "enabled": true, "last_result": 0,
    "last_run_at": "2026-10-10T09:40:00Z"
  },
  "job": {
    "id": "20261010-daily", "date": "2026-10-10",
    "status": "CAPCUT_READY", "provider": "gemini_pro_web",
    "fallback_used": false, "voice_mixed": false,
    "master_verified": false
  },
  "events": [
    {"job_id": "20261010-daily", "status": "GENERATING"},
    {"job_id": "20261010-daily", "status": "DOWNLOADED"},
    {"job_id": "20261010-daily", "status": "CAPCUT_READY"}
  ],
  "outputs": {
    "m4a": {"valid": true, "job_id": "20261010-daily",
      "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "duration_seconds": 10.0, "modified_at": "2026-10-10T10:00:00Z"},
    "wav": {"valid": true, "job_id": "20261010-daily",
      "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "duration_seconds": 10.0, "modified_at": "2026-10-10T10:00:00Z"}
  }
}
```

This is a **schema illustration**, not evidence of a live run.

## Required evidence collection (not implemented by this PR)

1. WordPress records server-side **receipt timestamp**, not just the client
   timestamp, and preserves status transitions per immutable job ID.
2. A read-only Windows probe checks actual file presence and decodability
   with FFprobe, measures durations of M4A and WAV, calculates SHA-256,
   checks modification time against job start, and reads Task Scheduler.
   It must publish only sanitized results through the existing bridge.
3. Each event in `events` belongs to the same job and follows
   `GENERATING -> DOWNLOADED -> CAPCUT_READY -> COMPLETE`; absence of
   history means **unverified**, not success.
4. The provider records `fallback_used`. Local fallback is never
   relabeled Gemini production success.
5. A transient heartbeat POST failure may be retried **at most once**
   only by the existing sender, after safe network classification.
   A permanent auth error must not be retried. No playback, generation,
   publish, data deletion or duplicate job retries are permitted.
6. Only one deduplicated Issue per incident; fixed issues remain
   informational and cannot trigger automatic production retries.
7. Confirm complete end-to-end live run, warning at >2h stale heartbeat,
   a missed daily production and two consecutive audits with no duplicate
   new Issue. Then separately approve production rollout.

## Master Status devir format

- `service: Jingle Factory`
- `heartbeat: last server receipt, age, PASS/STALE/UNVERIFIED`
- `Windows scheduler: latest expected/actual run and exit code`
- `job ID: status / ordered stages`
- `M4A/WAV: real duration, SHA, age, FFprobe PASS/FAIL`
- `music prepared: YES/NO; approved MASTER: YES/NO`
- `provider: Gemini/Local fallback`
- `incidents: deduped issue links; safe next step`

No new paid API, subscription, scheduled monitor or music-production
setting is introduced.
