#!/usr/bin/env python3
"""Daily English review production. No publishing credentials or endpoints."""
from __future__ import annotations
import argparse, base64, hashlib, io, json, os, re, subprocess, wave, zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests

ROOT = Path(__file__).resolve().parent
MODEL = 'gemini-2.5-flash-preview-tts'
PROFILE=json.loads((ROOT/'news-production-profile.json').read_text())
MUSIC=PROFILE['music']
CREDIT=(f'Music: "{MUSIC["title"]}" by {MUSIC["creator"]} (incompetech.com). '
        f'Licensed under {MUSIC["license"]}: {MUSIC["license_url"]}. '
        'Edited: excerpt, broadcast mix, ducking and fade-out.')


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


def clean_provider_pauses(raw, directory):
    """Remove only detected digital dead air; speech samples remain byte-identical."""
    with wave.open(io.BytesIO(raw), 'rb') as w:
        channels, width, rate = w.getnchannels(), w.getsampwidth(), w.getframerate()
        frames = w.readframes(w.getnframes())
    if (channels, width, rate) != (1, 2, 24000):
        raise RuntimeError('Unexpected provider PCM format; silence editing refused')
    duration = len(frames) / (rate * width)
    probe = subprocess.run(['ffmpeg','-hide_banner','-nostats','-i','pipe:0','-af',
        'silencedetect=n=-50dB:d=1.0','-f','null','-'],input=raw,capture_output=True,timeout=60,check=True)
    intervals=[]; start=None
    for m in re.finditer(r'silence_(start|end):\s*([\d.]+)',probe.stderr.decode()):
        if m[1]=='start': start=float(m[2])
        elif start is not None:
            intervals.append((start,min(duration,float(m[2]))));start=None
    if start is not None: intervals.append((start,duration))
    chunks=[]; cursor=0; edits=[]
    for a,b in intervals:
        # Keep a 20ms guard around detected boundaries, preserving speech transients.
        if a > .02: a += .02
        if b < duration-.02: b -= .02
        i,j=round(a*rate),round(b*rate)
        keep=.10 if b>=duration-.02 else (.10 if a<.02 else .50)
        if b-a<=keep: continue
        n=round(keep*rate); left=n//2
        chunks.extend([frames[cursor*width:i*width],frames[i*width:(i+left)*width],frames[(j-(n-left))*width:j*width]])
        cursor=j; edits.append({'silence_start':a,'silence_end':b,'kept_seconds':keep})
    chunks.append(frames[cursor*width:]);pcm=b''.join(chunks)
    result=io.BytesIO()
    with wave.open(result,'wb') as w:
        w.setnchannels(channels);w.setsampwidth(width);w.setframerate(rate);w.writeframes(pcm)
    cleaned=result.getvalue();directory.mkdir(parents=True,exist_ok=True)
    (directory/'provider-story-original.wav').write_bytes(raw)
    (directory/'provider-pause-edits.json').write_text(json.dumps({'original_sha256':hashlib.sha256(raw).hexdigest(),
        'cleaned_sha256':hashlib.sha256(cleaned).hexdigest(),'original_seconds':duration,
        'cleaned_seconds':len(pcm)/(rate*width),'speech_tempo_factor':1.0,'speech_samples_changed':False,'edits':edits},indent=2))
    return cleaned


