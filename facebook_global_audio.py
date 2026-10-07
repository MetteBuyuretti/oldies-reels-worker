"""English DJ recording template and fail-closed Facebook-only audio gates."""
from __future__ import annotations
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = json.loads((ROOT / 'facebook-global-template.json').read_text(encoding='utf-8'))

BRAND_NAME = 'Oldies Radyo'
BRAND_ADVERT = 'Oldies Radyo. Timeless music. Listen, enjoy, share.'
if TEMPLATE.get('brand_name') != BRAND_NAME or TEMPLATE.get('brand_translation_allowed') is not False or TEMPLATE.get('advert_text') != BRAND_ADVERT:
    raise RuntimeError('Facebook Global brand lock violated: the spoken and written brand must remain Oldies Radyo')


def build_dj_parts(candidate: dict) -> tuple[str, str]:
    artist = re.sub(r'\s+', ' ', str(candidate.get('artist', ''))).strip()
    year = str(candidate.get('event_date', ''))[:4]
    if not artist or not re.fullmatch(r'\d{4}', year):
        raise RuntimeError('Facebook DJ copy requires an artist and verified event year')
    kind = candidate.get('kind', 'events')
    if kind == 'births':
        story = f'Born on this day in {year}: {artist}. A voice from the golden years of music.'
    elif kind == 'deaths':
        story = f'Remembering {artist}, who left us on this day in {year}. The music lives on.'
    else:
        source = re.sub(r'\s+', ' ', str(candidate.get('source_text', ''))).strip()
        first = re.split(r'(?<=[.!?])\s+(?=[A-Z])', source, maxsplit=1)[0]
        if not first or artist.casefold() not in first.casefold() or not 4 <= len(first.split()) <= 20:
            raise RuntimeError('Facebook DJ needs a short, complete sourced English story')
        story = first.rstrip('.!?')
        if not re.search(r'\bon this day\b', story, re.I):
            story += f' — on this day in {year}'
        story += '.'
    if len(story.split()) > TEMPLATE['max_story_words']:
        raise RuntimeError('Facebook DJ story is too long for a relaxed recording')
    return story, BRAND_ADVERT


def build_dj_script(candidate: dict) -> str:
    return ' '.join(build_dj_parts(candidate))


def spoken_word_count(text: str) -> int:
    # Approximate four-digit years as three spoken words, rather than one token.
    return len(re.findall(r"[\w]+(?:['’][\w]+)?", text)) + 2 * len(re.findall(r'\b\d{4}\b', text))


def record_part(text: str, role: str, path: Path, project: str, token: str, synthesize) -> dict:
    prompt = (
        'English only. Be a warm, unhurried music-radio DJ speaking personally to one listener. '
        'A friendly smile in your voice; intimate and conversational, with gentle natural inflection. '
        'Never a newsreader, hard-sell announcer, or robotic voice. '
        f'Read at approximately {TEMPLATE["target_wpm"]} words per minute. Let each phrase breathe; '
        'do not race to fit a time limit. Read the supplied words exactly once. '
        'No music, singing, effects, filler or added words. '
    )
    if role == 'advert':
        prompt += ("This is a separate soft station promotion after the story. The brand name is exactly Oldies Radyo. "
                   "Do not translate, rewrite or substitute it as Oldies Radio. Pronounce Oldies Radyo clearly: old-eez rah-dee-oh. ")
    else:
        prompt += 'Start directly with the music story, with a small natural pause before the date. '
    raw = synthesize(text=text, prompt=prompt, language=TEMPLATE['language'], voice_name=TEMPLATE['voice'],
                     project=project, token=token, model_name='gemini-2.5-pro-tts')
    if not raw or len(raw) > 20 * 1024 * 1024:
        raise RuntimeError('Facebook English DJ TTS returned invalid audio bytes')
    path.write_bytes(raw)
    qc = inspect_audio(path)
    words = spoken_word_count(text)
    target_seconds = words * 60 / TEMPLATE['target_wpm']
    factor = min(1.0, qc['duration_seconds'] / target_seconds)
    if factor < TEMPLATE['minimum_slowdown_factor']:
        raise RuntimeError('Facebook DJ take was too rushed; rerecord instead of extreme time stretching')
    if factor < 0.995:
        timed = path.with_name(path.stem + '-relaxed.mp3')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(path), '-af', f'atempo={factor:.6f}',
                        '-c:a', 'libmp3lame', '-b:a', '192k', str(timed)], check=True, timeout=60)
        timed.replace(path)
        qc = inspect_audio(path)
    estimated_wpm = words * 60 / qc['duration_seconds']
    if estimated_wpm > TEMPLATE['max_estimated_wpm']:
        raise RuntimeError('Facebook DJ take exceeds the relaxed pace limit')
    return {'duration_seconds': qc['duration_seconds'], 'spoken_words_estimated': words,
            'estimated_wpm': round(estimated_wpm, 1), 'tempo_factor': round(factor, 4)}


