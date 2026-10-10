import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from jingle_local_probe import collect, file_status


class JingleLocalProbeTests(unittest.TestCase):
    def test_file_must_be_decodable_10_seconds(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "jingle.wav"
            p.write_bytes(b"x" * 2048)
            with patch("jingle_local_probe.subprocess.run",
                       return_value=Mock(stdout=json.dumps({"streams":[{"codec_type":"audio"}],"format":{"duration":"10.000"}}), returncode=0)):
                result = file_status(str(p), "job-1", "ffprobe")
            self.assertTrue(result["valid"])
            self.assertEqual(result["duration_seconds"], 10.0)
            self.assertEqual(result["job_id"], "job-1")
            self.assertEqual(len(result["sha256"]), 64)

    def test_reject_invalid_duration(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "jingle.m4a"
            p.write_bytes(b"x" * 2048)
            with patch("jingle_local_probe.subprocess.run",
                       return_value=Mock(stdout=json.dumps({"streams":[{"codec_type":"audio"}],"format":{"duration":"13.01"}}), returncode=0)):
                self.assertFalse(file_status(str(p), "job-1", "ffprobe")["valid"])

    def test_missing_file_is_not_green(self):
        self.assertFalse(file_status("X:/does-not-exist.wav", "job", "ffprobe")["valid"])

    def test_old_job_files_not_attributed_to_new_job(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "status.json").write_text(json.dumps({
                "job_id": "today", "status": "CAPCUT_READY",
                "prepared": {"m4a": "yesterday.m4a", "wav": "yesterday.wav",
                             "created_at": "yesterday"}}), encoding="utf-8")
            (root / "capcut-status.json").write_text(json.dumps({
                "m4a": "today.m4a", "wav": "today.wav",
                "created_at": "today"}), encoding="utf-8")
            with patch("jingle_local_probe.task_status",
                       return_value={"enabled": True, "last_result": 0}):
                output = collect(root)
            self.assertFalse(output["outputs"]["wav"]["valid"])
            self.assertEqual(output["events"], [])
            self.assertNotIn("last_successful_received_at", output)
            self.assertFalse(output["job"]["master_verified"])


if __name__ == "__main__":
    unittest.main()
