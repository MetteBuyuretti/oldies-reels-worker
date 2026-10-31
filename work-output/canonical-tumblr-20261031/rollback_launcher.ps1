$ErrorActionPreference='Stop'
$workspace=Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backup=Join-Path $workspace 'canonical-handoff-20261031\backup.private\Run-Factory.ps1'
$target='C:\Users\METE\Oldies-Jingle-Factory\scripts\Run-Factory.ps1'
function Hash($p){(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()}
$old='1300e811e001719fbe1d2b6fa581bd2f7b1f1297ea457117d2a51fe30973934d'
$new='21a6c0ea568a3fad76e7e33a843204f41eb7054d28cdca9a3fa7b8d84b5cc2f4'
if((Hash $target) -ne $new -or (Hash $backup) -ne $old){throw 'ROLLBACK_HASH_DRIFT'}
$tasks=@(Get-ScheduledTask | Where-Object {$_.TaskName -match 'Jingle'})
if($tasks.Count -lt 3 -or @($tasks|Where-Object {$_.State -ne 'Disabled'}).Count){throw 'JINGLE_TASK_NOT_DISABLED'}
$running=@(Get-CimInstance Win32_Process | Where-Object {$_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine -match 'Run-Factory\.ps1|jingle_factory\.py|producer[\\/]candidate\.cjs|run_daily_jingle\.ps1'})
if($running.Count){throw 'JINGLE_EXECUTOR_RUNNING'}
$temp=Join-Path (Split-Path $target) ('Run-Factory.rollback-'+[guid]::NewGuid().ToString('N')+'.tmp')
$postBackup=Join-Path (Split-Path $backup) ('rollback-postimage-'+[guid]::NewGuid().ToString('N')+'.ps1')
try {
 [IO.File]::WriteAllBytes($temp,[IO.File]::ReadAllBytes($backup))
 if((Hash $temp) -ne $old -or (Hash $target) -ne $new){throw 'ROLLBACK_RECHECK_FAILED'}
 [IO.File]::Replace($temp,$target,$postBackup)
 if((Hash $target) -ne $old -or (Hash $postBackup) -ne $new){throw 'ROLLBACK_VERIFY_FAILED'}
 'ROLLBACK_CANONICAL_PREIMAGE_RESTORED'
} finally {if(Test-Path -LiteralPath $temp){Remove-Item -LiteralPath $temp -Force}}
