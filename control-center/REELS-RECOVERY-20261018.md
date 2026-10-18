# PR33 — recovered checkpoint, 18 October 2026

Status: TEST EDİLDİ / preview only. Not an operational or editorial acceptance.

The original interrupted Windows snapshot is preserved separately; its useful
source, script and local preview stages were reconciled with PR33 at d0d56218.
No change was made to main, PR22, publishing locks, WordPress, Meta or other projects.

## Repaired paths

- Exact-day This Day In Music discovery; HTML comments removed, split date tags
  supported, no Soundod/Wikipedia fallback. Discovery remains explicitly unverified.
- TR and EN use the same independently sourced fact-to-script checks, 1950–1990
  bounds, language isolation and exact station closings. A song/album is optional.
- Three distinct photo bytes, artist/era/context/creator/license/territory evidence.
  Event year first; ±1 requires documented same-year search; ±2 requires a separate
  hash-bound exception review. Statues, bird Eagles and religious Madonna fail.
- Narration file binds to exact script/language/hash. Real audio decoding rejects
  absent/silent/mostly silent/padded audio; full MP4 video decode, FFprobe, 9:16,
  25.00–30.00s, aligned audio/video durations and SHA256 are required.
- Existing timeline renderer has working fades, bounded 0.12s final tail, no
  time stretching, no ten-second fallback, and usable Windows/Linux fonts.
- Both worker entry points are local preview only. They never read delivery
  credentials, call TTS, upload a draft, or publish. Direct legacy delivery adapters
  also require the independent gate before network calls.
- Completed render receipts are reused only for the same packet and code digest;
  ambiguous prior output stops for reconciliation. No existing artifacts are deleted.

## Run and evidence

Install existing requirements and put FFmpeg + FFprobe on PATH. Offline checks:

    python -B -m unittest -v test_editorial_quality_gate test_reels_duration_contract test_reels_media_integration test_reels_pipeline test_announcer

34 tests passed locally, including real synthetic 27s audio/video, the actual
timeline renderer, silent/missing audio, horizontal video, ten-second clips and
ten-second audio extended to 27s with silence. These synthetic signals are NOT
real Four Tops/Michael Jackson source files or natural DJ pilot approval.

For a local preview set OLDIES_REELS_LANGUAGE=tr or en, OLDIES_ZERO_COST_DATE,
and OLDIES_EDITORIAL_PACKET to a JSON file inside this checkout, then run worker.py.
No packet/evidence means BLOCKED_PREVIEW and process exit 2, with a saved report.
Output is output/<language>-preview/<packet-digest>-<code-digest>/.

## Packet contract / pending acceptance

The packet contains event_date, research_date, artist, reels_language,
primary_evidence (exact TDIM URL/excerpt/hash/retrieval timestamp/date/artist),
source_documents (independent authority excerpts and hashes), verified_facts
(at least two exact source excerpts plus script_span/date/artist/kind),
story_tr or story_en (opening/narrative/closing), identical dj_script_tr/en,
target_territories, and three image_credits with local_path, asset_sha256,
identity/media_type, rights/license URLs, creator, capture_year, decoded dimensions,
era/context evidence and rights_territories. Local voiceover and voice_evidence
must specify matching audio/script SHA256, transcript, language and unmodified_speed.

An unverified discovery cannot create these factual or licensing approvals.
Research and an independent original-source review are still required. The renderer
does not infer historical truth, worldwide rights or natural DJ quality from metadata.
Caption timings are estimated from words/pauses; independent full-video review of
sync/readability and full listening are mandatory before delivery acceptance.

Real two-event TR/EN pilots, authentic old-media negative checks, independent
Work-1 review and the owner's final audio/visual approval remain pending. The
free preview voice service returned NoAudioReceived on the initial TR attempt;
no paid fallback, merge, publishing unlock or external delivery is authorized.

Rollback: revert only this PR33 checkpoint commit. Original main and PR22 remain
unchanged, and the original interrupted local snapshot remains available.
