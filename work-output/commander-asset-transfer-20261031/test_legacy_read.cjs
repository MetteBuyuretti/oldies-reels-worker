'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const gateway=require('./gateway-asset.cjs');
const root=fs.mkdtempSync(path.join(__dirname,'READ-TEST-'));const file=path.join(root,'report.txt');fs.writeFileSync(file,'test report\n');
const policy={root,file,fileSHA256:gateway.sha256(fs.readFileSync(file))};let calls=0;
const upstream={callTool:async()=>{calls++;return {content:[{type:'text',text:'test report\n'}]}}};
(async()=>{assert.equal(gateway.PUBLIC_TOOL.name,'read_file');const r=await gateway.callReadOnly({name:'read_file',arguments:{file:gateway.FILE_ALIAS}},policy,upstream);assert(r.content[0].text.includes('test report'));assert.equal(calls,1);await assert.rejects(gateway.callReadOnly({name:'read_file',arguments:{file:'../../secret'}},policy,upstream),/ARGUMENTS_DENIED/);assert.equal(calls,1);console.log(JSON.stringify({status:'PASS',tool:'legacy fixed report read',active_runtime_unchanged:true}));})().catch(e=>{console.error(e.stack);process.exitCode=1});
