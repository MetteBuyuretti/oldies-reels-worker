function Invoke-OldiesSecureActivation {
 param([Parameter(Mandatory=$true)]$InputResult,[Parameter(Mandatory=$true)][string]$Engine,[Parameter(Mandatory=$true)][string]$ActivationScript,[Parameter(Mandatory=$true)][string]$ReceiptPath)
 $psi=$null;$process=$null;$secret=$null
 $parentBefore=[Environment]::GetEnvironmentVariable('CONTROL_PLANE_API_KEY','Process')
 try{
  if(-not $InputResult.Accepted){return @{state='CANCELLED_NO_RUNTIME_CHANGE';exitCode=0;runtimeStopAttempted=$false}}
  $secret=([string]$InputResult.Value).Trim();$InputResult.Value=$null
  if([string]::IsNullOrWhiteSpace($secret)){return @{state='EMPTY_INPUT_NO_RUNTIME_CHANGE';exitCode=42;runtimeStopAttempted=$false}}
  if(-not $secret.StartsWith('sk-',[StringComparison]::Ordinal) -or $secret.StartsWith('sk-admin-',[StringComparison]::OrdinalIgnoreCase) -or $secret -match '\s'){return @{state='INVALID_INPUT_NO_RUNTIME_CHANGE';exitCode=42;runtimeStopAttempted=$false}}
  $psi=[Diagnostics.ProcessStartInfo]::new()
  $psi.FileName=$Engine;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.WindowStyle=[Diagnostics.ProcessWindowStyle]::Hidden
  foreach($argument in @('-NoProfile','-NonInteractive','-File',$ActivationScript)){$psi.ArgumentList.Add($argument)}
  foreach($name in @($psi.Environment.Keys)){if($name -match '^(CONTROL_PLANE_|OPENAI_|AZURE_OPENAI_|GITHUB_|GH_TOKEN$)'){$null=$psi.Environment.Remove($name)}}
  # Only the activation child and its managed runtime inherit this transient reference.
  $psi.Environment['CONTROL_PLANE_API_KEY']=$secret
  $psi.Environment['CONTROL_PLANE_ORGANIZATION_ID']='org-2TiSjrrLTwfkczOgeglNV2YI'
  $psi.Environment['LOG_HTTP_RAW_UNSAFE']='false';$psi.Environment['TRACING_ENABLED']='false'
  $psi.Environment['HARPOON_CAPTURE_PAYLOADS']='false';$psi.Environment['ALLOW_REMOTE_UI']='false'
  $psi.Environment['HEALTH_LISTEN_ADDR']='127.0.0.1:0';$psi.Environment['CONTROL_PLANE_POLL_CHANNELS']='main'
  $psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
  $started=[DateTimeOffset]::UtcNow
  $process=[Diagnostics.Process]::new();$process.StartInfo=$psi
  if(-not $process.Start()){throw 'ACTIVATION_CHILD_NOT_STARTED'}
  $stdoutTask=$process.StandardOutput.ReadToEndAsync();$stderrTask=$process.StandardError.ReadToEndAsync()
  $process.WaitForExit()
  $stdout=$stdoutTask.GetAwaiter().GetResult();$stderr=$stderrTask.GetAwaiter().GetResult()
  # Never forward child output; even unexpected failures cannot echo input to chat/log.
  $outputSecretDetected=$stdout.Contains($secret) -or $stderr.Contains($secret)
  $stdout=$null;$stderr=$null
  if($outputSecretDetected){throw 'CHILD_OUTPUT_REDACTION_REQUIRED'}
  if(-not(Test-Path -LiteralPath $ReceiptPath)){throw 'ACTIVATION_CHILD_NO_FRESH_RECEIPT'}
  $receipt=Get-Content -LiteralPath $ReceiptPath -Raw | ConvertFrom-Json
  if(([DateTimeOffset]$receipt.at) -lt $started){throw 'ACTIVATION_CHILD_NO_FRESH_RECEIPT'}
  $allowed=@('ACTIVATED_LOCAL_RUNTIME_WORK_TEST_PENDING','ACTIVATION_FAILED_OLD_RUNTIME_RESTORED','ACTIVATION_FAILED_ROLLBACK_NEEDS_ATTENTION','ACTIVATION_NOT_STARTED')
  if($receipt.status -notin $allowed){throw 'ACTIVATION_CHILD_UNEXPECTED_STATUS'}
  return @{state=$receipt.status;exitCode=$process.ExitCode;runtimeStopAttempted=[bool]$receipt.runtimeStopAttempted;activated=[bool]$receipt.activated;reason=$receipt.reason;childOutputNotForwarded=$true}
 }finally{
  $InputResult.Value=$null;$secret=$null
  if($psi){$null=$psi.Environment.Remove('CONTROL_PLANE_API_KEY')}
  $script:OldiesSecureActivationAudit=@{childEnvironmentReferenceCleared=($null -eq $psi -or -not $psi.Environment.ContainsKey('CONTROL_PLANE_API_KEY'));inputReferenceCleared=($null -eq $InputResult.Value);parentEnvironmentUnchanged=([Environment]::GetEnvironmentVariable('CONTROL_PLANE_API_KEY','Process') -eq $parentBefore)}
  if($process){$process.Dispose()}
  # This function never changes the parent environment.
  if([Environment]::GetEnvironmentVariable('CONTROL_PLANE_API_KEY','Process') -ne $parentBefore){throw 'PARENT_ENVIRONMENT_CHANGED'}
 }
}
