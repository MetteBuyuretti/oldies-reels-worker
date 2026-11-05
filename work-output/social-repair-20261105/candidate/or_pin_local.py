"""OR-PIN local CSV preparation and read-only publication reconciliation.

No browser, Desktop Commander, third party package, or publication API is used.
PREPARED is never treated as Pinterest acceptance or publication.
"""
import argparse
import csv
import hashlib
import html
import io
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image, ImageChops, ImageOps, ImageStat

TRT = timezone(timedelta(hours=3))
FIELDS = ["Title", "Media URL", "Pinterest board", "Thumbnail", "Description", "Link", "Publish date", "Keywords"]
BOARDS = ["1950s Rock and Roll Gifts", "1980s Music & Retro Gifts", "1990s Music and Nostalgia Gifts", "Classic Music & Vinyl Gifts"]
CATALOG = Path(r"C:\Users\METE\Documents\Oldies-AI-Calismalari\Aktif-Araclar\Oldies-Seller-Manager-Master-v2.0\Oldies-Seller-Manager-Master\shopier-source.json")
REVIEWED = {"4561093225", "4559672408", "4528913035", "4523159200", "4518166637", "4517213421", "4544639730", "4517161572", "4542988059", "4538343718", "4510378549", "4543593045", "4531162010", "4518079736"}
# Exact original Etsy sources visually reviewed against live listings on 2026-11-05.
# Their individual source hashes and expiring DOM proofs remain mandatory.
REVIEWED.update({"4540159763", "4535918656", "4519806799", "4549965167", "4536185296", "4522282376", "4528886349", "4515468513"})
LEAD_MINUTES = 15


def now():
    return datetime.now(TRT).replace(microsecond=0)


def stamp(dt=None):
    return (dt or now()).isoformat(timespec="seconds")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def write_json(path, value):
    atomic(path, json.dumps(value, ensure_ascii=False, indent=2))


def read_json(path, default=None):
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if Path(path).exists() else default


def read_csv(path):
    if not Path(path).exists():
        return []
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def csv_text(rows, fields):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return "\ufeff" + buf.getvalue()


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(value or "").replace("&39;", "'")).strip()


