"""Real-media failure tests and Facebook-only narration regression checks."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import facebook_global_audio as audio
import worker


class FacebookAudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.candidate = {
            "artist": "The Beatles", "event_date": "1962-10-05", "kind": "events",
            "instagram_music_title": "Love Me Do", "reels_language": "en",
            "source_text": "The Beatles released their debut single, Love Me Do, in the United Kingdom.",
            "tts_language": "en-US", "dj_script_en": "The Beatles. Oldies Radyo.",
            "voiceover": {"enabled": True},
        }

    def tearDown(self):
        self.temp.cleanup()

    def media(self, name, sound=None, size="108x192", duration=10):
        path = self.directory / name
        args = ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"color=s={size}:r=10"]
        if sound:
            args += ["-f", "lavfi", "-i", sound, "-c:a", "aac"]
        args += ["-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
        subprocess.run(args, check=True)
        return path

    def test_audio_less_mp4_blocks_before_release_and_wordpress(self):
        video = self.media("no-audio.mp4")
        with patch.object(worker, "publish_delivery_asset") as delivery, patch.object(worker.requests, "post") as post:
            with self.assertRaisesRegex(RuntimeError, "no populated audio stream"):
                worker.publish_facebook_global(self.candidate, video, "unused", "https://unused.invalid")
            delivery.assert_not_called()
            post.assert_not_called()

    def test_silent_audio_track_is_also_blocked(self):
        video = self.media("silent-track.mp4", "anullsrc=r=48000:cl=stereo")
        with self.assertRaisesRegex(RuntimeError, "no audible signal"):
            audio.validate_media(video, self.candidate)

    def test_populated_decodable_audio_is_accepted(self):
        video = self.media("voiced.mp4", "sine=frequency=440:sample_rate=48000")
        qc = audio.validate_media(video, self.candidate)
        self.assertTrue(qc["audio_stream_detected"])
        self.assertGreater(qc["audio_packets"], 0)
        self.assertEqual((qc["width"], qc["height"]), (108, 192))

    def test_missing_voiceover_metadata_is_blocked(self):
        video = self.media("voiced.mp4", "sine=frequency=440:sample_rate=48000")
        self.candidate["voiceover"]["enabled"] = False
        with self.assertRaisesRegex(RuntimeError, "metadata is missing"):
            audio.validate_media(video, self.candidate)

    def test_tts_error_is_propagated_without_silent_fallback(self):
        def failed(**kwargs):
            raise RuntimeError("TTS unavailable")
        with self.assertRaisesRegex(RuntimeError, "TTS unavailable"):
            audio.synthesize_dj(self.candidate, self.directory, "existing-project", "unused", failed)
        self.assertFalse((self.directory / "voiceover-facebook-en.mp3").exists())

    def test_disabled_tts_cannot_reach_render_or_publish(self):
        candidate = dict(self.candidate)
        candidate.pop("tts_language")
        candidate.pop("dj_script_en")
        candidate.update(score=90, facts=["First single.", "1962."], sources=[], topic="Love Me Do")
        with patch.dict(os.environ, {"OLDIES_WP_BEARER": "unused", "OLDIES_WP_BASE_URL": "https://unused.invalid",
                                     "OLDIES_REELS_LANGUAGE": "en", "OLDIES_PREVIEW_ONLY": "true", "OLDIES_TTS_ENABLED": "false"}), \
             patch.object(worker, "OUTPUT", self.directory), \
             patch.object(worker, "research_candidates", return_value=[candidate]), \
             patch.object(worker.facebook_global_visuals, "load_period_photos", return_value=([Path("one"), Path("two"), Path("three")], [])), \
             patch.object(worker, "render") as render, patch.object(worker, "publish_facebook_global") as publish:
            with self.assertRaisesRegex(RuntimeError, "English DJ voice-over is mandatory"):
                worker.main()
            render.assert_not_called()
            publish.assert_not_called()

    def test_non_english_voice_is_rejected(self):
        self.candidate["tts_language"] = "tr-TR"
        with self.assertRaisesRegex(RuntimeError, "English DJ voice-over is mandatory"):
            audio.require_voiceover(self.candidate, Path("unused"))

    def test_wrong_aspect_is_rejected(self):
        video = self.media("landscape.mp4", "sine=frequency=440:sample_rate=48000", size="192x108")
        with self.assertRaisesRegex(RuntimeError, "9:16"):
            audio.validate_media(video, self.candidate)

    def test_long_reel_is_rejected(self):
        video = self.media("long.mp4", "sine=frequency=440:sample_rate=48000", duration=19)
        with self.assertRaisesRegex(RuntimeError, "10–18-second"):
            audio.validate_media(video, self.candidate)

    def test_copy_is_short_factual_english(self):
        script = audio.build_dj_script(self.candidate)
        self.assertTrue(script.startswith("The Beatles released"))
        self.assertIn("Love Me Do", script)
        self.assertIn("Oldies Radyo", script)
        self.assertNotIn("Oldies Radio", script)
        self.assertLessEqual(len(script.split()), 38)
        self.assertNotIn("...", script)

    def test_brand_name_is_locked_and_never_translated(self):
        story, advert = audio.build_dj_parts(self.candidate)
        self.assertEqual(advert, "Oldies Radyo. Timeless music. Listen, enjoy, share.")
        self.assertNotIn("Oldies Radio", advert)

    def test_separate_advert_has_a_real_silent_gap_and_no_speedup(self):
        story = self.media("story.mp4", "sine=frequency=440:sample_rate=48000", duration=9.5)
        advert = self.media("advert.mp4", "sine=frequency=660:sample_rate=48000", duration=3.5)
        with patch.object(audio, "ROOT", self.directory):
            path = audio.synthesize_dj(self.candidate, self.directory, "existing", "unused",
                                       lambda **kwargs: (advert if kwargs['text'].startswith('Oldies') else story).read_bytes())
        record = self.candidate['dj_recording']
        self.assertFalse(record['speedup_applied'])
        self.assertEqual(record['advert_gap_seconds'], 1.1)
        self.assertGreater(record['advert_start_seconds'], record['story']['duration_seconds'])
        import array
        raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-ss', str(record['story']['duration_seconds'] + .25),
                                       '-i', str(path), '-t', '0.5', '-f', 'f32le', '-ac', '1', 'pipe:1'])
        samples = array.array('f'); samples.frombytes(raw)
        self.assertLess(max(abs(v) for v in samples), .001)
        self.assertLess(audio.validate_recording(path, self.candidate)['gap_max_volume_db'], -50)

    def test_excessive_tts_overrun_still_fails_without_speedup(self):
        source = self.media("long-take.mp4", "sine=frequency=440:sample_rate=48000", duration=18)
        with patch.object(audio, "ROOT", self.directory):
            with self.assertRaisesRegex(RuntimeError, "too long"):
                audio.synthesize_dj(self.candidate, self.directory, "existing", "unused", lambda **kwargs: source.read_bytes())
        self.assertFalse((self.directory / "voiceover-facebook-en.mp3").exists())

    def test_rushed_take_is_rejected_instead_of_extreme_stretch(self):
        source = self.media("rushed.mp4", "sine=frequency=440:sample_rate=48000", duration=3)
        with self.assertRaisesRegex(RuntimeError, "too rushed"):
            audio.synthesize_dj(self.candidate, self.directory, "existing", "unused", lambda **kwargs: source.read_bytes())

    def test_advert_tts_failure_invalidates_the_whole_recording(self):
        source = self.media("story.mp4", "sine=frequency=440:sample_rate=48000", duration=9.5)
        def synthesize(**kwargs):
            if kwargs['text'].startswith('Oldies'):
                raise RuntimeError('advert TTS failed')
            return source.read_bytes()
        with patch.object(audio, "ROOT", self.directory):
            with self.assertRaisesRegex(RuntimeError, 'advert TTS failed'):
                audio.synthesize_dj(self.candidate, self.directory, 'existing', 'unused', synthesize)
        self.assertFalse((self.directory / 'voiceover-facebook-en.mp3').exists())

    def test_approved_station_recording_is_reused_without_second_tts_call(self):
        import hashlib
        from unittest.mock import Mock
        story = self.media('story.mp4', 'sine=frequency=440:sample_rate=48000', duration=9.5)
        advert = self.media('advert.mp4', 'sine=frequency=660:sample_rate=48000', duration=3.5)
        cached = self.directory / audio.TEMPLATE['advert_asset']; cached.parent.mkdir(parents=True)
        cached.write_bytes(advert.read_bytes())
        template = dict(audio.TEMPLATE, advert_sha256=hashlib.sha256(cached.read_bytes()).hexdigest())
        synthesize = Mock(return_value=story.read_bytes())
        with patch.object(audio, 'ROOT', self.directory), patch.object(audio, 'TEMPLATE', template):
            voice = audio.synthesize_dj(self.candidate, self.directory, 'existing', 'unused', synthesize)
        self.assertEqual(synthesize.call_count, 1)
        self.assertTrue(self.candidate['dj_recording']['advert']['cached_approved_recording'])
        self.assertTrue(voice.exists())

    def test_changed_station_recording_is_blocked(self):
        story = self.media('story.mp4', 'sine=frequency=440:sample_rate=48000', duration=9.5)
        cached = self.directory / audio.TEMPLATE['advert_asset']; cached.parent.mkdir(parents=True)
        cached.write_bytes(b'changed')
        with patch.object(audio, 'ROOT', self.directory), patch.dict(audio.TEMPLATE, {'advert_sha256':'invalid'}):
            with self.assertRaisesRegex(RuntimeError, 'recording hash mismatch'):
                audio.synthesize_dj(self.candidate, self.directory, 'existing', 'unused', lambda **kw: story.read_bytes())
        self.assertFalse((self.directory/'voiceover-facebook-en.mp3').exists())

    def test_missing_recording_template_blocks_publication(self):
        with self.assertRaisesRegex(RuntimeError, 'approved warm DJ'):
            audio.validate_recording(self.directory/'missing.mp4', self.candidate)

    def test_short_complete_source_is_preferred_to_malformed_title(self):
        self.candidate['source_text'] = "The Beatles released their debut single ‘Love Me Do’ in Britain. The record also featured ‘P.S. I Love You’ on the backside."
        self.candidate['instagram_music_title'] = "Love Me Do’ in Britain. The record also featured ‘P.S. I Love You"
        script = audio.build_dj_script(self.candidate)
        self.assertTrue(script.startswith("The Beatles released their debut single ‘Love Me Do’ in Britain"))
        self.assertIn("on this day in 1962", script)
        self.assertNotIn("P.S.", script)
        self.assertLessEqual(len(script.split()), 38)


if __name__ == "__main__":
    unittest.main()
