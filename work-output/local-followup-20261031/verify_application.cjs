'use strict';
// Runs only existing candidate verification/plan paths with read-only filesystem views.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const plan=JSON.parse(fs.readFileSync(path.join(__dirname,'application-plan.json')));
const root=path.dirname(plan.manifest.target),producer=path.join(root,'producer');
const originals=JSON.parse(fs.readFileSync(path.join(__dirname,'protected-preimage.private.json')));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const fingerprint=p=>!fs.existsSync(p)?'MISSING':fs.statSync(p).isFile()?sha(fs.readFileSync(p)):'DIRECTORY_PRESENT';
for(const [p,h] of Object.entries(originals))assert.equal(fingerprint(p),h);
const moduleSource=fs.readFileSync(path.join(producer,'candidate.cjs'),'utf8');
const baselineManifest=fs.readFileSync(plan.manifest.target);
const nextManifest=fs.readFileSync(plan.manifest.prepared_file);
const nextAdapter=fs.readFileSync(plan.adapter.existing_candidate);
assert.equal(sha(baselineManifest),plan.manifest.preimage_sha256);
assert.equal(sha(nextManifest),plan.manifest.postimage_sha256);
assert.equal(sha(nextAdapter),plan.adapter.postimage_sha256);
const rows=[];
async function check(name,{manifest=baselineManifest,adapter,error}={}){
 const touched=[];
 const readonly={readFileSync:(file,encoding)=>{
  const p=path.resolve(file);touched.push(p);
  const value=p===path.resolve(plan.manifest.target)?manifest:
   adapter&&p===path.resolve(plan.target)?adapter:fs.readFileSync(p);
  return encoding?value.toString(encoding):value;
 }};
 const module={exports:{}};
 const localRequire=name=>name==='node:fs'?readonly:name==='node:path'?path:name==='node:crypto'?crypto:
  name==='node:child_process'?{spawnSync:()=>{throw Error('EXTERNAL_PROCESS_FORBIDDEN');}}:(()=>{throw Error('UNREVIEWED_DEPENDENCY');})();
 vm.runInNewContext(moduleSource,{require:localRequire,module,__dirname:producer},{filename:'actual-candidate.cjs'});
 if(error)assert.throws(()=>module.exports.verify(),new RegExp(error));
 else{
  module.exports.verify();
  const result=await module.exports.main(['morning']);
  assert.equal(result.status,'CANDIDATE_PLAN_ONLY');assert.equal(result.provider_calls,0);assert.equal(result.live_success,false);
 }
 rows.push({name,result:'PASS',expectedError:error||null,actualCandidateVerify:true,readonly:true,externalProcessCalls:0});
}
(async()=>{
 await check('current-installed-pair');
 await check('adapter-only-with-stale-manifest',{adapter:nextAdapter,error:'CANDIDATE_HASH_MISMATCH'});
 await check('manifest-only-with-old-adapter',{manifest:nextManifest,error:'CANDIDATE_HASH_MISMATCH'});
 await check('reviewed-postimage-pair',{manifest:nextManifest,adapter:nextAdapter});
 await check('tampered-candidate',{manifest:nextManifest,adapter:Buffer.concat([nextAdapter,Buffer.from('//tampered')]),error:'CANDIDATE_HASH_MISMATCH'});
 const backup=plan.rollback.backup_directory;
 await check('exact-rollback-pair',{manifest:fs.readFileSync(path.join(backup,'SHA256-MANIFEST.json')),adapter:fs.readFileSync(path.join(backup,'gemini_jingle.staged.cjs'))});
 for(const [p,h] of Object.entries(originals))assert.equal(fingerprint(p),h,'protected postimage changed');
 const result={at:new Date().toISOString(),status:'PASS_READ_ONLY_APPLICATION_BINDING',cases:rows,
  protectedPrePostUnchanged:true,installed:false,realProviderDownloadImportMixCalls:0,
  fullPriorJ3NineCasesRerun:false,manifestPreimageSha256:plan.manifest.preimage_sha256,manifestPostimageSha256:plan.manifest.postimage_sha256};
 fs.writeFileSync(path.join(__dirname,'application-verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
