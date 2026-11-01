from pathlib import Path
import hashlib,json,difflib
p=Path(__file__).resolve().parent
src=p.parent/'local-exec-20261029/commander/gateway.candidate.cjs'
raw=src.read_bytes();old=raw.decode('utf-8-sig').replace('\r\n','\n');s=old
anchor="const { pathToFileURL } = require('node:url');";assert s.count(anchor)==1;s=s.replace(anchor,anchor+"\nconst {createAssetTools} = require('./asset-tools.cjs');",1)
anchor="  const server = new Server(";assert s.count(anchor)==1;s=s.replace(anchor,"  const assets = createAssetTools(policy.asset);\n"+anchor,1)
anchor='tools: [PUBLIC_TOOL,...projectTools.TOOLS]';assert s.count(anchor)==1;s=s.replace(anchor,'tools: [PUBLIC_TOOL,...projectTools.TOOLS,...assets.TOOLS]',1)
anchor='      if(projectTools.TOOLS.some(t=>t.name===request.params.name))';assert s.count(anchor)==1;s=s.replace(anchor,"      if(assets.TOOLS.some(t=>t.name===request.params.name))return await assets.call(request.params.name,request.params.arguments);\n"+anchor,1)
(p/'gateway-asset.cjs').write_text(s,encoding='utf-8');(p/'gateway-asset.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile='a/gateway.candidate.cjs',tofile='b/gateway-asset.cjs')),encoding='utf-8')
project=(src.parent/'project-tools.cjs').read_bytes()
assert hashlib.sha256(project).hexdigest()=='f8e5316c2831adb7d4be189e35f75ba3f7d9ed6cae9751c5ddf9592340805e4d'
(p/'project-tools.cjs').write_bytes(project)
h=lambda b:hashlib.sha256(b).hexdigest()
(p/'gateway-identity.json').write_text(json.dumps({'active_gateway_sha256':h(raw),'candidate_sha256':h((p/'gateway-asset.cjs').read_bytes()),'installed':False},indent=2)+'\n')
print((p/'gateway-identity.json').read_text())
