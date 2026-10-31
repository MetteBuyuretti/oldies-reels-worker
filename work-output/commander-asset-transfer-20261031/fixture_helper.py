"""Test-only local byte reader substitutes HTTPS; never activated as production helper."""
import json,sys,io
from PIL import Image
from asset_service import AssetService
r=json.load(sys.stdin)
b=io.BytesIO();Image.new('RGB',(4,3),'red').save(b,format='PNG');raw=b.getvalue()
s=AssetService(r['policy']['root'],r['policy']['sources'],lambda url,hosts:(raw,'image/png'))
try:
 result=s.transfer(r['asset_id'],r['name']) if r['operation']=='transfer' else s.inspect(r['name'])
 print(json.dumps(result))
except Exception as e:print(json.dumps({'error':str(e)}));sys.exit(2)
