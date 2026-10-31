"""Narrow T1 source/packet checks. No media bytes, provider, render or HTTP."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import os
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SNAPSHOT = Path(os.getenv('WORK2_SOURCE_SNAPSHOT', str(HERE.parents[1]))).resolve()
INPUT = HERE / 'SOURCE-SNAPSHOT.json'
sys.path.insert(0, str(SNAPSHOT))
import source_evidence
import editorial_quality_gate
import video_factory

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    packet_path = HERE / 'PREPRODUCTION.json'
    packet = json.loads(packet_path.read_text(encoding='utf-8'))
    bundle = json.loads(INPUT.read_text(encoding='utf-8'))
    comparisons = []
    for row in bundle['files']:
        raw = (SNAPSHOT / row['path']).read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()
        assert blob == row['expected_git_blob'], row['path']
        local_sha = bundle['local_R0']['workspaces'][0]['files'][row['path']]
        comparisons.append({'path': row['path'], 'github_blob': blob,
                            'github_snapshot_sha256': digest(raw),
                            'R0_LOCAL_REELS_1_sha256': local_sha,
                            'R0_exact_bytes_match': digest(raw) == local_sha})
    rows = []
    with patch('socket.socket', side_effect=AssertionError('No network allowed')), \
         patch('subprocess.run', side_effect=AssertionError('No subprocess/media allowed')):
        assert source_evidence.check_script(packet) == packet['dj_script_tr']
        rows.append({'check': 'actual_PR33_check_script_on_archive_packet',
                     'result': 'STRUCTURAL_ONLY_PASS', 'human_acceptance': False})
        wrong = copy.deepcopy(packet)
        wrong['research_date'] = packet['actual_research_session_date']
        try:
            source_evidence.check_script(wrong)
            raise AssertionError('Old event was incorrectly accepted as 31 October')
        except source_evidence.EvidenceError as exc:
            assert 'requested calendar day' in str(exc)
            rows.append({'check': 'old_event_as_current_day', 'result': 'EXPECTED_REJECTION',
                         'error': str(exc)})
        unsupported = copy.deepcopy(packet)
        unsupported['story_tr']['narrative'] += ' Bu kayıttan sonra yeni bir turne başladı.'
        try:
            source_evidence.check_script(unsupported)
            raise AssertionError('Unsupported appended narrative was accepted')
        except source_evidence.EvidenceError as exc:
            assert 'unsupported' in str(exc)
            rows.append({'check': 'unsupported_extra_narrative', 'result': 'EXPECTED_REJECTION',
                         'error': str(exc)})
        try:
            editorial_quality_gate.check_photo_evidence(packet)
            raise AssertionError('Incomplete photo package was accepted')
        except editorial_quality_gate.EditorialGateError as exc:
            rows.append({'check': 'no_photo_package_no_acceptance', 'result': 'EXPECTED_REJECTION',
                         'error': str(exc)})
        with patch.object(video_factory, 'audio_duration', return_value=27.0), \
             patch.object(video_factory, 'detect_pause_centers', return_value=[]):
            timeline = video_factory.build_timeline(packet['dj_script_tr'], Path('NOT_A_REAL_AUDIO_FILE'))
        worker = ast.parse((SNAPSHOT / 'worker.py').read_text(encoding='utf-8'))
        function = next(node for node in worker.body
                        if isinstance(node, ast.FunctionDef) and node.name == 'make_timeline_scenes')
        assignment = next(node for node in ast.walk(function)
                          if isinstance(node, ast.Assign)
                          and any(isinstance(target, ast.Name) and target.id == 'photo' for target in node.targets))
        expression = compile(ast.Expression(assignment.value), '<PR33-photo-assignment>', 'eval')
        photo_ids = [eval(expression, {'photos':['P1','P2','P3'], 'index':i, 'len':len})
                     for i in range(1, len(timeline)+1)]
        assert len(timeline) > 3 and len(set(photo_ids)) == 3
        rows.append({'check':'actual_PR33_timeline_and_photo_assignment_fixture',
                     'result':'EXISTING_STORYBOARD_CONSUMPTION_GAP_REPRODUCED',
                     'voice_seconds':27.0, 'duration_is':'STUB_NOT_A_MEASUREMENT',
                     'scene_count':len(timeline), 'photo_sequence':photo_ids,
                     'new_storyboard_consumed':False})
    words = len(packet['dj_script_tr'].split())
    estimate = [{'words_per_minute':wpm, 'speech_seconds_estimate':round(words*60/wpm,2),
                 'with_1_2s_draft_pause_seconds_estimate':round(words*60/wpm+1.2,2)}
                for wpm in (120,130,140)]
    output = {'job_id':packet['job_id'], 'status':'T1_TEXT_SOURCE_CHECKED_VISUAL_MEDIA_NOT_APPROVED',
              'python':sys.version.split()[0], 'base_ref':bundle['ref'],
              'source_snapshots':comparisons, 'focused_checks':rows,
              'script_words_whitespace':words,'script_sha256':source_evidence.text_sha256(packet['dj_script_tr']),
              'estimates_not_audio_measurements':estimate,
              'provider_calls':0,'network_calls':0,'media_calls':0,'render_calls':0,
              'audio_file_produced':False,'video_file_produced':False,
              'creative_acceptance':False,'visual_or_territory_acceptance':False,
              'prior_test_counts_reused':False}
    (HERE / 'VALIDATION.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',
                                          encoding='utf-8')
    print(json.dumps(output,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()

