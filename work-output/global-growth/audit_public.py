"""Resumable public Oldies Radyo audit. GET only; bounded workers; no site writes."""
import argparse, concurrent.futures as cf, csv, hashlib, json, re, time
import urllib.request, urllib.error, urllib.parse, xml.etree.ElementTree as ET
import subprocess, tempfile
from collections import Counter
from pathlib import Path
from lxml import html

BASE='https://oldiesradyo.com'
OUT=Path(__file__).parent/'data'
OUT.mkdir(parents=True,exist_ok=True)

def get(url):
    started=time.monotonic()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            hp=Path(tmp)/'headers';bp=Path(tmp)/'body'
            run=subprocess.run(['curl','--silent','--show-error','--location','--max-redirs','3','--connect-timeout','8','--max-time','20','--user-agent','OldiesRadyo-Owner-ReadOnly-Audit/1.0','--dump-header',str(hp),'--output',str(bp),'--write-out','%{http_code}\t%{url_effective}\t%{time_total}',url],capture_output=True,timeout=25)
            fields=run.stdout.decode().split('\t');code=int(fields[0]) if fields and fields[0].isdigit() else 0
            if run.returncode: return None,url,{},run.stderr,time.monotonic()-started
            h={}
            for line in hp.read_text().splitlines():
                if line.startswith('HTTP/'):h={}
                elif ':' in line:
                    k,v=line.split(':',1);h[k.lower()]=v.strip()
            return code,fields[1],h,bp.read_bytes(),time.monotonic()-started
    except Exception as e:
        return None,url,{},str(e).encode(),time.monotonic()-started

