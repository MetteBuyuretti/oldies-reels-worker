"""Offline Facebook consumer regressions: fixture bytes, no provider or media render."""
import copy
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import facebook_global_audio as audio


class FacebookSignoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / 'out'
        self.candidate = {'artist': 'The Beatles', 'event_date': '1962-10-05',
                          'kind': 'events', 'source_text': 'The Beatles released Love Me Do in Britain.'}
        self.raw = {'calm': b'fixture-calm-ending', 'energetic': b'fixture-energetic-ending'}
        self.identities = copy.deepcopy(audio.SIGNOFFS)
        for profile, identity in self.identities.items():
            identity.update(sha256=hashlib.sha256(self.raw[profile]).hexdigest(),
                            bytes=len(self.raw[profile]))
        self.calm = self.root / self.identities['calm']['asset']
        self.calm.parent.mkdir(parents=True)
        self.calm.write_bytes(self.raw['calm'])
        self.energetic = self.root / 'energetic.mp3'
        self.energetic.write_bytes(self.raw['energetic'])
        self.template = copy.deepcopy(audio.TEMPLATE)
        self.provider = Mock(return_value=b'fixture-story')
        self.story_seconds = 9.0
        self.joined = []
        self.record = Mock(side_effect=self.record_story)
        for context in (
            patch.object(audio, 'ROOT', self.root),
            patch.object(audio, 'SIGNOFFS', self.identities),
            patch.object(audio, 'TEMPLATE', self.template),
            patch.object(audio, 'record_part', self.record),
            patch.object(audio, 'inspect_audio', side_effect=self.inspect),
            patch.object(audio.subprocess, 'run', side_effect=self.join),
            patch.dict(os.environ, {'OLDIES_PREVIEW_ONLY': 'true',
                                   'OLDIES_FACEBOOK_ENERGETIC_SIGNOFF_PATH': str(self.energetic)}),
        ):
            context.start()
            self.addCleanup(context.stop)

    def record_story(self, text, role, path, project, token, synthesize):
        self.assertEqual(role, 'story', 'An accepted ending must never reach TTS')
        path.write_bytes(synthesize(text=text))
        return {'duration_seconds': self.story_seconds, 'estimated_wpm': 120,
                'tempo_factor': 1.0}

    def inspect(self, path):
        profile = self.candidate.get('signoff_profile', self.template['signoff_profile'])
        duration = self.identities[profile]['duration_seconds']
        if Path(path).name != 'dj-advert-en.mp3':
            duration += self.story_seconds + self.template['advert_gap_seconds']
        return {'duration_seconds': duration}

    def join(self, command, **kwargs):
        if command[0] != 'ffmpeg' or '-filter_complex' not in command:
            raise AssertionError('Unexpected subprocess in offline test')
        ending = Path(command[command.index('-filter_complex') - 1])
        self.joined.append(ending.read_bytes())
        Path(command[-1]).write_bytes(b'fixture-combined')

    def consume(self, profile='calm'):
        self.candidate['signoff_profile'] = profile
        return audio.synthesize_dj(self.candidate, self.out, 'fixture-project',
                                   'fixture-token', self.provider)

    def test_selected_profile_is_consumed_and_bound_without_advert_tts(self):
        for profile in ('calm', 'energetic'):
            with self.subTest(profile=profile):
                self.provider.reset_mock()
                self.record.reset_mock()
                self.assertTrue(self.consume(profile).is_file())
                self.assertEqual(self.joined[-1], self.raw[profile])
                self.provider.assert_called_once()
                self.record.assert_called_once()
                record = self.candidate['dj_recording']
                self.assertEqual(record['signoff_profile'], profile)
                self.assertEqual(record['advert_sha256'], self.identities[profile]['sha256'])
                self.assertEqual(record['signoff_evidence'], audio.SIGNOFF_EVIDENCE)
                self.assertFalse(record['final_media_approved'])
                audio.require_signoff_binding(self.candidate)
                self.assertIsNone(self.template['advert_approval'])
                self.assertFalse(self.template['advert_approved'])

    def test_default_profile_is_calm(self):
        audio.synthesize_dj(self.candidate, self.out, 'fixture', 'fixture', self.provider)
        self.assertEqual(self.joined[-1], self.raw['calm'])

    def test_unknown_profile_stops_before_provider(self):
        with self.assertRaisesRegex(RuntimeError, 'unknown profile'):
            self.consume('loud')
        self.provider.assert_not_called()

    def test_changed_hash_stops_before_provider(self):
        self.calm.write_bytes(b'changed')
        with self.assertRaisesRegex(RuntimeError, 'hash mismatch'):
            self.consume()
        self.provider.assert_not_called()

    def test_missing_file_stops_before_provider(self):
        self.calm.unlink()
        with self.assertRaisesRegex(RuntimeError, 'file is missing'):
            self.consume()
        self.provider.assert_not_called()

    def test_energetic_requires_explicit_local_mapping(self):
        with patch.dict(os.environ, {'OLDIES_FACEBOOK_ENERGETIC_SIGNOFF_PATH': ''}):
            with self.assertRaisesRegex(RuntimeError, 'mapping is missing'):
                self.consume('energetic')
        self.provider.assert_not_called()

    def test_changed_recording_binding_is_rejected(self):
        self.consume()
        for key, value in (('advert_sha256', '0' * 64), ('signoff_profile', 'energetic'),
                           ('signoff_source', 'wrong'), ('signoff_evidence', 'wrong')):
            with self.subTest(key=key):
                saved = self.candidate['dj_recording'][key]
                self.candidate['dj_recording'][key] = value
                with self.assertRaisesRegex(RuntimeError, 'does not bind'):
                    audio.require_signoff_binding(self.candidate)
                self.candidate['dj_recording'][key] = saved
        self.candidate['signoff_profile'] = 'energetic'
        with self.assertRaisesRegex(RuntimeError, 'does not bind'):
            audio.require_signoff_binding(self.candidate)

    def test_accepted_ending_does_not_open_publication(self):
        self.consume()
        with self.assertRaisesRegex(RuntimeError, 'approval metadata'):
            audio.require_approved_signoff(self.candidate)
        with patch.dict(os.environ, {'OLDIES_PREVIEW_ONLY': 'false'}):
            self.provider.reset_mock()
            with self.assertRaisesRegex(RuntimeError, 'approval metadata'):
                self.consume()
            self.provider.assert_not_called()

    def test_wrong_decoded_duration_rejects_without_regeneration(self):
        with patch.object(audio, 'inspect_audio', return_value={'duration_seconds': 1.0}):
            with self.assertRaisesRegex(RuntimeError, 'decoded duration mismatch'):
                self.consume()
        self.provider.assert_called_once()
        self.assertFalse((self.out / 'voiceover-facebook-en.mp3').exists())

    def test_immutable_rules_cannot_be_relaxed(self):
        for key, value in (('brand_name', 'Oldies Radio'), ('crop_allowed', True),
                           ('zoom_allowed', True), ('speedup_allowed', True),
                           ('advert_gap_seconds', .1), ('maximum_period_distance_years', 3)):
            with self.subTest(key=key):
                with self.assertRaises(RuntimeError):
                    audio.validate_template(dict(self.template, **{key: value}))

    def test_no_accepted_signoff_regeneration_switch(self):
        with self.assertRaisesRegex(RuntimeError, 'regeneration'):
            audio.validate_template(dict(self.template, preview_signoff_generation_allowed=True))


if __name__ == '__main__':
    unittest.main()
