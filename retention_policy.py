"""Pure, conservative retention decisions. This module never deletes anything."""
from datetime import datetime, timedelta, timezone

ACTIVE = {'DRAFT_REVIEW', 'READY_FOR_EDITS', 'BLOCKED'}
TERMINAL = {'REJECTED', 'ARCHIVED', 'LEGACY_TEST'}


def retention_decision(asset, receipt=None, *, now=None, retention_days=10):
    now = now or datetime.now(timezone.utc)
    try:
        created = datetime.fromisoformat(str(asset.get('created_at', '')).replace('Z', '+00:00'))
        if created.tzinfo is None or created > now:
            raise ValueError('invalid timestamp')
    except (TypeError, ValueError):
        return {'action': 'KEEP', 'reason': 'invalid_or_unknown_created_at'}
    if created >= now - timedelta(days=retention_days):
        return {'action': 'KEEP', 'reason': 'within_retention_window'}
    if not receipt or receipt.get('delivery_acknowledged') is not True:
        return {'action': 'KEEP', 'reason': 'delivery_unresolved_preserve_recovery_artifact'}
    if not asset.get('id') or receipt.get('asset_id') != asset.get('id'):
        return {'action': 'KEEP', 'reason': 'receipt_asset_identity_mismatch'}
    status = str(receipt.get('status', '')).upper()
    if status in ACTIVE:
        return {'action': 'KEEP', 'reason': 'active_editorial_work'}
    if status == 'PUBLISHED':
        verified = (receipt.get('instagram_verified') is True
                    and bool(receipt.get('instagram_media_id'))
                    and bool(receipt.get('final_media_url')))
        if not verified:
            return {'action': 'KEEP', 'reason': 'published_claim_unverified'}
    elif status not in TERMINAL:
        return {'action': 'KEEP', 'reason': 'unknown_status'}
    if receipt.get('backup_verified') is not True:
        return {'action': 'KEEP', 'reason': 'no_verified_recoverable_backup'}
    return {'action': 'REVIEW_ONLY', 'reason': 'terminal_or_verified_published_with_backup'}
