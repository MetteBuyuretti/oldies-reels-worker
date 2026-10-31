"""Read installed files; create only workspace application/rollback material. Never apply."""
from pathlib import Path
import hashlib,json,datetime
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
FACTORY=Path(r'C:\Users\METE\Oldies-Jingle-Factory')
STAGE=FACTORY/'backups/WORK2-20261015-STATE-QC-RECOVERY/FINAL-LIVE-ADAPTER-20261018'
SOURCE='d02e9d551dc1513e2e4312d5b904059c9237cc242f6f6c9b5ec37fd588434817'
CANDIDATE='f8534ee39676984db0260e991dc849e805f83efde517528f9f09e83f5e08fc01'
sha=lambda b:hashlib.sha256(b).hexdigest()
def keep(path,data):
    if path.exists():assert path.read_bytes()==data,'EXISTING_WORKSPACE_MATERIAL_CHANGED'
    else:
        with path.open('xb') as f:f.write(data)
target=STAGE/'producer/gemini_jingle.staged.cjs'
candidate=PROJECT/'work-output/jingle-j3-20261030/candidate/gemini_jingle.staged.cjs'
assert sha(target.read_bytes())==SOURCE,'SOURCE_PREIMAGE_CHANGED'
assert sha(candidate.read_bytes())==CANDIDATE,'CANDIDATE_CHANGED'
manifest=STAGE/'SHA256-MANIFEST.json'
original=manifest.read_bytes()
m=json.loads(original.decode('utf-8-sig'))
assert m['files']['producer/gemini_jingle.staged.cjs']==SOURCE
checks=[]
for group in ['files','live_preimages']:
    for name,want in m[group].items():
        p=STAGE/name if group=='files' else Path(name)
        assert p.is_file() and sha(p.read_bytes())==want,'MANIFEST_DEPENDENCY_PREIMAGE_CHANGED'
        checks.append({'group':group,'name':name if group=='files' else p.name,'matches':True})
assert original.count(SOURCE.encode())==1
post=original.replace(SOURCE.encode(),CANDIDATE.encode(),1)
parsed=json.loads(post.decode('utf-8-sig'))
expected=json.loads(original.decode('utf-8-sig'))
expected['files']['producer/gemini_jingle.staged.cjs']=CANDIDATE
assert parsed==expected
backup=HERE/'rollback.private';backup.mkdir(exist_ok=True)
keep(backup/'gemini_jingle.staged.cjs',target.read_bytes())
keep(backup/'SHA256-MANIFEST.json',original)
keep(HERE/'candidate-manifest.private.json',post)
activation=json.loads((STAGE/'config/activation.json').read_text(encoding='utf-8-sig'))
protected=[FACTORY/'config/production-state.json',FACTORY/'logs/heartbeat.json',
 FACTORY/'config/settings.json',FACTORY/'config/approved-jingle-standard-v3.1.json',
 FACTORY/'references/OldiesRadyo-V3.1-APPROVED-SOUND-REFERENCE.mp3',FACTORY/'config/run.lock',FACTORY/'logs/run.lock',
 STAGE/'runtime/browser-operation.lock',STAGE/'runtime/producer/operation-claims/2026-10-18-morning.json',
 STAGE/'config/activation.json',target,manifest]
protected += [STAGE/n for n in m['files']]
fingerprint=lambda p:sha(p.read_bytes()) if p.is_file() else 'DIRECTORY_PRESENT' if p.is_dir() else 'MISSING'
keep(HERE/'protected-preimage.private.json',json.dumps({str(p):fingerprint(p) for p in protected},sort_keys=True,indent=2).encode())
plan={'task_id':'LOCAL-J3-APPLICATION-PREP-20261031-01','status':'PREPARED_NOT_APPLIED',
 'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'target':str(target),
 'adapter':{'preimage_sha256':SOURCE,'postimage_sha256':CANDIDATE,'existing_candidate':str(candidate),'regenerated':False},
 'manifest':{'target':str(manifest),'preimage_sha256':sha(original),'postimage_sha256':sha(post),
  'single_field':'files.producer/gemini_jingle.staged.cjs','replacement':{'from':SOURCE,'to':CANDIDATE},
  'prepared_file':str(HERE/'candidate-manifest.private.json'),'other_entries_unchanged':True},
 'consumption':[
  'STAGE/RUN-MORNING.cmd or RUN-EVENING.cmd -> node producer/candidate.cjs <slot>',
  'candidate.main -> verify() reads SHA256-MANIFEST.json files + live_preimages before activation',
  'candidate --execute only after dated activation + live_guard + browser lock; createUiAdapter from target',
  'wrapper waitForTrack/download -> actual UI adapter -> produce -> prepareForHumanReview -> import_web_music -> awaiting-human-review',
  'factory_handoff.py is a separate explicit receipt/independent human/activation/Factory gate; not browser launcher'],
 'legacy_entry':{'path':str(FACTORY/'RUN-EVENING.cmd'),'chain':'scripts/Run-Factory.ps1 -> .venv Python src/jingle_factory.py',
  'consumes_j3_adapter':False,'changed':False},
 'activation_readonly':{k:activation.get(k) for k in ['date','daily_automation_authorized','daily_authorization_start','daily_authorization_end','factory_provider_calls_authorized']},
 'manifest_checks':checks,'all_preimages_match':True,
 'rollback':{'backup_directory':str(backup),'adapter_backup_sha256':sha((backup/'gemini_jingle.staged.cjs').read_bytes()),
  'manifest_backup_sha256':sha((backup/'SHA256-MANIFEST.json').read_bytes()),
  'rule':'Restore only the exact two reviewed files after verifying current hashes are the package postimages; reject drift. Never restore state/claim/activation/locks.',
  'future_apply_order':'Under exclusive maintenance/quiescence: recheck all pins; adapter then manifest; fail closed in between; verify complete pair. This preparation performs no writes to target.',
  'future_rollback_order':'Under same maintenance/quiescence: restore manifest then adapter from verified backups; fail closed in between; verify original pair.'},
 'installed':False,'provider_download_import_factory_mix_scheduler_calls':0}
(HERE/'application-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':plan['status'],'adapter_preimage':SOURCE,'adapter_postimage':CANDIDATE,
 'manifest_preimage':sha(original),'manifest_postimage':sha(post),'pins_verified':len(checks),'candidate_regenerated':False}))
