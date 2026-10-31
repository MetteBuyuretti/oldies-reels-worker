'use strict';
// Read-only inventory on one temporary page; no launcher, journal, editor, submission, or token refresh.
const path=require('node:path'),crypto=require('node:crypto'),fs=require('node:fs');
const {pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/METE/oldies-jingle-automation/node_modules/playwright-core');
const installed=process.env.OLDIES_INVENTORY_INSTALLED==='1';
const candidate=installed?'C:/Users/METE/oldies-jingle-automation/tumblr_auto_news_v3.mjs':path.resolve(__dirname,'../canonical-tumblr-20261031/candidate/tumblr_auto_news_v3.mjs');
if(crypto.createHash('sha256').update(fs.readFileSync(candidate)).digest('hex')!=='9e44f9af845c889c0079ba5cc956ea0e5be08b825050cb9aea6fa5670032c622')throw Error('PUBLISHER_HASH_CHANGED');
const resultPath=path.join(__dirname,'live-cards.json');
(async()=>{
 let page;try{
  const {cards}=await import(pathToFileURL(candidate).href);
  const browser=await chromium.connectOverCDP('http://127.0.0.1:9243');
  const contexts=browser.contexts();if(contexts.length!==1)throw Error('EXPECTED_ONE_EXISTING_BROWSER_CONTEXT');
  page=await contexts[0].newPage();
  await page.goto('https://www.tumblr.com/blog/oldiesradyo',{waitUntil:'domcontentloaded',timeout:30000});
  if(new URL(page.url()).hostname!=='www.tumblr.com'||!new URL(page.url()).pathname.startsWith('/blog/oldiesradyo'))throw Error('TUMBLR_AUTH_OR_ROUTE_UNAVAILABLE');
  const count=page.getByRole('link',{name:/^Gönderiler \d+/});await count.waitFor({state:'visible',timeout:15000});
  const label=await count.innerText(),expected=Number(label.match(/\d+/)?.[0]);if(!Number.isSafeInteger(expected))throw Error('POST_COUNT_UNAVAILABLE');
  const observed=await cards(page,{posts:[]},{expectedCount:expected});
  const ids=observed.inventory.map(x=>x.tumblrId);if(new Set(ids).size!==ids.length||ids.length!==expected)throw Error('INVENTORY_COUNT_MISMATCH');
  const result={status:'PASS',at:new Date().toISOString(),expected,unique_ids:ids.length,ids_sha256:crypto.createHash('sha256').update(ids.slice().sort().join('\n')).digest('hex'),complete:observed.complete,candidate_sha256:crypto.createHash('sha256').update(fs.readFileSync(candidate)).digest('hex'),uses_installed_candidate:installed,publisher_main_called:false,queue_publish_clicks:0};
  fs.writeFileSync(resultPath,JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }catch(e){const result={status:'READ_FAILED',at:new Date().toISOString(),error:String(e.message).slice(0,250),publisher_main_called:false,queue_publish_clicks:0};fs.writeFileSync(resultPath,JSON.stringify(result,null,2));console.log(JSON.stringify(result));process.exitCode=1;}
 finally{if(page)await page.close().catch(()=>{});setTimeout(()=>process.exit(process.exitCode||0),100);}
})();
