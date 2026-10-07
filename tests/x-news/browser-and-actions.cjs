const assert = require('node:assert/strict');
const {execFileSync} = require('node:child_process');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const php = process.env.PHP_BINARY || 'php';
const phpArgs = JSON.parse(process.env.PHP_TEST_ARGS || '[]');
let passed = 0;
function check(condition, name) { assert.ok(condition, name); passed++; }
function action(name) { return JSON.parse(execFileSync(php, [...phpArgs, path.join(__dirname, 'action.php'), name], {encoding:'utf8'})); }
function x(data) { return JSON.parse(data.rows['1'].metadata).x_news; }
const routes = {
 posted:'ALREADY_POSTED_OR_RESERVED_NO_RETRY',unapproved:'FRESH_EDITORIAL_APPROVAL_REQUIRED',changed_news:'NEWS_CHANGED_REAPPROVAL_REQUIRED',
 unpublished:'FRESH_EDITORIAL_APPROVAL_REQUIRED',sensitive:'FRESH_EDITORIAL_APPROVAL_REQUIRED',duplicate:'DUPLICATE_POST_BLOCKED',
 api_disabled:'API_DISABLED_ZERO_COST_MODE',api_budget_missing:'PAID_API_NOT_AUTHORIZED',api_identity_missing:'VERIFY_EXPECTED_X_ACCOUNT_FIRST',
 confirm_fake_url:'VALID_X_POST_URL_REQUIRED',confirm_unreserved:'NOT_AWAITING_CONFIRMATION',
 cancel_uncertain:'ONLY_UNUSED_WEB_INTENT_CAN_CANCEL',retry_uncertain:'ALREADY_POSTED_OR_RESERVED_NO_RETRY',
 retry_early:'RETRY_NOT_SAFE_OR_TOO_EARLY',missing_english_review:'HOLD_VERIFY_TEXT_AND_EVIDENCE',
 stale_editor:'EDITOR_STATE_CHANGED_RELOAD',confirm_duplicate_id:'X_POST_ID_ALREADY_RECORDED',
 import_old:'RECENT_NEWS_REQUIRED',import_page:'PUBLISHED_EN_NEWS_REQUIRED',import_draft:'PUBLISHED_EN_NEWS_REQUIRED',
 import_tr:'PUBLISHED_EN_NEWS_REQUIRED',import_project_category:'NEWS_CATEGORY_AND_OLDIES_URL_REQUIRED',
 import_same_source_other_post:'SOURCE_ALREADY_LINKED_TO_OTHER_EN_POST'
};
for (const [scenario,error] of Object.entries(routes)) { const result=action(scenario);check(result.redirect.includes(error)&&result.calls===0,scenario); }
for (const [scenario,error] of Object.entries({no_confirm:'CONFIRMATION_REQUIRED',unauthorized:'FORBIDDEN',bad_nonce:'BAD_NONCE'})) { const result=action(scenario);check(result.error===error&&result.calls===0,scenario); }
const intent=action('intent');check(intent.redirect.startsWith('https://twitter.com/intent/tweet?text=')&&x(intent).status==='AWAITING_CONFIRMATION'&&intent.calls===0,'Free composer never fakes posted status');
const confirmed=action('confirm');check(x(confirmed).status==='POSTED'&&x(confirmed).post_id==='123456789'&&confirmed.calls===0,'Manual URL confirmation');
const canceled=action('cancel');check(x(canceled).status==='READY'&&!x(canceled).approved_by,'Abandoned composer requires fresh approval');
const retried=action('retry_failed');check(x(retried).status==='VERIFIED'&&!x(retried).approved_by,'Definitive failure returns to approval');
check(x(action('approve')).status==='READY','Explicit approval');
check(x(action('reject')).status==='REJECTED','Reject');
const saved=action('save');check(x(saved).status==='VERIFIED'&&!x(saved).approved_by&&saved.rows['1'].status==='PUBLISHED','Edit resets approval without changing article state');
const importedExisting=action('import_existing');check(Object.keys(importedExisting.rows).length===1&&importedExisting.rows['1'].status==='PUBLISHED','Existing WordPress import does not duplicate or alter row');
const imported=action('import_new');check(Object.keys(imported.rows).length===2&&imported.rows['2'].en_post_id===20&&imported.rows['2'].status==='PENDING'&&imported.calls===0,'Fresh English news imports into shared queue without posting');
const sources=action('sources');check(sources.sources.length===22&&sources.sources[0].name==='Keep custom name'&&sources.sources.every(s=>s.is_active===0)&&sources.calls===0,'Catalog appends missing sources without changing existing configuration or making X calls');
for (const [scenario,status] of Object.entries({api_success:'POSTED',api_timeout:'OUTCOME_UNKNOWN',api_429:'FAILED'})) { const result=action(scenario);check(result.calls===1&&x(result).status===status&&x(result).spend_reservations[0].usd===0.2,scenario); }
// Execute the shipped browser bundle, not a separate copy of the counter.
let callback;
const input = {value:'🎸 Read more → https://oldiesradyo.com/en/'+ 'a'.repeat(800), addEventListener:(event,fn)=>callback=fn,setCustomValidity:function(v){this.invalid=v;}};
const output={textContent:'',style:{}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../wordpress/oldies-x-news-bridge/assets/editor.js'),'utf8'),{document:{getElementById:id=>id==='oldies-x-text'?input:output}});
check(output.textContent.startsWith('39/280')&&!input.invalid,'Shipped official browser counter: emoji + long URL');
input.value='a'.repeat(281);callback();check(output.textContent.startsWith('281/280')&&!!input.invalid,'Browser rejects oversize');
input.value='👨‍👩‍👧‍👦';callback();check(output.textContent.startsWith('2/280')&&!input.invalid,'Official family emoji handling');
input.value='Çığ Şölen İstanbul';callback();check(output.textContent.startsWith('18/280')&&!input.invalid,'Browser Turkish Unicode');
const render=scenario=>JSON.parse(execFileSync(php,[...phpArgs,path.join(__dirname,'render.php'),scenario],{encoding:'utf8'}));
const ready=render('ready');check(ready.html.includes('Publish: ücretsiz')&&!ready.html.includes('Publish via API')&&ready.network_calls===0,'Ready screen shows free publication and no paid action');
const candidate=render('candidate');check(!candidate.html.includes('Publish: ücretsiz')&&candidate.html.includes('NEWS CANDIDATE')&&candidate.network_calls===0,'Candidate has no Publish button');
const list=render('list');check(list.html.includes('WordPress haberini mevcut haber kuyruğuna bağla')&&list.network_calls===0,'WP import available in X News');
console.log(JSON.stringify({passed,failed:0,network:'mock only'},null,2));