def listing_id(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ("etsy.com", "www.etsy.com", "oldiesradyo.etsy.com"):
        return None
    if parsed.username or parsed.password or parsed.port:
        return None
    match = re.match(r"^/listing/(\d+)(?:/|$)", parsed.path)
    return match.group(1) if match else None


def url_key(url):
    parsed = urllib.parse.urlparse(url)
    return parsed.hostname, parsed.path


def etsy_media_key(url):
    match = re.search(r"/il_[^.]+\.([^/]+)$", urllib.parse.urlparse(url).path)
    return match.group(1) if match else None


def board_ok(row):
    title = (row.get("original_title", "") + " " + row.get("keywords", "")).lower()
    board = row.get("target_board")
    patterns = {BOARDS[0]: r"195\d|50s|fifties|rockabilly", BOARDS[1]: r"198\d|80s|eighties", BOARDS[2]: r"199\d|90s|nineties", BOARDS[3]: r"music|rock|vinyl|guitar|merseybeat|mods|country"}
    return board in patterns and bool(re.search(patterns[board], title))


def validation_errors(row, catalog, boards, approvals, live_evidence=None):
    errors = []
    lid = row.get("listing_id", "")
    product = catalog.get(lid)
    if listing_id(row.get("destination_url", "")) != lid:
        errors.append("ETSY_URL_ID_MISMATCH")
    if not product or listing_id(product.get("etsy_url", "")) != lid:
        errors.append("CATALOG_ID_MISMATCH")
    urls = ([product.get("first_image_url", "")] + product.get("image_urls", [])) if product else []
    if url_key(row.get("source_image_url", "")) not in [url_key(u) for u in urls]:
        errors.append("SOURCE_NOT_IN_LISTING_CATALOG")
    if live_evidence is not None:
        proof = live_evidence.get(lid, {})
        if not proof.get("source_on_page") or listing_id(proof.get("listing_url", "")) != lid or not etsy_media_key(row.get("source_image_url", "")) or etsy_media_key(proof.get("source_image_url", "")) != etsy_media_key(row["source_image_url"]):
            errors.append("LIVE_ETSY_SOURCE_PROOF_MISSING")
        elif current_age_days(proof.get("checked_at_trt", "")) > 7:
            errors.append("LIVE_ETSY_SOURCE_PROOF_EXPIRED")
    image = urllib.parse.urlparse(row.get("source_image_url", ""))
    if image.scheme != "https" or image.hostname != "i.etsystatic.com":
        errors.append("UNTRUSTED_MEDIA_URL")
    if not board_ok(row) or row.get("target_board") not in boards:
        errors.append("BOARD_MISMATCH")
    for field in ["identity_qa", "visual_qa", "link_qa", "board_qa"]:
        if row.get(field) != "PASS":
            errors.append("QA_" + field.upper())
    if row.get("source_locked") != "TRUE" or row.get("publish_status") != "READY":
        errors.append("SOURCE_OR_PUBLISH_GATE")
    if lid not in REVIEWED or approvals.get(lid, {}).get("source_image_sha256") != row.get("source_image_sha256"):
        errors.append("VISUAL_REVIEW_REQUIRED")
    for prefix in ["source", "pin"]:
        try:
            path = Path(row[prefix + "_image_path"])
            if not path.is_file() or sha(path).lower() != row[prefix + "_image_sha256"].lower():
                errors.append(prefix.upper() + "_HASH_MISMATCH")
        except (OSError, KeyError):
            errors.append(prefix.upper() + "_FILE_MISSING")
    if not 1 <= len(clean(row.get("pin_title"))) <= 100:
        errors.append("TITLE_LENGTH")
    if not 1 <= len(clean(row.get("pin_description"))) <= 500:
        errors.append("DESCRIPTION_LENGTH")
    return errors


def current_age_days(timestamp):
    try:
        return (now() - datetime.fromisoformat(timestamp)).total_seconds() / 86400
    except ValueError:
        return 999


def duplicate_errors(row, history, live, selected):
    errors = []
    lid, source = row["listing_id"], row["source_image_sha256"].lower()
    final = row["pin_image_sha256"].lower()
    # Conservative first-exposure policy also blocks same listing with a different image.
    if any(listing_id(p.get("link", "")) == lid for p in live):
        errors.append("LIVE_LISTING_EXISTS")
    if any(clean(p.get("title")) == clean(row["pin_title"]) for p in live):
        errors.append("LIVE_TITLE_EXISTS")
    for old in history + selected:
        old_source = old.get("source_image_sha256", "").lower()
        old_final = old.get("pin_image_sha256", "").lower()
        if old.get("listing_id") == lid and source == old_source:
            errors.append("LISTING_SOURCE_DUPLICATE")
        if source in (old_source, old_final) or final in (old_source, old_final):
            errors.append("FINAL_OR_MEDIA_HASH_DUPLICATE")
        if old.get("listing_id") == lid:
            errors.append("LEDGER_LISTING_EXISTS")
    return sorted(set(errors))


def slot_utc(day, clock):
    if clock not in ("18:00", "22:00", "00:30"):
        raise ValueError("INVALID_TRT_SLOT")
    local = datetime.fromisoformat(day + "T" + clock).replace(tzinfo=TRT)
    return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def slots(current, count, occupied):
    day = current.date()
    result = []
    while len(result) < count:
        for clock in ("18:00", "22:00"):
            dt = datetime.fromisoformat(day.isoformat() + "T" + clock).replace(tzinfo=TRT)
            if dt > current + timedelta(minutes=LEAD_MINUTES) and dt.isoformat(timespec="seconds") not in occupied:
                result.append(dt)
        day += timedelta(days=1)
        if day > current.date() + timedelta(days=30):
            raise ValueError("NO_FREE_SLOTS")
    return result[:count]


def spread_candidates(rows):
    groups = {b: [r for r in rows if r["target_board"] == b] for b in BOARDS}
    selected = []
    # Retain the original era weighting and also consume the general music board.
    while any(groups.values()):
        for board in (BOARDS[0], BOARDS[1], BOARDS[0], BOARDS[2], BOARDS[1], BOARDS[3]):
            if groups[board]:
                selected.append(groups[board].pop(0))
    return selected[:14]


def fetch_media(row, cache, current, media_root):
    key = row["source_image_url"]
    old = cache.get(key)
    if old and old.get("check_version") == 2 and old.get("status") == "PASS" and old.get("source_sha256") == row["source_image_sha256"] and current - datetime.fromisoformat(old["checked_at_trt"]) < timedelta(hours=20) and Path(old.get("local_media_path", "")).is_file() and sha(old["local_media_path"]) == old["sha256"]:
        return old
    result = {"checked_at_trt": stamp(current), "http_status": None, "sha256": "", "status": "BLOCKED", "check_version": 2, "source_sha256": row["source_image_sha256"]}
    try:
        request = urllib.request.Request(key, headers={"User-Agent": "OR-PIN/1.0 (+https://oldiesradyo.com)"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(30 * 1024 * 1024 + 1)
            result["http_status"] = response.status
            if response.status == 200 and response.headers.get_content_type().startswith("image/") and len(data) <= 30 * 1024 * 1024:
                result["sha256"] = hashlib.sha256(data).hexdigest()
                if result["sha256"] == row["source_image_sha256"].lower():
                    result["status"] = "PASS"
                    result["byte_identity"] = True
                else:
                    # Etsy's CDN serves differently compressed JPEG representations.
                    # Keep both hashes; permit only same dimensions with a tight
                    # decoded-pixel comparison against the visually reviewed source.
                    expected = Image.open(row["source_image_path"]).convert("RGB")
                    actual = Image.open(io.BytesIO(data)).convert("RGB")
                    if actual.size == expected.size:
                        result["decoded_pixel_rms"] = ImageStat.Stat(ImageChops.difference(actual, expected)).rms
                        result["status"] = "PASS" if max(result["decoded_pixel_rms"]) <= 3 else "REMOTE_VISUAL_CHANGED"
                    else:
                        result["status"] = "REMOTE_DIMENSIONS_CHANGED"
                    result["byte_identity"] = False
                if result["status"] == "PASS":
                    media_root.mkdir(parents=True, exist_ok=True)
                    media_path = media_root / (result["sha256"] + ".jpg")
                    if not media_path.exists():
                        temp = media_path.with_suffix(".tmp")
                        temp.write_bytes(data)
                        os.replace(temp, media_path)
                    result["local_media_path"] = str(media_path)
    except (urllib.error.URLError, TimeoutError, OSError):
        result["status"] = "MEDIA_UNAVAILABLE"
    cache[key] = result
    return result


def load_events(base):
    path = base / "or-pin-local-ledger.jsonl"
    if not path.exists():
        return []
    # Fail closed on a partial/corrupt ledger, never silently discard history.
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_event(base, event):
    with (base / "or-pin-local-ledger.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def visual_match(pin, row):
    """Require a close decoded-image match as well as Pin metadata.

    Pinterest recompresses images, so its file SHA cannot equal the Etsy SHA.
    A failed/unavailable visual check never produces a verified ledger event.
    """
    images = pin.get("media", {}).get("images", {})
    if not images:
        return False
    largest = max(images.values(), key=lambda i: i.get("width", 0) * i.get("height", 0))
    url = largest.get("url", "")
    if urllib.parse.urlparse(url).hostname != "i.pinimg.com":
        return False
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "OR-PIN/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read(30 * 1024 * 1024)
        actual = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
        expected = ImageOps.exif_transpose(Image.open(row["source_image_path"])).convert("RGB")
        if abs(actual.width / actual.height - expected.width / expected.height) > 0.02:
            return False
        diff = ImageChops.difference(actual.resize((96, 96)), expected.resize((96, 96)))
        return max(ImageStat.Stat(diff).rms) <= 8
    except (OSError, urllib.error.URLError, TimeoutError):
        return False


def reconcile(base, live, events):
    verified = {e.get("published_pin_id") for e in events if e.get("status") == "PUBLISHED_VERIFIED"}
    count = 0
    for manifest in sorted((base / "bulk-outbox").glob("*/manifest.json")):
        batch = read_json(manifest)
        if batch.get("status") == "SUPERSEDED_NOT_FOR_IMPORT":
            continue
        for row in batch["rows"]:
            matches = [p for p in live if listing_id(p.get("link", "")) == row["listing_id"]
                       and str(p.get("board_id")) == row["board_id"] and clean(p.get("title")) == row["pin_title"]
                       and p.get("created_at", "") >= batch["created_at_utc"]]
            for pin in matches:
                if pin["id"] not in verified and visual_match(pin, row):
                    event = {**row, "event_at_trt": stamp(), "status": "PUBLISHED_VERIFIED", "published_pin_id": pin["id"], "evidence": "live Pinterest API: id + listing + board + title + creation time + decoded image similarity", "batch_id": batch["batch_id"]}
                    append_event(base, event)
                    verified.add(pin["id"])
                    count += 1
    return count


def batch_progress(base, batch_id, events, live=None):
    """Resolve submitted rows using immutable, fully verified terminal events."""
    if not batch_id:
        return None
    batch = read_json(base / "bulk-outbox" / batch_id / "manifest.json")
    if not batch or not batch.get("rows"):
        raise ValueError("ACTIVE_BATCH_MANIFEST_MISSING")
    keys = ("listing_id", "source_image_sha256", "pin_image_sha256", "board_id")
    def identity(row):
        return tuple(str(row.get(k, "")).lower() for k in keys) + (clean(row.get("pin_title")), str(row.get("schedule_trt", "")))
    expected = [identity(row) for row in batch["rows"]]
    if any(not all(key) for key in expected) or len(set(expected)) != len(expected):
        raise ValueError("BATCH_ROW_IDENTITY_INVALID")
    verified = {}
    used_pins = set()
    for event in events:
        if event.get("batch_id") != batch_id or event.get("status") != "PUBLISHED_VERIFIED":
            continue
        key = identity(event)
        pin_id = str(event.get("published_pin_id", ""))
        if key not in expected or not re.fullmatch(r"\d{10,}", pin_id):
            raise ValueError("BATCH_PUBLICATION_IDENTITY_CONFLICT")
        if key in verified and verified[key] != pin_id:
            raise ValueError("BATCH_ROW_MULTIPLE_PUBLICATIONS")
        if pin_id in used_pins and verified.get(key) != pin_id:
            raise ValueError("BATCH_PIN_REUSED")
        verified[key] = pin_id
        used_pins.add(pin_id)
    if live is not None:
        by_id = {str(p.get("id")): p for p in live}
        for row in batch["rows"]:
            pin_id = verified.get(identity(row))
            if pin_id is None:
                continue
            remote = by_id.get(pin_id)
            if (not remote or listing_id(remote.get("link", "")) != row["listing_id"]
                    or str(remote.get("board_id")) != str(row["board_id"])
                    or clean(remote.get("title")) != clean(row["pin_title"])
                    or remote.get("created_at", "") < batch["created_at_utc"]):
                raise ValueError("VERIFIED_PIN_REMOTE_IDENTITY_CHANGED")
    remaining = len(expected) - len(verified)
    submitted = any(e.get("batch_id") == batch_id and e.get("status") in
                    ("SUBMITTED", "ACCEPTANCE_UNKNOWN") for e in events)
    return {"batch_id": batch_id, "total": len(expected), "verified": len(verified),
            "remaining": remaining, "complete": remaining == 0,
            "submission_pending": submitted and remaining > 0}


def close_verified_batch(base, active, progress, events):
    """A completion preserves all earlier events and never authorizes reimport."""
    if not active or not progress or not progress["complete"]:
        return
    batch_id = active["batch_id"]
    folder = base / "bulk-outbox" / batch_id
    batch = read_json(folder / "manifest.json")
    if not batch.get("csv_sha256") or sha(folder / "pinterest-bulk.csv") != batch["csv_sha256"]:
        raise ValueError("ACTIVE_BATCH_CSV_HASH_MISMATCH")
    if not any(e.get("batch_id") == batch_id and e.get("status") == "BATCH_PUBLISHED_VERIFIED"
               for e in events):
        append_event(base, {"status": "BATCH_PUBLISHED_VERIFIED", "batch_id": batch_id,
                           "event_at_trt": stamp(), "verified_rows": progress["verified"]})
    if batch.get("status") != "PUBLISHED_VERIFIED":
        batch.update(status="PUBLISHED_VERIFIED", completed_at_trt=stamp())
        write_json(folder / "manifest.json", batch)
    write_json(base / "or-pin-active-batch.json",
               {**active, "status": "PUBLISHED_VERIFIED", "verified_rows": progress["verified"]})
    atomic(folder / "DO-NOT-IMPORT.txt",
           "Completed: all rows have verified publication events. Never reimport this CSV.\n")


def record_submission(base, batch_id, evidence_path):
    if not batch_id or not re.fullmatch(r"\d{8}-\d{6}", batch_id):
        raise ValueError("INVALID_BATCH_ID")
    folder = base / "bulk-outbox" / batch_id
    manifest = read_json(folder / "manifest.json")
    evidence = Path(evidence_path or "")
    if not manifest or manifest["status"] != "PREPARED_NOT_SUBMITTED":
        raise ValueError("BATCH_NOT_ACTIVE_FOR_SUBMISSION")
    if not evidence.is_file():
        raise ValueError("SUBMISSION_EVIDENCE_FILE_REQUIRED")
    if sha(folder / "pinterest-bulk.csv") != manifest["csv_sha256"]:
        raise ValueError("BATCH_CSV_HASH_MISMATCH")
    events = load_events(base)
    if not any(e.get("batch_id") == batch_id and e["status"] == "ACCEPTANCE_UNKNOWN" for e in events):
        for row in manifest["rows"]:
            append_event(base, {**row, "status": "ACCEPTANCE_UNKNOWN", "event_at_trt": stamp(), "batch_id": batch_id, "evidence_path": str(evidence.resolve()), "evidence_sha256": sha(evidence)})
    return {"mode": "RecordSubmission", "status": "ONAY BEKLİYOR", "submitted_unverified": len(manifest["rows"]), "new_verified_published": 0, "verified_scheduled": 0, "blockers": ["SUBMISSION_RECORDED_ACCEPTANCE_NOT_VERIFIED"]}


def run(base, mode, batch_id=None, evidence_path=None):
    if mode == "RecordSubmission":
        return record_submission(base, batch_id, evidence_path)
    current = now()
    snapshot = read_json(base / "or-pin-live-snapshot.json")
    if not snapshot or not snapshot.get("complete") or current - datetime.fromisoformat(snapshot["checked_at_trt"]) > timedelta(minutes=30):
        raise ValueError("LIVE_INVENTORY_STALE_OR_INCOMPLETE")
    live = read_json(base / "or-pin-live-pins.json", [])
    boards = {b["name"]: str(b["id"]) for b in read_json(base / "or-pin-live-boards.json", []) if b["privacy"] == "PUBLIC"}
    if not all(board in boards for board in BOARDS):
        raise ValueError("REQUIRED_BOARD_MISSING")
    events = load_events(base)
    newly_verified = reconcile(base, live, events) if mode != "DryRun" else 0
    events = load_events(base)
    active = read_json(base / "or-pin-active-batch.json")
    progress = batch_progress(base, active["batch_id"], events, live) if active else None
    if mode != "DryRun":
        close_verified_batch(base, active, progress, events)
    if mode == "Reconcile":
        pending = progress is not None and progress["remaining"] > 0
        return {"mode": mode, "status": "ONAY BEKLİYOR" if pending else "YAYIN DOĞRULANDI" if progress else "TEST EDİLDİ",
                "new_verified_published": newly_verified, "verified_scheduled": 0,
                "live_pins": len(live), "batch_progress": progress,
                "blockers": ["PINTEREST_BULK_ACCEPTANCE_NOT_VERIFIED"] if pending else []}
    if mode == "Prepare" and progress and progress["submission_pending"]:
        return {"mode": mode, "status": "ONAY BEKLİYOR", "new_verified_published": newly_verified, "verified_scheduled": 0, "blockers": ["EXISTING_SUBMISSION_RESERVED_DO_NOT_REUPLOAD"], "batch_csv": str(base / "bulk-outbox" / active["batch_id"] / "pinterest-bulk.csv")}
    catalog = {str(p["listing_id"]): p for p in read_json(CATALOG)["items"]}
    approvals = read_json(base / "or-pin-visual-approvals.json", {})
    live_evidence = read_json(base / "or-pin-live-etsy-qa.json", {})
    overrides = read_json(base / "or-pin-source-overrides.json", {})
    for lid, override in overrides.items():
        if lid in catalog and live_evidence.get(lid, {}).get("source_image_url") == override.get("source_image_url"):
            catalog[lid] = {**catalog[lid], "first_image_url": override["source_image_url"], "image_urls": [override["source_image_url"]]}
    history = read_csv(base / "or-pin-published-ledger.csv")
    history += [e for e in events if e["status"] in ("SUBMITTED", "SCHEDULED_VERIFIED", "PUBLISHED_VERIFIED", "ACCEPTANCE_UNKNOWN")]
    old_schedule = read_csv(base / "or-pin-schedule-ledger.csv")
    history += [r for r in old_schedule if r.get("status") in ("SCHEDULED", "PUBLISHED")]
    occupied = set()
    for r in old_schedule:
        if r.get("status") in ("SCHEDULED", "PUBLISHED"):
            dt = datetime.fromisoformat(r["schedule_trt"]).replace(tzinfo=TRT)
            occupied.add(stamp(dt))
    cache = read_json(base / "or-pin-media-checks.json", {})
    candidates = [{**r, **overrides.get(r["listing_id"], {})} for r in read_csv(base / "or-pin-daily-ready.csv")]
    candidates.sort(key=lambda r: (BOARDS.index(r["target_board"]) if r["target_board"] in BOARDS else 9))
    selected, audit = [], []
    for row in candidates:
        errors = validation_errors(row, catalog, boards, approvals, live_evidence) + duplicate_errors(row, history, live, selected)
        if not errors:
            remote = fetch_media(row, cache, current, base / "source-assets" / "cdn-verified")
            if remote["status"] != "PASS":
                errors.append(remote["status"])
            elif any(remote["sha256"] in (old.get("pin_image_sha256", "").lower(), old.get("source_image_sha256", "").lower()) for old in history + selected):
                errors.append("REMOTE_FINAL_HASH_DUPLICATE")
        audit.append({"listing_id": row["listing_id"], "qa_status": "QA-PASS" if not errors else "BLOCKED", "reasons": ";".join(sorted(set(errors)))})
        if not errors:
            # Bulk CSV sends the actual Etsy source, not the locally rendered template.
            selected.append({**row, "rendered_pin_image_sha256": row["pin_image_sha256"], "pin_image_sha256": remote["sha256"], "pin_image_path": remote["local_media_path"], "visual_variant": "ORIGINAL_ETSY_MEDIA", "board_id": boards[row["target_board"]], "cdn_byte_identity": remote["byte_identity"], "cdn_decoded_pixel_rms": remote.get("decoded_pixel_rms", [0, 0, 0])})
    write_json(base / "or-pin-media-checks.json", cache)
    atomic(base / "or-pin-local-qa.csv", csv_text(audit, ["listing_id", "qa_status", "reasons"]))
    selected = spread_candidates(selected)
    if not selected:
        return {"mode": mode, "status": "HATALI", "qa_pass": 0, "qa_blocked": len(audit), "new_verified_published": newly_verified, "verified_scheduled": 0, "blockers": ["NO_QA_PASS_STOCK"], "exit_code": 20}
    # Reuse an existing future batch byte-for-byte; never export duplicate submissions.
    active = read_json(base / "or-pin-active-batch.json")
    if active:
        previous = read_json(base / "bulk-outbox" / active["batch_id"] / "manifest.json")
        if not previous:
            raise ValueError("ACTIVE_BATCH_MANIFEST_MISSING")
        csv_path = base / "bulk-outbox" / active["batch_id"] / "pinterest-bulk.csv"
        if not csv_path.exists() or sha(csv_path) != previous["csv_sha256"]:
            raise ValueError("ACTIVE_BATCH_CSV_HASH_MISMATCH")
        if batch_progress(base, active["batch_id"], events, live)["submission_pending"]:
            return {"mode": mode, "status": "ONAY BEKLİYOR", "qa_pass": len(selected), "new_verified_published": newly_verified, "verified_scheduled": 0, "blockers": ["PREVIOUS_BULK_SUBMISSION_REQUIRES_RECONCILIATION"], "batch_csv": str(csv_path)}
        still_valid = all(datetime.fromisoformat(r["schedule_trt"]) > current + timedelta(minutes=LEAD_MINUTES) for r in previous["rows"])
        def fingerprint(rows):
            return {(r["listing_id"], r["source_image_sha256"], r["pin_image_sha256"], r["target_board"], r["pin_title"]) for r in rows}
        same_candidates = fingerprint(previous["rows"]) == fingerprint(selected)
        if still_valid and same_candidates:
            return {"mode": mode, "status": "TEST EDİLDİ", "qa_pass": len(selected), "stock_low": len(selected) < 14, "batch_reused": True, "batch_csv": str(csv_path), "new_verified_published": newly_verified, "verified_scheduled": 0, "blockers": ["PINTEREST_LOGIN_REQUIRED_FOR_BULK_IMPORT", "CSV_ACCEPTANCE_NOT_VERIFIED"]}
    planned = slots(current, len(selected), occupied)
    csv_rows = []
    for row, dt in zip(selected, planned):
        row["pin_title"] = clean(row["pin_title"])
        row["pin_description"] = clean(row["pin_description"])
        row.update(schedule_trt=stamp(dt), publish_date=dt.date().isoformat(), publish_time_trt=dt.strftime("%H:%M"), qa_status="QA-PASS")
        csv_rows.append({"Title": row["pin_title"], "Media URL": row["source_image_url"], "Pinterest board": row["target_board"], "Thumbnail": "", "Description": row["pin_description"], "Link": row["destination_url"], "Publish date": slot_utc(row["publish_date"], row["publish_time_trt"]), "Keywords": clean(row.get("keywords"))})
    result = {"mode": mode, "status": "TEST EDİLDİ", "qa_pass": len(selected), "qa_blocked": sum(a["qa_status"] == "BLOCKED" for a in audit), "new_verified_published": newly_verified, "verified_scheduled": 0, "first_slot_trt": stamp(planned[0]), "last_slot_trt": stamp(planned[-1]), "third_slot_enabled": False, "blockers": ["PINTEREST_LOGIN_REQUIRED_FOR_BULK_IMPORT", "CSV_ACCEPTANCE_NOT_VERIFIED"], "source_provenance": "live Etsy listing DOM image + catalog identity + visually reviewed source SHA256 + live Etsy CDN; proofs expire after 7 days"}
    result["stock_low"] = len(selected) < 14
    if mode == "DryRun":
        # Test serialization and UTC without creating an uploadable outbox or ledger.
        roundtrip = list(csv.DictReader(io.StringIO(csv_text(csv_rows, FIELDS).lstrip("\ufeff"))))
        if roundtrip != csv_rows:
            raise ValueError("CSV_ROUNDTRIP_FAILED")
        result["dry_run_no_publish"] = True
        return result
    batch_id = current.strftime("%Y%m%d-%H%M%S")
    out = base / "bulk-outbox" / batch_id
    if out.exists():
        raise ValueError("BATCH_ID_ALREADY_EXISTS")
    out.mkdir(parents=True)
    atomic(out / "pinterest-bulk.csv", csv_text(csv_rows, FIELDS))
    manifest = {"batch_id": batch_id, "created_at_trt": stamp(current), "created_at_utc": current.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"), "status": "PREPARED_NOT_SUBMITTED", "csv_sha256": sha(out / "pinterest-bulk.csv"), "rows": selected, "schema_reference": "https://help.pinterest.com/en/business/article/bulk-upload-video-pins"}
    write_json(out / "manifest.json", manifest)
    for row in selected:
        append_event(base, {**row, "status": "PREPARED", "event_at_trt": stamp(), "batch_id": batch_id})
    if active:
        completed = previous.get("status") == "PUBLISHED_VERIFIED"
        previous["status"] = "PUBLISHED_VERIFIED" if completed else "SUPERSEDED_NOT_FOR_IMPORT"
        previous["next_batch_id" if completed else "superseded_by"] = batch_id
        write_json(base / "bulk-outbox" / active["batch_id"] / "manifest.json", previous)
        atomic(base / "bulk-outbox" / active["batch_id"] / "DO-NOT-IMPORT.txt", "Completed or superseded. Never reimport this CSV.\n")
        append_event(base, {"status": "COMPLETED_BATCH_REPLACED" if completed else "SUPERSEDED_BATCH", "batch_id": active["batch_id"], "replacement_batch_id": batch_id, "event_at_trt": stamp()})
    write_json(base / "or-pin-active-batch.json", {"batch_id": batch_id, "status": "PREPARED_NOT_SUBMITTED"})
    result["batch_csv"] = str(out / "pinterest-bulk.csv")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--mode", choices=["DryRun", "Prepare", "Reconcile", "RecordSubmission"], required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--batch-id")
    parser.add_argument("--evidence-path")
    args = parser.parse_args()
    try:
        result = run(args.base, args.mode, args.batch_id, args.evidence_path)
    except Exception as exc:
        # No HTTP bodies, credentials, or arbitrary exception contents in logs.
        code = str(exc) if isinstance(exc, ValueError) and re.fullmatch(r"[A-Z0-9_]+", str(exc)) else type(exc).__name__
        result = {"mode": args.mode, "status": "HATALI", "error": code, "exit_code": 30, "new_verified_published": 0, "verified_scheduled": 0}
    write_json(args.result, result)
    print(json.dumps(result, ensure_ascii=True))
    return result.get("exit_code", 0)


if __name__ == "__main__":
    sys.exit(main())
