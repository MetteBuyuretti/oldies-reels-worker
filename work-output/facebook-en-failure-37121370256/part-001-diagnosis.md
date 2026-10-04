# English Facebook Reel — failure diagnosis
Run: https://github.com/MetteBuyuretti/oldies-reels-worker/actions/runs/37121370256
Job: https://github.com/MetteBuyuretti/oldies-reels-worker/actions/runs/37121370256/job/111197981166
Run commit: d37e2cc9226e2a79cc72c6370a4eb4d4499abdd9
Observed failure: 2026-10-03 11:59:55 UTC (14:59:55 Europe/Istanbul).

## Verified
- Scheduled workflow: .github/workflows/facebook-global-en.yml.
- Checkout, Python setup and renderer installation succeeded.
- A 15-second MP4 was rendered, and a GitHub reels-delivery asset was uploaded.
- The failure occurred in worker.py publish_facebook_global(), calling the WordPress companion endpoint /wp-json/oldies-global/v1/publish-url.
- The companion returned HTTP 400, code fb_token_check, with message:
  "TOKEN CHECK: Error validating access token: The session is invalid because the user logged out."
- This is a Facebook access-token/session validation failure. The reported reason is session invalidation following logout; the log does not establish a scheduled token-expiry date or the exact logout event.
- The failure occurs at the companion's token-check boundary. This run did not confirm successful Facebook publication.
- Audit artifact 11273426228 was retained successfully and is currently unexpired; it expires on 2026-10-10 at 11:59:55 UTC.
- Daily schedule is 11:00 UTC (14:00 Europe/Istanbul); this particular queued run started at 11:58:50 UTC.

## Necessary repair
Reconnect the Facebook account and obtain a valid Page access token for the English/Global destination, then replace that token in the WordPress Global Facebook companion connection. This workflow provides OLDIES_WP_BEARER to authenticate to WordPress; it does not supply the Facebook token as a GitHub environment secret. The exact live settings field must be inspected before any credential change.

Perform a read-only token/Page check or companion dry-run after reconnection. Preserve the existing delivery asset and validate deduplication/publication status before any single approved live retry. Repeating this job without repairing the token will not address the recorded cause.

## Checkpoint / mutations / rollback
Diagnosis completed. Runtime code, credentials, schedules and publishing state were not changed. No live rerun or Facebook publication was attempted. This report and the work-state task are the only repository changes; they are reversible Git commits. No secrets, notification email tokens or access-token values are stored here.

## Remaining
Facebook credential reconnection and authenticated verification remain outstanding. The diagnosis itself is complete.
