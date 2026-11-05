// 05.11.2026 — imports observed platform receipts; no browser or network calls.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {validatePackage,readJson} from 'file:///C:/Users/METE/oldies-jingle-automation/tumblr_editorial_control_v4.mjs';
import {bodyHash,acquirePublisherLock} from 'file:///C:/Users/METE/oldies-jingle-automation/tumblr_auto_news_v3.mjs';
const root='C:/Users/METE/oldies-jingle-automation';
const base='C:/Users/METE/Documents/Oldies-Radyo-Automation/Tumblr/editorial';
const repair=path.join(base,'repair-20261105');
const paths=[path.join(base,'tumblr-editorial-package.json'),path.join(root,'tumblr-editorial-state.json'),path.join(root,'tumblr-publication-authorization.json')];
const lock=path.join(root,'tumblr-publisher.lock');
const handle=acquirePublisherLock(lock);
const baseline=paths.map(p=>fs.readFileSync(p));
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const backup=path.join(repair,'backup-'+new Date().toISOString().replace(/[:.]/g,'-'));
fs.mkdirSync(backup,{recursive:true});
paths.forEach((p,i)=>fs.writeFileSync(path.join(backup,path.basename(p)),baseline[i]));
let wrote=false;
try {
 const pkg=JSON.parse(baseline[0]),journal=JSON.parse(baseline[1]),auth=JSON.parse(baseline[2]);
 const fresh=readJson(path.join(base,'new-editorial-posts.json'));
 const receipt=readJson(path.join(repair,'platform-receipts.json'));
 const images=readJson(path.join(repair,'reviewed-image-bytes.json'));
 if(fresh.posts.length!==9||receipt.items.length!==9||new Set(receipt.items.map(x=>x.id)).size!==9)throw Error('EXACT_NINE_VERIFIED_RECEIPTS_REQUIRED');
 const originalCounts={posts:pkg.posts.length,journal:journal.items.length,grants:auth.items.length};
 const imageProof=[];
 for(const p of fresh.posts){
  const r=receipt.items.find(r=>r.id===p.id);
  if(!r||!['PUBLISHED_VERIFIED','QUEUED_VERIFIED'].includes(r.status)||!/^\d{10,}$/.test(r.tumblrId))throw Error('UNVERIFIED_RECEIPT');
  if(new URL(r.url).pathname.match(/^\/oldiesradyo\/(\d+)\//)?.[1]!==r.tumblrId)throw Error('RECEIPT_ID_MISMATCH');
  if(!images[p.id]||path.basename(p.image)!==p.image)throw Error('IMAGE_BYTES_MISSING');
  const bytes=Buffer.from(images[p.id],'base64');
  if(bytes.length<10000||bytes.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('INVALID_IMAGE');
  fs.writeFileSync(path.join(base,p.image),bytes);
  imageProof.push({id:p.id,sha256:digest(bytes),bytes:bytes.length});
  delete p.targetAt;
  Object.assign(p,{tumblrId:r.tumblrId,status:r.status,qcVerifiedAt:r.verifiedAt,editUrl:'https://www.tumblr.com/edit/oldiesradyo/'+r.tumblrId});
  const old=pkg.posts.find(x=>x.id===p.id);
  if(old&&bodyHash(old)!==bodyHash(p))throw Error('PACKAGE_CONFLICT');
  if(!old)pkg.posts.push(p);
 }
 const items=validatePackage(pkg,base);
 for(const p of fresh.posts){
  const r=receipt.items.find(x=>x.id===p.id),v=items.find(x=>x.id===p.id);
  const old=journal.items.find(x=>x.id===p.id);
  if(old&&(old.hash!==v.hash||old.tumblrId!==r.tumblrId))throw Error('JOURNAL_CONFLICT');
  const row={...v,...r,sourceDraftId:r.sourceDraftId||r.tumblrId,scheduled:r.scheduleLabel||null,evidence:r.evidence||'Saved draft and actual platform card: story, sources, image/alt, UTM verified'};
  if(old)Object.assign(old,row);else journal.items.push(row);
  const grant={id:p.id,tumblrDraftId:row.sourceDraftId,bodyHash:bodyHash(p),qcVerified:true,recordedAt:r.verifiedAt,scope:'Only this reviewed body/image/alt and observed platform ID; no blanket authority'};
  const oldGrant=auth.items.find(x=>x.id===p.id);
  if(oldGrant&&(oldGrant.bodyHash!==grant.bodyHash||oldGrant.tumblrDraftId!==grant.tumblrDraftId))throw Error('GRANT_CONFLICT');
  if(!oldGrant)auth.items.push(grant);
 }
 auth.previousAuthorization ||= auth.authorization;
 auth.authorization='Existing three grants preserved. Additional nine individually reviewed stories under Mete’s 5 November 2026 Pinterest/Tumblr restoration instruction. No other content is authorized by this file. Daily maximum remains three, zero added cost.';
 auth.recordedAt=new Date().toISOString();
 const daily={};for(const r of receipt.items){const s=r.publishedAt||r.scheduledAt;if(!s)throw Error('MISSING_DAY');const d=new Date(Date.parse(s)+3*3600000).toISOString().slice(0,10);daily[d]=(daily[d]||0)+1;}if(Object.values(daily).some(n=>n>3))throw Error('DAILY_LIMIT_EXCEEDED');
 paths.forEach((p,i)=>{if(digest(fs.readFileSync(p))!==digest(baseline[i]))throw Error('CONCURRENT_CHANGE');});
 wrote=true;
 [pkg,journal,auth].forEach((value,i)=>{const tmp=paths[i]+'.social-repair.tmp';fs.writeFileSync(tmp,JSON.stringify(value,null,2));fs.renameSync(tmp,paths[i]);});
 validatePackage(readJson(paths[0]),base);
 const proof={at:new Date().toISOString(),mode:'IMPORT_VERIFIED_BROWSER_RECEIPTS_ONLY',published:receipt.items.filter(x=>x.status==='PUBLISHED_VERIFIED').length,queued:receipt.items.filter(x=>x.status==='QUEUED_VERIFIED').length,daily,originalCounts,finalCounts:{posts:pkg.posts.length,journal:journal.items.length,grants:auth.items.length},files:paths.map(p=>({path:p,sha256:digest(fs.readFileSync(p))})),imageProof,backup,networkCalls:0,publicationCalls:0};
 fs.writeFileSync(path.join(repair,'import-receipt.json'),JSON.stringify(proof,null,2));console.log(JSON.stringify(proof));
}catch(e){if(wrote)paths.forEach((p,i)=>fs.writeFileSync(p,baseline[i]));throw e;}
finally{fs.closeSync(handle);fs.unlinkSync(lock);}
