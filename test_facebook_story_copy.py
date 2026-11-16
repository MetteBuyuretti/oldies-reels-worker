"""Story integrity and provider-cost regressions; no network or real TTS."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import facebook_global_audio as audio

STORY = ('Between tours and radio shows, the Beatles made their second album. '
         'With the Beatles reached British shops on November twenty-second, nineteen sixty-three, '
         'mixing Lennon–McCartney originals with favourites from their stage set. '
         'Imagine hearing that record for the very first time.')


class StoryCopyTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {'artist': 'The Beatles', 'event_date': '1963-11-22', 'source_text': STORY}

    def test_all_source_sentences_reach_story(self):
        story, _ = audio.build_dj_parts(self.candidate)
        self.assertIn('British shops', story)
        self.assertIn('very first time', story)

    def test_authored_story_is_exact_and_does_not_invent_today(self):
        self.candidate['dj_story_text'] = STORY
        story, advert = audio.build_dj_parts(self.candidate)
        self.assertEqual(story, STORY)
        self.assertNotIn('on this day', story)
        self.assertEqual(advert, audio.BRAND_ADVERT)

    def test_authored_story_cannot_change_artist(self):
        self.candidate['dj_story_text'] = 'A different group made a record.'
        with self.assertRaisesRegex(RuntimeError, 'complete sourced'):
            audio.build_dj_parts(self.candidate)

    def test_long_source_is_rejected_instead_of_silently_truncated(self):
        self.candidate['source_text'] += ' Another complete sentence.' * 10
        with self.assertRaisesRegex(RuntimeError, 'complete sourced'):
            audio.build_dj_parts(self.candidate)

    def test_short_copy_stops_before_paid_provider(self):
        self.candidate['dj_story_text'] = 'The Beatles made their second album.'
        provider = Mock(side_effect=AssertionError('Provider must not be called'))
        identity = audio.SIGNOFFS['calm']
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(os.environ, {'OLDIES_PREVIEW_ONLY': 'true'}), \
             patch.object(audio, 'selected_signoff', return_value=('calm', identity, b'fixture')):
            with self.assertRaisesRegex(RuntimeError, '25–30'):
                audio.synthesize_dj(self.candidate, Path(directory), 'fixture', 'fixture', provider)
        provider.assert_not_called()

    def test_new_authored_copy_has_feasible_budget_for_both_profiles(self):
        words = audio.spoken_word_count(STORY)
        for identity in audio.SIGNOFFS.values():
            duration = audio.planned_video_seconds(words * 60 / audio.TEMPLATE['target_wpm']
                                                 + 1.1 + identity['duration_seconds'])
            self.assertGreaterEqual(duration, 25)
            self.assertLessEqual(duration, 30)


if __name__ == '__main__':
    unittest.main()
