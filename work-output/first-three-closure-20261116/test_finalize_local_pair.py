"""New orchestration regressions, no provider, browser or scheduler calls."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

spec = importlib.util.spec_from_file_location("pair", Path(__file__).with_name("finalize-local-pair.py"))
pair = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pair)


class FinalizationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.day, self.slot = "2026-11-11", "morning"
        self.job = self.base / self.day
        self.job.mkdir()
        self.output = self.base / "outputs"
        self.output.mkdir()
        self.states = {}
        for kind in ("music", "video"):
            prompt = self.job / f"morning-{kind}.txt"
            prompt.write_text("fixture " + kind)
            source = self.job / (kind + (".mp3" if kind == "music" else ".mp4"))
            source.write_bytes((kind * 10000).encode())
            state = {"day": self.day, "slot": self.slot, "kind": kind,
                     "prompt_sha256": pair.sha(prompt), "status": pair.READY,
                     "output_file": str(source), "output_sha256": pair.sha(source),
                     "attempts": [{"result": "MEDIA_DOWNLOADED"}]}
            self.states[kind] = state
            self.write_state(kind)
        self.renderer = Mock(side_effect=AssertionError("Unexpected render"))

    def write_state(self, kind):
        (self.job / f"morning-{kind}-five-try.json").write_text(json.dumps(self.states[kind]))

    def run_final(self):
        return pair.finalize(self.base, self.base/"factory", self.output,
                             self.day, self.slot, renderer=self.renderer)

    def existing(self):
        mp3 = self.output / "fixture-existing.mp3"
        mp3.write_bytes(b"previous completed output bytes")
        report = {"sha256_music": self.states["music"]["output_sha256"],
                  "sha256_video": self.states["video"]["output_sha256"],
                  "output_mp3": str(mp3), "output_mp3_sha256": pair.sha(mp3),
                  "human_listening_pass": False}
        target = self.output / "OldiesRadyo-MORNING-20261111-V31-GEMINI-NEW-QC.json"
        target.write_text(json.dumps(report))
        return mp3, target

    def test_second_download_missing_never_renders(self):
        self.states["video"]["status"] = "UNKNOWN_PENDING_REVIEW"
        self.write_state("video")
        self.assertEqual(self.run_final()["status"], "WAITING_FOR_BOTH_DOWNLOADS")
        self.renderer.assert_not_called()

    def test_historical_pair_reused_twice_without_render_or_false_approval(self):
        _, report = self.existing()
        original = report.read_bytes()
        for _ in range(2):
            result = self.run_final()
            self.assertFalse(result["new_render"])
            self.assertFalse(result["human_listening_pass"])
        self.assertEqual(report.read_bytes(), original)
        self.renderer.assert_not_called()

    def test_tampered_existing_output_stops_without_overwrite(self):
        mp3, _ = self.existing()
        mp3.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "EXISTING_MASTER_CHANGED"):
            self.run_final()
        self.assertEqual(mp3.read_bytes(), b"changed")
        self.renderer.assert_not_called()

    def test_wrong_day_receipt_does_not_relabel_old_source(self):
        self.states["music"]["day"] = "2026-11-10"
        self.write_state("music")
        with self.assertRaisesRegex(ValueError, "SOURCE_JOB_MISMATCH"):
            self.run_final()

    def test_changed_prompt_blocks_render(self):
        (self.job / "morning-video.txt").write_text("different prompt")
        with self.assertRaisesRegex(ValueError, "PROMPT_CHANGED"):
            self.run_final()

    def test_source_bytes_change_blocks_render(self):
        Path(self.states["music"]["output_file"]).write_bytes(b"bad"*20000)
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH_CHANGED"):
            self.run_final()

    def test_source_outside_job_directory_blocks_render(self):
        outside = self.base / "other.mp4"
        outside.write_bytes(b"other"*10000)
        self.states["video"].update(output_file=str(outside), output_sha256=pair.sha(outside))
        self.write_state("video")
        with self.assertRaisesRegex(ValueError, "SOURCE_OUTSIDE_JOB"):
            self.run_final()

    def test_inflight_lock_is_not_bypassed(self):
        lock = self.job / "morning-v31-finalization.lock"
        lock.write_text("another worker")
        self.assertEqual(self.run_final()["status"], "FINALIZATION_INFLIGHT_RECONCILE_FIRST")
        self.assertEqual(lock.read_text(), "another worker")
        self.renderer.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
