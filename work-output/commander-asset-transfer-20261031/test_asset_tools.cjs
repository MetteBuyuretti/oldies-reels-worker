'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {createAssetTools,TOOLS}=require('./asset-tools.cjs');
const root=fs.mkdtempSync(path.join(__dirname,'MCP-TEST-'));
const policy={root,python:'C:/Users/METE/AppData/Local/Programs/Python/Python312/python.exe',helper:path.join(__dirname,'fixture_helper.py'),sources:{fixture:{url:'https://images.example.test/fixture.png',hosts:['images.example.test']}}};
const t=createAssetTools(policy);const unwrap=r=>JSON.parse(r.content[0].text);
(async()=>{
 assert.equal(TOOLS.length,3);assert(t.TOOLS.every(x=>x.description.includes(root)));
 await assert.rejects(t.call('import_approved_image',{asset_id:'fixture',name:'../bad.png'}),/ASSET_OPERATION_DENIED/);
 await assert.rejects(t.call('import_approved_image',{asset_id:'fixture',name:'x.png',url:'https://bad'}),/ARGUMENTS_DENIED/);
 const receipt=unwrap(await t.call('import_approved_image',{asset_id:'fixture',name:'actual.png'}));
 assert.equal(receipt.status,'TRANSFERRED');assert.equal(receipt.sha256,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'actual.png'))).digest('hex'));assert.equal(receipt.width,4);assert.equal(receipt.height,3);
 const verify=unwrap(await t.call('verify_asset_file',{name:'actual.png'}));assert.equal(verify.sha256,receipt.sha256);
 const reread=unwrap(await t.call('read_asset_receipt',{name:'actual.png'}));assert.equal(reread.sha256,receipt.sha256);assert.equal(reread.receipt_kind,'RECOMPUTED_FROM_EXISTING_FILE');
 const repeated=unwrap(await t.call('import_approved_image',{asset_id:'fixture',name:'actual.png'}));assert.equal(repeated.status,'ALREADY_PRESENT');
 const out={status:'PASS',mcp_handler_calls:['import_approved_image','verify_asset_file','read_asset_receipt'],actual_windows_file:true,sha256:receipt.sha256,bytes:receipt.bytes,width:receipt.width,height:receipt.height,network:'TEST-ONLY local byte injection, not live HTTPS',production_tool_activated:false};
 fs.writeFileSync(path.join(__dirname,'handler-test.json'),JSON.stringify(out,null,2)+'\n');console.log(JSON.stringify(out));
})().catch(e=>{console.error(e.stack);process.exitCode=1});
