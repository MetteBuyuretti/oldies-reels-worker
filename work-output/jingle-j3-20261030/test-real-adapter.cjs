'use strict';
// No browser, network or Python process: real adapter/producer/orchestration with strict doubles.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),crypto=require('node:crypto');
const LIVE=process.env.JINGLE_STAGE_ROOT || 'C:\\Users\\METE\\Oldies-Jingle-Factory\\backups\\WORK2-20261015-STATE-QC-RECOVERY\\FINAL-LIVE-ADAPTER-20261018';
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const patch=JSON.parse(fs.readFileSync(path.join(__dirname,'menu-wait-patch.json'),'utf8'));
const source=fs.readFileSync(path.join(LIVE,patch.source),'utf8');
const eol=source.includes('\r\n')?'\r\n':'\n';
const old=patch.old.replaceAll('\n',eol),replacement=patch.new.replaceAll('\n',eol);
assert.equal(source.split(old).length,2,'exact source anchor');
const candidate=source.replace(old,replacement);
assert.equal(crypto.createHash('sha256').update(candidate).digest('hex'),sha(path.join(__dirname,'candidate/gemini_jingle.staged.cjs')));
const snapshot=JSON.parse(fs.readFileSync(path.join(__dirname,'evidence/preimage.private.json'),'utf8'));
const fingerprint=p=>!fs.existsSync(p)?'MISSING':fs.statSync(p).isFile()?sha(p):'DIRECTORY_PRESENT';
for(const [p,h] of Object.entries(snapshot.protected))assert.equal(fingerprint(p),h,'preimage changed');
const root=fs.mkdtempSync(path.join(__dirname,'fixture-'));
const rows=[];
function load(sourceText,filename,requireMap,dirname){
 const module={exports:{}};
 const localRequire=name=>{
  if(Object.hasOwn(requireMap,name))return requireMap[name];
  assert(['node:fs','node:path','node:crypto'].includes(name),'unapproved dependency: '+name);
  return require(name);
 };
 vm.runInNewContext(sourceText,{require:localRequire,module,__dirname:dirname},{filename});
 return module.exports;
}
function makePage(kind){
 const calls=[];let clock=0,showAt=Infinity,text='fixture prompt',listener=null,submitted=false;
 const download={saveAs:async target=>{
  calls.push('download.saveAs');
  if(kind==='save-failure'){const e=Error('PRIVATE_ERROR_DO_NOT_EXPORT');e.code='EACCES';throw e;}
  fs.writeFileSync(target,Buffer.alloc(2048,70)); // deliberately NOT an MP3; never import this fixture
 }};
 function locator(type){
  const present=()=>type==='menu'?clock>=showAt:
   ['model','active-music','prompt','send'].includes(type)||type==='download'&&submitted;
  const loc={count:async()=>present()?1:0,first:()=>loc,
   isVisible:async()=>!!present(),isEnabled:async()=>true,
   innerText:async()=>type==='model'?'3.1 Pro':text,
   fill:async value=>{assert.equal(type,'prompt');text=value;},
   waitFor:async options=>{
    assert.equal(type,'menu');assert.equal(options.state,'visible');assert.equal(options.timeout,10000);
    calls.push('menu.waitFor.visible');
    if(showAt>clock+options.timeout){clock+=options.timeout;throw Error('PRIVATE_TIMEOUT_DO_NOT_EXPORT');}
    clock=Math.max(clock,showAt);assert(present());
   },
   click:async()=>{
    assert(present(),'clicked a missing fixture locator');calls.push(type+'.click');
    if(type==='send'){submitted=true;text='';}
    if(type==='download')showAt=kind==='missing-menu'?Infinity:clock+(kind==='delayed-menu'?75:0);
    if(type==='menu'){
     assert(listener,'download listener must precede menu click');
     if(kind==='event-timeout')listener.reject(Error('PRIVATE_TIMEOUT_DO_NOT_EXPORT'));
     else listener.resolve(download);
    }
   }
  };return loc;
 }
 const page={
  getByRole:(role,{name})=>{
   const regex=String(name);
   if(role==='menuitem')return locator('menu');
   if(role==='button'&&regex.includes('Mod seçiciyi'))return locator('model');
   if(role==='button'&&regex.includes('Müzik öğesinin'))return locator('active-music');
   if(role==='button'&&regex.includes('Mesaj gönder'))return locator('send');
   if(role==='button'&&regex.includes('Parçayı indir'))return locator('download');
   throw Error('UNEXPECTED_FIXTURE_ROLE');
  },
  locator:selector=>{
   const type=selector.includes('contenteditable')||selector==='textarea'?'prompt':'absent';
   const loc=locator(type);loc.filter=()=>loc;return loc;
  },
  url:()=> 'https://fixture.invalid/app/fake',
  waitForTimeout:async ms=>{clock+=ms;},
  waitForEvent:(name,options)=>{
   assert.equal(name,'download');assert.equal(options.timeout,30000);calls.push('download.listen');
   return new Promise((resolve,reject)=>{listener={resolve,reject};});
  }
 };
 return {page,calls,get clock(){return clock;}};
}
async function run(variant,kind,{reuse,slot='morning'}={}){
 const stage=reuse?.stage||path.join(root,variant+'-'+kind);
 const producer=path.join(stage,'producer'),factoryRoot=path.join(stage,'runtime/factory'),producerRoot=path.join(stage,'runtime/producer');
 fs.mkdirSync(producer,{recursive:true});fs.mkdirSync(path.join(factoryRoot,'config'),{recursive:true});fs.mkdirSync(producerRoot,{recursive:true});
 fs.writeFileSync(path.join(factoryRoot,'config/settings.json'),'{}');
 const contract=load(fs.readFileSync(path.join(LIVE,'producer/producer_contract.cjs'),'utf8'),'actual-producer.cjs',{},producer);
 const ui=load(variant==='baseline'?source:candidate,'actual-adapter.cjs',{'./producer_contract.cjs':contract},producer);
 let boundaryCalls=0,guardCalls=0;
 const child={spawnSync:(_binary,args)=>{
  assert.equal(args[0],'-B');
  if(args.some(x=>String(x).endsWith('recovery_probe.py'))){guardCalls++;return {status:0,stdout:JSON.stringify({guard:kind==='guard-block'?'REVIEW_REQUIRED':'CLEAR',root:factoryRoot})};}
  assert(args.some(x=>String(x).endsWith('import_web_music.py')),'no Factory/preflight subprocess allowed');
  boundaryCalls++;
  const arg=key=>args[args.indexOf(key)+1];
  const status=JSON.parse(fs.readFileSync(arg('--status-file'),'utf8'));
  for(const key of ['date','slot','job-id','sha256'])assert.equal(arg('--'+key),status[key.replace('-','_')]);
  assert.equal(arg('--root'),factoryRoot);assert.equal(arg('--producer-root'),producerRoot);
  // Deliberately stop before the real importer: no import, receipt, QC, Factory or mix.
  throw Error('IMPORT_BOUNDARY_SENTINEL');
 }};
 const orchestration=load(fs.readFileSync(path.join(LIVE,'producer/staged_orchestration.cjs'),'utf8'),
  'actual-orchestration.cjs',{'./producer_contract.cjs':contract,'./gemini_jingle.staged.cjs':ui,'node:child_process':child},producer);
 const double=makePage(kind);let error;
 try{await orchestration.preparePageForHumanReview({page:double.page,prompt:'non-production fixture',factoryRoot,producerRoot,slot,python:'FORBIDDEN_REAL_PROCESS'});}
 catch(e){error=e.message;}
 const expected=kind==='guard-block'?'STAGED_GUARD_REVIEW_REQUIRED':kind==='duplicate-raw'?'WEB_DOWNLOAD_ERROR':
   kind==='delayed-menu'&&variant==='baseline'||['missing-menu','event-timeout','save-failure'].includes(kind)?'WEB_DOWNLOAD_ERROR':'IMPORT_REVIEW_REQUIRED';
 assert.equal(error,expected);
 const jobs=fs.readdirSync(producerRoot).filter(x=>x.startsWith('web-'));
 const job=jobs.map(j=>JSON.parse(fs.readFileSync(path.join(producerRoot,j,'status.json'),'utf8'))).find(s=>s.slot===slot);
 const reached=['immediate-menu','delayed-menu'].includes(kind)&&!(variant==='baseline'&&kind==='delayed-menu');
 assert.equal(boundaryCalls,reached?1:0);
 const claimsDir=path.join(producerRoot,'operation-claims');
 const claimCount=fs.existsSync(claimsDir)?fs.readdirSync(claimsDir).length:0;
 if(kind==='guard-block'){assert.equal(double.calls.length,0);assert.equal(claimCount,0);}
 else{
  assert.equal(job.retry_generation,reached?undefined:false); // DOWNLOADED has no retry field
  assert.equal(job.status,reached?'DOWNLOADED':'DOWNLOAD_ERROR');
  for(const j of jobs)assert(!fs.existsSync(path.join(producerRoot,j,'awaiting-human-review.json')));
  const prior=double.calls.length;
  await assert.rejects(orchestration.preparePageForHumanReview({page:double.page,prompt:'non-production fixture',factoryRoot,producerRoot,slot,python:'FORBIDDEN_REAL_PROCESS'}),/DAY_SLOT_REVIEW_REQUIRED/);
  assert.equal(double.calls.length,prior,'blind retry must perform no page action');
  for(const name of fs.readdirSync(claimsDir))assert.equal(JSON.parse(fs.readFileSync(path.join(claimsDir,name))).state,'RESERVED_REVIEW_REQUIRED');
 }
 if(reached)assert(double.calls.indexOf('download.listen')<double.calls.indexOf('menu.click'));
 if(kind==='delayed-menu'&&variant==='candidate')assert(double.calls.includes('menu.waitFor.visible'));
 if(kind==='missing-menu')assert(!double.calls.includes('download.listen'));
 if(kind==='duplicate-raw')assert.equal(fs.readdirSync(path.join(producerRoot,'raw-claims')).length,1);
 if(job)assert(!JSON.stringify(job).includes('PRIVATE_'));
 rows.push({variant,scenario:kind,requiredTransition:['immediate-menu','delayed-menu'].includes(kind)?'DOWNLOADED_BEFORE_IMPORT':'REJECT_WITHOUT_IMPORT',
  observedStatus:job?.status||'NO_JOB',error,importBoundaryStubCalls:boundaryCalls,
  realProviderBrowserDownloadImportFactoryMixCalls:0,claimCount,blindRetryBlocked:kind==='guard-block'?null:true,
  virtualMenuWaitMs:kind==='delayed-menu'?75:kind==='missing-menu'?10000:0,
  regressionObserved:variant==='baseline'&&kind==='delayed-menu',
  result:variant==='baseline'&&kind==='delayed-menu'?'EXPECTED_BASELINE_FAILURE':'PASS'});
 return {stage};
}
(async()=>{
 await run('baseline','delayed-menu');await run('candidate','delayed-menu');
 await run('baseline','immediate-menu');const success=await run('candidate','immediate-menu');
 for(const kind of ['missing-menu','event-timeout','save-failure','guard-block'])await run('candidate',kind);
 await run('candidate','duplicate-raw',{reuse:success,slot:'evening'});
 for(const [p,h] of Object.entries(snapshot.protected))assert.equal(fingerprint(p),h,'protected postimage changed');
 const result={at:new Date().toISOString(),status:'PASS_REAL_ADAPTER_FOCUSED_REGRESSION',
  cases:rows,sourceAdapterSha256:sha(path.join(LIVE,patch.source)),
  candidateAdapterSha256:crypto.createHash('sha256').update(candidate).digest('hex'),
  realFunctions:'preparePageForHumanReview -> prepareForHumanReview -> produce -> createUiAdapter methods',
  installed:false,historicalRootCauseProven:false,protectedPrePostUnchanged:true,
  actualBrowserProviderImportFactoryMixCalls:0,syntheticRawIsAudio:false};
 fs.writeFileSync(path.join(__dirname,'evidence/real-adapter-tests.json'),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
