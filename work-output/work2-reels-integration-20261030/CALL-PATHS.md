# Source-bound entry map — 30 October 2026

| Ref | Entry → consumer | Signoff / timing |
|---|---|---|
| main 1ca60d823b38b238166a2b730f1882a220829410 | .github/workflows/facebook-global-en.yml → worker.py main → synthesize_google_voice (engine auto) | Job quarantined by if:false. Does not call PR22 facebook_global_audio. |
| PR22 9ad08776e882af386f2897ac43e85eaeb28f029e | workflow OLDIES_TTS_ENGINE=facebook_dj → worker.py:965 → facebook_global_audio.synthesize_dj → copied ending → FFmpeg concat → facebook_global_visuals.render → validate_media/validate_recording; publication also require_approved_signoff | Actual candidate selected for this change. Base preview could regenerate ending. 18/17.4-second limits. |
| PR33 073e7665d9d381e7c8d595fcd60b905a9071490a | reels_preview.prepare_preview → packet local_voiceover + exact script/hash evidence → injected local renderer | This preview does not call synthesize_google_voice. Its workflow remains quarantined; do not confuse worker helper with preview entry. |
| Windows active entry | Not supplied | No installed source/ref/launcher or energetic file mapping receipt. No runtime claim. |

Only the PR22 consumer is changed on the Work2 branch. The PR22 workflow is inherited, not executed or modified. Its historical publishing workflow must not be dispatched as a test: it authenticates to Google and can call paid TTS.

Evidence: source files fetched through GitHub at the fixed SHAs above; accepted asset identities at e1c87bd0616ca763a2362282ff4d878aab3f02f4/work-output/local-exec-20261029/review/reels-signoff-identities.json and #32/6509320201.
