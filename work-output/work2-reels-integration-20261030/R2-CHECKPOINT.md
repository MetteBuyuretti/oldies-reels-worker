# R2 source checkpoint

WORK2-REELS-INTEGRATION-20261030-01
R1 checkpoint: 63395276b95960ce0de54150957c1e5a7d4d9915.

The Facebook-only template, synthesis, renderer and MP4 gate now share a natural 25–30-second calculation. Story + unchanged accepted ending + existing 1.1s gap are measured; a fixed 0.6s ending tail is quantized to 30fps. Short/long/nonfinite durations reject; no 15s floor or silent padding of short copy into acceptance. Natural takes are not time-stretched. The original maximum 25 story words / first-sentence 20-word restriction becomes a 52-word ceiling; this is an upper bound, not duration proof.

Existing photo selection/licensing/period/full-frame functions are byte-for-byte unchanged. Other channels and worker.py are unchanged. Whole-story originality/source quality, real media and Windows entry remain unaccepted; base PR22 generic birth/death copy can fail the duration gate and is not silently expanded with filler. Longer sourced first-sentence support is not independent editorial verification.

22 offline test methods prepared across test_facebook_signoff_integration and migrated test_facebook_global_audio. Fixtures stub audio bytes, measurements and concat/render subprocesses. Obsolete tests expecting preview ending regeneration, extreme slowdown or 10–18s acceptance were migrated; silence/stream/aspect/brand/gap/pacing/approval checks retained in fixture form.

Attempted exact command: python -m unittest -v test_facebook_signoff_integration test_facebook_global_audio
Result: NOT STARTED — No usable execution environment is available. No Python tests or syntax checks passed. JavaScript payload assertions only checked source strings and JSON production flags, not Python semantics.

Next: validate this exact implementation commit in an authorized offline Python environment. Do not run the inherited PR22 Google-auth/TTS workflow.
