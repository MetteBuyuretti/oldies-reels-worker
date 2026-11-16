# Daily English review — 17 November 2026

Daily review scheduling is installed on main at 11:23 UTC / 14:23 Istanbul. Existing Facebook and Turkish publication quarantines remain unchanged.

Source files: english_review.py, english-reviewed-events.json, test_english_review.py and .github/workflows/english-review.yml. Durable day/event reservations live on english-review-state; only completed private Actions artifact storage permits artifact_saved. No public media publication is performed.

Seven orchestration regressions pass. Reviewed music is Carefree by Kevin MacLeod, CC BY 4.0, source https://www.incompetech.com/music/royalty-free/index.html?isrc=USUAN1400037 and SHA256 8433b770a630d9b1594fd484442c677907ece899a4d149954cd2e74fd733e311. Mandatory attribution is written to caption.txt and music-license.json before delivery.

The November 17 candidate uses Official Charts' own November 17-23, 1963 album chart: Please Please Me #1, How Do You Like It #2. Source https://www.officialcharts.com/charts/albums-chart/19631117/7502/ . Three approved original 1963 Beatles photos are reused with exact hashes. Existing accepted calm signoff is not regenerated.

Actual runs:
- 43974153471: source/photograph coverage gate rejected all discovered candidates; no provider call and no final.
- 43974531991: actual free-tier API succeeded; take 14.570958 seconds / 156.5 estimated WPM was rejected by the <=138 WPM rule.
- 43974968577: second actual free-tier take 15.210958 seconds, still above pace gate; no final. Both failed reservations retained in failed_attempts before targeted owner-authorized recovery.
- 43975302748: structured natural-pause prompt run in progress; result must be read before any further provider request. No additional provider call will be made while it is pending.

Open scope: only one artist currently has a reviewed three-photo bank. Daily coverage across other artists and dates is not established. Scheduling, provider authentication and seven fixture tests do not establish uninterrupted daily video output or independent human media acceptance.
