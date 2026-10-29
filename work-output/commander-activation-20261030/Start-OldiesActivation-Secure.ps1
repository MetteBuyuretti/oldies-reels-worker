param([switch]$UiSelfTest)
$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot
$projectRoot=Split-Path (Split-Path $taskRoot -Parent) -Parent
$oldUi=Join-Path $projectRoot 'artifacts\commander-tunnel-20261029\SecureKeyDialog.cs'
$statePath=Join-Path $taskRoot 'evidence\masked-activation-state.json'
$answer=$null
$mutex=[Threading.Mutex]::new($false,'Local\OLDIES_Commander_Masked_Activation_20261030')
$ownsMutex=$false
function Save-UiState($state,$details=$null){@{at=(Get-Date).ToUniversalTime().ToString('o');state=$state;processId=$PID;details=$details}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath $statePath -Encoding utf8}
try{
 $ownsMutex=$mutex.WaitOne(0)
 if(-not $ownsMutex){Write-Host 'OLDIES: Mevcut aktivasyon penceresi zaten acik.';exit 0}
 $manifest=Get-Content -LiteralPath (Join-Path $taskRoot 'secure-launcher-pins.json') -Raw | ConvertFrom-Json
 foreach($item in $manifest.files){if((Get-FileHash -LiteralPath $item.path).Hash.ToLower() -ne $item.sha256){throw 'SECURE_LAUNCHER_PREIMAGE_CHANGED'}}
 $plan=Get-Content -LiteralPath (Join-Path $taskRoot 'activation-plan.private.json') -Raw|ConvertFrom-Json
 foreach($item in $plan.files){if((Get-FileHash -LiteralPath $item.path).Hash.ToLower() -ne $item.sha256 -or (Get-FileHash -LiteralPath $item.backup).Hash.ToLower() -ne $item.sha256){throw 'ACTIVE_PREIMAGE_OR_BACKUP_CHANGED'}}
 $principal=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
 if($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ADMINISTRATOR_TOKEN_DENIED'}
 if([DateTimeOffset]::UtcNow -ge [DateTimeOffset]'2026-11-04T23:49:12Z'){throw 'EXPECTED_RUNTIME_KEY_EXPIRED'}
 . (Join-Path $taskRoot 'SecureActivation.Core.ps1')
 Add-Type -AssemblyName System.Windows.Forms;Add-Type -AssemblyName System.Drawing
 $references=@('System.Windows.Forms.dll','System.Windows.Forms.Primitives.dll','System.Private.Windows.Core.dll','System.Drawing.Primitives.dll','System.ComponentModel.Primitives.dll','System.ComponentModel.TypeConverter.dll','System.Runtime.dll')
 Add-Type -Path $oldUi -ReferencedAssemblies $references
 if($UiSelfTest){if(-not [OldiesLocalKeyDialog]::SelfTest()){throw 'MASKED_UI_SELF_TEST_FAILED'};Write-Output 'MASKED_ACTIVATION_UI_COMPILE_PASS';exit 0}
 Save-UiState 'MASKED_ACTIVATION_INPUT_READY' @{shortcut='OLDIES - Anahtar Penceresi';button='Proje araçlarını etkinleştir';scope='Existing six tools only';runtimeStopped=$false}
 $answer=[OldiesLocalKeyDialog]::CaptureActivation()
 if(-not $answer.Accepted){Save-UiState 'CANCELLED_NO_RUNTIME_CHANGE';exit 0}
 Save-UiState 'SECURE_INPUT_RECEIVED_ACTIVATING' @{secretLogged=$false}
 $result=Invoke-OldiesSecureActivation -InputResult $answer -Engine (Get-Process -Id $PID).Path -ActivationScript (Join-Path $taskRoot 'activate-managed.ps1') -ReceiptPath (Join-Path $taskRoot 'evidence\activation-result.json')
 Save-UiState $result.state $result
 if($result.state -eq 'ACTIVATED_LOCAL_RUNTIME_WORK_TEST_PENDING'){
  [System.Windows.Forms.MessageBox]::Show('Proje araçları mevcut tünelde etkinleştirildi. Work üzerinden son araç testi ayrıca yapılacak.','OLDIES — aktivasyon tamamlandı')|Out-Null
 }elseif($result.state -notmatch 'CANCELLED|EMPTY_INPUT'){
  [System.Windows.Forms.MessageBox]::Show('Aktivasyon sonucu gizlisiz yerel kayda yazıldı. Ayrıntı #32 tesliminde bildirilecek.','OLDIES — aktivasyon sonucu')|Out-Null
 }
 exit $result.exitCode
}catch{
 Save-UiState 'SECURE_ACTIVATION_FAILED' @{errorCode='SECURE_UI_OR_CHILD_GUARD_FAILED';secretLogged=$false}
 Write-Host 'OLDIES: Guvenli aktivasyon durdu; gizlisiz yerel sonuc kaydedildi.'
 exit 1
}finally{
 if($answer){$answer.Value=$null}
 if($ownsMutex){$mutex.ReleaseMutex()};$mutex.Dispose()
}
