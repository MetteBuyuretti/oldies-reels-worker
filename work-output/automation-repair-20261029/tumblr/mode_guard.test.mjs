import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import vm from 'node:vm';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const here=path.dirname(fileURLToPath(import.meta.url));
const evidence=path.resolve(here,'../../local-repair-20261026');
const budget=fs.readFileSync(path.join(evidence,'budget-excerpt.mjs'),'utf8').replace(/\r\n/g,'\n');
const flow=fs.readFileSync(path.join(evidence,'verify-flow.txt'),'utf8').replace(/\r\n/g,'\n');
// These are approved source excerpts, not a complete installed Windows publisher.
const original=budget+'\n'+flow;
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),'oldies-mode-'));
const source=path.join(tmp,'source.mjs'),candidate=path.join(tmp,'candidate.mjs');
fs.writeFileSync(source,original);
const run=(src,out,hash)=>spawnSync('python3',[path.join(here,'build_candidate.py'),
 '--source',src,'--output',out,'--expected-sha256',hash],{encoding:'utf8'});
const built=run(source,candidate,sha(original));
assert.equal(built.status,0,built.stderr);
const patched=fs.readFileSync(candidate,'utf8');
function context(text,args){
 const effects=[];
 const sandbox={process:{argv:['node','publisher',...args]},ROOT:'unused',PACKAGE:'unused',
  path,crypto,URL,structuredClone,console:{log:()=>effects.push('console')},
  fs:new Proxy({}, {get:(_,name)=>()=>{effects.push(String(name));throw Error('FIRST_EFFECT_SENTINEL');}})};
 const ctx=vm.createContext(sandbox);
 // Remove module syntax only; execute the actual supplied main and shouldSubmit bodies.
 vm.runInContext(text.replace(/^import .*;\n/gm,'').replace(/^export /gm,''),ctx);
 return {ctx,effects};
}
for(const args of [['--verify','--queue-ready'],['--queue-ready','--verify']]){
 test('baseline reproduces unsafe submission for '+args.join(' '),()=>{
  const {ctx}=context(original,args);
  vm.runInContext('eligible=()=>true',ctx);
  assert.equal(vm.runInContext('shouldSubmit(process.argv.slice(2),{},{},{})',ctx),true);
 });
 test('patched main rejects before any effect for '+args.join(' '),async()=>{
  const {ctx,effects}=context(patched,args);
  await assert.rejects(vm.runInContext('main()',ctx),/CONFLICTING_PUBLISHER_MODES/);
  assert.deepEqual(effects,[]);
 });
 test('patched submission rejects before eligibility for '+args.join(' '),()=>{
  const {ctx}=context(patched,args);
  vm.runInContext("eligible=()=>{throw Error('ELIGIBILITY_MUST_NOT_RUN')}",ctx);
  assert.throws(()=>vm.runInContext('shouldSubmit(process.argv.slice(2),{},{},{})',ctx),/CONFLICTING_PUBLISHER_MODES/);
 });
}
for(const args of [[],['--verify'],['--queue-ready']]){
 test('single/legacy mode retains entry for '+JSON.stringify(args),async()=>{
  const {ctx,effects}=context(patched,args);
  await assert.rejects(vm.runInContext('main()',ctx),/FIRST_EFFECT_SENTINEL/);
  assert.deepEqual(effects,['mkdirSync']);
 });
}
test('Verify never calls eligibility',()=>{
 const {ctx}=context(patched,['--verify']);
 vm.runInContext("eligible=()=>{throw Error('ELIGIBILITY_MUST_NOT_RUN')}",ctx);
 assert.equal(vm.runInContext('shouldSubmit(process.argv.slice(2),{},{},{})',ctx),false);
});
test('queue still requires existing authorization',()=>{
 const {ctx}=context(patched,['--queue-ready']);
 assert.throws(()=>vm.runInContext('shouldSubmit(process.argv.slice(2),{id:"x"},{},{})',ctx),/QC_OR_SCOPED_AUTHORIZATION_REQUIRED/);
});
test('queue still evaluates eligibility result',()=>{
 const {ctx}=context(patched,['--queue-ready']);
 vm.runInContext('eligible=()=>false',ctx);
 assert.equal(vm.runInContext('shouldSubmit(process.argv.slice(2),{},{},{})',ctx),false);
 vm.runInContext('eligible=()=>true',ctx);
 assert.equal(vm.runInContext('shouldSubmit(process.argv.slice(2),{},{},{})',ctx),true);
});
test('existing daily budget and target-time gates remain closed',()=>{
 const {ctx}=context(patched,[]);
 assert.throws(()=>vm.runInContext('dailyAdmission({allPathsCovered:false},{items:[]},"2026-10-29T11:00:00Z","2026-10-30T11:00:00Z")',ctx),/DAILY_PUBLICATION_BUDGET_UNVERIFIED/);
 assert.throws(()=>vm.runInContext('submissionBudget({},{},{},{})',ctx),/TARGET_PUBLICATION_TIME_UNVERIFIED/);
});
test('builder preserves source and refuses overwrite, same-path and wrong hash',()=>{
 assert.equal(fs.readFileSync(source,'utf8'),original);
 assert.match(run(source,candidate,sha(original)).stderr,/OUTPUT_ALREADY_EXISTS/);
 assert.match(run(source,source,sha(original)).stderr,/IN_PLACE_WRITE_FORBIDDEN/);
 assert.match(run(source,path.join(tmp,'wrong.mjs'),'0'.repeat(64)).stderr,/PREIMAGE_SHA256_MISMATCH/);
 assert.equal(fs.existsSync(path.join(tmp,'wrong.mjs')),false);
});
test('changed entry fails closed without candidate',()=>{
 const changed=path.join(tmp,'changed.mjs'),out=path.join(tmp,'changed-out.mjs');
 const text=original.replace('async function main(){','async function main() {');
 fs.writeFileSync(changed,text);
 assert.match(run(changed,out,sha(text)).stderr,/SOURCE_ANCHOR_MISMATCH/);
 assert.equal(fs.existsSync(out),false);
});
test('CRLF is preserved and staging candidate parses as JavaScript',()=>{
 const crlf=path.join(tmp,'crlf.mjs'),out=path.join(tmp,'crlf-out.mjs');
 const text=original.replace(/\n/g,'\r\n');fs.writeFileSync(crlf,text);
 assert.equal(run(crlf,out,sha(text)).status,0);
 const result=fs.readFileSync(out,'utf8');assert.equal(result.replace(/\r\n/g,'').includes('\n'),false);
 const check=spawnSync(process.execPath,['--check',out],{encoding:'utf8'});
 assert.equal(check.status,0,check.stderr);
});
test.after(()=>fs.rmSync(tmp,{recursive:true,force:true}));
