# OLDIES RADYO — Facebook Global locked recording template v3.0

This replaces every earlier Facebook recording/photo standard. Scope: Facebook Global English only. It does not authorize live publication.

| Recording part | Immutable rule |
|---|---|
| Main announcement | Short, complete sourced English music story. Start directly with the topic; max 25 written words. |
| Voice | Existing authenticated Gemini TTS, Charon, en-US. Warm, conversational music-radio DJ speaking personally to one listener; gentle inflection, unhurried phrases. |
| Pace | Approximately 128 WPM; estimated maximum 138. No speeding up. Limited pitch-preserving slowing only; reject overly rushed/long takes. |
| Separation | Separate story and station recording, with exactly 1.1 seconds of inserted digital silence between them. |
| Station recording | **Oldies Radyo. Timeless music. Listen, enjoy, share.** Brand spelling and spoken name stay Oldies Radyo in English. |
| Pronunciation direction | Oldies: OLD-eez. Radyo: RAH-dyoh, two syllables, first vowel ah. Directions do not replace the supplied script. |
| Reuse | After owner listening approval, bind the new recording to its SHA256, reviewer and approval timestamp. Production rejects unapproved or changed recordings. The superseded recording is removed. |
| Preview approval state | A new signoff may be generated for preview only. Its checksum is evidence of file identity, not owner approval. Production remains blocked while approval is pending. |
| Output | 1080×1920, 9:16, about 15–18 seconds. Real populated, decodable, audible MP4 audio stream. No audio:0kB. |
| Music | No automatically added music. Owner may add Meta Music Library music later. |

Example story: The Beatles released their debut single ‘Love Me Do’ in Britain — on this day in 1962.

Warm voice direction: English only. Be a warm, unhurried music-radio DJ speaking personally to one listener. A friendly smile in your voice; intimate and conversational, with gentle natural inflection. Never a newsreader, hard-sell announcer or robotic voice. Read the supplied words exactly once, at approximately 128 WPM. Let each phrase breathe. No added words, music, singing or effects.

## Immutable photography policy

1. Search the actual event year first. Prefer three distinct reviewed photographs of that year.
2. Use ±1 year only when sufficient eligible same-year photographs cannot be found; record sources, reviewer, timestamp and necessity.
3. ±2 years is never an automatic fallback. It needs event-specific manual approval bound to the photograph SHA256 and recorded necessity plus hair, clothing, lineup and stage/appearance checks. Same-year and ±1 choices must first be exhausted.
4. ±3 years and beyond are forbidden even with an override.
5. Required together: correct artist, correct year/era, correct appearance, **artist-dominant composition**. Equal-weight guests, distracting guests, or the artist small/in the background are rejected.
6. Real photographs only. No statues, plaques, signs, covers/sleeves, replicas, illustrations or unrelated subjects. No unresolved copyright disputes. Source, photographer, date evidence, reuse license and SHA256 must be recorded.
7. Visually review the complete original source composition. All four Beatles must remain visible. At least 1080 pixels on the long edge; no fabricated upscaling to qualify a weak source.
8. Show the complete approved source image using proportional contain. No crop, zoom, pan or blurred crop-fill. No derived copies to fill three photo slots. Three distinct compositions and three distinct hashes are mandatory.
9. Archive year is labeled explicitly. A +1 archive photograph is not claimed to show the release event.
10. If sufficient eligible photographs do not exist, fail closed. Do not advance to older/newer eras to fill slots.

## Beatles 1962 pool

The actual 1962 Cavern result reviewed was only 711×501 and had an active copyright/deletion dispute. Modern exhibits, replicas and covers did not qualify. No set of three eligible high-resolution 1962 photos was verified. The test uses three distinct 1963 (+1) photographs: Hoffmann publicity portrait, Bo Trenter Stockholm group photograph, and Hötorgscity group jump. Dates, licensing evidence, visual review and hashes are in facebook-global-photo-bank.json. No 1964/1965 fallback or ±2 approval is used.

Publication gates validate the actual rendered MP4, brand/copy, separate recording gap, approved signoff hash, event-year-first bank selection and visual metadata before the existing R2.2/WordPress delivery body. TTS failure has no silent fallback. Other social workflows and delivery/dedupe semantics remain outside this change.
