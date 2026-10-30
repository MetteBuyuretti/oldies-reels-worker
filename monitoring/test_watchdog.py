import unittest
from datetime import datetime, timezone
from watchdog import collect, alert, WORKFLOW_SELF

NOW = datetime(2026, 10, 9, 0, 0, tzinfo=timezone.utc)

class API:
    def __init__(self, runs, workflows=None):
        self.runs = runs
        self.workflows = workflows if workflows is not None else [{'id': 42, 'path': '.github/workflows/publisher.yml',
                                      'name': 'publisher', 'state': 'active'}]
        self.posted = []
        self.issues = []

    def request(self, path, *, method='GET', data=None):
        if method == 'POST':
            self.posted.append(data)
            self.issues.append({'title': data['title']})
            return {}
        if path.startswith('/actions/workflows?'):
            return {'workflows': self.workflows if 'page=1' in path else []}
        if '/runs?' in path:
            return {'workflow_runs': self.runs}
        if path.startswith('/issues?'):
            return list(self.issues)
        raise AssertionError(path)

class WatchdogTests(unittest.TestCase):
    def self_api(self, runs):
        return API(runs, workflows=[dict(id=42, path=WORKFLOW_SELF,
                                        name='watchdog', state='active')])

    def test_current_audit_does_not_hide_previous_schedule_gap(self):
        current = dict(id=9, status='in_progress', created_at='2026-10-09T00:00:00Z')
        prior = dict(id=8, status='completed', conclusion='success',
                     created_at='2026-10-08T16:00:00Z')
        a = self.self_api([current, prior])
        findings, _, _ = collect(a, {'self_schedule_freshness_hours': 3}, NOW,
                                current_run_id='9')
        self.assertEqual(findings[0]['reason'], 'watchdog_schedule_gap')
        self.assertEqual(findings[0]['run_id'], 8)
        self.assertEqual(alert(a, findings, {'.github/workflows/publisher.yml'}), 0)

    def test_completed_current_audit_does_not_hide_gap(self):
        current = dict(id=9, status='completed', conclusion='success',
                       created_at='2026-10-09T00:00:00Z')
        prior = dict(id=8, status='completed', conclusion='success',
                     created_at='2026-10-08T16:00:00Z')
        findings, _, _ = collect(self.self_api([current, prior]),
                                {'self_schedule_freshness_hours': 3}, NOW, current_run_id='9')
        self.assertEqual(findings[0]['run_id'], 8)

    def test_recent_watchdog_schedule_is_not_flagged(self):
        prior = dict(id=8, status='completed', conclusion='success',
                     created_at='2026-10-08T23:00:00Z')
        self.assertEqual(collect(self.self_api([prior]),
                                 {'self_schedule_freshness_hours': 3}, NOW)[0], [])

    def test_first_watchdog_audit_has_no_prior_gap(self):
        current = dict(id=9, status='in_progress', created_at='2026-10-09T00:00:00Z')
        self.assertEqual(collect(self.self_api([current]),
                                 {'self_schedule_freshness_hours': 3}, NOW, current_run_id='9')[0], [])

    def test_unconfigured_self_monitoring_preserves_existing_behavior(self):
        prior = dict(id=8, status='completed', conclusion='success',
                     created_at='2026-10-08T16:00:00Z')
        self.assertEqual(collect(self.self_api([prior]), {}, NOW)[0], [])

    def test_success_is_healthy(self):
        a = API([dict(id=5, status='completed', conclusion='success', created_at='2026-10-08T23:00:00Z')])
        self.assertEqual(collect(a, {}, NOW)[0], [])

    def test_failed_run_is_flagged(self):
        a = API([dict(id=5, status='completed', conclusion='failure', created_at='2026-10-08T23:00:00Z')])
        findings, _, _ = collect(a, {}, NOW)
        self.assertEqual(findings[0]['reason'], 'failed_run')
        self.assertEqual(alert(a, findings, {'.github/workflows/publisher.yml'}), 1)
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
        self.assertEqual(alert(a, findings, {'.github/workflows/publisher.yml'}), 0)  # no false outage issue

    def test_old_manual_preview_failure_is_not_alerted(self):
        a = API([dict(id=12, status='completed', conclusion='failure',
                      created_at='2026-09-26T12:00:00Z')])
        findings, healthy, unchecked = collect(a, {'manual_workflow_lookback_hours': 48}, NOW)
        self.assertEqual(findings, [])
        self.assertEqual(unchecked, ['.github/workflows/publisher.yml'])

    def test_alert_only_monitored_workflows_and_no_duplicates(self):
        a = API([])
        monitored = '.github/workflows/publisher.yml'
        findings = [
            dict(path=monitored, name='publisher', reason='failed_run', run_id=19, url='https://github.com/run/19'),
            dict(path='.github/workflows/legacy-preview.yml', name='legacy', reason='failed_run', run_id=18, url='https://github.com/run/18'),
        ]
        self.assertEqual(alert(a, findings, {monitored}), 1)
        self.assertEqual(alert(a, findings, {monitored}), 0)
        self.assertEqual(len(a.posted), 1)


"""Offline run-state regressions. No network or publishing calls."""
import io
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
import watchdog


