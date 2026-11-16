# Daily English review — 17 November 2026

Daily review scheduling is installed on main at 11:23 UTC / 14:23 Istanbul. Existing Facebook and Turkish publication quarantines remain unchanged.

Source files: english_review.py, english-reviewed-events.json, test_english_review.py and .github/workflows/english-review.yml. Durable day/event reservations live on english-review-state; only completed private Actions artifact storage permits artifact_saved. No public media publication is performed.

Seven orchestration regressions pass. Reviewed music is Carefree by Kevin MacLeod, CC BY 4.0, source https://www.incompetech.com/music/royalty-free/index.html?isrc=USUAN1400037 and SHA256 8433b770a630d9b1594fd484442c677907ece899a4d149954cd2e74fd733e311. Mandatory attribution is written to caption.txt and music-license.json before delivery.

The November 17 candidate uses Official Charts' own November 17-23, 1963 album chart: Please Please Me #1, How Do You Like It #2. Source https://www.officialcharts.com/charts/albums-chart/19631117/7502/ . Three approved original 1963 Beatles photos are reused with exact hashes. Existing accepted calm signoff is not regenerated.

Actual runs:
- 43974153471: source/photograph coverage gate rejected all discovered candidates; no provider call and no final.
- 43974531991: actual free-tier API succeeded; take 14.570958 seconds / 156.5 estimated WPM was rejected by the <=138 WPM rule.
- 43974968577: second actual free-tier take 15.210958 seconds, still above pace gate; no final. Both failed reservations retained in failed_attempts before targeted owner-authorized recovery.
- 43975302748: structured prompt caused invalid provider audio bytes; size gate rejected it. No final MP4 or completion record was written. The failed reservation is retained in history. A simplified supported prompt plus the complete sourced November 17 date is the final bounded repair attempt (main d9c8a73).

Open scope: only one artist currently has a reviewed three-photo bank. Daily coverage across other artists and dates is not established. Scheduling, provider authentication and seven fixture tests do not establish uninterrupted daily video output or independent human media acceptance.

## Exact root cause and bounded recovery

Run43976092224 produced the right 42-word story with relaxed delivery, but its 36.050958-second WAV contained 7.417s and 7.301833s of digital silence plus a 1.190708s tail. SHA25614fb3f51c766a339fcea278765ed5b0a1c390ba32c7e3cc663b26b02a6771181.

The repair removes only digital silence detected below-50dB for>=1s, with20ms boundary guards. Internal gaps retain0.50s, tail0.10s. Every speech sample is preserved; no time stretching, speed-up, padding, or acceptance-limit change. Actual cleaned story21.341s/~118WPM; planned final29.766667s.

Nine current orchestration and waveform-preservation regressions PASS, including push-event execution and transcript/hash-bound recovery. The exact failed-run source is being recovered from its authenticated Actions artifact, tied to run/head/script/audio hashes, with zero new provider calls. Final artifact and completion ledger still require actual run acceptance.

## Accepted technical delivery

Actual GitHub run43977060028 completed SUCCESS: https://github.com/MetteBuyuretti/oldies-reels-worker/actions/runs/43977060028 . Nine regressions passed; exact failed-run source was recovered with zero new provider calls. The natural voice, separate1.1s station break, three full-frame period photos and licensed music were rendered. Actions artifact14280279853 was saved before the durable ledger changed to artifact_saved. Remote MP4SHA256d4221fb56035bc4bcd1656fec4b3b028e85880d7cc1902efba7885d18be8f0a4.

A second actual run43977248722 completed SUCCESS and logged Duplicate day blocked; no provider request. The completed ledger and original hash remained unchanged.

Final visual QC caught the inherited four-line story card truncating the narration. The existing layout now accepts an optional concise on_screen_story; all old defaults remain. The corrected final user review was rerendered locally from the exact same verified raw speech, accepted signoff and photos, with zero provider calls. Its three actual frames were checked; the concise chart fact now appears complete.

Delivered revision:29.833333s,1080x1920/H264/30fps,AAC48kHzstereo;2,135,235bytes; SHA2569303fe1f785e9bf771fdd9e4138048c7fbbf19b123c21847f7a7076949e745ec. Story118.1WPM; approved station gap1.1s, clean gap peak-91dBFS; no speed-up. User copy: https://chatgpt.com/library?file_id=libfile_de84f323a7d08191b2129d1971039aea&account_id=personal .

The scheduler connection is COMPLETE. Uninterrupted different-artist daily delivery is not complete: the reviewed bank still has only three Beatles photos and one curated date. Human media listening/acceptance remains separate. No social publication was performed. Existing Facebook and Turkish quarantine guards remain closed. Do not regenerate the accepted source, rerun these completed tests, or repeat the duplicate proof without a relevant change. Next missing unit is source-backed daily event and photo-bank expansion.
