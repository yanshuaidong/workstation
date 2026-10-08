"""Offline tests: no real API requests or database writes."""
import base64
import copy
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    review = importlib.import_module("collector.vision_review")
except ModuleNotFoundError as exc:
    if exc.name != "collector.vision_review":
        raise
    review = None


class VisionReviewTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(review, "DeepSeek screenshot review module must exist")
        network = patch("socket.socket.connect", side_effect=AssertionError("Network is forbidden in unit tests"))
        network.start()
        self.addCleanup(network.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.main = self.root / "main"
        self.retail = self.root / "retail"
        for folder in (self.main, self.retail):
            folder.mkdir()
            for vid in (1, 2):
                color = (vid * 60, 255 if folder == self.main else 0, 0)
                Image.new("RGB", (110, 25), color).save(folder / f"contract_{vid:03d}.png")
        self.original = [
            {"id": 1, "key": "im", "main_force": 25.8, "retail": None},
            {"id": 2, "key": "rbm", "main_force": 4.34, "retail": 0.0},
        ]
        self.items = [
            {"id": 1, "key": "im", "main_force": "-25.80", "retail": "1.56"},
            {"id": 2, "key": "rbm", "main_force": "0.37", "retail": "0.00"},
        ]
        self.report = self.root / "result.review.json"

    def content(self, items=None):
        return json.dumps({"items": self.items if items is None else items})

    def test_corrects_sign_decimal_and_missing_ocr_without_mutating_input(self):
        before = copy.deepcopy(self.original)
        result = review.validate_review(self.content(list(reversed(self.items))), self.original)
        self.assertEqual(result, [
            {"id": 1, "key": "im", "main_force": -25.8, "retail": 1.56},
            {"id": 2, "key": "rbm", "main_force": 0.37, "retail": 0.0},
        ])
        self.assertEqual(self.original, before)

    def test_rejects_unclear_or_non_decimal_values(self):
        for bad in (None, True, 1.23, "NaN", "Infinity", "2131", "1.234", "1e2", "数值1.23", "1.23↓"):
            with self.subTest(bad=bad):
                items = copy.deepcopy(self.items)
                items[0]["main_force"] = bad
                with self.assertRaises(review.ReviewError):
                    review.validate_review(self.content(items), self.original)

    def test_rejects_missing_duplicate_extra_or_wrong_identity(self):
        wrong_key = copy.deepcopy(self.items)
        wrong_key[0]["key"] = "wrong"
        bool_id = copy.deepcopy(self.items)
        bool_id[0]["id"] = True
        missing_field = copy.deepcopy(self.items)
        del missing_field[0]["retail"]
        for items in (self.items[:1], self.items * 2, [self.items[0]] * 2, wrong_key, bool_id, missing_field):
            with self.subTest(items=items), self.assertRaises(review.ReviewError):
                review.validate_review(self.content(items), self.original)

    def test_rejects_duplicate_json_members(self):
        content = self.content().replace('"main_force": "-25.80"', '"main_force": null, "main_force": "-25.80"')
        with self.assertRaises(review.ReviewError):
            review.validate_review(content, self.original)

    def test_rejects_invalid_json_and_empty_input(self):
        for content in ("not JSON", "[]", '{"items":null}', '{"items":[NaN]}'):
            with self.subTest(content=content), self.assertRaises(review.ReviewError):
                review.validate_review(content, self.original)
        with self.assertRaises(review.ReviewError):
            review.run_review([], self.main, self.retail, self.report, reviewer=Mock())

    def test_sends_original_images_with_explicit_identity_and_ocr(self):
        client = review.DeepSeekReviewer("test-secret")
        response = {"choices": [{"finish_reason": "stop", "message": {"content": self.content()}}]}
        with patch.object(client, "_post", return_value=response) as post:
            self.assertEqual(client.review_batch(self.original, self.main, self.retail), self.content())
        payload = post.call_args.args[0]
        self.assertEqual(payload["model"], "deepseek-flash")
        blocks = payload["messages"][0]["content"]
        images = [block for block in blocks if block["type"] == "image_url"]
        self.assertEqual(len(images), 4)
        self.assertTrue(all(img["image_url"]["url"].startswith("data:image/png;base64,") for img in images))
        for index in range(1, len(blocks), 2):
            label = json.loads(blocks[index]["text"])
            folder = self.main if label["field"] == "main_force" else self.retail
            expected_bytes = (folder / f"contract_{label['id']:03d}.png").read_bytes()
            encoded = blocks[index + 1]["image_url"]["url"].split(",", 1)[1]
            self.assertEqual(base64.b64decode(encoded), expected_bytes)
        texts = "\n".join(block["text"] for block in blocks if block["type"] == "text")
        for value in ("main_force", "retail", "im", "rbm", "25.8", "null"):
            self.assertIn(value, texts)
        self.assertNotIn("test-secret", json.dumps(payload))

    def test_missing_screenshot_prevents_network_request(self):
        (self.main / "contract_001.png").unlink()
        client = review.DeepSeekReviewer("test-secret")
        with patch.object(client, "_post") as post, self.assertRaises(review.ReviewError):
            client.review_batch(self.original, self.main, self.retail)
        post.assert_not_called()

    def test_truncated_or_missing_response_is_rejected(self):
        client = review.DeepSeekReviewer("test-secret")
        for response in ({}, {"choices": []}, {"choices": [{"finish_reason": "length", "message": {"content": self.content()}}]}):
            with patch.object(client, "_post", return_value=response), self.assertRaises(review.ReviewError):
                client.review_batch(self.original, self.main, self.retail)

    def test_batch_review_writes_audit_and_changes(self):
        client = Mock()
        client.model = "test-model"
        client.review_batch.side_effect = [self.content([item]) for item in self.items]
        result = review.run_review(self.original, self.main, self.retail, self.report, reviewer=client, batch_size=1)
        self.assertEqual(len(result), 2)
        self.assertEqual(client.review_batch.call_count, 2)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "passed")
        self.assertEqual(len(report["changes"]), 3)
        self.assertEqual(report["ocr_result"], self.original)
        self.assertEqual(report["reviewed_result"], result)

    def test_failed_batch_preserves_partial_audit_and_stops(self):
        client = Mock()
        client.model = "test-model"
        client.review_batch.side_effect = [self.content(self.items[:1]), review.ReviewError("unclear image")]
        with self.assertRaises(review.ReviewError):
            review.run_review(self.original, self.main, self.retail, self.report, reviewer=client, batch_size=1)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(len(report["reviewed_result"]), 1)
        self.assertIn("unclear image", report["error"])

    def test_reads_root_env_without_polluting_database_environment(self):
        env_path = self.root / ".env"
        env_path.write_text("DEEPSEEK_KEY=root-secret\nDB_HOST=wrong-host\n", encoding="utf-8")
        with patch.dict(os.environ, {"DB_HOST": "existing-host"}, clear=True), patch.object(review, "ROOT_ENV_PATH", env_path):
            client = review.DeepSeekReviewer.from_env()
            self.assertEqual(client.api_key, "root-secret")
            self.assertEqual(os.environ["DB_HOST"], "existing-host")
            self.assertNotIn("DEEPSEEK_KEY", os.environ)
        with patch.dict(os.environ, {"DEEPSEEK_KEY": "environment-secret"}, clear=True), patch.object(review, "ROOT_ENV_PATH", env_path):
            self.assertEqual(review.DeepSeekReviewer.from_env().api_key, "environment-secret")

    def test_missing_key_fails_without_api_call(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(review, "ROOT_ENV_PATH", self.root / "absent"), self.assertRaises(review.ReviewError):
            review.DeepSeekReviewer.from_env()

    def test_transport_retries_transient_failures_and_sets_auth_timeout(self):
        client = review.DeepSeekReviewer("test-secret")
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"choices": []}'
        with patch.object(review, "urlopen", side_effect=[URLError("temporary"), response]) as request, patch.object(review.time, "sleep"):
            self.assertEqual(client._post({"model": "deepseek-flash"}), {"choices": []})
        self.assertEqual(request.call_count, 2)
        req = request.call_args.args[0]
        self.assertEqual(req.full_url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(req.get_header("Authorization"), "Bearer test-secret")
        self.assertGreater(request.call_args.kwargs["timeout"], 0)

    def test_auth_failure_is_not_retried_and_does_not_expose_secret(self):
        client = review.DeepSeekReviewer("test-secret")
        error = HTTPError("https://api.deepseek.com/chat/completions", 401, "test-secret", {}, None)
        with patch.object(review, "urlopen", side_effect=error) as request, self.assertRaises(review.ReviewError) as caught:
            client._post({})
        self.assertEqual(request.call_count, 1)
        self.assertIn("401", str(caught.exception))
        self.assertNotIn("test-secret", str(caught.exception))

    def test_atomic_write_keeps_previous_file_on_serialization_failure(self):
        path = self.root / "final.json"
        path.write_text("previous", encoding="utf-8")
        with self.assertRaises(ValueError):
            review.write_json_atomic(path, {"bad": float("nan")})
        self.assertEqual(path.read_text(), "previous")
        self.assertEqual(list(self.root.glob("*.tmp")), [])
        review.write_json_atomic(path, {"ok": 1.23})
        self.assertEqual(json.loads(path.read_text()), {"ok": 1.23})

    def test_invalid_model_reply_is_saved_for_manual_inspection(self):
        client = Mock(model="test-model")
        client.review_batch.return_value = "invalid JSON"
        with self.assertRaises(review.ReviewError):
            review.run_review(self.original, self.main, self.retail, self.report, reviewer=client)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["batches"][0]["response"], "invalid JSON")

    def test_rate_limit_and_server_errors_retry(self):
        for status in (429, 500, 503):
            client = review.DeepSeekReviewer("test-secret", max_attempts=2)
            error = HTTPError("https://api.deepseek.com/chat/completions", status, "error", {}, None)
            with self.subTest(status=status), patch.object(review, "urlopen", side_effect=error) as request, patch.object(review.time, "sleep"), self.assertRaises(review.ReviewError):
                client._post({})
            self.assertEqual(request.call_count, 2)

    def test_retry_exhaustion_stops(self):
        client = review.DeepSeekReviewer("test-secret", max_attempts=2)
        with patch.object(review, "urlopen", side_effect=TimeoutError()) as request, patch.object(review.time, "sleep"), self.assertRaises(review.ReviewError):
            client._post({})
        self.assertEqual(request.call_count, 2)


if __name__ == "__main__":
    unittest.main()
