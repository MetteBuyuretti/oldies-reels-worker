from pathlib import Path
import json,hashlib,shutil,subprocess
HERE=Path(__file__).resolve().parent;PROJECT=HERE.parents[1]
old='3dd7b0988c091526ce59bc73a155bbc37ea9dacb553f49cfb132e0d729e5c38a';new='9e44f9af845c889c0079ba5cc956ea0e5be08b825050cb9aea6fa5670032c622'
source=Path(r'C:\Users\METE\oldies-jingle-automation\tumblr_auto_news_v3.mjs');candidate=PROJECT/'work-output/canonical-tumblr-20261031/candidate/tumblr_auto_news_v3.mjs'
policy=PROJECT/'work-output/local-exec-20261029/commander/policy.candidate.private.json';plan=PROJECT/'work-output/commander-activation-20261030/activation-plan.private.json';pins=PROJECT/'work-output/commander-activation-20261030/secure-launcher-pins.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(source.read_bytes())==old and sha(candidate.read_bytes())==new
pb=policy.read_bytes();pl=plan.read_bytes();sp=pins.read_bytes();p=json.loads(pb.decode('utf-8-sig'));a=json.loads(pl.decode('utf-8-sig'));sec=json.loads(sp.decode('utf-8-sig'))
assert pb.count(old.encode())==1 and p['project']['sources']['TUMBLR_PUBLISHER']['sha256']==old
assert a['candidate_policy_sha256']==sha(pb) and pl.count(sha(pb).encode())==1
assert sum(1 for f in sec['files'] if Path(f['path'])==plan and f['sha256']==sha(pl))==1 and sp.count(sha(pl).encode())==1
pb1=pb.replace(old.encode(),new.encode());pl1=pl.replace(sha(pb).encode(),sha(pb1).encode());sp1=sp.replace(sha(pl).encode(),sha(pl1).encode())
priv=HERE/'tumblr-pins.private';priv.mkdir(exist_ok=True)
for name,blob in [('publisher.old',source.read_bytes()),('policy.old',pb),('policy.new',pb1),('plan.old',pl),('plan.new',pl1),('pins.old',sp),('pins.new',sp1)]:
 f=priv/name
 if f.exists():assert f.read_bytes()==blob,'FIXTURE_PREIMAGE_CHANGED'
 else:f.write_bytes(blob)
# Reproduce actual projectTools.source against a private isolated copy of all three pinned sources.
fixture=HERE/'commander-TEST';fixture.mkdir(exist_ok=True);sourcedir=fixture/'sources';sourcedir.mkdir(exist_ok=True)
project=p['project'];mapped={}
for alias,entry in project['sources'].items():
 target=sourcedir/Path(entry['path']).name
 shutil.copyfile(candidate if alias=='TUMBLR_PUBLISHER' else entry['path'],target)
 mapped[alias]={'path':str(target.resolve()),'sha256':new if alias=='TUMBLR_PUBLISHER' else entry['sha256']}
safe={'sourceRoot':str(sourcedir.resolve()),'sources':mapped};(fixture/'policy.json').write_text(json.dumps(safe),encoding='utf-8')
module=PROJECT/'work-output/local-exec-20261029/commander/project-tools.cjs'
code="const t=require(process.argv[1]),p=JSON.parse(require('fs').readFileSync(process.argv[2])); for(const a of Object.keys(p.sources))t.source(p,a);"
r=subprocess.run(['node','-e',code,str(module),str(fixture/'policy.json')],capture_output=True,text=True,timeout=15);assert r.returncode==0,r.stderr
out={'source_old':old,'source_new':new,'policy_old':sha(pb),'policy_new':sha(pb1),'activation_plan_old':sha(pl),'activation_plan_new':sha(pl1),'secure_pins_old':sha(sp),'secure_pins_new':sha(sp1),'source_policy_fixture':'PASS','policy_hash_pin_chain':'PASS','runtime_restart':False}
(HERE/'tumblr-pin-evidence.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
