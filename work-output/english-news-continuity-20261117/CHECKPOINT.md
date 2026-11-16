# Upbeat English news and continuity — 17 November 2026

Owner decision: news should be lively; background music should be clearly audible. Do not restore the slow bedtime/late-night style for news.

Implemented news-production-profile.json as the permanent source of settings: natural Charon target145/max160WPM; bright engaged delivery; Kevin MacLeod's News Theme,124BPM,CC BY4.0, source https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1100544 . Exact MP3 SHA256671e9432ce2361a0074a5c97a9d2e19e495f8ff29e6cbad2afe35e2a7d6057e4. Bed normalized to-24LUFS before gentle2:1speech ducking. Caption attribution is automatic. Other calm-template speech limits remain128/138.

Actual new take:17.731s,46estimated spoken words,155.7WPM, tempo1.0. One new provider call only. First real preview43979581753 passed voice/clean-film gates; failed in mix because afade duration .7 was not accepted by the runtime. Fixed0.7 and reused the exact provider waveform, transcript, run and commit; no second provider generation.

Final actual workflow43980617825 SUCCESS:
https://github.com/MetteBuyuretti/oldies-reels-worker/actions/runs/43980617825
13 narrow regressions pass. Full news mix, licensed music and complete short fact card rendered. Final26.166667s,1080x1920/30fps; integrated-16.4LUFS,true peak-2.3dBFS. SHA256c4bd5c60c5e77ab0dc012ff51d2f08baf73e9a169e174b3e9e7485ca8c9ab71c.
Delivered: https://chatgpt.com/library?file_id=libfile_33d87ff9eda08191b898bfb212a602f6&account_id=personal

Continuity:
- Existing daily preparation schedule14:23Istanbul remains active; production ledger prevents repeated events/days.
- Seven unused source-reviewed text stories with three validated1963 period photos are now prepared as archive backups. These are prepared texts/photos, not seven prerendered films. Current preview health lists8 because it includes today's preview plus7backups; normal production ledger excludes today's already delivered event and has7backups.
- Day-relevant unused items have priority. Otherwise consume an unused reviewed archive story, show its real historical date and FROM THE MUSIC ARCHIVE; never pretend an archive event happened today.
- stock-health.json checks natural-duration eligibility and all image hashes before provider use. Low-stock warning starts at3remaining.
- Existing automation6adeb7788b448191bc35ab09148fc565 is updated, not duplicated: enabled, next configured check17November05:15Istanbul. It now checks actual worker/stock and, at<=3remaining, attempts to restore7verified items using foreign primary sources and genuine licensed period imagery. It prioritizes80s/90s and different artists, spends at most10minutes, avoids PC/Commander and repeated TTS/render/tests, and reports only meaningful failures/deliveries in two short sentences.
- The initial backup set is still Beatles-only; diverse-artist replenishment has not yet been executed by the future maintenance run. Do not claim a future maintenance result or unlimited stock.
- No social publication performed. New preview is an owner-requested profile revision; the completed normal November17 production ledger was not reset.

For future music-level changes, reuse the exact existing clean film and remix only. For tone changes, generate at most one new take, then keep its original WAV for all renderer/mix fixes. No broad re-audit or re-running old signoff tests.

Verified backup primary sources:
https://www.thebeatles.com/please-please-me
https://www.thebeatles.com/me-you
https://www.thebeatles.com/she-loves-you
https://www.thebeatles.com/i-want-hold-your-hand
