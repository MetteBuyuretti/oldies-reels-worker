"""Photo quality gates and full-frame composition regression tests."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image, ImageDraw
import facebook_global_visuals as visuals
import worker


class FacebookVisualTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        path = self.root / 'photo.jpg'
        image = Image.new('RGB', (1600, 800), 'white'); draw = ImageDraw.Draw(image)
        for box, color in [((0,0,180,180),'red'),((1420,0,1599,180),'green'),((0,620,180,799),'blue'),((1420,620,1599,799),'yellow')]:
            draw.rectangle(box, fill=color)
        image.save(path)
        self.photo = dict(artist='The Beatles', photo_year=1963, date_evidence='1963 verified photograph',
                          source='https://commons.wikimedia.org/wiki/File:Period.jpg', license='Public domain',
                          title='File:The Beatles 1963.jpg', asset='photo.jpg', composition_id='photo-one',
                          sha256=hashlib.sha256(path.read_bytes()).hexdigest(), source_cropped=False,
                          manual_period_approvals=[], source_is_cover=False, guest_equal_weight=False, guest_distracts=False,
                          artist_is_background=False, dominance_note='All four musicians are the foreground subject.',
                          appearance_note='1962 lineup and early suits and hair verified.', reviewed_by='test editor',
                          **{flag: True for flag in visuals.REVIEW_FLAGS})
        self.candidate = dict(artist='The Beatles', event_date='1962-10-05')

    def tearDown(self):
        self.temp.cleanup()

    def audit(self):
        return {'artist':'The Beatles','event_year':1962,'same_year_review_complete':True,
                'plus_one_review_complete':True,'reason':'Same year source research did not yield three qualifying assets.',
                'reviewed_by':'test editor','reviewed_at':'2026-10-07','search_sources':['https://commons.wikimedia.org/wiki/Category:The_Beatles_in_1962']}

    def test_equal_weight_guest_is_blocked_even_with_the_correct_artist(self):
        self.photo['guest_equal_weight'] = True
        with self.assertRaisesRegex(RuntimeError, 'equal-weight guests'):
            visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root)

    def test_appearance_review_is_required(self):
        self.photo['correct_appearance'] = False
        with self.assertRaisesRegex(RuntimeError, 'appearance review'):
            visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root)

    def test_cover_and_copyright_dispute_are_rejected(self):
        p=dict(self.photo,source_is_cover=True)
        with self.assertRaisesRegex(RuntimeError,'cover'):
            visuals.validate_photo(p,'The Beatles',1962,self.root)
        p=dict(self.photo,copyright_disputed=True)
        with self.assertRaisesRegex(RuntimeError,'copyright dispute'):
            visuals.validate_photo(p,'The Beatles',1962,self.root)

    def test_plus_two_approval_cannot_be_reused_for_a_different_event_year(self):
        self.photo['photo_year']=1964
        self.photo['manual_period_approvals']=[{'event_year':1963,'approved':True,'photo_sha256':self.photo['sha256']}]
        with self.assertRaisesRegex(RuntimeError,'event-specific manual'):
            visuals.validate_photo(self.photo,'The Beatles',1962,self.root)

    def test_no_same_year_research_blocks_plus_one_fallback(self):
        photos=[]
        for i,color in enumerate(['red','green','blue']):
            path=self.root/f'photo-{i}.jpg';Image.new('RGB',(1600,800),color).save(path)
            photos.append(dict(self.photo,asset=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),composition_id=f'distinct-{i}'))
        (self.root/visuals.TEMPLATE['photo_bank']).write_text(json.dumps({'photos':photos}))
        with self.assertRaisesRegex(RuntimeError,'same-year-first source research'):
            visuals.load_period_photos(self.candidate,self.root,self.root)

    def test_valid_reviewed_period_photo_is_accepted(self):
        self.assertEqual(visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root), self.root/'photo.jpg')

    def test_wrong_period_is_rejected(self):
        self.photo['photo_year'] = 2005
        with self.assertRaisesRegex(RuntimeError, 'outside'):
            visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root)

    def test_all_review_flags_are_mandatory(self):
        for flag in visuals.REVIEW_FLAGS:
            with self.subTest(flag=flag):
                photo = dict(self.photo); photo[flag] = False
                with self.assertRaisesRegex(RuntimeError, 'approval'):
                    visuals.validate_photo(photo, 'The Beatles', 1962, self.root)

    def test_artist_must_dominate_the_composition(self):
        self.photo['artist_dominant'] = False
        with self.assertRaisesRegex(RuntimeError, 'approval'):
            visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root)

    def test_plus_two_year_photo_requires_manual_approval(self):
        self.photo['photo_year'] = 1964
        with self.assertRaisesRegex(RuntimeError, 'manual period approval'):
            visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root)
        self.photo['manual_period_approvals'] = [{'event_year':1962,'approved':True,'approved_by':'test editor',
             'approved_at':'2026-10-07','photo_sha256':self.photo['sha256'], 'reason':'No approved same-year or plus-one set exists.',
             'appearance_checks':{'hair':'Early hair matches verified reference.', 'clothing':'Early suits match reference.',
                                  'lineup':'John Paul George and Ringo remain correct.', 'stage':'Stage context consistent with the early era.'}}]
        self.assertEqual(visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root), self.root/'photo.jpg')
        self.photo['manual_period_approvals'][0]['appearance_checks']['hair'] = True
        with self.assertRaisesRegex(RuntimeError, 'manual period approval'):
            visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root)

    def test_plus_three_year_photo_is_never_automatic_or_manual_fallback(self):
        self.photo['photo_year'] = 1965
        self.photo['manual_period_override'] = True
        self.photo['manual_period_note'] = 'Even manual approval cannot exceed the hard ±2 boundary.'
        with self.assertRaisesRegex(RuntimeError, 'outside the locked event-year policy'):
            visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root)

    def test_same_year_is_selected_before_plus_one(self):
        plus_one = dict(self.photo, photo_year=1963, composition_id='plus-one')
        same = dict(self.photo, photo_year=1962, composition_id='same-year')
        p2 = self.root/'same.jpg'
        Image.new('RGB',(1600,800),'gray').save(p2)
        same['asset']='same.jpg'; same['sha256']=hashlib.sha256(p2.read_bytes()).hexdigest()
        p3 = self.root/'third.jpg'
        Image.new('RGB',(1600,800),'black').save(p3)
        third = dict(same, asset='third.jpg', sha256=hashlib.sha256(p3.read_bytes()).hexdigest(), composition_id='same-year-2')
        (self.root / visuals.TEMPLATE['photo_bank']).write_text(json.dumps({'photos':[plus_one, same, third], 'year_research':[self.audit()]}))
        photos, credits = visuals.load_period_photos(self.candidate, self.root, self.root)
        self.assertEqual([p['photo_year'] for p in credits[:2]], [1962, 1962])

    def test_statue_plaque_and_crops_are_rejected(self):
        for title in ('Beatles statue', 'Beatles plaque', 'Beatles photo cropped', 'Beatles crop'):
            with self.subTest(title=title):
                photo = dict(self.photo, title=title)
                with self.assertRaisesRegex(RuntimeError, 'crop or derived'):
                    visuals.validate_photo(photo, 'The Beatles', 1962, self.root)

    def test_wrong_artist_and_changed_asset_are_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'wrong artist'):
            visuals.validate_photo(self.photo, 'Elvis Presley', 1962, self.root)
        (self.root/'photo.jpg').write_bytes(b'changed after review')
        with self.assertRaisesRegex(RuntimeError, 'changed since review'):
            visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root)

    def test_three_copies_of_one_photo_cannot_fill_the_bank(self):
        (self.root / visuals.TEMPLATE['photo_bank']).write_text(json.dumps({'photos':[self.photo]*3}))
        with self.assertRaisesRegex(RuntimeError, 'three distinct'):
            visuals.load_period_photos(self.candidate, self.root, self.root)

    def test_landscape_photo_keeps_all_four_corners(self):
        canvas = visuals.full_frame_canvas(self.root/'photo.jpg').convert('RGB')
        # All four original corner markers remain in the contained landscape photo.
        for xy, dominant in [((75,285),'r'),((1005,285),'g'),((75,730),'b'),((1005,730),'y')]:
            r,g,b = canvas.getpixel(xy)
            self.assertTrue({'r':r>g+50 and r>b+50,'g':g>r+40 and g>b+40,'b':b>r+50 and b>g+50,'y':r>b+50 and g>b+50}[dominant])
        self.assertEqual(canvas.size, (1080,1920))

    def test_visual_publish_block_runs_before_upload_or_wordpress(self):
        with patch.object(worker.facebook_global_audio,'validate_media'), patch.object(worker.facebook_global_audio,'validate_recording'), patch.object(worker.facebook_global_audio,'require_approved_signoff'), patch.object(worker,'publish_delivery_asset') as upload, patch.object(worker.requests,'post') as post:
            with self.assertRaisesRegex(RuntimeError, 'three distinct'):
                worker.publish_facebook_global(self.candidate, self.root/'unused.mp4', 'unused', 'https://unused.invalid')
            upload.assert_not_called(); post.assert_not_called()


if __name__ == '__main__': unittest.main()
