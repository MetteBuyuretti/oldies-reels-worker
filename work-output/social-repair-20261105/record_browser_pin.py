"""Record evidence of native web publishing; never creates a Pinterest Pin.

Invoke while the existing .or-pin-run.lock is held by the PowerShell caller.
"""
import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--base",type=Path,required=True)
ap.add_argument("--listing",required=True)
ap.add_argument("--pin-id")
args=ap.parse_args()
base=args.base
spec=importlib.util.spec_from_file_location("or_pin",base/"or_pin_local.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
stock=p.read_json(base/"work-output/social-repair-20261105/reviewed-stock-input.json")
item=next(r for r in stock if r["id"]==args.listing)
assert p.sha(item["source_image_path"])==item["source_image_sha256"],"SOURCE_HASH_CHANGED"
assert p.listing_id(item["proof"]["share_save_url"])==args.listing
assert item["proof"]["source_on_page"] and p.current_age_days(item["proof"]["checked_at_trt"])<1
snapshot=p.read_json(base/"or-pin-live-snapshot.json")
assert snapshot["complete"] and p.current_age_days(snapshot["checked_at_trt"])<30/1440,"STALE_SNAPSHOT"
live=p.read_json(base/"or-pin-live-pins.json")
boards=p.read_json(base/"or-pin-live-boards.json")
board=next(b for b in boards if b["name"]=="Classic Music & Vinyl Gifts" and b["privacy"]=="PUBLIC")
events=p.load_events(base)
common=dict(listing_id=args.listing,source_image_url=item["source"],source_image_path=item["source_image_path"],
    source_image_sha256=item["source_image_sha256"],pin_image_path=item["source_image_path"],
    pin_image_sha256=item["source_image_sha256"],pin_title=item["pin_title"],pin_description=item["pin_description"],
    alt_text=item["alt_text"],target_board=board["name"],board_id=board["id"],source_locked="TRUE",
    identity_qa="PASS",visual_qa="PASS",link_qa="PASS",board_qa="PASS",event_at_trt=p.stamp(),batch_id="BROWSER-SOCIAL-20261105")
matches=[x for x in live if p.listing_id(x.get("link",""))==args.listing]
if args.pin_id:
    assert len(matches)==1 and matches[0]["id"]==args.pin_id,"LIVE_IDENTITY_CONFLICT"
    pin=matches[0]
    assert pin["board_id"]==board["id"] and pin["title"]==item["pin_title"],"BOARD_OR_TITLE_MISMATCH"
    assert pin.get("alt_text")==item["alt_text"] and pin.get("description")==item["pin_description"],"METADATA_MISMATCH"
    assert "utm_source=Pinterest" in pin["link"] and "utm_campaign=Share" in pin["link"],"SHARE_LINK_MISSING"
    assert any(e.get("listing_id")==args.listing and e.get("status")=="ACCEPTANCE_UNKNOWN" and
        e.get("source_image_sha256")==item["source_image_sha256"] for e in events),"RESERVATION_MISSING"
    assert p.visual_match(pin,common),"PUBLISHED_IMAGE_MISMATCH"
    receipt=dict(common,status="PUBLISHED_VERIFIED",published_pin_id=pin["id"],destination_url=pin["link"],
        platform_created_at_utc=pin["created_at"],live_snapshot_checked_at_trt=snapshot["checked_at_trt"],
        evidence="Native Pinterest web save; PUBLIC board; read-only live API exact id/listing/board/title/description/alt; decoded original-image similarity")
    dest=base/"work-output/social-repair-20261105"/(args.listing+"-published-receipt.json")
    p.write_json(dest,dict(receipt=receipt,platform_pin=pin))
    if not any(e.get("published_pin_id")==pin["id"] and e.get("status")=="PUBLISHED_VERIFIED" for e in events):
        p.append_event(base,receipt)
    print(json.dumps(dict(status="PUBLISHED_VERIFIED",pin_id=pin["id"],listing_id=args.listing,evidence_path=str(dest))))
else:
    assert not matches,"LISTING_ALREADY_LIVE"
    assert not any(e.get("listing_id")==args.listing and e.get("status") in
        ("PUBLISHED_VERIFIED","ACCEPTANCE_UNKNOWN","SUBMITTED","SCHEDULED_VERIFIED") for e in events),"LISTING_RESERVED"
    today=p.now().date()
    today_pins=[x for x in live if datetime.fromisoformat(x["created_at"]).replace(tzinfo=timezone.utc).astimezone(p.TRT).date()==today]
    live_lids={p.listing_id(x.get("link","")) for x in today_pins}
    reserved={e.get("listing_id") for e in events if e.get("status")=="ACCEPTANCE_UNKNOWN" and
        e.get("event_at_trt","").startswith(today.isoformat())}-live_lids
    assert len(today_pins)+len(reserved)<2,"DAILY_LIMIT_REACHED"
    p.append_event(base,dict(common,status="ACCEPTANCE_UNKNOWN",destination_url=item["proof"]["share_save_url"],
        evidence="Exact live Etsy original and Share & Save link visually reviewed. Reserved before native web save; daily limit checked against complete read-only inventory."))
    print(json.dumps(dict(status="RESERVED_NOT_PUBLISHED",listing_id=args.listing,today_live=len(today_pins),today_other_reserved=len(reserved))))
