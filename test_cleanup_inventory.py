import io
import json
import os
import unittest
import urllib.error
from contextlib import redirect_stdout
from unittest.mock import patch

import cleanup_inventory


class InventoryTests(unittest.TestCase):
    def run_inventory(self, responses):
        requests = []
        def open_read(request, timeout):
            requests.append(request)
            value = responses[len(requests) - 1]
            if isinstance(value, Exception):
                raise value
            return io.BytesIO(json.dumps(value).encode())
        output = io.StringIO()
        with patch.dict(os.environ, {'REPOSITORY': 'MetteBuyuretti/oldies-reels-worker'}, clear=True), patch.object(cleanup_inventory.urllib.request, 'urlopen', side_effect=open_read), redirect_stdout(output):
            cleanup_inventory.main()
        return requests, output.getvalue()

    def test_old_and_active_assets_are_only_inventoried_with_anonymous_get(self):
        assets = [{'id': 42, 'name': 'old.mp4', 'created_at': '2020-01-01T00:00:00Z'}, {'id': 43, 'name': 'active.mp4', 'created_at': '2020-01-01T00:00:00Z'}, {'id': 44, 'name': 'notes.txt'}]
        requests, output = self.run_inventory([{'id': 9}, assets])
        self.assertEqual(len(requests), 2)
        for request in requests:
            self.assertEqual(request.get_method(), 'GET')
            self.assertIsNone(request.data)
            self.assertFalse(any(k.lower() == 'authorization' for k in request.headers))
        decisions = [json.loads(line) for line in output.splitlines() if line.startswith('{')]
        self.assertEqual([x['asset_id'] for x in decisions], [42, 43])
        self.assertTrue(all(x['action'] == 'KEEP' for x in decisions))
        self.assertIn('zero writes/deletes', output)

    def test_all_pages_are_read_and_every_unresolved_asset_is_kept(self):
        page = [{'id': i, 'name': str(i) + '.mp4', 'created_at': '2020-01-01T00:00:00Z'} for i in range(1, 101)]
        requests, output = self.run_inventory([{'id': 9}, page, [{'id': 101, 'name': 'last.mp4', 'created_at': '2020-01-01T00:00:00Z'}]])
        self.assertEqual(len(requests), 3)
        self.assertIn('page=2', requests[-1].full_url)
        self.assertEqual(output.count('"action": "KEEP"'), 101)

    def test_absent_release_is_a_read_only_no_op(self):
        error = urllib.error.HTTPError('https://example.test', 404, 'fixture', {}, None)
        requests, output = self.run_inventory([error])
        self.assertEqual(len(requests), 1)
        self.assertIn('nothing to inventory', output)

    def test_http_failure_is_sanitized_and_not_retried_as_mutation(self):
        error = urllib.error.HTTPError('https://example.test', 403, 'fixture-private-body', {}, io.BytesIO(b'fixture-private-body'))
        with self.assertRaisesRegex(RuntimeError, '^GitHub inventory HTTP 403$'):
            self.run_inventory([error])

    def test_network_failure_is_sanitized_without_remote_mutation(self):
        with self.assertRaisesRegex(RuntimeError, '^GitHub inventory read failed; no remote writes attempted$'):
            self.run_inventory([urllib.error.URLError('fixture-private-body')])

    def test_invalid_metadata_fails_closed(self):
        for responses in ([['wrong release']], [{'id': 9}, {'unexpected': 'assets'}], [{'id': 9}, ['wrong asset']]):
            with self.subTest(responses=responses), self.assertRaisesRegex(RuntimeError, '^GitHub inventory invalid'):
                self.run_inventory(responses)


if __name__ == '__main__':
    unittest.main()
