"""Actual intake validator, early rejection only; isolated TEST roots and stub imports."""
from pathlib import Path
import types,sys,json,importlib.util,datetime,hashlib
HERE=Path(__file__).resolve().parent
actual=Path(r'C:\Users\METE\Oldies-Jingle-Factory\src\web_music_handoff.py')
root=HERE/'validator-TEST';src=root/'src';factory=root/'factory';producer=root/'producer';outside=root/'outside'
for p in [src,factory/'config',producer/'job',outside]:p.mkdir(parents=True,exist_ok=True)
source=actual.read_bytes();(src/'web_music_handoff.py').write_bytes(source);(factory/'config/settings.json').write_text('{}')
today='2026-10-31'; digest='a'*64
status={'status':'DOWNLOADED','job_id':'job-test','date':today,'slot':'evening','rawPath':'job/raw.mp3'}
(producer/'job/status.json').write_text(json.dumps(status));(outside/'status.json').write_text('{}')
(producer/'job/raw.mp3').write_bytes(b'TEST_NOT_AUDIO_'*100)
class FactoryError(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
class Factory:
 def review_recovery_state(self,_):pass
def forbidden(*a,**kw):raise AssertionError('SIDE_EFFECT_FORBIDDEN')
mods={'audio':{'command':forbidden,'decode':forbidden},'common':{'FactoryError':FactoryError,'atomic_json':forbidden,'now':lambda:datetime.datetime(2026,10,31,tzinfo=datetime.timezone(datetime.timedelta(hours=3))),'read_json':lambda p,default=None:default,'run_lock':forbidden},'qc':{'music_gate':forbidden},'jingle_factory':{'Factory':Factory}}
for name,attributes in mods.items():
 mod=types.ModuleType(name);mod.__dict__.update(attributes);sys.modules[name]=mod
spec=importlib.util.spec_from_file_location('actual_handoff',src/'web_music_handoff.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
rows=[]
def run(label,expected,**changes):
 args={'day':today,'slot':'morning','job_id':'job-test','expected_sha256':digest};args.update(changes)
 statuspath=args.pop('status_file',producer/'job/status.json')
 try:mod.import_download(factory,producer,statuspath,**args)
 except FactoryError as e:assert e.code==expected,(label,e.code,expected)
 else:raise AssertionError(label+' did not reject')
 rows.append({'case':label,'actual_error':expected,'result':'PASS'})
run('wrong_day','WEB_MUSIC_SOURCE_STALE',day='2026-10-30')
run('wrong_slot','WEB_MUSIC_SLOT_MISMATCH')
run('invalid_job','WEB_MUSIC_MANIFEST_INVALID',job_id='../bad')
run('invalid_hash','WEB_MUSIC_MANIFEST_INVALID',expected_sha256='short')
run('mismatched_job','WEB_MUSIC_STATUS_INVALID',slot='evening',job_id='other-test')
run('mismatched_hash','WEB_MUSIC_SOURCE_HASH_OR_SIZE_INVALID',slot='evening',expected_sha256='b'*64)
run('status_outside_producer_root','WEB_MUSIC_PATH_INVALID',status_file=outside/'status.json')
assert not (factory/'incoming').exists() and not (factory/'logs').exists()
result={'status':'PASS','actual_source_sha256':hashlib.sha256(source).hexdigest(),'actual_callable':'import_download early input validation','cases':rows,'factory_class_and_dependencies':'explicit no-effect fixture stubs','actual_provider_qc_mix_import_write_calls':0,'real_receipt_used':False}
(HERE/'validator-tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
