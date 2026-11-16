import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import english_review as review

class ReviewTests(unittest.TestCase):
    def test_reservation_survives_fresh_process(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t)/'state.json'; first=review.Ledger(p)
            self.assertTrue(first.reserve('2026-11-17','a'))
            second=review.Ledger(p)
            self.assertFalse(second.reserve('2026-11-17','b'))
            self.assertFalse(second.reserve('2026-11-18','a'))
    def test_completed_delivery_requires_matching_reservation(self):
        with tempfile.TemporaryDirectory() as t:
            ledger=review.Ledger(Path(t)/'state.json'); ledger.reserve('2026-11-17','a')
            with self.assertRaises(RuntimeError):
                ledger.complete({'production_day':'2026-11-17','event_key':'b','sha256':'x'})
            ledger.complete({'production_day':'2026-11-17','event_key':'a','sha256':'x'})
            self.assertEqual(ledger.data['events']['a']['status'],'artifact_saved')
    def test_free_provider_never_falls_back_or_retries(self):
        with patch.dict('os.environ', {'GEMINI_API_KEY':'fixture'}), patch.object(review.requests,'post') as post:
            post.return_value.ok=False; post.return_value.status_code=429
            with self.assertRaises(RuntimeError): review.free_tts(prompt='warm',text='test')
            self.assertEqual(post.call_count,1)
            self.assertIn(review.MODEL,post.call_args.args[0])
            self.assertNotIn('fixture',post.call_args.args[0])
    def test_licensed_music_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as t, patch.object(review.requests,'get') as get:
            get.return_value.content=b'changed music'
            with self.assertRaises(RuntimeError): review.licensed_music(Path(t))
    def test_no_audio_response_is_rejected(self):
        with patch.dict('os.environ', {'GEMINI_API_KEY':'fixture'}), patch.object(review.requests,'post') as post:
            post.return_value.ok=True; post.return_value.json.return_value={'candidates':[{'content':{'parts':[]}}]}
            with self.assertRaises(RuntimeError): review.free_tts(prompt='warm',text='test')
    def test_reservation_is_not_reported_as_delivery(self):
        with tempfile.TemporaryDirectory() as t:
            ledger=review.Ledger(Path(t)/'state.json'); ledger.reserve('2026-11-17','a')
            self.assertEqual(ledger.data['days']['2026-11-17']['status'],'reserved')
    def test_event_key_changes_with_event(self):
        a={'artist':'The Beatles','event_date':'1963-11-22','source_text':'Release'}
        self.assertEqual(review.event_key(a),review.event_key(dict(a,artist='THE BEATLES')))
        self.assertNotEqual(review.event_key(a),review.event_key(dict(a,event_date='1963-11-23')))

if __name__=='__main__': unittest.main()
