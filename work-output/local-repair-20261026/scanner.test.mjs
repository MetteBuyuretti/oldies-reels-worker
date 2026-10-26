import test from 'node:test';
import assert from 'node:assert/strict';
import {cards} from './budget-excerpt.mjs';
const pkg={posts:[1,2,3].map(n=>({id:'fixture-'+n,title:'Synthetic '+n,paragraphs:['Synthetic paragraph '+n],utm:'https://example.test/?fixture='+n}))};
const rows=pkg.posts.map((p,n)=>({title:p.title,paragraphs:p.paragraphs,url:'https://www.tumblr.com/oldiesradyo/'+(1001+n)+'/fixture',times:[{iso:'2026-10-26T10:00:00Z'}]}));
const ad={title:'Sponsored',paragraphs:[],url:'https://www.tumblr.com/otherblog/9000/ad',times:[]};
function fakePage(batches,{wrongFooter=false,wrongStory=false}={}){
 let pass=0,wheels=0;
 const list=()=>batches[Math.min(pass,batches.length-1)];
 function locator(rows){return {
  count:async()=>rows.length,first:()=>locator(rows.slice(0,1)),last:()=>locator(rows.slice(-1)),nth:i=>locator(rows.slice(i,i+1)),
  waitFor:async()=>{if(!rows.length)throw Error('NO_VISIBLE_ARTICLE');},
  scrollIntoViewIfNeeded:async()=>{},
  getAttribute:async name=>rows[0]?.[name]??null,
  allTextContents:async()=>rows.map(x=>x.text||''),
  innerText:async()=>rows[0]?.paragraphs?.join(' ')||'',
  getByRole:(role,options={})=>{
   const r=rows[0];if(role==='time')return locator(r?.times?.map(x=>({datetime:x.iso,text:x.title}))||[]);
   if(role==='link'&&options.name==='Kalıcı bağlantı')return locator(r?[{href:r.url}]:[]);
   if(role==='link'&&options.name==='https://oldiesradyo.com/'){
    const p=pkg.posts.find(x=>x.title===r?.title);return locator(p?[{href:wrongFooter?'https://example.com/':p.utm}]:[]);
   }
   throw Error('Unexpected fixture role '+role);
  },
  filter:({has})=>locator(rows.filter(r=>r.title===has.title).map(r=>wrongStory?{...r,paragraphs:['Changed story']}:r)),
 };}
 return {get wheels(){return wheels;},getByRole:(role,opts)=>role==='heading'?{title:opts.name}:locator(list()),mouse:{wheel:async()=>{wheels++;pass++;}},waitForTimeout:async()=>{}};
}


test('dynamic partial scan plus foreign sponsored card completes own inventory',async()=>{
 const page=fakePage([[rows[0],ad],[...rows,ad]]);const result=await cards(page,pkg,{expectedCount:3});
 assert.equal(page.wheels,1);assert.equal(result.inventory.length,3);assert.equal(result.matches.length,3);
});
test('generic queue timestamp does not become a publication target',async()=>{
 const result=await cards(fakePage([rows]),pkg,{expectedCount:3,kind:'queue'});
 assert.ok(result.inventory.every(x=>!x.scheduledAt&&!x.publishedAt&&x.timeSemantics==='UNVERIFIED_QUEUE_TIMESTAMP'));
});
test('wrong body is rejected',async()=>assert.rejects(cards(fakePage([rows],{wrongStory:true}),pkg,{expectedCount:3}),/REMOTE_STORY_MISMATCH/));
test('partial inventory reaches bounded fail-closed result',async()=>assert.rejects(cards(fakePage([[rows[0]]]),pkg,{expectedCount:3,maxPasses:2}),/REMOTE_INVENTORY_INCOMPLETE/));