def recovered_provider_take(text):
    marker=ROOT/'.github/manual-english-review-trigger'
    if os.getenv('GITHUB_EVENT_NAME')!='push' or not marker.exists(): return None
    try: spec=json.loads(marker.read_text()).get('recover_provider')
    except ValueError: return None
    if not spec: return None
    if hashlib.sha256(text.encode()).hexdigest()!=spec['story_sha256']:
        raise RuntimeError('Recovered provider transcript mismatch')
    repo=os.environ['GITHUB_REPOSITORY'];headers={'Authorization':'Bearer '+os.environ['GH_TOKEN']}
    base=f'https://api.github.com/repos/{repo}/actions/artifacts/{int(spec["artifact_id"])}'
    metadata=requests.get(base,headers=headers,timeout=30);metadata.raise_for_status()
    run=metadata.json()['workflow_run']
    if run['id']!=spec['run_id'] or run['head_sha']!=spec['head_sha']:
        raise RuntimeError('Recovered provider artifact provenance mismatch')
    archive=requests.get(base+'/zip',headers=headers,timeout=60);archive.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(archive.content)) as z:
        member=spec.get('member','dj-story-en.mp3')
        if member not in {'dj-story-en.mp3','provider-story-original.wav'}: raise RuntimeError('Unexpected recovery audio member')
        info=z.getinfo(member)
        if info.file_size>20*1024*1024: raise RuntimeError('Recovered provider source too large')
        raw=z.read(info)
    if hashlib.sha256(raw).hexdigest()!=spec['audio_sha256']:
        raise RuntimeError('Recovered provider audio hash mismatch')
    print('Recovered exact provider recording and transcript; new provider calls=0')
    return raw


def free_tts(**kwargs):
    """Fixed free-tier Developer API model; never select a paid fallback."""
    directory=Path(os.environ.get('OLDIES_EN_OUTPUT_DIR',str(ROOT/'english-output')))
    recovered=recovered_provider_take(kwargs['text'])
    if recovered is not None: return clean_provider_pauses(recovered,directory)
    key = os.environ['GEMINI_API_KEY']
    prompt=PROFILE['voice_direction']+'\nTranscript:\n'
    payload = {'contents': [{'parts': [{'text': prompt + kwargs['text']}]}],
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
    if not 1000 < len(raw) < 20 * 1024 * 1024:
        raise RuntimeError(f'Invalid TTS bytes: {len(raw)}; MIME {part.get("mimeType", "unknown")}')
    if 'wav' in part.get('mimeType', ''): return clean_provider_pauses(raw,directory)
    if not part.get('mimeType', '').startswith('audio/L16') and not part.get('mimeType', '').startswith('audio/pcm'):
        raise RuntimeError('Unexpected TTS audio encoding')
    out = io.BytesIO()
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(raw)
    return clean_provider_pauses(out.getvalue(),directory)


def era_music(candidate):
    year=int(candidate['event_date'][:4])
    decade=int(candidate.get('music_era_decade',year//10*10))
    catalog=json.loads((ROOT/'era-music-catalog.json').read_text())['tracks']
    if str(decade) not in catalog:raise RuntimeError('1950s-1990s musical era must be explicitly identified')
    track=dict(catalog[str(decade)])
    if track.get('instrumental') is not True or track['style_decade']!=decade:
        raise RuntimeError('Instrumental era metadata mismatch')
    credit=(f'Music: "{track["title"]}" by {track["creator"]} (incompetech.com). '
            f'Licensed under {track["license"]}: {track["license_url"]}. '
            'Edited: excerpt, broadcast mix, ducking and fade-out.')
    candidate['music_license']=track;candidate['music_credit']=credit
    return track,credit


def licensed_music(directory, candidate=None):
    track,credit=era_music(candidate) if candidate is not None else (MUSIC,CREDIT)
    path = directory / 'licensed-bed.mp3'
    r = requests.get(track['download'], timeout=45); r.raise_for_status()
    if len(r.content) > 15 * 1024 * 1024: raise RuntimeError('Music exceeds size limit')
    path.write_bytes(r.content)
    if digest(path) != track['sha256']: raise RuntimeError('Licensed music changed; re-review required')
    (directory / 'music-license.json').write_text(json.dumps(dict(track, credit=credit), indent=2))
    return path


def mix_music(clean, bed, target, duration):
    # Preserve the DJ recording and its actual gap; mix the bed at a restrained level.
    graph = (f'[0:a]asplit=2[voice][control];'
             f'[1:a]atrim=duration={duration},asetpts=PTS-STARTPTS,'
             f'loudnorm=I={PROFILE["bed_lufs"]}:TP=-3:LRA=6,'
             f'aresample=48000,aformat=channel_layouts=stereo,'
             f'afade=t=in:d=0.15,afade=t=out:st={duration-.7}:d=0.7[bed];'
             f'[bed][control]sidechaincompress=threshold=0.06:ratio={PROFILE["duck_ratio"]}:'
             'attack=15:release=220[ducked];'
             '[voice][ducked]amix=inputs=2:duration=first:normalize=0,'
             'alimiter=limit=0.76:level=false[a]')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(clean), '-stream_loop', '-1', '-i', str(bed),
        '-filter_complex', graph, '-map', '0:v:0', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac',
        '-b:a', '192k', '-ar', '48000', '-ac', '2', '-t', str(duration), '-movflags', '+faststart', str(target)], check=True, timeout=120)
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(target), '-f', 'null', '-'], check=True, timeout=120)


