import unittest
from datetime import datetime

from server import infer_question_tags, local_answer_question
from xuanxue_engine.parsing import parse_birth_details, parse_datetime_from_text
from xuanxue_engine.registry import calculate_system


LUNAR_QUESTION = (
    "\u6211\u51fa\u751f\u4e8e\u519c\u53861990\u5e74\u56db\u6708\u5341\u516b\u65e5"
    "\u4e0b\u5348\u4e24\u70b9\u534a\uff0c\u7537\uff0c\u6cb3\u5357\u4fe1\u9633\uff0c"
    "\u73b0\u5728\u60f3\u95ee\u4eca\u5e74\u6362\u5de5\u4f5c\u548c\u642c\u5bb6\u54ea\u4e2a\u5148\u505a\u66f4\u987a\u3002"
)

LUNAR_PROFILE_ONLY = (
    "\u6211\u51fa\u751f\u4e8e\u519c\u53861990\u5e74\u56db\u6708\u5341\u516b\u65e5"
    "\u4e0b\u5348\u4e24\u70b9\u534a\uff0c\u7537\uff0c\u6cb3\u5357\u4fe1\u9633"
)
TRADITIONAL_LUNAR_PROFILE = (
    "\u6211\u51fa\u751f\u65bc\u8fb2\u66c61990\u5e74\u56db\u6708\u5341\u516b\u65e5"
    "\u4e0b\u5348\u5169\u9ede\u534a\uff0c\u7537\uff0c\u6cb3\u5357\u4fe1\u967d"
)
ENGLISH_BIRTH_PROFILE = "I was born on 1990-05-12 at 14:30 in Beijing."
ENGLISH_MONTH_PROFILE = "I was born on May 12, 1990 at 2:30pm in Beijing."
CONFLICTING_PROFILE = (
    "\u6211\u516c\u53861990-05-12 14:30\u51fa\u751f\uff0c"
    "\u4f46\u5bb6\u91cc\u53c8\u8bf4\u6211\u662f\u519c\u53861990\u5e74\u4e94\u6708\u521d\u4e00\u4e0b\u5348\u4e24\u70b9\u534a\uff0c\u7537\uff0c\u5317\u4eac\u3002"
)


class NaturalLanguageParsingTests(unittest.TestCase):
    def test_parse_birth_details_supports_lunar_time_gender_and_tail_location(self):
        parsed = parse_birth_details(LUNAR_PROFILE_ONLY)
        self.assertEqual(parsed.birth_datetime, datetime(1990, 5, 12, 14, 30))
        self.assertTrue(parsed.has_time)
        self.assertEqual(parsed.calendar, "lunar")
        self.assertEqual(parsed.gender, "\u7537")
        self.assertEqual(parsed.birth_location, "\u6cb3\u5357\u4fe1\u9633")

    def test_registry_bazi_accepts_natural_language_lunar_question(self):
        result, status = calculate_system("bazi", {"question": LUNAR_PROFILE_ONLY})
        self.assertEqual(status, 200)
        self.assertEqual(result["input"]["birth_datetime"], "1990-05-12 14:30")
        self.assertEqual(result["input"]["calendar_source"], "lunar")
        self.assertEqual(result["input"]["parsed_gender"], "\u7537")
        self.assertEqual(result["input"]["parsed_birth_location"], "\u6cb3\u5357\u4fe1\u9633")

    def test_parse_birth_details_supports_traditional_lunar_and_traditional_location(self):
        parsed = parse_birth_details(TRADITIONAL_LUNAR_PROFILE)
        self.assertEqual(parsed.birth_datetime, datetime(1990, 5, 12, 14, 30))
        self.assertEqual(parsed.birth_location, "\u6cb3\u5357\u4fe1\u967d")
        self.assertEqual(parsed.calendar, "lunar")

    def test_parse_birth_details_supports_english_location(self):
        parsed = parse_birth_details(ENGLISH_BIRTH_PROFILE)
        self.assertEqual(parsed.birth_datetime, datetime(1990, 5, 12, 14, 30))
        self.assertEqual(parsed.birth_location, "Beijing")

    def test_parse_birth_details_supports_english_month_and_ampm(self):
        parsed = parse_birth_details(ENGLISH_MONTH_PROFILE)
        self.assertEqual(parsed.birth_datetime, datetime(1990, 5, 12, 14, 30))
        self.assertEqual(parsed.birth_location, "Beijing")

    def test_parse_birth_details_infers_gender_from_baby_terms(self):
        parsed = parse_birth_details("给2026年6月13日23点42分出生的女宝宝，姓彭起一个名字。")
        self.assertEqual(parsed.gender, "女")

    def test_parse_birth_details_flags_conflicting_calendar_inputs(self):
        parsed = parse_birth_details(CONFLICTING_PROFILE)
        self.assertTrue(parsed.has_conflict)
        self.assertTrue(parsed.conflict_note)

    def test_parse_datetime_from_text_supports_non_birth_event_time(self):
        parsed = parse_datetime_from_text("现在是2026-06-13 21:10，我想问这周先谈合作还是先推进招聘。")
        self.assertEqual(parsed, datetime(2026, 6, 13, 21, 10))

    def test_parse_birth_details_does_not_treat_trip_date_as_birth(self):
        question = "我想从阴阳道看这周出差去东京，2026-06-18 出发，住新宿，方向和禁忌有什么要注意？"
        parsed = parse_birth_details(question)
        self.assertIsNone(parsed.birth_datetime)
        self.assertFalse(parsed.has_time)
        self.assertEqual(parsed.birth_location, "")
        event_dt = parse_datetime_from_text(question)
        self.assertEqual(event_dt, datetime(2026, 6, 18, 0, 0))

    def test_server_local_answer_uses_tags_and_emits_local_bazi_chart(self):
        self.assertEqual(infer_question_tags(LUNAR_QUESTION), {"space", "career", "timing"})
        result = local_answer_question(LUNAR_QUESTION)
        bazi_answer = next(item["answer"] for item in result["result"]["system_answers"] if item["system"] == "\u516b\u5b57")
        self.assertIn("八字排盘为：", bazi_answer)
        self.assertIn("已识别农历生日并换算为阳历起八字", bazi_answer)
        synthesis = result["result"]["final_answer"]["synthesis"]
        self.assertTrue("空间" in synthesis or "Spatial factors are central here" in synthesis)


if __name__ == "__main__":
    unittest.main()
