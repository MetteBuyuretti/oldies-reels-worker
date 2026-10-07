# X News — reviewable implementation, live deployment pending

## Completed

New delivery adapter: `wordpress/oldies-x-news-bridge/`, version 0.1.0. Existing WordPress editorial queue is reused; article bodies, main status, other metadata and other social publishers are preserved. English Polylang association, evidence review, editorial approval, short independent X text, link preview policy and global duplicate guard are implemented. Fresh English news created outside the scanner can be imported into that same queue. Legacy pages, projects, old posts, drafts and Turkish-language records are excluded from that import.

120 passing offline checks: 74 PHP policy/store/publisher checks and 46 admin-action/browser/render checks. All PHP files passed syntax validation. Actual DB/cloud admin/account/card testing has not occurred. The API responses and WPDB in tests are fakes, not production connection proof.

All 19 pre-existing named GitHub branches were inspected for X/Twitter publisher markers in PHP/Python/YAML code, excluding work-output. None matched. The local Social & News baseline has no publisher; live plugin inventory contains no X-specific module. No prior live X publishing was verified.

22-outlet foreign source catalog, 14 locally validated RSS feeds. Existing catalog records are preserved; additional records are initially inactive until the installed scanner's actual parser is verified. No second scanner or scheduled social dispatch is added. Official artist/label domains can be used as reviewed evidence; no claim of continuous official social-account monitoring.

Free route: approved X text → reserved composer → human Post on X → actual post URL confirmation. This is assisted publishing; it is not unattended free API publishing. Opening the composer alone never marks POSTED.

Paid route is coded but OFF and unconnected. No billable test, no card or auto-recharge, no account/token changes. Official URL-post price checked 2026-10-07 is $0.20; 90–180 URL posts/30 days approximately $18–$36 before additional operations/tax. The optional first-card $20 incentive is one time, expires in three months and has not been activated.

## Pending live checks

X account ownership/handle/profile/bio/site URL, verification, Developer App and write authorization. Live Command Center 1.0.9 source/schema, custom adapter installation, all parser/source activations, real English news preparation, public Open Graph/X card rendering and disposable live post/delete test. X account existence and developer access remain **unknown**, not presumed absent.

## Exact access blocker

Current WordPress connector can enumerate plugins and install WP.org/marketplace slugs. It cannot upload this custom ZIP or read/edit existing PHP sources. Browser tool instructions require user approval before plugin fallback. No browser has been initialized in this task. Obtain permission for browser fallback to oldiesradyo.com admin and the intended X account/developer console; then perform remaining possible work autonomously. Owner login/captcha/2FA handoff may be needed only if observed.

## Practical limits

The duplicate paraphrase test is a deterministic artist-constrained token-overlap heuristic plus event-key and canonical URL history. It is not an embedding-based semantic model. An editor should use the same event key for the same artist/story from distinct sources. Server weighted length is conservative; official bundled browser twitter-text accurately counts complex emoji, while the server can reject a near-limit string that X permits. No automatic image upload; actual card presentation is controlled by X and the live page metadata.

Rollback is adapter deactivation only. Preserve namespaced X history for duplicate prevention; no shared queue cleanup or migration is part of this change.
