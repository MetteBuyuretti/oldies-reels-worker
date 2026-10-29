'use strict';
// Staging proposal only. The active tunnel/profile is never modified here.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const FILES=['tumblr_auto_news_v3.mjs','run_tumblr_auto.ps1','review-note.txt'];
const ALIASES=['TUMBLR_PUBLISHER','TUMBLR_LAUNCHER','TUMBLR_EDITORIAL_CONTROLLER'];
const MAX=200000;
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const same=(a,b)=>path.resolve(a).toLowerCase()===path.resolve(b).toLowerCase();
const schema=properties=>({type:'object',properties,required:Object.keys(properties),additionalProperties:false});
const file={type:'string',enum:FILES},alias={type:'string',enum:ALIASES};
const digest={type:'string',pattern:'^[0-9a-f]{64}$'};
const content={type:'string',maxLength:MAX};
const TOOLS=[
 ['list_project_files',{},'List only three pinned Tumblr source identities; no directory traversal.'],
 ['read_project_file',{alias},'Read one pinned Tumblr source through Commander; no arbitrary path/URL.'],
 ['create_staging_file',{file,content,expected_source_sha256:digest},'Create a new candidate only in the designated staging directory; refuses overwrite.'],
 ['read_staging_file',{file},'Read one allowed staging candidate.'],
 ['replace_staging_file',{file,content,expected_stage_sha256:digest},'Replace only a staging candidate when its current hash matches.'],
 ['check_staging_syntax',{file},'Parse a staging .mjs/.ps1 only with a fixed command; never execute candidate code.']
].map(([name,properties,description])=>({name,description,inputSchema:schema(properties),annotations:{readOnlyHint:/^(list|read|check)_/.test(name),destructiveHint:false,openWorldHint:false}}));
function validate(name,args){
 const tool=TOOLS.find(t=>t.name===name);if(!tool)throw Error('TOOL_DENIED');
 if(!args||Array.isArray(args)||typeof args!=='object')throw Error('ARGUMENTS_DENIED');
 const props=tool.inputSchema.properties;
 if(Object.keys(args).length!==Object.keys(props).length||Object.keys(args).some(k=>!Object.hasOwn(props,k)))throw Error('ARGUMENTS_DENIED');
 for(const [k,p] of Object.entries(props))if(typeof args[k]!==p.type||(p.enum&&!p.enum.includes(args[k]))||(p.pattern&&!new RegExp(p.pattern).test(args[k]))||(p.maxLength&&args[k].length>p.maxLength))throw Error('ARGUMENTS_DENIED');
}
function directory(p){
 if(!same(fs.realpathSync.native(p),p)||!fs.statSync(p).isDirectory())throw Error('ROOT_REPARSE_DENIED');
}
function read(p){
 if(!same(fs.realpathSync.native(p),p))throw Error('FILE_REPARSE_DENIED');
 const st=fs.lstatSync(p);if(!st.isFile()||st.isSymbolicLink()||st.size>MAX)throw Error('FILE_TYPE_OR_SIZE_DENIED');
 const raw=fs.readFileSync(p);if(raw.length>MAX||raw.includes(0)||!Buffer.from(raw.toString('utf8')).equals(raw))throw Error('FILE_FORMAT_DENIED');
 return raw;
}
function source(policy,key){
 if(!ALIASES.includes(key))throw Error('ARGUMENTS_DENIED');
 directory(policy.sourceRoot);
 const entry=policy.sources[key];if(!entry||!same(path.dirname(entry.path),policy.sourceRoot))throw Error('SOURCE_POLICY_DENIED');
 const raw=read(entry.path);if(hash(raw)!==entry.sha256)throw Error('SOURCE_CHANGED_DENIED');
 return {entry,raw};
}
function stage(policy,name,mustExist=true){
 if(!FILES.includes(name))throw Error('ARGUMENTS_DENIED');directory(policy.stagingRoot);
 const p=path.join(policy.stagingRoot,name);
 if(!same(path.dirname(p),policy.stagingRoot))throw Error('PATH_DENIED');
 if(fs.existsSync(p))read(p);else if(mustExist)throw Error('STAGING_FILE_MISSING');
 return p;
}
function pack(raw){return {sha256:hash(raw),bytes:raw.length,text:raw.toString('utf8')};}
function checkedContent(s){const raw=Buffer.from(s,'utf8');if(raw.length>MAX||raw.includes(0))throw Error('FILE_FORMAT_DENIED');return raw;}
function reply(data){return {content:[{type:'text',text:JSON.stringify(data)}]};}
async function callProject(name,args,policy,upstream){
 validate(name,args);
 if(name==='list_project_files')return reply({files:ALIASES.map(alias=>{const {raw}=source(policy,alias);return {alias,sha256:hash(raw),bytes:raw.length};})});
 if(name==='read_project_file'){
  const {entry,raw}=source(policy,args.alias);
  const result=await upstream.callTool({name:'read_file',arguments:{path:entry.path,isUrl:false,offset:0,length:3000}});
  const again=source(policy,args.alias).raw;
  const norm=s=>s.replace(/\r\n/g,'\n').trimEnd();
  if(!raw.equals(again)||result.isError||result.content?.length!==1||result.content[0].type!=='text'||!norm(result.content[0].text).endsWith(norm(raw.toString('utf8'))))throw Error('UPSTREAM_CONTENT_MISMATCH');
  return reply({alias:args.alias,...pack(raw)});
 }
 if(name==='read_staging_file')return reply({file:args.file,...pack(read(stage(policy,args.file)))});
 if(name==='create_staging_file'){
  const binding=args.file==='tumblr_auto_news_v3.mjs'?'TUMBLR_PUBLISHER':args.file==='run_tumblr_auto.ps1'?'TUMBLR_LAUNCHER':'TUMBLR_PUBLISHER';
  const {raw:original}=source(policy,binding);if(hash(original)!==args.expected_source_sha256)throw Error('PREIMAGE_SHA256_MISMATCH');
  const p=stage(policy,args.file,false),raw=checkedContent(args.content);
  const fd=fs.openSync(p,'wx');try{fs.writeFileSync(fd,raw);}finally{fs.closeSync(fd);}
  return reply({file:args.file,sha256:hash(raw),bytes:raw.length,scope:'STAGING_ONLY'});
 }
 if(name==='replace_staging_file'){
  const p=stage(policy,args.file),before=read(p);if(hash(before)!==args.expected_stage_sha256)throw Error('PREIMAGE_SHA256_MISMATCH');
  const raw=checkedContent(args.content),temporary=p+'.candidate-tmp';
  const fd=fs.openSync(temporary,'wx');try{fs.writeFileSync(fd,raw);}finally{fs.closeSync(fd);}
  // Synchronous CAS inside this single-process gateway; no claimed protection against a hostile OS user.
  if(hash(read(p))!==args.expected_stage_sha256){fs.unlinkSync(temporary);throw Error('PREIMAGE_SHA256_MISMATCH');}
  fs.renameSync(temporary,p);return reply({file:args.file,sha256:hash(raw),bytes:raw.length,scope:'STAGING_ONLY'});
 }
 const p=stage(policy,args.file);read(p);
 let result;
 const env=Object.fromEntries(['SystemRoot','WINDIR','TEMP','TMP'].filter(k=>process.env[k]).map(k=>[k,process.env[k]]));
 if(args.file.endsWith('.mjs'))result=spawnSync(policy.node,['--permission','--allow-fs-read='+policy.stagingRoot,'--check',p],{encoding:'utf8',timeout:10000,windowsHide:true,env});
 else if(args.file.endsWith('.ps1'))result=spawnSync(policy.powershell,['-NoProfile','-NonInteractive','-File',policy.syntaxHelper,'-Source',p],{encoding:'utf8',timeout:10000,windowsHide:true,env});
 else throw Error('SYNTAX_TYPE_DENIED');
 return reply({file:args.file,status:result.status===0?'SYNTAX_OK':'SYNTAX_ERROR',exitCode:result.status,signal:result.signal||null,executedCandidate:false});
}
module.exports={TOOLS,validate,source,stage,callProject,hash};
