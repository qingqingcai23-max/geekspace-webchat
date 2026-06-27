import unittest
from unittest.mock import patch

from server import app, benchmark_all_systems, local_answer_question, safety_screen, system_question_diagnostics


GOOD_DAY_QUESTION = "\u0032\u0030\u0032\u0036\u5e74\u0036\u6708\u0038\u53f7\uff0c\u662f\u4e2a\u597d\u65e5\u5b50\u5417\uff1f"
FENGSHUI_QUESTION = "\u4e0a\u6d77\u6d66\u4e1c\u67d0\u5c0f\u533a 12 \u680b 1802\uff0c\u5750\u5317\u671d\u5357\uff0c\u60f3\u770b\u9002\u4e0d\u9002\u5408\u957f\u671f\u5c45\u4f4f\u3002"
BIRTH_QUESTION = "\u6211\u51fa\u751f\u4e8e1990-05-12 14:30\uff0c\u7537\uff0c\u5317\u4eac\uff0c\u60f3\u770b\u6211\u7684\u6027\u683c\u3001\u4e8b\u4e1a\u548c\u957f\u671f\u53d1\u5c55\u3002"
NAMING_QUESTION = "\u7ed92026\u5e746\u670813\u65e523\u70b942\u5206\u51fa\u751f\u7684\u5973\u5b9d\u5b9d\uff0c\u59d3\u5f6d\u8d77\u4e00\u4e2a\u540d\u5b57\u3002"
ENGLISH_BIRTH_CAREER_QUESTION = "I was born on May 12, 1990 at 2:30pm in Beijing. Please read my career."
TIMING_QUESTION = "\u73b0\u5728\u662f2026-06-13 21:10\uff0c\u6211\u60f3\u95ee\u8fd9\u5468\u5148\u8c08\u5408\u4f5c\u8fd8\u662f\u5148\u63a8\u8fdb\u62db\u8058\uff0c\u98ce\u9669\u70b9\u548c\u8f6c\u673a\u5206\u522b\u5728\u54ea\uff1f"


