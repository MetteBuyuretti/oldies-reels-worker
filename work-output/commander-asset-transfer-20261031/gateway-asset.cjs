'use strict';
// This separate gateway never changes Desktop Commander or Codex configuration.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { createRequire } = require('node:module');
const { pathToFileURL } = require('node:url');
const {createAssetTools} = require('./asset-tools.cjs');

let projectTools;
const FILE_ALIAS = 'OLDIES-ETSY-REDACTED-REPORT';
const MAX_BYTES = 262144;
const PUBLIC_TOOL = Object.freeze({
  name: 'read_file',
  description: 'Read the previously approved redacted OLDIES Etsy report. This is a historical review copy, not current production health. Only the fixed file alias is accepted; no paths, URLs or commands.',
  inputSchema: { type: 'object', properties: { file: { type: 'string', enum: [FILE_ALIAS] } }, required: ['file'], additionalProperties: false },
  annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false }
});
const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const normalize = s => s.replace(/\r\n/g, '\n').trimEnd();
const samePath = (a, b) => path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase();

function validateCall(params) {
  if (!params || params.name !== 'read_file') throw new Error('TOOL_DENIED');
  const args = params.arguments;
  if (!args || Array.isArray(args) || typeof args !== 'object' || Object.keys(args).length !== 1 || args.file !== FILE_ALIAS) throw new Error('ARGUMENTS_DENIED');
}

function readPinnedFile(policy) {
  const root = path.resolve(policy.root);
  const file = path.resolve(policy.file);
  if (!samePath(fs.realpathSync.native(root), root)) throw new Error('ROOT_REPARSE_DENIED');
  if (!file.toLowerCase().startsWith(root.toLowerCase() + path.sep)) throw new Error('PATH_DENIED');
  if (!samePath(fs.realpathSync.native(file), file)) throw new Error('FILE_REPARSE_DENIED');
  const stat = fs.lstatSync(file);
  if (stat.isSymbolicLink() || !stat.isFile() || stat.size > MAX_BYTES) throw new Error('FILE_TYPE_OR_SIZE_DENIED');
  const bytes = fs.readFileSync(file);
  if (bytes.length > MAX_BYTES || sha256(bytes) !== policy.fileSHA256) throw new Error('FILE_CHANGED_DENIED');
  const text = bytes.toString('utf8');
  if (text.includes('\u0000') || text.split(/\r?\n/).length > 900) throw new Error('FILE_FORMAT_DENIED');
  return text;
}

async function callReadOnly(params, policy, upstream) {
  validateCall(params); // Denied tools/arguments never reach the upstream MCP.
  const before = readPinnedFile(policy);
  const result = await upstream.callTool({ name: 'read_file', arguments: { path: policy.file, isUrl: false, offset: 0, length: 1000 } });
  const after = readPinnedFile(policy);
  if (before !== after || result.isError || !Array.isArray(result.content) || result.content.length !== 1 || result.content[0].type !== 'text') throw new Error('UPSTREAM_RESULT_DENIED');
  const received = normalize(result.content[0].text);
  const approved = normalize(after);
  if (!approved || !received.endsWith(approved)) throw new Error('UPSTREAM_CONTENT_MISMATCH');
  // Return only the verified suffix read through Commander, never upstream metadata.
  const verifiedBody = received.slice(received.length - approved.length);
  return { content: [{ type: 'text', text: `[${FILE_ALIAS}; historical redacted review copy; SHA256 ${policy.fileSHA256}]\n\n${verifiedBody}` }] };
}

