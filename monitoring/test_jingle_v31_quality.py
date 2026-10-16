import copy
import unittest
from datetime import datetime, timezone

from jingle_v31_quality import review_v31

NOW = datetime(2026, 10, 11, 1, 0, tzinfo=timezone.utc)
JOB = {"id": "job-20261011"}
MASTER = "a" * 64

def report():
    return {
        "standard": "OLDIES_RADYO_JINGLE_V3_1",
        "job_id": JOB["id"],
        "mix": {"configured_duck_db": -4.0, "verified_music_gain_db": -4.0,
                "gain_measured_from_isolated_bed": True, "no_predj_duck": True,
                "dj_intelligibility_pass": True},
        "ending": {"dj_end_clean": True, "same_music_bed": True,
                   "no_foreign_guitar": True, "no_second_music": True,
                   "no_abrupt_cut": True, "smooth_fade_out": True},
        "master": {"valid": True, "kind": "MASTER",
                   "job_id": JOB["id"], "sha256": MASTER, "duration_seconds": 14.18,
                   "duplicate_of_previous": False},
        "source": {"sha256": "b" * 64, "duplicate_of_previous": False},
        "auditory_review": {"status": "PASS", "reviewer_type": "human",
                            "review_id": "test-review-only", "master_sha256": MASTER},
        "master_qc_pass": True
    }

class V31QualityTests(unittest.TestCase):
    def fail(self, case, expected):
        ok, reasons = review_v31(case, JOB, NOW, verified_master_sha256=MASTER)
        self.assertFalse(ok)
        self.assertIn(expected, reasons)

    def test_full_independent_fixture_passes(self):
        self.assertEqual(review_v31(report(), JOB, NOW, verified_master_sha256=MASTER), (True, []))

    def test_missing_independent_master_sha(self):
        ready, reasons = review_v31(report(), JOB, NOW)
        self.assertFalse(ready)
        self.assertIn("v31_master_file_unverified", reasons)

    def test_missing_certificate(self):
        self.fail({}, "v31_standard_or_job_mismatch")

    def test_wrong_version_or_job(self):
        p = report()
        p["standard"] = "OLDIES_RADYO_JINGLE_V3"
        self.fail(p, "v31_standard_or_job_mismatch")
        p = report()
        p["job_id"] = "previous"
        self.fail(p, "v31_standard_or_job_mismatch")

    def test_reject_old_music_levels(self):
        for level in (-12.0, -4.8, -6.0):
            with self.subTest(level=level):
                p = report()
                p["mix"]["configured_duck_db"] = level
                self.fail(p, "v31_balance_not_verified")

    def test_reject_unmeasured_gain(self):
        p = report()
        p["mix"]["gain_measured_from_isolated_bed"] = False
        self.fail(p, "v31_balance_not_verified")

    def test_reject_bad_ending_and_foreign_guitar(self):
        for flag in ("dj_end_clean","same_music_bed","no_foreign_guitar",
                     "no_second_music","no_abrupt_cut","smooth_fade_out"):
            with self.subTest(flag=flag):
                p = report()
                p["ending"][flag] = False
                self.fail(p, "v31_clean_end_not_verified")

    def test_reject_reused_source_and_master(self):
        p = report()
        p["source"]["duplicate_of_previous"] = True
        self.fail(p, "v31_source_reused")
        p = report()
        p["master"]["duplicate_of_previous"] = True
        self.fail(p, "v31_master_duplicate_or_unverified")

    def test_reject_missing_file_and_wrong_hash(self):
        p = report()
        p["master"]["valid"] = False
        self.fail(p, "v31_master_audio_invalid")
        p = report()
        p["master"]["sha256"] = "not-a-hash"
        self.fail(p, "v31_master_audio_invalid")

    def test_review_must_match_exact_master(self):
        p = report()
        p["auditory_review"]["master_sha256"] = "c" * 64
        self.fail(p, "v31_auditory_review_pending")

    def test_audio_qc_not_publication_approval(self):
        p = report()
        p["master_qc_pass"] = False
        self.fail(p, "v31_master_qc_not_passed")

if __name__ == "__main__":
    unittest.main()