def synthesize_dj(candidate: dict, directory: Path, project: str, token: str, synthesize) -> Path:
    story, advert = build_dj_parts(candidate)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'voiceover-facebook-en.mp3'
    path.unlink(missing_ok=True)
    story_path, advert_path = directory / 'dj-story-en.mp3', directory / 'dj-advert-en.mp3'
    try:
        story_qc = record_part(story, 'story', story_path, project, token, synthesize)
        cached = ROOT / TEMPLATE['advert_asset']
        expected_hash = str(TEMPLATE.get('advert_sha256') or '').strip()
        if cached.is_file() and expected_hash:
            if hashlib.sha256(cached.read_bytes()).hexdigest() != expected_hash:
                raise RuntimeError('Facebook approved station recording hash mismatch')
            advert_path.write_bytes(cached.read_bytes())
            advert_qc = inspect_audio(advert_path)
            advert_qc = {'duration_seconds': advert_qc['duration_seconds'], 'cached_approved_recording': True}
        else:
            # The previous cached signoff said "Oldies Radio" and is intentionally never reused.
            # Until a new Oldies Radyo signoff is approved and hash-locked, synthesize the exact locked brand text.
            advert_qc = record_part(advert, 'advert', advert_path, project, token, synthesize)
        gap = TEMPLATE['advert_gap_seconds']
        duration = story_qc['duration_seconds'] + gap + advert_qc['duration_seconds']
        if duration > TEMPLATE['max_voiceover_seconds']:
            raise RuntimeError(f'Facebook relaxed DJ recording is too long ({duration:.2f}s); shorten the copy, never speed up')
        # A separate digital silence guarantees distance from the main announcement.
        graph = (f'[0:a]aresample=48000,aformat=channel_layouts=mono[a];'
                 f'anullsrc=r=48000:cl=mono,atrim=duration={gap},asetpts=PTS-STARTPTS[gap];'
                 '[1:a]aresample=48000,aformat=channel_layouts=mono[b];'
                 '[a][gap][b]concat=n=3:v=0:a=1[voice]')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(story_path), '-i', str(advert_path),
                        '-filter_complex', graph, '-map', '[voice]', '-c:a', 'libmp3lame', '-b:a', '192k', str(path)],
                       check=True, timeout=60)
        qc = inspect_audio(path)
        if qc['duration_seconds'] > TEMPLATE['max_voiceover_seconds']:
            raise RuntimeError('Facebook combined DJ recording exceeds the template duration')
    except Exception:
        path.unlink(missing_ok=True)
        raise
    recording = {'version': TEMPLATE['version'], 'brand_name': BRAND_NAME, 'story_text': story, 'advert_text': advert,
                 'story': story_qc, 'advert': advert_qc, 'advert_gap_seconds': gap,
                 'advert_start_seconds': round(story_qc['duration_seconds'] + gap, 3),
                 'speedup_applied': False, 'background_music_added': False}
    candidate.update(dj_script_en=f'{story} {advert}', tts_language=TEMPLATE['language'], tts_voice=TEMPLATE['voice'],
                     tts_engine='gemini-2.5-pro-tts-facebook-dj', dj_recording=recording,
                     voiceover_duration_seconds=qc['duration_seconds'])
    (directory / 'dj-recording.json').write_text(json.dumps(recording, indent=2), encoding='utf-8')
    print(f'English DJ voice-over generated: warm template {TEMPLATE["version"]}, {qc["duration_seconds"]:.2f}s, separate advert + {gap:.2f}s gap')
    return path


