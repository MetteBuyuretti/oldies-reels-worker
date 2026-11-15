"""Entry integration regressions: invalid inputs stop before any provider call."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import worker


class FacebookEntryPreflightTests(unittest.TestCase):
    def run_invalid(self, engine='facebook_dj', profile='calm'):
        env = {'OLDIES_TTS_ENABLED': 'true', 'OLDIES_TTS_ENGINE': engine,
               'OLDIES_FACEBOOK_SIGNOFF_PROFILE': profile}
        with patch.dict(os.environ, env, clear=True), patch.object(worker, 'google_auth_default') as auth:
            with self.assertRaises((RuntimeError, worker.VoiceoverQualityError)):
                worker.synthesize_google_voice({'reels_language': 'en'}, Path('.'))
            auth.assert_not_called()

    def test_generic_english_engine_stops_before_auth(self):
        self.run_invalid(engine='auto')

    def test_unknown_profile_stops_before_auth(self):
        self.run_invalid(profile='unknown')

    def test_missing_energetic_mapping_stops_before_auth(self):
        self.run_invalid(profile='energetic')

    def test_accepted_calm_routes_to_existing_consumer(self):
        credentials = SimpleNamespace(token='fixture-only', refresh=Mock())
        candidate = {'reels_language': 'en'}
        env = {'OLDIES_TTS_ENABLED': 'true', 'OLDIES_TTS_ENGINE': 'facebook_dj',
               'OLDIES_FACEBOOK_SIGNOFF_PROFILE': 'calm'}
        with patch.dict(os.environ, env, clear=True), patch.object(worker, 'google_auth_default', return_value=(credentials, 'fixture-project')), patch.object(worker, 'GoogleAuthRequest'), patch.object(worker.facebook_global_audio, 'synthesize_dj', return_value=Path('fixture.mp3')) as consume:
            self.assertEqual(worker.synthesize_google_voice(candidate, Path('.')), Path('fixture.mp3'))
            self.assertEqual(candidate['signoff_profile'], 'calm')
            consume.assert_called_once()
            self.assertIs(consume.call_args.args[0], candidate)

    def test_main_quarantines_and_schedule_survive_integration(self):
        facebook = Path('.github/workflows/facebook-global-en.yml').read_text()
        reels = Path('.github/workflows/reels-worker.yml').read_text()
        self.assertIn('    if: ${{ false }}\n', facebook)
        self.assertIn("    if: github.event_name == 'workflow_dispatch' && inputs.preview_only == true\n", reels)
        self.assertIn('    - cron: "23 11 * * *"\n', facebook)
        self.assertIn('    - cron: "17 9 * * *"\n', reels)
        self.assertIn('          OLDIES_TTS_ENGINE: "facebook_dj"\n', facebook)
        self.assertIn('          OLDIES_TTS_FALLBACK: "false"\n', facebook)


if __name__ == '__main__':
    unittest.main()
