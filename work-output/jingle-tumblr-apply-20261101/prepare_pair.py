from pathlib import Path
import hashlib,json,shutil,subprocess
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
STAGE=Path(r'C:\Users\METE\Oldies-Jingle-Factory\backups\WORK2-20261015-STATE-QC-RECOVERY\FINAL-LIVE-ADAPTER-20261018')
LAUNCH=Path(r'C:\Users\METE\Oldies-Jingle-Factory\scripts\Run-Factory.ps1')
CAND=PROJECT/'work-output/canonical-handoff-20261031/candidate/Run-Factory.ps1'
OLD='1300e811e001719fbe1d2b6fa581bd2f7b1f1297ea457117d2a51fe30973934d';NEW='21a6c0ea568a3fad76e7e33a843204f41eb7054d28cdca9a3fa7b8d84b5cc2f4'
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=STAGE/'SHA256-MANIFEST.json'; raw=manifest.read_bytes(); data=json.loads(raw.decode('utf-8-sig'))
assert sha(LAUNCH.read_bytes())==OLD and sha(CAND.read_bytes())==NEW
assert data['live_preimages'][str(LAUNCH)]==OLD and raw.count(OLD.encode())==1
for n,d in data['files'].items():assert sha((STAGE/n).read_bytes())==d,n
for n,d in data['live_preimages'].items():assert sha(Path(n).read_bytes())==d,Path(n).name
post=raw.replace(OLD.encode(),NEW.encode());newdata=json.loads(post.decode('utf-8-sig'));test=json.loads(raw.decode('utf-8-sig'));test['live_preimages'][str(LAUNCH)]=NEW;assert test==newdata
private=HERE/'pair.private';private.mkdir(parents=True,exist_ok=True)
(private/'launcher.original.ps1').write_bytes(LAUNCH.read_bytes());(private/'manifest.original.json').write_bytes(raw);(private/'manifest.candidate.json').write_bytes(post)
fixture=HERE/'pair-TEST'; fixture.mkdir(exist_ok=True); mapped={}
for n in data['files']:
 p=fixture/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(STAGE/n,p)
for i,(n,d) in enumerate(data['live_preimages'].items()):
 p=fixture/'originals'/f'{i}.bin';p.parent.mkdir(exist_ok=True);shutil.copyfile(n,p);mapped[n]=str(p.resolve())
original={**data,'live_preimages':{mapped[k]:v for k,v in data['live_preimages'].items()}}
fixturemanifest=fixture/'SHA256-MANIFEST.json';fixturemanifest.write_text(json.dumps(original),encoding='utf-8')
def verify():
 r=subprocess.run(['node','-e',"require('./producer/candidate.cjs').verify()"],cwd=fixture,capture_output=True,text=True,timeout=20);return r.returncode
assert verify()==0
target=Path(mapped[str(LAUNCH)]); target.write_bytes(CAND.read_bytes())
assert verify()!=0
updated=json.loads(json.dumps(original));updated['live_preimages'][str(target)]=NEW
fixturemanifest.write_text(json.dumps(updated),encoding='utf-8');assert verify()==0
# Inject failure in second step: restore both fixture preimages, then execute real verify.
target.write_bytes((private/'launcher.original.ps1').read_bytes());fixturemanifest.write_text(json.dumps(original),encoding='utf-8');assert verify()==0
try:
 target.write_bytes(CAND.read_bytes());assert verify()!=0
 raise OSError('INJECTED_MANIFEST_WRITE_FAILURE')
except OSError:
 target.write_bytes((private/'launcher.original.ps1').read_bytes());fixturemanifest.write_text(json.dumps(original),encoding='utf-8')
assert verify()==0 and sha(target.read_bytes())==OLD and json.loads(fixturemanifest.read_text())==original
result={'status':'PASS','original_manifest_sha256':sha(raw),'candidate_manifest_sha256':sha(post),'launcher_old':OLD,'launcher_new':NEW,'baseline_pair':'PASS','mixed_pair':'REJECT','updated_pair':'PASS','injected_second_step_failure_rollback_pair':'PASS','all_other_pins_unchanged':True,'fixture_only':True}
(HERE/'pair-evidence.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
