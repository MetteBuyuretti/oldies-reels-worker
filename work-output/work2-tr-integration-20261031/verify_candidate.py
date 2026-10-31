"""Read-only candidate pre/postimage check. No source writes or network."""
import argparse
import hashlib
import json
from pathlib import Path

def verify(root, mode, manifest):
    rows = []
    for entry in manifest['files']:
        path = root / entry['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        expected = entry[mode + '_sha256']
        rows.append({'path':entry['path'],'expected':expected,'actual':actual,'match':actual==expected})
    if mode == 'postimage':
        for name, expected in manifest.get('new_test_files', {}).items():
            path = root / name
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            rows.append({'path':name,'expected':expected,'actual':actual,'match':actual==expected})
    return {'job_id':'WORK2-TR-INTEGRATION-20261031-02','mode':mode,
            'status':'MATCH' if all(row['match'] for row in rows) else 'STOP_HASH_MISMATCH',
            'files':rows,'source_writes':0,'network_calls':0}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--mode', choices=['preimage','postimage'], required=True)
    args = parser.parse_args()
    manifest = json.loads((Path(__file__).parent/'CODE-IDENTITIES.json').read_text(encoding='utf-8'))
    result = verify(args.root.resolve(), args.mode, manifest)
    print(json.dumps(result, indent=2))
    return 0 if result['status']=='MATCH' else 2

if __name__=='__main__':
    raise SystemExit(main())

