"""Synthetic structural fixtures; never historical or independent review proof.
Real-byte measurement is exercised separately in test_reels_media_integration.
"""
from pathlib import Path
import unittest
from unittest.mock import patch
from editorial_quality_gate import EditorialGateError, check_approved_reel, check_photo_evidence, load_approval
from source_evidence import EvidenceError, check_script, packet_sha256, text_sha256

def sample(language="tr"):
    artist = "Test Artist"
    facts = (["Test Artist o gün stüdyoya girdi ve kaydın ilk bölümünü canlı olarak tamamladı.",
              "İkinci bölümde grubun üç üyesi aynı mikrofonun başına geçti; bu düzenleme kayıt notlarında ayrıntılı olarak anlatıldı ve eserin sonraki sürümünde de korundu."]
             if language == "tr" else
             ["Test Artist entered the studio that day and completed the opening section in a single live take.",
              "For the second section, three members shared one microphone; the session notes describe this arrangement in detail, and it remained part of the later recording."])
    opening = "Bir stüdyo gününün ayrıntılarına birlikte kulak verelim." if language == "tr" else "Let us step inside one unusually busy recording session."
    closing = "Oldies Radyo. Dinle, beğen, paylaş." if language == "tr" else "Oldies Radyo. Timeless music. Listen, enjoy, share."
    primary = "18 Oct 1964 Test Artist test-only session evidence; not a historical claim."
    secondary = "Test-only exact date: 18 October 1964. Test-only detail: three members shared one microphone."
    url = "https://www.thebeatles.com/test-only-not-real-evidence"
    c = {"artist":artist, "producer":"TEST_PRODUCER", "event_date":"1964-10-18",
         "research_date":"2026-10-18", "reels_language":language,"target_territories":["worldwide"],
         "primary_evidence":{"url":"https://www.thisdayinmusic.com/on-this-day-in-music-october-18/",
            "text":primary,"sha256":text_sha256(primary),"retrieved_at":"2026-10-18T00:00:00Z",
            "artist":artist,"event_date":"1964-10-18"},
         "source_documents":[{"url":url,"text":secondary,"sha256":text_sha256(secondary),"retrieved_at":"2026-10-18T00:00:00Z"}],
         "verified_facts":[{"url":url,"script_span":span,"source_excerpt":excerpt,"event_date":"1964-10-18",
            "artist":artist,"kind":kind} for span,excerpt,kind in zip(facts,
            ["Test-only exact date: 18 October 1964.","three members shared one microphone."],["event_date","detail"])],
         f"story_{language}":{"opening":opening,"narrative":" ".join(facts),"closing":closing},
         f"dj_script_{language}":" ".join([opening,*facts,closing]),"image_credits":[]}
    for i in range(3):
        c["image_credits"].append({"title":f"Test Artist studio photograph {i}","identity":artist,
            "media_type":"photograph","identity_source_url":url,"description_url":url,
            "url":f"https://upload.wikimedia.org/test-only-{i}.jpg","license":"CC BY 4.0",
            "license_url":"https://creativecommons.org/licenses/by/4.0/","rights_source_url":url,
            "creator":"TEST ONLY","capture_year":1964,"width":1000,"height":1000,
            "era_context":"Test-only contemporary studio photograph.","event_context":"Test-only session participants.",
            "era_source_url":url,"rights_territories":["worldwide"],"asset_sha256":text_sha256(str(i))})
    return c

def approval(c):
    return {"status":"APPROVED","reviewer":"TEST_ONLY_NOT_A_REAL_REVIEW","candidate_sha256":packet_sha256(c),
            "media_sha256":"f"*64,**{x:True for x in ("historical_sources_verified","script_facts_verified",
            "natural_dj_voice_verified","opening_narrative_closing_verified","photo_rights_identity_era_verified",
            "subtitles_sync_readability_verified","full_video_watched","full_audio_listened")},
            "visual_evidence":[{"asset_sha256":p["asset_sha256"],"artist_confirmed":True,
            "event_context_confirmed":True,"era_confirmed":True,"rights_confirmed":True,
            "evidence_url":p["description_url"]} for p in c["image_credits"]]}

