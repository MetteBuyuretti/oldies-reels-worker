'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const {createPilot} = require('./readonly-pilot.cjs');
async function scenario(fn){
 const root=fs.mkdtempSync(path.join(os.tmpdir(),'oldies-pilot-'));
 const project=path.join(root,'other-project');fs.mkdirSync(project);
 fs.writeFileSync(path.join(project,'good.txt'),'hello oldies\n');
 fs.writeFileSync(path.join(project,'.env'),'PRIVATE=1');
 fs.mkdirSync(path.join(project,'.git'));fs.writeFileSync(path.join(project,'.git','config'),'PRIVATE=1');
 fs.writeFileSync(path.join(project,'bad.txt'),Buffer.from([0xc3,0x28]));
 fs.writeFileSync(path.join(project,'huge.txt'),Buffer.alloc(65537,0x61));
 fs.mkdirSync(path.join(project,'sub'));
 const p = (options={})=>createPilot({roots:{other:project},...options},{allowedDirectories:[root]});
 try{return await fn({root,project,p});} finally {fs.rmSync(root,{recursive:true,force:true});}
}
const decoded = r => JSON.parse(r.content[0].text);
test('lists allowed project, excluding dot files',()=>scenario(async ({p})=>{
 const a=decoded(await p().call('pilot_list_directory',{project:'other',relative_path:''}));
 assert(a.entries.some(e=>e.name==='good.txt'));assert(!a.entries.some(e=>e.name==='.env'));assert(!a.entries.some(e=>e.name==='.git'));
}));
test('reads text and exact sha',()=>scenario(async ({p})=>{
 const a=decoded(await p().call('pilot_read_text',{project:'other',relative_path:'good.txt'}));
 assert.equal(a.text,'hello oldies\n');assert.equal(a.bytes,13);
 assert.equal(a.sha256,crypto.createHash('sha256').update('hello oldies\n').digest('hex'));
}));
test('rejects traversal and alternate Windows notation',()=>scenario(async ({p})=>{
 for(const rel of ['../good.txt','sub/../good.txt','C:\\Windows\\win.ini','\\\\server\\share','good.txt:secret','.env','.git/config','sub\\..\\good.txt'])
  await assert.rejects(p().call('pilot_read_text',{project:'other',relative_path:rel}),/PATH_DENIED/);
}));
test('rejects unknown project and unexpected input',()=>scenario(async ({p})=>{
 await assert.rejects(p().call('pilot_read_text',{project:'secrets',relative_path:'good.txt'}),/PROJECT_DENIED/);
 await assert.rejects(p().call('pilot_read_text',{project:'other',relative_path:'good.txt',shell:'cmd'}),/ARGUMENTS_DENIED/);
}));
test('rejects roots not allowed by actual upstream config',()=>scenario(({project})=>{
 assert.throws(()=>createPilot({roots:{other:project}},{allowedDirectories:[os.tmpdir()+'/unrelated']}),/UPSTREAM_DIRECTORY_DENIED/);
}));
test('rejects symlink escape',()=>scenario(async ({root,project,p})=>{
 fs.symlinkSync(root,path.join(project,'escape'));
 await assert.rejects(p().call('pilot_read_text',{project:'other',relative_path:'escape/other-project/good.txt'}),/FILE_TYPE_DENIED|REPARSE_DENIED/);
}));
test('rejects too large and malformed utf8',()=>scenario(async ({p})=>{
 await assert.rejects(p().call('pilot_read_text',{project:'other',relative_path:'huge.txt'}),/FILE_TOO_LARGE/);
 await assert.rejects(p().call('pilot_read_text',{project:'other',relative_path:'bad.txt'}),/FILE_FORMAT_DENIED/);
}));
test('fixed command cannot run on non-Windows',()=>scenario(async ({p})=>{
 await assert.rejects(p().call('pilot_powershell_info',{project:'other'}),/WINDOWS_ONLY/);
}));
test('rejects unpinned executable even in simulated Windows',()=>scenario(async ({project})=>{
 const pilot=createPilot({roots:{other:project}},{allowedDirectories:[path.dirname(project)],platform:'win32'});
 await assert.rejects(pilot.call('pilot_powershell_info',{project:'other'}),/EXE_PIN_REQUIRED/);
}));
test('simulated Windows exec has fixed exact PowerShell args and cwd',()=>scenario(async ({project})=>{
 const exe=path.join(project,'pwsh.exe');fs.writeFileSync(exe,'synthetic executable');
 const hash=crypto.createHash('sha256').update('synthetic executable').digest('hex');
 let called=0;
 const pilot=createPilot({roots:{other:project},powershellExe:exe,powershellSha256:hash},
  {allowedDirectories:[path.dirname(project)],platform:'win32',runner:(command,args,opts)=>{
   called++;assert.equal(command,exe);assert.equal(opts.cwd,project);assert.equal(opts.shell,false);
   assert.equal(args.at(-1),'$PSVersionTable.PSVersion.ToString(); (Get-Location).Path');
   return {status:0,stdout:'5.1\n'+project+'\n',stderr:''};
  }});
 const out=decoded(await pilot.call('pilot_powershell_info',{project:'other'}));
 assert.equal(out.status,'COMPLETED');assert.equal(called,1);
}));
test('rejects unrecognized action',()=>scenario(async ({p})=>{
 await assert.rejects(p().call('start_process',{project:'other',command:'rm -rf /'}),/TOOL_DENIED/);
}));
test('rejects unpinned changed executable',()=>scenario(async ({project})=>{
 const exe=path.join(project,'pwsh.exe');fs.writeFileSync(exe,'new executable');
 const pilot=createPilot({roots:{other:project},powershellExe:exe,powershellSha256:'0'.repeat(64)},
  {allowedDirectories:[path.dirname(project)],platform:'win32',runner:()=>{throw Error('MUST_NOT_RUN')}});
 await assert.rejects(pilot.call('pilot_powershell_info',{project:'other'}),/EXE_CHANGED_DENIED/);
}));
test('preserves nonzero exit code of a fixed failed command',()=>scenario(async ({project})=>{
 const exe=path.join(project,'pwsh.exe');fs.writeFileSync(exe,'fake exe');
 const sha=crypto.createHash('sha256').update('fake exe').digest('hex');
 const pilot=createPilot({roots:{other:project},powershellExe:exe,powershellSha256:sha},
  {allowedDirectories:[path.dirname(project)],platform:'win32',runner:()=>({status:9,stdout:'',stderr:'failure'})});
 const out=decoded(await pilot.call('pilot_powershell_info',{project:'other'}));
 assert.equal(out.status,'FAILED');assert.equal(out.exitCode,9);
}));
test('rejects interrupted or timed-out commands as incomplete',()=>scenario(async ({project})=>{
 const exe=path.join(project,'pwsh.exe');fs.writeFileSync(exe,'fake exe');
 const sha=crypto.createHash('sha256').update('fake exe').digest('hex');
 const pilot=createPilot({roots:{other:project},powershellExe:exe,powershellSha256:sha},
  {allowedDirectories:[path.dirname(project)],platform:'win32',runner:()=>({status:null,signal:'SIGTERM',error:{code:'ETIMEDOUT'}})});
 await assert.rejects(pilot.call('pilot_powershell_info',{project:'other'}),/COMMAND_NOT_COMPLETED/);
}));
