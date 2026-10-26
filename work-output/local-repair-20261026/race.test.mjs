import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawn} from 'node:child_process';
import {fileURLToPath} from 'node:url';
test('two synthetic entry points compete for one target-day reservation',async()=>{
 const dir=fs.mkdtempSync(path.join(fileURLToPath(new URL('./',import.meta.url)),'budget-race-'));
 const file=path.join(dir,'ledger.json'),lock=path.join(dir,'publisher.lock');
 fs.writeFileSync(file,JSON.stringify({items:[]}));
 const mod=new URL('./budget-excerpt.mjs',import.meta.url).href;
 const childCode=`import fs from 'node:fs';import {acquirePublisherLock,dailyAdmission,atomic} from ${JSON.stringify(mod)};
 const file=${JSON.stringify(file)},lock=${JSON.stringify(lock)};let h;
 try{h=acquirePublisherLock(lock);const j=JSON.parse(fs.readFileSync(file));const at='2026-10-27T10:00:00Z';
 const i={allPathsCovered:true,complete:true,queueComplete:true,published:[{tumblrId:'manual',publishedAt:at}],queued:[{tumblrId:'auto',scheduledAt:at}]};
 const b=dailyAdmission(i,j,'2026-10-26T12:00:00Z',at);if(!b.remaining)throw Error('FULL');
 j.items.push({id:process.argv[1],status:'SUBMITTING',reservedDay:b.day,targetAt:at});atomic(file,j);console.log('ADMITTED');
 await new Promise(r=>setTimeout(r,200));}catch(e){console.log('BLOCKED:'+e.code+':'+e.message);}finally{if(h!==undefined){fs.closeSync(h);fs.unlinkSync(lock);}}`;
 const run=entry=>new Promise((resolve,reject)=>{let out='';const c=spawn(process.execPath,['--input-type=module','-e',childCode,entry]);c.stdout.on('data',d=>out+=d);c.once('error',reject);c.once('exit',code=>code?reject(Error('child '+code)):resolve(out));});
 try{const out=await Promise.all([run('synthetic-launcher'),run('synthetic-legacy')]);assert.equal(out.filter(x=>x.includes('ADMITTED')).length,1,JSON.stringify(out));const j=JSON.parse(fs.readFileSync(file));assert.equal(j.items.length,1);assert.equal(j.items[0].reservedDay,'2026-10-27');}
 finally{for(const p of [file,file+'.tmp',lock])if(fs.existsSync(p))fs.unlinkSync(p);fs.rmdirSync(dir);}
});
