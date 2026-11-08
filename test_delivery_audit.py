import io
import os
import unittest
from unittest.mock import patch

import requests
import worker
from test_worker_delivery import FakeResponse


class DeliveryAuditTests(unittest.TestCase):
    def call_transport(self, proxy, responses):
        method = 'post' if proxy else 'request'
        with patch.dict(os.environ, {'OLDIES_DRAFT_PROXY_URL': 'https://proxy.example'}), patch.object(worker.requests, method, side_effect=responses) as transport, patch.object(worker.time, 'sleep') as sleep:
            if proxy:
                result = worker.proxy_draft_request({'artist': 'Eagles'}, 'fixture')
            else:
                result = worker.wordpress_request('PUT', 'drafts', 'fixture', 'https://oldies.example', data={'artist': 'Eagles'})
            return result, transport, sleep

    def test_first_delivery_and_duplicate_replay(self):
        for proxy in (False, True):
            for response, skipped in ((FakeResponse(201, {'success': True}), False), (FakeResponse(409, {'code': 'duplicate_draft'}), True)):
                with self.subTest(proxy=proxy, skipped=skipped):
                    result, transport, sleep = self.call_transport(proxy, [response])
                    self.assertTrue(result['success'])
                    self.assertEqual(bool(result.get('skipped')), skipped)
                    self.assertEqual(transport.call_count, 1)
                    sleep.assert_not_called()

    def test_daily_limit_is_skip_without_retry(self):
        for proxy in (False, True):
            with self.subTest(proxy=proxy):
                result, transport, sleep = self.call_transport(proxy, [FakeResponse(429, {'code': 'daily_draft_limit'})])
                self.assertEqual(result['reason'], 'daily_draft_limit')
                self.assertTrue(result['skipped'])
                self.assertEqual(transport.call_count, 1)
                sleep.assert_not_called()

    def test_transient_failure_then_duplicate(self):
        for proxy in (False, True):
            with self.subTest(proxy=proxy):
                result, transport, sleep = self.call_transport(proxy, [FakeResponse(503, {}), FakeResponse(409, {'code': 'duplicate_draft'})])
                self.assertEqual(result['reason'], 'duplicate_draft')
                self.assertEqual(transport.call_count, 2)
                self.assertEqual(sleep.call_count, 1)

    def test_generic_429_retries_are_bounded(self):
        for proxy in (False, True):
            method = 'post' if proxy else 'request'
            with self.subTest(proxy=proxy), patch.dict(os.environ, {'OLDIES_DRAFT_PROXY_URL': 'https://proxy.example'}), patch.object(worker.requests, method, return_value=FakeResponse(429, {'code': 'rate_limit'})) as transport, patch.object(worker.time, 'sleep') as sleep:
                with self.assertRaises(RuntimeError):
                    if proxy:
                        worker.proxy_draft_request({}, 'fixture')
                    else:
                        worker.wordpress_request('PUT', 'drafts', 'fixture', 'https://oldies.example', data={})
                self.assertEqual(transport.call_count, 4)
                self.assertEqual(sleep.call_count, 3)

    def test_other_409_is_conflict_not_success(self):
        for proxy in (False, True):
            with self.subTest(proxy=proxy), self.assertRaises(RuntimeError):
                self.call_transport(proxy, [FakeResponse(409, {'code': 'payload_conflict'})])

    def test_http_error_body_is_not_logged_or_reported(self):
        for proxy in (False, True):
            with self.subTest(proxy=proxy):
                try:
                    self.call_transport(proxy, [FakeResponse(400, {'code': 'bad_request', 'message': 'PRIVATE_SENTINEL'})])
                except RuntimeError as exc:
                    self.assertNotIn('PRIVATE_SENTINEL', str(exc))
                else:
                    self.fail('Bad request must fail')

    def test_timeout_after_possible_acceptance_is_unknown_no_blind_retry(self):
        for proxy in (False, True):
            method = 'post' if proxy else 'request'
            with self.subTest(proxy=proxy), patch.dict(os.environ, {'OLDIES_DRAFT_PROXY_URL': 'https://proxy.example'}), patch.object(worker.requests, method, side_effect=requests.Timeout('PRIVATE_SENTINEL')) as transport, patch.object(worker.time, 'sleep') as sleep:
                with self.assertRaisesRegex(RuntimeError, 'UNKNOWN_REMOTE_RESULT'):
                    if proxy:
                        worker.proxy_draft_request({}, 'fixture')
                    else:
                        worker.wordpress_request('PUT', 'drafts', 'fixture', 'https://oldies.example', data={})
                self.assertEqual(transport.call_count, 1)
                sleep.assert_not_called()

    def test_non_draft_request_cannot_be_duplicate_success(self):
        for method, path in (('GET', 'drafts'), ('POST', 'publish')):
            with self.subTest(method=method, path=path), patch.object(worker.requests, 'request', return_value=FakeResponse(409, {'code': 'duplicate_draft'})):
                with self.assertRaises(RuntimeError):
                    worker.wordpress_request(method, path, 'fixture', 'https://oldies.example')

    def test_multipart_rewinds_between_retries(self):
        handle = io.BytesIO(b'video-fixture')
        positions = []
        def response(*args, **kwargs):
            positions.append(handle.tell())
            handle.read()
            return FakeResponse(503, {}) if len(positions) == 1 else FakeResponse(201, {'success': True})
        with patch.object(worker.requests, 'request', side_effect=response), patch.object(worker.time, 'sleep'):
            result = worker.wordpress_request('POST', 'drafts', 'fixture', 'https://oldies.example', files={'reel_video': ('test.mp4', handle, 'video/mp4')})
        self.assertTrue(result['success'])
        self.assertEqual(positions, [0, 0])

    def test_retry_after_is_respected_and_bounded(self):
        for proxy in (False, True):
            with self.subTest(proxy=proxy):
                response = FakeResponse(429, {'code': 'rate_limit'})
                response.headers = {'Retry-After': '120'}
                _, _, sleep = self.call_transport(proxy, [response, FakeResponse(201, {'success': True})])
                sleep.assert_called_once_with(120)


if __name__ == '__main__':
    unittest.main()
