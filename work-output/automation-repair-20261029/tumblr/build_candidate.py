"""Build a new staging publisher; never overwrite or execute the installed file."""
import argparse
import hashlib
import json
from pathlib import Path
import re

GUARD = """function assertPublisherMode(args){
 if(args.includes('--verify')&&args.includes('--queue-ready'))throw Error('CONFLICTING_PUBLISHER_MODES');
}
"""

def patch_source(source):
    if 'assertPublisherMode' in source:
        raise ValueError('ALREADY_PATCHED_OR_UNRECOGNIZED_GUARD')
    # Validate each known integration point before changing any text.
    main = 'async function main(){'
    argv = " const args=process.argv.slice(2),arg=n=>{const i=args.indexOf(n);return i<0?null:args[i+1]};"
    submit = " return args.includes('--queue-ready')&&eligible(p,row,auth);"
    entry = main + '\n' + argv + '\n'
    if source.count(entry) != 1 or source.count(submit) != 1:
        raise ValueError('SOURCE_ANCHOR_MISMATCH')
    if len(re.findall(r'(?:export )?function shouldSubmit\(args,p,row,auth\)\{', source)) != 1:
        raise ValueError('SUBMISSION_ANCHOR_MISMATCH')
    source = source.replace(submit, ' assertPublisherMode(args);\n' + submit, 1)
    return source.replace(entry, GUARD + '\n' + entry + ' assertPublisherMode(args);\n', 1)

def build(source_path, output_path, expected_sha256):
    source_path, output_path = Path(source_path), Path(output_path)
    if source_path.resolve() == output_path.resolve():
        raise ValueError('IN_PLACE_WRITE_FORBIDDEN')
    if source_path.is_symlink() or output_path.is_symlink():
        raise ValueError('SYMLINK_FORBIDDEN')
    raw = source_path.read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if not re.fullmatch(r'[a-f0-9]{64}', expected_sha256) or actual != expected_sha256:
        raise ValueError('PREIMAGE_SHA256_MISMATCH')
    if output_path.exists():
        raise ValueError('OUTPUT_ALREADY_EXISTS')
    newline = '\r\n' if b'\r\n' in raw else '\n'
    text = raw.decode('utf-8').replace('\r\n', '\n')
    patched = patch_source(text).replace('\n', newline).encode('utf-8')
    # Exclusive creation; the source and all production state remain untouched.
    with output_path.open('xb') as target:
        target.write(patched)
    return {'status': 'STAGING_CANDIDATE_ONLY', 'source_sha256': actual,
            'candidate_sha256': hashlib.sha256(patched).hexdigest(),
            'installed': False, 'executed': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--expected-sha256', required=True)
    args = parser.parse_args()
    try:
        result = build(args.source, args.output, args.expected_sha256)
    except (ValueError, OSError, UnicodeError) as error:
        parser.exit(1, f'{error}\n')
    print(json.dumps(result, sort_keys=True))
