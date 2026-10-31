$ErrorActionPreference='Stop'
$p=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'application-plan.json') -Raw | ConvertFrom-Json
$target=$p.target; $manifest=$p.manifest.target; $backup=$p.rollback.backup_directory
function Hash($file) {(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()}
if((Hash $target) -ne $p.adapter.preimage_sha256 -or (Hash $manifest) -ne $p.manifest.preimage_sha256) {throw 'PREIMAGE_CHANGED'}
if((Hash $p.adapter.existing_candidate) -ne $p.adapter.postimage_sha256 -or (Hash $p.manifest.prepared_file) -ne $p.manifest.postimage_sha256) {throw 'CANDIDATE_CHANGED'}
if((Hash (Join-Path $backup 'gemini_jingle.staged.cjs')) -ne $p.adapter.preimage_sha256 -or (Hash (Join-Path $backup 'SHA256-MANIFEST.json')) -ne $p.manifest.preimage_sha256) {throw 'BACKUP_CHANGED'}
$tasks=@(Get-ScheduledTask -TaskName 'Oldies Jingle Factory - Aksam','Oldies Jingle Factory - Sabah')
if($tasks.Count -ne 2 -or @($tasks | Where-Object {$_.State -ne 'Disabled'}).Count -gt 0) {throw 'SCHEDULE_NOT_DISABLED'}
$running=@(Get-CimInstance Win32_Process -Filter "Name='node.exe'" | Where-Object {$_.CommandLine -and $_.CommandLine -match 'FINAL-LIVE-ADAPTER-20261018|producer[\\/]candidate\.cjs'})
if($running.Count -gt 0) {throw 'STAGE_PROCESS_ACTIVE'}
$stage=Split-Path -Parent $manifest
Push-Location $stage
try { & node -e "require('./producer/candidate.cjs').verify()"; if($LASTEXITCODE -ne 0){throw 'BASE_VERIFY_FAILED'} } finally {Pop-Location}
$changed=$false
try {
 [IO.File]::WriteAllBytes($target,[IO.File]::ReadAllBytes($p.adapter.existing_candidate)); $changed=$true
 [IO.File]::WriteAllBytes($manifest,[IO.File]::ReadAllBytes($p.manifest.prepared_file))
 if((Hash $target) -ne $p.adapter.postimage_sha256 -or (Hash $manifest) -ne $p.manifest.postimage_sha256){throw 'POSTIMAGE_MISMATCH'}
 Push-Location $stage
 try { & node -e "require('./producer/candidate.cjs').verify()"; if($LASTEXITCODE -ne 0){throw 'POST_VERIFY_FAILED'} } finally {Pop-Location}
 [ordered]@{status='INSTALLED_STAGE_ONLY';adapter_sha256=(Hash $target);manifest_sha256=(Hash $manifest);tasks_disabled=$true;candidate_verify='PASS';backup_verified=$true} | ConvertTo-Json
} catch {
 if($changed){
  if((Hash $target) -ne $p.adapter.postimage_sha256 -or @($p.manifest.preimage_sha256,$p.manifest.postimage_sha256) -notcontains (Hash $manifest)){throw 'ROLLBACK_REQUIRES_MANUAL_RECONCILIATION'}
  [IO.File]::WriteAllBytes($manifest,[IO.File]::ReadAllBytes((Join-Path $backup 'SHA256-MANIFEST.json')))
  [IO.File]::WriteAllBytes($target,[IO.File]::ReadAllBytes((Join-Path $backup 'gemini_jingle.staged.cjs')))
  if((Hash $target) -ne $p.adapter.preimage_sha256 -or (Hash $manifest) -ne $p.manifest.preimage_sha256){throw 'ROLLBACK_VERIFY_FAILED'}
  Write-Output 'ROLLBACK_PREIMAGES_RESTORED'
 }
 throw
}
