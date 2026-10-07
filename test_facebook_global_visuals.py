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
