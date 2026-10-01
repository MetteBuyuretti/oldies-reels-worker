# Conservative release retention — Issue 16

The previous workflow deleted every delivery MP4 older than ten days regardless of WordPress receipt or editorial status. This PR replaces that with a read-only inventory. The daily schedule stays at 03:35 UTC. There is no deletion request or cleanup activation switch.

The repository is public. Both workflows use permissions:{} and anonymous Git/API reads; no contents permission, credential persistence or GITHUB_TOKEN is passed to the inventory. Anonymous Git fetch checks out the exact workflow commit. This would need a separately reviewed read credential if repository visibility changes. API throttling/read errors fail the inventory without any remote mutation.

Retention decisions preserve DRAFT_REVIEW, READY_FOR_EDITS and BLOCKED forever until explicit editorial resolution. PUBLISHED needs verified Instagram media ID and final URL, a matching asset receipt and a verified recoverable backup before REVIEW_ONLY. REJECTED, ARCHIVED and LEGACY_TEST also require backup before review. Age and successful delivery alone are not permission to delete. Unknown or interrupted delivery always preserves the artifact. Repeated inventory is deterministic.

The inventory currently has no authenticated WordPress receipt source, so it deliberately keeps every release asset. This is a safety stop, not a complete durable delivery ledger. Storage will grow until receipts and backups exist. A later, separately approved retention implementation must not equate WordPress delivery with completed Instagram editing.

## Independent worker / editorial states

GENERATED -> ARTIFACT_UPLOADED -> DELIVERY_ATTEMPTED -> DELIVERED or UNKNOWN_REMOTE_RESULT / DELIVERY_FAILED -> RETAINED_FOR_RETRY. Retry exhausted keeps the recovery artifact and requests review. Daily quota is DEFERRED, never delivered. A 409 duplicate is an acknowledged replay only under the existing server fingerprint contract.

The corresponding editorial record remains DRAFT_REVIEW -> READY_FOR_EDITS -> actual Instagram publish -> verified instagram_media_id and final_media_url -> YouTube. Neither raw GitHub MP4 nor READY_FOR_EDITS is a final source.

WordPress seven-day record removal and fifty-record truncation require a separate change against the active Reels Bridge source. Do not apply a dated snapshot to production without hash matching. Preserve persistent fingerprint tombstones even if a record is archived. Full receipt persistence, retry reuse of existing artifact and payload-conflict detection remain follow-up work under Issues 12/14/16.

## Validation

python -m unittest -v test_retention_policy test_cleanup_inventory

17 offline test methods cover interrupted upload/acknowledgement, timeout after possible WP acceptance, stale undelivered MP4, old delivered active drafts, all requested statuses, verified publication, missing backup, identity mismatch, repeated cleanup, invalid/future timestamps, GET-only anonymous inventory, pagination, absent release and sanitized/fail-closed read errors. PR CI runs tests only. No live workflows were dispatched, no credentials read, and no artifacts deleted by these changes.
