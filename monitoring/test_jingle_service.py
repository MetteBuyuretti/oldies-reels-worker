import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from jingle_service import audit, evaluate, output_valid

NOW = datetime(2026, 10, 10, 13, 0, tzinfo=timezone.utc)  # 16:00 Istanbul
CFG = {"enabled": True, "heartbeat_timeout_hours": 2, "audio_target_seconds": 10,
       "audio_tolerance_seconds": .6, "daily_scheduled_local_time": "12:40", "daily_grace_hours": 2}


def approved_v31_fixture(jid):
    h = "f" * 64
    return {
        "standard": "OLDIES_RADYO_JINGLE_V3_1", "job_id": jid,
        "mix": {"configured_duck_db": -4.0, "verified_music_gain_db": -4.0,
                "gain_measured_from_isolated_bed": True,
                "no_predj_duck": True, "dj_intelligibility_pass": True},
        "ending": {"dj_end_clean": True, "same_music_bed": True,
                   "no_foreign_guitar": True, "no_second_music": True,
                   "no_abrupt_cut": True, "smooth_fade_out": True},
        "master": {"valid": True, "kind": "MASTER", "sha256": h, "job_id": jid,
                   "duration_seconds": 14.18, "duplicate_of_previous": False},
        "source": {"sha256": "e" * 64, "duplicate_of_previous": False},
        "auditory_review": {"status": "PASS", "reviewer_type": "human",
                            "review_id": "mock-user-review", "master_sha256": h},
        "master_qc_pass": True
    }


def sample(status="COMPLETE", fallback=False):
    jid = "20261010-daily"
    seq = ["GENERATING", "DOWNLOADED", "CAPCUT_READY", "COMPLETE"]
    events = [{"job_id": jid, "status": stage} for stage in seq[:seq.index(status)+1]]
    file = lambda: {"valid": True, "job_id": jid, "sha256": "a" * 64,
                    "duration_seconds": 10.0, "modified_at": "2026-10-10T12:55:00Z"}
    return {
        "last_successful_received_at": "2026-10-10T12:20:00Z",
        "windows_task": {"enabled": True, "last_result": 0, "last_run_at": "2026-10-10T09:40:00Z"},
        "job": {"id": jid, "date": "2026-10-10", "status": status, "provider": "gemini_pro_web",
                "fallback_used": fallback, "voice_mixed": True, "master_verified": True},
        "events": events, "outputs": {"m4a": file(), "wav": file()},
        "quality_v31": approved_v31_fixture(jid) if status == "COMPLETE" else None,
    }


