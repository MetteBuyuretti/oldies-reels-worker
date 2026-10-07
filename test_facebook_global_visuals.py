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
                          manual_period_override=False, manual_period_note='',
                          **{flag: True for flag in visuals.REVIEW_FLAGS})
        self.candidate = dict(artist='The Beatles', event_date='1962-10-05')

    def tearDown(self):
        self.temp.cleanup()

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
        self.photo['manual_period_override'] = True
        self.photo['manual_period_note'] = 'Owner/editor confirmed appearance and era match.'
        self.assertEqual(visuals.validate_photo(self.photo, 'The Beatles', 1962, self.root), self.root/'photo.jpg')

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
        (self.root / visuals.TEMPLATE['photo_bank']).write_text(json.dumps({'photos':[plus_one, same, third]}))
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
        with patch.object(worker.facebook_global_audio,'validate_media'), patch.object(worker.facebook_global_audio,'validate_recording'), patch.object(worker,'publish_delivery_asset') as upload, patch.object(worker.requests,'post') as post:
            with self.assertRaisesRegex(RuntimeError, 'three distinct'):
                worker.publish_facebook_global(self.candidate, self.root/'unused.mp4', 'unused', 'https://unused.invalid')
            upload.assert_not_called(); post.assert_not_called()


if __name__ == '__main__': unittest.main()
