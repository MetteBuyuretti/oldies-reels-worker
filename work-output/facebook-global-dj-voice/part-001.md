# Facebook Global English DJ voice fix — checkpoint 001

Facebook-only Gemini Charon English one-take narration uses the existing Google workload identity and authenticated TTS function. TTS is enabled; silent fallback is disabled. Narration failure, missing/empty audio streams, undecodable audio, digital silence, non-English metadata, wrong aspect ratio and excessive duration fail before delivery. The pre-existing three-photo visual layout is preserved. R2.2 / WordPress payload and topic dedupe are unchanged.

10 Facebook-specific real-media tests passed. Full suite: 33/34 passed; the existing Turkish unsupported-story test also fails at the unmodified base commit and is outside this fix. Other workflows are byte-identical. No live Facebook publishing has been performed.

Next: run the Facebook workflow on the fix branch in forced preview mode for 2026-10-05 / The Beatles, then inspect the MP4 and logs. Main has not been changed.
