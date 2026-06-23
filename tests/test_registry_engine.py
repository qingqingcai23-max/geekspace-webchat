import unittest

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


if __name__ == "__main__":
    unittest.main()
