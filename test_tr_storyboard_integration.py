"""Real preview/render callable tests; synthetic images/timestamps, no real AV.

Requests and Pillow are real dependencies. Audio measurement, word timestamps
and FFmpeg/final-MP4 inspection are explicit fixtures, never media acceptance.
"""
import copy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch

from PIL import Image, ImageDraw
import worker
import video_factory
import media_evidence
import editorial_quality_gate as gate
from source_evidence import check_script, text_sha256
from test_editorial_quality_gate import sample


class StoryboardIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source_root = Path(worker.__file__).resolve().parent
        for name in ('worker.py','video_factory.py','media_evidence.py','source_evidence.py',
                     'editorial_quality_gate.py','reels_preview.py'):
            (self.root/name).write_bytes((self.source_root/name).read_bytes())
        self.candidate = sample('tr')
        self.script = check_script(self.candidate)
        for index, photo in enumerate(self.candidate['image_credits']):
            path = self.root / f'fixture-original-{index}.png'
            image = Image.new('RGB', (1000,1000), ('gray','navy','maroon')[index])
            draw = ImageDraw.Draw(image)
            for xy, color in (((0,0,100,100),'red'),((900,0,999,100),'green'),
                              ((0,900,100,999),'blue'),((900,900,999,999),'yellow')):
                draw.rectangle(xy,fill=color)
            image.save(path)
            photo.update(local_path=path.name, asset_sha256=gate.media_sha256(path),
                         composition_id=f'FIXTURE_COMPOSITION_{index}')
        voice = self.root/'fixture-voice.bin'
        voice.write_bytes(b'SYNTHETIC FIXTURE BYTES NOT AN AUDIO RECORDING')
        self.candidate.update(local_voiceover=voice.name, voice_evidence={
            'sha256':gate.media_sha256(voice),'script_sha256':text_sha256(self.script),
            'transcript':self.script,'language':'tr','unmodified_speed':True})
        words = self.script.split(); size = len(words)
        # Deliberately synthetic; reviewed_by identifies a fixture, not a person.
        self.candidate['voice_alignment'] = {'version':'word-alignment-v1',
            'timing_basis':'reviewed_audio_word_boundaries','reviewed_by':'TEST_FIXTURE_NOT_HUMAN',
            'evidence_id':'SYNTHETIC_WORD_TIMESTAMPS',
            'audio_sha256':gate.media_sha256(voice),'script_sha256':text_sha256(self.script),
            'words':[{'word':word,'start':i*27/size,'end':(i+1)*27/size}
                     for i,word in enumerate(words)]}
        ends = (0,size//3,2*size//3,size)
        self.candidate['visual_storyboard'] = {'version':'storyboard-v1',
            'profile':'legacy_short_25_30','script_sha256':text_sha256(self.script),
            'scenes':[{'scene_id':f'S{i+1}','start_word':ends[i],'end_word':ends[i+1],
                       'photo_sha256':photo['asset_sha256']}
                      for i,photo in enumerate(self.candidate['image_credits'])]}
        self.seal()
        self.commands = []
        self.provider = Mock(side_effect=AssertionError('Provider is forbidden'))
        self.voice_inspection = Mock(return_value={'decoded_seconds':27.0})
        self.contexts = [
            patch.object(worker,'__file__',str(self.root/'worker.py')),
            patch.dict(os.environ,{'OLDIES_REELS_LANGUAGE':'tr','OLDIES_ZERO_COST_DATE':'2026-10-18',
                                   'OLDIES_EDITORIAL_PACKET':'packet.json',
                                   'OLDIES_EDITORIAL_APPROVAL_MANIFEST':''}),
            patch.object(worker,'synthesize_google_voice',self.provider),
            patch.object(worker.requests.sessions.Session,'request',side_effect=AssertionError('HTTP forbidden')),
            patch.object(socket,'socket',side_effect=AssertionError('Network forbidden')),
            patch('reels_preview.inspect_audio',self.voice_inspection),
            patch.object(video_factory,'audio_duration',return_value=27.0),
            patch.object(video_factory.subprocess,'run',side_effect=self.fake_ffmpeg),
            patch.object(media_evidence,'inspect_reel',return_value={'fixture':True}),
            patch('reels_preview.check_media_duration',return_value={
                'fixture':True,'media_sha256':'f'*64,'audio':{'decoded_seconds':27.0}}),
        ]
        for context in self.contexts:
            context.start();self.addCleanup(context.stop)

    def seal(self):
        p=self.candidate['visual_storyboard']
        p.update(source_evidence_sha256=gate.storyboard_source_sha256(self.candidate),
                 photo_evidence_sha256=gate.storyboard_photos_sha256(self.candidate))

    def fake_ffmpeg(self, command, **kwargs):
        self.assertEqual(command[0],'ffmpeg')
        self.commands.append(command)
        Path(command[-1]).write_bytes(b'NOT AN MP4 - TEST CONSUMER RECEIPT ONLY')

    def run_main(self):
        (self.root/'packet.json').write_text(json.dumps(self.candidate),encoding='utf-8')
        try:
            worker.main()
        except SystemExit as exc:
            self.assertEqual(exc.code,2)
        return json.loads((self.root/'output/tr-preview/preview-status.json').read_text())

    def assert_blocked(self, text=None):
        result=self.run_main()
        self.assertEqual(result['status'],'BLOCKED_PREVIEW')
        self.assertFalse(result['video_created'])
        if text:self.assertIn(text,' '.join(result['blockers']))
        self.assertEqual(self.commands,[])
        self.provider.assert_not_called()
        return result

    def test_real_main_preview_renderer_uses_three_photo_intervals_and_eight_captions(self):
        result=self.run_main()
        self.assertEqual(result['status'],'UNAPPROVED_MEDIA_PREVIEW')
        self.assertFalse(result['editorial_approved']);self.assertFalse(result['delivery_allowed'])
        self.assertEqual(len(self.commands),1)
        command=self.commands[0];graph=command[command.index('-filter_complex')+1]
        inputs=[command[i+1] for i,x in enumerate(command) if x=='-i']
        photos=[x for x in inputs if Path(x).name.startswith('story-photo-')]
        overlays=[x for x in inputs if Path(x).name.startswith('caption-overlay-')]
        self.assertEqual(len(photos),3);self.assertEqual(len(set(photos)),3)
        self.assertEqual(len(overlays),8)
        self.assertEqual(graph.count('xfade='),2)
        self.assertEqual(graph.count('overlay=enable='),8)
        folder=Path(result['video_path']).parent
        captions=json.loads((folder/'timeline.json').read_text())
        photo_timeline=json.loads((folder/'photo-timeline.json').read_text())
        self.assertEqual(' '.join(x['text'] for x in captions),self.script)
        self.assertEqual(photo_timeline[-1]['end'],27.0)
        self.assertEqual(captions[-1]['end'],27.0)
        self.assertTrue(' '.join(x['text'] for x in captions).endswith('Oldies Radyo. Dinle, beğen, paylaş.'))
        self.assertEqual([x['photo_sha256'] for x in photo_timeline],
                         [x['asset_sha256'] for x in self.candidate['image_credits']])
        for photo in photos:
            with Image.open(photo) as image:
                self.assertEqual(image.size,(1080,1920))
                # All four source corner markers survive contain placement.
                self.assertEqual(image.getpixel((66,166)),(255,0,0))
                self.assertEqual(image.getpixel((1012,166)),(0,128,0))
                self.assertEqual(image.getpixel((66,1114)),(0,0,255))
                self.assertEqual(image.getpixel((1012,1114)),(255,255,0))
        self.provider.assert_not_called()

    def test_missing_plan_never_falls_back_to_legacy_modulo(self):
        del self.candidate['visual_storyboard'];self.assert_blocked('no legacy fallback')
        self.voice_inspection.assert_not_called()

    def test_unknown_plan_rejected_before_audio_or_renderer(self):
        self.candidate['visual_storyboard']['version']='unknown';self.assert_blocked('unknown')
        self.voice_inspection.assert_not_called()

    def test_wrong_script_binding(self):
        self.candidate['visual_storyboard']['script_sha256']='0'*64;self.assert_blocked('binding mismatch')

    def test_wrong_source_binding(self):
        self.candidate['visual_storyboard']['source_evidence_sha256']='0'*64;self.assert_blocked('binding mismatch')

    def test_wrong_photo_evidence_binding(self):
        self.candidate['visual_storyboard']['photo_evidence_sha256']='0'*64;self.assert_blocked('binding mismatch')

    def test_wrong_photo_asset_reference(self):
        self.candidate['visual_storyboard']['scenes'][1]['photo_sha256']='0'*64;self.assert_blocked('ranges/photos')

    def test_gap_in_word_coverage(self):
        self.candidate['visual_storyboard']['scenes'][1]['start_word']+=1;self.assert_blocked('ranges/photos')

    def test_overlap_in_word_coverage(self):
        self.candidate['visual_storyboard']['scenes'][1]['start_word']-=1;self.assert_blocked('ranges/photos')

    def test_closing_cannot_be_omitted(self):
        self.candidate['visual_storyboard']['scenes'][-1]['end_word']-=1;self.assert_blocked('exact closing')

    def test_rejected_photo_cannot_render(self):
        self.candidate['image_credits'][0]['review_status']='REJECTED_BY_USER';self.seal();self.assert_blocked('rejected')

    def test_renamed_rejected_photo_hash_cannot_render(self):
        self.candidate['rejected_visual_sha256']=[self.candidate['image_credits'][0]['asset_sha256']]
        self.assert_blocked('rejected/cropped/derived')

    def test_derived_photo_identity_cannot_bypass_diversity(self):
        self.candidate['image_credits'][1]['derived_from_sha256']=self.candidate['image_credits'][0]['asset_sha256']
        self.seal();self.assert_blocked('derived')

    def test_duplicate_composition_cannot_bypass_distinct_bytes(self):
        self.candidate['image_credits'][1]['composition_id']=self.candidate['image_credits'][0]['composition_id']
        self.seal();self.assert_blocked('composition')

    def test_missing_rights_rejected_before_render(self):
        self.candidate['image_credits'][0]['license_url']='';self.seal();self.assert_blocked('license/rights')

    def test_photo_bytes_change_rejected(self):
        (self.root/self.candidate['image_credits'][0]['local_path']).write_bytes(b'changed')
        self.assert_blocked('photo hash')

    def test_missing_alignment_is_not_estimated_from_words(self):
        del self.candidate['voice_alignment'];self.assert_blocked('alignment is required')

    def test_estimated_alignment_is_not_accepted_as_measured(self):
        self.candidate['voice_alignment']['timing_basis']='estimated_word_rate';self.assert_blocked('estimates')

    def test_overlapping_word_timestamps_rejected(self):
        self.candidate['voice_alignment']['words'][1]['start']=0;self.assert_blocked('without overlap')

    def test_changed_voice_bytes_cannot_use_old_alignment(self):
        (self.root/self.candidate['local_voiceover']).write_bytes(b'changed voice fixture')
        self.assert_blocked('Local narration')

    def test_alignment_end_must_match_measured_voice(self):
        self.voice_inspection.return_value={'decoded_seconds':26.5};self.assert_blocked('measured natural audio')

    def test_ten_second_voice_remains_rejected(self):
        with patch.object(video_factory,'audio_duration',return_value=10.0):
            self.assert_blocked('25-30s')

    def test_over_thirty_second_voice_remains_rejected(self):
        with patch.object(video_factory,'audio_duration',return_value=30.01):
            self.assert_blocked('25-30s')

    def test_missing_independent_approval_cannot_reach_delivery(self):
        with patch.object(worker.requests,'post',side_effect=AssertionError('network')) as post:
            with self.assertRaises(gate.EditorialGateError):
                worker.publish_facebook_global(self.candidate,Path('fixture-only'),'unused','https://unused.invalid')
            post.assert_not_called()


if __name__=='__main__':unittest.main()