def inspect_audio(path: Path) -> dict:
    if not path.is_file() or not path.stat().st_size:
        raise RuntimeError('Silent publish blocked: audio file is missing or empty')
    probe = subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-show_streams', '-show_format', '-of', 'json', str(path)],
                           check=True, capture_output=True, text=True, timeout=60)
    data = json.loads(probe.stdout)
    audio = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
    if not audio or int(audio[0].get('nb_read_packets') or 0) <= 0:
        raise RuntimeError('Silent publish blocked: no populated audio stream (audio:0kB)')
    duration = float(audio[0].get('duration') or data.get('format', {}).get('duration') or 0)
    if not math.isfinite(duration) or duration <= 0:
        raise RuntimeError('Silent publish blocked: invalid audio duration')
    decoded = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(path), '-map', '0:a:0', '-af', 'volumedetect', '-f', 'null', '-'],
                             capture_output=True, text=True, timeout=60)
    mean = re.search(r'mean_volume:\s*([-\d.]+) dB', decoded.stderr)
    peak = re.search(r'max_volume:\s*([-\d.]+) dB', decoded.stderr)
    if decoded.returncode or not mean or not peak or float(mean.group(1)) <= -60 or float(peak.group(1)) <= -50:
        raise RuntimeError('Silent publish blocked: audio cannot be decoded or contains no audible signal')
    return {'audio_stream_detected': True, 'audio_packets': int(audio[0]['nb_read_packets']),
            'audio_codec': audio[0]['codec_name'], 'duration_seconds': round(duration, 3),
            'mean_volume_db': float(mean.group(1)), 'max_volume_db': float(peak.group(1)), 'streams': data['streams']}


def require_voiceover(candidate: dict, voiceover: Path | None) -> None:
    if not voiceover or not str(candidate.get('tts_language', '')).startswith('en-') or not candidate.get('dj_script_en'):
        raise RuntimeError('Silent publish blocked: generated English DJ voice-over is mandatory')
    inspect_audio(voiceover)


def validate_media(video: Path, candidate: dict) -> dict:
    if not candidate.get('voiceover', {}).get('enabled') or not str(candidate.get('tts_language', '')).startswith('en-') or not candidate.get('dj_script_en'):
        raise RuntimeError('Silent publish blocked: English DJ voice-over metadata is missing')
    qc = inspect_audio(video)
    visual = next((s for s in qc.pop('streams') if s.get('codec_type') == 'video'), {})
    width, height = int(visual.get('width', 0)), int(visual.get('height', 0))
    if not width or width * 16 != height * 9:
        raise RuntimeError('Facebook Global MP4 must retain the 9:16 visual template')
    duration = float(visual.get('duration') or qc['duration_seconds'])
    if not 10 <= duration <= TEMPLATE['max_video_seconds'] + 0.05:
        raise RuntimeError(f'Facebook Global MP4 must fit a 10–18-second relaxed Reel: {duration:.2f}s')
    qc.update(width=width, height=height, video_duration_seconds=duration, silent_publish_blocked=True, background_music_added=False)
    print(f'Audio stream detected: {qc["audio_codec"]}, {qc["audio_packets"]} packets; silent publish blocked')
    return qc


def validate_recording(video: Path, candidate: dict) -> dict:
    recording = candidate.get('dj_recording', {})
    if (recording.get('version') != TEMPLATE['version'] or recording.get('brand_name') != BRAND_NAME
            or recording.get('advert_text') != BRAND_ADVERT or 'Oldies Radio' in str(candidate.get('dj_script_en', ''))
            or recording.get('speedup_applied') is not False
            or recording.get('advert_gap_seconds') != TEMPLATE['advert_gap_seconds']
            or recording.get('background_music_added') is not False):
        raise RuntimeError('Facebook publish blocked: approved warm DJ recording and separated station promotion required')
    if float(recording.get('story', {}).get('estimated_wpm', 999)) > TEMPLATE['max_estimated_wpm']:
        raise RuntimeError('Facebook publish blocked: DJ story is too fast')
    advert = recording.get('advert', {})
    advert_wpm = spoken_word_count(recording['advert_text']) * 60 / float(advert.get('duration_seconds') or .001)
    if advert_wpm > TEMPLATE['max_estimated_wpm']:
        raise RuntimeError('Facebook publish blocked: station promotion is too fast')
    center = float(recording.get('story', {}).get('duration_seconds') or 0) + TEMPLATE['advert_gap_seconds'] / 2
    decoded = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-ss', f'{center - .2:.3f}', '-i', str(video),
                              '-t', '0.4', '-vn', '-af', 'volumedetect', '-f', 'null', '-'],
                             capture_output=True, text=True, timeout=60)
    level = re.search(r'max_volume:\s*([-\d.]+) dB', decoded.stderr)
    if decoded.returncode or not level or float(level.group(1)) > -50:
        raise RuntimeError('Facebook publish blocked: story and station promotion must have a real silent gap')
    return {'warm_recording_template': TEMPLATE['version'], 'story_estimated_wpm': recording['story']['estimated_wpm'],
            'advert_estimated_wpm': round(advert_wpm, 1), 'advert_gap_seconds': TEMPLATE['advert_gap_seconds'],
            'gap_max_volume_db': float(level.group(1)), 'speedup_applied': False}
