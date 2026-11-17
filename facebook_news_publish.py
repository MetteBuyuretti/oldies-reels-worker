#!/usr/bin/env python3
"""Publish the accepted 25-30s English news through the existing WP companion."""
import argparse,io,json,os,re,zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import requests
import english_review as review
import facebook_global_audio as audio
import facebook_global_visuals as visuals
from worker import publish_delivery_asset
ROOT=Path(__file__).resolve().parent
POLICY=json.loads((ROOT/'facebook-news-policy.json').read_text())


def require_policy():
    if not POLICY.get('owner_approved') or not POLICY.get('live_facebook_enabled') or not POLICY.get('approved_at'):
        raise RuntimeError('Owner publication authorization is absent')


def get_artifact(artifact_id,output,expected_sha=None):
    repo=os.environ['GITHUB_REPOSITORY'];headers={'Authorization':'Bearer '+os.environ['GH_TOKEN']}
    r=requests.get(f'https://api.github.com/repos/{repo}/actions/artifacts/{int(artifact_id)}/zip',headers=headers,timeout=90)
    r.raise_for_status();output.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        for info in z.infolist():
            dest=(output/info.filename).resolve()
            if not dest.is_relative_to(output.resolve()) or info.file_size>100*1024*1024:raise RuntimeError('Invalid artifact member')
        z.extractall(output)
    manifest=json.loads((output/'manifest.json').read_text())
    if review.digest(output/'oldies-english-licensed-master.mp4')!=manifest['sha256']:
        raise RuntimeError('Recovered film does not match its saved manifest')
    if expected_sha and manifest['sha256']!=expected_sha:raise RuntimeError('Not the owner-accepted source film')
    return manifest


def prepare_existing(output,ledger,day):
    require_policy();record=ledger.data.get('days',{}).get(day,{})
    bootstrap=POLICY.get('bootstrap',{})
    if bootstrap.get('day')==day:
        manifest=get_artifact(bootstrap['artifact_id'],output,bootstrap['sha256'])
    else:
        run_id=record.get('artifact_run')
        if not run_id:raise RuntimeError('No saved daily review exists for publication recovery')
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN']}
        r=requests.get(f'https://api.github.com/repos/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{run_id}/artifacts',headers=headers,timeout=30)
        r.raise_for_status();items=[a for a in r.json()['artifacts'] if a['name']==f'english-review-{run_id}' and not a['expired']]
        if len(items)!=1:raise RuntimeError('Exact daily artifact is unavailable')
        manifest=get_artifact(items[0]['id'],output,record.get('sha256'))
    candidate=manifest['candidate'];bed=review.licensed_music(output,candidate)
    clean=output/'clean-dj-review.mp4'
    audio.validate_media(clean,candidate);audio.validate_recording(clean,candidate);visuals.validate_publish(candidate)
    target=output/'oldies-english-licensed-master.mp4'
    review.mix_music(clean,bed,target,manifest['clean_qc']['video_duration_seconds'])
    caption=candidate['dj_script_en']+'\n\n'+candidate['music_credit']+'\nMusic source: '+candidate['music_license']['source']
    for source in candidate.get('sources',[]):caption+='\nEvent source: '+source
    for p in candidate['image_credits']:caption+='\nPhoto: '+p['creator']+' — '+p['license']+' — '+p['source']
    (output/'caption.txt').write_text(caption)
    manifest.update(sha256=review.digest(target),bytes=target.stat().st_size,music=candidate['music_license'],music_credit=candidate['music_credit'],
                    candidate=candidate,production_day=day,reused_approved_source=True,new_provider_calls=0,
                    publication_policy=POLICY['id'],mixed_audio_qc=audio.inspect_audio(target))
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Recovered accepted review, remixed event-era music; provider calls=0')
    return manifest


def verify_final(output,manifest):
    require_policy();candidate=manifest['candidate'];video=output/'oldies-english-licensed-master.mp4'
    if review.digest(video)!=manifest['sha256']:raise RuntimeError('Final MP4 hash mismatch')
    audio.validate_media(output/'clean-dj-review.mp4',candidate)
    audio.validate_recording(output/'clean-dj-review.mp4',candidate);visuals.validate_publish(candidate)
    track,credit=review.era_music(dict(candidate))
    if manifest['music']['sha256']!=track['sha256'] or credit not in (output/'caption.txt').read_text():
        raise RuntimeError('Event-era licensed instrumental or its required credit does not match')
    qc=audio.inspect_audio(video)
    stream=next(s for s in qc['streams'] if s.get('codec_type')=='video')
    duration=float(stream['duration'])
    if not POLICY['min_seconds']<=duration<=POLICY['max_seconds'] or (int(stream['width']),int(stream['height']))!=(1080,1920):
        raise RuntimeError('Final duration or format violates permanent policy')
    return candidate,video


