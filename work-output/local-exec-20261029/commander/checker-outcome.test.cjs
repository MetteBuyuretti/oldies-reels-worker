'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {callProject,syntaxOutcome}=require('./project-tools.cjs');

for(const [file,binary] of [['tumblr_auto_news_v3.mjs','node'],['run_tumblr_auto.ps1','powershell']]){
 test('missing '+binary+' is a checker failure, not a source syntax diagnosis',async()=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'oldies-checker-'));
  try{
   fs.writeFileSync(path.join(root,file),file.endsWith('.mjs')?'const valid = true;':'$valid = $true');
   const policy={stagingRoot:root,node:process.execPath,powershell:'unused',syntaxHelper:'unused'};
   policy[binary]=path.join(root,'missing-checker');
   const result=JSON.parse((await callProject('check_staging_syntax',{file},policy,null)).content[0].text);
   assert.equal(result.status,'CHECK_UNAVAILABLE');
   assert.equal(result.checkerErrorCode,'ENOENT');
   assert.equal(result.exitCode,null);
   assert.equal(result.executedCandidate,false);
   assert(!JSON.stringify(result).includes(root));
  }finally{fs.rmSync(root,{recursive:true,force:true});}
 });
}
test('timeout cannot be reported as completed syntax validation',()=>{
 assert.deepEqual(syntaxOutcome({error:{code:'ETIMEDOUT'},status:null,signal:'SIGTERM'}),
  {status:'CHECK_TIMEOUT',checkerErrorCode:'ETIMEDOUT'});
});
test('interrupted or missing exit cannot pass syntax validation',()=>{
 for(const result of [{status:null,signal:'SIGTERM'},{status:null,signal:null},{status:0,signal:'SIGTERM'}])
  assert.equal(syntaxOutcome(result).status,'CHECK_INTERRUPTED');
});
test('successful completed parser and real parser rejection remain distinct',()=>{
 assert.equal(syntaxOutcome({status:0,signal:null}).status,'SYNTAX_OK');
 assert.equal(syntaxOutcome({status:1,signal:null}).status,'SYNTAX_ERROR');
});
test('unknown launch error details are not disclosed',()=>{
 const r=syntaxOutcome({error:{code:'PRIVATE_CODE',message:'private path or credential'},status:null});
 assert.deepEqual(r,{status:'CHECK_UNAVAILABLE',checkerErrorCode:'CHECKER_FAILED'});
});
test('actual node checker still parses valid staging code without executing it',async()=>{
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'oldies-parse-'));
 try{
  const file='tumblr_auto_news_v3.mjs',sentinel=path.join(root,'NOT_EXECUTED');
  fs.writeFileSync(path.join(root,file),`import fs from 'node:fs';fs.writeFileSync(${JSON.stringify(sentinel)},'bad');`);
  const r=JSON.parse((await callProject('check_staging_syntax',{file},{stagingRoot:root,node:process.execPath},null)).content[0].text);
  assert.equal(r.status,'SYNTAX_OK');assert(!fs.existsSync(sentinel));
  fs.writeFileSync(path.join(root,file),'const = ;');
  const bad=JSON.parse((await callProject('check_staging_syntax',{file},{stagingRoot:root,node:process.execPath},null)).content[0].text);
  assert.equal(bad.status,'SYNTAX_ERROR');
 }finally{fs.rmSync(root,{recursive:true,force:true});}
});
