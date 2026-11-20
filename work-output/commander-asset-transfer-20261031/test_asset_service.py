from pathlib import Path
import io,json,tempfile,unittest,hashlib,sys,socket
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
import asset_service as a
HERE=Path(__file__).resolve().parent
def png(color='red'):
 b=io.BytesIO();Image.new('RGB',(4,3),color).save(b,format='PNG');return b.getvalue()
class Cases(unittest.TestCase):
 def setUp(self):
  self.root=Path(tempfile.mkdtemp(prefix='TEST-',dir=HERE)).resolve();self.data=png();self.man={'fixture':{'url':'https://images.example.test/image.png','hosts':['images.example.test']}}
  self.service=a.AssetService(self.root,self.man,lambda url,hosts:(self.data,'image/png'))
 def test_real_bytes_receipt_and_idempotency(self):
  r=self.service.transfer('fixture','one.png');self.assertEqual(r['status'],'TRANSFERRED');self.assertEqual((r['width'],r['height'],r['bytes']),(4,3,len(self.data)));self.assertEqual(r['sha256'],hashlib.sha256((self.root/'one.png').read_bytes()).hexdigest());self.assertEqual(self.service.transfer('fixture','one.png')['status'],'ALREADY_PRESENT');self.assertEqual(self.service.inspect('one.png')['sha256'],r['sha256'])
 def test_traversal_name_and_unapproved_alias(self):
  for name in ['../evil.png','C:\\evil.png','x:ads.png','CON.png','\\\\host\\evil.png']:
   with self.assertRaises(ValueError):self.service.transfer('fixture',name)
  with self.assertRaisesRegex(ValueError,'SOURCE_DENIED'):self.service.transfer('unknown','x.png')
 def test_conflict_does_not_overwrite(self):
  (self.root/'one.png').write_bytes(png('blue'));before=(self.root/'one.png').read_bytes()
  with self.assertRaisesRegex(ValueError,'CONFLICT_DENIED'):self.service.transfer('fixture','one.png')
  self.assertEqual((self.root/'one.png').read_bytes(),before)
 def test_wrong_type_and_corrupt(self):
  with self.assertRaisesRegex(ValueError,'MIME_DENIED'):a.decode(self.data,'fake.jpg','image/png')
  with self.assertRaisesRegex(ValueError,'IMAGE_DENIED'):a.decode(b'not-image','x.png','image/png')
 def test_byte_limit(self):
  with self.assertRaisesRegex(ValueError,'SIZE_DENIED'):a.decode(b'a'*(a.MAX_BYTES+1),'x.png','image/png')
 def test_private_address_and_redirect(self):
  with patch.object(a.socket,'getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('127.0.0.1',443))]):
   with self.assertRaisesRegex(ValueError,'NETWORK_DENIED'):a.request_https('https://images.example.test/a',{'images.example.test'})
  class Response:
   status=302
   def getheader(self,k,*args):return 'https://127.0.0.1/internal' if k=='Location' else None
  class Conn:
   def __init__(self,*args,**kw):pass
   def request(self,*args,**kw):pass
   def getresponse(self):return Response()
   def close(self):pass
  with patch.object(a.socket,'getaddrinfo',return_value=[(socket.AF_INET,socket.SOCK_STREAM,6,'',('8.8.8.8',443))]),patch.object(a.http.client,'HTTPSConnection',Conn):
   with self.assertRaisesRegex(ValueError,'SOURCE_DENIED'):a.request_https('https://images.example.test/a',{'images.example.test'})
 def test_disallowed_host(self):
  with self.assertRaisesRegex(ValueError,'SOURCE_DENIED'):a.AssetService(self.root,{'x':{'url':'https://unapproved.test/file','hosts':['approved.test']}},lambda *a:(self.data,'image/png')).transfer('x','x.png')
if __name__=='__main__':unittest.main(verbosity=2)
