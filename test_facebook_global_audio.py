"""Offline tests for natural Facebook timing and existing media/brand gates.

The former preview-advert-generation expectations are superseded by the accepted
cached-ending contract. All bytes and media measurements here are test fixtures.
"""
import copy
import os
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import facebook_global_audio as audio
import facebook_global_visuals as visuals
import worker
import test_facebook_signoff_integration as fixtures

INSPECT_AUDIO = audio.inspect_audio


class FacebookAudioTests(fixtures.SignoffFixture, unittest.TestCase):
    def media_qc(self, duration, width=108, height=192):
        return {'duration_seconds': duration, 'audio_stream_detected': True,
                'audio_packets': 100, 'audio_codec': 'aac',
                'streams': [{'codec_type': 'video', 'width': width, 'height': height,
                             'duration': str(duration)}]}

    def test_worker_facebook_engine_consumes_selected_ending(self):
        self.candidate.update(reels_language='en', signoff_profile='energetic')
        credentials = SimpleNamespace(token='fixture-token', refresh=Mock())
        with patch.dict(os.environ, {'OLDIES_TTS_ENABLED': 'true', 'OLDIES_TTS_ENGINE': 'facebook_dj',
                                     'OLDIES_GCP_PROJECT': 'fixture-project'}), \
             patch.object(worker, 'google_auth_default', return_value=(credentials, 'fixture-project')), \
             patch.object(worker, 'GoogleAuthRequest'), \
             patch.object(worker, '_gemini_tts_bytes', self.provider):
            voice = worker.synthesize_google_voice(self.candidate, self.out)
        self.assertTrue(voice.is_file())
        self.assertEqual(self.joined[-1], self.raw['energetic'])
        self.provider.assert_called_once()
        audio.require_signoff_binding(self.candidate)

    def test_disabled_tts_cannot_reach_render_or_publish(self):
        candidate = dict(self.candidate, score=90, facts=['Fixture fact one', 'Fixture fact two'],
                         sources=[], topic='Fixture')
        with patch.dict(os.environ, {'OLDIES_WP_BEARER': 'fixture', 'OLDIES_WP_BASE_URL': 'https://unused.invalid',
                                     'OLDIES_REELS_LANGUAGE': 'en', 'OLDIES_PREVIEW_ONLY': 'true',
                                     'OLDIES_TTS_ENABLED': 'false'}), \
             patch.object(worker, 'OUTPUT', self.out), \
             patch.object(worker, 'research_candidates', return_value=[candidate]), \
             patch.object(worker.facebook_global_visuals, 'load_period_photos',
                          return_value=([Path('one'), Path('two'), Path('three')], [])), \
             patch.object(worker, 'render') as render, \
             patch.object(worker.facebook_global_visuals, 'render') as facebook_render, \
             patch.object(worker, 'publish_facebook_global') as publish:
            with self.assertRaisesRegex(RuntimeError, 'English DJ voice-over is mandatory'):
                worker.main()
        render.assert_not_called()
        facebook_render.assert_not_called()
        publish.assert_not_called()

    def test_missing_audio_blocks_before_external_delivery(self):
        self.consume()
        with patch.object(audio, 'inspect_audio', side_effect=RuntimeError('no populated audio stream')), \
             patch.object(worker, 'publish_delivery_asset') as delivery, \
             patch.object(worker.requests, 'post') as post:
            with self.assertRaisesRegex(RuntimeError, 'no populated audio stream'):
                worker.publish_facebook_global(self.candidate, Path('fixture.mp4'),
                                               'fixture', 'https://unused.invalid')
        delivery.assert_not_called()
        post.assert_not_called()

    def test_natural_profile_segment_render_and_media_gates_agree(self):
        for profile in ('calm', 'energetic'):
            with self.subTest(profile=profile):
                voice = self.consume(profile)
                natural = self.story_seconds + 1.1 + self.identities[profile]['duration_seconds']
                duration = audio.planned_video_seconds(natural)
                self.assertGreaterEqual(duration, 25)
                self.assertLessEqual(duration, 30)
                target = self.out / 'fixture-video.mp4'
                commands = []
                def render(command, **kwargs):
                    commands.append(command)
                    Path(command[-1]).write_bytes(b'fixture-video')
                with patch.object(visuals, 'TEMPLATE', self.template), \
                     patch.object(visuals, 'inspect_audio', return_value={'duration_seconds': natural}), \
                     patch.object(visuals.subprocess, 'run', side_effect=render):
                    visuals.render([Path('one'), Path('two'), Path('three')],
                                   target, voice, self.candidate, 1000)
                times = [commands[0][i + 1] for i, value in enumerate(commands[0]) if value == '-t']
                self.assertEqual(float(times[-1]), duration)
                self.assertNotIn('atempo', ' '.join(commands[0]))
                with patch.object(audio, 'inspect_audio', return_value=self.media_qc(duration)):
                    self.assertEqual(audio.validate_media(target, self.candidate)['video_duration_seconds'], duration)

    def test_short_story_and_overrun_reject_without_time_manipulation(self):
        for seconds in (9.0, 24.0, float('nan')):
            with self.subTest(seconds=seconds):
                self.story_seconds = seconds
                with self.assertRaises(RuntimeError):
                    self.consume()
                self.assertFalse((self.out / 'voiceover-facebook-en.mp3').exists())

    def test_exact_duration_boundaries_and_nonfinite_values(self):
        self.assertEqual(audio.planned_video_seconds(24.4), 25)
        self.assertEqual(audio.planned_video_seconds(29.4), 30)
        for duration in (17.4, 24.3, 29.401, 30, 0, float('nan'), float('inf')):
            with self.subTest(duration=duration):
                with self.assertRaises(RuntimeError):
                    audio.planned_video_seconds(duration)

    def test_old_short_media_long_media_and_truncation_are_rejected(self):
        self.consume()
        for duration in (17, 24.9, 30.01, 25.0, float('nan')):
            with self.subTest(duration=duration):
                with patch.object(audio, 'inspect_audio', return_value=self.media_qc(duration)):
                    with self.assertRaises(RuntimeError):
                        audio.validate_media(Path('fixture.mp4'), self.candidate)

    def test_wrong_aspect_and_missing_metadata_still_reject(self):
        self.consume()
        duration = audio.planned_video_seconds(self.candidate['voiceover_duration_seconds'])
        with patch.object(audio, 'inspect_audio', return_value=self.media_qc(duration, 192, 108)):
            with self.assertRaisesRegex(RuntimeError, '9:16'):
                audio.validate_media(Path('fixture.mp4'), self.candidate)
        self.candidate['voiceover']['enabled'] = False
        with self.assertRaisesRegex(RuntimeError, 'metadata is missing'):
            audio.validate_media(Path('fixture.mp4'), self.candidate)

    def test_recording_timing_pace_and_segment_binding_reject_tampering(self):
        self.consume()
        original = copy.deepcopy(self.candidate)
        for part, key, value in (
            ('story', 'duration_seconds', 10), ('story', 'tempo_factor', .9),
            ('story', 'estimated_wpm', 139), ('story', 'estimated_wpm', float('nan')),
            ('advert', 'duration_seconds', 6.0),
        ):
            with self.subTest(part=part, key=key):
                self.candidate = copy.deepcopy(original)
                self.candidate['dj_recording'][part][key] = value
                with self.assertRaises(RuntimeError):
                    audio.validate_natural_recording(self.candidate, original['voiceover_duration_seconds'])

    def test_actual_gap_gate_is_preserved(self):
        self.consume()
        for level, accepted in ((-90, True), (-10, False)):
            with self.subTest(level=level):
                with patch.object(audio.subprocess, 'run', return_value=SimpleNamespace(
                        returncode=0, stderr=f'max_volume: {level} dB')):
                    if accepted:
                        self.assertLess(audio.validate_recording(Path('fixture.mp4'), self.candidate)['gap_max_volume_db'], -50)
                    else:
                        with self.assertRaisesRegex(RuntimeError, 'real silent gap'):
                            audio.validate_recording(Path('fixture.mp4'), self.candidate)

    def test_record_part_preserves_natural_take_without_retiming(self):
        target = self.out / 'natural.mp3'
        self.out.mkdir()
        # Exercise the actual recorder, while inspecting synthetic provider bytes.
        real_recorder = RECORD_PART
        with patch.object(audio, 'inspect_audio', return_value={'duration_seconds': 10}), \
             patch.object(audio.subprocess, 'run') as command:
            measured = real_recorder('A warm voice remembers a record from another day today',
                                     'story', target, 'fixture', 'fixture', self.provider)
        self.assertEqual(measured['tempo_factor'], 1.0)
        command.assert_not_called()

    def test_rushed_take_stops_instead_of_accelerating_or_stretching(self):
        self.out.mkdir()
        with patch.object(audio, 'inspect_audio', return_value={'duration_seconds': 1}), \
             patch.object(audio.subprocess, 'run') as command:
            with self.assertRaisesRegex(RuntimeError, 'too rushed'):
                RECORD_PART('A warm voice remembers a record from another day today',
                            'story', self.out / 'rushed.mp3', 'fixture', 'fixture', self.provider)
        command.assert_not_called()

    def test_brand_lock_and_complete_story_remain(self):
        story, advert = audio.build_dj_parts(self.candidate)
        self.assertIn('The Beatles', story)
        self.assertIn('1962', story)
        self.assertEqual(advert, 'Oldies Radyo. Timeless music. Listen, enjoy, share.')
        self.assertNotIn('Oldies Radio', advert)
        self.assertLessEqual(len(story.split()), self.template['max_story_words'])

    def test_real_audio_inspector_rejects_missing_stream_and_silence(self):
        self.out.mkdir()
        path = self.out / 'fixture.mp3'
        path.write_bytes(b'not-real-audio')
        for streams, stderr, message in (
            ([], '', 'no populated audio stream'),
            ([{'codec_type': 'audio', 'nb_read_packets': '10', 'duration': '26', 'codec_name': 'mp3'}],
             'mean_volume: -80 dB max_volume: -70 dB', 'no audible signal'),
        ):
            with self.subTest(message=message):
                probe = SimpleNamespace(stdout=json.dumps({'streams': streams}))
                decoded = SimpleNamespace(returncode=0, stderr=stderr)
                with patch.object(audio.subprocess, 'run', side_effect=[probe, decoded]):
                    with self.assertRaisesRegex(RuntimeError, message):
                        INSPECT_AUDIO(path)


# Save the true implementation before fixture setUp installs a recording stub.
RECORD_PART = audio.record_part

if __name__ == '__main__':
    unittest.main()
