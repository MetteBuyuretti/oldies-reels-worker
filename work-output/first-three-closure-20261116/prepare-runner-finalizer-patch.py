"""Produce a reviewed candidate; never overwrite the installed runner.

Operate on original UTF-8 bytes so Turkish UI locators are preserved. The cloud
review transcript's replacement characters are deliberately not used as source.
"""
import argparse
from pathlib import Path
import hashlib
import json

OLD = "if(init.status==='DOWNLOADED_AWAITING_AUDIO_VIDEO_QC'){console.log('MEDIA_DOWNLOADED_NO_RETRY');return}"
NEW = """if(init.status==='DOWNLOADED_AWAITING_AUDIO_VIDEO_QC'){
    // Local post-download completion only: no browser, provider or scheduler.
    const finalize=require('child_process').spawnSync;
    const python='C:\\\\Users\\\\METE\\\\Oldies-Jingle-Factory\\\\.venv\\\\Scripts\\\\python.exe';
    const result=finalize(python,[path.join(__dirname,'finalize-local-pair.py'),day,slot],
      {encoding:'utf8',windowsHide:true,timeout:240000});
    if(result.stdout)console.log(result.stdout.trim());
    if(result.error||result.status!==0)throw new Error('V31_FINALIZATION_BLOCKED_NO_PROVIDER_RETRY');
    return;
  }"""

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('original',type=Path)
    parser.add_argument('candidate',type=Path)
    args=parser.parse_args()
    raw=args.original.read_bytes()
    text=raw.decode('utf-8-sig')
    if '\ufffd' in text:
        raise SystemExit('INVALID_REVIEW_COPY_USE_ORIGINAL_UTF8_SOURCE')
    if text.count(OLD)!=1:
        raise SystemExit('SOURCE_ANCHOR_CHANGED_STOP')
    candidate=text.replace(OLD,NEW)
    # Do not rewrite the source file, even if the caller supplied the same path.
    if args.original.resolve()==args.candidate.resolve() or args.candidate.exists():
        raise SystemExit('CANDIDATE_MUST_BE_NEW_PATH')
    args.candidate.write_text(candidate,encoding='utf-8')
    print(json.dumps({'installed':False,'source_sha256':hashlib.sha256(raw).hexdigest(),
                      'candidate_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest()}))
