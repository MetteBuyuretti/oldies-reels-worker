"""Known files only; no discovery, synthesis, playback, rendering or publication."""
from pathlib import Path
import hashlib,json,subprocess,datetime
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((PROJECT/'work-output/local-exec-20261029/reels-r0-local-identity.private.json').read_text())
repos=[Path(x['workspace']) for x in prior['workspaces']]
files=['worker.py','reels_preview.py','video_factory.py','media_evidence.py','source_evidence.py','editorial_quality_gate.py']
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'workspaces':[]}
for i,repo in enumerate(repos,1):
    entry={'alias':f'LOCAL_REELS_{i}','path':str(repo),'files':{f:sha(repo/f) if (repo/f).is_file() else None for f in files}}
    if (repo/'.git').exists():
        r=subprocess.run(['git','-C',str(repo),'rev-parse','--show-toplevel','HEAD'],capture_output=True,text=True,timeout=10)
        lines=r.stdout.splitlines()
        entry['git_head']=lines[1] if r.returncode==0 and len(lines)==2 and Path(lines[0]).resolve()==repo.resolve() else 'NOT_BOUND_TO_THIS_ROOT'
        entry['git_head_is_full_worktree_identity']=False
    else:entry['git_head']='NO_GIT_METADATA'
    result['workspaces'].append(entry)
expected={'calm':'1dc358ef0cea5a3a6d9fe20d9934358fed5ccd0009ba0838a60bba9f28bb9d9c',
          'energetic':'a2df71619290530249fbacbc02c546caceeecaf3c05d265bd8321ebfeefb4ac8'}
calm_paths=[r/'assets/facebook/en-warm-signoff-radyo-v3.mp3' for r in repos]
calm_paths += [Path.home()/'Downloads/en-warm-signoff-radyo-v3.mp3']
energetic=Path.home()/'Downloads/Oldies-Radyo-DJ-Energetic-Preview.mp3'
result['accepted_assets']={
 'calm':{'expected_sha256':expected['calm'],'checked_paths':[str(p) for p in calm_paths],
         'local_matches':[str(p) for p in calm_paths if p.is_file() and sha(p)==expected['calm']],
         'original_source':'PR22/9ad08776/assets/facebook/en-warm-signoff-radyo-v3.mp3'},
 'energetic':{'expected_sha256':expected['energetic'],'path':str(energetic),
              'actual_sha256':sha(energetic) if energetic.is_file() else None,
              'bytes':energetic.stat().st_size if energetic.is_file() else None,
              'matches_accepted_bytes':energetic.is_file() and sha(energetic)==expected['energetic']}}
content=repos[0]/'work-output/p0-reels-repair-20261018/first-pair/en-render/add552ef578f5880-d0fd54ecb2e8/content.json'
packet=json.loads(content.read_text(encoding='utf-8-sig'))
result['last_marked_english_packet']={'date':packet.get('research_date'),'language':packet.get('reels_language'),
 'local_voiceover':packet.get('local_voiceover'),'file_sha256':sha(content)}
result['entry']={'source_entry':'LOCAL_REELS_1/worker.py main -> prepare_preview -> packet.local_voiceover -> inspect_audio -> render_preview -> render_timeline',
 'active_windows_facebook_launcher_ref':'NOT_EVIDENCED_IN_MARKED_ENTRY_OR_RECEIPTS',
 'accepted_signoff_profile_bound_in_this_consumer':False,
 'scope':'Known workspaces and marked prior receipts only; not a whole-device absence claim',
 'new_tts_audio_video_render_publish_calls':0}
(HERE/'evidence/reels-r0-input.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
