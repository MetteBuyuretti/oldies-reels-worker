# ENTRY-MAP — WORK2 TR integration

Code identity: `2e829a56cee7452959f88d4182e14f62e88cc75a`; T1 preimage `3b71f9debc4becc4b2a868796b88897ad1da484d`. PR38 targets PR33's `fix/p0-evidence-based-reels-qc-20261016` branch (initial PR33 SHA `073e7665d9d381e7c8d595fcd60b905a9071490a`). No PR33/main ref was modified.

| Called point | Behaviour/evidence |
|---|---|
| `worker.main` (1197) | The existing preview branch passes the top-level `render_preview` callable to `prepare_preview`; normal publish entry remains separate. |
| `reels_preview.prepare_preview` (22) | Script/source/photo gates, plan validation, actual photo bytes/dimensions, natural exact-script voice hash, decoded duration; before renderer invocation. Missing TR plan cannot choose legacy. |
| `editorial_quality_gate.check_storyboard` (170) | Version/profile, canonical source/photo bundle SHA, exact script SHA, unique original assets/compositions, complete half-open word ranges, reviewed exact-audio word alignment. Word index is coverage, not measured time. |
| `worker.render_preview` (1176) | Calls the real new builder, writes separate timelines, makes one photo canvas per scene and separate transparent caption canvases. |
| `video_factory.build_storyboard_timelines` (150) | Uses supplied reviewed audio boundaries and independently measured duration. At the tested 27s fixture: eight captions and three contiguous photo scenes. Caption grouping may vary with permitted duration; photo changes follow explicit scene ranges only. |
| `worker.make_storyboard_scenes` (1113) | Verifies original photo SHA again; full contain layout, no face crop, archive year and creator credit. |
| `worker.make_caption_overlays` (1149) | Exact full script, readable two-line fit; no text truncation. |
| `video_factory.render_timeline` (249) | Separate photo/caption intervals: 3 continuous photo inputs, 2 scene transitions, 8 overlay inputs in tested fixture. Caption changes neither reopen nor transition photos. Existing natural audio/short duration contract retained. |
| `editorial_quality_gate.check_approved_reel` (248) | Existing independent original-source/photo/natural-DJ approval remains mandatory; plan metadata does not grant delivery. |

`source_evidence.py` and `media_evidence.py` are byte-identical to T1. Existing TTS/model thresholds, speed, silence constraints and short 25–30s profile were not relaxed. English legacy helper is retained, but the TR preview branch does not call its caption modulo selector. No 59s project included.

Contract prerequisites: `visual_storyboard.version=storyboard-v1`, `profile=legacy_short_25_30`, exact script/source/photo hashes, scenes with unique `scene_id`, original `photo_sha256`, zero-based `[start_word,end_word)` covering the entire script. `voice_alignment.version=word-alignment-v1`, `timing_basis=reviewed_audio_word_boundaries`, real reviewer/evidence reference, exact script/audio SHA and every exact token's finite ordered start/end seconds. Real alignment is **missing**; the fixture explicitly says TEST_FIXTURE_NOT_HUMAN and cannot be reused as production evidence.

The immutable T1 STORYBOARD is editorial preproduction, not this runtime schema. It has not been silently converted into measured timings or accepted runtime image credits.
