"""Discovery and preview boundaries; no network, credentials or model calls."""
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
import unittest
from unittest.mock import patch, Mock
import worker
import zero_cost
from reels_preview import prepare_preview, workspace_file
from source_evidence import EvidenceError
from editorial_quality_gate import EditorialGateError
from test_editorial_quality_gate import sample

TODAY=datetime(2026,10,18,tzinfo=timezone.utc)

class PipelineTests(unittest.TestCase):
    def test_discovery_uses_exact_tdim_day_and_never_wikipedia_fallback(self):
        session=Mock(); response=session.get.return_value
        response.url="https://www.thisdayinmusic.com/on-this-day-in-music-october-18/"
        response.text="<!-- hidden duplicate 18 Oct 1964 The Beatles false data -->" + \
            "<div>18</div><div>Oct</div><div>1964</div><p>The Beatles recorded several songs in the studio.</p>" + \
            "<div>19 Oct 1967</div><p>Bee Gees a different date must be ignored.</p>"
        c=zero_cost.build_history_candidates([],TODAY,session=session)
        self.assertEqual(len(c),1); self.assertEqual(c[0]["artist"],"The Beatles")
        self.assertEqual(c[0]["editorial_status"],"UNVERIFIED_DISCOVERY")
        self.assertEqual(c[0]["verified_facts"],[])
        self.assertNotIn("false data",c[0]["primary_evidence"]["text"])
        self.assertEqual(session.get.call_count,1)
        response.url="https://soundod.com/music"
        with self.assertRaises(RuntimeError): zero_cost.build_history_candidates([],TODAY,session=session)

    def test_both_channels_skip_credentials_tts_and_delivery(self):
        for lang in ("tr","en"):
            with patch.dict(os.environ,{"OLDIES_REELS_LANGUAGE":lang,"OLDIES_PREVIEW_ONLY":"false",
                    "OLDIES_TTS_ENABLED":"true","OLDIES_ZERO_COST_DATE":"2026-10-18"}), \
                 patch.object(worker,"prepare_preview",return_value={"video_created":True}) as prepare, \
                 patch.object(worker,"require_env",side_effect=AssertionError("credential read")), \
                 patch.object(worker,"synthesize_google_voice",side_effect=AssertionError("paid call")), \
                 patch.object(worker,"upload_draft",side_effect=AssertionError("WP delivery")), \
                 patch.object(worker,"publish_facebook_global",side_effect=AssertionError("FB publish")):
                worker.main(); self.assertEqual(prepare.call_args.kwargs["language"],lang)

    def test_incidental_artist_country_and_different_band_are_not_event_subjects(self):
        session=Mock(); r=session.get.return_value
        r.url="https://www.thisdayinmusic.com/on-this-day-in-music-october-18/"
        r.text=("18 Oct 1979 Buggles were at No.1 with a record. " + "Additional context. "*8 + "It aired in North America. "
                "18 Oct 1967 Bobbie Gentry topped the album chart. " + "Additional context. "*8 + "The Beatles were displaced. "
                "18 Oct 1974 Sweet Sensation were at No.1 with Sad Sweet Dreamer.")
        self.assertEqual(zero_cost.build_history_candidates([],TODAY,session=session),[])

    def test_direct_delivery_helpers_require_approval_before_network(self):
        with patch.dict(os.environ,{"OLDIES_EDITORIAL_APPROVAL_MANIFEST":""}), \
             patch.object(worker.requests,"post",side_effect=AssertionError("network")):
            for fn,args in ((worker.publish_delivery_asset,({},Path("missing"))),
                            (worker.upload_draft,({},Path("missing"),"unused","https://invalid")),
                            (worker.publish_facebook_global,({},Path("missing"),"unused","https://invalid"))):
                with self.assertRaises(EditorialGateError): fn(*args)

    def test_preview_without_corrobation_persists_blocker_and_never_renders(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); packet=sample(); packet["source_documents"]=[]
            (root/"packet.json").write_text(json.dumps(packet),encoding="utf-8")
            render=Mock(side_effect=AssertionError("render must not run"))
            r=prepare_preview(root=root,output=root/"output",today=TODAY,packet_path="packet.json",
                              discover=Mock(),render=render)
            self.assertEqual(r["status"],"BLOCKED_PREVIEW"); self.assertFalse(r["video_created"])
            self.assertTrue((root/"output/preview-status.json").is_file()); render.assert_not_called()

    def test_packet_path_cannot_escape_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(EvidenceError): workspace_file(Path(temp),"../outside.mp3")

    def test_voice_provider_disabled_does_not_import_auth_or_call_api(self):
        with patch.dict(os.environ,{"OLDIES_TTS_ENABLED":"false"}):
            self.assertIsNone(worker.synthesize_google_voice({},Path("unused")))

    def test_scene_builder_uses_real_readable_font_on_this_platform(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); photo=root/"test-panel.jpg"; Image.new("RGB",(1000,1000),"gray").save(photo)
            for lang in ("tr","en"):
                c=sample(lang)
                scenes=worker.make_timeline_scenes(c,[photo],[{"text":c[f"story_{lang}"]["opening"]}],root)
                with Image.open(scenes[0]) as image: self.assertEqual(image.size,(1080,1920))

if __name__=="__main__": unittest.main()
