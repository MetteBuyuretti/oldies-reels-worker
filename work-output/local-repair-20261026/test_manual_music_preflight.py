import sys
sys.dont_write_bytecode=True
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
from manual_music_preflight import prepare_manual_source,sha256

class ManualSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'original.mp3'
        self.path.write_bytes(b'synthetic-test-fixture'*100)
        self.meta={'source_kind':'MANUAL','track_id':'fixture-track-19','source_date':'2026-10-19',
                   'sha256':sha256(self.path),'bytes':self.path.stat().st_size}
    def tearDown(self):self.temp.cleanup()
    def prepare(self,receipt=None,metadata=None,**kwargs):
        return prepare_manual_source(self.path,receipt,metadata,expected_track_id=kwargs.get('track','fixture-track-19'),expected_source_date=kwargs.get('day','2026-10-19'))
    def test_missing_existing_receipt_stays_unresolved(self):
        self.assertEqual(self.prepare()['status'],'UNRESOLVED')
        self.assertEqual(self.prepare()['source_kind'],'UNVERIFIED')
    def test_missing_track_cannot_be_inferred_from_filename(self):
        self.assertIn('VERIFIED_TRACK_ID',self.prepare(self.meta,self.meta,track=None)['missing'])
    def test_complete_consistency_is_preparation_not_import_or_qc(self):
        result=self.prepare(self.meta,self.meta)
        self.assertEqual(result['source_kind'],'MANUAL')
        self.assertEqual(result['status'],'PREPARED_FOR_REVIEW');self.assertFalse(result['production_receipt']);self.assertFalse(result['import_allowed']);self.assertFalse(result['qc_approved'])
    def test_old_slot_receipt_cannot_fill_new_manual_identity(self):
        wrong={**self.meta,'source_date':'2026-10-18'}
        self.assertIn('IDENTITY_BINDING_SOURCE_DATE',self.prepare(wrong,self.meta)['missing'])
    def test_hash_mismatch_is_unresolved(self):
        self.assertIn('SOURCE_HASH_BINDING',self.prepare({**self.meta,'sha256':'0'*64},self.meta)['missing'])
    def test_today_cannot_relabel_historical_track(self):
        self.assertEqual(self.prepare(self.meta,self.meta,day='2026-10-26')['status'],'UNRESOLVED')
    def test_preflight_preserves_source_and_receipt(self):
        before=self.path.read_bytes();meta=dict(self.meta);self.prepare(meta,meta)
        self.assertEqual(self.path.read_bytes(),before);self.assertEqual(meta,self.meta)

if __name__=='__main__':unittest.main(verbosity=2)
