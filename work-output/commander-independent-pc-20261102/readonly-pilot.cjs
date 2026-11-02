'use strict';
// Isolated, fail-closed first pilot. DO NOT put into the running gateway without
// a local preimage/policy review and real Work-to-Windows acceptance.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawnSync } = require('node:child_process');
const { TextDecoder } = require('node:util');

const MAX_TEXT = 64 * 1024;
const MAX_ENTRIES = 100;
const DENIED_PART = /^(?:\..*|secrets?|credentials?|tokens?|id_rsa|id_ed25519|.*\.(?:pem|pfx|key|kdbx))$/i;
const sha256 = b => crypto.createHash('sha256').update(b).digest('hex');
const same = (a, b) => process.platform === 'win32'
  ? path.normalize(a).toLowerCase() === path.normalize(b).toLowerCase()
  : path.normalize(a) === path.normalize(b);
const within = (root, target) => {
  if (same(root,target)) return true;
  const base=path.normalize(root)+path.sep;
  return process.platform==='win32' ? target.toLowerCase().startsWith(base.toLowerCase()) : target.startsWith(base);
};
const reply = value => ({ content: [{type: 'text', text: JSON.stringify(value)}] });
function ensure(condition, code) { if (!condition) throw Error(code); }

function relativeSegments(input, allowRoot = false) {
  ensure(typeof input === 'string' && input.length <= 280 && !input.includes('\0'), 'PATH_DENIED');
  if (input === '' && allowRoot) return [];
  ensure(input !== '' && !path.isAbsolute(input) && !path.win32.isAbsolute(input) && !input.includes(':'), 'PATH_DENIED');
  const parts = input.split(/[\\/]/);
  ensure(parts.length <= 16 && parts.every(p => p && p !== '.' && p !== '..' && !DENIED_PART.test(p)), 'PATH_DENIED');
  return parts;
}
function realFile(f, kind) {
  const absolute = path.resolve(f);
  const st = fs.lstatSync(absolute);
  ensure(!st.isSymbolicLink() && (kind === 'directory' ? st.isDirectory() : st.isFile()), 'FILE_TYPE_DENIED');
  ensure(same(fs.realpathSync.native(absolute), absolute), 'REPARSE_DENIED');
  return {absolute, st};
}
function createPilot(policy, options = {}) {
  const runner = options.runner || spawnSync;
  const platform = options.platform || process.platform;
  // Must come from actual validated upstream get_config, not from an external MCP argument.
  const allowed = options.allowedDirectories;
  ensure(Array.isArray(allowed) && allowed.length > 0 && allowed.every(x => typeof x === 'string'), 'UPSTREAM_CONFIG_REQUIRED');
  ensure(policy && typeof policy === 'object' && policy.roots && !Array.isArray(policy.roots), 'POLICY_REQUIRED');
  const roots = Object.entries(policy.roots);
  ensure(roots.length === 1 && roots.every(([id, dir]) => /^[a-z][a-z0-9_-]{1,35}$/i.test(id) && typeof dir === 'string'), 'PILOT_SCOPE_DENIED');
  const rootMap = {};
  for (const [id, dir] of roots) {
    const {absolute} = realFile(dir, 'directory');
    ensure(allowed.some(base => within(path.resolve(base), absolute)), 'UPSTREAM_DIRECTORY_DENIED');
    rootMap[id] = absolute;
  }
  const names = Object.keys(rootMap);
  const props = (extra = {}) => ({type:'object',properties:{project:{type:'string',enum:names},...extra},required:['project',...Object.keys(extra)],additionalProperties:false});
  const relPath = {type:'string',maxLength:280};
  const TOOLS = [
    {name:'pilot_list_directory',description:'List only a configured pilot project directory (never hidden files).',inputSchema:props({relative_path:relPath})},
    {name:'pilot_read_text',description:'Read a small, non-hidden UTF-8 pilot file with SHA-256.',inputSchema:props({relative_path:relPath})},
    {name:'pilot_powershell_info',description:'Run ONLY pinned Windows PowerShell version/current-folder query.',inputSchema:props()}
  ];
  const validate = (name, args) => {
    const t = TOOLS.find(t => t.name === name);
    ensure(t && args && typeof args === 'object' && !Array.isArray(args), 'TOOL_DENIED');
    const required = t.inputSchema.required;
    ensure(Object.keys(args).length === required.length && required.every(k => Object.hasOwn(args, k)), 'ARGUMENTS_DENIED');
    ensure(typeof args.project === 'string' && Object.hasOwn(rootMap,args.project), 'PROJECT_DENIED');
    if (name !== 'pilot_powershell_info') ensure(typeof args.relative_path === 'string', 'PATH_DENIED');
  };
  function resolveInProject(project, rel, kind, allowRoot = false) {
    const root = rootMap[project];
    const parts = relativeSegments(rel, allowRoot);
    const target = path.resolve(root, ...parts);
    ensure(within(root, target), 'PATH_DENIED');
    // Check each component; no symbolic links/junctions or any root escape.
    for (let i = 1; i <= parts.length; i++) realFile(path.resolve(root,...parts.slice(0,i)), i === parts.length ? kind : 'directory');
    return parts.length ? realFile(target,kind) : realFile(root,kind);
  }
  async function call(name, args) {
    validate(name,args);
    if (name === 'pilot_list_directory') {
      const {absolute} = resolveInProject(args.project, args.relative_path, 'directory', true);
      const all = fs.readdirSync(absolute, {withFileTypes:true});
      const safe = all.filter(d => !DENIED_PART.test(d.name) && !d.isSymbolicLink())
        .slice(0,MAX_ENTRIES).map(d => ({name:d.name,type:d.isDirectory()?'directory':d.isFile()?'file':'other'}));
      return reply({status:'READ_ONLY',project:args.project,entries:safe,truncated:all.length > MAX_ENTRIES});
    }
    if (name === 'pilot_read_text') {
      const {absolute,st} = resolveInProject(args.project,args.relative_path,'file');
      ensure(st.size <= MAX_TEXT,'FILE_TOO_LARGE');
      const bytes = fs.readFileSync(absolute);
      ensure(bytes.length <= MAX_TEXT && !bytes.includes(0),'FILE_FORMAT_DENIED');
      let text;
      try { text = new TextDecoder('utf-8',{fatal:true}).decode(bytes); } catch { throw Error('FILE_FORMAT_DENIED'); }
      return reply({status:'READ_ONLY',project:args.project,bytes:bytes.length,sha256:sha256(bytes),text});
    }
    // No caller-selected command, arguments, cwd, stdin, env, or shell.
    ensure(platform === 'win32','WINDOWS_ONLY');
    ensure(typeof policy.powershellExe === 'string' && /^[a-f0-9]{64}$/.test(policy.powershellSha256||''),'EXE_PIN_REQUIRED');
    const exe = realFile(policy.powershellExe,'file').absolute;
    ensure(sha256(fs.readFileSync(exe)) === policy.powershellSha256, 'EXE_CHANGED_DENIED');
    const fixedArgs=['-NoLogo','-NoProfile','-NonInteractive','-Command','$PSVersionTable.PSVersion.ToString(); (Get-Location).Path'];
    const result = runner(exe,fixedArgs,{shell:false,cwd:rootMap[args.project],timeout:8000,encoding:'utf8',maxBuffer:8192,windowsHide:true,
      env:Object.fromEntries(['SystemRoot','WINDIR','TEMP','TMP'].filter(k=>process.env[k]).map(k=>[k,process.env[k]]))});
    ensure(!result.error && !result.signal && Number.isInteger(result.status),'COMMAND_NOT_COMPLETED');
    return reply({status:result.status===0?'COMPLETED':'FAILED',exitCode:result.status,stdout:(result.stdout||'').slice(0,2000),stderr:(result.stderr||'').slice(0,500)});
  }
  return {TOOLS,call};
}
module.exports = { createPilot, relativeSegments };
