# WORK2 R1 checkpoint — WORK2-REELS-INTEGRATION-20261030-01

## Problem → candidate behavior
PR22 only locked the calm path and could synthesize a new ending in preview. The real facebook_dj consumer now selects calm/energetic, verifies accepted SHA256/byte identity before story TTS, copies those exact bytes into the actual FFmpeg concat input and binds profile/hash/evidence/source/duration into dj_recording. Missing/mutated assets, unknown profiles and mismatched recording bindings stop. Accepted endings never fall back to TTS.

Asset identity evidence is #32/6509320201; no invented approver/date. Existing publication metadata remains false/empty and independently blocks production. final_media_approved is always false in this candidate. This is neither full story nor MP4 acceptance.

## Source and changes
Base PR22: 9ad08776e882af386f2897ac43e85eaeb28f029e.
Branch: work2/reels-integration-20261030.
facebook_global_audio.py and facebook-global-template.json only; focused offline regression source in test_facebook_signoff_integration.py.
See CALL-PATHS.md for main/PR22/PR33 distinctions.
Energetic mapping requires existing original file via OLDIES_FACEBOOK_ENERGETIC_SIGNOFF_PATH; no audio uploaded.

## Verification truth
Attempted local commands: pwd; python --version. Both failed before starting: No usable execution environment is available (environment exec-server initialization failed).
Prepared command: python -m unittest -v test_facebook_signoff_integration
Status: NOT RUN. 11 test methods authored with synthetic fixture bytes, record/inspect/concat stubs. No provider/real media/Windows access. Test method count is not a PASS count. No Python parser, ffprobe, FFmpeg or behavioural execution available.
GitHub source inspection confirms call-site replacement and no advert record_part fallback; that is source review, not runtime validation.
Historical test_facebook_global_audio includes obsolete preview-regeneration/approval fixtures and will need reconciliation with R2 before a whole-suite PASS can be claimed.

## Scope / next
R1 source and test preparation checkpoint only; execution acceptance remains BLOCKED.
Proceed to R2 in same branch: natural 25–30-second timing agreement without speeding or padding a short story into acceptance.
Windows active entry/ref + original energetic path/hash receipt and actual final media/independent approval remain external work; do not dispatch inherited PR22 workflow to run tests.
No main/PR22/PR33/PR35 writes, workflow changes, deployment, publication, TTS calls, raw audio upload, Jingle/Windows staging writes.
