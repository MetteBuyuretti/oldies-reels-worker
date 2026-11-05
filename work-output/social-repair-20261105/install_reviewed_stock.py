"""Transactional import of eight specifically reviewed original Etsy sources.
Caller must hold the existing Windows OR-PIN exclusive file lock.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

base=Path(sys.argv[1])
work=base/"work-output/social-repair-20261105"
spec=importlib.util.spec_from_file_location("pin",base/"or_pin_local.py")
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
assert p.sha(base/"or_pin_local.py").lower()=="ac7fc77dde4c10b52544bce6a525e1250de4c17dc542dabd0eb2af61b32c671b","UNEXPECTED_PREIMAGE"
stock=p.read_json(work/"reviewed-stock-input.json")
assert len(stock)==8 and len({s["id"] for s in stock})==8
proofs=p.read_json(base/"or-pin-live-etsy-qa.json",{})
approvals=p.read_json(base/"or-pin-visual-approvals.json",{})
old=p.read_csv(base/"or-pin-daily-ready.csv")
fields=list(old[0])
assert not any(r["listing_id"] in {s["id"] for s in stock} for r in old),"STOCK_ALREADY_IMPORTED"
overrides=p.read_json(base/"or-pin-source-overrides.json",{})
catalog=p.read_json(p.CATALOG)
products={str(x["listing_id"]):x for x in catalog["items"]}
rows=[]
for s in stock:
    lid=s["id"]
    assert p.sha(s["source_image_path"])==s["source_image_sha256"]
    proof=s["proof"]
    assert proof["source_on_page"] and p.listing_id(proof["listing_url"])==lid
    assert proof["source_image_url"]==s["source"] and p.current_age_days(proof["checked_at_trt"])<1
    assert p.listing_id(proof["share_save_url"])==lid
    product=products[lid]
    assert p.url_key(s["source"]) in [p.url_key(x) for x in [product.get("first_image_url","")]+product.get("image_urls",[])]
    assert lid not in overrides,"UNEXPECTED_SOURCE_OVERRIDE"
    assert 1<=len(s["pin_title"])<=100 and 1<=len(s["pin_description"])<=500 and 1<=len(s["alt_text"])<=500
    proofs[lid]={**proof,"checked_at_trt":p.datetime.fromisoformat(proof["checked_at_trt"]).astimezone(p.TRT).isoformat(timespec="seconds")}
    approvals[lid]=dict(recorded_at_trt=p.stamp(),source_image_sha256=s["source_image_sha256"],
        catalog_generated_at=catalog.get("generated_at"),review="WORK WATCHDOG: original product visual inspected in full, matched to fresh live Etsy listing image and Share & Save link. No redraw or retouch.")
    row=dict.fromkeys(fields,"")
    row.update(listing_id=lid,target_board="Classic Music & Vinyl Gifts",source_image_url=s["source"],
        destination_url=proof["share_save_url"],original_title=proof["title"],keywords=s["keywords"],
        status="PLANNED",qa_status="QA-PASS",source_image_path=s["source_image_path"],source_image_sha256=s["source_image_sha256"],
        pin_image_path=s["source_image_path"],pin_image_sha256=s["source_image_sha256"],pin_title=s["pin_title"],
        pin_description=s["pin_description"],alt_text=s["alt_text"],visual_variant="ORIGINAL_ETSY_MEDIA",source_locked="TRUE",
        identity_qa="PASS",visual_qa="PASS",link_qa="PASS",board_qa="PASS",publish_status="READY")
    rows.append(row)
names=["or_pin_local.py","or-pin-daily-ready.csv","or-pin-live-etsy-qa.json","or-pin-visual-approvals.json"]
backup=base/"backups"/("OR-PIN-STOCK-"+p.now().strftime("%Y%m%d-%H%M%S"))
backup.mkdir(parents=True)
before={name:(base/name).read_bytes() for name in names}
for name,data in before.items():
    (backup/name).write_bytes(data)
try:
    p.atomic(base/"or_pin_local.py",(work/"candidate/or_pin_local.py").read_text(encoding="utf-8-sig"))
    p.atomic(base/"or-pin-daily-ready.csv",p.csv_text(old+rows,fields))
    p.write_json(base/"or-pin-live-etsy-qa.json",proofs)
    p.write_json(base/"or-pin-visual-approvals.json",approvals)
    assert p.read_csv(base/"or-pin-daily-ready.csv")[:len(old)]==old,"OLD_ROWS_CHANGED"
    receipt=dict(installed_at_trt=p.stamp(),backup=str(backup),new_reviewed_sources=len(rows),ready_rows=len(old)+len(rows),
        code_sha256=p.sha(base/"or_pin_local.py"),files={name:dict(before_sha256=hashlib.sha256(before[name]).hexdigest(),after_sha256=p.sha(base/name)) for name in names})
    p.write_json(work/"stock-install-receipt.json",receipt)
    print(json.dumps(receipt))
except BaseException:
    for name,data in before.items():
        temp=(base/name).with_suffix(".rollback")
        temp.write_bytes(data)
        os.replace(temp,base/name)
    raise
