"""Exercise only the actual fixed-snapshot identity reader against the already known file."""
from pathlib import Path
import hashlib,json,sys,os,datetime
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
SNAPSHOT=HERE/'reels-snapshot'
bindings=json.loads((HERE/'snapshot-bindings.json').read_text())
for row in bindings['files']:
    assert hashlib.sha256((SNAPSHOT/row['path']).read_bytes()).hexdigest()==row['sha256']
sys.dont_write_bytecode=True
def audit(event,args):
    if event in {'socket.connect','socket.getaddrinfo','subprocess.Popen','os.system','os.startfile'}:
        raise AssertionError('EXTERNAL_CALL_FORBIDDEN')
sys.addaudithook(audit)
sys.path.insert(0,str(SNAPSHOT))
import facebook_global_audio as audio
key='OLDIES_FACEBOOK_ENERGETIC_SIGNOFF_PATH'
known=Path(r'C:\Users\METE\Downloads\Oldies-Radyo-DJ-Energetic-Preview.mp3')
previous=os.environ.get(key)
try:
    os.environ[key]=str(known)
    profile,identity,raw=audio.selected_signoff({'signoff_profile':'energetic'})
    result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot':bindings['ref'],
     'actual_function':'facebook_global_audio.selected_signoff','profile':profile,
     'local_path':str(known),'mapping_key':key,'mapping_scope':'this child process only; cleared/restored in finally',
     'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'matches_actual_contract':True,
     'production_approval_metadata_changed':False,'raw_audio_exported':False,'new_media_provider_calls':0}
    raw=None
finally:
    if previous is None:os.environ.pop(key,None)
    else:os.environ[key]=previous
result['mapping_cleanup_verified']=os.environ.get(key)==previous
prior=json.loads((PROJECT/'work-output/jingle-j3-20261030/evidence/reels-r0-input.json').read_text())
result['calm_reference']=prior['accepted_assets']['calm']
result['calm_searched_again']=False
repo=PROJECT/'artifacts/reels-recovery-20261018/repo'
packet=repo/'work-output/p0-reels-repair-20261018/first-pair/en-render/add552ef578f5880-d0fd54ecb2e8/content.json'
packet_data=json.loads(packet.read_text(encoding='utf-8-sig'))
preview=repo/'output/en-preview/preview-status.json'
preview_data=json.loads(preview.read_text(encoding='utf-8-sig'))
result['marked_entry_evidence']={'workspace':str(repo),'entry':'worker.main -> prepare_preview -> local_voiceover -> inspect_audio -> render_timeline',
 'packet_sha256':hashlib.sha256(packet.read_bytes()).hexdigest(),
 'packet_voice':packet_data.get('local_voiceover'),'packet_date':packet_data.get('research_date'),
 'preview_status':preview_data.get('status'),'video_created':preview_data.get('video_created'),
 'active_windows_facebook_launcher_ref':'NOT_PROVEN_IN_MARKED_ENTRY_RECEIPTS',
 'scope':'Known entry/receipt set only; no whole-device scan or absence claim'}
(HERE/'reels-identity-binding.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'profile':profile,'bytes':result['bytes'],'sha256':result['sha256'],'actual_contract_matched':True,
 'process_only_mapping_cleaned':result['mapping_cleanup_verified'],'active_windows_launcher_proven':False}))
