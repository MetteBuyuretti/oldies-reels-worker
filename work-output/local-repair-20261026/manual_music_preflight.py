"""Read-only MANUAL source/receipt consistency preparation; never an import receipt.

No provider, downloader, Factory, canonical state, claim or lock is constructed.
PREPARED_FOR_REVIEW means field consistency only, not provider authenticity or QC.
"""
from pathlib import Path
import hashlib
import re

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def prepare_manual_source(source, receipt, original_metadata, *, expected_track_id, expected_source_date):
    result={'status':'UNRESOLVED','source_kind':'UNVERIFIED','requested_source_kind':'MANUAL','missing':[],
            'production_receipt':False,'import_allowed':False,'qc_approved':False,
            'provider_calls':0,'canonical_writes':0}
    source=Path(source)
    if source.is_symlink() or not source.is_file() or source.suffix.lower()!='.mp3':
        result['missing'].append('ORIGINAL_MP3');return result
    if not expected_track_id:
        result['missing'].append('VERIFIED_TRACK_ID')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',expected_source_date or ''):
        result['missing'].append('VERIFIED_SOURCE_DATE')
    if not isinstance(receipt,dict):
        result['missing'].append('EXISTING_MANUAL_RECEIPT')
    if not isinstance(original_metadata,dict):
        result['missing'].append('ORIGINAL_PROVIDER_DOWNLOAD_METADATA')
    if result['missing']:return result
    required={'source_kind':'MANUAL','track_id':expected_track_id,'source_date':expected_source_date}
    for key,wanted in required.items():
        if receipt.get(key)!=wanted or original_metadata.get(key)!=wanted:
            result['missing'].append('IDENTITY_BINDING_'+key.upper())
    actual_hash=sha256(source);actual_bytes=source.stat().st_size
    if actual_bytes<1000 or receipt.get('sha256')!=actual_hash or original_metadata.get('sha256')!=actual_hash:
        result['missing'].append('SOURCE_HASH_BINDING')
    if receipt.get('bytes')!=actual_bytes or original_metadata.get('bytes')!=actual_bytes:
        result['missing'].append('SOURCE_SIZE_BINDING')
    # Source day remains historical; never rewrite it to today's scheduling slot.
    if not result['missing']:
        result.update(status='PREPARED_FOR_REVIEW',source_kind='MANUAL',source_date=expected_source_date,
                      authenticity='NOT_ESTABLISHED_BY_LOCAL_FIELDS',human_review_required=True)
    return result
