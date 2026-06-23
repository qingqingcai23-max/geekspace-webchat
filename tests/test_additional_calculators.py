import unittest

from server import answer_question, local_answer_question, normalize_multi_turn_question, relevant_packs, system_question_diagnostics
from xuanxue_engine.registry import IMPLEMENTED_SYSTEMS, calculate_system


class AdditionalCalculatorTests(unittest.TestCase):
    def test_implemented_systems_expanded(self):
        self.assertTrue(
            {
                "yijing_and_symbolism",
                "date_selection",
                "fengshui",
                "tarot",
                "liuyao_and_meihua",
                "name_studies",
                "onmyodo",
                "qizheng_siyu",
                "ziwei_doushu",
                "western_astrology",
                "vedic_astrology",
                "human_design",
                "qimen_dunjia",
                "liu_ren",
                "kabbalah",
                "physiognomy",
                "daoist_arts",
                "alchemy_and_hermeticism",
                "modern_esotericism",
            }.issubset(IMPLEMENTED_SYSTEMS)
        )

    def test_yijing_numbers_casting(self):
        result, status = calculate_system(
            "yijing_and_symbolism",
            {
                "question": "Should I switch jobs now?",
                "casting_method": "numbers",
                "numbers_or_datetime": "3,5,6",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "yijing_and_symbolism")
        self.assertEqual(result["normalized_input"]["moving_line"], 6)
        self.assertIn("base_hexagram", result["derived_factors"])

    def test_tarot_requires_real_cards_and_parses_them(self):
        result, status = calculate_system(
            "tarot",
            {
                "question": "What is the tone of this project?",
                "spread": "three_card",
                "cards": ["The Fool upright", "Death reversed", "Ace of Cups"],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "tarot")
        self.assertEqual(result["derived_factors"]["major_arcana_count"], 2)
        self.assertEqual(result["derived_factors"]["reversed_count"], 1)

    def test_birth_chart_systems_reject_conflicting_birth_inputs(self):
        result, status = calculate_system(
            "bazi",
            {
                "question": (
                    "\u6211\u516c\u53861990-05-12 14:30\u51fa\u751f\uff0c"
                    "\u4f46\u5bb6\u91cc\u53c8\u8bf4\u6211\u662f\u519c\u53861990\u5e74\u4e94\u6708\u521d\u4e00\u4e0b\u5348\u4e24\u70b9\u534a\uff0c\u7537\uff0c\u5317\u4eac\u3002"
                )
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("\u4e0d\u4e00\u81f4", result["error"])

    def test_tarot_accepts_chinese_minor_arcana(self):
        result, status = calculate_system(
            "tarot",
            {
                "question": "想问这个月项目走向。",
                "spread": "three_card",
                "cards": ["愚者正位", "死神逆位", "圣杯首牌正位"],
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "tarot")
        self.assertEqual(result["derived_factors"]["major_arcana_count"], 2)
        self.assertEqual(result["derived_factors"]["cards"][2]["suit"], "cups")

    def test_date_selection_ranks_candidates(self):
        result, status = calculate_system(
            "date_selection",
            {
                "event_type": "move",
                "candidate_dates": ["2026-06-10", "2026-06-12"],
                "participant_birth": "1990-05-12",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "date_selection")
        self.assertEqual(len(result["derived_factors"]["ranked_candidates"]), 2)
        self.assertIn("候选日期里排名最高的是", result["primary_finding"])
        self.assertNotIn("Top-ranked candidate", result["primary_finding"])
        joined_signals = " ".join(result["supporting_signals"])
        self.assertIn("中性规则组合", joined_signals)
        self.assertNotIn("neutral rule mix", joined_signals)

    def test_date_selection_question_parser_ignores_birth_date(self):
        result, status = calculate_system(
            "date_selection",
            {
                "question": (
                    "我出生于1990-05-12 14:30，男，"
                    "现在想在2026-06-10和2026-06-12之间选一天搬家。"
                )
            },
        )
        self.assertEqual(status, 200)
        ranked_dates = [item["date"] for item in result["derived_factors"]["ranked_candidates"]]
        self.assertEqual(ranked_dates, ["2026-06-10", "2026-06-12"])

    def test_date_selection_accepts_single_date_question(self):
        result, status = calculate_system(
            "date_selection",
            {
                "question": "2026年6月8号，是个好日子吗？"
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["derived_factors"]["ranked_candidates"][0]["date"], "2026-06-08")
        self.assertIn("候选日期里排名最高的是 2026-06-08", result["primary_finding"])

    def test_fengshui_eight_mansions_matching(self):
        result, status = calculate_system(
            "fengshui",
            {
                "location_or_floorplan": "Apartment 12A",
                "facing_direction": "坐北朝南",
                "birth_datetime": "1990-05-12 14:30",
                "gender": "男",
                "build_year": "2025",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "fengshui")
        self.assertEqual(result["derived_factors"]["occupant_kua"], 1)
        self.assertEqual(result["derived_factors"]["period"]["period"], 9)

    def test_liuyao_numbers_casting_returns_body_use_structure(self):
        result, status = calculate_system(
            "liuyao_and_meihua",
            {
                "question": "Will this negotiation land smoothly?",
                "casting_method": "numbers",
                "hexagram_or_casting_data": "3,5,6",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "liuyao_and_meihua")
        self.assertIn("body_use_relation", result["derived_factors"])
        self.assertIn("primary_finding", result)

    def test_local_oracle_accepts_line_based_casting_seed_when_numeric_seed_is_present(self):
        answer = local_answer_question(
            "六爻起卦，我想问这次合作能不能成，初爻少阳，二爻少阴，三爻老阳，四爻少阴，五爻少阳，上爻少阴，动爻第三爻，数字 1 6 3。"
        )
        liuyao = next(item for item in answer["result"]["system_answers"] if item["key"] == "liuyao_and_meihua")
        self.assertTrue(liuyao["used_local_calculation"])
        self.assertEqual(liuyao["missing_inputs"], [])

    def test_name_studies_can_parse_name_from_question(self):
        result, status = calculate_system(
            "name_studies",
            {"question": "名字林清和适合男孩吗"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "name_studies")
        self.assertEqual(result["derived_factors"]["script"], "cjk")
        self.assertEqual(result["derived_factors"]["surname"], "林")

    def test_name_studies_keeps_full_name_when_question_contains_mingzi_shi(self):
        result, status = calculate_system(
            "name_studies",
            {"question": "我想看我这个名字和命格合不合，名字是林清和，出生于1990-05-12 14:30，北京。"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["used_inputs"]["name"], "林清和")
        self.assertIn("林清和", result["primary_finding"])

    def test_name_studies_can_generate_candidates_for_baby_naming(self):
        result, status = calculate_system(
            "name_studies",
            {"question": "给2026年6月13日23点42分出生的女宝宝，姓彭起一个名字。"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "name_studies")
        self.assertEqual(result["question_type"], "name_generation")
        self.assertTrue(result["generated_candidates"])
        self.assertTrue(result["used_inputs"]["name"].startswith("彭"))
        first = result["generated_candidates"][0]
        self.assertTrue(first["source_title"])
        self.assertTrue(first["meaning"])
        self.assertTrue(first["why_selected"])

    def test_name_studies_generates_boy_candidates_from_local_composition(self):
        result, status = calculate_system(
            "name_studies",
            {"question": "孩子姓沈，男孩，别给我生僻字，也别太娘，最好有点书卷气，先给我方向就行。"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["question_type"], "name_generation")
        self.assertTrue(result["generated_candidates"])
        top_names = [item["name"] for item in result["generated_candidates"][:5]]
        self.assertTrue(all(name.startswith("沈") for name in top_names))
        self.assertTrue(all(name[1:] not in {"书雅", "清妍", "清婉", "若棠", "静姝", "沐兰", "芳菲", "令姝"} for name in top_names))
        self.assertTrue(
            any(
                "重新组合" in " ".join(item.get("supporting_signals") or [])
                or "重新组合" in str(item.get("why_selected") or "")
                for item in result["generated_candidates"][:3]
            )
        )

    def test_local_oracle_naming_answer_includes_source_grounding(self):
        answer = local_answer_question(
            "给2026年6月13日23点42分出生的女宝宝，姓彭起一个名字，要文雅一点，最好有诗文出处。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("首选", synthesis)
        self.assertTrue(any(token in synthesis for token in ["出处", "名字主旨", "诗经", "楚辞", "礼记"]))
        self.assertNotIn("。，", synthesis)
        system_answers = answer["result"]["system_answers"]
        naming = next(item for item in system_answers if item["key"] == "name_studies")
        self.assertIn("经典出处", naming["answer"])

    def test_local_oracle_naming_question_reuses_baby_gender_for_bazi_support(self):
        answer = local_answer_question("给2026年6月13日23点42分出生的女宝宝，姓彭起一个名字。")
        bazi = next(item for item in answer["result"]["system_answers"] if item["key"] == "bazi")
        self.assertNotIn("性别", bazi["missing_inputs"])
        self.assertFalse(any("未提供性别" in item for item in (bazi.get("risk_flags") or [])))

    def test_onmyodo_direction_screening(self):
        result, status = calculate_system(
            "onmyodo",
            {
                "date": "2026-06-10",
                "direction_or_location": "东北",
                "event_type": "travel",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "onmyodo")
        self.assertEqual(result["used_inputs"]["resolved_direction"], "NE")
        self.assertIn("score", result["derived_factors"])

    def test_local_oracle_follow_up_style_naming_question_routes_to_name_generation(self):
        answer = local_answer_question("起什么名字\n2026年6月13日23点42分出生的女宝宝，姓彭")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        system_answers = answer["result"]["system_answers"]
        naming = next(item for item in system_answers if item["key"] == "name_studies")

        self.assertIn("首选是", synthesis)
        self.assertIn("彭", synthesis)
        self.assertIn("当前更推荐", naming["verdict"])

    def test_local_oracle_semicolon_style_naming_question_routes_to_name_generation(self):
        answer = local_answer_question("2026年6月13日23点42分出生的女宝宝，姓彭；起什么名字")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        system_answers = answer["result"]["system_answers"]
        naming = next(item for item in system_answers if item["key"] == "name_studies")

        self.assertIn("首选是", synthesis)
        self.assertIn("彭", naming["verdict"])

    def test_western_astrology_builds_local_chart(self):
        result, status = calculate_system(
            "western_astrology",
            {
                "birth_datetime": "1990-05-12 14:30",
                "birth_location": "Beijing",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "western_astrology")
        self.assertEqual(result["derived_factors"]["big_three"]["sun"], "Taurus")
        self.assertEqual(result["derived_factors"]["big_three"]["ascendant"], "Virgo")
        self.assertTrue(result["derived_factors"]["major_aspects"])
        self.assertIn("太阳落在金牛座", result["primary_finding"])
        joined_signals = " ".join(result["supporting_signals"])
        self.assertIn("太阳落在金牛座", joined_signals)
        self.assertNotIn("Sun is in", joined_signals)
        self.assertNotIn("Taurus in", joined_signals)

    def test_ziwei_doushu_builds_local_chart(self):
        result, status = calculate_system(
            "ziwei_doushu",
            {
                "birth_datetime": "1990-05-12 14:30",
                "gender": "male",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "ziwei_doushu")
        self.assertEqual(result["derived_factors"]["five_elements_class"], "土五局")
        self.assertEqual(result["derived_factors"]["key_palaces"]["命宫"]["major_stars"], ["太阴"])
        self.assertEqual(result["derived_factors"]["current_cycles"]["decadal_focus"], "命宫")

    def test_qizheng_siyu_builds_local_chart(self):
        result, status = calculate_system(
            "qizheng_siyu",
            {
                "birth_datetime": "1990-05-12 14:30",
                "birth_location": "Beijing",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "qizheng_siyu")
        self.assertEqual(result["derived_factors"]["seven_governors"]["Sun"]["sign_full"], "Taurus")
        self.assertEqual(result["derived_factors"]["four_remainders"]["Luohou"]["house_number"], 11)
        self.assertEqual(result["derived_factors"]["four_remainders"]["Ziqi"]["house_number"], 9)

    def test_vedic_astrology_builds_local_chart(self):
        result, status = calculate_system(
            "vedic_astrology",
            {
                "birth_datetime": "1990-05-12 14:30",
                "birth_location": "Beijing",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "vedic_astrology")
        self.assertEqual(result["derived_factors"]["lagna"]["sign_full"], "Leo")
        self.assertEqual(result["derived_factors"]["moon_nakshatra"]["name"], "Jyeshtha")
        self.assertEqual(result["used_inputs"]["ayanamsa"], "LAHIRI")
        self.assertIn("命宫落在狮子座", result["primary_finding"])
        joined_signals = " ".join(result["supporting_signals"])
        self.assertIn("上升点落在狮子座", joined_signals)
        self.assertIn("心宿", joined_signals)
        self.assertNotIn("Lagna is", joined_signals)
        self.assertNotIn("Jyeshtha", joined_signals)

    def test_human_design_builds_local_chart(self):
        result, status = calculate_system(
            "human_design",
            {
                "birth_datetime": "1990-05-12 14:30",
                "birth_location": "Beijing",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "human_design")
        self.assertEqual(result["derived_factors"]["type"]["name"], "Projector")
        self.assertEqual(result["derived_factors"]["authority"]["name"], "Emotional Authority")
        self.assertEqual(result["derived_factors"]["profile"]["numbers"], "3/5")
        self.assertIn("Throat", result["derived_factors"]["centers"]["defined_names"])

    def test_kabbalah_builds_local_tree_reading(self):
        result, status = calculate_system(
            "kabbalah",
            {
                "topic": "career direction and visible purpose",
                "sephirah_or_path": "Tiphereth",
                "source": "Hermetic Qabalah",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "kabbalah")
        self.assertEqual(result["derived_factors"]["target_type"], "sephirah")
        self.assertEqual(result["derived_factors"]["tree_index"], 6)
        self.assertEqual(result["derived_factors"]["canonical_name"], "Tiphereth")
        self.assertEqual(result["derived_factors"]["source_stream"], "hermetic-qabalah")
        self.assertIn("career", result["derived_factors"]["topic_domains"])

    def test_kabbalah_gematria_supports_hebrew_text(self):
        result, status = calculate_system(
            "kabbalah",
            {
                "topic": "שלום",
                "sephirah_or_path": "27",
                "source": "Sefer Yetzirah",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["derived_factors"]["target_type"], "path")
        self.assertEqual(result["derived_factors"]["tree_index"], 27)
        self.assertEqual(result["derived_factors"]["gematria"]["total"], 376)
        self.assertEqual(result["derived_factors"]["gematria"]["reduced"], 7)

    def test_physiognomy_builds_local_observation_reading(self):
        result, status = calculate_system(
            "physiognomy",
            {
                "image_or_description": "broad bright forehead, clear eyes, straight full nose, full chin, even complexion",
                "observation_context": "daylight portrait photo",
                "age": 32,
                "gender": "male",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "physiognomy")
        self.assertGreaterEqual(result["derived_factors"]["recognized_feature_count"], 4)
        self.assertEqual(result["derived_factors"]["features"]["eyes"]["leaning"], "positive")
        self.assertGreater(result["derived_factors"]["three_courts"]["middle"]["score"], 0)

    def test_daoist_arts_builds_local_ritual_reading(self):
        result, status = calculate_system(
            "daoist_arts",
            {
                "topic": "protective home talisman and cleansing rite",
                "source_or_lineage": "Zhengyi Daoism",
                "ritual_text": "incense altar talisman petition scripture recitation",
                "region": "Jiangnan",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "daoist_arts")
        self.assertEqual(result["derived_factors"]["lineage"]["canonical"], "zhengyi")
        self.assertIn(result["derived_factors"]["practice_family"], {"protective-talismans", "liturgical-ritual"})
        self.assertTrue(result["derived_factors"]["ritual_components"])

    def test_daoist_arts_flags_high_risk_requests(self):
        result, status = calculate_system(
            "daoist_arts",
            {
                "topic": "curse and possession work",
                "ritual_text": "血祭 请神上身 符水治病",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["derived_factors"]["safety_tier"], "cultural-only")
        self.assertTrue(result["derived_factors"]["taboo_hits"])

    def test_alchemy_and_hermeticism_builds_local_transformation_reading(self):
        result, status = calculate_system(
            "alchemy_and_hermeticism",
            {
                "topic": "nigredo shadow work with mercury and salt",
                "text_or_image": "blackening crow vessel mercury salt",
                "stage_model": "nigredo",
                "tradition": "Jungian Hermetic",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "alchemy_and_hermeticism")
        self.assertEqual(result["derived_factors"]["stage"]["name"], "nigredo")
        self.assertEqual(result["derived_factors"]["stage"]["next_stage"], "albedo")
        self.assertTrue(result["derived_factors"]["symbols"])
        self.assertIn("nigredo", result["derived_factors"]["transformation_path"])

    def test_modern_esotericism_builds_local_risk_reading(self):
        result, status = calculate_system(
            "modern_esotericism",
            {
                "topic": "manifestation and chakra energy work",
                "source": "new age reiki circle",
                "practice_description": "aura clearing, law of attraction, abundance journaling",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "modern_esotericism")
        self.assertEqual(result["derived_factors"]["source_family"]["name"], "new-age")
        self.assertIn(result["derived_factors"]["concept_family"]["name"], {"prosperity-technique", "energy-map"})
        self.assertIn(result["derived_factors"]["risk_tier"], {"low", "medium"})

    def test_modern_esotericism_flags_high_risk_overreach(self):
        result, status = calculate_system(
            "modern_esotericism",
            {
                "topic": "channeling-based healing authority",
                "practice_description": "stop medication and join only my group to ascend",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["derived_factors"]["risk_tier"], "high")
        self.assertTrue(result["derived_factors"]["high_risk_markers"])

    def test_qimen_dunjia_builds_local_chart(self):
        result, status = calculate_system(
            "qimen_dunjia",
            {
                "event_datetime": "2026-06-08 14:30",
                "question": "事业发展如何？",
                "timezone": "Asia/Shanghai",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "qimen_dunjia")
        self.assertEqual(result["derived_factors"]["dun_type"], "yang")
        self.assertEqual(result["derived_factors"]["ju_number"], 6)
        self.assertEqual(result["derived_factors"]["zhi_fu"]["palace"], 7)
        self.assertEqual(result["derived_factors"]["zhi_shi"]["palace"], 2)
        self.assertEqual(len(result["raw_chart"]["palaces"]), 9)

    def test_liu_ren_builds_local_chart(self):
        result, status = calculate_system(
            "liu_ren",
            {
                "event_datetime": "2026-06-08 14:30",
                "question": "事业发展如何？",
                "birth_year": 1990,
                "gender": "male",
                "timezone": "Asia/Shanghai",
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["system"], "liu_ren")
        self.assertTrue(result["derived_factors"]["transmission_method"])
        self.assertTrue(result["derived_factors"]["diurnal"])
        self.assertIn("chu", result["derived_factors"]["san_chuan"])
        self.assertTrue(result["raw_chart"]["gong_infos"])

    def test_local_oracle_surfaces_chart_results_for_birth_questions(self):
        answer = local_answer_question(
            "我出生于1990-05-12 14:30，男，北京，现在想从紫微、星盘和吠陀角度看性格、事业和后续发展。"
        )
        top_keys = [pack.key for pack in answer["systems"][:8]]
        self.assertIn("ziwei_doushu", top_keys)
        self.assertIn("western_astrology", top_keys)
        self.assertIn("vedic_astrology", top_keys)
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:8])
        self.assertIn("命宫主轴为太阴", joined_answers)
        self.assertIn("太阳金牛座", joined_answers)
        self.assertIn("狮子座上升", joined_answers)
        final_answer = answer["result"]["final_answer"]
        self.assertTrue(
            any(
                "本轮实际参与本地实算的体系有：" in item
                for item in final_answer["agreements"]
            )
        )
        self.assertTrue(
            any(
                "其中已经形成直接结论的体系有：" in item
                for item in final_answer["agreements"]
            )
        )

    def test_career_question_prefers_career_specific_verdicts(self):
        answer = local_answer_question(
            "我出生于1990-05-12 14:30，男，北京，想看事业发展和职业方向。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("事业", synthesis)
        self.assertTrue(
            any(token in synthesis for token in ["职业", "路径", "方向", "岗位", "项目"])
        )
        top_verdicts = [item["verdict"] for item in answer["result"]["system_answers"] if item["verdict"]][:4]
        self.assertTrue(any("事业" in item or "职业" in item for item in top_verdicts))

    def test_relationship_question_does_not_promote_generic_personality_output(self):
        answer = local_answer_question(
            "我出生于1990-05-12 14:30，男，北京，想看婚姻和感情走向。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue(any(token in synthesis for token in ["婚姻", "感情", "关系", "伴侣"]))
        self.assertNotIn("性格与行动风格都较鲜明", synthesis)
        agreements = " ".join(answer["result"]["final_answer"]["agreements"])
        self.assertIn("辅助线索", " ".join(item["answer"] for item in answer["result"]["system_answers"]))
        self.assertTrue("婚姻" in agreements or "感情" in agreements)

    def test_timing_question_prefers_timing_systems_over_birth_chart_fallbacks(self):
        answer = local_answer_question(
            "我想用奇门和六壬看 2026-06-08 14:30 这个时点问事业推进，下一步怎么走？"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue(any(token in synthesis for token in ["下一步", "推进", "时点", "先稳住"]))
        agreements = " ".join(answer["result"]["final_answer"]["agreements"])
        self.assertIn("奇门遁甲", agreements)
        self.assertIn("大六壬", agreements)
        top_answers = answer["result"]["system_answers"][:3]
        self.assertTrue(any(item["key"] == "qimen_dunjia" and item["verdict"] for item in top_answers))

    def test_multi_part_wealth_question_covers_requested_facets(self):
        answer = local_answer_question(
            "我出生于1990-05-12 14:30，男，北京，想看我这两年的财运走向、赚钱方式和破财风险。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue("财运" in synthesis or "收入" in synthesis)
        self.assertTrue("方式" in synthesis or "路径" in synthesis or "靠" in synthesis)
        self.assertTrue("风险" in synthesis or "要防" in synthesis or "破财" in synthesis)

    def test_birth_wealth_question_routes_to_birth_chart_systems(self):
        answer = local_answer_question(
            "我出生于1990-05-12 14:30，男，北京，想看未来两年的财运主轴、赚钱方式和最大的破财风险。"
        )
        top_keys = [pack.key for pack in answer["systems"][:4]]
        self.assertIn("bazi", top_keys)
        self.assertIn("ziwei_doushu", top_keys)
        controller = answer["result"]["controller"]
        self.assertEqual(controller["questionType"], "事业/财运问题")
        self.assertEqual(controller["executionStatus"], "answered")

    def test_multi_part_relationship_question_covers_partner_type_and_conflict(self):
        answer = local_answer_question(
            "我出生于1990-05-12 14:30，男，北京，想看婚姻走向、适合什么类型对象、关系里最大的矛盾点。"
        )
        agreements = " ".join(answer["result"]["final_answer"]["agreements"])
        self.assertTrue("对象类型" in agreements or "适合" in agreements)
        self.assertTrue("矛盾点" in agreements or "要防" in agreements or "关系里" in agreements)

    def test_space_question_without_timing_does_not_prioritize_timing_systems(self):
        answer = local_answer_question(
            "我现在看一套坐北朝南的房子，想知道适不适合长期居住、最需要注意的空间问题是什么。1990-05-12 14:30生，男。"
        )
        self.assertEqual(answer["systems"][0].key, "fengshui")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("长期居住", synthesis)
        self.assertTrue("空间" in synthesis or "朝向" in synthesis or "布局" in synthesis)

    def test_fengshui_question_with_building_numbers_does_not_pull_divination_systems(self):
        answer = local_answer_question(
            "上海浦东某小区12栋1802，坐北朝南，入户门偏东，主卧在西南角，最近总觉得睡眠差、口舌多，想看风水上哪里有问题，怎么调整。"
        )
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertEqual(top_keys[0], "fengshui")
        self.assertNotIn("yijing_and_symbolism", top_keys[:3])
        self.assertNotIn("liuyao_and_meihua", top_keys[:3])
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue("空间" in synthesis or "主卧" in synthesis or "朝向" in synthesis or "睡眠" in synthesis)

    def test_fengshui_long_term_residence_question_returns_direct_verdict(self):
        answer = local_answer_question("上海浦东某小区 12 栋 1802，坐北朝南，想看适不适合长期居住。")
        fengshui = next(item for item in answer["result"]["system_answers"] if item["key"] == "fengshui")
        self.assertEqual(fengshui["verdict_quality"], "conclusion")
        self.assertIn("长期居住", fengshui["answer"])

    def test_fengshui_long_term_and_space_issue_question_returns_direct_verdict(self):
        answer = local_answer_question("上海浦东某小区 12 栋 1802，坐北朝南，想看适不适合长期住，最需要注意的空间问题在哪？")
        fengshui = next(item for item in answer["result"]["system_answers"] if item["key"] == "fengshui")
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(fengshui["verdict_quality"], "conclusion")
        self.assertIn("长期居住", fengshui["verdict"])
        self.assertIn("空间问题", fengshui["verdict"])
        self.assertIn("长期居住", synthesis)
        self.assertTrue(any(token in synthesis for token in ["入户门", "主卧", "床位", "动线"]))

    def test_tarot_relationship_question_returns_actionable_relationship_verdict(self):
        answer = local_answer_question(
            "三张牌分别是愚者正位、圣杯二正位、宝剑十逆位。我想问这段关系接下来一个月会怎么发展，我该主动还是先观察？"
        )
        self.assertEqual(answer["systems"][0].key, "tarot")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue("关系" in synthesis or "主动" in synthesis or "观察" in synthesis)
        self.assertNotIn("事业", synthesis)

    def test_tarot_without_drawn_cards_stays_in_follow_up_mode(self):
        answer = local_answer_question("我想用塔罗看这个月项目能不能成，以及我该不该继续投钱。")
        self.assertEqual(answer["systems"], [])
        controller = answer["result"]["controller"]
        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertTrue("牌" in (controller["followUpPrompt"] or ""))
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("塔罗", synthesis)
        self.assertNotIn("不建议继续加码", synthesis)

    def test_daoist_arts_question_returns_scene_and_boundary_verdict(self):
        answer = local_answer_question(
            "我是正一道法脉背景，想了解净宅、护身、化煞、安神这几类法事分别适合什么场景，有哪些禁忌和风险？"
        )
        self.assertEqual(answer["systems"][0].key, "daoist_arts")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue("适合" in synthesis or "边界" in synthesis or "禁忌" in synthesis or "护持" in synthesis)


    def test_relevant_packs_prioritize_chart_systems_for_birth_chart_questions(self):
        question = "我出生于1990-05-12 14:30，男，北京，现在想从紫微、星盘和吠陀角度看性格、事业和后续发展。"
        top_keys = [pack.key for pack in relevant_packs(question, limit=8)]
        self.assertIn("ziwei_doushu", top_keys[:4])
        self.assertIn("western_astrology", top_keys[:4])
        self.assertIn("vedic_astrology", top_keys[:5])
        self.assertEqual(top_keys[:3], ["ziwei_doushu", "western_astrology", "vedic_astrology"])
        self.assertNotIn("qimen_dunjia", top_keys[:5])
        self.assertNotIn("liu_ren", top_keys[:5])
        self.assertNotIn("fengshui", top_keys[:5])

    def test_local_model_alias_uses_local_synthesis(self):
        question = "我出生于1990-05-12 14:30，男，北京，想看星盘和吠陀角度的性格。"
        answer = answer_question(question, "local-vault-synthesis")
        self.assertEqual(answer["model"], "local-vault-synthesis")
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("western_astrology", top_keys)
        self.assertIn("vedic_astrology", top_keys)

    def test_local_oracle_surfaces_human_design_when_explicitly_requested(self):
        question = "我出生于1990-05-12 14:30，男，北京，想从人类图角度看我的类型、权威和事业风格。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("human_design", top_keys)
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("投射者", joined_answers)

    def test_local_oracle_surfaces_qimen_and_liu_ren_for_timing_questions(self):
        question = "我想用奇门和六壬看 2026-06-08 14:30 这个时点问事业推进，下一步怎么走？"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("qimen_dunjia", top_keys[:3])
        self.assertIn("liu_ren", top_keys[:4])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("本局为", joined_answers)
        self.assertIn("大六壬课体为", joined_answers)

    def test_mixed_birth_and_timing_question_keeps_chart_and_timing_layers(self):
        question = "我出生于1990-05-12 14:30，北京，现在是2026-06-13 21:10。我想看长期职业方向，也想看这周适不适合提离职。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:8]]
        self.assertIn("bazi", top_keys)
        self.assertIn("western_astrology", top_keys)
        self.assertTrue(any(key in top_keys for key in ("qimen_dunjia", "liu_ren")))
        controller = answer["result"]["controller"]
        self.assertEqual(controller["questionType"], "命盘 + 时机混合问题")
        selected_status = {item["key"]: item["status"] for item in controller["selectedSystems"]}
        self.assertEqual(selected_status["bazi"], "answered")
        self.assertEqual(selected_status["western_astrology"], "answered")

    def test_local_oracle_skips_systems_that_cannot_compute_from_current_question(self):
        question = "我出生于1990-05-12 14:30，男，北京，想看我的性格和事业发展。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:12]]
        self.assertIn("bazi", top_keys)
        self.assertIn("western_astrology", top_keys)
        self.assertNotIn("qimen_dunjia", top_keys)
        self.assertNotIn("liu_ren", top_keys)
        self.assertNotIn("tarot", top_keys)
        self.assertNotIn("fengshui", top_keys)
        self.assertNotIn("daoist_arts", top_keys)

    def test_local_oracle_surfaces_yijing_when_numbers_are_present(self):
        question = "我想用易经看这件事，数字是 3 8 5。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("yijing_and_symbolism", top_keys[:3])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("本卦为", joined_answers)
        self.assertIn("变卦为", joined_answers)

    def test_local_oracle_surfaces_date_selection_for_single_good_day_question(self):
        question = "2026年6月8号，是个好日子吗？"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("date_selection", top_keys[:3])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("本地择日得分", joined_answers)

    def test_local_oracle_surfaces_liuyao_when_numbers_are_present(self):
        question = "我想用六爻看这件事，数字是 3 8 5。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("liuyao_and_meihua", top_keys[:3])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("体卦为", joined_answers)
        self.assertIn("用卦为", joined_answers)

    def test_liuyao_feasibility_question_returns_direct_outcome_language(self):
        answer = local_answer_question("我想问这次合作能不能成，数字 3 8 5。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue(any(token in synthesis for token in ["不是完全不能做", "机会窗口", "后面会卡", "先有势头"]))

    def test_timing_choice_question_returns_explicit_order(self):
        answer = local_answer_question("现在是2026-06-13 21:10，我想问这周先谈合作还是先推进招聘，风险点和转机分别在哪？")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("先后顺序上", synthesis)
        self.assertTrue(any(token in synthesis for token in ["先谈合作", "先推进招聘"]))
        self.assertTrue(any(token in synthesis for token in ["风险点", "转机", "边界", "节奏"]))

    def test_name_studies_medium_result_mentions_style_fit(self):
        answer = local_answer_question("名字林清和适合男孩吗？用于正式姓名。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("林清和", synthesis)
        self.assertIn("拼音桥接数", synthesis)
        self.assertTrue(any(token in synthesis for token in ["清秀温和", "清雅平稳", "男孩正式姓名"]))

    def test_tarot_missing_follow_up_stays_focused_on_tarot_only(self):
        answer = local_answer_question("我想用塔罗看这个月项目能不能成，以及我该不该继续投钱。")
        controller = answer["result"]["controller"]
        self.assertIn("牌", controller["followUpPrompt"])
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["抽到", "发我"]))
        self.assertEqual(controller["missingInputs"], [{"system": "塔罗", "field": "牌阵或抽牌结果"}])

    def test_liuyao_missing_follow_up_stays_focused_on_hexagram_seed(self):
        answer = local_answer_question("我想用六爻看这次合作能不能成，顺便看看最大的卡点。")
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["三个数字", "本卦", "卦象"]))
        self.assertEqual(controller["selectedSystems"][0]["key"], "liuyao_and_meihua")

    def test_multi_symbolic_missing_follow_up_lists_action_steps_for_each_system(self):
        answer = local_answer_question("我想让塔罗和易经一起看这次合作该不该继续。")
        controller = answer["result"]["controller"]

        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertTrue(any(item["system"] == "塔罗" for item in controller["missingInputs"]))
        self.assertTrue(any(item["system"] == "易经与象数" for item in controller["missingInputs"]))
        self.assertIn("一起看", controller["followUpPrompt"])
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["1.", "2."]))
        self.assertIn("塔罗", controller["followUpPrompt"])
        self.assertIn("易经", controller["followUpPrompt"])
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["抽到的牌", "牌"]))
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["三个数字", "本卦", "动爻"]))

    def test_tarot_and_physiognomy_missing_follow_up_lists_both_preconditions(self):
        answer = local_answer_question("我想让塔罗和面相一起看这段关系还要不要继续。")
        controller = answer["result"]["controller"]

        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertTrue(any(item["system"] == "塔罗" for item in controller["missingInputs"]))
        self.assertTrue(any(item["system"] == "相术" for item in controller["missingInputs"]))
        self.assertIn("一起看", controller["followUpPrompt"])
        self.assertIn("塔罗", controller["followUpPrompt"])
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["面相", "额头", "照片观察"]))

    def test_general_wealth_question_enters_conversational_clarification(self):
        answer = local_answer_question("我最近财运怎么样？")
        controller = answer["result"]["controller"]
        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertTrue(controller["followUpPrompt"])
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["长期趋势", "出生年月日时", "事情背景"]))

    def test_fengshui_intent_without_address_stays_in_missing_input_instead_of_compute_error(self):
        answer = local_answer_question("我想搬家，看看风水")
        controller = answer["result"]["controller"]
        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertIn("地址", controller["followUpPrompt"])
        selected = controller["selectedSystems"][0]
        self.assertEqual(selected["key"], "fengshui")
        self.assertEqual(selected["status"], "missing_inputs")

    def test_fengshui_question_without_address_surfaces_structured_missing_fields(self):
        answer = local_answer_question("我想看现在住的房子会不会越住越压抑，从风水看该不该尽快搬。")
        controller = answer["result"]["controller"]

        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertEqual(controller["selectedSystems"][0]["key"], "fengshui")
        self.assertEqual(
            controller["missingInputs"],
            [
                {"system": "风水", "field": "城市或地址"},
                {"system": "风水", "field": "坐向或平面图"},
            ],
        )

    def test_general_wealth_question_surfaces_candidate_systems_for_follow_up(self):
        answer = local_answer_question("我最近财运怎么样？")
        controller = answer["result"]["controller"]
        selected_keys = [item["key"] for item in controller["selectedSystems"]]
        alternate_keys = [item["key"] for item in controller["alternateSystems"]]
        self.assertTrue(
            any(key in selected_keys for key in ["bazi", "ziwei_doushu", "western_astrology"])
            or any(key in alternate_keys for key in ["bazi", "ziwei_doushu", "western_astrology"])
        )

    def test_explicit_human_design_follow_up_requests_birth_data_with_clear_output_goal(self):
        answer = local_answer_question("我想看人类图")
        controller = answer["result"]["controller"]
        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertEqual(controller["selectedSystems"][0]["key"], "human_design")
        self.assertIn("出生年月日时", controller["followUpPrompt"])
        self.assertIn("出生地", controller["followUpPrompt"])
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["类型", "权威", "决策方式"]))

    def test_general_wealth_follow_up_distinguishes_long_term_from_current_issue(self):
        answer = local_answer_question("我最近财运怎么样？")
        prompt = answer["result"]["controller"]["followUpPrompt"]
        self.assertIn("长期财运走势", prompt)
        self.assertTrue(any(token in prompt for token in ["眼前这件事", "进财", "破财"]))
        self.assertIn("出生年月日时", prompt)

    def test_general_relationship_follow_up_distinguishes_long_term_from_current_issue(self):
        answer = local_answer_question("我想看感情")
        prompt = answer["result"]["controller"]["followUpPrompt"]
        self.assertIn("感情长期走向", prompt)
        self.assertTrue(any(token in prompt for token in ["眼前这段关系", "现状", "判断的点"]))

    def test_relationship_multi_question_mentions_mistake_or_action_in_synthesis(self):
        answer = local_answer_question(
            "我出生于1990-05-12 14:30，女，北京，想看婚姻走向、适合什么类型伴侣、关系里我最容易犯的错、如果今年想推进关系该注意什么。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue(any(token in synthesis for token in ["对象类型", "适合", "伴侣"]))
        self.assertTrue(any(token in synthesis for token in ["推进", "太急", "注意", "慢一点"]))

    def test_career_multi_question_mentions_capability_gap_in_synthesis(self):
        answer = local_answer_question(
            "我出生于1990-05-12 14:30，男，北京，想看未来两年的事业走向、适合的赚钱方式、最大的破财风险，以及如果要创业该先补哪块能力。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertTrue(any(token in synthesis for token in ["先补的能力", "现金流", "回款", "持续经营"]))

    def test_liuyao_numeric_question_does_not_request_hexagram_again_after_local_compute(self):
        answer = local_answer_question("我想问这次合作能不能成，数字 3 8 5。")
        liuyao = next(item for item in answer["result"]["system_answers"] if item["key"] == "liuyao_and_meihua")
        self.assertTrue(liuyao["used_local_calculation"])
        self.assertNotIn("起卦方式或卦象", liuyao["answer"])

    def test_local_oracle_surfaces_kabbalah_when_explicitly_requested(self):
        question = "我想从卡巴拉的 Tiphereth 角度看 career direction 和事业发展。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("kabbalah", top_keys[:3])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("Tiphereth", joined_answers)

    def test_local_oracle_surfaces_physiognomy_when_explicitly_requested(self):
        question = "我想从面相看一下：额头开阔明亮，眼神清，鼻梁挺，气色还不错，这是白天照片。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("physiognomy", top_keys[:3])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("主轴更落在", joined_answers)

    def test_local_oracle_surfaces_daoist_arts_when_explicitly_requested(self):
        question = "我想从道术角度看正一净宅科仪，涉及符、章表、诵经和法坛，这样的结构该怎么理解？"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("daoist_arts", top_keys[:3])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertTrue("道术看这类" in joined_answers or "法脉框架偏" in joined_answers)

    def test_local_oracle_surfaces_alchemy_when_explicitly_requested(self):
        question = "我想从炼金术和赫尔墨斯角度看 nigredo 到 albedo 的转化，里面还有 mercury、salt 和衔尾蛇。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("alchemy_and_hermeticism", top_keys[:3])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("炼金术这一路", joined_answers)

    def test_local_oracle_surfaces_modern_esotericism_when_explicitly_requested(self):
        question = "我想从现代神秘学角度看 manifestation、chakra、reiki 和 shadow work 这些实践到底是什么结构。"
        answer = local_answer_question(question)
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertIn("modern_esotericism", top_keys[:3])
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"][:6])
        self.assertIn("现代神秘学", joined_answers)

    def test_local_oracle_polishes_english_esoteric_terms_in_final_synthesis(self):
        modern = local_answer_question("我在做 manifesting、chakra、reiki 和 shadow work，想看这条实践路径的结构和风险。")
        modern_synthesis = modern["result"]["final_answer"]["synthesis"]
        self.assertIn("自我理解框架", modern_synthesis)
        self.assertIn("能量疗愈流", modern_synthesis)
        self.assertNotIn("identity-framework", modern_synthesis)
        self.assertNotIn("energy-healing", modern_synthesis)

        alchemy = local_answer_question("nigredo 阶段的 shadow work，材料是 crow mercury salt。")
        alchemy_synthesis = alchemy["result"]["final_answer"]["synthesis"]
        self.assertIn("黑化阶段", alchemy_synthesis)
        self.assertIn("汞性原则", alchemy_synthesis)
        self.assertIn("盐性原则", alchemy_synthesis)
        self.assertNotIn("nigredo", alchemy_synthesis)
        self.assertNotIn("mercury", alchemy_synthesis)
        alchemy_answer = " ".join(item["answer"] for item in alchemy["result"]["system_answers"])
        self.assertNotIn("ouroboros", alchemy_answer)

    def test_local_oracle_translates_remaining_astrology_and_date_signals(self):
        western, western_status = calculate_system(
            "western_astrology",
            {"birth_datetime": "1990-05-12 14:30", "birth_location": "Beijing"},
        )
        self.assertEqual(western_status, 200)
        western_text = " ".join(western["supporting_signals"]) + " " + western["primary_finding"]
        self.assertNotIn("Sun is in", western_text)
        self.assertNotIn("Moon is in", western_text)

        vedic, vedic_status = calculate_system(
            "vedic_astrology",
            {"birth_datetime": "1990-05-12 14:30", "birth_location": "Beijing"},
        )
        self.assertEqual(vedic_status, 200)
        vedic_text = " ".join(vedic["supporting_signals"]) + " " + vedic["primary_finding"]
        self.assertNotIn("Lagna is", vedic_text)
        self.assertNotIn("Jyeshtha", vedic_text)

        date_result, date_status = calculate_system(
            "date_selection",
            {"event_type": "move", "candidate_dates": ["2026-06-10", "2026-06-12"], "participant_birth": "1990-05-12"},
        )
        self.assertEqual(date_status, 200)
        date_text = " ".join(date_result["supporting_signals"]) + " " + date_result["primary_finding"]
        self.assertNotIn("neutral rule mix", date_text)
        self.assertNotIn("Top-ranked candidate", date_text)

    def test_modern_esotericism_polishes_remaining_family_labels(self):
        answer = local_answer_question("我想从现代神秘学和炼金术一起看 shadow work、manifestation、mercury、salt 这些东西是不是混了。")
        modern = next(item for item in answer["result"]["system_answers"] if item["key"] == "modern_esotericism")
        self.assertIn("显化变现流", modern["answer"])
        self.assertNotIn("manifestation-commerce", modern["answer"])
        self.assertNotIn("symbolic personal use", modern["answer"])

    def test_candidate_date_question_keeps_explicit_fengshui_and_onmyodo(self):
        answer = local_answer_question("我想从风水、择日和阴阳道看搬家，房子坐北朝南，候选日期是 2026年6月10日 和 2026年6月12日，地点在上海。")
        top_keys = [pack.key for pack in answer["systems"][:4]]
        self.assertIn("date_selection", top_keys)
        self.assertIn("fengshui", top_keys)
        self.assertIn("onmyodo", top_keys)

    def test_explicit_ziwei_qizheng_palace_question_covers_all_three_axes(self):
        answer = local_answer_question("我想从紫微斗数和七政四余一起看财帛宫、官禄宫和夫妻宫，出生于1990-05-12 14:30，男，北京。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("财帛宫", synthesis)
        self.assertIn("官禄宫", synthesis)
        self.assertIn("夫妻宫", synthesis)

    def test_explicit_ziwei_question_leads_final_synthesis(self):
        answer = local_answer_question("我想从紫微斗数看命宫、财帛宫和夫妻宫，出生于1990-05-12 14:30，男，北京。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("紫微斗数看", synthesis)
        self.assertNotIn("数字命理看", synthesis)

    def test_timing_question_promotes_qimen_to_direct_conclusion(self):
        answer = local_answer_question("现在是2026-06-14 10:20，我想问这周适不适合提离职。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("下一步", synthesis)
        self.assertIn("可以推进", synthesis)
        self.assertNotIn("辅助线索", synthesis)
        qimen = next(item for item in answer["result"]["system_answers"] if item["key"] == "qimen_dunjia")
        self.assertEqual(qimen["verdict_quality"], "conclusion")
        self.assertTrue(qimen["verdict"])

    def test_explicit_qizheng_siyu_question_uses_qizheng_as_lead_system(self):
        answer = local_answer_question("我想从七政四余看事业推进和财路，出生于1990-05-12 14:30，北京。")
        top_keys = [pack.key for pack in answer["systems"][:6]]
        self.assertEqual(top_keys[0], "qizheng_siyu")
        system_answers = answer["result"]["system_answers"]
        self.assertEqual(system_answers[0]["key"], "qizheng_siyu")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("七政四余看事业", synthesis)
        self.assertIn("官禄位", synthesis)

    def test_explicit_kabbalah_question_is_fully_chinese_polished(self):
        answer = local_answer_question("我想从卡巴拉的 Tiphereth 角度看 career direction 和 visible purpose。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("Tiphereth（美）", synthesis)
        self.assertIn("调和", synthesis)
        self.assertIn("整合", synthesis)
        self.assertNotIn("Beauty", synthesis)
        self.assertNotIn("harmony", synthesis)
        joined_answers = " ".join(item["answer"] for item in answer["result"]["system_answers"])
        self.assertNotIn("Tiphereth sits in", joined_answers)

    def test_explicit_daoist_question_translates_family_and_lineage_labels(self):
        answer = local_answer_question(
            "我是正一道法脉背景，想了解净宅、护身、化煞、安神这几类法事分别适合什么场景，有哪些禁忌和风险。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("净化与禳解类", synthesis)
        self.assertIn("正一", synthesis)
        self.assertNotIn("cleansing-exorcistic", synthesis)
        self.assertNotIn("zhengyi", synthesis)

    def test_explicit_physiognomy_question_translates_axis_label(self):
        answer = local_answer_question("我想从面相看一下：额头开阔明亮，眼神清，鼻梁挺，气色还不错，这是白天照片。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("精神头与当下行动力", synthesis)
        self.assertNotIn("vitality and immediate energy", synthesis)

    def test_physiognomy_multifacet_question_covers_career_relationship_strength_and_restraint(self):
        answer = local_answer_question(
            "额头开阔，眼神清，鼻梁直，下巴饱满，日间正面照片观察，想看整体面相倾向、事业气质和感情表达，哪里是优势，哪里要收着点？"
        )
        physiognomy = next(item for item in answer["result"]["system_answers"] if item["key"] == "physiognomy")
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(physiognomy["verdict_quality"], "conclusion")
        self.assertIn("事业气质", physiognomy["verdict"])
        self.assertIn("感情表达", physiognomy["verdict"])
        self.assertIn("优势在于", physiognomy["verdict"])
        self.assertIn("要收着点的地方", physiognomy["verdict"])
        self.assertIn("事业气质", synthesis)
        self.assertIn("感情表达", synthesis)
        self.assertIn("优势在于", synthesis)
        self.assertIn("要收着点的地方", synthesis)

    def test_onmyodo_trip_question_translates_hexagram_names_in_synthesis(self):
        answer = local_answer_question("我想从阴阳道角度看 2026-06-20 去上海西南方向出行，这个方向和时点合不合适？")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("噬嗑", synthesis)
        self.assertNotIn("Gnawing Bite", synthesis)

    def test_onmyodo_trip_question_without_explicit_direction_still_routes_to_onmyodo(self):
        answer = local_answer_question("我想从阴阳道看这周出差去东京，2026-06-18 出发，住新宿，方向和禁忌有什么要注意？")
        top_keys = [pack.key for pack in answer["systems"][:4]]
        self.assertIn("onmyodo", top_keys)
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("阴阳道按当前日时看", synthesis)
        self.assertNotIn("数字命理看", synthesis)

    def test_onmyodo_trip_question_without_explicit_direction_surfaces_direct_travel_verdict(self):
        answer = local_answer_question("我这周想去东京出差，2026-06-24 出发，住新宿，想看这个时点和方向有没有明显禁忌，要不要改期。")
        onmyodo = next(item for item in answer["result"]["system_answers"] if item["key"] == "onmyodo")
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(onmyodo["verdict_quality"], "conclusion")
        self.assertIn("阴阳道按当前日时看", synthesis)
        self.assertTrue(any(token in synthesis for token in ["偏不利", "改期", "绕开"]))
        self.assertNotIn("Providing For", synthesis)

    def test_onmyodo_trip_question_prefers_onmyodo_as_synthesis_lead(self):
        answer = local_answer_question("我这周想去东京出差，2026-06-24 出发，住新宿，想看这个时点和方向有没有明显禁忌，要不要改期。")
        controller = answer["result"]["controller"]
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(controller["selectedSystems"][0]["key"], "onmyodo")
        self.assertIn("阴阳道按当前日时看", synthesis)

    def test_onmyodo_relative_day_question_prefers_onmyodo_as_synthesis_lead(self):
        answer = local_answer_question("我后天要去西南方向见客户，阴阳道这套看这个方向和时点合不合适？")
        controller = answer["result"]["controller"]
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(controller["selectedSystems"][0]["key"], "onmyodo")
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertIn("阴阳道按当前日时看", synthesis)
        self.assertNotIn("如果只按当前这类时机题的结构先给直话", synthesis)

    def test_mixed_onmyodo_qimen_trip_question_still_delivers_onmyodo_conclusion(self):
        answer = local_answer_question("我这周想去杭州见合作方，也想顺便问一下这个方向会不会犯什么，阴阳道、奇门一起看。")
        controller = answer["result"]["controller"]
        synthesis = answer["result"]["final_answer"]["synthesis"]
        onmyodo = next(item for item in answer["result"]["system_answers"] if item["key"] == "onmyodo")

        self.assertEqual(controller["executionStatus"], "answered")
        self.assertEqual(controller["selectedSystems"][0]["key"], "onmyodo")
        self.assertEqual(onmyodo["verdict_quality"], "conclusion")
        self.assertIn("阴阳道按当前日时看", synthesis)
        self.assertNotIn("这一路已经给出可参考的计算结果", synthesis)

    def test_kabbalah_multi_node_question_mentions_secondary_node(self):
        answer = local_answer_question("我想从卡巴拉看 Tiphereth 和 Yesod 对事业与关系的影响。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("Tiphereth（美）", synthesis)
        self.assertIn("Yesod（基底）", synthesis)
        self.assertNotIn("substrate", synthesis)
        self.assertNotIn("linkage", synthesis)

    def test_physiognomy_sales_question_can_form_direct_verdict(self):
        answer = local_answer_question("我想从面相和八字一起看我适不适合做销售：额头开阔，眼神亮，鼻梁挺，出生于1990-05-12 14:30，男，北京。")
        physiognomy = next(item for item in answer["result"]["system_answers"] if item["key"] == "physiognomy")
        self.assertEqual(physiognomy["verdict_quality"], "conclusion")
        self.assertIn("销售", physiognomy["verdict"])
        self.assertNotIn("material anchoring and practical resources", physiognomy["verdict"])

    def test_explicit_fengshui_ziwei_priority_question_forms_direct_ordering(self):
        answer = local_answer_question(
            "我想从风水和紫微斗数一起看，是先换工作还是先搬家，出生于1990-05-12 14:30，男，北京，现在住上海，房子朝南。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("先换工作", synthesis)
        self.assertIn("再", synthesis)
        ziwei = next(item for item in answer["result"]["system_answers"] if item["key"] == "ziwei_doushu")
        self.assertEqual(ziwei["verdict_quality"], "conclusion")

    def test_career_mode_choice_question_mentions_employment_vs_entrepreneurship_vs_freelance(self):
        answer = local_answer_question(
            "我想从人类图、八字和西占一起看我更适合上班、创业还是自由职业，出生于1990-05-12 14:30，男，北京。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("上班", synthesis)
        self.assertIn("自由职业", synthesis)
        self.assertIn("创业", synthesis)
        self.assertIn("后一阶段", synthesis)

    def test_career_option_question_mentions_sales_consulting_project_work(self):
        answer = local_answer_question(
            "我想从八字、紫微和西占一起看，我更适合做销售、咨询还是自己接项目，出生于1990-05-12 14:30，男，北京。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("咨询", synthesis)
        self.assertIn("销售", synthesis)
        self.assertIn("自己接项目", synthesis)
        self.assertTrue("后一阶段" in synthesis or "放在已有口碑和稳定客户之后" in synthesis)

    def test_career_mode_choice_question_mentions_employment_vs_freelance_vs_self_project(self):
        answer = local_answer_question(
            "1990-05-12 14:30，北京，想看我的人类图类型、决策方式，以及我更适合上班、自由职业还是自己接项目。"
        )
        human_design = next(item for item in answer["result"]["system_answers"] if item["key"] == "human_design")
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(human_design["verdict_quality"], "conclusion")
        self.assertIn("上班", human_design["verdict"])
        self.assertIn("自由职业", human_design["verdict"])
        self.assertIn("自己接项目", human_design["verdict"])
        self.assertTrue("后一阶段" in human_design["verdict"] or "不要一上来" in human_design["verdict"])
        self.assertIn("上班", synthesis)
        self.assertIn("自由职业", synthesis)
        self.assertIn("自己接项目", synthesis)

    def test_answered_supporting_systems_do_not_keep_optional_missing_inputs(self):
        answer = local_answer_question(
            "我不想听套话，你就从人类图的角度告诉我，我现在更适合在组织里冲，还是先做个人输出品牌，1990-05-12 14:30，北京。"
        )
        bazi = next(item for item in answer["result"]["system_answers"] if item["key"] == "bazi")

        self.assertTrue(bazi["used_local_calculation"])
        self.assertEqual(bazi["missing_inputs"], [])

    def test_human_like_career_question_with_birth_details_at_tail_still_routes_to_birth_chart_systems(self):
        answer = local_answer_question(
            "我不想听空话，就直接告诉我，我这种人现阶段到底更适合在公司里做出成绩，还是开始自己出来接活，或者直接扛项目？1990-05-12 14:30，北京。"
        )
        controller = answer["result"]["controller"]
        selected_keys = [item["key"] for item in controller["selectedSystems"]]
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(controller["executionStatus"], "answered")
        self.assertIn("bazi", selected_keys)
        self.assertIn("western_astrology", selected_keys)
        self.assertIn("human_design", selected_keys)
        self.assertIn("上班", synthesis)

    def test_tail_birth_city_hint_makes_location_based_birth_systems_computable(self):
        question = "我不想听空话，就直接告诉我，我这种人现阶段到底更适合在公司里做出成绩，还是开始自己出来接活，或者直接扛项目？1990-05-12 14:30，北京。"
        diagnostics = {item["key"]: item for item in system_question_diagnostics(question)}
        answer = local_answer_question(question)
        selected_keys = [pack.key for pack in answer["systems"]]

        for key in ["western_astrology", "human_design", "vedic_astrology", "qizheng_siyu"]:
            self.assertIn(key, selected_keys)
            self.assertTrue(diagnostics[key]["canReplyNow"])
            self.assertIn(diagnostics[key]["replyStatus"], {"answered", "computable"})
            self.assertEqual(diagnostics[key]["missingInputs"], [])

    def test_kabbalah_balance_question_gives_direct_imbalance_reading(self):
        answer = local_answer_question(
            "我想从卡巴拉看，不要只说优势，也直接说我最容易失衡在哪，特别是事业推进和自我价值感这两块。"
        )
        kabbalah = next(item for item in answer["result"]["system_answers"] if item["key"] == "kabbalah")
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(kabbalah["verdict_quality"], "conclusion")
        self.assertIn("最容易失衡", kabbalah["verdict"])
        self.assertIn("事业", synthesis)
        self.assertIn("失衡", synthesis)

    def test_daoist_priority_question_gives_order_and_boundary(self):
        answer = local_answer_question(
            "我是正一道法脉背景，最近住的地方总觉得压着，净宅、护身、化煞、安神这几类我现在先做哪类，哪些别乱碰？"
        )
        daoist = next(item for item in answer["result"]["system_answers"] if item["key"] == "daoist_arts")
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(daoist["verdict_quality"], "conclusion")
        self.assertIn("先做", daoist["verdict"])
        self.assertTrue(any(token in daoist["verdict"] for token in ["别乱碰", "不要一上来就重手", "不适合"]))
        self.assertIn("净宅", synthesis)
        self.assertIn("化煞", synthesis)

    def test_human_design_org_vs_personal_brand_question_gets_direct_ranking(self):
        answer = local_answer_question(
            "我不想听套话，你就从人类图的角度告诉我，我现在更适合在组织里冲，还是先做个人输出品牌，1990-05-12 14:30，北京。"
        )
        human_design = next(item for item in answer["result"]["system_answers"] if item["key"] == "human_design")
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertEqual(human_design["verdict_quality"], "conclusion")
        self.assertIn("组织里冲", human_design["verdict"])
        self.assertIn("个人输出品牌", human_design["verdict"])
        self.assertIn("组织里冲", synthesis)

    def test_human_design_org_vs_personal_brand_synthesis_does_not_repeat_structural_fallback(self):
        answer = local_answer_question(
            "我不想听套话，你就从人类图的角度告诉我，我现在更适合在组织里冲，还是先做个人输出品牌，1990-05-12 14:30，北京。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertIn("组织里冲", synthesis)
        self.assertNotIn("如果先不拉命盘", synthesis)

    def test_tarot_answered_synthesis_does_not_append_generic_relationship_direct_note(self):
        answer = local_answer_question(
            "三张牌分别是愚者正位、圣杯二正位、宝剑十逆位。我想问这段关系接下来一个月会怎么发展，我该主动还是先观察？"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertIn("愚者", synthesis)
        self.assertNotIn("如果只按当前这类关系题的结构先给直话", synthesis)

    def test_answered_yijing_controller_missing_inputs_stays_empty(self):
        answer = local_answer_question("我想从易经象数看我这次换工作要不要动，数字 6 1 4。")
        controller = answer["result"]["controller"]

        self.assertEqual(controller["executionStatus"], "answered")
        self.assertEqual(controller["missingInputs"], [])

    def test_answered_human_design_controller_missing_inputs_stays_empty(self):
        answer = local_answer_question(
            "我不想听套话，你就从人类图的角度告诉我，我现在更适合在组织里冲，还是先做个人输出品牌，1990-05-12 14:30，北京。"
        )
        controller = answer["result"]["controller"]

        self.assertEqual(controller["executionStatus"], "answered")
        self.assertEqual(controller["missingInputs"], [])

    def test_physiognomy_without_observable_features_stays_in_follow_up_mode(self):
        answer = local_answer_question("我想从面相看一下我适不适合做销售。")
        controller = answer["result"]["controller"]

        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertEqual(controller["selectedSystems"][0]["key"], "physiognomy")
        self.assertTrue(any("外貌描述" in item["field"] for item in controller["missingInputs"]))
        self.assertTrue(any(token in (controller["followUpPrompt"] or "") for token in ["外貌特征", "照片观察"]))

    def test_vague_physiognomy_description_surfaces_structured_missing_input(self):
        answer = local_answer_question("我想看面相，但我现在只能说个大概：额头还行，眼神不差，鼻子算直，这样够不够？")
        controller = answer["result"]["controller"]
        physiognomy = next(item for item in answer["result"]["system_answers"] if item["key"] == "physiognomy")

        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertEqual(controller["selectedSystems"][0]["key"], "physiognomy")
        self.assertTrue(any("外貌描述" in item["field"] for item in controller["missingInputs"]))
        self.assertTrue(any("外貌描述" in item for item in physiognomy["missing_inputs"]))
        self.assertTrue(any(token in (controller["followUpPrompt"] or "") for token in ["具体一点", "照片观察"]))

    def test_yijing_numeric_question_translates_hexagram_names_to_chinese(self):
        answer = local_answer_question("我想从易经象数看我这次换工作要不要动，数字 6 1 4。")
        synthesis = answer["result"]["final_answer"]["synthesis"]

        self.assertNotIn("Attending", synthesis)
        self.assertNotIn("Parting", synthesis)
        self.assertIn("需", synthesis)
        self.assertIn("夬", synthesis)


    def test_human_like_project_vs_big_company_question_gives_ranked_recommendation_without_birth_data(self):
        answer = local_answer_question(
            "朋友拉我一起做项目，说来钱快；一个是大厂岗位，慢一点但稳定... 主推荐、次推荐、不推荐"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertIn("主推荐", synthesis)
        self.assertIn("次推荐", synthesis)
        self.assertIn("不推荐", synthesis)
        self.assertEqual(controller["executionStatus"], "answered")

    def test_negative_framed_sales_consulting_project_question_names_riskiest_and_steadiest_path(self):
        answer = local_answer_question(
            "销售、咨询、自己接项目这三条里，哪条最容易前面有戏后面被回款、边界或者关系拖死？哪条最稳？"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertIn("咨询", synthesis)
        self.assertIn("自己接项目", synthesis)
        self.assertTrue(any(token in synthesis for token in ["最稳", "回款", "边界"]))
        self.assertEqual(controller["executionStatus"], "answered")

    def test_three_way_city_house_job_ordering_question_returns_explicit_ranking(self):
        answer = local_answer_question("先换城市、先换房、还是先稳工作？排个序")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertIn("先稳工作", synthesis)
        self.assertIn("再换房", synthesis)
        self.assertIn("最后再换城市", synthesis)
        self.assertEqual(controller["executionStatus"], "answered")

    def test_human_like_dirty_priority_question_prefers_work_before_move(self):
        answer = local_answer_question(
            "我有点纠结... 北京男... 现在人在上海，房子朝南... 从风水、紫微、八字一起看... 先换工作还是先搬家？顺便说说如果硬要两件一起推..."
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("先换工作", synthesis)
        self.assertIn("再处理搬家", synthesis)

    def test_human_like_name_direction_question_generates_candidates_instead_of_treating_whole_sentence_as_name(self):
        answer = local_answer_question(
            "名字这事我家里吵半天了，小孩姓周，男孩，想要不土、不网红、读起来顺，最好兼顾一点八字，但我现在就先想听方向，不要一上来一堆生僻字。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertIn("首选", synthesis)
        self.assertIn("周", synthesis)
        self.assertEqual(controller["executionStatus"], "answered")

    def test_name_direction_only_request_without_birth_can_answer(self):
        answer = local_answer_question("孩子姓周，男孩，要书卷气，不生僻，也别太像网名，先给三组方向。")
        controller = answer["result"]["controller"]
        synthesis = answer["result"]["final_answer"]["synthesis"]
        naming = next(item for item in answer["result"]["system_answers"] if item["key"] == "name_studies")

        self.assertEqual(controller["executionStatus"], "answered")
        self.assertEqual(controller["missingInputs"], [])
        self.assertTrue(naming["used_local_calculation"])
        self.assertEqual(naming["verdict_quality"], "conclusion")
        self.assertEqual(naming["missing_inputs"], [])
        self.assertTrue(any(token in synthesis for token in ["首选", "方向", "周"]))

    def test_human_like_job_plus_side_hustle_vs_solo_question_gets_direct_ranking(self):
        answer = local_answer_question(
            "我这两个月一直想动一动副业，朋友说我适合自己出来接活，但我又怕钱回不来、人情也烂掉。你从八字、紫微、西占这种角度，直接说我更适合上班主线+副业，还是直接出去单干。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertIn("上班主线", synthesis)
        self.assertTrue(any(token in synthesis for token in ["单干放在后面", "单干"]))
        self.assertEqual(controller["executionStatus"], "answered")

    def test_human_like_daoist_question_with_negated_harm_is_not_misclassified_as_coercive(self):
        answer = local_answer_question(
            "我想从道家法事那套看一下，不是让我害人，就是最近家里老吵、我自己也心烦，净宅、安神、护身这三种到底先做哪个，哪些情况压根不该碰？"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        self.assertIn("净宅", synthesis)
        self.assertNotIn("高风险边界", synthesis)

    def test_human_like_go_meet_partner_timing_question_does_not_fall_back_to_generic_clarification(self):
        answer = local_answer_question(
            "这两周要不要去杭州见那个合作方？嘴上都说得很好听，但我总感觉节奏不太对。就看时机，别给我讲性格。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in synthesis for token in ["先约见", "先试探", "边界", "推进正式拍板"]))
        self.assertEqual(controller["executionStatus"], "answered")

    def test_human_like_relationship_stop_loss_question_gets_direct_verdict(self):
        answer = local_answer_question(
            "别给我上课，我就想知道：现在这个关系到底值不值得继续磨，还是该撤？前面还好过，现在全是消耗。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in synthesis for token in ["不建议继续硬磨", "及时止损", "收缩投入", "拉开一点节奏"]))
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertNotIn("你这次更想看感情长期走向", synthesis)

    def test_human_like_monthly_relationship_question_is_not_routed_to_general_clarification(self):
        answer = local_answer_question("这个月我和他还有没有必要续谈，还是应该及时止损？")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in synthesis for token in ["及时止损", "收缩投入", "主动修复", "现实动作"]))
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertNotEqual(controller["questionType"], "综合问题")

    def test_human_like_work_style_question_gets_direct_ranking(self):
        answer = local_answer_question("我更适合做整合型、表达型，还是深度执行型？")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in synthesis for token in ["整合和表达放在前面", "深度执行放在支撑位", "提炼", "串联"]))
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertIn(controller["questionType"], ["事业/职业问题", "性格/方向问题"])

    def test_human_like_front_middle_back_work_style_question_gets_direct_ranking(self):
        answer = local_answer_question("我这种人更适合做哪种活：前端对接、中间统筹，还是后端死磕执行？")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in synthesis for token in ["中间统筹", "前端对接", "后端执行"]))
        self.assertEqual(controller["executionStatus"], "answered")

    def test_human_like_content_ip_vs_operating_delivery_question_gets_direct_ranking(self):
        answer = local_answer_question("我现在手上有两条路，一条是继续做内容IP，另一条是去帮别人做操盘交付。你就直接说现阶段主推哪条？")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in synthesis for token in ["内容IP", "操盘交付"]))
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertIn(controller["questionType"], ["事业/职业问题", "事业/财运问题"])

    def test_human_like_surname_boy_bookish_naming_direction_routes_to_name_generation(self):
        answer = local_answer_question("孩子姓沈，男孩，别给我生僻字，也别太娘，最好有点书卷气，先给我方向就行。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertIn("起名", controller["questionType"])
        self.assertTrue(any(token in synthesis for token in ["书卷", "名字", "首选"]))

    def test_human_like_investor_touch_base_timing_question_does_not_fall_back_to_wealth_clarification(self):
        answer = local_answer_question("我这两个月到底该不该去见那个投资人？不是签协议，就是先碰一下。我怕我现在去显得很急。")
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertIn(controller["questionType"], ["时机/成败问题", "财运/收入问题"])
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertTrue(any(token in synthesis for token in ["先", "节奏", "缓进", "推进"]))

    def test_human_like_project_investment_question_gets_stop_additional_spend_verdict(self):
        answer = local_answer_question(
            "我不想聊虚的，就直接说我这个项目要继续投钱还是停掉？现在看起来已经出现回款风险。"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in synthesis for token in ["不建议继续加码", "先停新增投入", "回款路径", "止损线"]))
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertNotIn("你这次更想看长期财运走势", synthesis)

    def test_human_like_multi_system_spiritual_boundary_question_prefers_stop_then_boundary(self):
        answer = local_answer_question(
            "道术、卡巴拉、炼金术一起看，我更适合先净化整理、先做边界保护，还是先停下来别乱碰？"
        )
        synthesis = answer["result"]["final_answer"]["synthesis"]
        controller = answer["result"]["controller"]
        self.assertTrue(any(token in synthesis for token in ["先停下来别乱碰", "边界保护", "高刺激", "生活秩序稳住"]))
        self.assertEqual(controller["executionStatus"], "answered")


    def test_wrapped_follow_up_normalization_moves_supplement_ahead_of_original(self):
        question = "原问题：我最近财运怎么样？\n补充信息：我想看长期走势，1990-05-12 14:30，男，北京"
        normalized = normalize_multi_turn_question(question)

        self.assertTrue(normalized.startswith("我想看长期走势"))
        self.assertIn("我财运怎么样", normalized)
        self.assertNotIn("原问题：", normalized)
        self.assertNotIn("补充信息：", normalized)

    def test_wrapped_human_design_follow_up_is_computable(self):
        question = "原问题：我想看人类图\n补充信息：1990-05-12 14:30，北京"
        diagnostics = {item["key"]: item for item in system_question_diagnostics(question)}
        human_design = diagnostics["human_design"]

        self.assertTrue(human_design["questionMatched"])
        self.assertTrue(human_design["canReplyNow"])
        self.assertIn(human_design["replyStatus"], {"answered", "computable"})
        self.assertEqual(human_design["missingInputs"], [])

    def test_wrapped_long_term_wealth_follow_up_routes_to_birth_chart_systems(self):
        question = "原问题：我最近财运怎么样？\n补充信息：我想看长期走势，1990-05-12 14:30，男，北京"
        answer = local_answer_question(question)
        controller = answer["result"]["controller"]
        selected_keys = [item["key"] for item in controller["selectedSystems"]]
        selected_modes = {item["mode"] for item in controller["selectedSystems"]}

        self.assertEqual(controller["executionStatus"], "answered")
        self.assertEqual(controller["questionType"], "事业/财运问题")
        self.assertIn("destiny", selected_modes)
        self.assertNotIn("liu_ren", selected_keys[:4])
        self.assertNotIn("qimen_dunjia", selected_keys[:4])
        self.assertTrue(any(key in selected_keys for key in ["bazi", "ziwei_doushu", "western_astrology"]))

if __name__ == "__main__":
    unittest.main()
