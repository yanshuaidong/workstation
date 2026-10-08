"""Pipeline tests replace desktop OCR/API/database boundaries only."""
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pipeline


class TodayReviewPipelineTests(unittest.TestCase):
    def setUp(self):
        network = patch("socket.socket.connect", side_effect=AssertionError("Network is forbidden in unit tests"))
        network.start()
        self.addCleanup(network.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.out = self.root / "result.json"
        self.original = [{"id": 1, "key": "im", "main_force": 25.8, "retail": 1.56}]
        self.corrected = [{"id": 1, "key": "im", "main_force": -25.8, "retail": 1.56}]
        self.events = []
        self.ocr = types.ModuleType("collector.ocr")
        self.ocr.run_today = Mock(side_effect=self.basic_ocr)
        self.ocr.run_history = Mock(return_value=[])
        self.screenshot = types.ModuleType("collector.screenshot")
        self.screenshot.screenshot_dir_for = lambda cfg, key: self.root / key
        self.screenshot.history_screenshot_dir_for = lambda cfg, key: self.root / ("history_" + key)
        self.review = types.ModuleType("collector.vision_review")
        self.review.run_review = Mock(side_effect=self.review_ocr)
        self.review.write_json_atomic = self.write_json
        self.anomaly = types.ModuleType("trading.anomaly.detector")
        self.anomaly.run_anomaly_detection = Mock(return_value=0)
        self.modules = patch.dict(sys.modules, {
            "trading.anomaly.detector": self.anomaly,
            "collector.ocr": self.ocr,
            "collector.screenshot": self.screenshot,
            "collector.vision_review": self.review,
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)

    def write_json(self, path, result):
        path.write_text(json.dumps(result), encoding="utf-8")

    def basic_ocr(self, main_dir, retail_dir, out_path, total_count):
        self.events.append("ocr")
        self.write_json(out_path, self.original)
        return self.original

    def review_ocr(self, result, main_dir, retail_dir, report_path):
        self.events.append("review")
        self.assertEqual(result, self.original)
        self.assertFalse(self.out.exists(), "Unverified results must not be uploadable")
        return self.corrected

    def test_today_publishes_reviewed_result_and_preserves_basic_ocr(self):
        result = pipeline.step_ocr("today", {}, self.out)
        self.assertEqual(self.events, ["ocr", "review"])
        self.assertEqual(result, self.corrected)
        self.assertEqual(json.loads(self.out.read_text()), self.corrected)
        self.assertEqual(json.loads((self.root / "result.ocr.json").read_text()), self.original)

    def test_failed_review_removes_uploadable_old_result_but_keeps_backup(self):
        self.out.write_text('[{"old": true}]', encoding="utf-8")
        self.review.run_review.side_effect = RuntimeError("review failed")
        with self.assertRaisesRegex(RuntimeError, "review failed"):
            pipeline.step_ocr("today", {}, self.out)
        self.assertFalse(self.out.exists())
        self.assertEqual(json.loads((self.root / "result.previous.json").read_text()), [{"old": True}])
        self.assertTrue((self.root / "result.ocr.json").exists())

    def test_ocr_failure_also_invalidates_old_result(self):
        self.out.write_text("[]", encoding="utf-8")
        self.ocr.run_today.side_effect = RuntimeError("ocr failed")
        with self.assertRaisesRegex(RuntimeError, "ocr failed"):
            pipeline.step_ocr("today", {}, self.out)
        self.assertFalse(self.out.exists())
        self.review.run_review.assert_not_called()

    def test_history_keeps_existing_behavior(self):
        pipeline.step_ocr("history", {}, self.out, history_count=3)
        self.review.run_review.assert_not_called()
        self.ocr.run_history.assert_called_once_with(self.root / "history_main_force", self.root / "history_retail", self.out, 3, None)

    def test_dry_run_does_not_touch_files_or_call_ocr_review(self):
        self.out.write_text("old result", encoding="utf-8")
        self.assertEqual(pipeline.step_ocr("today", {}, self.out, dry_run=True), [])
        self.assertEqual(self.out.read_text(), "old result")
        self.ocr.run_today.assert_not_called()
        self.review.run_review.assert_not_called()

    def test_full_run_stops_upload_and_close_sync_on_review_failure(self):
        self.review.run_review.side_effect = RuntimeError("review failed")
        with patch.object(pipeline, "DATA_DIR", self.root), patch.object(pipeline, "setup_logging"), patch.object(pipeline, "load_calibration", return_value={}), patch.object(pipeline, "load_varieties", return_value=[]), patch.object(pipeline, "generate_trade_dates", return_value=["2026-10-08"]), patch.object(pipeline, "step_screenshot"), patch.object(pipeline, "step_upload") as upload, patch.object(pipeline, "step_close_sync") as close:
            with self.assertRaises(SystemExit) as caught:
                pipeline.run("today")
        self.assertEqual(caught.exception.code, 1)
        upload.assert_not_called()
        close.assert_not_called()
        self.anomaly.run_anomaly_detection.assert_not_called()

    def test_full_run_uploads_only_reviewed_values(self):
        with patch.object(pipeline, "DATA_DIR", self.root), patch.object(pipeline, "setup_logging"), patch.object(pipeline, "load_calibration", return_value={}), patch.object(pipeline, "load_varieties", return_value=[]), patch.object(pipeline, "generate_trade_dates", return_value=["2026-10-08"]), patch.object(pipeline, "step_screenshot"), patch.object(pipeline, "step_upload") as upload, patch.object(pipeline, "step_close_sync") as close:
            pipeline.run("today")
        upload.assert_called_once_with(self.corrected, ["2026-10-08"], [], dry_run=False)
        close.assert_called_once()
        self.anomaly.run_anomaly_detection.assert_called_once_with("2026-10-08")

    def test_no_upload_still_runs_review_without_any_database_steps(self):
        with patch.object(pipeline, "DATA_DIR", self.root), patch.object(pipeline, "setup_logging"), patch.object(pipeline, "load_calibration", return_value={}), patch.object(pipeline, "load_varieties", return_value=[]), patch.object(pipeline, "generate_trade_dates", return_value=["2026-10-08"]), patch.object(pipeline, "step_screenshot"), patch.object(pipeline, "step_upload") as upload, patch.object(pipeline, "step_close_sync") as close:
            pipeline.run("today", skip_upload=True)
        self.assertEqual(self.events, ["ocr", "review"])
        upload.assert_not_called()
        close.assert_not_called()
        self.anomaly.run_anomaly_detection.assert_not_called()

    def test_upload_only_refuses_after_failed_review(self):
        self.out.write_text("[]", encoding="utf-8")
        self.review.run_review.side_effect = RuntimeError("review failed")
        with self.assertRaises(RuntimeError):
            pipeline.step_ocr("today", {}, self.out)
        with patch.object(pipeline, "DATA_DIR", self.root), patch.object(pipeline, "setup_logging"), patch.object(pipeline, "step_upload") as upload:
            with self.assertRaises(SystemExit) as caught:
                pipeline.run_upload_only()
        self.assertEqual(caught.exception.code, 1)
        upload.assert_not_called()

    def test_screenshot_failure_invalidates_old_result_before_ocr(self):
        self.out.write_text('[{"old": true}]', encoding="utf-8")
        with patch.object(pipeline, "DATA_DIR", self.root), patch.object(pipeline, "setup_logging"), patch.object(pipeline, "load_calibration", return_value={}), patch.object(pipeline, "load_varieties", return_value=[]), patch.object(pipeline, "generate_trade_dates", return_value=["2026-10-08"]), patch.object(pipeline, "step_screenshot", side_effect=RuntimeError("screenshot failed")), patch.object(pipeline, "step_upload") as upload:
            with self.assertRaises(SystemExit):
                pipeline.run("today")
        self.assertFalse(self.out.exists())
        self.assertEqual(json.loads((self.root / "result.previous.json").read_text()), [{"old": True}])
        self.ocr.run_today.assert_not_called()
        upload.assert_not_called()

    def test_ocr_only_today_also_reviews(self):
        with patch.object(pipeline, "DATA_DIR", self.root), patch.object(pipeline, "setup_logging"), patch.object(pipeline, "load_calibration", return_value={}):
            self.assertEqual(pipeline.run_ocr_only("today"), self.corrected)
        self.assertEqual(self.events, ["ocr", "review"])


if __name__ == "__main__":
    unittest.main()
