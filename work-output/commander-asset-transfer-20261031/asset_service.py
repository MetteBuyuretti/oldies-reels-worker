"""Isolated candidate: manifest-bound HTTPS images into one fixed root; not activated."""
import hashlib,http.client,io,ipaddress,json,os,re,socket,ssl,sys,tempfile,urllib.parse,warnings
from pathlib import Path
from PIL import Image

MAX_BYTES=20*1024*1024
MAX_PIXELS=50_000_000
Image.MAX_IMAGE_PIXELS=MAX_PIXELS
FORMATS={'PNG':('image/png','.png'),'JPEG':('image/jpeg','.jpg'),'WEBP':('image/webp','.webp')}
def fail(code):raise ValueError(code)
def safe_name(name):
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,119}\.(png|jpg|jpeg|webp)',name,re.I) or name.endswith('.') or name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:fail('NAME_DENIED')
    return name
def root_check(root):
    root=Path(root)
    if not root.is_absolute() or not root.is_dir():fail('ROOT_DENIED')
    for p in (root,*root.parents):
        s=p.lstat()
        if p.is_symlink() or getattr(s,'st_file_attributes',0)&0x400:fail('REPARSE_DENIED')
    if os.path.normcase(str(root.resolve()))!=os.path.normcase(str(root)):fail('ROOT_DENIED')
    return root
def decode(data,name,mime=None):
    if not data or len(data)>MAX_BYTES:fail('SIZE_DENIED')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as im:
                fmt=im.format; width,height=im.size
                if fmt not in FORMATS or width<=0 or height<=0 or width*height>MAX_PIXELS:fail('IMAGE_DENIED')
                expected,ext=FORMATS[fmt]
                if (Path(name).suffix.lower() not in ({'.jpg','.jpeg'} if ext=='.jpg' else {ext}) or mime is not None and mime.split(';')[0].strip().lower()!=expected):fail('MIME_DENIED')
                im.load()
    except ValueError:raise
    except Exception:fail('IMAGE_DENIED')
    return {'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'width':width,'height':height,'mime':expected}
def request_https(url,allowed_hosts):
    for _ in range(3):
        u=urllib.parse.urlsplit(url)
        if u.scheme!='https' or not u.hostname or u.hostname.lower() not in allowed_hosts or u.username or u.password or u.port not in (None,443):fail('SOURCE_DENIED')
        addresses={item[4][0] for item in socket.getaddrinfo(u.hostname,443,type=socket.SOCK_STREAM)}
        if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):fail('NETWORK_DENIED')
        address=sorted(addresses)[0]
        conn=http.client.HTTPSConnection(u.hostname,443,timeout=15,context=ssl.create_default_context())
        # Pin the DNS result used to connect while retaining original hostname for TLS SNI.
        conn._create_connection=lambda _addr,timeout=None,source_address=None:socket.create_connection((address,443),timeout,source_address)
        try:
            conn.request('GET',urllib.parse.urlunsplit(('', '',u.path or '/',u.query,'')),headers={'Accept':'image/png,image/jpeg,image/webp'})
            r=conn.getresponse()
            if r.status in (301,302,303,307,308):
                loc=r.getheader('Location');
                if not loc:fail('REDIRECT_DENIED')
                url=urllib.parse.urljoin(url,loc);continue
            if r.status!=200:fail('SOURCE_FAILED')
            if r.getheader('Content-Length') and int(r.getheader('Content-Length'))>MAX_BYTES:fail('SIZE_DENIED')
            mime=r.getheader('Content-Type','');data=r.read(MAX_BYTES+1)
            if len(data)>MAX_BYTES:fail('SIZE_DENIED')
            return data,mime
        finally:conn.close()
    fail('REDIRECT_DENIED')
class AssetService:
    def __init__(self,root,manifest,fetch=request_https):self.root=root_check(root);self.manifest=manifest;self.fetch=fetch
    def inspect(self,name):
        name=safe_name(name);root_check(self.root);p=self.root/name
        if not p.exists() or p.is_symlink() or getattr(p.lstat(),'st_file_attributes',0)&0x400 or not p.is_file():fail('FILE_DENIED')
        if p.stat().st_size>MAX_BYTES:fail('SIZE_DENIED')
        return {'name':name,**decode(p.read_bytes(),name)}
    def transfer(self,asset_id,name):
        name=safe_name(name)
        if asset_id not in self.manifest:fail('SOURCE_DENIED')
        entry=self.manifest[asset_id];hosts=set(entry['hosts']);url=entry['url']
        # Validate even injected readers against the same manifest host rule.
        u=urllib.parse.urlsplit(url)
        if u.scheme!='https' or u.hostname not in hosts or u.username or u.password or u.port not in (None,443):fail('SOURCE_DENIED')
        data,mime=self.fetch(url,hosts);info=decode(data,name,mime)
        if entry.get('sha256') and info['sha256']!=entry['sha256']:fail('SOURCE_HASH_DENIED')
        root_check(self.root);p=self.root/name
        if p.exists() or p.is_symlink():
            prior=self.inspect(name)
            if prior['sha256']!=info['sha256']:fail('CONFLICT_DENIED')
            return {**prior,'status':'ALREADY_PRESENT'}
        fd,temp=tempfile.mkstemp(prefix='.asset-',suffix='.tmp',dir=self.root)
        try:
            with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            root_check(self.root)
            try:os.link(temp,p)
            except FileExistsError:fail('CONFLICT_DENIED')
        finally:
            if os.path.exists(temp):os.unlink(temp)
        installed=self.inspect(name)
        if any(installed[k]!=info[k] for k in ('sha256','bytes','width','height','mime')):fail('FILE_DENIED')
        return {**installed,'status':'TRANSFERRED'}
def main():
    try:
        req=json.load(sys.stdin);service=AssetService(req['policy']['root'],req['policy']['sources'])
        if req['operation']=='transfer':result=service.transfer(req['asset_id'],req['name'])
        elif req['operation']=='inspect':result=service.inspect(req['name'])
        else:fail('TOOL_DENIED')
        print(json.dumps(result))
    except Exception as e:
        allowed={'NAME_DENIED','ROOT_DENIED','REPARSE_DENIED','SIZE_DENIED','IMAGE_DENIED','MIME_DENIED','SOURCE_DENIED','NETWORK_DENIED','REDIRECT_DENIED','SOURCE_FAILED','SOURCE_HASH_DENIED','FILE_DENIED','CONFLICT_DENIED','TOOL_DENIED'}
        print(json.dumps({'error':str(e) if str(e) in allowed else 'ASSET_FAILED_CLOSED'}));sys.exit(2)
if __name__=='__main__':main()
