"""Offline regression evidence only; fixtures are not production/QC evidence."""
import copy
import io
import unittest
import urllib.error
from datetime import timedelta
from unittest.mock import patch

from jingle_service import evaluate, fetch_status, output_valid, SERVICE
from test_jingle_service import sample, NOW, CFG
from watchdog import alert


class TelemetryRegressionTests(unittest.TestCase):
    def test_nonfinite_durations_never_pass(self):
        for value in (float('nan'), float('inf'), -float('inf'), True, '10'):
            with self.subTest(value=value):
                data = sample()
                data['outputs']['wav']['duration_seconds'] = value
                findings, report = evaluate(data, NOW, CFG)
                self.assertIn('jingle_audio_invalid_or_stale', [f['reason'] for f in findings])
                self.assertIn('MASTER: NOT VERIFIED', report)

    def test_missing_timestamp_does_not_crash_audit(self):
        data = sample()
        del data['outputs']['wav']['modified_at']
        findings, _ = evaluate(data, NOW, CFG)
        self.assertIn('jingle_audio_invalid_or_stale', [f['reason'] for f in findings])

    def test_nonhex_hash_rejected(self):
        data = sample()
        data['outputs']['wav']['sha256'] = 'z' * 64
        self.assertFalse(output_valid(data['outputs']['wav'], data['job']['id'], NOW, 10, .6))

    def test_failed_trace_cannot_be_final(self):
        data = sample()
        data['events'].insert(2, {'job_id': data['job']['id'], 'status': 'ERROR'})
        findings, report = evaluate(data, NOW, CFG)
        self.assertIn('jingle_stage_trace_unverified', [f['reason'] for f in findings])
        self.assertIn('MASTER: NOT VERIFIED', report)

    def test_trace_must_reach_reported_stage(self):
        data = sample('CAPCUT_READY')
        data['events'].pop()
        findings, _ = evaluate(data, NOW, CFG)
        self.assertIn('jingle_stage_trace_unverified', [f['reason'] for f in findings])

    def test_untrusted_identifiers_and_provider_not_echoed(self):
        for field in ('id', 'status', 'provider'):
            with self.subTest(field=field):
                data = sample()
                data['job'][field] = 'C:\\private\\SENSITIVE_VALUE\nmore'
                self.assertNotIn('SENSITIVE_VALUE', str(evaluate(data, NOW, CFG)))
        data = sample()
        data['windows_task'].update(last_result=4, last_run_at='PRIVATE_VALUE')
        self.assertNotIn('PRIVATE_VALUE', str(evaluate(data, NOW, CFG)))

    def test_receipt_threshold_exactly_two_hours_and_over(self):
        for seconds, stale in ((7200, False), (7201, True)):
            data = sample()
            data['last_successful_received_at'] = (NOW - timedelta(seconds=seconds)).isoformat()
            findings, report = evaluate(data, NOW, CFG)
            self.assertEqual('jingle_heartbeat_stale' in [f['reason'] for f in findings], stale)
            self.assertEqual('STALE' in report, stale)

    def test_repeated_stale_audits_use_existing_dedupe(self):
        data = sample()
        data['last_successful_received_at'] = (NOW - timedelta(hours=3)).isoformat()
        findings, _ = evaluate(data, NOW, CFG)
        findings = [f for f in findings if f['reason'] == 'jingle_heartbeat_stale']
        class MemoryAPI:
            issues = []
            def request(self, path, method='GET', data=None):
                if method == 'POST':
                    self.issues.append(data.copy())
                    return data
                return copy.deepcopy(self.issues)
        api = MemoryAPI()
        self.assertEqual(alert(api, findings, {SERVICE}), 1)
        later, _ = evaluate(data, NOW + timedelta(hours=1), CFG)
        later = [f for f in later if f['reason'] == 'jingle_heartbeat_stale']
        self.assertEqual(alert(api, later, {SERVICE}), 0)

    def test_transport_rejects_plaintext_and_missing_auth(self):
        for url, token in [('http://example.org', 'token'), ('https://example.org', '')]:
            with self.assertRaises(ValueError):
                fetch_status(url, token)

    def test_transport_refuses_redirect_handler(self):
        with patch('jingle_service.urllib.request.build_opener') as build:
            build.return_value.open.side_effect = urllib.error.HTTPError('https://example.org', 302, 'redirect', {}, None)
            with self.assertRaises(urllib.error.HTTPError):
                fetch_status('https://example.org', 'test-token')
            handler = build.call_args.args[0]()
            self.assertIsNone(handler.redirect_request(None, None, None, None, None, None))

    def test_oversized_and_malformed_response_fail_closed(self):
        for body in (b'x' * 65537, b'not-json'):
            response = io.BytesIO(body)
            response.status = 200
            with patch('jingle_service.urllib.request.build_opener') as build:
                build.return_value.open.return_value = response
                with self.assertRaises(ValueError):
                    fetch_status('https://example.org', 'test-token')

if __name__ == '__main__':
    unittest.main()
