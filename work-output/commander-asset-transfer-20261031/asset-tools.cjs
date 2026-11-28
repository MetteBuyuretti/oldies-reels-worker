'use strict';
// Candidate module only. Fixed policy and executables are supplied by the gateway, never by caller.
const {spawnSync}=require('node:child_process');
const TOOLS=[
 {name:'import_approved_image',description:'Transfer a manifest-approved image into the single configured asset root; never overwrite a differing file.',inputSchema:{type:'object',properties:{asset_id:{type:'string'},name:{type:'string'}},required:['asset_id','name'],additionalProperties:false},annotations:{readOnlyHint:false,destructiveHint:false,openWorldHint:false}},
 {name:'verify_asset_file',description:'Validate one named image in the configured asset root and return its SHA256, byte count and dimensions.',inputSchema:{type:'object',properties:{name:{type:'string'}},required:['name'],additionalProperties:false},annotations:{readOnlyHint:true,destructiveHint:false,openWorldHint:false}},
 {name:'read_asset_receipt',description:'Recompute and return a receipt from the existing named image in the configured asset root.',inputSchema:{type:'object',properties:{name:{type:'string'}},required:['name'],additionalProperties:false},annotations:{readOnlyHint:true,destructiveHint:false,openWorldHint:false}}
];
function createAssetTools(policy,runner=spawnSync){
 async function call(name,args){
  const spec=TOOLS.find(t=>t.name===name);if(!spec)throw Error('TOOL_DENIED');
  if(!args||typeof args!=='object'||Array.isArray(args)||Object.keys(args).length!==spec.inputSchema.required.length||spec.inputSchema.required.some(k=>typeof args[k]!=='string')||Object.keys(args).some(k=>!spec.inputSchema.required.includes(k)))throw Error('ARGUMENTS_DENIED');
  const request={operation:name==='import_approved_image'?'transfer':'inspect',name:args.name,asset_id:args.asset_id,policy:{root:policy.root,sources:policy.sources}};
  const env=Object.fromEntries(['SystemRoot','WINDIR','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE'].filter(k=>process.env[k]).map(k=>[k,process.env[k]]));
  const r=runner(policy.python,['-B',policy.helper],{input:JSON.stringify(request),encoding:'utf8',timeout:45000,windowsHide:true,env,shell:false,maxBuffer:65536});
  if(r.error||r.signal||!Number.isInteger(r.status))throw Error('ASSET_HELPER_UNAVAILABLE');
  let result;try{result=JSON.parse(r.stdout)}catch{throw Error('ASSET_HELPER_UNAVAILABLE')}
  if(r.status!==0||result.error)throw Error('ASSET_OPERATION_DENIED');
  if(name==='read_asset_receipt')result.receipt_kind='RECOMPUTED_FROM_EXISTING_FILE';
  return {content:[{type:'text',text:JSON.stringify(result)}]};
 }
 return {TOOLS:TOOLS.map(t=>({...t,description:t.description+' Asset root: '+policy.root+'.'})),call};
}
module.exports={TOOLS,createAssetTools};
