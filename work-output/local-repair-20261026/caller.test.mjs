import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {dailyAdmission,submissionBudget,shouldSubmit,cards} from './budget-excerpt.mjs';
const now='2026-10-26T12:00:00Z',targetAt='2026-10-27T09:00:00Z';
const inv=()=>({complete:true,queueComplete:true,allPathsCovered:true,published:[],queued:[],nextQueueTarget:{forDraftId:'draft-1',semantics:'VERIFIED_NEXT_PUBLICATION_TIME',source:'PLATFORM_QUEUE_PREVIEW',observedAt:now,scheduledAt:targetAt}});
test('integrated caller refuses fourth item on a full future target day',()=>{
 const i=inv();i.queued=[1,2,3].map(x=>({tumblrId:String(x),scheduledAt:targetAt}));
 const b=submissionBudget(i,{items:[]},{},{tumblrId:'draft-1'},now);
 assert.equal(b.day,'2026-10-27');assert.equal(b.remaining,0);
});
test('reservation day and timestamp returned to caller are target values',()=>{
 const b=submissionBudget(inv(),{items:[]},{},{sourceDraftId:'draft-1',tumblrId:'new-id'},now);
 assert.equal(b.day,'2026-10-27');assert.equal(b.targetAt,targetAt);
 const source=fs.readFileSync(new URL('./verify-flow.txt',import.meta.url),'utf8');
 assert.ok(source.includes('row.reservedDay=budget.day;row.targetAt=budget.targetAt;'));
});
test('unproved, stale, wrong-draft and generic DOM timestamps cannot admit',()=>{
 for(const change of [{nextQueueTarget:null},{nextQueueTarget:{...inv().nextQueueTarget,forDraftId:'wrong'}},{nextQueueTarget:{...inv().nextQueueTarget,source:'GENERIC_DOM_TIME'}},{nextQueueTarget:{...inv().nextQueueTarget,observedAt:'2026-10-26T11:58:00Z'}}]){
  assert.throws(()=>submissionBudget({...inv(),...change},{items:[]},{},{tumblrId:'draft-1'},now),/TARGET_PUBLICATION/);
 }
});
test('publisher verification does not require an enqueue authorization',()=>{
 assert.equal(shouldSubmit([],null,null,null),false);
 assert.equal(shouldSubmit(['--verify'],null,null,null),false);
 assert.throws(()=>shouldSubmit(['--queue-ready'],{id:'a',bodyHtml:'',alt:'',image:''},{},{}),/AUTHORIZATION_REQUIRED/);
});
test('same-day manual plus queue plus unresolved reservation exhaust capacity',()=>{
 const i=inv();i.published=[{tumblrId:'manual',publishedAt:targetAt}];i.queued=[{tumblrId:'auto',scheduledAt:targetAt}];
 assert.equal(dailyAdmission(i,{items:[{id:'reserved',status:'UNKNOWN',reservedDay:'2026-10-27'}]},now,targetAt).remaining,0);
});
test('missing all-writer evidence remains blocked in integrated helper',()=>{
 const i=inv();i.allPathsCovered=false;
 assert.throws(()=>submissionBudget(i,{items:[]},{},{tumblrId:'draft-1'},now),/BUDGET_UNVERIFIED/);
});
