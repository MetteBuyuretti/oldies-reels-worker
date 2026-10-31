$ErrorActionPreference='Stop'
$base=Split-Path -Parent $MyInvocation.MyCommand.Path;$project=Split-Path -Parent (Split-Path -Parent $base);$priv=Join-Path $base 'tumblr-pins.private'
$publisher='C:\Users\METE\oldies-jingle-automation\tumblr_auto_news_v3.mjs';$candidate=Join-Path $project 'work-output\canonical-tumblr-20261031\candidate\tumblr_auto_news_v3.mjs'
$policy=Join-Path $project 'work-output\local-exec-20261029\commander\policy.candidate.private.json'
$plan=Join-Path $project 'work-output\commander-activation-20261030\activation-plan.private.json'
$pins=Join-Path $project 'work-output\commander-activation-20261030\secure-launcher-pins.json'
function Get-Fingerprint($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$items=@(
 @{target=$publisher;old='3dd7b0988c091526ce59bc73a155bbc37ea9dacb553f49cfb132e0d729e5c38a';new='9e44f9af845c889c0079ba5cc956ea0e5be08b825050cb9aea6fa5670032c622';original=(Join-Path $priv 'publisher.old');candidate=$candidate},
 @{target=$policy;old='992132c3f078decbba3f8eb7be215736db3217ca4accaff9e8a91b7dd562b826';new='d46d12956429994f45337b3dcda136edc01c17c4e7f3db0dce8c5719bb32ea01';original=(Join-Path $priv 'policy.old');candidate=(Join-Path $priv 'policy.new')},
 @{target=$plan;old='a031c175ac889f71a5f9eac12979457720162b09a8485fe753b23b869d99fcc6';new='c7cf8361b7af4a1fcbdc60419468d0edefa6a72c73fea1ac98f9aa6085c3cc09';original=(Join-Path $priv 'plan.old');candidate=(Join-Path $priv 'plan.new')},
 @{target=$pins;old='aec0ee71221573587e33b87a9418e93c17b490526989e7fca4899765d3097805';new='358d90ab95d26821a13bd71e67617c864cfc2068c999ae6bec4e421301c43ef5';original=(Join-Path $priv 'pins.old');candidate=(Join-Path $priv 'pins.new')}
)
foreach($x in $items){if((Get-Fingerprint $x.target) -ne $x.old -or (Get-Fingerprint $x.original) -ne $x.old -or (Get-Fingerprint $x.candidate) -ne $x.new){throw 'PREIMAGE_OR_BACKUP_DRIFT'}}
if(Test-Path -LiteralPath 'C:\Users\METE\oldies-jingle-automation\tumblr-publisher.lock'){throw 'PUBLISHER_LOCK_PRESENT'}
$task=Get-ScheduledTask -TaskName 'Oldies-Tumblr-48h';$next=($task | Get-ScheduledTaskInfo).NextRunTime
if($task.State -eq 'Running' -or ($next -gt (Get-Date) -and $next -lt (Get-Date).AddMinutes(10))){throw 'SCHEDULE_BUSY'}
$running=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine -match 'tumblr_auto_news_v3\.mjs|run_tumblr_auto\.ps1|gateway\.candidate\.cjs|tunnel-client\.exe'})
if($running.Count){throw 'PUBLISHER_OR_COMMANDER_RUNNING'}
function Replace-File($source,$target){
 $temp=Join-Path (Split-Path $target) ('codex-'+[guid]::NewGuid().ToString('N')+'.tmp');$saved=Join-Path $priv ('atomic-'+[guid]::NewGuid().ToString('N')+'.bak')
 try{[IO.File]::WriteAllBytes($temp,[IO.File]::ReadAllBytes($source));[IO.File]::Replace($temp,$target,$saved)}finally{if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Force}}
}
try{
 foreach($x in $items){if((Get-Fingerprint $x.target) -ne $x.old){throw 'CONCURRENT_DRIFT'};Replace-File $x.candidate $x.target;if((Get-Fingerprint $x.target) -ne $x.new){throw 'POSTIMAGE_FAILED'}}
 & node --check $publisher;if($LASTEXITCODE -ne 0){throw 'PUBLISHER_SYNTAX_FAILED'}
 $verify="const fs=require('fs'),crypto=require('crypto'),t=require(process.argv[1]),p=JSON.parse(fs.readFileSync(process.argv[2]));for(const a of Object.keys(p.project.sources))t.source(p.project,a);const plan=JSON.parse(fs.readFileSync(process.argv[3]));if(crypto.createHash('sha256').update(fs.readFileSync(process.argv[2])).digest('hex')!==plan.candidate_policy_sha256)throw Error('POLICY_PIN');const pins=JSON.parse(fs.readFileSync(process.argv[4]));for(const f of pins.files)if(crypto.createHash('sha256').update(fs.readFileSync(f.path)).digest('hex')!==f.sha256)throw Error('SECURE_PIN');"
 & node -e $verify (Join-Path $project 'work-output\local-exec-20261029\commander\project-tools.cjs') $policy $plan $pins
 if($LASTEXITCODE -ne 0){throw 'COMMANDER_PIN_CHAIN_FAILED'}
 $env:OLDIES_INVENTORY_INSTALLED='1'
 try{& node (Join-Path $base 'read_cards.cjs');if($LASTEXITCODE -ne 0){throw 'REAL_CARDS_FAILED'}}finally{Remove-Item Env:OLDIES_INVENTORY_INSTALLED -ErrorAction SilentlyContinue}
 [ordered]@{status='INSTALLED_PUBLISHER_AND_PIN_CHAIN';publisher=(Get-Fingerprint $publisher);policy=(Get-Fingerprint $policy);plan=(Get-Fingerprint $plan);pins=(Get-Fingerprint $pins);real_cards='PASS';commander_runtime_restarted=$false;publication_started=$false} | ConvertTo-Json
}catch{
 $problem=$_.Exception.Message
 for($i=$items.Count-1;$i -ge 0;$i--){$x=$items[$i];$cur=Get-Fingerprint $x.target;if($cur -eq $x.new){Replace-File $x.original $x.target}elseif($cur -ne $x.old){throw 'ROLLBACK_DRIFT_RECONCILIATION_REQUIRED'}}
 foreach($x in $items){if((Get-Fingerprint $x.target) -ne $x.old){throw 'ROLLBACK_VERIFY_FAILED'}}
 Write-Output ('TUMBLR_ROLLBACK_VERIFIED '+$problem);throw
}
