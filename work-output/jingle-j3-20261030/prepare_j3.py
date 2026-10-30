from pathlib import Path
import hashlib, json, difflib, datetime

HERE = Path(__file__).resolve().parent
FACTORY = Path(r'C:\Users\METE\Oldies-Jingle-Factory')
STAGE = FACTORY / 'backups/WORK2-20261015-STATE-QC-RECOVERY/FINAL-LIVE-ADAPTER-20261018'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
HERE.joinpath('candidate').mkdir(parents=True, exist_ok=True)
HERE.joinpath('evidence').mkdir(exist_ok=True)
source = STAGE / 'producer/gemini_jingle.staged.cjs'
data = source.read_bytes()
old = """    const item = await firstVisible([
      page.getByRole('menuitem', {name:/Yalnızca ses|Audio only|MP3 parçası|MP3 track/i})
    ]);
    if (!item) throw new Error('DOWNLOAD_AUDIO_MENU_NOT_FOUND');"""
new = """    const item = page.getByRole('menuitem',
      {name:/Yalnızca ses|Audio only|MP3 parçası|MP3 track/i}).first();
    // A completed button click does not imply an asynchronously rendered menu is visible.
    try { await item.waitFor({state:'visible', timeout:10000}); }
    catch (_) { throw new Error('DOWNLOAD_AUDIO_MENU_NOT_FOUND'); }"""
eol = '\r\n' if b'\r\n' in data else '\n'
old_bytes, new_bytes = old.replace('\n', eol).encode(), new.replace('\n', eol).encode()
assert data.count(old_bytes) == 1, 'SOURCE_ANCHOR_CHANGED'
candidate = HERE / 'candidate/gemini_jingle.staged.cjs'
candidate.write_bytes(data.replace(old_bytes, new_bytes, 1))
patch = {'source':'producer/gemini_jingle.staged.cjs', 'old':old, 'new':new}
(HERE/'menu-wait-patch.json').write_text(json.dumps(patch,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
(HERE/'adapter-menu-wait.diff').write_text(''.join(difflib.unified_diff(
    data.decode().replace('\r\n','\n').splitlines(True),
    candidate.read_text(encoding='utf-8').splitlines(True),
    fromfile='a/producer/gemini_jingle.staged.cjs',tofile='b/producer/gemini_jingle.staged.cjs',n=4)),encoding='utf-8')
protected = [FACTORY/'config/production-state.json',FACTORY/'config/settings.json',
    FACTORY/'config/approved-jingle-standard-v3.1.json',FACTORY/'config/run.lock',FACTORY/'logs/run.lock',
    FACTORY/'logs/heartbeat.json',FACTORY/'references/OldiesRadyo-V3.1-APPROVED-SOUND-REFERENCE.mp3',
    STAGE/'runtime/producer/operation-claims/2026-10-18-morning.json',
    STAGE/'runtime/browser-operation.lock', STAGE/'config/activation.json']
sources = ['producer/gemini_jingle.staged.cjs','producer/producer_contract.cjs',
    'producer/staged_orchestration.cjs','producer/candidate.cjs','src/import_web_music.py',
    'src/web_music_handoff.py','src/producer_factory_pipeline.py']
protected += [STAGE/p for p in sources]
fingerprint=lambda p: sha(p) if p.is_file() else 'DIRECTORY_PRESENT' if p.is_dir() else 'MISSING'
job = STAGE/'runtime/producer/web-2026-10-18-morning-23562c19-98d4-44ff-a566-058a79de044a'
protected += [job/'status.json']
snap = {'protected':{str(p):fingerprint(p) for p in protected}}
(HERE/'evidence/preimage.private.json').write_text(json.dumps(snap,indent=2),encoding='utf-8')
evidence = {'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'historical_job_files':sorted(p.name for p in job.iterdir()),
    'historical_download_subcause':'NOT_RECOVERABLE_FROM_MARKED_JOB',
    'historical_root_cause_proven':False,
    'source_sha256':{p:sha(STAGE/p) for p in sources},
    'candidate_sha256':sha(candidate),'installed':False,
    'change':'Bounded visible-menu wait instead of immediate count/isVisible snapshot',
    'output_files': [{'name':p.name,'bytes':p.stat().st_size} for p in (FACTORY/'output').iterdir() if p.is_file()]}
(HERE/'evidence/source-contract.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
print(json.dumps(evidence,indent=2))
