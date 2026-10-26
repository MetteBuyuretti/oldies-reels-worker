// Exact scoped functions extracted from installed publisher; no browser startup.
import fs from 'node:fs';
import crypto from 'node:crypto';
export const normalise=s=>s.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();
export const bodyHash=p=>crypto.createHash('sha256').update(p.bodyHtml+'\n'+p.alt+'\n'+p.image).digest('hex');
export function eligible(p,item,auth){
 const grant=auth?.items?.find(x=>x.id===p.id);
 if(auth?.blog!=='oldiesradyo'||!grant||grant.bodyHash!==bodyHash(p)||grant.tumblrDraftId!==(item.sourceDraftId||item.tumblrId)||grant.qcVerified!==true)throw Error('QC_OR_SCOPED_AUTHORIZATION_REQUIRED: '+p.id);
 return item.status==='DRAFT_VERIFIED';
}
export const atomic=(file,data)=>{fs.writeFileSync(file+'.tmp',JSON.stringify(data,null,2));fs.renameSync(file+'.tmp',file);};
const uncertain = new Set(['SUBMITTING','UNKNOWN','RECONCILIATION_REQUIRED']);
export function istanbulDay(value) {
  if (typeof value !== 'string' || !/(?:Z|[+-]\d{2}:\d{2})$/.test(value)) throw Error('EXPLICIT_TIMEZONE_REQUIRED');
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) throw Error('INVALID_PUBLICATION_TIME');
  return new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Istanbul',year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
}
export function reconcileJournal(pkg,journal,queued,published,at=new Date().toISOString()){
 // Validate the whole observation before mutating or writing any journal row.
 const next=structuredClone(journal);
 for(const p of pkg.posts){
  const row=next.items.find(x=>x.id===p.id);if(!row)throw Error('UNREGISTERED_DRAFT: '+p.id);
  const qs=queued.filter(x=>x.id===p.id),ps=published.filter(x=>x.id===p.id);
  if(qs.length>1||ps.length>1||qs.length&&ps.length)throw Error('REMOTE_CONFLICT: '+p.id);
  const remote=ps[0]||qs[0];
  if(remote){
   if(row.status==='PUBLISHED_VERIFIED'&&!ps.length)throw Error('REMOTE_STATE_DOWNGRADE: '+p.id);
   const url=new URL(remote.url);const postId=url.pathname.match(/^\/oldiesradyo\/(\d+)(?:\/|$)/)?.[1];
   if(url.origin!=='https://www.tumblr.com'||!postId||postId!==remote.tumblrId)throw Error('REMOTE_ID_MISMATCH: '+p.id);
   row.sourceDraftId ||= row.tumblrId||p.tumblrId;
   Object.assign(row,remote,{status:ps.length?'PUBLISHED_VERIFIED':'QUEUED_VERIFIED',verifiedAt:at,evidence:'Complete account scan; unique title, exact story, actual permalink and tracked footer'});
  }else if(['SUBMITTING','UNKNOWN','RECONCILIATION_REQUIRED','QUEUED_VERIFIED','PUBLISHED_VERIFIED'].includes(row.status))throw Error('REMOTE_STATE_RECONCILIATION_REQUIRED: '+p.id);
 }
 return next;
}
export function dailyAdmission(inventory, journal, now, targetAt) {
  if (!inventory?.complete || !inventory?.queueComplete || inventory.allPathsCovered !== true) throw Error('DAILY_PUBLICATION_BUDGET_UNVERIFIED');
  if (!Array.isArray(inventory.published) || !Array.isArray(inventory.queued) || !Array.isArray(journal?.items)) throw Error('DAILY_INVENTORY_INVALID');
  if (!targetAt) throw Error('TARGET_PUBLICATION_TIME_UNVERIFIED');
  const today=istanbulDay(now), day=istanbulDay(targetAt), reservations=new Map();
  if (day < today) throw Error('TARGET_PUBLICATION_DAY_IN_PAST');
  const remember=(key,date)=>{
    if (reservations.has(key) && reservations.get(key)!==date) throw Error('PUBLICATION_DAY_CONFLICT');
    reservations.set(key,date);
  };
  for (const post of inventory.published) {
    if (!post.tumblrId || !post.publishedAt) throw Error('DAILY_PUBLICATION_TIME_UNVERIFIED');
    remember('post:'+post.tumblrId,istanbulDay(post.publishedAt));
  }
  for (const post of inventory.queued) {
    if (!post.tumblrId || !post.scheduledAt) throw Error('DAILY_PUBLICATION_TIME_UNVERIFIED');
    remember('post:'+post.tumblrId,istanbulDay(post.scheduledAt));
  }
  for (const row of journal.items) {
    if (!uncertain.has(row.status)) continue;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(row.reservedDay||'') || row.reservedDay < today) throw Error('UNCERTAIN_PUBLICATION_REQUIRES_RECONCILIATION');
    if (!row.tumblrId && !row.id) throw Error('RESERVATION_ID_MISSING');
    remember(row.tumblrId?'post:'+row.tumblrId:'job:'+row.id,row.reservedDay);
  }
  const used=[...reservations.values()].filter(date=>date===day).length;
  return {day,used,remaining:Math.max(0,3-used)};
}


