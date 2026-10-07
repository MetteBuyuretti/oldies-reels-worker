# Oldies X News Bridge 0.1.0

Adds **Ana Kumanda → X NEWS** to the existing `oldies-cc-dashboard` menu. This is an X delivery adapter, not a replacement news scanner or a parallel editorial queue.

## Data and approval

- Uses existing `oldies_news_articles.metadata.x_news`. Preserves all other metadata and the existing article status, TR/EN bodies, source links and publishers. No new table, schema migration, cron or workflow dispatch.
- Existing scanner candidates appear even before a WordPress story exists. A published English Polylang post of type `post` must be associated through `en_post_id` before sharing.
- Editing resets approval. Editor reviews sources and English text, then explicitly approves. Approval expires after one day and is bound to current text, evidence, article content and WordPress modification time.
- Sensitive categories/keywords need reviewed evidence from two independent trusted publishers, or a trusted source plus an official artist/label/organizer statement. Different URLs from one publisher/group are insufficient. Unknown source hosts fail closed.
- `NEWS CANDIDATE → NEW/HOLD → VERIFIED → READY → AWAITING_CONFIRMATION/POSTED`. `REJECTED`, `FAILED`, `SENDING`, `OUTCOME_UNKNOWN` are explicit terminal/recovery states.
- No media is reuploaded. The featured image appears only in the private review screen; X card depends on public Open Graph metadata and X rendering.

## Free publication

`Publish` reserves the approved item and opens X's standard web intent with its English text. The account owner reviews and clicks Post on X, then records the actual X post URL with account/text/link attestation. Opening a composer is **not** recorded as a successful post. If the composer was abandoned, an explicit non-publication confirmation releases the reservation and requires new approval. This is assisted publication, not unattended zero-cost API automation.

## Duplicate and recovery safety

URL canonicalization strips tracking parameters; persistent story keys identify the same event across sources. Artist-constrained token overlap provides an additional paraphrase heuristic, not a guarantee of full semantic understanding. MySQL global advisory lock serializes X operations. Metadata updates use compare-and-swap to preserve concurrent scanner edits. Posted and uncertain/reserved items are checked across all recorded history, not only the newest page.

An API timeout, malformed success response, 5xx or crash is held as uncertain and cannot automatically retry. Definitive 4xx rejection can return through review after backoff. A separate minimal outcome journal preserves the X ID if a metadata write fails after API success. Never call a bulk cleanup on the shared queue; permanent duplicate history would be lost.

## Optional paid API: OFF by default

Secrets are read only from server environment or private `wp-config.php` constants. Never put real values in this repository, UI, endpoint, report or log.

```text
OLDIES_X_API_ENABLED=false
OLDIES_X_EXPECTED_USERNAME=<verified account handle>
OLDIES_X_MAX_REQUEST_USD=0
OLDIES_X_MONTHLY_BUDGET_USD=0
# OAuth 1.0a user context:
OLDIES_X_API_KEY=<secret>
OLDIES_X_API_SECRET=<secret>
OLDIES_X_ACCESS_TOKEN=<secret>
OLDIES_X_ACCESS_TOKEN_SECRET=<secret>
# OR OAuth 2 user access token (not an app-only bearer):
OLDIES_X_USER_ACCESS_TOKEN=<secret>
OLDIES_X_OAUTH2_SCOPES=tweet.read tweet.write users.read
```

OAuth1 app needs Read and Write, then a user token generated with those permissions. OAuth2 PKCE also uses `offline.access` if a refresh token lifecycle is separately implemented; this adapter does not implement authorization/refresh setup. An expired token blocks publication. Existing unrelated tokens are never altered.

Enabling paid requests requires explicit spending authorization, positive budgets and a read-only `/2/users/me` identity check matching the expected username. Identity is invalidated on a credential change and expires after one day. Reads reserve $0.01; URL posts reserve $0.20 under a shared lock. Reservations are retained on failure as a conservative spending cap; the Developer Console remains authoritative for actual charges/rate limits.

Official pricing checked 7 October 2026: URL posts $0.20 each, standard posts $0.015. At 3–6 URL posts/day, 30 days costs about $18–$36 before reads/media/tax/other operations. Pay per use has no recurring free posting tier stated in the pricing page. The one-time $20 first-card credit expires in three months and is not activated by this module. No purchase, card entry, auto-recharge or live billable test is performed by installing it.

Standard posts use 280 weighted characters, URLs 23. Browser counter bundles official `twitter-text@3.1.0`; server uses a conservative Unicode upper bound and can reject a near-limit multi-code-point emoji/decomposed-character string that X itself permits. This fails safely instead of exceeding the limit. Keep a little headroom for such text.

Official docs: [pricing](https://docs.x.com/x-api/getting-started/pricing), [incentives](https://docs.x.com/x-api/getting-started/free-credits), [rate limits](https://docs.x.com/x-api/fundamentals/rate-limits), [characters](https://docs.x.com/fundamentals/counting-characters), [authentication](https://docs.x.com/fundamentals/authentication/overview).

## Deployment and verification

1. Verify the current live Command Center 1.0.9 source and shared table columns. The Windows 1.0.3 replica must not replace it.
2. Upload only this adapter folder, activate it, and confirm its submenu and absence of PHP errors. The activation boot does not alter queue rows, source settings or credentials.
3. Check a real published English news row, sources, text and public Open Graph tags. Save/review/approve it and test the composer. Never mark POSTED without an actual matching post.
4. Use source registration to append missing entries to the existing scanner's source table. New entries are **inactive** pending the existing parser's live validation; existing sources and their activation states remain untouched. The catalog supports all 22 requested outlets; local HTTP/RSS results are in `work-output/x-news-20261007/source-probes.json`.
5. Test a genuine approved X post only after account login is available; delete a disposable live test afterwards. No public test is run in the offline suite.

Rollback: deactivate only **Oldies X News Bridge**. Leave Social & News Automation, Command Center and other publishers active. Article bodies and main states were never changed; namespaced X history remains for deduplication.

Requirements: WordPress with the existing Oldies editorial queue and Command Center, Polylang, PHP 8+, mbstring, MySQL advisory locks. No outbound API call at activation or page load.
