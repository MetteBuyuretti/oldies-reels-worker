from pathlib import Path
import hashlib,difflib,json
root=Path(__file__).resolve().parent
factory=Path(r'C:\Users\METE\Oldies-Jingle-Factory')
source=factory/'scripts/Run-Factory.ps1'; python=factory/'src/jingle_factory.py'
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=source.read_bytes(); text=raw.decode('utf-8-sig'); newline='\r\n' if '\r\n' in text else '\n'; text=text.replace('\r\n','\n')
assert "parser.add_argument(\"--music-handoff\"" in python.read_text(encoding='utf-8-sig')
old='[switch]$Morning, [switch]$Evening)'; new='[switch]$Morning, [switch]$Evening, [AllowEmptyString()][string]$MusicHandoff)'
assert text.count(old)==1; candidate=text.replace(old,new,1)
anchor="$ErrorActionPreference = 'Stop'\n"
insert=r'''function ConvertTo-WindowsArgument([string]$Value) {
    # Windows CreateProcess quoting: double backslashes before quotes and the closing quote.
    $quoted = [regex]::Replace($Value, '(\\*)"', { param($m) ('\' * (2 * $m.Groups[1].Value.Length + 1)) + '"' })
    $quoted = [regex]::Replace($quoted, '(\\+)$', { param($m) '\' * (2 * $m.Groups[1].Value.Length) })
    return '"' + $quoted + '"'
}
if ($PSBoundParameters.ContainsKey('MusicHandoff')) {
    if ([string]::IsNullOrWhiteSpace($MusicHandoff) -or -not (Test-Path -LiteralPath $MusicHandoff -PathType Leaf)) { throw 'MUSIC_HANDOFF_FILE_REQUIRED' }
    $MusicHandoff = (Resolve-Path -LiteralPath $MusicHandoff).ProviderPath
    if ($Doctor -or $SelfTest -or $CheckApi -or $ScheduleReady) { throw 'MUSIC_HANDOFF_MODE_CONFLICT' }
}
'''
assert candidate.count(anchor)==1;candidate=candidate.replace(anchor,anchor+insert,1)
anchor="    if ($ScheduleReady) { $factoryArguments = @( '--schedule-ready', $(if ($Morning) {'--morning'} else {'--evening'}) ) }\n"
assert candidate.count(anchor)==1;candidate=candidate.replace(anchor,anchor+"    if ($PSBoundParameters.ContainsKey('MusicHandoff')) { $factoryArguments += @('--music-handoff', (ConvertTo-WindowsArgument $MusicHandoff)) }\n",1)
out=candidate.replace('\n',newline).encode('utf-8'); (root/'candidate').mkdir(exist_ok=True);(root/'backup.private').mkdir(exist_ok=True)
(root/'candidate/Run-Factory.ps1').write_bytes(out); (root/'backup.private/Run-Factory.ps1').write_bytes(raw)
(root/'handoff.diff').write_text(''.join(difflib.unified_diff(text.splitlines(True),candidate.splitlines(True),fromfile='a/scripts/Run-Factory.ps1',tofile='b/scripts/Run-Factory.ps1')),encoding='utf-8')
(root/'identity.json').write_text(json.dumps({'launcher_source_sha256':sha(raw),'factory_source_sha256':sha(python.read_bytes()),'candidate_sha256':sha(out),'installed':False},indent=2)+'\n')
print((root/'identity.json').read_text())
