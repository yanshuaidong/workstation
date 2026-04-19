import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from routes import assistant_routes


class AssistantSignalExplanationTests(unittest.TestCase):
    def test_all_indicator_labels_are_mapped(self):
        expected_labels = {
            "MF_Edge3": "主力三连变起点",
            "MF_Accel": "趋势加速度",
            "MF_Duration": "趋势持续天数",
            "MS_Divergence": "主散背离强度",
            "MF_Magnitude": "主力变化幅度",
            "MF_BreakZone": "区域突破信号",
            "Composite_Score": "综合评分",
        }

        for indicator, label in expected_labels.items():
            with self.subTest(indicator=indicator):
                result = assistant_routes._build_signal_explanation(indicator, "LONG", "示例", 0.6, {})
                self.assertEqual(result["indicator_label_cn"], label)

    def test_build_signal_explanation_for_accel(self):
        result = assistant_routes._build_signal_explanation(
            "MF_Accel",
            "LONG",
            "加速(+2.62)",
            2.62,
            {
                "delta1": 3.0,
                "delta2": 5.62,
                "acceleration": 2.62,
            },
        )

        self.assertEqual(result["indicator_label_cn"], "趋势加速度")
        self.assertEqual(result["indicator_short_desc"], "第二步变化是否比第一步更猛")
        self.assertEqual(result["strength_level"], "极强")
        self.assertIn("第二步变化幅度", result["calc_explanation"])
        self.assertIn("加速", result["indicator_display_value"])
        self.assertIn("偏多", result["judgement_title"])
        self.assertIn("主力连续走强", result["judgement_reason"])
        self.assertEqual(len(result["calc_sections"]), 4)
        self.assertIn("delta1 = 3.00", " ".join(result["calc_sections"][0]["items"]))
        self.assertIn("当前 strength 字段就是加速度 2.62", result["strength_explanation"])

    def test_build_signal_explanation_for_composite_score(self):
        result = assistant_routes._build_signal_explanation(
            "Composite_Score",
            "SHORT",
            "1.40",
            1.2,
            {
                "components": {
                    "duration_score": 2,
                    "accel_score": 1,
                    "edge_score": 1,
                    "divergence_score": 1,
                    "magnitude_score": 0,
                },
                "window_quantiles": {
                    "edge_p10": -30.0,
                    "edge_p20": -10.0,
                    "edge_p80": 12.0,
                    "edge_p90": 22.0,
                    "magnitude_p25": 5.0,
                    "magnitude_p75": 9.0,
                },
                "streak_length": 5,
                "current_magnitude": 7.8,
            },
        )

        self.assertEqual(result["indicator_label_cn"], "综合评分")
        self.assertEqual(result["strength_level"], "极强")
        self.assertIn("加权合成", result["calc_explanation"])
        self.assertIn("1.40", result["indicator_display_value"])
        self.assertIn("偏空", result["judgement_title"])
        self.assertIn("0.30", " ".join(result["calc_sections"][1]["items"]))
        self.assertIn("duration(2 x 0.30)", " ".join(result["calc_sections"][2]["items"]))
        self.assertIn("当前 strength 字段就是综合得分 1.20", result["strength_explanation"])

    def test_build_signal_explanation_handles_missing_strength_and_value(self):
        result = assistant_routes._build_signal_explanation(
            "MF_BreakZone",
            "SHORT",
            "",
            None,
            {},
        )

        self.assertEqual(result["indicator_label_cn"], "区域突破信号")
        self.assertEqual(result["strength_level"], "--")
        self.assertIn("暂无强度分数", result["strength_explanation"])
        self.assertTrue(result["indicator_display_value"])
        self.assertIn("关键边界", result["calc_explanation"])

    def test_build_signal_explanation_for_edge3_includes_thresholds_and_relative_reading(self):
        result = assistant_routes._build_signal_explanation(
            "MF_Edge3",
            "LONG",
            "普通底部",
            -22.93,
            {
                "start_value": -22.93,
                "values": [-22.93, -17.40, -8.15],
                "window_quantiles": {
                    "p10": -35.50,
                    "p50": -5.20,
                    "p90": 18.60,
                },
            },
        )

        self.assertEqual(len(result["calc_sections"]), 4)
        self.assertIn("[-22.93, -17.40, -8.15]", " ".join(result["calc_sections"][0]["items"]))
        self.assertIn("start_val = -22.93", " ".join(result["calc_sections"][1]["items"]))
        self.assertIn("普通底部", " ".join(result["calc_sections"][2]["items"]))
        self.assertIn("近 3 个月滚动窗口", " ".join(result["calc_sections"][3]["items"]))
        self.assertIn("不是统一的强弱分", result["strength_explanation"])

    def test_build_signal_explanation_for_duration_can_use_context_series(self):
        result = assistant_routes._build_signal_explanation(
            "MF_Duration",
            "LONG",
            "D5",
            5.0,
            {"streak_length": 5},
            [
                {"trade_date": "2026-04-07", "main_force": -11.5, "retail": 2.0},
                {"trade_date": "2026-04-08", "main_force": -9.0, "retail": 1.0},
                {"trade_date": "2026-04-09", "main_force": -6.0, "retail": 0.5},
                {"trade_date": "2026-04-10", "main_force": -3.0, "retail": -0.5},
                {"trade_date": "2026-04-11", "main_force": 1.0, "retail": -1.0},
            ],
        )

        self.assertEqual(len(result["calc_sections"]), 4)
        self.assertIn("[-11.50, -9.00, -6.00, -3.00, 1.00]", " ".join(result["calc_sections"][0]["items"]))
        self.assertIn("相邻变化 = [2.50, 3.00, 3.00, 4.00]", " ".join(result["calc_sections"][1]["items"]))
        self.assertIn("D5", " ".join(result["calc_sections"][2]["items"]))
        self.assertIn("启动段", " ".join(result["calc_sections"][3]["items"]))

    def test_build_operation_explanation_for_duration_divergence_long(self):
        result = assistant_routes._build_operation_explanation(
            "2B",
            "LONG",
            {
                "MF_Duration": "D7",
                "MS_Divergence": "强共振(5.98)",
            },
            1.26,
        )

        self.assertEqual(result["strategy_meta"]["code"], "2B")
        self.assertEqual(result["strategy_meta"]["label_cn"], "D7 主散共振做多")
        self.assertIn("趋势后段", result["strategy_meta"]["thesis"])
        self.assertEqual(result["action_advice"]["label"], "可继续关注做多")
        self.assertIn("综合分主要用于同页排序", result["score_explanation"]["usage_tip"])
        self.assertIn("持续 7 天", result["summary"])
        self.assertEqual(len(result["trigger_explanations"]), 2)
        self.assertIn("持续 7 天", result["trigger_explanations"][0]["value_cn"])
        self.assertIn("主散背离较强", result["trigger_explanations"][1]["meaning"])
        self.assertIn("后段", result["risk_note"])

    def test_build_operation_explanation_for_magnitude_divergence_short(self):
        result = assistant_routes._build_operation_explanation(
            "1B",
            "SHORT",
            {
                "MF_Magnitude": "高幅度(12.30)",
                "MS_Divergence": "强共振(4.40)",
            },
            0.92,
        )

        self.assertEqual(result["strategy_meta"]["label_cn"], "高幅度主散共振做空")
        self.assertEqual(result["action_advice"]["label"], "可关注偏空机会")
        self.assertIn("高幅度", result["trigger_explanations"][0]["value_cn"])
        self.assertIn("主力近三日动作较大", result["trigger_explanations"][0]["meaning"])
        self.assertIn("0.92", result["score_explanation"]["score_text"])
        self.assertIn("经验上", result["score_explanation"]["threshold_tip"])


if __name__ == "__main__":
    unittest.main()
