# X News — checkpoint 2

Adapter source is in wordpress/oldies-x-news-bridge/. The live site's older local Command Center replica was NOT installed/replaced.

Tests at this checkpoint: 74 policy/storage/publisher checks plus 34 browser/admin-action checks (108 passing, no real X API or public post). PHP 8.3 syntax checks passed. Further WordPress import and UI render tests follow.

Verified: sensitive-source review, ownership-aware source grouping, English associated publication requirement, duplicate history including >200 rows, optimistic metadata merge, global lock fail-closed, Unicode/emoji/long-URL browser counter, manual publication reservation and confirmation, zero-budget hard block, wrong-account block, safe FAILED review/backoff, uncertain-result no-retry, changed story invalidating approval, stale editor revision block, duplicate X post ID block. Existing main news status and body preserved.

22 source definitions present. A concurrent HTTP/RSS probe returned 14 valid nonempty RSS feeds. HTTP-list sources are not called validated merely for HTTP 200; failing or untested parsers are not silently enabled. Catalog registration appends missing sources INACTIVE to existing source table and preserves existing entries. Live scanner parser/source activation still awaits deployment/access.

Scoped Windows configuration name-only audit found no X/Twitter environment keys under oldies-global-work, oldies-cc-maint, work2-live-sources. This does not prove no keys exist anywhere or in repository secrets; secret values were not requested or printed.

Live deployment, live Open Graph/X card verification, account/developer identity and disposable post/delete test are incomplete. WordPress connector plugin.install schema supports WP.org/marketplace slugs, not custom ZIP upload or plugin source edits. Browser fallback requires owner approval under browser tool instructions. No browser initialized, no paid request, no token changed.
