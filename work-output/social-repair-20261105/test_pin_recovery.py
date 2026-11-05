import importlib.util
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).parent / "candidate" / "or_pin_local.py"
spec = importlib.util.spec_from_file_location("pin_candidate", SOURCE)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PublicationRecovery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.batch_id = "20261021-181119"
        self.folder = self.base / "bulk-outbox" / self.batch_id
        self.folder.mkdir(parents=True)
        self.csv = self.folder / "pinterest-bulk.csv"
        self.csv.write_text("original submitted CSV\n", encoding="utf-8")
        self.rows = [dict(listing_id=str(4500000000+i), source_image_sha256=str(i)*64,
                          pin_image_sha256=str(i+2)*64, board_id="1150317998513708229",
                          pin_title="Original title "+str(i), schedule_trt="2026-10-22T18:00:00+03:00") for i in (1, 2)]
        self.batch = dict(batch_id=self.batch_id, status="PREPARED_NOT_SUBMITTED",
                          rows=self.rows, csv_sha256=p.sha(self.csv), created_at_utc="2026-10-21T15:11:19")
        p.write_json(self.folder / "manifest.json", self.batch)
        p.write_json(self.base / "or-pin-active-batch.json", dict(batch_id=self.batch_id, status="UPLOADED_PROCESSING"))
        self.events = [dict(r, batch_id=self.batch_id, status="ACCEPTANCE_UNKNOWN") for r in self.rows]
        self.live = [dict(id=str(1150000000000000000+i), title=r["pin_title"], board_id=r["board_id"],
                          link="https://oldiesradyo.etsy.com/listing/"+r["listing_id"],
                          created_at="2026-10-22T15:00:00") for i,r in enumerate(self.rows)]
        p.write_json(self.base / "or-pin-live-snapshot.json", dict(complete=True, checked_at_trt=p.stamp()))
        p.write_json(self.base / "or-pin-live-pins.json", self.live)
        p.write_json(self.base / "or-pin-live-boards.json",
                     [dict(id="1150317998513708229",name=b,privacy="PUBLIC") for b in p.BOARDS])

    def persist(self, events):
        (self.base / "or-pin-local-ledger.jsonl").write_text(
            "".join(json.dumps(e)+"\n" for e in events), encoding="utf-8")

    def proof(self, index):
        return dict(self.rows[index], batch_id=self.batch_id, status="PUBLISHED_VERIFIED",
                    published_pin_id=self.live[index]["id"])

    def test_partial_submission_remains_reserved(self):
        self.persist(self.events+[self.proof(0)])
        with patch.object(p,"reconcile",return_value=0):
            result=p.run(self.base,"Prepare")
        self.assertEqual(result["blockers"],["EXISTING_SUBMISSION_RESERVED_DO_NOT_REUPLOAD"])
        self.assertEqual(self.csv.read_text(),"original submitted CSV\n")

    def test_completed_terminal_events_override_historical_unknown(self):
        progress=p.batch_progress(self.base,self.batch_id,self.events+[self.proof(0),self.proof(1)],self.live)
        self.assertEqual((progress["verified"],progress["remaining"],progress["submission_pending"]),(2,0,False))

    def test_complete_reconcile_closes_batch_without_rewriting_csv_or_erasing_history(self):
        self.persist(self.events+[self.proof(0),self.proof(1)])
        old_csv=self.csv.read_bytes()
        with patch.object(p,"reconcile",return_value=0):
            result=p.run(self.base,"Reconcile")
        self.assertEqual(result["blockers"],[])
        self.assertEqual(result["status"],"YAYIN DOĞRULANDI")
        self.assertEqual(self.csv.read_bytes(),old_csv)
        self.assertEqual(sum(e["status"]=="ACCEPTANCE_UNKNOWN" for e in p.load_events(self.base)),2)
        self.assertEqual(p.read_json(self.folder/"manifest.json")["status"],"PUBLISHED_VERIFIED")
        self.assertTrue((self.folder/"DO-NOT-IMPORT.txt").exists())

    def test_repeated_reconciliation_is_idempotent(self):
        self.persist(self.events+[self.proof(0),self.proof(1)])
        with patch.object(p,"reconcile",return_value=0):
            p.run(self.base,"Reconcile")
            p.run(self.base,"Reconcile")
        self.assertEqual(sum(e["status"]=="BATCH_PUBLISHED_VERIFIED" for e in p.load_events(self.base)),1)

    def test_unpublished_row_and_current_counts_are_reported(self):
        self.persist(self.events+[self.proof(0)])
        with patch.object(p,"reconcile",return_value=0):
            result=p.run(self.base,"Reconcile")
        self.assertEqual(result["batch_progress"]["remaining"],1)
        self.assertEqual(result["blockers"],["PINTEREST_BULK_ACCEPTANCE_NOT_VERIFIED"])

    def test_two_publications_for_one_row_fail_closed(self):
        other=dict(self.proof(0),published_pin_id="1159999999999999999")
        with self.assertRaisesRegex(ValueError,"BATCH_ROW_MULTIPLE_PUBLICATIONS"):
            p.batch_progress(self.base,self.batch_id,[self.proof(0),other])

    def test_one_pin_cannot_complete_two_rows(self):
        reused=dict(self.proof(1),published_pin_id=self.proof(0)["published_pin_id"])
        with self.assertRaisesRegex(ValueError,"BATCH_PIN_REUSED"):
            p.batch_progress(self.base,self.batch_id,[self.proof(0),reused])

    def test_current_deleted_or_changed_pin_cannot_complete_batch(self):
        with self.assertRaisesRegex(ValueError,"VERIFIED_PIN_REMOTE_IDENTITY_CHANGED"):
            p.batch_progress(self.base,self.batch_id,[self.proof(0),self.proof(1)],self.live[:1])

    def test_matching_id_with_wrong_media_does_not_become_verified(self):
        self.persist(self.events)
        with patch.object(p,"visual_match",return_value=False):
            count=p.reconcile(self.base,self.live,p.load_events(self.base))
        self.assertEqual(count,0)
        self.assertEqual(p.batch_progress(self.base,self.batch_id,p.load_events(self.base))["remaining"],2)

    def test_wrong_csv_hash_cannot_mark_batch_completed(self):
        self.persist(self.events+[self.proof(0),self.proof(1)])
        self.csv.write_text("tampered",encoding="utf-8")
        with patch.object(p,"reconcile",return_value=0):
            with self.assertRaisesRegex(ValueError,"ACTIVE_BATCH_CSV_HASH_MISMATCH"):
                p.run(self.base,"Reconcile")
        self.assertNotIn("BATCH_PUBLISHED_VERIFIED",[e["status"] for e in p.load_events(self.base)])

    def test_wrong_planned_slot_proof_is_not_counted(self):
        wrong=dict(self.proof(0),schedule_trt="2026-10-23T18:00:00+03:00")
        with self.assertRaisesRegex(ValueError,"BATCH_PUBLICATION_IDENTITY_CONFLICT"):
            p.batch_progress(self.base,self.batch_id,[wrong])

    def test_older_pin_cannot_satisfy_current_batch(self):
        older=[dict(self.live[0],created_at="2026-10-20T15:00:00"),self.live[1]]
        with self.assertRaisesRegex(ValueError,"VERIFIED_PIN_REMOTE_IDENTITY_CHANGED"):
            p.batch_progress(self.base,self.batch_id,[self.proof(0),self.proof(1)],older)

    def test_after_complete_prepare_reaches_new_candidate_checks(self):
        self.persist(self.events+[self.proof(0),self.proof(1)])
        cat=self.base/"catalog.json"
        p.write_json(cat,dict(items=[]))
        with patch.object(p,"reconcile",return_value=0),patch.object(p,"CATALOG",cat):
            result=p.run(self.base,"Prepare")
        self.assertEqual(result["blockers"],["NO_QA_PASS_STOCK"])
        self.assertEqual(p.read_json(self.folder/"manifest.json")["status"],"PUBLISHED_VERIFIED")


