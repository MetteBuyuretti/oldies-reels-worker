$ErrorActionPreference='Stop'
$base=$PSScriptRoot
$enc=(Get-Content -Raw -LiteralPath (Join-Path $base '.pinterest_access_token.enc')).Trim()
$sec=$enc|ConvertTo-SecureString
$b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
try{$token=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($b)}finally{[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b)}
$h=@{Authorization='Bearer '+$token}
function Convert-PinterestUtf8Json([IO.Stream]$Stream){
  $bytes=[IO.MemoryStream]::new()
  try {
    if($Stream.CanSeek){$Stream.Position=0}
    $Stream.CopyTo($bytes)
    $utf8=[Text.UTF8Encoding]::new($false,$true)
    return ($utf8.GetString($bytes.ToArray()) | ConvertFrom-Json)
  } finally {$bytes.Dispose()}
}
function Get-AllItems([string]$Endpoint){
  $items=[Collections.Generic.List[object]]::new()
  $seen=[Collections.Generic.HashSet[string]]::new()
  $bookmark=''
  do {
    $uri='https://api.pinterest.com/v5/'+$Endpoint+'?page_size=100'
    if($bookmark){$uri+='&bookmark='+[uri]::EscapeDataString($bookmark)}
    # Decode the raw JSON bytes explicitly: Windows PowerShell may infer Latin-1.
    $wire=Invoke-WebRequest -UseBasicParsing -Uri $uri -Headers $h -TimeoutSec 60
    if([int]$wire.StatusCode -ne 200){throw 'PINTEREST_READ_FAILED'}
    $response=Convert-PinterestUtf8Json $wire.RawContentStream
    foreach($item in @($response.items)){$items.Add($item)}
    $bookmark=[string]$response.bookmark
    if($bookmark -and (-not $seen.Add($bookmark) -or $seen.Count -ge 100)){throw 'PINTEREST_PAGINATION_INCOMPLETE'}
  } while ($bookmark)
  return $items.ToArray()
}
function Atomic-Json([string]$Name,$Value,[int]$Depth=15){
  $path=Join-Path $base $Name
  ConvertTo-Json -InputObject @($Value) -Depth $Depth | Set-Content -LiteralPath ($path+'.tmp') -Encoding UTF8
  Move-Item -LiteralPath ($path+'.tmp') -Destination $path -Force
}
# Snapshot is invalidated before collection so partial reads cannot pass QA.
$snapshot=Join-Path $base 'or-pin-live-snapshot.json'
@{complete=$false;checked_at_trt=[DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(3)).ToString('yyyy-MM-ddTHH:mm:sszzz')} | ConvertTo-Json | Set-Content -LiteralPath $snapshot -Encoding UTF8
$live=@(Get-AllItems 'pins')
$boards=@(Get-AllItems 'boards')
Atomic-Json 'or-pin-live-pins.json' $live
Atomic-Json 'or-pin-live-boards.json' @($boards | Select-Object id,name,privacy)
$snapshotData=@{complete=$true;checked_at_trt=[DateTimeOffset]::UtcNow.ToOffset([TimeSpan]::FromHours(3)).ToString('yyyy-MM-ddTHH:mm:sszzz');pin_count=$live.Count;board_count=$boards.Count}
$snapshotData | ConvertTo-Json | Set-Content -LiteralPath ($snapshot+'.tmp') -Encoding UTF8
Move-Item -LiteralPath ($snapshot+'.tmp') -Destination $snapshot -Force
$ready=@(Import-Csv -LiteralPath (Join-Path $base 'or-pin-daily-ready.csv'))
$published=@(Import-Csv -LiteralPath (Join-Path $base 'or-pin-published-ledger.csv'))
$scheduled=@(Import-Csv -LiteralPath (Join-Path $base 'or-pin-schedule-ledger.csv'))
$out=foreach($r in $ready){
  $reasons=[Collections.Generic.List[string]]::new()
  if(-not $r.listing_id -or $r.listing_id -notmatch '^\d+$'){$reasons.Add('INVALID_LISTING_ID')}
  elseif($live | Where-Object { $_.link -match ('/listing/'+[regex]::Escape($r.listing_id)+'(?:/|\?|$)') }){$reasons.Add('LIVE_LISTING_ALREADY_EXISTS')}
  if($live | Where-Object { $_.title -eq $r.pin_title }){$reasons.Add('LIVE_EXACT_TITLE_EXISTS')}
  if($published | Where-Object { $_.pin_image_sha256 -eq $r.pin_image_sha256 }){$reasons.Add('PUBLISHED_IMAGE_HASH_EXISTS')}
  if($published | Where-Object { $_.listing_id -eq $r.listing_id -and $_.source_image_sha256 -eq $r.source_image_sha256 }){$reasons.Add('PUBLISHED_LISTING_SOURCE_EXISTS')}
  if($scheduled | Where-Object { $_.listing_id -eq $r.listing_id -and $_.status -in @('SCHEDULED','PUBLISHED') }){$reasons.Add('SCHEDULED_LISTING_EXISTS')}
  [pscustomobject]@{publish_date=$r.publish_date;publish_time_trt=$r.publish_time_trt;listing_id=$r.listing_id;target_board=$r.target_board;pin_title=$r.pin_title;pin_image_path=$r.pin_image_path;pin_image_sha256=$r.pin_image_sha256;source_image_sha256=$r.source_image_sha256;destination_url=$r.destination_url;preflight=$(if($reasons.Count){'BLOCKED'}else{'PASS'});reasons=($reasons -join ';')}
}
$out | Export-Csv -LiteralPath (Join-Path $base 'or-pin-live-preflight.csv') -NoTypeInformation -Encoding UTF8
Write-Output ('LIVE_PREFLIGHT_OK pass='+@($out | Where-Object preflight -eq 'PASS').Count+' blocked='+@($out | Where-Object preflight -eq 'BLOCKED').Count+' total='+$out.Count+' live='+$live.Count+' complete=True')
