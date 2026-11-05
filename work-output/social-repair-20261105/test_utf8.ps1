param([string]$Candidate)
$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($Candidate,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'PARSER_FAILED'}
$fn=$ast.Find({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Convert-PinterestUtf8Json'},$true)
if(-not $fn){throw 'UTF8_HELPER_MISSING'}
Invoke-Expression $fn.Extent.Text
$original='{"title":"Livin 80s '+[char]0x2013+' Nostalgia '+[char]0x2019+'"}'
$stream=[IO.MemoryStream]::new([Text.Encoding]::UTF8.GetBytes($original))
$decoded=Convert-PinterestUtf8Json $stream
if($decoded.title -cne ('Livin 80s '+[char]0x2013+' Nostalgia '+[char]0x2019)){throw 'UNICODE_ROUNDTRIP_FAILED'}
$invalid=[IO.MemoryStream]::new([byte[]]@(0xFF,0xFE,0xFF))
$rejected=$false
try{Convert-PinterestUtf8Json $invalid | Out-Null}catch{$rejected=$true}
if(-not $rejected){throw 'INVALID_UTF8_NOT_REJECTED'}
@{syntax='PASS';utf8_roundtrip='PASS';invalid_utf8='PASS';network_calls=0;candidate_executed=$false}|ConvertTo-Json