STATE_NOW = datetime(2026, 10, 31, 0, 0, tzinfo=timezone.utc)
PATH = '.github/workflows/publisher.yml'
CONFIG = {'expected_freshness_hours': {PATH: 36}}

class NeverWriteAPI:
    def request(self, *args, **kwargs):
        raise AssertionError('Informational states must not access issue API')


class RunStateTests(unittest.TestCase):
    def collect(self, *, status='completed', conclusion='skipped',
                created_at='2026-10-30T23:00:00Z'):
        return watchdog.collect(API([dict(id=7, status=status, conclusion=conclusion,
                                         created_at=created_at)]), CONFIG, STATE_NOW)

    def test_scheduled_skip_is_visible_and_not_healthy(self):
        findings, healthy, _ = self.collect()
        self.assertEqual(healthy, [])
        self.assertEqual(findings[0]['reason'], 'run_skipped')
        self.assertTrue(findings[0]['informational'])
        self.assertEqual(watchdog.alert(NeverWriteAPI(), findings, {PATH}), 0)

    def test_pending_or_running_is_not_a_success(self):
        for state in ('queued', 'in_progress', 'waiting', 'pending'):
            with self.subTest(state=state):
                findings, healthy, _ = self.collect(status=state, conclusion=None)
                self.assertEqual(healthy, [])
                self.assertEqual(findings[0]['reason'], 'run_pending')
                self.assertTrue(findings[0]['informational'])
                self.assertEqual(watchdog.alert(NeverWriteAPI(), findings, {PATH}), 0)

    def test_cancelled_neutral_unknown_are_not_success(self):
        for conclusion in ('cancelled', 'neutral', 'stale', None):
            with self.subTest(conclusion=conclusion):
                findings, healthy, _ = self.collect(conclusion=conclusion)
                self.assertEqual(healthy, [])
                self.assertEqual(findings[0]['reason'], 'run_not_success')
                self.assertTrue(findings[0]['informational'])
                self.assertEqual(watchdog.alert(NeverWriteAPI(), findings, {PATH}), 0)

    def test_completed_success_remains_workflow_success_only(self):
        findings, healthy, _ = self.collect(conclusion='success')
        self.assertEqual(findings, [])
        self.assertEqual(healthy, [PATH])

    def test_old_skip_still_raises_existing_freshness_incident(self):
        findings, healthy, _ = self.collect(created_at='2026-10-29T00:00:00Z')
        self.assertEqual(healthy, [])
        self.assertEqual(findings[0]['reason'], 'late_run')
        self.assertFalse(findings[0].get('informational', False))
        api = API([])
        self.assertEqual(watchdog.alert(api, findings, {PATH}), 1)
        self.assertEqual(watchdog.alert(api, findings, {PATH}), 0)

    def test_stalled_pending_still_raises_existing_incident(self):
        findings, healthy, _ = self.collect(status='in_progress', conclusion=None,
                                            created_at='2026-10-30T20:00:00Z')
        self.assertEqual(findings[0]['reason'], 'stalled_run')
        self.assertFalse(findings[0].get('informational', False))
        self.assertEqual(healthy, [])

    def test_skipped_run_never_claims_recovery_after_failure(self):
        latest = dict(id=8, status='completed', conclusion='skipped',
                      created_at='2026-10-30T23:00:00Z')
        older = dict(id=7, status='completed', conclusion='failure',
                     created_at='2026-10-30T22:00:00Z')
        findings, healthy, _ = watchdog.collect(API([latest, older]), CONFIG, STATE_NOW)
        self.assertEqual(healthy, [])
        self.assertEqual(findings[0]['reason'], 'run_skipped')
        self.assertNotIn('recovered_after_recent_failure', [f['reason'] for f in findings])

    def test_summary_separates_review_info_and_delivery_evidence(self):
        findings, healthy, unchecked = self.collect()
        text = watchdog.render_summary(findings, healthy, unchecked)
        self.assertIn('Completed success runs (delivery not verified): 0', text)
        self.assertIn('Requires review: 0', text)
        self.assertIn('Informational/non-success state: 1', text)
        self.assertIn('run_skipped', text)
        self.assertIn('publication delivery is NOT verified', text)

    def test_main_uses_real_classification_without_issue_side_effect(self):
        api = API([dict(id=7, status='completed', conclusion='skipped',
                        created_at='2026-10-30T23:00:00Z')])
        with patch.object(watchdog, 'GitHub', return_value=api), \
             patch.object(watchdog.json, 'loads', return_value=dict(CONFIG, issue_alerts_enabled=True)), \
             patch.object(watchdog, 'datetime') as date, \
             patch.dict(watchdog.os.environ, {'GITHUB_REPOSITORY':'fixture/repo',
                                               'GITHUB_TOKEN':'fixture-only',
                                               'GITHUB_STEP_SUMMARY':''}), \
             patch('sys.stdout', new_callable=io.StringIO) as stdout:
            date.now.return_value = STATE_NOW
            date.fromisoformat.side_effect = datetime.fromisoformat
            self.assertEqual(watchdog.main(), 0)
        self.assertIn('Completed success runs (delivery not verified): 0', stdout.getvalue())
        self.assertIn('Informational/non-success state: 1', stdout.getvalue())
        self.assertEqual(api.posted, [])


if __name__ == '__main__':
    unittest.main()
