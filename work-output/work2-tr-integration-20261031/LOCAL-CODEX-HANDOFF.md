# Windows Codex — candidate-only handoff

Job `WORK2-TR-INTEGRATION-20261031-02`. No Windows command or installation was executed by Work2. This is a staged application procedure for Windows Codex, not evidence that the running worker uses these bytes.

## Fixed identities and stop conditions

- T1 preimage: `3b71f9debc4becc4b2a868796b88897ad1da484d`.
- Code + new test: `2e829a56cee7452959f88d4182e14f62e88cc75a` (code unchanged in subsequent output commits).
- Visual review: `3a1b9c329b05bb5ebb2305f0a06e404c92b35e42`.
- Candidate branch `work2/tr-preproduction-20261031`, draft PR38. Do not apply a moving branch without first recording its full commit. The final #32 result links the fixed C package containing this handoff/verifier/diff.
- `CODE-IDENTITIES.json` gives exact SHA256 and Git blob identities for all six modules and SHA256 of the new test. `candidate-code.diff` changes only four allowed root modules and creates the focused test. Neither source/media evidence module is patched.
- The earlier Windows R0 had two nonmatching modules (worker and editorial gate); four matches do not authorize replacing all six files. The observed live/installed source path, current bytes, dirty state and real launcher are not proved by this task. Treat the known R0 as STOP until freshly reconciled. Do not copy over a different local implementation.
- Stop on any missing source, mismatched SHA, dirty/conflicting staged files, occupied destination, unknown Python/launcher, or failed check. Preserve local modifications; no force/reset/clean.

## Safe isolated staging

Prerequisites: Git, Python 3.12 with the project's existing real requests/Pillow dependencies, all baseline tracked source/test/catalog files, and an empty staging destination. Existing FFmpeg/ffprobe is needed only for subsequent authorized real media work; tests below stub media inspection/rendering. No installation/paid provider is needed for these tests. If dependencies are absent, report them rather than install/change the running environment.

Use a separate clone or detached worktree; do not change the running worker checkout. Example PowerShell, substituting an already verified repository and an unused staging path:

```powershell
$Repo = 'C:\path\to\verified-repository'
$Stage = 'C:\path\to\unused-work2-stage'
git -C $Repo status --porcelain
# Stop/reconcile if this checkout contains relevant local edits.
git -C $Repo worktree add --detach $Stage 3b71f9debc4becc4b2a868796b88897ad1da484d
# Each following command is a separate step: stop immediately if its exit code is nonzero.
```

Obtain the final fixed C output directory from the commit linked in #32 into a separate `$Package` directory. Keep the files together, especially verifier and CODE-IDENTITIES. Verify the C commit/ref first; never resolve the package from an unchecked branch. Do not add any runtime data, credentials, claim, lock, scheduler or activation file.

```powershell
$Package = 'C:\path\to\verified-fixed-C-package'
python "$Package\verify_candidate.py" --root $Stage --mode preimage
# Must print MATCH, exit 0 for ALL six modules.
git -C $Stage apply --check "$Package\candidate-code.diff"
# Back up the four exact preimage files outside all runtime/output locations before applying.
# Record each source path, size and Get-FileHash -Algorithm SHA256 in a private backup manifest.
# The new test must be absent before applying; record that absence for rollback.
git -C $Stage apply "$Package\candidate-code.diff"
python "$Package\verify_candidate.py" --root $Stage --mode postimage
# Must print MATCH, exit 0, including the new test.
```

The local read-only verifier was itself checked against exact baseline (MATCH), an altered worker (STOP_HASH_MISMATCH/exit 2), and current candidate (MATCH). A clean isolated scratch Git fixture passed apply-check, application, postimage check, reverse-check, reverse and restored preimage check. These are Linux scratch checks, not a claim of Windows application.

## Offline validation only

Run from `$Stage`, with the verified project interpreter and existing dependencies. These commands import the worker but invoke its main only inside fixtures that block HTTP/socket/provider calls. Do not run bare `python worker.py`, schedule it, synthesize narration or render a real story.

```powershell
Set-Location $Stage
python -m py_compile worker.py video_factory.py reels_preview.py editorial_quality_gate.py test_tr_storyboard_integration.py
python -m unittest -v test_tr_storyboard_integration
python -m unittest -v test_editorial_quality_gate test_reels_pipeline test_reels_duration_contract
```

Expected: 24 new focused methods PASS; 23 existing affected methods PASS. Keep stdout/stderr and interpreter/dependency identity. Existing `oldies-artists.json` must be present unchanged; missing it caused two initial snapshot setup errors here. `tests-A.log` is the final 24-method log. FFmpeg graph was additionally run with synthetic color inputs/synthetic silence to a null sink: PASS, no output media file. This only checks graph compatibility, not all-frame timing, natural voice quality, closing audibility or real film quality.

Expected actual consumer: `worker.main → reels_preview.prepare_preview → worker.render_preview → video_factory.build_storyboard_timelines → make_storyboard_scenes/make_caption_overlays → video_factory.render_timeline`. The 27s fixture must have 8 caption overlays, 3 distinct photo inputs, 2 photo transitions, complete exact closing and no delivery approval. An unknown/missing storyboard, changed binding/asset/voice, bad ranges, rejected/derived composition or missing rights must stop before the renderer/provider.

## Rollback and installed-source boundary

Rollback applies only to the isolated staging patch described above. First verify candidate postimage again. If it differs, STOP and reconcile the edits; do not overwrite. Then:

```powershell
python "$Package\verify_candidate.py" --root $Stage --mode postimage
git -C $Stage apply --reverse --check "$Package\candidate-code.diff"
git -C $Stage apply --reverse "$Package\candidate-code.diff"
python "$Package\verify_candidate.py" --root $Stage --mode preimage
```

Verify the new test is absent and four restored source files match the private preimage backup hashes. Preimage mode deliberately does not require the new test. Generated `__pycache__` files are not source; no destructive cleanup is necessary. A failed reverse check is a reconciliation stop, never permission to force reset. A separate installed-source change, if subsequently authorized, needs its own exact launcher/path/backup proof; this package grants none and asserts none.

## Real-media input package still open

Owner for coordination: MASTER; execution after explicit assignment: Windows Codex/media reviewer; independent acceptance: WORK WATCHDOG and founder as required by existing gates.

1. Three distinct, story-relevant, identity/composition-approved original images, particularly a credible guitar/studio/work scene; see `ASSET-MANIFEST.json`. P3 is a Work2 candidate, not final approval; the five archive originals do not make an accepted three-scene set.
2. Primary rights/territory/personality assessment for intended TR/GB/US use. LOC donor staff-rights basis is documented, but not CC0/worldwide clearance. Do not fill runtime image credits with invented Public domain/CC0 fields just to pass a gate.
3. A natural exact-script local Turkish narration, decoded within unchanged short-profile limits, audio SHA/transcript and reviewed measured word boundaries. No estimated timings, provider call or real voice/film was created here.
4. Independent source/photo/natural-DJ/final-media review; still required even if all local metadata validators pass. Preview status remains unapproved.
5. Canonical full founder-approved V3.0 constitution: not found in repo filename/code, Library or targeted context searches. MASTER must supply its exact source/version; do not mark it read. AGENTS, continuity, explicit task and central state were read. This missing source was reported during A and does not represent an inferred permission to expand scope.
