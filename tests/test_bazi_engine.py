import unittest
from datetime import datetime
from unittest.mock import patch

from xuanxue_engine import BaziInput, calculate_bazi
from xuanxue_engine.bazi import ten_god
from xuanxue_engine.parsing import parse_datetime_from_text


class BaziEngineTests(unittest.TestCase):
    def test_ten_god_examples(self):
        self.assertEqual(ten_god("甲", "甲"), "比肩")
        self.assertEqual(ten_god("甲", "乙"), "劫财")
        self.assertEqual(ten_god("甲", "丙"), "食神")
        self.assertEqual(ten_god("甲", "丁"), "伤官")
        self.assertEqual(ten_god("甲", "戊"), "偏财")
        self.assertEqual(ten_god("甲", "己"), "正财")
        self.assertEqual(ten_god("甲", "庚"), "七杀")
        self.assertEqual(ten_god("甲", "辛"), "正官")
        self.assertEqual(ten_god("甲", "壬"), "偏印")
        self.assertEqual(ten_god("甲", "癸"), "正印")

    def test_parse_datetime_from_text(self):
        self.assertEqual(parse_datetime_from_text("1990-05-12 14:30"), datetime(1990, 5, 12, 14, 30))
        self.assertEqual(parse_datetime_from_text("1990年5月12日14点30"), datetime(1990, 5, 12, 14, 30))

    def test_calculate_bazi_known_shape(self):
        result = calculate_bazi(BaziInput(datetime(1990, 5, 12, 14, 30), gender="男", birth_location="北京"))
        self.assertEqual(result["system"], "bazi")
        self.assertEqual(result["pillars"]["year"]["text"], "庚午")
        self.assertEqual(result["pillars"]["month"]["text"], "辛巳")
        self.assertEqual(result["pillars"]["day"]["text"], "丁丑")
        self.assertEqual(result["pillars"]["hour"]["text"], "丁未")
        self.assertEqual(result["day_master"]["stem"], "丁")
        self.assertGreater(sum(result["five_element_counts"].values()), 0)
        self.assertIn("pattern_name", result["pattern_profile"])
        self.assertIn("summary", result["pattern_conditions"])
        self.assertIn("summary", result["yongshen_profile"])
        self.assertIn("summary", result["timing_linkage"])
        self.assertIn("career", result["theme_guidance"])
        self.assertIn("wealth", result["theme_guidance"])
        self.assertIn("primary_mode", result["career_decision"])
        self.assertIn("job_change", result["special_topic_guidance"])

    def test_calculate_bazi_continues_when_location_cannot_be_resolved(self):
        result = calculate_bazi(BaziInput(datetime(1990, 5, 12, 14, 30), gender="男", birth_location="北京"))
        self.assertEqual(result["system"], "bazi")
        self.assertEqual(result["pillars"]["day"]["text"], "丁丑")
        self.assertTrue(result["input"]["location_resolution_failed"] or result["input"]["resolved_location"])

    def test_calculate_bazi_builds_decadal_annual_and_monthly_cycles_when_gender_present(self):
        result = calculate_bazi(BaziInput(datetime(1990, 5, 12, 14, 30), gender="男", birth_location="北京"))
        self.assertTrue(result["luck_cycle"]["available"])
        self.assertIn(result["luck_cycle"]["direction"], {"forward", "backward"})
        self.assertGreaterEqual(len(result["dayun"]), 8)
        self.assertIsNotNone(result["luck_cycle"]["current_cycle"])
        self.assertTrue(result["annual_cycles"]["available"])
        self.assertGreaterEqual(len(result["liunian"]), 5)
        self.assertTrue(result["monthly_cycles"]["available"])
        self.assertGreaterEqual(len(result["liuyue"]), 5)
        self.assertIsNotNone(result["monthly_cycles"]["current_month"])
        self.assertEqual(result["current_cycles"]["monthly"]["pillar_text"], result["summary"]["current_liuyue"])
        self.assertEqual(result["summary"]["has_decadal_timing"], True)
        self.assertTrue(result["summary"]["current_dayun"])
        self.assertTrue(result["summary"]["current_liunian"])
        self.assertTrue(result["summary"]["current_liuyue"])
        self.assertTrue(result["summary"]["pattern_name"])
        self.assertTrue(result["summary"]["yongshen_summary"])
        self.assertEqual(result["summary"]["structure"], result["pattern_profile"]["structure"])
        self.assertEqual(result["favorable_elements"], result["yongshen_profile"]["favorable_elements"])
        self.assertTrue(result["summary"]["pattern_conditions_summary"])
        self.assertTrue(result["summary"]["timing_linkage_summary"])
        self.assertIsNotNone(result["current_cycles"]["decadal"])
        self.assertEqual(result["summary"]["current_dayun"], result["current_cycles"]["decadal"]["pillar_text"])
        self.assertTrue(result["theme_guidance"]["career"]["summary"])
        self.assertIsInstance(result["theme_guidance"]["wealth"]["risk_points"], list)
        self.assertTrue(result["theme_guidance"]["health"]["timing_note"])
        self.assertTrue(result["career_decision"]["summary"])
        self.assertGreaterEqual(len(result["career_decision"]["mode_order"]), 3)
        self.assertTrue(result["special_topic_guidance"]["startup_timing"]["summary"])

    def test_calculate_bazi_skips_decadal_cycles_without_gender(self):
        result = calculate_bazi(BaziInput(datetime(1990, 5, 12, 14, 30), birth_location="北京"))
        self.assertFalse(result["luck_cycle"]["available"])
        self.assertEqual(result["luck_cycle"]["reason"], "missing_gender")
        self.assertEqual(result["dayun"], [])
        self.assertTrue(result["monthly_cycles"]["available"])
        self.assertTrue(result["summary"]["current_liuyue"])
        self.assertIn("未提供性别", " ".join(result["risk_flags"]))
        self.assertEqual(result["summary"]["has_decadal_timing"], False)
        self.assertTrue(result["summary"]["pattern_name"])
        self.assertTrue(result["summary"]["yongshen_summary"])
        self.assertTrue(result["summary"]["pattern_conditions_summary"])
        self.assertTrue(result["summary"]["timing_linkage_summary"])
        self.assertTrue(result["theme_guidance"]["relationship"]["summary"])

    @patch("xuanxue_engine.astro_common.has_tencent_map_key", return_value=True)
    @patch("xuanxue_engine.astro_common.geocode_address")
    def test_calculate_bazi_can_use_map_geocoder_for_birth_location(self, mock_geocode, _mock_has_key):
        from xuanxue_engine.map_provider_tencent import TencentMapResolvedLocation

        mock_geocode.return_value = TencentMapResolvedLocation(
            query="河南信阳罗山",
            address="河南省信阳市罗山县",
            title="罗山县",
            lat=32.2032,
            lng=114.5310,
            adcode="411521",
            province="河南省",
            city="信阳市",
            district="罗山县",
        )
        result = calculate_bazi(BaziInput(datetime(1990, 5, 12, 14, 30), gender="男", birth_location="罗山宝城广场附近"))
        self.assertEqual(result["system"], "bazi")
        self.assertEqual(result["input"]["resolved_location"], "河南省信阳市罗山县")
        self.assertEqual(result["input"]["resolved_tz_str"], "Asia/Shanghai")


if __name__ == "__main__":
    unittest.main()
