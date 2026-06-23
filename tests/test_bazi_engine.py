import unittest
from datetime import datetime

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


if __name__ == "__main__":
    unittest.main()
