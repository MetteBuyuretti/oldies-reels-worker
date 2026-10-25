import test from 'node:test';
import assert from 'node:assert/strict';
import {dailyAdmission,istanbulDay} from './daily-budget.mjs';
const now='2026-10-25T02:00:00Z', target='2026-10-26T09:00:00Z';
const empty=()=>({complete:true,queueComplete:true,allPathsCovered:true,published:[],queued:[]});
const journal=()=>({items:[]});
test('tomorrow full, today empty: fourth tomorrow has zero capacity',()=>{
 const i=empty(); i.queued=[1,2,3].map(x=>({tumblrId:String(x),scheduledAt:'2026-10-26T10:00:00Z'}));
 assert.equal(dailyAdmission(i,journal(),now,target).remaining,0);
});
test('today full does not consume tomorrow capacity',()=>{
 const i=empty(); i.published=[1,2,3].map(x=>({tumblrId:String(x),publishedAt:now}));
 assert.equal(dailyAdmission(i,journal(),now,target).remaining,3);
});
test('target day uses Istanbul midnight, not host timezone',()=>{
 assert.equal(istanbulDay('2026-10-25T21:00:00Z'),'2026-10-26');
 const i=empty(); i.queued=[{tumblrId:'1',scheduledAt:'2026-10-25T21:00:00Z'}];
 assert.equal(dailyAdmission(i,journal(),now,target).used,1);
});
test('no all-path evidence remains blocked',()=>{
 const i=empty(); i.allPathsCovered=false;
 assert.throws(()=>dailyAdmission(i,journal(),now,target),/BUDGET_UNVERIFIED/);
});
test('unknown target cannot silently default to today',()=>assert.throws(()=>dailyAdmission(empty(),journal(),now),/TARGET_PUBLICATION_TIME_UNVERIFIED/));
test('missing queue time is not inferred from observation time',()=>{
 const i=empty(); i.queued=[{tumblrId:'1'}];
 assert.throws(()=>dailyAdmission(i,journal(),now,target),/TIME_UNVERIFIED/);
});
test('duplicate platform identity across paths counts once',()=>{
 const i=empty(); i.queued=[{tumblrId:'1',scheduledAt:target},{tumblrId:'1',scheduledAt:target}];
 assert.equal(dailyAdmission(i,journal(),now,target).used,1);
});
test('manual publication plus queue plus reservation exhausts target day',()=>{
 const i=empty(); i.published=[{tumblrId:'manual',publishedAt:target}]; i.queued=[{tumblrId:'queue',scheduledAt:target}];
 const j={items:[{id:'pending',status:'SUBMITTING',reservedDay:'2026-10-26'}]};
 assert.equal(dailyAdmission(i,j,now,target).remaining,0);
});
test('uncertain known post and matching platform record count once',()=>{
 const i=empty(); i.queued=[{tumblrId:'1',scheduledAt:target}];
 const j={items:[{id:'a',tumblrId:'1',status:'UNKNOWN',reservedDay:'2026-10-26'}]};
 assert.equal(dailyAdmission(i,j,now,target).used,1);
});
test('one identity on inconsistent days requires reconciliation',()=>{
 const i=empty(); i.published=[{tumblrId:'1',publishedAt:now}];i.queued=[{tumblrId:'1',scheduledAt:target}];
 assert.throws(()=>dailyAdmission(i,journal(),now,target),/PUBLICATION_DAY_CONFLICT/);
});
test('past uncertain reservation is never forgotten',()=>{
 const j={items:[{id:'old',status:'UNKNOWN',reservedDay:'2026-10-24'}]};
 assert.throws(()=>dailyAdmission(empty(),j,now,target),/REQUIRES_RECONCILIATION/);
});
test('past target day is rejected',()=>assert.throws(()=>dailyAdmission(empty(),journal(),now,'2026-10-24T09:00:00Z'),/DAY_IN_PAST/));
test('invalid and timezone-less timestamps are rejected',()=>{
 assert.throws(()=>dailyAdmission(empty(),journal(),now,'not-a-dateZ'),/INVALID_PUBLICATION_TIME/);
 assert.throws(()=>dailyAdmission(empty(),journal(),now,'2026-10-26T09:00:00'),/TIMEZONE_REQUIRED/);
});
test('pure calculation preserves inventory and ledger',()=>{
 const i=empty(),j=journal(),before=JSON.stringify({i,j});dailyAdmission(i,j,now,target);
 assert.equal(JSON.stringify({i,j}),before);
});
