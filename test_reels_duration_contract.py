"""Offline P0 guard: reject any legacy 10-second video timing contract."""
import math
import unittest

from video_factory import final_reel_duration


class ReelsDurationContractTests(unittest.TestCase):
    def test_short_voiceovers_never_become_padded_reels(self):
        for seconds in (0.0, 9.2, 10.0, 12.0, 18.5, 24.87):
            with self.subTest(seconds=seconds), self.assertRaisesRegex(RuntimeError, "25-30s"):
                final_reel_duration(seconds)

    def test_voiceover_must_have_finite_plausible_duration(self):
        for seconds in (float("nan"), float("inf"), -math.inf, 29.89, 32.0):
            with self.subTest(seconds=seconds), self.assertRaisesRegex(RuntimeError, "25-30s"):
                final_reel_duration(seconds)

    def test_full_length_natural_voiceovers_are_accepted(self):
        for voice, expected in ((24.88, 25.0), (26.88, 27.0), (29.88, 30.0)):
            with self.subTest(voice=voice):
                self.assertAlmostEqual(final_reel_duration(voice), expected, places=2)


if __name__ == "__main__":
    unittest.main()
