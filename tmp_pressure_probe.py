from __future__ import annotations

import json
from typing import Any

from server import local_answer_question


TEST_QUESTIONS = [
    {
        "id": "physio_missing",
        "question": "我想从面相看一下我适不适合做销售。",
    },
    {
        "id": "physio_with_features",
        "question": "我想从面相和八字一起看我适不适合做销售：额头开阔，眼神亮，鼻梁挺，下巴稳，日间正面照片观察，出生于1990-05-12 14:30，男，北京。",
    },
    {
        "id": "human_design_rank",
        "question": "我不想听套话，你就从人类图的角度告诉我，我现在更适合在组织里冲，还是先做个人输出品牌，1990-05-12 14:30，北京。",
    },
    {
        "id": "yijing_numbers",
        "question": "我想从易经象数看我这次换工作要不要动，数字 6 1 4。",
    },
    {
        "id": "yijing_missing_seed",
        "question": "我想从易经看这次合作该不该继续推进。",
    },
    {
        "id": "tarot_missing_cards",
        "question": "我想用塔罗看这段关系还有没有必要继续。",
    },
    {
        "id": "tarot_with_cards",
        "question": "塔罗看感情：恋人正位、宝剑二逆位、圣杯六正位，我和他还有没有必要继续谈？",
    },
    {
        "id": "kabbalah_multi_node",
        "question": "我想从卡巴拉看 Tiphereth 和 Yesod 对事业与关系的影响。",
    },
    {
        "id": "daoist_priority",
        "question": "我是正一道法脉背景，最近住的地方总觉得压着，净宅、护身、化煞、安神这几类我现在先做哪类，哪些别乱碰？",
    },
    {
        "id": "alchemy_stage",
        "question": "我想从炼金术角度看我现在这段状态：像在黑化和分离之间，老想拆掉旧结构，又怕自己越拆越空。",
    },
    {
        "id": "modern_esoteric_risk",
        "question": "我最近一边做显化，一边跟着某个脉轮疗愈课做练习，还打算拿它去做变现内容。你从现代神秘学这套看，风险最大在哪？",
    },
    {
        "id": "fengshui_missing_inputs",
        "question": "我想看现在住的房子会不会越住越压抑，从风水看该不该尽快搬。",
    },
    {
        "id": "onmyodo_trip",
        "question": "我后天要去西南方向见客户，阴阳道这套看这个方向和时点合不合适？",
    },
    {
        "id": "name_generation",
        "question": "孩子姓沈，男孩，别给我生僻字，也别太娘，最好有点书卷气，先给我方向就行。",
    },
]


def shorten(value: Any, limit: int = 220) -> str:
    text = str(value or "").strip().replace("\n", " ")
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def compact_answer(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": item.get("key"),
        "system": item.get("system"),
        "verdict_quality": item.get("verdict_quality"),
        "missing_inputs": item.get("missing_inputs"),
        "used_local_calculation": item.get("used_local_calculation"),
        "verdict": shorten(item.get("verdict")),
        "answer": shorten(item.get("answer")),
    }


def main() -> None:
    results = []
    for case in TEST_QUESTIONS:
        answer = local_answer_question(case["question"])
        result = answer["result"]
        controller = result["controller"]
        system_answers = result["system_answers"]
        results.append(
            {
                "id": case["id"],
                "question": case["question"],
                "executionStatus": controller.get("executionStatus"),
                "questionType": controller.get("questionType"),
                "selectedSystems": [item.get("key") for item in controller.get("selectedSystems") or []],
                "missingInputs": controller.get("missingInputs"),
                "followUpPrompt": controller.get("followUpPrompt"),
                "synthesis": shorten((result.get("final_answer") or {}).get("synthesis"), 320),
                "systemAnswers": [compact_answer(item) for item in system_answers[:4]],
            }
        )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
