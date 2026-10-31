from pathlib import Path
import subprocess,json,hashlib
HERE=Path(__file__).resolve().parent
source=Path(r'C:\Users\METE\oldies-jingle-automation\run_tumblr_auto.ps1').read_text(encoding='utf-8-sig')
rows=[]
def lit(s):return "'"+str(s).replace("'","''")+"'"
for name,fresh in [('failed_child_preserves_old_success',False),('failed_child_reports_fresh_error',True)]:
 root=(HERE/('launcher-TEST-'+name)).resolve();logs=root/'logs';logs.mkdir(parents=True,exist_ok=True)
 latest=logs/'tumblr-publisher-latest.json';latest.write_text('{"at":"2000-01-01T00:00:00Z","status":"OLD_SUCCESS"}')
 before=hashlib.sha256(latest.read_bytes()).hexdigest()
 launcher=root/'launcher.ps1';launcher.write_text(source.replace("$root='C:\\Users\\METE\\oldies-jingle-automation'",'$root='+lit(root)),encoding='utf-8')
 child=root/'fake-child.mjs';child.write_text("import fs from 'node:fs';"+("fs.writeFileSync(process.argv[2],JSON.stringify({at:new Date().toISOString(),status:'ERROR'}));" if fresh else '')+"process.exit(17);",encoding='utf-8')
 script='''function Invoke-RestMethod { return @{} }
function Start-Process {
 param($FilePath,$ArgumentList,$WorkingDirectory,$WindowStyle,[switch]$Wait,[switch]$PassThru,$RedirectStandardOutput,$RedirectStandardError)
 if(($ArgumentList -join ' ') -match 'tumblr_editorial_control_v4'){return [pscustomobject]@{ExitCode=0}}
 return Microsoft.PowerShell.Management\\Start-Process -FilePath $FilePath -ArgumentList @(CHILD,LATEST) -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput $RedirectStandardOutput -RedirectStandardError $RedirectStandardError
}
& LAUNCHER -Mode Verify
exit $LASTEXITCODE
'''.replace('CHILD',lit('"'+str(child)+'"')).replace('LATEST',lit('"'+str(latest)+'"')).replace('LAUNCHER',lit(launcher))
 harness=root/'test.ps1';harness.write_text(script,encoding='utf-8')
 p=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-File',str(harness)],capture_output=True,text=True,timeout=25)
 line=json.loads((logs/'tumblr-launcher.jsonl').read_text(encoding='utf-8-sig').splitlines()[-1]);after=hashlib.sha256(latest.read_bytes()).hexdigest()
 assert p.returncode==17 and line['publisherExit']==17 and line['exitCode']==17 and line['publisherReportFresh']==fresh
 assert line['publisherStatus']==('ERROR' if fresh else None) and (before!=after)==fresh
 rows.append({'case':name,'launcher_exit':p.returncode,'publisher_exit':line['publisherExit'],'report_fresh':fresh,'status':line['publisherStatus'],'old_report_unchanged':before==after,'result':'PASS'})
(HERE/'launcher-error-tests.json').write_text(json.dumps({'status':'PASS','cases':rows,'real_browser_or_publisher_calls':0},indent=2)+'\n');print(json.dumps(rows))
