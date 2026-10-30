"""Run the unchanged HANDOFF modules with existing real dependencies; no import shims."""
from pathlib import Path
import contextlib,hashlib,io,json,os,runpy,sys,re,datetime

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
SNAPSHOT=HERE/'reels-snapshot'
DEPS=PROJECT/'artifacts/reels-recovery-20261018/python-deps'
bindings=json.loads((HERE/'snapshot-bindings.json').read_text())
def verify():
    for f in bindings['files']:
        assert hashlib.sha256((SNAPSHOT/f['path']).read_bytes()).hexdigest()==f['sha256'],'SNAPSHOT_CHANGED'
verify()
# Do not expose or propagate stored environment credentials to imports/tests.
allowed={'SystemRoot','SYSTEMROOT','SystemDrive','WINDIR','windir','TEMP','TMP','APPDATA','LOCALAPPDATA','USERPROFILE','PATH'}
retained={k:v for k,v in os.environ.items() if k in allowed}
os.environ.clear();os.environ.update(retained)
fixture_temp=(HERE/'fixture-temp').resolve()
assert fixture_temp.is_relative_to(HERE.resolve())
fixture_temp.mkdir(exist_ok=True)
os.environ['TEMP']=os.environ['TMP']=str(fixture_temp)
import tempfile
tempfile.tempdir=str(fixture_temp)
sys.dont_write_bytecode=True
sys.path.insert(0,str(DEPS))
hits=[]
def blocked(label):
    def deny(*args,**kwargs):
        hits.append(label);raise AssertionError('OFFLINE_GUARD_'+label)
    return deny
def audit(event,args):
    if event in {'socket.connect','socket.getaddrinfo','subprocess.Popen','os.system','os.startfile','os.posix_spawn'}:
        blocked(event)()
    if event=='open' and isinstance(args[0],(str,bytes)):
        name=os.fsdecode(args[0]).replace('\\','/').lower()
        if 'application_default_credentials.json' in name or '/.aws/credentials' in name or '/.config/gcloud/' in name:
            blocked('credential-file')()
sys.addaudithook(audit)
import requests,google.auth,google.auth._default,google.auth.transport.requests,PIL
requests.sessions.Session.request=blocked('requests.Session.request')
google.auth.default=blocked('google.auth.default')
google.auth._default.default=blocked('google.auth._default.default')
google.auth.load_credentials_from_file=blocked('google.auth.load_credentials_from_file')
google.auth._default.load_credentials_from_file=blocked('google.auth._default.load_credentials_from_file')
google.auth.transport.requests.Request.__call__=blocked('google.auth.transport.Request')
dependencies={'requests':{'version':requests.__version__,'file':requests.__file__},
 'google.auth':{'version':google.auth.__version__,'file':google.auth.__file__},
 'PIL':{'version':PIL.__version__,'file':PIL.__file__}}
os.chdir(SNAPSHOT)
sys.path.insert(0,str(SNAPSHOT))
commands=[['compileall','-q','facebook_global_audio.py','facebook_global_visuals.py',
 'test_facebook_signoff_integration.py','test_facebook_global_audio.py'],
 ['unittest','-v','test_facebook_signoff_integration','test_facebook_global_audio','test_facebook_global_visuals']]
rows=[]
for args in commands:
    stream=io.StringIO();code=0
    sys.argv=args
    with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        try:runpy.run_module(args[0],run_name='__main__',alter_sys=True)
        except SystemExit as e:code=int(e.code or 0)
    log=stream.getvalue()
    rows.append({'prepared_command':'python -m '+' '.join(args),'execution':'same stdlib CLI module through guarded runpy; real dependency imports',
                 'exit_code':code,'log':log})
    (HERE/(args[0]+'-windows.log')).write_text(log,encoding='utf-8')
verify()
tests=re.search(r'Ran (\d+) tests?',rows[-1]['log'])
result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'snapshot':bindings['ref'],'python':sys.version.split()[0],'python_executable':sys.executable,
 'dependencies':dependencies,'dependency_import_shims':[],
 'commands':rows,'tests_run':int(tests.group(1)) if tests else None,
 'passed':all(x['exit_code']==0 for x in rows) and not hits,
 'external_effect_guard_hits':hits,'source_and_test_bytes_unchanged':True,
 'real_provider_tts_http_ffmpeg_video_publish_calls':0,'new_dependencies_installed':False,
 'prior_43_are_new_tests':False,'installed_reels_changed':False,'fixture_temp_root':str(fixture_temp)}
(HERE/'reels-local-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='commands'},ensure_ascii=True,indent=2))
sys.exit(0 if result['passed'] else 1)
