import copy
import unittest
from datetime import datetime, timezone

from retention_policy import retention_decision


class RetentionTests(unittest.TestCase):
    NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)
    ASSET = {'id': 42, 'created_at': '2026-09-01T00:00:00Z'}

    def decide(self, receipt=None, asset=None):
        return retention_decision(asset or self.ASSET, receipt, now=self.NOW)

    def receipt(self, status, **changes):
        return {'asset_id': 42, 'delivery_acknowledged': True, 'status': status, **changes}

    def test_crash_after_upload_before_acknowledgement(self):
        self.assertEqual(self.decide()['action'], 'KEEP')

    def test_timeout_after_wp_acceptance_retains_without_receipt(self):
        self.assertEqual(self.decide({'delivery_acknowledged': False})['action'], 'KEEP')

    def test_stale_undelivered_artifact(self):
        self.assertIn('delivery_unresolved', self.decide()['reason'])

    def test_active_states_never_expire(self):
        for status in ('DRAFT_REVIEW', 'READY_FOR_EDITS', 'BLOCKED'):
            with self.subTest(status=status):
                self.assertEqual(self.decide(self.receipt(status, backup_verified=True))['action'], 'KEEP')

    def test_old_delivered_artifact_alone_is_not_cleanup_permission(self):
        self.assertEqual(self.decide(self.receipt('READY_FOR_EDITS'))['action'], 'KEEP')

    def test_published_requires_verified_id_and_final_url(self):
        for changes in ({}, {'instagram_verified': True, 'instagram_media_id': '123'}, {'instagram_verified': True, 'final_media_url': 'https://example.test/final.mp4'}):
            with self.subTest(changes=changes):
                self.assertEqual(self.decide(self.receipt('PUBLISHED', backup_verified=True, **changes))['action'], 'KEEP')

    def test_verified_published_with_backup_is_review_only(self):
        receipt = self.receipt('PUBLISHED', instagram_verified=True, instagram_media_id='123', final_media_url='https://example.test/final.mp4', backup_verified=True)
        self.assertEqual(self.decide(receipt)['action'], 'REVIEW_ONLY')

    def test_terminal_states_require_backup(self):
        for status in ('REJECTED', 'ARCHIVED', 'LEGACY_TEST'):
            with self.subTest(status=status):
                self.assertEqual(self.decide(self.receipt(status))['action'], 'KEEP')
                self.assertEqual(self.decide(self.receipt(status, backup_verified=True))['action'], 'REVIEW_ONLY')

    def test_unknown_state_and_wrong_asset_are_preserved(self):
        self.assertEqual(self.decide(self.receipt('UNRECOGNIZED', backup_verified=True))['action'], 'KEEP')
        receipt = self.receipt('ARCHIVED', backup_verified=True)
        receipt['asset_id'] = 43
        self.assertEqual(self.decide(receipt)['action'], 'KEEP')

    def test_repeat_is_idempotent_and_inputs_not_mutated(self):
        receipt = self.receipt('ARCHIVED', backup_verified=True)
        before = copy.deepcopy(receipt)
        self.assertEqual(self.decide(receipt), self.decide(receipt))
        self.assertEqual(before, receipt)

    def test_malformed_naive_future_and_recent_timestamps(self):
        for value in ('', 'bad', '2026-09-01', '2027-09-01T00:00:00Z', '2026-09-29T00:00:00Z'):
            with self.subTest(value=value):
                self.assertEqual(self.decide(asset={'id': 42, 'created_at': value})['action'], 'KEEP')


if __name__ == '__main__':
    unittest.main()
