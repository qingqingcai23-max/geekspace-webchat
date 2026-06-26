import unittest
from unittest.mock import patch

from xuanxue_engine.registry import calculate_system


class RegistryEngineTests(unittest.TestCase):
    def test_numerology_calculation(self):
        result, status = calculate_system("numerology", {"birth_date": "1990-05-12", "name": "Alex"})
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "numerology")
        self.assertEqual(result["derived_factors"]["life_path"], 9)
        self.assertIsNotNone(result["derived_factors"]["expression_number"])

    def test_unknown_system_returns_not_found(self):
        result, status = calculate_system("unknown_system", {"question": "test"})
        self.assertEqual(status, 404)
        self.assertIn("Unknown system", result["error"])

    def test_qimen_ignores_birth_datetime_when_no_event_time_is_supplied(self):
        question = "我出生于1990年5月12日下午2点30分，男，河南信阳。想看今年换工作和搬家哪个先做更顺。"
        result, status = calculate_system("qimen_dunjia", {"question": question})
        self.assertEqual(status, 200)
        self.assertEqual(result["used_inputs"]["time_source"], "inferred-current-time")

    def test_liu_ren_ignores_birth_datetime_when_no_event_time_is_supplied(self):
        question = "我出生于1990年5月12日下午2点30分，男，河南信阳。想看今年换工作和搬家哪个先做更顺。"
        result, status = calculate_system("liu_ren", {"question": question})
        self.assertEqual(status, 200)
        self.assertEqual(result["used_inputs"]["time_source"], "inferred-current-time")

    def test_qimen_still_uses_explicit_event_datetime_inside_mixed_question(self):
        question = (
            "我出生于1990年5月12日下午2点30分，男，河南信阳。"
            "想看2026-06-10 09:30这个时点搬家是否合适。"
        )
        result, status = calculate_system("qimen_dunjia", {"question": question})
        self.assertEqual(status, 200)
        self.assertEqual(result["used_inputs"]["time_source"], "question-datetime")
        self.assertEqual(result["used_inputs"]["event_datetime"], "2026-06-10 09:30")

    @patch("xuanxue_engine.registry.collect_nearby_poi_signals")
    @patch("xuanxue_engine.registry.has_tencent_map_key", return_value=True)
    @patch("xuanxue_engine.registry.static_map_url", return_value="https://example.com/static-map")
    @patch("xuanxue_engine.registry.geocode_address")
    def test_fengshui_can_attach_map_context(self, mock_geocode, _mock_static, _mock_has_key, mock_collect_poi):
        from xuanxue_engine.map_provider_tencent import TencentMapResolvedLocation

        mock_geocode.return_value = TencentMapResolvedLocation(
            query="上海浦东某小区 12 栋 1802",
            address="上海市浦东新区某小区 12 栋 1802",
            title="某小区 12 栋 1802",
            lat=31.2304,
            lng=121.4737,
            adcode="310115",
            province="上海市",
            city="上海市",
            district="浦东新区",
        )
        mock_collect_poi.return_value = {
            "park": [{"title": "中心公园", "distance": 260}],
            "hospital": [{"title": "社区医院", "distance": 520}],
        }
        result, status = calculate_system(
            "fengshui",
            {
                "location": "上海浦东某小区 12 栋 1802",
                "facing_direction": "坐北朝南",
                "birth_date": "1990-05-12",
                "gender": "男",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "fengshui")
        self.assertIn("map_context", result["used_inputs"])
        self.assertEqual(result["used_inputs"]["map_context"]["city"], "上海市")
        self.assertEqual(result["used_inputs"]["map_context"]["static_map_url"], "https://example.com/static-map")
        self.assertIn("external_environment", result["derived_factors"])


if __name__ == "__main__":
    unittest.main()
