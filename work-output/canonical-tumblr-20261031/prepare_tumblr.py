from pathlib import Path
import hashlib,json,difflib
root=Path(__file__).resolve().parent
src=Path(r'C:\Users\METE\oldies-jingle-automation\tumblr_auto_news_v3.mjs')
raw=src.read_bytes(); text=raw.decode('utf-8-sig').replace('\r\n','\n'); old=text
text=text.replace("const articles=page.getByRole('article');let lastOwn=null;","const articles=page.getByRole('article');let lastOwnId=null;",1)
text=text.replace('   lastOwn=article;','   lastOwnId=id;',1)
line='  if(!complete){if(lastOwn)await lastOwn.scrollIntoViewIfNeeded();await page.mouse.wheel(0,700);await page.waitForTimeout(500);}'
replacement='''  if(!complete){
   if(lastOwnId){
    for(let attempt=0;attempt<3;attempt++){
     try{
      // Reacquire the current article by the previously observed numeric permalink ID.
      const current=page.getByRole('article').filter({has:page.locator(`a[href*="/oldiesradyo/${lastOwnId}/"], a[href$="/oldiesradyo/${lastOwnId}"]`)}).first();
      await current.waitFor({state:'visible',timeout:15000});
      await current.scrollIntoViewIfNeeded();
      break;
     }catch(error){
      if(attempt===2||!/not attached|detached/i.test(String(error?.message)))throw error;
     }
    }
   }
   await page.mouse.wheel(0,700);await page.waitForTimeout(500);
  }'''
assert old.count(line)==1 and line in text
text=text.replace(line,replacement,1)
eol='\r\n' if b'\r\n' in raw else '\n';out=text.replace('\n',eol).encode('utf-8')
(root/'candidate').mkdir(exist_ok=True);(root/'backup.private').mkdir(exist_ok=True)
(root/'candidate/tumblr_auto_news_v3.mjs').write_bytes(out);(root/'backup.private/tumblr_auto_news_v3.mjs').write_bytes(raw)
(root/'tumblr-scroll.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile='a/tumblr_auto_news_v3.mjs',tofile='b/tumblr_auto_news_v3.mjs')),encoding='utf-8')
h=lambda b:hashlib.sha256(b).hexdigest()
(root/'tumblr-identity.json').write_text(json.dumps({'source_sha256':h(raw),'candidate_sha256':h(out),'installed':False,'scope':'cards read-only scan scroll only'},indent=2)+'\n')
print((root/'tumblr-identity.json').read_text())
