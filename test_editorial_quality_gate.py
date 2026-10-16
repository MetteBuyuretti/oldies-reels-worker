"""Offline regression tests for the P0 editorial delivery guard (no network)."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from editorial_quality_gate import EditorialGateError, check_approved_reel, load_approval, media_sha256


DJ = (
    "On dört Ekim bin dokuz yüz yetmiş yedi. David Bowie Berlin'de Heroes albümünü yayımladı. "
    "O günün hikâyesi yalnızca bir plak satışından ibaret değildi. Yapımcı Tony Visconti'nin "
    "anlattığına göre ilk kayıt günlerinde ortada tamamlanmış şarkılar yoktu; yalnızca ritimler "
    "ve akor fikirleri vardı. Brian Eno'nun deneyleri ve Robert Fripp'in gitarları bu cesur "
    "çalışmaya eşlik etti. Albüm İngiltere'de üçüncülüğe yükseldi. Oldies Radyo. Dinle, beğen, paylaş."
)


def sample():
    photos = [
        dict(title=f"File:David Bowie Berlin 1977 photo {i}.jpg", license="CC BY-SA 4.0",
             description_url=f"https://commons.wikimedia.org/wiki/File:David_Bowie_1977_{i}.jpg",
             width=1600, height=1200)
        for i in range(3)
    ]
    return {
        "artist": "David Bowie", "reels_language": "tr", "event_date": "1977-10-14",
        "sources": ["https://www.thisdayinmusic.com/on-this-day-in-music-october-14/"],
        "dj_script_tr": DJ,
        "image_credits": photos,
    }


def evidence(video):
    return {
        "status": "APPROVED", "reviewer": "Independent Work-1 QA",
        "media_sha256": media_sha256(video),
        "fact_evidence": [
            {"claim": "Album released 14 October 1977", "url": "https://www.davidbowie.com/blog/2017/10/14/heroes-released-on-this-day-in-1977"},
            {"claim": "Recorded wholly in Berlin", "url": "https://www.davidbowie.com/blog/2022/7/29/heroes-anniversary-vinyl-and-live-78-digital"}
        ],
        "visual_evidence": [
            {"artist_confirmed": True, "event_context_confirmed": True,
             "evidence_url": "https://commons.wikimedia.org/wiki/File:David_Bowie_1977_"+str(i)+".jpg"}
            for i in range(3)
        ],
    }


class EditorialGateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.video = Path(self.directory.name) / "reel.mp4"
        self.video.write_bytes(b"fake-local-fixture" * 200)

    def test_valid_evidence_and_real_duration_gate_pass(self):
        value = check_approved_reel(sample(), self.video, evidence(self.video), measured_duration=27.1)
        self.assertEqual(value["status"], "PASS")
        self.assertEqual(value["photo_count"], 3)

    def test_four_tops_10_second_regression_fails(self):
        with self.assertRaisesRegex(EditorialGateError, "25-30"):
            check_approved_reel(sample(), self.video, evidence(self.video), measured_duration=10.0)

    def test_unapproved_24_or_31_seconds_fail(self):
        for duration in (24.99, 30.01):
            with self.subTest(duration=duration):
                with self.assertRaises(EditorialGateError):
                    check_approved_reel(sample(), self.video, evidence(self.video), measured_duration=duration)

    def test_wrong_day_or_soundod_only_rejected(self):
        candidate = sample()
        candidate["sources"] = ["https://soundod.com/october-14-in-music-history/"]
        with self.assertRaisesRegex(EditorialGateError, "This Day"):
            check_approved_reel(candidate, self.video, evidence(self.video), measured_duration=27)

    def test_figurine_statue_photo_rejected(self):
        candidate = sample()
        candidate["image_credits"][0]["title"] = "File:David Bowie waxwork statue 1977.jpg"
        with self.assertRaisesRegex(EditorialGateError, "Forbidden"):
            check_approved_reel(candidate, self.video, evidence(self.video), measured_duration=27)

    def test_wrong_or_missing_license_and_review_rejected(self):
        candidate = sample()
        candidate["image_credits"][0]["license"] = ""
        with self.assertRaisesRegex(EditorialGateError, "license"):
            check_approved_reel(candidate, self.video, evidence(self.video), measured_duration=27)
        candidate = sample()
        approvals = evidence(self.video)
        approvals["visual_evidence"][1]["artist_confirmed"] = False
        with self.assertRaisesRegex(EditorialGateError, "not verified"):
            check_approved_reel(candidate, self.video, approvals, measured_duration=27)

    def test_bad_sha_cannot_approve_different_mp4(self):
        approvals = evidence(self.video)
        approvals["media_sha256"] = "0" * 64
        with self.assertRaisesRegex(EditorialGateError, "exact final MP4"):
            check_approved_reel(sample(), self.video, approvals, measured_duration=27)

    def test_generic_two_word_script_fails(self):
        c = sample()
        c["dj_script_tr"] = "Bugün güzel müzik. Oldies Radyo. Dinle, beğen, paylaş."
        with self.assertRaisesRegex(EditorialGateError, "too short"):
            check_approved_reel(c, self.video, evidence(self.video), measured_duration=27)

    def test_no_external_approval_file_refuses_delivery(self):
        with self.assertRaisesRegex(EditorialGateError, "No external"):
            load_approval("")

    def test_unverified_facts_rejected(self):
        approvals = evidence(self.video)
        approvals["fact_evidence"] = [
            {"claim": "Top album", "url": "https://en.wikipedia.org/wiki/David_Bowie"},
            {"claim": "Berlin", "url": "https://www.wikidata.org/wiki/Q5383"}
        ]
        with self.assertRaisesRegex(EditorialGateError, "independent cited"):
            check_approved_reel(sample(), self.video, approvals, measured_duration=27)


if __name__ == "__main__":
    unittest.main()
