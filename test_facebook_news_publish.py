import unittest
import english_review as review
import facebook_news_publish as publish

class EraMusicTests(unittest.TestCase):
    def test_five_decades_choose_distinct_licensed_instrumentals(self):
        names=[]
        for decade in [1950,1960,1970,1980,1990]:
            c={'event_date':str(decade+5)+'-06-01'};track,credit=review.era_music(c)
            self.assertEqual(track['style_decade'],decade)
            self.assertTrue(track['instrumental'])
            self.assertEqual(track['license'],'CC BY 4.0')
            self.assertIn(track['title'],credit);self.assertIn('https://creativecommons.org/licenses/by/4.0/',credit)
            names.append(track['title'])
        self.assertEqual(len(set(names)),5)
    def test_unidentified_modern_news_cannot_silently_choose_a_historical_era(self):
        with self.assertRaises(RuntimeError):review.era_music({'event_date':'2026-11-17'})
    def test_explicit_artist_musical_era_can_cover_modern_news(self):
        track,_=review.era_music({'event_date':'2026-11-17','music_era_decade':1980})
        self.assertEqual(track['style_decade'],1980)

class PublicationReceiptTests(unittest.TestCase):
    def test_processing_is_not_completed_publication(self):
        r=publish.classify({'success':True,'video_id':'12345','status':{'video_status':'processing','publishing_phase':{'status':'complete'}}})
        self.assertFalse(r['publication_verified'])
    def test_dry_run_is_never_publication(self):
        r=publish.classify({'success':True,'dry_run':True,'video_id':'12345','status':{'video_status':'ready','publishing_phase':{'status':'complete'}}})
        self.assertFalse(r['publication_verified'])
    def test_ready_and_complete_with_real_id_is_verified(self):
        r=publish.classify({'success':True,'video_id':'12345','status':{'video_status':'ready','publishing_phase':{'status':'complete'}}})
        self.assertTrue(r['publication_verified']);self.assertEqual(r['permalink'],'https://www.facebook.com/reel/12345')
    def test_missing_id_or_remote_failure_cannot_report_success(self):
        for data in [{'success':True,'status':{'video_status':'ready','publishing_phase':{'status':'complete'}}},
                     {'success':False,'video_id':'12345','status':{'video_status':'ready','publishing_phase':{'status':'complete'}}}]:
            self.assertFalse(publish.classify(data)['publication_verified'])

if __name__=='__main__':unittest.main()