class JingleWatchdogTests(unittest.TestCase):
    def reasons(self, payload):
        return [x["reason"] for x in evaluate(payload, NOW, CFG)[0]]

    def test_complete_with_matching_job_outputs_and_receipt(self):
        self.assertEqual(self.reasons(sample()), [])

    def test_two_hours_is_threshold(self):
        p = sample()
        p["last_successful_received_at"] = "2026-10-10T10:59:00Z"
        self.assertIn("jingle_heartbeat_stale", self.reasons(p))

    def test_sender_timestamp_not_a_verified_heartbeat(self):
        p = sample()
        del p["last_successful_received_at"]
        p["sent_at"] = "2026-10-10T12:59:00Z"
        self.assertIn("jingle_heartbeat_unverified", self.reasons(p))

    def test_errors_are_not_healthy(self):
        for error in ["AUTH_REQUIRED", "ERROR", "CAPCUT_PREP_FAILED", "LAUNCHER_ERROR"]:
            with self.subTest(error=error):
                p = sample("GENERATING")
                p["job"]["status"] = error
                self.assertIn("jingle_" + error.lower(), self.reasons(p))

    def test_mismatched_stage_job_id(self):
        p = sample()
        p["events"][1]["job_id"] = "yesterday"
        self.assertIn("jingle_stage_trace_unverified", self.reasons(p))

    def test_skipped_transition_is_invalid(self):
        p = sample()
        p["events"].pop(1)
        self.assertIn("jingle_stage_trace_unverified", self.reasons(p))

    def test_audio_wrong_job_or_duration(self):
        p = sample()
        p["outputs"]["m4a"]["job_id"] = "other"
        self.assertIn("jingle_audio_invalid_or_stale", self.reasons(p))
        p = sample()
        p["outputs"]["wav"]["duration_seconds"] = 13.01
        self.assertIn("jingle_audio_invalid_or_stale", self.reasons(p))

    def test_audio_from_previous_day_is_rejected(self):
        p = sample()
        p["outputs"]["m4a"]["modified_at"] = "2026-10-07T13:00:00Z"
        self.assertIn("jingle_audio_invalid_or_stale", self.reasons(p))

    def test_no_master_if_capcut_only(self):
        p = sample("CAPCUT_READY")
        self.assertIn("jingle_daily_incomplete", self.reasons(p))
        self.assertIn("MASTER: NOT VERIFIED", evaluate(p, NOW, CFG)[1])

    def test_task_exit_zero_is_not_production_success(self):
        p = sample("GENERATING")
        self.assertIn("jingle_daily_incomplete", self.reasons(p))

    def test_local_fallback_distinct_from_gemini_success(self):
        p = sample(fallback=True)
        reasons, report = evaluate(p, NOW, CFG)
        self.assertIn("LOCAL FALLBACK", report)
        self.assertIn("jingle_complete_not_proven", [x["reason"] for x in reasons])

    def test_complete_without_mixed_voice_is_false_success(self):
        p = sample()
        p["job"]["voice_mixed"] = False
        self.assertIn("jingle_complete_not_proven", self.reasons(p))

    def test_missing_task_is_flagged(self):
        p = sample()
        p["windows_task"] = {}
        self.assertIn("jingle_task_not_verified", self.reasons(p))

    def test_missing_config_reports_not_monitored_not_green(self):
        with patch.dict(os.environ, {}, clear=True):
            findings, report, connected = audit(CFG, NOW)
        self.assertEqual(findings, [])
        self.assertFalse(connected)
        self.assertIn("NOT MONITORED", report)

    def test_telemetry_error_is_single_issue_without_secret(self):
        with patch.dict(os.environ, {"OLDIES_JINGLE_STATUS_URL": "https://example.org/status",
                                     "OLDIES_JINGLE_STATUS_TOKEN": "SUPER_SECRET"}, clear=True):
            with patch("jingle_service.fetch_status", side_effect=TimeoutError):
                findings, report, connected = audit(CFG, NOW)
        self.assertTrue(connected)
        self.assertEqual(findings[0]["reason"], "jingle_telemetry_unavailable")
        self.assertNotIn("SUPER_SECRET", str(findings) + report)


    def test_complete_without_v31_report_must_never_be_final(self):
        p = sample()
        del p["quality_v31"]
        self.assertIn("v31_qc_report_missing", self.reasons(p))
        self.assertIn("jingle_complete_not_proven", self.reasons(p))

    def test_complete_wrong_duck_or_unreviewed_tail_blocked(self):
        p = sample()
        p["quality_v31"]["mix"]["verified_music_gain_db"] = -12.0
        self.assertIn("v31_balance_not_verified", self.reasons(p))
        p = sample()
        p["quality_v31"]["ending"]["no_foreign_guitar"] = False
        self.assertIn("v31_clean_end_not_verified", self.reasons(p))

    def test_complete_duplicate_source_is_not_new(self):
        p = sample()
        p["quality_v31"]["source"]["duplicate_of_previous"] = True
        self.assertIn("v31_source_reused", self.reasons(p))

    def test_complete_without_human_listening_stays_pending(self):
        p = sample()
        p["quality_v31"]["auditory_review"]["status"] = "PENDING"
        self.assertIn("v31_auditory_review_pending", self.reasons(p))

    def test_unverified_file(self):
        self.assertFalse(output_valid({"valid": True}, "id", NOW, 10, .6))


if __name__ == "__main__":
    unittest.main()
