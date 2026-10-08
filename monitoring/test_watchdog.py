import unittest
from datetime import datetime, timezone
from watchdog import collect, alert

NOW = datetime(2026, 10, 9, 0, 0, tzinfo=timezone.utc)

class API:
    def __init__(self, runs, workflows=None):
        self.runs = runs
        self.workflows = workflows if workflows is not None else [{'id': 42, 'path': '.github/workflows/publisher.yml',
                                      'name': 'publisher', 'state': 'active'}]
        self.posted = []

    def request(self, path, *, method='GET', data=None):
        if method == 'POST':
            self.posted.append(data)
            return {}
        if path.startswith('/actions/workflows?'):
            return {'workflows': self.workflows if 'page=1' in path else []}
        if '/runs?' in path:
            return {'workflow_runs': self.runs}
        if path.startswith('/issues?'):
            return []
        raise AssertionError(path)

class WatchdogTests(unittest.TestCase):
    def test_success_is_healthy(self):
        a = API([dict(id=5, status='completed', conclusion='success', created_at='2026-10-08T23:00:00Z')])
        self.assertEqual(collect(a, {}, NOW)[0], [])

    def test_failed_run_is_flagged(self):
        a = API([dict(id=5, status='completed', conclusion='failure', created_at='2026-10-08T23:00:00Z')])
        findings, _, _ = collect(a, {}, NOW)
        self.assertEqual(findings[0]['reason'], 'failed_run')
        self.assertEqual(alert(a, findings), 1)
        self.assertIn('Do not rerun', a.posted[0]['body'])

    def test_stalled_run(self):
        a = API([dict(id=5, status='in_progress', conclusion=None, created_at='2026-10-08T19:00:00Z')])
        self.assertEqual(collect(a, {'stalled_hours': 3}, NOW)[0][0]['reason'], 'stalled_run')

    def test_schedule_freshness(self):
        a = API([dict(id=5, status='completed', conclusion='success', created_at='2026-10-07T22:00:00Z')])
        config = {'expected_freshness_hours': {'.github/workflows/publisher.yml': 24}}
        self.assertEqual(collect(a, config, NOW)[0][0]['reason'], 'late_run')

    def test_no_run_without_config_is_not_false_alarm(self):
        self.assertEqual(collect(API([]), {}, NOW)[0], [])

    def test_workflow_missing(self):
        a = API([], workflows=[dict(id=10, path='other', name='other', state='active')])
        config = {'expected_freshness_hours': {'.github/workflows/required.yml': 24}}
        self.assertEqual(collect(a, config, NOW)[0][0]['reason'], 'workflow_missing_or_disabled')

    def test_scheduled_recovered_failure_is_reported_without_alert(self):
        success = dict(id=8, status='completed', conclusion='success',
                       created_at='2026-10-08T18:00:00Z',
                       html_url='https://github.com/example/run/8')
        failed = dict(id=7, status='completed', conclusion='failure',
                      created_at='2026-10-07T18:00:00Z',
                      html_url='https://github.com/example/run/7')
        a = API([success, failed])
        config = {'expected_freshness_hours': {'.github/workflows/publisher.yml': 36}}
        findings, healthy, _ = collect(a, config, NOW)
        self.assertEqual(findings[0]['reason'], 'recovered_after_recent_failure')
        self.assertEqual(findings[0]['run_id'], 7)
        self.assertEqual(alert(a, findings), 0)  # no false outage issue

if __name__ == '__main__':
    unittest.main()
