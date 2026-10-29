param([Parameter(Mandatory=$true)][string]$Source)
$parseErrors=$null
[void][Management.Automation.Language.Parser]::ParseFile($Source,[ref]$null,[ref]$parseErrors)
if($parseErrors.Count -gt 0){exit 1}
exit 0
