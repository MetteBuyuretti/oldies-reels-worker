# Live Facebook connection audit

Owner requested repair after diagnosis. WordPress admin access is healthy. Active Companion is v1.0.7-R7 (existing directory oldies-facebook-global-companion-v1.0.3-R3-ROOT-DEPLOY); Global MCP Bridge v1.0.5 is active. Runtime source was read in the native plugin editor; no source changes were made.

The active Companion gets FACEBOOK_PAGE_ID/FACEBOOK_PAGE_ACCESS_TOKEN from the environment, if present, otherwise oldies_social_fb_page_id/oldies_social_fb_page_access_token. All three legacy Global Settings plugins are inactive, so activating one blindly could introduce an old environment override; none was activated. The current Social Automation settings have a configured Facebook Page ID and masked token, with no Facebook reconnect/refresh button. Main Instagram has a separate healthy Instagram Login connection and must be left unchanged.

The Companion has no token refresh endpoint. Its health response checks token presence, not current Meta validity; its delivery dry-run validates MP4, not Facebook authentication. A dry-run success alone is insufficient proof of restored publication.

Meta Developers opened its official sign-in screen in the cloud browser and requires Facebook or managed Meta account authentication. No credentials were read, copied or entered. The next step is secure browserAuth sign-in, then inspect the existing app and renew the same Page grant without expanding permissions. Any manual new token entry must be performed by the owner under the browser credential-change handoff policy.

Mutations/rollback: no runtime, credentials, menus, schedules or publishing state changed; no live retry. Only checkpoint documentation and task-state updates. Blocker: Meta authentication is required to repair the invalid session.
