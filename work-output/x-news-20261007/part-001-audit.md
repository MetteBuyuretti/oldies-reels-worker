# X News — 7 October 2026, checkpoint 1

## Evidence
- Live WordPress connector inventory: Command Center 1.0.9, Social & News Automation 1.7.5, Facebook Companion 1.0.7-R7, Reels Bridge 2.3.7-YT8-SAFE2 active.
- main repository ae09f0d4555a307704202f1cb529546a97c6aa95: no X publishing module or workflow. Existing branches have no X-labelled branch. Windows Social & News baseline contains no X publisher; one Twitter reference is a URL-normalization test.
- Existing NewsRepository/Schema uses oldies_news_articles and oldies_news_sources; article metadata LONGTEXT and en_post_id already exist. X delivery can be a namespace in article metadata, without a new queue/table or edits to other publishers.
- Windows Command Center replica is 1.0.3; live is 1.0.9. Never overwrite it with the older replica. A separate module can register a submenu under the observed oldies-cc-dashboard parent; live source/schema must be verified before activation.
- Oldies X account and developer access unverified. No credentials discovered or altered.

## Official documentation read on 2026-10-07
- https://docs.x.com/x-api/getting-started/pricing : pay per use, no fixed subscription. Post Create $0.015; with URL $0.200. 90–180 link posts/30 days = $18–$36, excluding reads/media/taxes and other endpoints.
- https://docs.x.com/x-api/getting-started/free-credits : optional one-time $20 credit for first eligible card, expires after 3 months; saving a card is not an ongoing free tier. No card, purchase, auto-recharge or billable request authorized/performed.
- https://docs.x.com/x-api/fundamentals/rate-limits : POST /2/tweets 100/15 minutes per user, 10,000/24 hours per app. These are endpoint ceilings, not a free monthly quota.
- https://docs.x.com/fundamentals/counting-characters : standard 280 weighted characters; each URL 23, emoji special rules; use official twitter-text.
- https://docs.x.com/fundamentals/authentication/overview : OAuth1 user context or OAuth2 authorization code PKCE. OAuth2 user write requires tweet.read, tweet.write, users.read; offline.access needed for refresh.

## Implementation decision
Zero-cost draft/verification/web-intent publication first. Existing news scanner remains discovery engine. X API code defaults disabled, requires explicit positive per-post and monthly budget plus credentials. Sensitive news always needs editorial evidence review and manual approval. No polling or cross-platform dispatch changes.

## Live access limitation
WordPress connector exposes plugin inventory/marketplace management, not custom plugin source editing/upload or X account sessions. Browser fallback requires user approval under browser tool instructions; build and test reviewable changes before that final approval request.
