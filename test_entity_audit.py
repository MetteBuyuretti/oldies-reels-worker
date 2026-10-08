import unittest
from unittest.mock import patch
from datetime import datetime, timezone

import zero_cost

IDENTITIES = {
    'Eagles': ('Eagles (band)', 'Q189635'),
    'Queen': ('Queen (band)', 'Q15862'),
    'Chicago': ('Chicago (band)', 'Q371938'),
    'America': ('America (band)', 'Q126852'),
    'Genesis': ('Genesis (band)', 'Q151012'),
    'Boston': ('Boston (band)', 'Q204289'),
    'Journey': ('Journey (band)', 'Q464749'),
    'Europe': ('Europe (band)', 'Q185144'),
    'Kansas': ('Kansas (band)', 'Q204328'),
    'Traffic': ('Traffic (band)', 'Q1048439'),
    'Bread': ('Bread (band)', 'Q903536'),
    'Cream': ('Cream (band)', 'Q203736'),
    'Kiss': ('Kiss (band)', 'Q124179'),
    'Yes': ('Yes (band)', 'Q184386'),
    'Rush': ('Rush (band)', 'Q203871'),
    'The Police': ('The Police', 'Q178095'),
}


class EntityAuditTests(unittest.TestCase):
    def test_canonical_band_wins_over_generic(self):
        for artist, (title, qid) in IDENTITIES.items():
            with self.subTest(artist=artist):
                generic = {'title': artist, 'wikibase_item': 'Q1'}
                band = {'title': title, 'wikibase_item': qid}
                self.assertEqual(zero_cost._page_for_artist({'pages': [generic, band]}, artist), band)

    def test_generic_only_and_near_matches_fail_closed(self):
        for artist, (title, _) in IDENTITIES.items():
            wrong_titles = [title + ' discography', 'List of ' + title + ' members']
            if title != artist:
                wrong_titles.append(artist)
            for wrong in wrong_titles:
                with self.subTest(artist=artist, wrong=wrong):
                    self.assertEqual(zero_cost._page_for_artist({'pages': [{'title': wrong, 'wikibase_item': 'Q1'}]}, artist), {})

    def test_wrong_qid_with_canonical_title_is_rejected(self):
        for artist, (title, _) in IDENTITIES.items():
            with self.subTest(artist=artist):
                self.assertEqual(zero_cost._page_for_artist({'pages': [{'title': title, 'wikibase_item': 'Q156298'}]}, artist), {})

    def test_missing_qid_fails_closed_for_ambiguous_artist(self):
        for artist, (title, _) in IDENTITIES.items():
            with self.subTest(artist=artist):
                self.assertEqual(zero_cost._page_for_artist({'pages': [{'title': title}]}, artist), {})

    def test_police_force_is_not_the_police(self):
        self.assertEqual(zero_cost._page_for_artist({'pages': [{'title': 'Police', 'wikibase_item': 'Q1'}]}, 'The Police'), {})

    def test_case_punctuation_alias_and_ampersand(self):
        page = {'title': 'Simon & Garfunkel', 'wikibase_item': 'Q484918'}
        self.assertEqual(zero_cost._page_for_artist({'pages': [page]}, 'Simon and Garfunkel'), page)
        page = {'title': 'Eagles (band)', 'wikibase_item': 'Q189635'}
        for alias in ('  EAGLES  ', 'The Eagles'):
            self.assertEqual(zero_cost._page_for_artist({'pages': [page]}, alias), page)
        self.assertEqual(zero_cost._page_for_artist({'pages': [{'title': 'Boney M.', 'wikibase_item': 'Q156298'}]}, 'Boney M.'), {'title': 'Boney M.', 'wikibase_item': 'Q156298'})

    def test_mismatch_never_becomes_scored_candidate(self):
        item = {'year': 1979, 'text': 'Eagles released an album.', 'pages': [{'title': 'Eagle', 'wikibase_item': 'Q2092297'}], 'source_url': 'https://example.test/history'}
        with patch.object(zero_cost, 'fetch_day_candidates', return_value={'events': [item]}), patch.object(zero_cost, 'fetch_music_history_candidates', return_value=[]):
            self.assertEqual(zero_cost.build_history_candidates([], today=datetime(2026, 9, 24, tzinfo=timezone.utc)), [])


if __name__ == '__main__':
    unittest.main()
