'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const baseline=fs.readFileSync('C:/Users/METE/oldies-jingle-automation/tumblr_auto_news_v3.mjs','utf8');
const candidate=fs.readFileSync(path.join(__dirname,'candidate/tumblr_auto_news_v3.mjs'),'utf8');
function load(source){const start=source.indexOf('export async function cards('),end=source.indexOf('\nasync function verifyEditor(',start);assert(start>=0&&end>start);const actual=source.slice(start,end).replace('export async function cards','async function cards');return vm.runInNewContext(actual+'\ncards',{URL,normalise:s=>s});}
function makePage(mode){let phase=0,scrolls=0,wheels=0;
 const records=[{id:'111',title:'A'},{id:'222',title:'B'}];
 function card(r){const c={getByRole:(role,opt)=>{
  if(role==='link'&&opt.name==='Kalıcı bağlantı')return {count:async()=>1,first(){return this},getAttribute:async()=>`https://www.tumblr.com/oldiesradyo/${r.id}/post`};
  if(role==='link')return {count:async()=>1,getAttribute:async()=> 'https://example.test/utm'};
  if(role==='time')return {first(){return this},count:async()=>1,getAttribute:async()=> '2026-10-31T10:00:00Z',allTextContents:async()=>['today']};throw Error('unexpected role');},
  innerText:async()=> 'story',scrollIntoViewIfNeeded:async()=>{scrolls++;throw Error('Element is not attached to the DOM');}};return c;}
 const page={getByRole:(role,opt)=>{
  if(role==='heading')return {heading:opt.name};
  if(role!=='article')throw Error('unexpected role');
  const active=()=>phase===0?[records[0]]:records;
  const list={first:()=>({waitFor:async()=>{}}),count:async()=>active().length,nth:i=>card(active()[i]),filter:({has})=>{
   if(has.heading){const matches=active().filter(r=>r.title===has.heading);const chosen=card(matches[0]||records[0]);chosen.count=async()=>matches.length;return chosen;}
   assert(has.selector);return {first:()=>({waitFor:async()=>{},scrollIntoViewIfNeeded:async()=>{scrolls++;if(mode==='persistent'||scrolls===1)throw Error('Element is not attached to the DOM');}})};
  }};return list;
 },locator:selector=>({selector}),mouse:{wheel:async()=>{wheels++;phase=1;}},waitForTimeout:async()=>{}};
 return {page,stats:()=>({scrolls,wheels})};}
const pkg={posts:[{id:'p1',title:'A',utm:'https://example.test/utm',paragraphs:['story']}]};
(async()=>{
 const old=load(baseline),next=load(candidate),rows=[];
 let f=makePage('recover');await assert.rejects(old(f.page,pkg,{expectedCount:2}),/not attached/);rows.push({case:'baseline_detach',result:'EXPECTED_FAILURE',...f.stats()});
 f=makePage('recover');const v=await next(f.page,pkg,{expectedCount:2});assert.equal(v.complete,true);assert.equal(v.inventory.length,2);assert.equal(v.matches.length,1);assert.equal(v.matches[0].tumblrId,'111');assert.equal(f.stats().scrolls,2);rows.push({case:'candidate_detach_recovers_deduplicates',result:'PASS',inventory:v.inventory.length,matches:v.matches.length,...f.stats()});
 f=makePage('persistent');await assert.rejects(next(f.page,pkg,{expectedCount:2}),/not attached/);assert.equal(f.stats().scrolls,3);assert.equal(f.stats().wheels,0);rows.push({case:'persistent_detach_bounded_failure',result:'PASS',...f.stats()});
 f=makePage('recover');await assert.rejects(next(f.page,pkg,{expectedCount:3,maxPasses:2}),/REMOTE_INVENTORY_INCOMPLETE/);rows.push({case:'incomplete_scan_no_green_result',result:'PASS',...f.stats()});
 fs.writeFileSync(path.join(__dirname,'tumblr-tests.json'),JSON.stringify({status:'PASS',cases:rows,actualFunction:'cards',publisherExecuted:false,realBrowserProviderPublishCalls:0,installed:false},null,2)+'\n');console.log(JSON.stringify(rows));
})().catch(e=>{console.error(e.stack);process.exitCode=1});
