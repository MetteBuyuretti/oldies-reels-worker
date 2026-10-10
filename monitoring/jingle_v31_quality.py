"""OLDIES RADYO V3.1 fail-closed QA evidence gate for the existing Jingle Watchdog.

It does not edit producer settings or mark files final. Exact signal identity
and listening review are separate: automated waveform/metadata checks CANNOT
establish the absence of an unfamiliar guitar timbre by themselves.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

V31_ID = "OLDIES_RADYO_JINGLE_V3_1"
DUCK_DB = -4.0
DUCK_TOLERANCE_DB = 0.2
REQUIRED_ENDING_CHECKS = (
    "dj_end_clean",
    "same_music_bed",
    "no_foreign_guitar",
    "no_second_music",
    "no_abrupt_cut",
    "smooth_fade_out",
)


def hash_ok(value):
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdefABCDEF" for c in value))


def gain_ok(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and abs(value - DUCK_DB) <= DUCK_TOLERANCE_DB)


def review_v31(qc, job, now):
    """Return (ready, stable reasons) from evidence tied to the current MASTER hash.

    Required QC is produced by an independent render/QA step, not inferred
    from a heartbeat, CapCut delivery, or the user's baseline-standard approval.
    """
    reasons = []
    if not isinstance(qc, dict):
        return False, ["v31_qc_report_missing"]

    jid = str(job.get("id", ""))
    if qc.get("standard") != V31_ID or qc.get("job_id") != jid:
        reasons.append("v31_standard_or_job_mismatch")

    mix = qc.get("mix", {})
    if not isinstance(mix, dict) or not (gain_ok(mix.get("configured_duck_db"))
            and gain_ok(mix.get("verified_music_gain_db"))
            and mix.get("gain_measured_from_isolated_bed") is True
            and mix.get("no_predj_duck") is True
            and mix.get("dj_intelligibility_pass") is True):
        reasons.append("v31_balance_not_verified")

    ending = qc.get("ending", {})
    if not isinstance(ending, dict) or any(ending.get(flag) is not True for flag in REQUIRED_ENDING_CHECKS):
        reasons.append("v31_clean_end_not_verified")

    master = qc.get("master", {})
    if not isinstance(master, dict) or (master.get("valid") is not True
            or master.get("kind") != "MASTER" or not hash_ok(master.get("sha256"))
            or master.get("job_id") != jid or not isinstance(master.get("duration_seconds"), (int, float))
            or isinstance(master.get("duration_seconds"), bool)
            or not math.isfinite(master["duration_seconds"])
            or not 9 <= master["duration_seconds"] <= 20):
        reasons.append("v31_master_audio_invalid")

    source = qc.get("source", {})
    if not isinstance(source, dict) or not hash_ok(source.get("sha256")):
        reasons.append("v31_new_source_unverified")
    elif source.get("duplicate_of_previous") is not False:
        reasons.append("v31_source_reused")

    if isinstance(master, dict) and hash_ok(master.get("sha256")):
        if master.get("duplicate_of_previous") is not False:
            reasons.append("v31_master_duplicate_or_unverified")

    # No automatic genre/timbre classifier is falsely represented as a listener.
    listening = qc.get("auditory_review", {})
    if not isinstance(listening, dict) or (listening.get("status") != "PASS"
            or listening.get("reviewer_type") != "human"
            or not isinstance(listening.get("review_id"), str)
            or not listening["review_id"].strip()
            or not isinstance(master, dict)
            or listening.get("master_sha256") != master.get("sha256")):
        reasons.append("v31_auditory_review_pending")
    # The user's approval of V3.1 SOUND STANDARD is not approval of this new file.
    if qc.get("master_qc_pass") is not True:
        reasons.append("v31_master_qc_not_passed")
    return not reasons, reasons
