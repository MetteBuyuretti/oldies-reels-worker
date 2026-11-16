import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import english_review as review

class ReviewTests(unittest.TestCase):
    def setUp(self):
        context=patch.dict('os.environ', {'GITHUB_EVENT_NAME':'unit-test'})
        context.start();self.addCleanup(context.stop)
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

class NewsProfileTests(unittest.TestCase):
    def test_news_and_calm_have_separate_natural_speech_rules(self):
        import facebook_global_audio as audio
        self.assertEqual(audio.speech_rules({'delivery_profile':'news-upbeat-v1'}),(145,160))
        self.assertEqual(audio.speech_rules({}),(128,138))
    def test_news_uses_licensed_driving_bed_at_audible_level(self):
        self.assertEqual(review.MUSIC['title'],'News Theme')
        self.assertEqual(review.PROFILE['bed_lufs'],-24)
        self.assertIn('CC BY 4.0',review.CREDIT)

class PauseCleanupTests(unittest.TestCase):
    def test_only_detected_silent_samples_are_removed(self):
        import io, math, struct, wave
        rate=24000
        tone=b''.join(struct.pack('<h',int(8000*math.sin(2*math.pi*440*i/rate))) for i in range(rate))
        out=io.BytesIO()
        with wave.open(out,'wb') as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
            w.writeframes(tone+b'\0'*(2*rate*2)+tone+b'\0'*(int(1.2*rate)*2))
        with tempfile.TemporaryDirectory() as t:
            cleaned=review.clean_provider_pauses(out.getvalue(),Path(t))
            with wave.open(io.BytesIO(cleaned),'rb') as w:
                frames=w.readframes(w.getnframes());duration=w.getnframes()/rate
            self.assertAlmostEqual(duration,2.66,places=2)
            self.assertEqual(frames[:len(tone)],tone)
            self.assertIn(tone,frames[len(tone):])
            info=json.loads((Path(t)/'provider-pause-edits.json').read_text())
            self.assertFalse(info['speech_samples_changed'])
            self.assertEqual(info['speech_tempo_factor'],1.0)
    def test_recovery_rejects_different_transcript_before_download(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'.github').mkdir()
            (root/'.github/manual-english-review-trigger').write_text(json.dumps({'recover_provider':{'story_sha256':'other'}}))
            with patch.object(review,'ROOT',root),patch.dict('os.environ',{'GITHUB_EVENT_NAME':'push'}),patch.object(review.requests,'get') as get:
                with self.assertRaises(RuntimeError):review.recovered_provider_take('different story')
                get.assert_not_called()

if __name__=='__main__': unittest.main()
