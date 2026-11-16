#!/usr/bin/env python3
"""Daily English review production. No publishing credentials or endpoints."""
from __future__ import annotations
import argparse, base64, hashlib, io, json, os, subprocess, wave
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests

ROOT = Path(__file__).resolve().parent
MODEL = 'gemini-2.5-flash-preview-tts'
MUSIC = {
    'title': 'Carefree', 'creator': 'Kevin MacLeod',
    'source': 'https://incompetech.com/music/royalty-free/index.html?isrc=USUAN1400037',
    'download': 'https://incompetech.com/music/royalty-free/mp3-royaltyfree/Carefree.mp3',
    'license': 'CC BY 4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
    'sha256': '8433b770a630d9b1594fd484442c677907ece899a4d149954cd2e74fd733e311',
}
CREDIT = ('Music: "Carefree" by Kevin MacLeod (incompetech.com). '
          'Licensed under CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. '
          'Edited: excerpt, reduced volume and fade-out.')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def event_key(candidate):
    return hashlib.sha256(json.dumps([candidate['artist'].casefold(), candidate['event_date'],
        candidate.get('kind', 'events')], ensure_ascii=False).encode()).hexdigest()


class Ledger:
    """Optimistic writes plus workflow concurrency; reservations precede provider use."""
    def __init__(self, local=None):
        self.local = Path(local) if local else None
        self.sha = None
        self.data = {'days': {}, 'events': {}}
        if self.local:
            if self.local.exists(): self.data = json.loads(self.local.read_text())
            return
        repo = os.environ['GITHUB_REPOSITORY']
        self.url = f'https://api.github.com/repos/{repo}/contents/english-review-ledger.json'
        self.headers = {'Authorization': 'Bearer ' + os.environ['GH_TOKEN'], 'Accept': 'application/vnd.github+json'}
        r = requests.get(self.url, params={'ref': 'english-review-state'}, headers=self.headers, timeout=30)
        r.raise_for_status()
        item = r.json(); self.sha = item['sha']
        self.data = json.loads(base64.b64decode(item['content']))

    def save(self):
        text = json.dumps(self.data, ensure_ascii=False, indent=2)
        if self.local:
            self.local.parent.mkdir(parents=True, exist_ok=True)
            temp = self.local.with_suffix('.tmp'); temp.write_text(text); temp.replace(self.local)
            return
        r = requests.put(self.url, headers=self.headers, json={'message': 'checkpoint: English review reservation/result',
            'branch': 'english-review-state', 'sha': self.sha,
            'content': base64.b64encode(text.encode()).decode()}, timeout=30)
        r.raise_for_status(); self.sha = r.json()['content']['sha']

    def reserve(self, day, key):
        if day in self.data['days'] or key in self.data['events']:
            return False
        record = {'day': day, 'event': key, 'status': 'reserved', 'run_id': os.getenv('GITHUB_RUN_ID', 'local')}
        self.data['days'][day] = record
        self.data['events'][key] = record
        self.save(); return True

    def complete(self, manifest):
        day, key = manifest['production_day'], manifest['event_key']
        record = self.data['days'].get(day, {})
        if record.get('event') != key or record.get('run_id') != os.getenv('GITHUB_RUN_ID', 'local'):
            raise RuntimeError('Reservation ownership mismatch')
        record = dict(record, status='artifact_saved', sha256=manifest['sha256'],
                      artifact_run=os.getenv('GITHUB_RUN_ID', 'local'))
        self.data['days'][day] = record; self.data['events'][key] = record; self.save()


def free_tts(**kwargs):
    """Fixed free-tier Developer API model; never select a paid fallback."""
    key = os.environ['GEMINI_API_KEY']
    payload = {'contents': [{'parts': [{'text': 'Synthesize speech. ' + kwargs['prompt'] +
                 '\nRead only this transcript:\n' + kwargs['text']}]}],
        'generationConfig': {'responseModalities': ['AUDIO'], 'speechConfig': {
            'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': 'Charon'}}}}}
    r = requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent',
        headers={'x-goog-api-key': key}, json=payload, timeout=180)
    if not r.ok:
        raise RuntimeError(f'Free-tier TTS refused ({r.status_code}); no paid fallback or automatic retry')
    parts = r.json().get('candidates', [{}])[0].get('content', {}).get('parts', [])
    part = next((p['inlineData'] for p in parts if 'inlineData' in p), None)
    if not part: raise RuntimeError('TTS returned no audio')
    raw = base64.b64decode(part['data'], validate=True)
    if not 1000 < len(raw) < 20 * 1024 * 1024: raise RuntimeError('Invalid TTS bytes')
    if 'wav' in part.get('mimeType', ''): return raw
    if not part.get('mimeType', '').startswith('audio/L16') and not part.get('mimeType', '').startswith('audio/pcm'):
        raise RuntimeError('Unexpected TTS audio encoding')
    out = io.BytesIO()
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)
    return out.getvalue()


def licensed_music(directory):
    path = directory / 'licensed-bed.mp3'
    r = requests.get(MUSIC['download'], timeout=45); r.raise_for_status()
    if len(r.content) > 15 * 1024 * 1024: raise RuntimeError('Music exceeds size limit')
    path.write_bytes(r.content)
    if digest(path) != MUSIC['sha256']: raise RuntimeError('Licensed music changed; re-review required')
    (directory / 'music-license.json').write_text(json.dumps(dict(MUSIC, credit=CREDIT), indent=2))
    return path