export function submissionBudget(inventory,journal,p,row,now=new Date().toISOString()){
 const target=inventory.nextQueueTarget;
 // Generic DOM <time> and operator booleans cannot prove an automatic queue slot.
 if(!target||target.semantics!=='VERIFIED_NEXT_PUBLICATION_TIME'||
    target.source!=='PLATFORM_QUEUE_PREVIEW'||target.forDraftId!==(row.sourceDraftId||row.tumblrId))throw Error('TARGET_PUBLICATION_TIME_UNVERIFIED');
 const age=Date.parse(now)-Date.parse(target.observedAt);
 if(!Number.isFinite(age)||age<0||age>60000)throw Error('TARGET_PUBLICATION_EVIDENCE_STALE');
 const budget=dailyAdmission(inventory,journal,now,target.scheduledAt);
 return {...budget,targetAt:target.scheduledAt};
}
export function shouldSubmit(args,p,row,auth){
 // Verify never evaluates publication eligibility or enters editor/enqueue.
 return args.includes('--queue-ready')&&eligible(p,row,auth);
}
export const acquirePublisherLock=file=>{
 const handle=fs.openSync(file,'wx');
 try{fs.writeSync(handle,JSON.stringify({pid:process.pid,at:new Date().toISOString()}));return handle;}
 catch(e){fs.closeSync(handle);fs.unlinkSync(file);throw e;}
};
export async function cards(page,pkg,{expectedCount,maxPasses=30,kind='published'}={}){
 const found=new Map(),observed=new Map();let complete=expectedCount===0;
 for(let pass=0;pass<maxPasses&&!complete;pass++){
  // The account-count link renders before article bodies. Wait for content first.
  await page.getByRole('article').first().waitFor({state:'visible',timeout:15000});
  const articles=page.getByRole('article');let lastOwn=null;
  for(let i=0;i<await articles.count();i++){
   const article=articles.nth(i);
   const permalink=article.getByRole('link',{name:'Kalıcı bağlantı',exact:true});
   if(!await permalink.count())continue;
   const href=await permalink.first().getAttribute('href');
   const id=href?.match(/(?:^|\/)oldiesradyo\/(\d+)(?:\/|$)/)?.[1];
   if(!id)continue; // Sponsored cards belong to other blogs, outside this inventory.
   lastOwn=article;
   const time=article.getByRole('time').first();
   const datetime=await time.count()?await time.getAttribute('datetime'):null;
   observed.set(id,kind==='published'?{tumblrId:id,publishedAt:datetime}:{tumblrId:id,observedTime:datetime,timeSemantics:'UNVERIFIED_QUEUE_TIMESTAMP'});
  }
  for(const p of pkg.posts){
   const card=articles.filter({has:page.getByRole('heading',{name:p.title,exact:true})});
   if(await card.count()>1)throw Error('DUPLICATE_REMOTE_TITLE: '+p.id);
   if(await card.count()===1){
    const href=await card.getByRole('link',{name:'Kalıcı bağlantı',exact:true}).first().getAttribute('href');
    const id=href?.match(/oldiesradyo\/(\d+)/)?.[1];if(!id)throw Error('REMOTE_ID_MISSING');
    const link=card.getByRole('link',{name:'https://oldiesradyo.com/',exact:true});
    if(await link.count()!==1||await link.getAttribute('href')!==p.utm)throw Error('REMOTE_FOOTER_MISMATCH: '+p.id);
    const body=normalise(await card.innerText());
    if(!p.paragraphs.every(s=>body.includes(normalise(s))))throw Error('REMOTE_STORY_MISMATCH: '+p.id);
    if(found.has(p.id)&&found.get(p.id).tumblrId!==id)throw Error('DUPLICATE_REMOTE_TITLE: '+p.id);
    const timestamp=observed.get(id)?.publishedAt;
    found.set(p.id,{id:p.id,tumblrId:id,url:new URL(href,'https://www.tumblr.com').href,scheduled:(await card.getByRole('time').allTextContents())[0]?.trim()||null,...(timestamp?{publishedAt:timestamp}:{})});
   }
  }
  complete=Number.isInteger(expectedCount)&&observed.size===expectedCount;
  if(!complete){if(lastOwn)await lastOwn.scrollIntoViewIfNeeded();await page.mouse.wheel(0,700);await page.waitForTimeout(500);}
 }
 if(!complete)throw Error('REMOTE_INVENTORY_INCOMPLETE');
 return {matches:[...found.values()],inventory:[...observed.values()],complete};
}