def classify(result):
    payload=result.get('data',result)
    if not isinstance(payload,dict):return {'state':'unverified','publication_verified':False}
    vid=str(payload.get('video_id') or payload.get('post_id') or '')
    status=payload.get('status') if isinstance(payload.get('status'),dict) else {}
    phase=status.get('publishing_phase') or {}
    phase=phase.get('status','') if isinstance(phase,dict) else str(phase)
    ready=str(status.get('video_status','')).lower() in {'ready','published'}
    dry=payload.get('dry_run') is True or payload.get('simulated') is True
    verified=(bool(re.fullmatch(r'[0-9_]+',vid)) and not dry and result.get('success') is not False
              and payload.get('success') is not False and ready
              and (payload.get('published') is True or str(phase).lower() in {'complete','completed','published'}))
    return {'state':'published' if verified else ('dry_run' if dry else 'uploaded_unverified'),'video_id':vid,
        'publication_verified':verified,'permalink':payload.get('permalink_url') or payload.get('permalink') or (f'https://www.facebook.com/reel/{vid}' if verified else '')}


def publish(output,ledger,day):
    require_policy();record=ledger.data.get('days',{}).get(day)
    if not record:raise RuntimeError('Daily render ledger entry is missing')
    prior=record.get('facebook',{})
    if prior.get('publication_verified'):
        (output/'facebook-publication.json').write_text(json.dumps(dict(prior,duplicate_blocked=True),indent=2))
        print('Facebook daily publication already verified; no upload');return
    manifest=json.loads((output/'manifest.json').read_text()) if (output/'manifest.json').exists() else prepare_existing(output,ledger,day)
    candidate,video=verify_final(output,manifest)
    content_id='oldies-news-'+review.event_key(candidate)[:48]
    if prior.get('content_id') and prior['content_id']!=content_id:raise RuntimeError('Pending publication content binding changed')
    public_url=prior.get('delivery_url')
    if public_url and prior.get('sha256')!=manifest['sha256']:raise RuntimeError('Pending publication source bytes changed')
    if not public_url:public_url=publish_delivery_asset(candidate,video)
    if not public_url:raise RuntimeError('Delivery asset URL unavailable')
    request={'content_id':content_id,'video_url':public_url,'sha256':manifest['sha256'],
        'caption':(output/'caption.txt').read_text()+'\n\nMore music history: oldiesradyo.com/en/',
        'title':str(candidate.get('event_headline') or candidate['artist'])[:120],'dry_run':False,'policy_id':POLICY['id']}
    binding={'state':'publication_requested','publication_verified':False,'content_id':content_id,'sha256':manifest['sha256'],'delivery_url':public_url,'run_id':os.environ.get('GITHUB_RUN_ID')}
    record['facebook']=binding;ledger.data['events'][record['event']]['facebook']=binding;ledger.save()
    bearer=os.environ['OLDIES_WP_BEARER'];base=os.getenv('OLDIES_WP_BASE_URL') or POLICY['wordpress_site']
    if base.rstrip('/')!=POLICY['wordpress_site'].rstrip('/'):raise RuntimeError('Unexpected WordPress publication destination')
    response=requests.post(base.rstrip('/')+'/wp-json/oldies-global/v1/publish-url',headers={'Authorization':'Bearer '+bearer,'X-Oldies-Reels-Secret':bearer},json=request,timeout=240)
    response.raise_for_status();result=response.json();out=dict(binding,**classify(result),remote_response=result)
    (output/'facebook-publication.json').write_text(json.dumps(out,indent=2))
    record['facebook']=out;ledger.data['events'][record['event']]['facebook']=out;ledger.save()
    print(json.dumps({k:out.get(k) for k in ['state','video_id','permalink','publication_verified']}))
    if not out['publication_verified']:raise RuntimeError('Facebook upload was not verified as completed publication; keep receipt for bounded follow-up')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-existing',action='store_true');args=parser.parse_args()
    output=ROOT/'english-output';output.mkdir(exist_ok=True);day=datetime.now(ZoneInfo('Europe/Istanbul')).date().isoformat();ledger=review.Ledger()
    if args.prepare_existing:prepare_existing(output,ledger,day)
    else:publish(output,ledger,day)
if __name__=='__main__':main()
