from pathlib import Path
import subprocess,hashlib,json,os,base64,shutil
HERE=Path(__file__).resolve().parent
root=HERE/'fixture'; (root/'scripts').mkdir(parents=True,exist_ok=True); (root/'.venv/Scripts').mkdir(parents=True,exist_ok=True); (root/'src').mkdir(exist_ok=True)
fake=root/'.venv/Scripts/python.exe'
cs='''using System; using System.Text; public class Fixture { public static int Main(string[] args) { foreach(string a in args) Console.WriteLine(Convert.ToBase64String(Encoding.UTF8.GetBytes(a))); return Environment.GetEnvironmentVariable("FIXTURE_REJECT") == "1" ? 42 : 0; } }'''
(root/'fake.cs').write_text(cs,encoding='utf-8')
ps=r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
cmd="Add-Type -Path '"+str(root/'fake.cs').replace("'","''")+"' -OutputAssembly '"+str(fake).replace("'","''")+"' -OutputType ConsoleApplication"
if not fake.exists():
 build=subprocess.run([ps,'-NoProfile','-NonInteractive','-Command',cmd],capture_output=True,text=True);assert build.returncode==0,build.stderr
target=root/'scripts/Run-Factory.ps1'; main=root/'src/jingle_factory.py';main.write_text('# fixture, not executed')
fixture=root/'special $ & ü [x].json';fixture.write_text('{"fixture":true}')
baseline=(HERE/'backup.private/Run-Factory.ps1').read_text(encoding='utf-8-sig')
candidate=(HERE/'candidate/Run-Factory.ps1').read_text(encoding='utf-8-sig')
secret="[Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')"
assert secret in baseline and secret in candidate
baseline=baseline.replace(secret,'$null');candidate=candidate.replace(secret,'$null')
rows=[]
def run(label,code,args,reject=False):
 target.write_text(code,encoding='utf-8-sig');env={k:v for k,v in os.environ.items() if k in ['SystemRoot','SYSTEMROOT','WINDIR','TEMP','TMP','PATH','USERPROFILE']};env['FIXTURE_REJECT']='1' if reject else '0'
 p=subprocess.run([ps,'-NoProfile','-NonInteractive','-File',str(target),*args],env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20)
 parsed=[]
 for line in p.stdout.splitlines():
  if not line:continue
  try:parsed.append(base64.b64decode(line,validate=True).decode('utf-8'))
  except Exception:pass
 rows.append({'case':label,'exit':p.returncode,'argv':parsed});return p,parsed
v,argv=run('baseline_explicit',baseline,['-Morning','-MusicHandoff',str(fixture)])
assert '--music-handoff' not in argv
v,argv=run('candidate_default',candidate,[]);assert v.returncode==0 and argv==[str(main),'--evening'],(v.stdout,v.stderr,argv)
v,argv=run('candidate_special_path',candidate,['-Morning','-MusicHandoff',str(fixture)]);assert v.returncode==0 and argv==[str(main),'--morning','--music-handoff',str(fixture)],(v.stdout,v.stderr,argv)
v,argv=run('candidate_missing',candidate,['-MusicHandoff',str(root/'missing.json')]);assert v.returncode!=0 and not argv
v,argv=run('candidate_blank',candidate,['-MusicHandoff','']);assert v.returncode!=0 and not argv
v,argv=run('candidate_validator_reject',candidate,['-Morning','-MusicHandoff',str(fixture)],True);assert v.returncode==42 and argv[-1]==str(fixture)
v,argv=run('candidate_utility_conflict',candidate,['-Doctor','-MusicHandoff',str(fixture)]);assert v.returncode!=0 and not argv
result={'status':'PASS','cases':rows,'fake_child_only':True,'real_factory_provider_calls':0,'fixture_secret_lookup_replaced':True,'validator_rejection':'simulated child exit 42; real Python validation not executed','installed':False}
(HERE/'fixture-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(result,ensure_ascii=True,indent=2))