async function main(policyPath) {
  if (!policyPath) throw new Error('POLICY_REQUIRED');
  const policy = JSON.parse(fs.readFileSync(policyPath, 'utf8').replace(/^\uFEFF/, ''));
  // Runtime control-plane credentials must not enter Commander child processes.
  for (const name of Object.keys(process.env)) if (/^(CONTROL_PLANE_|OPENAI_|AZURE_OPENAI_|GITHUB_|GH_TOKEN$)/i.test(name)) delete process.env[name];
  for (const pinned of policy.pinnedSources) if (sha256(fs.readFileSync(pinned.path)) !== pinned.sha256) throw new Error('SOURCE_CHANGED_DENIED');
  projectTools=require('./project-tools.cjs');
  readPinnedFile(policy);
  const sdk = createRequire(policy.sdkAnchor);
  const { Server } = sdk('@modelcontextprotocol/sdk/server/index.js');
  const { StdioServerTransport } = sdk('@modelcontextprotocol/sdk/server/stdio.js');
  const { Client } = sdk('@modelcontextprotocol/sdk/client/index.js');
  const { StdioClientTransport } = sdk('@modelcontextprotocol/sdk/client/stdio.js');
  const { ListToolsRequestSchema, CallToolRequestSchema, McpError, ErrorCode } = sdk('@modelcontextprotocol/sdk/types.js');
  const upstreamTransport = new StdioClientTransport({ command: policy.command, args: policy.args, env: policy.commanderEnv, cwd: policy.root, stderr: 'ignore' });
  const upstream = new Client({ name: 'oldies-readonly-gateway', version: '1.0.0' }, { capabilities: {} });
  await upstream.connect(upstreamTransport);
  const configResult = await upstream.callTool({ name: 'get_config', arguments: {} });
  let wrapper = configResult.structuredContent;
  if (!wrapper) for (const block of configResult.content ?? []) if (block.type === 'text') { try { wrapper = JSON.parse(block.text); break; } catch {} }
  const actualConfig = wrapper?.config ?? wrapper;
  if (configResult.isError || actualConfig?.version !== '0.3.0' || actualConfig.telemetryEnabled !== false || !Array.isArray(actualConfig.allowedDirectories) || actualConfig.allowedDirectories.length !== policy.expectedDirectories.length || !actualConfig.allowedDirectories.every(p=>policy.expectedDirectories.some(q=>samePath(p,q)))) {
    await upstream.close();
    throw new Error('UPSTREAM_POLICY_MISMATCH');
  }
  const assets = createAssetTools(policy.asset);
  const server = new Server({ name: 'oldies-commander-project-staging-proposal', version: '1.1.0-candidate' }, { capabilities: { tools: {} }, instructions: 'Review candidate: pinned Tumblr reads and designated staging only. No installed source writes, general shell, URL or production health acceptance.' });
  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: [PUBLIC_TOOL,...projectTools.TOOLS,...assets.TOOLS] }));
  server.setRequestHandler(CallToolRequestSchema, async request => {
    try {
      if(assets.TOOLS.some(t=>t.name===request.params.name))return await assets.call(request.params.name,request.params.arguments);
      if(projectTools.TOOLS.some(t=>t.name===request.params.name))return await projectTools.callProject(request.params.name,request.params.arguments,policy.project,upstream);
      return await callReadOnly(request.params, policy, upstream);
    }
    catch (error) {
      const safe = ['TOOL_DENIED', 'ARGUMENTS_DENIED', 'ROOT_REPARSE_DENIED', 'PATH_DENIED', 'FILE_REPARSE_DENIED', 'FILE_TYPE_OR_SIZE_DENIED', 'FILE_CHANGED_DENIED', 'FILE_FORMAT_DENIED', 'UPSTREAM_RESULT_DENIED', 'UPSTREAM_CONTENT_MISMATCH','SOURCE_POLICY_DENIED','SOURCE_CHANGED_DENIED','PREIMAGE_SHA256_MISMATCH','STAGING_FILE_MISSING','SYNTAX_TYPE_DENIED'].includes(error.message) ? error.message : 'READ_FAILED_CLOSED';
      throw new McpError(ErrorCode.InvalidParams, safe);
    }
  });
  server.onclose = () => { upstream.close().catch(() => {}); };
  process.on('SIGINT', () => { upstream.close().finally(() => process.exit(0)); });
  process.on('SIGTERM', () => { upstream.close().finally(() => process.exit(0)); });
  await server.connect(new StdioServerTransport());
}

module.exports = { FILE_ALIAS, PUBLIC_TOOL, validateCall, readPinnedFile, callReadOnly, sha256, main };
if (require.main === module) main(process.argv[2]).catch(() => { process.stderr.write('OLDIES_GATEWAY_STARTUP_FAILED_CLOSED\n'); process.exit(78); });