def inventory():
    records=[]
    for typ in ['pages','posts']:
        page=1
        while True:
            u=f'{BASE}/wp-json/wp/v2/{typ}?per_page=100&page={page}&_fields=id,type,slug,link,title,content,excerpt,modified,date,lang,translations,categories,tags,featured_media'
            status,final,headers,body,elapsed=get(u)
            if status!=200: raise RuntimeError(f'Inventory incomplete: {u}: {status}')
            data=json.loads(body)
            (OUT/f'{typ}-{page:03}.json').write_bytes(body)
            records.extend(data)
            print(f'inventory {typ} page {page}: {len(data)}',flush=True)
            if page>=int(headers.get('X-WP-TotalPages',headers.get('x-wp-totalpages','1'))): break
            page+=1
    (OUT/'wp-inventory.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    status,_,_,robots,_=get(BASE+'/robots.txt')
    (OUT/'robots.txt').write_bytes(robots)
    todo=re.findall(r'^Sitemap:\s*(\S+)',robots.decode(),re.M|re.I)
    seen=set(); entries=[]; sitemap_status=[]
    while todo:
        url=todo.pop(0)
        if url in seen: continue
        seen.add(url)
        status,final,headers,body,elapsed=get(url)
        sitemap_status.append({'url':url,'status':status,'final':final})
        (OUT/('sitemap-'+hashlib.sha256(url.encode()).hexdigest()[:12]+'.xml')).write_bytes(body)
        if status!=200: continue
        root=ET.fromstring(body)
        for elem in root:
            loc=elem.find('{*}loc')
            if loc is None: continue
            if root.tag.endswith('sitemapindex'): todo.append(loc.text)
            else: entries.append({'url':loc.text,'sitemap':url})
        print(f'sitemap {url}: {len(entries)} cumulative',flush=True)
    (OUT/'sitemap-urls.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2))
    (OUT/'sitemap-status.json').write_text(json.dumps(sitemap_status,indent=2))
    urls=sorted(set(x['link'] for x in records)|set(x['url'] for x in entries)|{BASE+'/',BASE+'/en/'})
    (OUT/'all-urls.json').write_text(json.dumps(urls,ensure_ascii=False,indent=2))
    print(json.dumps({'content_count':len(records),'types':dict(Counter(x['type'] for x in records)),'sitemap_entries':len(entries),'unique_urls':len(urls)}),flush=True)

def audit(url):
    status,final,headers,body,elapsed=get(url)
    (OUT/'responses').mkdir(exist_ok=True)
    (OUT/'responses'/(hashlib.sha256(url.encode()).hexdigest()+'.json')).write_text(json.dumps({'url':url,'status':status,'final_url':final,'headers':headers,'elapsed_seconds':elapsed}))
    return parse_response(url,status,final,headers,body,elapsed)

def parse_response(url,status,final,headers,body,elapsed):
    r={'url':url,'status':status,'final_url':final,'elapsed_seconds':round(elapsed,3),'bytes':len(body),'content_type':headers.get('Content-Type',headers.get('content-type','')),'x_robots_tag':headers.get('X-Robots-Tag',headers.get('x-robots-tag','')),'checked_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    if status is None:
        r['error']=body.decode(); return r
    if 'html' not in r['content_type']: return r
    try:
        doc=html.fromstring(body)
        r.update(title=' '.join(doc.xpath('//title/text()')),html_lang=doc.get('lang',''),canonical=doc.xpath('//link[@rel="canonical"]/@href'),descriptions=doc.xpath('//meta[translate(@name,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="description"]/@content'),robots=doc.xpath('//meta[@name="robots"]/@content'),h1=doc.xpath('//h1//text()'),hreflang=[{'lang':n.get('hreflang'),'url':n.get('href')} for n in doc.xpath('//link[@hreflang]')],og=dict((n.get('property'),n.get('content')) for n in doc.xpath('//meta[starts-with(@property,"og:")]')))
        main=doc.xpath('//main') or doc.xpath('//article') or [doc]
        r['main_words']=len(' '.join(main[0].xpath('.//text()[not(ancestor::script) and not(ancestor::style)]')).split())
        r['main_links']=[{'url':urllib.parse.urljoin(final,n.get('href')),'text':' '.join(n.itertext()).strip()} for n in main[0].xpath('.//a[@href]')]
        r['internal_links']=sorted(set(urllib.parse.urljoin(final,n) for n in doc.xpath('//a/@href') if urllib.parse.urlparse(urllib.parse.urljoin(final,n)).hostname=='oldiesradyo.com'))
        imgs=main[0].xpath('.//img');r['images']=len(imgs);r['missing_alt']=sum(1 for n in imgs if n.get('alt') is None);r['empty_alt']=sum(1 for n in imgs if n.get('alt')=='')
        r['schema_types']=[]
        def schema(x):
            if isinstance(x,dict):
                t=x.get('@type',[]);r['schema_types'].extend(t if isinstance(t,list) else [t])
                for v in x.values(): schema(v)
            elif isinstance(x,list):
                for v in x: schema(v)
        for n in doc.xpath('//script[@type="application/ld+json"]/text()'):
            try: schema(json.loads(n))
            except ValueError: pass
        r['schema_types']=sorted(set(r['schema_types']))
        (OUT/'html').mkdir(exist_ok=True)
        (OUT/'html'/(hashlib.sha256(url.encode()).hexdigest()+'.html')).write_bytes(body)
    except Exception as e: r['parse_error']=str(e)
    return r

def crawl(retry_errors=False):
    urls=json.loads((OUT/'all-urls.json').read_text())
    log=OUT/'live-results.jsonl';done={}
    if log.exists():
        for line in log.read_text().splitlines():
            try:
                x=json.loads(line);done[x['url']]=x
            except ValueError: pass
    pending=[u for u in urls if u not in done or (retry_errors and done[u]['status'] is None)]
    with cf.ThreadPoolExecutor(max_workers=2 if retry_errors else 6) as pool:
        futures={pool.submit(audit,u):u for u in pending}
        for i,future in enumerate(cf.as_completed(futures),1):
            try:r=future.result()
            except Exception as e:r={'url':futures[future],'status':None,'error':str(e),'content_type':''}
            done[r['url']]=r
            log.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in done.values()))
            if i%50==0: print(f'crawl {len(done)}/{len(urls)}',flush=True)
    summary={'checked':len(done),'statuses':dict(Counter(str(r['status']) for r in done.values())),'languages':dict(Counter(r.get('html_lang','') for r in done.values())),'duplicate_description':sum(len(r.get('descriptions',[]))>1 for r in done.values()),'missing_canonical':sum(r['status']==200 and 'html' in r['content_type'] and not r.get('canonical') for r in done.values())}
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['inventory','crawl']);p.add_argument('--retry-errors',action='store_true');args=p.parse_args()
    inventory() if args.phase=='inventory' else crawl(args.retry_errors)