def select_candidate(day, directory, ledger=None):
    from zero_cost import research_candidates
    import worker, facebook_global_audio as audio, facebook_global_visuals as visuals
    failures = []
    reviewed = json.loads((ROOT / 'english-reviewed-events.json').read_text())['events']
    used=(ledger.data.get('events',{}) if ledger else {})
    eligible=[c for c in reviewed if c.get('reviewed') is True and c.get('sources') and event_key(c) not in used]
    dated=[c for c in eligible if str(c.get('event_date',''))[5:]==day[5:]]
    archive=[c for c in eligible if c.get('archive_fallback_allowed') and c not in dated]
    curated=dated+archive
    candidates=curated or research_candidates([], today=datetime.fromisoformat(day))
    for candidate in candidates:
        try:
            headline = candidate.get('event_headline') if candidate in curated else None
            candidate = worker.apply_reel_language(candidate, 'en')
            if headline: candidate['event_headline'] = headline
            candidate['signoff_profile'] = 'calm'
            candidate['delivery_profile'] = PROFILE['id']
            candidate['date_context']='on_this_day' if candidate['event_date'][5:]==day[5:] else 'archive'
            # Gate text and all reviewed photos before any provider request.
            story, _ = audio.build_dj_parts(candidate)
            audio.planned_video_seconds(audio.spoken_word_count(story) * 60 / PROFILE['target_wpm'] + 1.1 + 6.72)
            photos, credits = visuals.load_period_photos(candidate, directory)
            candidate['image_credits'] = credits
            return candidate, photos
        except (RuntimeError, ValueError) as exc:
            failures.append(f"{candidate.get('artist')}: {exc}")
    raise RuntimeError('No eligible event with three reviewed period photos. ' + ' | '.join(failures)[:3000])


def stock_health(day,ledger,output):
    import facebook_global_audio as audio,facebook_global_visuals as visuals
    ready=[];rejected=[]
    for c in json.loads((ROOT/'english-reviewed-events.json').read_text())['events']:
        if (not c.get('reviewed') or not c.get('sources') or event_key(c) in ledger.data.get('events',{})
                or not (c.get('archive_fallback_allowed') or c['event_date'][5:]==day[5:])):continue
        try:
            c=dict(c,delivery_profile=PROFILE['id'])
            story,_=audio.build_dj_parts(c)
            audio.planned_video_seconds(audio.spoken_word_count(story)*60/PROFILE['target_wpm']+1.1+6.72)
            visuals.select_period_photos(c)
            ready.append({'artist':c['artist'],'event_date':c['event_date'],'kind':c['kind']})
        except (ValueError,RuntimeError) as exc:rejected.append({'event':c['event_date'],'reason':str(exc)})
    report={'checked_day':day,'ready_unproduced_stories':len(ready),'target':PROFILE['stock_target_days'],
            'status':'ready' if len(ready)>PROFILE['stock_warning_days'] else 'low_stock','items':ready,'rejected':rejected,
            'note':'Reviewed text and period-photo stock, not pre-rendered videos. Archive items show their real date.'}
    output.mkdir(parents=True,exist_ok=True);(output/'stock-health.json').write_text(json.dumps(report,indent=2))
    summary=os.getenv('GITHUB_STEP_SUMMARY')
    if summary:
        with open(summary,'a') as f:f.write(f"\nEnglish news stock: {len(ready)} reviewed unused stories; status {report['status']}.\n")
    if report['status']=='low_stock':print('::warning::English reviewed content stock is below three stories')
    return report


