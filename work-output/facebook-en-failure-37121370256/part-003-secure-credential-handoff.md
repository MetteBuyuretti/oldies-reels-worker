# English Facebook Reel — secure credential handoff checkpoint

Task: facebook-en-failure-37121370256
Recorded: 2026-10-04 (UTC)

## Completed
- Resumed after the live-connection audit; no repeated deployment or publishing.
- Secure Facebook account authentication completed in the cloud browser.
- Confirmed signed-in access to existing Oldies Radyo Social App, app ID 886955667589846.
- Graph API Explorer retained its six existing selected permissions: business_management, pages_manage_posts, pages_read_engagement, pages_show_list, instagram_basic, instagram_content_publish. No permissions were added or removed.
- Selected the existing Oldies Radyo Page Access Token entry without inspecting or copying its secret value.
- Read-only Graph v26.0 GET me?fields=id,name returned id 1318926181298428 and name Oldies Radyo. A usable credential for the intended Page is available in the authenticated Meta UI.
- Opened the current live Social Automation settings and located Facebook Page ID and Page Access Token. Existing configured Page ID matches the verified Page.

## Pending / exact blocker
The invalid Facebook credential stored in WordPress has not yet been replaced. Browser credential-change policy requires the account owner to enter and submit the new credential. Prepare owner handoff: Copy Token in Graph API Explorer (Oldies Radyo Page selected), paste into only the WordPress Facebook Page Access Token field, then Ayarları Kaydet.
Do not copy the credential into chat, repository, logs, or checkpoints.

## Verification limits
- The Graph Explorer credential is valid for the read-only identity query at this checkpoint; expiration/lifetime and publishing permission exercise remain unverified.
- WordPress runtime still holds the old invalid token until the owner saves the replacement.
- Companion health confirms presence only, and publish-url dry-run bypasses Facebook authentication. Neither proves this repair.
- No live retry, video creation, Facebook publication, or success claim yet.

## Changes / rollback
Only the selected Explorer Page/query and documentation/checkpoint changed. No stored WordPress credential, plugin source, runtime, schedules, Instagram settings, Site Integrity, menus, categories, content or player were mutated.
No runtime rollback is required. The previous invalid credential is not exported as a backup. If replacement fails, retain the deployment/configuration and repair the exact Page credential; do not enable legacy Global Settings plugins.

## Next step
Owner completes credential entry and submission. Then inspect save confirmation without reading secret values; perform a runtime token validity check if supported; check deduplication/publishing state; retry the one failed English Facebook job only once and confirm successful Facebook result. Do not claim repair complete before live verification.

## Safe preparation links
- https://developers.facebook.com/tools/explorer/
- https://oldiesradyo.com/wp-admin/admin.php?page=oldies-social-automation-settings