class PartialStock(unittest.TestCase):
    def test_general_music_board_is_consumed_without_dropping_rows(self):
        rows=[dict(listing_id=str(i),target_board=p.BOARDS[3]) for i in range(7)]
        self.assertEqual(p.spread_candidates(rows),rows)
        self.assertEqual(len(p.spread_candidates(rows*3)),14)

    def test_general_board_rejects_unrelated_product(self):
        self.assertFalse(p.board_ok(dict(original_title="Garden sculpture",keywords="home decor",target_board=p.BOARDS[3])))
        self.assertTrue(p.board_ok(dict(original_title="Country Music Cowboy Shirt",target_board=p.BOARDS[3])))

    def test_small_stock_creates_future_batch_and_reuses_exact_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            current=p.now()
            p.write_json(base/"or-pin-live-snapshot.json",dict(complete=True,checked_at_trt=p.stamp(current)))
            p.write_json(base/"or-pin-live-pins.json",[])
            p.write_json(base/"or-pin-live-boards.json",[dict(id=str(i+1),name=b,privacy="PUBLIC") for i,b in enumerate(p.BOARDS)])
            rows=[]
            approvals={}
            proofs={}
            products=[]
            for i,lid in enumerate(["4535918656","4519806799","4549965167"]):
                source=base/(lid+".jpg")
                p.Image.new("RGB",(12,18),(i*60,20,80)).save(source)
                digest=p.sha(source)
                url="https://i.etsystatic.com/123/r/il/abc/"+lid+"/il_fullxfull."+lid+"_abc.jpg"
                dest="https://oldiesradyo.etsy.com/listing/"+lid
                products.append(dict(listing_id=lid,etsy_url=dest,first_image_url=url))
                approvals[lid]=dict(source_image_sha256=digest)
                proofs[lid]=dict(source_on_page=True,listing_url=dest,source_image_url=url,checked_at_trt=p.stamp(current))
                rows.append(dict(listing_id=lid,target_board=p.BOARDS[3],original_title="Retro music shirt",keywords="music",
                    source_image_url=url,destination_url=dest,source_image_path=str(source),source_image_sha256=digest,
                    pin_image_path=str(source),pin_image_sha256=digest,pin_title="Music tee "+lid,pin_description="Original music graphic",
                    source_locked="TRUE",publish_status="READY",identity_qa="PASS",visual_qa="PASS",link_qa="PASS",board_qa="PASS"))
            cat=base/"catalog.json"
            p.write_json(cat,dict(items=products))
            p.write_json(base/"or-pin-visual-approvals.json",approvals)
            p.write_json(base/"or-pin-live-etsy-qa.json",proofs)
            p.atomic(base/"or-pin-daily-ready.csv",p.csv_text(rows,list(rows[0])))
            def remote(row,*args):
                return dict(status="PASS",sha256=row["source_image_sha256"],byte_identity=True,local_media_path=row["source_image_path"])
            with patch.object(p,"CATALOG",cat),patch.object(p,"fetch_media",side_effect=remote):
                result=p.run(base,"Prepare")
                csv_path=Path(result["batch_csv"])
                original=csv_path.read_bytes()
                second=p.run(base,"Prepare")
            self.assertEqual(result["qa_pass"],3)
            self.assertTrue(result["stock_low"])
            self.assertEqual(result["verified_scheduled"],0)
            self.assertTrue(second["batch_reused"])
            self.assertEqual(original,csv_path.read_bytes())
            planned=p.read_csv(csv_path)
            self.assertEqual(len(planned),3)
            dates=[p.datetime.fromisoformat(r["Publish date"]).replace(tzinfo=p.timezone.utc).astimezone(p.TRT) for r in planned]
            self.assertTrue(all(d>current+p.timedelta(minutes=p.LEAD_MINUTES) for d in dates))
            self.assertLessEqual(max(Counter(d.date() for d in dates).values()),2)
            # Actual publication still requires platform acceptance; preparation is not a receipt.
            self.assertEqual({e["status"] for e in p.load_events(base)},{"PREPARED"})


if __name__=="__main__":
    unittest.main(verbosity=2)