def build(day, output, ledger):
    import facebook_global_audio as audio, facebook_global_visuals as visuals
    from worker import draw_text_block, MAX_VIDEO_BYTES
    output.mkdir(parents=True, exist_ok=True)
    stock_health(day,ledger,output)
    if day in ledger.data['days']:
        (output / 'status.json').write_text(json.dumps({'status': 'duplicate_blocked', 'day': day}))
        print('Duplicate day blocked; no provider request.'); return
    audio.selected_signoff({'signoff_profile': 'calm'})
    candidate, photos = select_candidate(day, output, ledger)
    bed = licensed_music(output,candidate)
    key = event_key(candidate)
    if not ledger.reserve(day, key):
        (output / 'status.json').write_text(json.dumps({'status': 'duplicate_blocked', 'event': key}))
        print('Duplicate event blocked; no provider request.'); return
    os.environ['OLDIES_PREVIEW_ONLY'] = 'true'
    os.environ['OLDIES_EN_OUTPUT_DIR'] = str(output.resolve())
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
    credit=candidate['music_credit'];music=candidate['music_license']
    caption = candidate.get('dj_script_en', '') + '\n\n' + credit + '\nMusic source: ' + music['source']
    for source in candidate.get('sources', []): caption += '\nEvent source: ' + source
    for p in candidate['image_credits']:
        caption += '\nPhoto: ' + p['creator'] + ' — ' + p['license'] + ' — ' + p['source']
    (output / 'caption.txt').write_text(caption, encoding='utf-8')
    if credit not in (output / 'caption.txt').read_text(): raise RuntimeError('Mandatory attribution missing')
    manifest = {'status': 'rendered_pending_artifact', 'production_day': day, 'event_key': key,
        'sha256': digest(target), 'bytes': target.stat().st_size, 'tts_model': MODEL, 'production_profile': PROFILE,
        'clean_qc': clean_qc, 'mixed_audio_qc': final_qc, 'music': music, 'music_credit': credit,
        'background_music_added': True, 'publication_performed': False, 'human_media_acceptance': False, 'candidate': candidate}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(json.dumps({k:manifest[k] for k in ('status','production_day','sha256','publication_performed')}))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--commit', action='store_true')
    parser.add_argument('--day', default=datetime.now(ZoneInfo('Europe/Istanbul')).date().isoformat())
    parser.add_argument('--output', type=Path, default=ROOT / 'english-output')
    parser.add_argument('--local-ledger'); args = parser.parse_args()
    marker=ROOT/'.github/manual-english-review-trigger'
    try: preview=json.loads(marker.read_text()).get('preview_audio_profile') if os.getenv('GITHUB_EVENT_NAME')=='push' else False
    except (ValueError,OSError): preview=False
    ledger=Ledger(args.output/'profile-preview-ledger.json' if preview else args.local_ledger)
    if args.commit:
        path = args.output / 'manifest.json'
        if path.exists():
            manifest=json.loads(path.read_text())
            if not manifest.get('reused_approved_source'): ledger.complete(manifest)
        return
    try: build(args.day, args.output, ledger)
    except Exception as exc:
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / 'status.json').write_text(json.dumps({'status': 'blocked', 'reason': str(exc),
            'publication_performed': False}, ensure_ascii=False, indent=2))
        raise

if __name__ == '__main__': main()
