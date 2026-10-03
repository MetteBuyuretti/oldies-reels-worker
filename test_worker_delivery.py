import os
import unittest
from unittest.mock import patch

import worker


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = str(payload)

    def json(self):
        return self._payload


class DraftDeliveryIdempotencyTests(unittest.TestCase):
    def duplicate_response(self):
        return FakeResponse(
            409,
            {
                "code": "duplicate_draft",
                "message": "Aynı sanatçı, tarih ve konu için zaten bir taslak bulunuyor.",
                "data": {"status": 409},
            },
        )

    def test_wordpress_duplicate_draft_is_idempotent_success(self):
        with patch.object(worker.requests, "request", return_value=self.duplicate_response()):
            result = worker.wordpress_request(
                "PUT",
                "drafts",
                "test-secret",
                "https://oldies.example",
                data={"artist": "Eagles"},
            )
        self.assertTrue(result["success"])
        self.assertTrue(result["skipped"])
        self.assertEqual(result["reason"], "duplicate_draft")

    def test_proxy_duplicate_draft_is_idempotent_success(self):
        with patch.dict(os.environ, {"OLDIES_DRAFT_PROXY_URL": "https://proxy.example"}, clear=False):
            with patch.object(worker.requests, "post", return_value=self.duplicate_response()):
                result = worker.proxy_draft_request({"artist": "Eagles"}, "test-secret")
        self.assertTrue(result["success"])
        self.assertTrue(result["skipped"])
        self.assertEqual(result["reason"], "duplicate_draft")


if __name__ == "__main__":
    unittest.main()
