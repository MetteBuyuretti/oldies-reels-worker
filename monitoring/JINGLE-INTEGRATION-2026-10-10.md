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

## Evidence and still-required live bridge

1. WordPress records server-side **receipt timestamp**, not just the client
   timestamp, and preserves status transitions per immutable job ID.
2. A **read-only Windows probe is included** in this PR:
   `monitoring/jingle_local_probe.py`. It checks M4A/WAV audio streams using
   FFprobe, 10 ± 0.6 s durations, SHA-256, task status and job/output binding,
   and rejects files outside the CapCut inbox. It performs **no scheduling,
   network delivery, generation or mutation**. Feeding its sanitized result
   through a protected WordPress relay is **still pending**.
3. Each event in `events` belongs to the same job and follows
   `GENERATING -> DOWNLOADED -> CAPCUT_READY -> COMPLETE`; absence of
   history means **unverified**, not success.
4. The provider records `fallback_used`. Local fallback is never
   relabeled Gemini production success.
5. The **existing Windows sender** received a minimal retry guard on
   10 Oct after a verified backup:
   `backups/send_jingle_heartbeat.before-watchdog-20261010.ps1`.
   It retries heartbeat POST **once only** for timeout/connectivity or HTTP
   429/5xx; it does not retry 401/403. Syntax PASS and one safe live send
   ACK PASS (`attempts=1`). The transient-failure branch has not been
   exercised against the real site. No generation, publish or duplicate
   job retries were made.
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

## 10 October observed test evidence

- Windows is online, task `Oldies Radyo Gemini Jingle` enabled; last scheduler
  exit result 0 is **not** proof of produced MASTER.
- Current job ID: `20261010-manual-recovery`; `CAPCUT_READY`,
  `voice_mixed=false`, `final_master_verified=false`.
- Local 10 Oct M4A and WAV both **decode with FFprobe** and measure **10.0 s**.
  Distinct SHA-256 digests confirmed; current prepared-job binding verified.
- No persisted per-job stage history; the probe returns an empty `events`
  array rather than fabricating any stage completion.
- Existing + new Python Watchdog checks: **29/29 Windows local tests PASS**.
- GitHub PR remains **DRAFT**. WordPress authenticated read-only relay,
  repository secret setup, live hourly audit and automatic Issue verification
  are **not yet complete**.

The Github PR does **not** deploy the Windows sender update, which was
surgically applied to its existing local script with a byte-for-byte backup.
