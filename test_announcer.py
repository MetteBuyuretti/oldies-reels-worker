"""Regression checks for Turkish Reels facts and DJ copy."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import tempfile
import unittest

import worker
from zero_cost import artist_page_title, deterministic_copy


class AnnouncerTests(unittest.TestCase):
    def candidate(self, artist, date, source):
        copy = deterministic_copy(
            artist=artist, kind="events",
            event_date=datetime.fromisoformat(date).replace(tzinfo=timezone.utc),
            source_text=source, tr_extract="",
        )
        return {"artist": artist, "kind": "events", "event_date": date,
                "source_text": source, "instagram_music_title": copy["music_title"], **copy}

    def test_lennon_tells_the_event_and_later_outcome(self):
        item = self.candidate(
            "John Lennon", "1974-09-23",
            "John Lennon released ‘Whatever Gets You thru the Night’ on this day "
            "September 23 which later became his first solo No.1 single in the US.",
        )
        spoken = worker.build_turkish_gemini_script(item)
        self.assertIn("Yirmi üç Eylül bin dokuz yüz yetmiş dört", spoken)
        self.assertIn("sonra", spoken)
        self.assertIn("ilk solo liste birinciliğini", spoken)
        self.assertIn("Elton John piyanoda ve geri vokalde", spoken)
        self.assertTrue(any("johnlennon.com" in source for source in item["sources"]))
        self.assertIn("John Lennon,", spoken)
        self.assertNotIn("Lennon\u0027ın", spoken)
        self.assertNotIn("Oldies Radyo", spoken)
        self.assertNotIn("1974", spoken)
        prompt = worker.turkish_gemini_style_prompt(item)
        self.assertIn("Whatever Gets You thru the Night", prompt)
        self.assertIn("haber spikeri tonundan", prompt)

    def test_album_apostrophe_and_type_are_preserved(self):
        item = self.candidate(
            "The Rolling Stones", "1973-09-22",
            "The number one album in the United Kingdom on this day was "
            "‘Goat’s Head Soup’ by The Rolling Stones.",
        )
        self.assertEqual(item["instagram_music_title"], "Goat’s Head Soup")
        spoken = worker.build_turkish_gemini_script(item)
        self.assertIn("'Goat’s Head Soup' albümü", spoken)
        self.assertIn("Zirvede iki hafta kaldı", spoken)
        self.assertTrue(any("officialcharts.com" in source for source in item["sources"]))
        self.assertNotIn("'Goat'", spoken)

    def test_unsupported_story_is_rejected(self):
        item = self.candidate("Eagles", "1979-09-24", "Eagles made music history.")
        with self.assertRaises(worker.VoiceoverQualityError):
            worker.build_turkish_gemini_script(item)

    def test_eagles_bird_and_castle_cannot_be_band_sources(self):
        self.assertEqual(artist_page_title("Eagles"), "Eagles (band)")
        self.assertFalse(worker.image_matches_artist({"title": "Eagles Castle"}, "Eagles"))
        self.assertTrue(worker.image_matches_artist({"title": "Eagles band live in concert"}, "Eagles"))
        self.assertFalse(worker.image_matches_artist({"title": "Bootleg LP Rolling Stones 1969"}, "The Rolling Stones", "Goat’s Head Soup"))
        self.assertFalse(worker.image_matches_artist({"title": "A Rolling Stones crowd - 1976"}, "The Rolling Stones", "Goat’s Head Soup"))
        self.assertTrue(worker.image_matches_artist({"title": "Rolling Stones 1971"}, "The Rolling Stones", "Goat’s Head Soup"))

    def test_station_and_cta_have_real_pauses(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            clips = []
            for label, seconds in (("story", 8.5), ("station", 1.0), ("cta", 2.0)):
                path = directory / f"{label}.mp3"
                subprocess.run(
                    ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                     "-i", "sine=frequency=440:sample_rate=48000", "-t", str(seconds),
                     "-c:a", "libmp3lame", str(path)], check=True,
                )
                clips.append(path)
            output = directory / "complete.mp3"
            worker._join_tts_segments([
                clips[0], worker._silence_mp3(directory, "pause1.mp3", 0.9),
                clips[1], worker._silence_mp3(directory, "pause2.mp3", 0.35),
                clips[2],
            ], output)
            self.assertAlmostEqual(worker._audio_duration(output), 12.75, delta=0.15)

    def test_fixed_station_is_single_and_cta_is_brief(self):
        assets = Path(worker.__file__).with_name("assets")
        self.assertLess(worker._audio_duration(assets / "station-charon.mp3"), 1.5)
        self.assertLess(worker._audio_duration(assets / "cta-charon-natural.mp3"), 2.1)


if __name__ == "__main__":
    unittest.main()