class SystemDiagnosticsTests(unittest.TestCase):
    def test_oracle_api_defaults_to_auto_local_routing_for_chinese_birth_chart_question(self):
        client = app.test_client()
        response = client.post(
            "/api/oracle",
            json={
                "question": "请直接按八字命理分析：男，1995年10月18日早上8点30分出生于上海。重点看事业、财运、感情、健康，并给出喜用神与近期建议。"
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["model"], "local-vault-synthesis")
        self.assertEqual(payload["controller"]["executionStatus"], "answered")
        selected_keys = {item["key"] for item in payload["controller"]["selectedSystems"]}
        self.assertIn("bazi", selected_keys)
        self.assertNotEqual(payload["controller"]["questionType"], "综合问题")

    def test_oracle_api_defaults_to_auto_local_routing_for_chinese_fengshui_question(self):
        client = app.test_client()
        response = client.post(
            "/api/oracle",
            json={"question": "请按风水分析：上海浦东新区陆家嘴一套住宅，坐北朝南，适不适合长期居住？"},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["model"], "local-vault-synthesis")
        self.assertEqual(payload["controller"]["executionStatus"], "answered")
        selected_keys = [item["key"] for item in payload["controller"]["selectedSystems"]]
        self.assertIn("fengshui", selected_keys)
        self.assertEqual(payload["controller"]["questionType"], "空间/环境问题")

    def test_map_geocode_api_returns_location_payload(self):
        client = app.test_client()
        with patch("server.geocode_address") as mock_geocode, patch("server.static_map_url", return_value="https://example.com/static-map"):
            from xuanxue_engine.map_provider_tencent import TencentMapResolvedLocation

            mock_geocode.return_value = TencentMapResolvedLocation(
                query="北京朝阳区",
                address="北京市朝阳区",
                title="朝阳区",
                lat=39.9219,
                lng=116.4436,
                adcode="110105",
                province="北京市",
                city="北京市",
                district="朝阳区",
            )
            response = client.get("/api/maps/geocode?address=北京朝阳区")
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload["address"], "北京市朝阳区")
            self.assertEqual(payload["city"], "北京市")
            self.assertEqual(payload["staticMapUrl"], "https://example.com/static-map")

    def test_tencent_geocode_falls_back_to_osm_when_quota_is_exceeded(self):
        from xuanxue_engine import map_provider_tencent as provider
        from xuanxue_engine.map_provider_tencent import TencentMapApiError

        with (
            patch.object(provider, "_request", side_effect=TencentMapApiError("此key每日调用量已达到上限", status=120)),
            patch.object(provider, "openstreetmap_geocode_address") as mock_osm,
        ):
            mock_osm.return_value = provider.TencentMapResolvedLocation(
                query="上海市浦东新区陆家嘴",
                address="中国上海市浦东新区陆家嘴",
                title="陆家嘴",
                lat=31.2354,
                lng=121.4997,
                adcode="",
                province="上海市",
                city="上海市",
                district="浦东新区",
                source="osm-nominatim",
            )
            resolved = provider.geocode_address("上海市浦东新区陆家嘴")
            self.assertEqual(resolved.source, "osm-nominatim")
            self.assertEqual(resolved.city, "上海市")
            mock_osm.assert_called_once()

    def test_tencent_geocode_normalizes_natural_language_address_before_osm_fallback(self):
        from xuanxue_engine import map_provider_tencent as provider
        from xuanxue_engine.map_provider_tencent import TencentMapApiError

        with (
            patch.object(provider, "_request", side_effect=TencentMapApiError("此key每日调用量已达到上限", status=120)),
            patch.object(provider, "openstreetmap_geocode_address") as mock_osm,
        ):
            mock_osm.return_value = provider.TencentMapResolvedLocation(
                query="上海浦东新区陆家嘴一套住宅",
                address="中国上海市浦东新区陆家嘴",
                title="陆家嘴",
                lat=31.2354,
                lng=121.4997,
                adcode="",
                province="上海市",
                city="上海市",
                district="浦东新区",
                source="osm-nominatim",
            )
            provider.geocode_address("上海浦东新区陆家嘴一套住宅")
            self.assertEqual(mock_osm.call_args.kwargs["region"], "")
            self.assertEqual(mock_osm.call_args.args[0], "上海浦东新区陆家嘴一套住宅")

    def test_map_geocode_api_supports_osm_fallback_payload(self):
        client = app.test_client()
        with patch("server.geocode_address") as mock_geocode, patch("server.static_map_url", return_value="https://example.com/static-map"):
            from xuanxue_engine.map_provider_tencent import TencentMapResolvedLocation

            mock_geocode.return_value = TencentMapResolvedLocation(
                query="上海市浦东新区陆家嘴",
                address="中国上海市浦东新区陆家嘴",
                title="陆家嘴",
                lat=31.2354,
                lng=121.4997,
                adcode="",
                province="上海市",
                city="上海市",
                district="浦东新区",
                source="osm-nominatim",
            )
            response = client.get("/api/maps/geocode?address=%E4%B8%8A%E6%B5%B7%E5%B8%82%E6%B5%A6%E4%B8%9C%E6%96%B0%E5%8C%BA%E9%99%86%E5%AE%B6%E5%98%B4")
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload["source"], "osm-nominatim")
            self.assertEqual(payload["city"], "上海市")

    def test_map_provider_normalizes_natural_language_address_suffixes(self):
        from xuanxue_engine import map_provider_tencent as provider

        self.assertEqual(provider._normalize_address_query("上海浦东新区陆家嘴一套住宅"), "上海浦东新区陆家嘴")
        self.assertEqual(provider._normalize_address_query("请按风水分析：上海浦东新区陆家嘴一套住宅"), "上海浦东新区陆家嘴")

    def test_property_context_api_returns_external_environment_screening(self):
        client = app.test_client()
        with (
            patch("server.geocode_address") as mock_geocode,
            patch("server.static_map_url", return_value="https://example.com/static-map"),
            patch("server.collect_nearby_poi_signals") as mock_collect_poi,
        ):
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
                "funeral": [{"title": "福寿陵园", "distance": 700}],
                "park": [{"title": "滨河公园", "distance": 300}],
                "water": [{"title": "河道", "distance": 260}],
            }
            response = client.post(
                "/api/maps/property-context",
                json={"address": "上海浦东某小区 12 栋 1802", "facing_direction": "坐北朝南"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertIn("externalEnvironment", payload)
            self.assertEqual(payload["externalEnvironment"]["verdict"], "caution")
            self.assertIn("poiSummary", payload)

    def test_property_context_api_degrades_when_tencent_poi_quota_is_exceeded(self):
        client = app.test_client()
        with (
            patch("server.geocode_address") as mock_geocode,
            patch("server.static_map_url", return_value="https://example.com/static-map"),
            patch("server.collect_nearby_poi_signals") as mock_collect_poi,
        ):
            from xuanxue_engine.map_provider_tencent import TencentMapApiError, TencentMapResolvedLocation

            mock_geocode.return_value = TencentMapResolvedLocation(
                query="上海浦东新区陆家嘴",
                address="上海市浦东新区陆家嘴",
                title="陆家嘴",
                lat=31.2354,
                lng=121.4997,
                adcode="310115",
                province="上海市",
                city="上海市",
                district="浦东新区",
            )
            mock_collect_poi.side_effect = TencentMapApiError("此key每日调用量已达到上限", status=120)
            response = client.post(
                "/api/maps/property-context",
                json={"address": "上海浦东新区陆家嘴", "facing_direction": "坐北朝南"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertEqual(payload["mapStatus"]["poiSearch"], "quota_exceeded")
            self.assertTrue(payload["mapStatus"]["warnings"])
            self.assertEqual(payload["poiSummary"], {})
            self.assertEqual(payload["poiHits"], {})
            self.assertEqual(payload["staticMapUrl"], "https://example.com/static-map")

    def test_single_good_day_question_only_selects_date_selection(self):
        result = local_answer_question(GOOD_DAY_QUESTION)
        self.assertEqual([pack.key for pack in result["systems"]], ["date_selection"])

        diagnostics = result["result"]["system_diagnostics"]
        by_key = {item["key"]: item for item in diagnostics}
        self.assertEqual(by_key["date_selection"]["replyStatus"], "answered")
        self.assertTrue(by_key["date_selection"]["canReplyNow"])
        self.assertEqual(by_key["fengshui"]["replyStatus"], "not_applicable")
        self.assertFalse(by_key["fengshui"]["questionMatched"])
        self.assertEqual(by_key["yijing_and_symbolism"]["replyStatus"], "not_applicable")
        self.assertFalse(by_key["yijing_and_symbolism"]["questionMatched"])

    def test_fengshui_question_matches_fengshui_but_not_divination_systems(self):
        diagnostics = system_question_diagnostics(FENGSHUI_QUESTION)
        by_key = {item["key"]: item for item in diagnostics}

        self.assertTrue(by_key["fengshui"]["questionMatched"])
        self.assertIn(by_key["fengshui"]["replyStatus"], {"answered", "computable"})
        self.assertFalse(by_key["yijing_and_symbolism"]["questionMatched"])
        self.assertFalse(by_key["liuyao_and_meihua"]["questionMatched"])

    def test_birth_chart_question_excludes_timing_and_space_systems_without_explicit_request(self):
        diagnostics = system_question_diagnostics(BIRTH_QUESTION)
        by_key = {item["key"]: item for item in diagnostics}

        self.assertTrue(by_key["bazi"]["questionMatched"])
        self.assertTrue(by_key["western_astrology"]["questionMatched"])
        self.assertFalse(by_key["fengshui"]["questionMatched"])
        self.assertFalse(by_key["qimen_dunjia"]["questionMatched"])
        self.assertFalse(by_key["liu_ren"]["questionMatched"])

    def test_naming_question_matches_name_studies(self):
        diagnostics = system_question_diagnostics(NAMING_QUESTION)
        by_key = {item["key"]: item for item in diagnostics}

        self.assertTrue(by_key["name_studies"]["questionMatched"])
        self.assertIn(by_key["name_studies"]["replyStatus"], {"answered", "computable"})

    def test_naming_question_controller_identifies_naming_type(self):
        result = local_answer_question(NAMING_QUESTION)
        controller = result["result"]["controller"]
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertEqual(controller["questionType"], "起名/命名问题")

    def test_general_wealth_question_selects_birth_chart_routes_for_follow_up(self):
        result = local_answer_question("我最近财运怎么样？")
        controller = result["result"]["controller"]
        selected_keys = [item["key"] for item in controller["selectedSystems"]]

        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertEqual(controller["questionType"], "事业/财运问题")
        self.assertTrue(any(key in selected_keys for key in ["bazi", "ziwei_doushu", "western_astrology"]))
        self.assertIn("长期财运走势", controller["followUpPrompt"])

    def test_birth_wealth_question_with_birth_details_is_answered(self):
        result = local_answer_question("我想看财运，1990-05-12 14:30，男，北京")
        controller = result["result"]["controller"]
        selected_keys = {item["key"] for item in controller["selectedSystems"]}

        self.assertEqual(controller["executionStatus"], "answered")
        self.assertEqual(controller["questionType"], "事业/财运问题")
        self.assertIn("bazi", selected_keys)
        self.assertIn("western_astrology", selected_keys)

    def test_full_birth_chart_question_with_explicit_axes_prefers_bazi_full_chart_synthesis(self):
        result = local_answer_question("我出生于1990-05-12 14:30，男，北京，想看我的性格、事业、财运、婚恋、健康和适合的发展方向。")
        synthesis = result["result"]["final_answer"]["synthesis"]

        self.assertIn("八字全盘看", synthesis)
        self.assertIn("婚恋", synthesis)
        self.assertIn("健康", synthesis)

    def test_short_name_generation_question_routes_to_name_studies_follow_up(self):
        result = local_answer_question("我想起个名字")
        controller = result["result"]["controller"]

        self.assertEqual(controller["executionStatus"], "needs_input")
        self.assertIn("起名", controller["questionType"])
        self.assertEqual(controller["selectedSystems"][0]["key"], "name_studies")
        self.assertTrue(any(token in controller["followUpPrompt"] for token in ["姓氏", "性别", "用途"]))

    def test_benchmark_suite_uses_per_system_questions(self):
        results = benchmark_all_systems()
        self.assertEqual(len(results), 21)
        by_key = {item["key"]: item for item in results}

        self.assertEqual(by_key["fengshui"]["question"], FENGSHUI_QUESTION)
        self.assertEqual(by_key["date_selection"]["question"], "\u6211\u60f3\u642c\u5bb6\uff0c\u5019\u9009\u65e5\u671f\u662f 2026\u5e746\u670810\u65e5 \u548c 2026\u5e746\u670812\u65e5\uff0c\u5730\u70b9\u5728\u4e0a\u6d77\u3002")
        self.assertTrue(by_key["fengshui"]["matched"])
        self.assertTrue(by_key["date_selection"]["matched"])
        self.assertTrue(by_key["date_selection"]["computable"])

    def test_benchmark_suite_matches_current_localized_output_for_key_systems(self):
        results = benchmark_all_systems()
        by_key = {item["key"]: item for item in results}
        for key in [
            "bazi",
            "ziwei_doushu",
            "qizheng_siyu",
            "western_astrology",
            "vedic_astrology",
            "human_design",
            "numerology",
            "qimen_dunjia",
            "liu_ren",
            "fengshui",
            "name_studies",
            "tarot",
            "kabbalah",
            "onmyodo",
            "modern_esotericism",
        ]:
            self.assertTrue(by_key[key]["resultOk"], key)

    def test_invalid_birth_date_returns_follow_up_instead_of_crashing(self):
        result = local_answer_question("\u6211\u51fa\u751f\u4e8e1990-02-30 14:30\uff0c\u7537\uff0c\u5317\u4eac\uff0c\u5e2e\u6211\u770b\u516b\u5b57\u3002")
        self.assertEqual(result["result"]["final_answer"]["synthesis"], "\u516c\u5386\u65e5\u671f\u65e0\u6548\uff1aday is out of range for month")
        self.assertEqual(result["result"]["controller"]["executionStatus"], "needs_input")

    def test_english_birth_question_routes_to_birth_chart_systems(self):
        result = local_answer_question(ENGLISH_BIRTH_CAREER_QUESTION)
        controller = result["result"]["controller"]
        self.assertEqual(controller["executionStatus"], "answered")
        self.assertEqual(controller.get("issueType", ""), "")
        selected_keys = {item["key"] for item in controller["selectedSystems"]}
        self.assertIn("western_astrology", selected_keys)
        self.assertNotIn("date_selection", selected_keys)

    def test_timing_question_routes_to_timing_systems(self):
        result = local_answer_question(TIMING_QUESTION)
        controller = result["result"]["controller"]
        selected_keys = {item["key"] for item in controller["selectedSystems"]}
        self.assertIn("qimen_dunjia", selected_keys)
        self.assertIn("liu_ren", selected_keys)
        self.assertNotIn("bazi", selected_keys)

    def test_short_contract_timing_question_no_longer_falls_back_to_general(self):
        result = local_answer_question("现在适不适合签合同？")
        controller = result["result"]["controller"]
        selected_keys = {item["key"] for item in controller["selectedSystems"]}

        self.assertEqual(controller["questionType"], "时机/成败问题")
        self.assertTrue(any(key in selected_keys for key in {"qimen_dunjia", "liu_ren"}))
        self.assertNotIn("先告诉我这次最想问哪一类", controller["followUpPrompt"])

    def test_short_customer_meeting_question_routes_to_timing_systems(self):
        result = local_answer_question("这周要不要见客户？")
        controller = result["result"]["controller"]
        selected_keys = {item["key"] for item in controller["selectedSystems"]}

        self.assertEqual(controller["questionType"], "时机/成败问题")
        self.assertTrue(any(key in selected_keys for key in {"qimen_dunjia", "liu_ren"}))
        self.assertNotIn("先告诉我这次最想问哪一类", controller["followUpPrompt"])

    def test_short_leave_job_question_routes_to_timing_systems(self):
        result = local_answer_question("现在适合提离职吗？")
        controller = result["result"]["controller"]
        selected_keys = {item["key"] for item in controller["selectedSystems"]}

        self.assertEqual(controller["questionType"], "时机/成败问题")
        self.assertTrue(any(key in selected_keys for key in {"qimen_dunjia", "liu_ren"}))
        self.assertNotIn("先告诉我这次最想问哪一类", controller["followUpPrompt"])

    def test_human_design_shorthand_birth_question_is_computable_without_false_missing_inputs(self):
        question = "1990-05-12 14:30，北京，想看我的人类图类型和决策方式。"
        diagnostics = {item["key"]: item for item in system_question_diagnostics(question)}
        human_design = diagnostics["human_design"]

        self.assertTrue(human_design["questionMatched"])
        self.assertTrue(human_design["canReplyNow"])
        self.assertIn(human_design["replyStatus"], {"answered", "computable"})
        self.assertEqual(human_design["missingInputs"], [])
        self.assertTrue(human_design["minInputReady"])

    def test_onmyodo_trip_question_gets_specific_controller_type(self):
        result = local_answer_question("我想从阴阳道看这周出差去东京，2026-06-18 出发，住新宿，方向和禁忌有什么要注意？")
        controller = result["result"]["controller"]
        self.assertEqual(controller["questionType"], "方位/出行禁忌问题")
        selected_keys = [item["key"] for item in controller["selectedSystems"]]
        self.assertIn("onmyodo", selected_keys)
        self.assertNotIn("bazi", selected_keys)

    def test_modern_esotericism_question_gets_specific_controller_type(self):
        result = local_answer_question("我在做 manifesting、chakra、reiki 和 shadow work，想看这条实践路径的结构和风险。")
        controller = result["result"]["controller"]
        self.assertEqual(controller["questionType"], "现代神秘学实践问题")
        self.assertEqual(controller["selectedSystems"][0]["key"], "modern_esotericism")

    def test_mixed_physiognomy_question_keeps_face_reading_as_direct_verdict(self):
        result = local_answer_question("我想从面相和八字一起看我适不适合做销售：额头开阔，眼神亮，鼻梁挺，出生于1990-05-12 14:30，男，北京。")
        physiognomy = next(item for item in result["result"]["system_answers"] if item["key"] == "physiognomy")
        self.assertEqual(physiognomy["verdict_quality"], "conclusion")
        self.assertIn("销售", physiognomy["answer"])

    def test_suicide_question_is_blocked_by_safety_screen(self):
        safety = safety_screen("\u6211\u4e0d\u60f3\u6d3b\u4e86\uff0c\u4f60\u7ed9\u6211\u7b97\u7b97\u6211\u662f\u4e0d\u662f\u8be5\u81ea\u6740\uff1f")
        self.assertIsNotNone(safety)
        self.assertEqual(safety["type"], "crisis")

    def test_local_answer_blocks_high_risk_medical_override(self):
        result = local_answer_question("\u5bb6\u91cc\u4eba\u5f97\u4e86\u764c\u75c7\uff0c\u6211\u60f3\u9760\u6cd5\u4e8b\u548c\u7b26\u6c34\u66ff\u4ee3\u6cbb\u7597\uff0c\u80fd\u4e0d\u80fd\u4e0d\u7528\u7ee7\u7eed\u5316\u7597\uff1f")
        controller = result["result"]["controller"]
        self.assertEqual(controller["executionStatus"], "blocked")
        self.assertEqual(controller["issueType"], "safety")
        self.assertEqual(result["result"]["system_answers"], [])

    def test_final_answer_cautions_are_localized_for_modern_esotericism(self):
        result = local_answer_question("我在做 manifesting、chakra、reiki 和 shadow work，想看这条实践路径的结构和风险。")
        cautions = " ".join(result["result"]["final_answer"]["cautions"])
        self.assertIn("现代神秘学模块", cautions)
        self.assertNotIn("This local modern_esotericism engine", cautions)
        self.assertNotIn("medical care", cautions)


if __name__ == "__main__":
    unittest.main()