class EditorialGateTests(unittest.TestCase):
    def setUp(self):
        mock=patch("editorial_quality_gate.check_media_duration",return_value={"duration_seconds":27,
            "media_sha256":"f"*64,"audio":{"decoded_seconds":27}}); mock.start(); self.addCleanup(mock.stop)

    def test_both_languages_require_full_evidence(self):
        for lang in ("tr","en"):
            c=sample(lang); self.assertEqual(check_approved_reel(c,Path("test-only"),approval(c))["status"],"PASS")

    def test_wrong_day_or_soundod_only_rejected(self):
        for lang in ("tr","en"):
            c=sample(lang); c["primary_evidence"]["url"]="https://soundod.com/on-this-day"
            with self.assertRaises(EditorialGateError): check_approved_reel(c,Path("x"),approval(c))
            c=sample(lang); c["event_date"]="1964-10-19"
            with self.assertRaises(EvidenceError): check_script(c)

    def test_untrusted_independent_source_rejected(self):
        for host in ("en.wikipedia.org","udiscovermusic.com","thisdayinmusic.com","example.org"):
            c=sample(); c["source_documents"][0]["url"]=f"https://{host}/story"
            with self.assertRaises(EvidenceError): check_script(c)

    def test_wrong_chart_date_and_changed_excerpt_rejected(self):
        for field,value in (("event_date","1964-10-17"),("source_excerpt","Invented quotation")):
            c=sample(); c["verified_facts"][0][field]=value
            with self.assertRaises(EvidenceError): check_script(c)

    def test_generic_and_unsupported_script_rejected(self):
        c=sample(); c["dj_script_tr"]="Oldies Radyo. Dinle, beğen, paylaş."
        with self.assertRaises(EvidenceError): check_script(c)
        c=sample(); c["story_tr"]["narrative"]+=" Unsupported new fact."
        with self.assertRaises(EvidenceError): check_script(c)

    def test_language_leakage_and_wrong_brand_rejected(self):
        for lang,leak in (("tr","Today the band was released"),("en","Bugün şarkı tarihinde dinle")):
            c=sample(lang); c[f"story_{lang}"]["opening"]=leak
            c[f"dj_script_{lang}"]=" ".join(c[f"story_{lang}"].values())
            with self.assertRaises(EvidenceError): check_script(c)
        c=sample("en"); c["story_en"]["closing"]="Oldies Radio. Listen, like and share."
        with self.assertRaises(EvidenceError): check_script(c)

    def test_eagles_beegees_madonna_substitutes_rejected(self):
        for title in ("Eagles eagle bird animal","Bee Gees waxwork statue","Madonna and Child painting",
                      "Madonna wax figure","Bee Gees figurine logo"):
            c=sample(); c["image_credits"][0]["title"]=title
            with self.assertRaises(EditorialGateError): check_photo_evidence(c)

    def test_duplicate_crop_and_wrong_photo_era_rejected(self):
        c=sample(); c["image_credits"][1]["asset_sha256"]=c["image_credits"][0]["asset_sha256"]
        with self.assertRaises(EditorialGateError): check_photo_evidence(c)
        for year in (1965,1966,2025):
            c=sample(); c["image_credits"][0]["capture_year"]=year
            with self.assertRaises(EditorialGateError): check_photo_evidence(c)

    def test_missing_license_and_territory_rejected(self):
        for field,value in (("license","Getty Images"),("license_url",""),("rights_territories",["US"]),("identity","Other")):
            c=sample(); c["image_credits"][0][field]=value
            with self.assertRaises(EditorialGateError): check_photo_evidence(c)

    def test_packet_media_and_each_photo_review_hash_required(self):
        for lang in ("tr","en"):
            c=sample(lang)
            for field in ("candidate_sha256","media_sha256","natural_dj_voice_verified","full_audio_listened"):
                a=approval(c); a[field]=False
                with self.assertRaises(EditorialGateError): check_approved_reel(c,Path("x"),a)
            a=approval(c); a["visual_evidence"][0]["asset_sha256"]="0"*64
            with self.assertRaises(EditorialGateError): check_approved_reel(c,Path("x"),a)
            a=approval(c); a["reviewer"]=c["producer"]
            with self.assertRaises(EditorialGateError): check_approved_reel(c,Path("x"),a)

    def test_no_external_approval_file_refuses_delivery(self):
        with self.assertRaises(EditorialGateError): load_approval("")

    def test_previously_rejected_photo_cannot_be_reintroduced(self):
        c=sample(); c["image_credits"][0]["review_status"]="REJECTED_BLUR_OR_IDENTITY"
        with self.assertRaises(EditorialGateError): check_photo_evidence(c)

if __name__=="__main__": unittest.main()
