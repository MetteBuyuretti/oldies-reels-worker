import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import tdim_daily as source
import english_review as review


def row(**changes):
    data={'nID':'14581','nDay':'18','nMonth':'11','nYear':'1963','nEventID':'1',
          'sArtist':'The Beatles','sDescription':'The Beatles received silver records at EMI House in London.'}
    return dict(data,**changes)


def page(*rows):
    return '\n'.join('<!--<pre>'+json.dumps(r)+'</pre>-->' for r in rows)


class DailySourceTests(unittest.TestCase):
    def test_exact_date_events_only_not_births_or_another_day(self):
        entries=source.parse_events(page(row(),row(nID='2',nDay='19'),row(nID='3',nEventID='2')),'2026-11-18')
        self.assertEqual([e['source_event_id'] for e in entries],['14581'])
        self.assertEqual(entries[0]['event_date'],'1963-11-18')

    def test_changed_layout_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,'parser returned no'):
            source.parse_events('<h1>Unexpected page</h1>','2026-11-18')

    def test_source_binding_rejects_wrong_day_artist_or_changed_event(self):
        e=source.parse_events(page(row()),'2026-11-18')[0]
        c={'artist':'The Beatles','event_date':e['event_date'],'reviewed':True,'sources':[e['source_url']],
           'daily_source':{'provider':'thisdayinmusic.com','event_id':e['source_event_id'],
                           'source_url':e['source_url'],'source_sha256':e['source_sha256']}}
        self.assertTrue(source.matches(c,e,'2026-11-18'))
        self.assertFalse(source.matches(c,e,'2026-11-19'))
        self.assertFalse(source.matches(dict(c,artist='Queen'),e,'2026-11-18'))
        self.assertFalse(source.matches(c,dict(e,source_sha256='changed'),'2026-11-18'))

    def test_no_photo_candidate_fails_before_provider(self):
        e=source.parse_events(page(row()),'2026-11-18')[0]
        with tempfile.TemporaryDirectory() as d, patch('tdim_daily.fetch_events',return_value=[e]), \
             patch.object(review,'free_tts') as tts, \
             patch('facebook_global_visuals.load_period_photos',side_effect=RuntimeError('photo missing')):
            with self.assertRaises(RuntimeError): review.select_candidate('2026-11-18',Path(d))
            tts.assert_not_called()

    def test_source_404_is_not_silently_substituted(self):
        with patch.object(source.requests,'get',side_effect=source.requests.HTTPError('404')):
            with self.assertRaises(source.requests.HTTPError): source.fetch_events('2026-11-18')


if __name__=='__main__': unittest.main()