def mix_music(clean, bed, target, duration):
    # Preserve the DJ recording and its actual gap; mix the bed at a restrained level.
    graph = (f'[1:a]atrim=duration={duration},asetpts=PTS-STARTPTS,volume=0.055,'
             f'afade=t=in:d=0.6,afade=t=out:st={duration-1.2}:d=1.2[bed];'
             '[0:a][bed]amix=inputs=2:duration=first:normalize=0,'
             'alimiter=limit=0.794:level=false[a]')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(clean), '-stream_loop', '-1', '-i', str(bed),
        '-filter_complex', graph, '-map', '0:v:0', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac',
        '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', str(duration), '-movflags', '+faststart', str(target)], check=True, timeout=120)
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(target), '-f', 'null', '-'], check=True, timeout=120)


def select_candidate(day, directory):
    from zero_cost import research_candidates
    import worker, facebook_global_audio as audio, facebook_global_visuals as visuals
    failures = []
    reviewed = json.loads((ROOT / 'english-reviewed-events.json').read_text())['events']
    curated = [c for c in reviewed if c.get('reviewed') is True and c.get('sources')
               and str(c.get('event_date', ''))[5:] == day[5:]]
    candidates = curated or research_candidates([], today=datetime.fromisoformat(day))
    for candidate in candidates:
        try:
            headline = candidate.get('event_headline') if candidate in curated else None
            candidate = worker.apply_reel_language(candidate, 'en')
            if headline: candidate['event_headline'] = headline
            candidate['signoff_profile'] = 'calm'
            # Gate text and all reviewed photos before any provider request.
            story, _ = audio.build_dj_parts(candidate)
            audio.planned_video_seconds(audio.spoken_word_count(story) * 60 / audio.TEMPLATE['target_wpm'] + 1.1 + 6.72)
            photos, credits = visuals.load_period_photos(candidate, directory)
            candidate['image_credits'] = credits
            return candidate, photos
        except (RuntimeError, ValueError) as exc:
            failures.append(f"{candidate.get('artist')}: {exc}")
    raise RuntimeError('No eligible event with three reviewed period photos. ' + ' | '.join(failures)[:3000])


def build(day, output, ledger):
    import facebook_global_audio as audio, facebook_global_visuals as visuals
    from worker import draw_text_block, MAX_VIDEO_BYTES
    output.mkdir(parents=True, exist_ok=True)
    if day in ledger.data['days']:
        (output / 'status.json').write_text(json.dumps({'status': 'duplicate_blocked', 'day': day}))
        print('Duplicate day blocked; no provider request.'); return
    audio.selected_signoff({'signoff_profile': 'calm'})
    bed = licensed_music(output)
    candidate, photos = select_candidate(day, output)
    key = event_key(candidate)
    if not ledger.reserve(day, key):
        (output / 'status.json').write_text(json.dumps({'status': 'duplicate_blocked', 'event': key}))
        print('Duplicate event blocked; no provider request.'); return
    os.environ['OLDIES_PREVIEW_ONLY'] = 'true'
    voice = audio.synthesize_dj(candidate, output, '', '', free_tts)
    candidate['tts_engine'] = MODEL
    candidate['voiceover'] = {'enabled': True, 'source': MODEL}
    clean = output / 'clean-dj-review.mp4'
    visuals.render(visuals.make_scenes(candidate, photos, output, draw_text_block), clean, voice, candidate, MAX_VIDEO_BYTES)
    clean_qc = audio.validate_media(clean, candidate)
    clean_qc.update(audio.validate_recording(clean, candidate)); visuals.validate_publish(candidate)
    target = output / 'oldies-english-licensed-master.mp4'
    mix_music(clean, bed, target, clean_qc['video_duration_seconds'])
    final_qc = audio.inspect_audio(target)
    streams = final_qc.pop('streams')
    video_stream = next(s for s in streams if s.get('codec_type') == 'video')
    if (int(video_stream['width']) != 1080 or int(video_stream['height']) != 1920
            or abs(float(video_stream['duration']) - clean_qc['video_duration_seconds']) > 0.05
            or target.stat().st_size > MAX_VIDEO_BYTES):
        raise RuntimeError('Mixed final film differs from verified duration/frame/size')
    caption = candidate.get('dj_script_en', '') + '\n\n' + CREDIT + '\nMusic source: ' + MUSIC['source']
    for source in candidate.get('sources', []): caption += '\nEvent source: ' + source
    for p in candidate['image_credits']:
        caption += '\nPhoto: ' + p['creator'] + ' — ' + p['license'] + ' — ' + p['source']
    (output / 'caption.txt').write_text(caption, encoding='utf-8')
    if CREDIT not in (output / 'caption.txt').read_text(): raise RuntimeError('Mandatory attribution missing')
    manifest = {'status': 'rendered_pending_artifact', 'production_day': day, 'event_key': key,
        'sha256': digest(target), 'bytes': target.stat().st_size, 'tts_model': MODEL,
        'clean_qc': clean_qc, 'mixed_audio_qc': final_qc, 'music': MUSIC, 'music_credit': CREDIT,
        'publication_performed': False, 'human_media_acceptance': False, 'candidate': candidate}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({k:manifest[k] for k in ('status','production_day','sha256','publication_performed')}))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--commit', action='store_true')
    parser.add_argument('--day', default=datetime.now(ZoneInfo('Europe/Istanbul')).date().isoformat())
    parser.add_argument('--output', type=Path, default=ROOT / 'english-output')
    parser.add_argument('--local-ledger'); args = parser.parse_args()
    ledger = Ledger(args.local_ledger)
    if args.commit:
        path = args.output / 'manifest.json'
        if path.exists(): ledger.complete(json.loads(path.read_text()))
        return
    try: build(args.day, args.output, ledger)
    except Exception as exc:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'status.json').write_text(json.dumps({'status': 'blocked', 'reason': str(exc),
            'publication_performed': False}, ensure_ascii=False, indent=2))
        raise

if __name__ == '__main__': main()
