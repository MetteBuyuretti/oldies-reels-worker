$ErrorActionPreference='Stop'
$base=Split-Path -Parent $MyInvocation.MyCommand.Path
$priv=Join-Path $base 'pair.private'
$project=Split-Path -Parent (Split-Path -Parent $base)
$stage='C:\Users\METE\Oldies-Jingle-Factory\backups\WORK2-20261015-STATE-QC-RECOVERY\FINAL-LIVE-ADAPTER-20261018'
$launcher='C:\Users\METE\Oldies-Jingle-Factory\scripts\Run-Factory.ps1';$manifest=Join-Path $stage 'SHA256-MANIFEST.json'
$candidate=Join-Path $project 'work-output\canonical-handoff-20261031\candidate\Run-Factory.ps1'
$l0='1300e811e001719fbe1d2b6fa581bd2f7b1f1297ea457117d2a51fe30973934d';$l1='21a6c0ea568a3fad76e7e33a843204f41eb7054d28cdca9a3fa7b8d84b5cc2f4'
$m0='6cd1a6fb3ad7af2a5e70afa5f39c8b0de7bf632849d5438d96f0a8dd97c003c5';$m1='8520b954029103e4259c16175a698da903125f1ef6d5b2cb9f63191c2a8005e1'
function Get-PairHash($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
if((Get-PairHash $launcher) -ne $l0 -or (Get-PairHash $manifest) -ne $m0 -or (Get-PairHash $candidate) -ne $l1 -or (Get-PairHash (Join-Path $priv 'launcher.original.ps1')) -ne $l0 -or (Get-PairHash (Join-Path $priv 'manifest.original.json')) -ne $m0 -or (Get-PairHash (Join-Path $priv 'manifest.candidate.json')) -ne $m1){throw 'PREIMAGE_OR_BACKUP_DRIFT'}
$tasks=@(Get-ScheduledTask | Where-Object {$_.TaskName -match 'Jingle'})
if($tasks.Count -lt 3 -or @($tasks|Where-Object {$_.State -ne 'Disabled'}).Count){throw 'JINGLE_TASK_NOT_DISABLED'}
$running=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine -match 'Run-Factory\.ps1|jingle_factory\.py|producer[\\/]candidate\.cjs|run_daily_jingle\.ps1'})
if($running.Count){throw 'JINGLE_EXECUTOR_RUNNING'}
Push-Location $stage
try {& node -e "require('./producer/candidate.cjs').verify()";if($LASTEXITCODE -ne 0){throw 'ORIGINAL_VERIFY_FAILED'}} finally {Pop-Location}
function Replace-Atomic($source,$target){
 $temp=Join-Path (Split-Path $target) ('codex-'+[guid]::NewGuid().ToString('N')+'.tmp')
 $bk=Join-Path $priv ('replace-'+[guid]::NewGuid().ToString('N')+'.bak')
 try{[IO.File]::WriteAllBytes($temp,[IO.File]::ReadAllBytes($source));[IO.File]::Replace($temp,$target,$bk)}finally{if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Force}}
}
try {
 Replace-Atomic $candidate $launcher
 if((Get-PairHash $launcher) -ne $l1 -or (Get-PairHash $manifest) -ne $m0){throw 'INTERMEDIATE_CHANGED'}
 Replace-Atomic (Join-Path $priv 'manifest.candidate.json') $manifest
 if((Get-PairHash $launcher) -ne $l1 -or (Get-PairHash $manifest) -ne $m1){throw 'POSTIMAGE_FAILED'}
 Push-Location $stage
 try{& node -e "require('./producer/candidate.cjs').verify()";if($LASTEXITCODE -ne 0){throw 'NEW_PAIR_VERIFY_FAILED'}}finally{Pop-Location}
 $errs=$null;$tokens=$null;[void][System.Management.Automation.Language.Parser]::ParseFile($launcher,[ref]$tokens,[ref]$errs);if($errs.Count){throw 'PARSE_FAILED'}
 [ordered]@{status='CANONICAL_BRIDGE_AND_STAGE_PIN_INSTALLED';launcher=(Get-PairHash $launcher);manifest=(Get-PairHash $manifest);candidate_verify='PASS';parse='PASS';scheduler='DISABLED';production_started=$false} | ConvertTo-Json
}catch{
 $lh=Get-PairHash $launcher;$mh=Get-PairHash $manifest
 if(@($l0,$l1) -notcontains $lh -or @($m0,$m1) -notcontains $mh){throw 'ROLLBACK_DRIFT_RECONCILE'}
 if($mh -ne $m0){Replace-Atomic (Join-Path $priv 'manifest.original.json') $manifest}
 if($lh -ne $l0){Replace-Atomic (Join-Path $priv 'launcher.original.ps1') $launcher}
 Push-Location $stage
 try{& node -e "require('./producer/candidate.cjs').verify()";if($LASTEXITCODE -ne 0){throw 'ROLLBACK_VERIFY_FAILED'}}finally{Pop-Location}
 Write-Output 'ROLLBACK_PAIR_VERIFIED';throw
}
