from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AlchemyHermeticismInput:
    topic: str
    text_or_image: str = ""
    stage_model: str = ""
    tradition: str = ""
    practical_context: str = ""


STAGE_RULES = {
    "nigredo": {
        "aliases": ("nigredo", "blackening", "putrefaction", "腐败", "腐敗", "黑化", "黑相", "乌鸦", "烏鴉", "crow", "raven"),
        "element": "earth-water",
        "planet": "Saturn",
        "keywords": ("decomposition", "shadow material", "breaking fixed form"),
        "next_stage": "albedo",
    },
    "albedo": {
        "aliases": ("albedo", "whitening", "purification", "白化", "净化", "淨化", "swan", "moon wash", "白天鹅", "白天鵝"),
        "element": "water-air",
        "planet": "Moon",
        "keywords": ("clarification", "washing", "separating subtle from coarse"),
        "next_stage": "citrinitas",
    },
    "citrinitas": {
        "aliases": ("citrinitas", "yellowing", "illumination", "黄化", "黃化", "dawn", "solar awakening", "黎明"),
        "element": "air-fire",
        "planet": "Mercury-Sun",
        "keywords": ("emergent consciousness", "discernment", "integration of insight"),
        "next_stage": "rubedo",
    },
    "rubedo": {
        "aliases": ("rubedo", "reddening", "perfection", "conjunction", "red king", "赤化", "红化", "紅化", "贤者之石", "賢者之石", "philosopher's stone"),
        "element": "fire-earth",
        "planet": "Sun",
        "keywords": ("embodiment", "stabilized union", "completion"),
        "next_stage": "rubedo",
    },
}


OPERATION_RULES = {
    "calcination": ("calcination", "burn", "ash", "fire", "煅烧", "煅燒", "焚", "灰"),
    "dissolution": ("dissolution", "dissolve", "bath", "water", "溶解", "洗", "水浴"),
    "separation": ("separation", "separate", "筛", "筛分", "分离", "分離"),
    "conjunction": ("conjunction", "marriage", "king and queen", "合一", "结合", "結合"),
    "fermentation": ("fermentation", "ferment", "wine", "spirit rise", "发酵", "發酵"),
    "distillation": ("distillation", "distill", "vapor", "蒸馏", "蒸餾"),
    "coagulation": ("coagulation", "salt", "stone", "凝结", "凝結", "结晶", "結晶"),
}


SYMBOL_RULES = {
    "sulfur": {
        "aliases": ("sulfur", "sulphur", "硫", "soul-fire"),
        "axis": "active principle",
        "element": "fire",
        "planet": "Sun-Mars",
    },
    "mercury": {
        "aliases": ("mercury", "mercurius", "quicksilver", "汞", "水银", "水銀"),
        "axis": "volatile principle",
        "element": "water-air",
        "planet": "Mercury-Moon",
    },
    "salt": {
        "aliases": ("salt", "sal", "盐", "鹽"),
        "axis": "fixed body",
        "element": "earth",
        "planet": "Earth-Saturn",
    },
    "sun": {
        "aliases": ("sun", "sol", "太阳", "太陽"),
        "axis": "conscious gold",
        "element": "fire",
        "planet": "Sun",
    },
    "moon": {
        "aliases": ("moon", "luna", "月亮", "太阴", "太陰"),
        "axis": "receptive silver",
        "element": "water",
        "planet": "Moon",
    },
    "green_lion": {
        "aliases": ("green lion", "绿狮", "綠獅"),
        "axis": "solvent force",
        "element": "acid-water",
        "planet": "Venus-Mercury",
    },
    "ouroboros": {
        "aliases": ("ouroboros", "uroboros", "衔尾蛇", "銜尾蛇"),
        "axis": "cyclic self-transformation",
        "element": "all-elements",
        "planet": "Saturn-Mercury",
    },
    "phoenix": {
        "aliases": ("phoenix", "凤凰", "鳳凰"),
        "axis": "renewal after destruction",
        "element": "fire-air",
        "planet": "Sun",
    },
    "vessel": {
        "aliases": ("vessel", "athanor", "retort", "容器", "炉", "爐"),
        "axis": "container and process discipline",
        "element": "earth-fire",
        "planet": "Saturn",
    },
}


TRADITION_RULES = {
    "hermetic": ("hermetic", "hermes", "赫尔墨斯", "赫耳墨斯", "emerald tablet", "翠玉录", "翠玉錄"),
    "paracelsian": ("paracelsus", "paracelsian", "帕拉塞尔苏斯", "三原质", "三原質"),
    "jungian": ("jung", "jungian", "荣格", "榮格", "individuation", "个体化", "個體化"),
    "laboratory": ("laboratory", "lab", "坩埚", "坩堝", "蒸馏", "蒸餾"),
    "rosicrucian": ("rosicrucian", "rosy cross", "玫瑰十字"),
}


MATERIAL_MARKERS = ("metal", "gold", "silver", "substance", "matter", "金属", "金屬", "物质", "物質", "实验", "實驗")
SPIRITUAL_MARKERS = ("soul", "inner", "spirit", "awakening", "shadow", "self", "灵魂", "靈魂", "内在", "內在", "意识", "意識")


def normalize_text(*parts: str) -> str:
    return " ".join(part.strip().lower() for part in parts if part and part.strip())


def hits_for(text: str, aliases: tuple[str, ...]) -> list[str]:
    return [alias for alias in aliases if alias.lower() in text]


def detect_stage(text: str, stage_model: str) -> tuple[str, list[str], str]:
    explicit_text = normalize_text(stage_model)
    if explicit_text:
        for stage, rule in STAGE_RULES.items():
            stage_hits = hits_for(explicit_text, rule["aliases"])
            if stage_hits:
                return stage, stage_hits, "explicit-stage-model"
    best_stage = "nigredo"
    best_hits: list[str] = []
    for stage, rule in STAGE_RULES.items():
        stage_hits = hits_for(text, rule["aliases"])
        if len(stage_hits) > len(best_hits):
            best_stage = stage
            best_hits = stage_hits
    mode = "symbol-inference" if best_hits else "default-sequence-anchor"
    return best_stage, best_hits, mode


def detect_operations(text: str) -> list[str]:
    operations = []
    for name, aliases in OPERATION_RULES.items():
        if any(alias.lower() in text for alias in aliases):
            operations.append(name)
    return operations


def detect_symbols(text: str) -> list[dict[str, Any]]:
    results = []
    for name, rule in SYMBOL_RULES.items():
        found = hits_for(text, rule["aliases"])
        if found:
            results.append(
                {
                    "name": name,
                    "hits": found,
                    "axis": rule["axis"],
                    "element": rule["element"],
                    "planet": rule["planet"],
                }
            )
    return results


def detect_tradition(text: str) -> dict[str, Any]:
    best_name = "unspecified"
    best_hits: list[str] = []
    for name, aliases in TRADITION_RULES.items():
        found = hits_for(text, aliases)
        if len(found) > len(best_hits):
            best_name = name
            best_hits = found
    return {"name": best_name, "hits": best_hits}


def detect_layer_balance(text: str) -> dict[str, Any]:
    material_hits = [marker for marker in MATERIAL_MARKERS if marker.lower() in text]
    spiritual_hits = [marker for marker in SPIRITUAL_MARKERS if marker.lower() in text]
    if len(material_hits) > len(spiritual_hits):
        emphasis = "material"
    elif len(spiritual_hits) > len(material_hits):
        emphasis = "spiritual"
    else:
        emphasis = "balanced"
    return {
        "emphasis": emphasis,
        "material_hits": material_hits,
        "spiritual_hits": spiritual_hits,
    }


def transformation_path(stage: str, operations: list[str], symbols: list[dict[str, Any]]) -> list[str]:
    path = [stage]
    next_stage = STAGE_RULES[stage]["next_stage"]
    if next_stage != stage:
        path.append(next_stage)
    if operations:
        path.extend(operation for operation in operations[:2] if operation not in path)
    for symbol in symbols[:2]:
        if symbol["name"] not in path:
            path.append(symbol["name"])
    return path


def translate_marker_hit(value: str) -> str:
    marker = str(value or "").strip()
    stage_map = {
        "nigredo": "黑化",
        "albedo": "白化",
        "citrinitas": "黄化",
        "rubedo": "赤化",
        "blackening": "黑化",
        "whitening": "白化",
        "yellowing": "黄化",
        "reddening": "赤化",
        "putrefaction": "腐败",
        "purification": "净化",
        "crow": "乌鸦",
        "raven": "渡鸦",
    }
    return stage_map.get(marker.lower(), marker)


def calculate_alchemy_and_hermeticism(data: AlchemyHermeticismInput) -> dict[str, Any]:
    topic = (data.topic or "").strip()
    if not topic:
        raise ValueError("topic is required for alchemy_and_hermeticism")

    text_or_image = (data.text_or_image or "").strip()
    stage_model = (data.stage_model or "").strip()
    tradition_text = (data.tradition or "").strip()
    practical_context = (data.practical_context or "").strip()
    combined = normalize_text(topic, text_or_image, stage_model, tradition_text, practical_context)

    stage, stage_hits, stage_mode = detect_stage(combined, stage_model)
    operations = detect_operations(combined)
    symbols = detect_symbols(combined)
    tradition = detect_tradition(combined)
    balance = detect_layer_balance(combined)
    path = transformation_path(stage, operations, symbols)

    stage_name_map = {
        "nigredo": "黑化阶段",
        "albedo": "白化阶段",
        "rubedo": "赤化阶段",
        "citrinitas": "黄化阶段",
    }
    element_map = {
        "earth": "土",
        "water": "水",
        "fire": "火",
        "air": "风",
        "earth-water": "土水",
        "water-air": "水风",
        "air-fire": "风火",
        "fire-earth": "火土",
        "all-elements": "全元素循环",
        "acid-water": "酸性水相",
    }
    planet_map = {
        "saturn": "土星",
        "moon": "月亮",
        "sun": "太阳",
        "mercury": "水星",
        "mercury-sun": "水星与太阳",
        "sun-mars": "太阳与火星",
        "mercury-moon": "水星与月亮",
        "earth-saturn": "土性与土星",
        "saturn-mercury": "土星与水星",
        "venus-mercury": "金星与水星",
    }
    keyword_map = {
        "decomposition": "分解",
        "shadow material": "阴影材料",
        "breaking fixed form": "打破旧定形",
        "clarification": "澄清",
        "washing": "洗炼",
        "discernment": "辨明",
        "integration": "整合",
        "separating subtle from coarse": "把精微与粗重分开",
        "emergent consciousness": "新意识浮现",
        "integration of insight": "洞见整合",
        "embodiment": "落地承载",
        "stabilized union": "稳定结合",
        "completion": "完成定形",
        "vital union": "活性结合",
        "coherence": "一致化",
        "illumination": "显明",
        "subtle gold": "内在金性",
        "stabilized insight": "稳定洞见",
    }
    symbol_name_map = {"ouroboros": "衔尾蛇", "mercury": "汞性原则", "salt": "盐性原则", "sulfur": "硫性原则"}
    tradition_name_map = {
        "jungian-hermetic": "荣格化赫尔墨斯框架",
        "hermetic": "赫尔墨斯框架",
        "paracelsian": "帕拉塞尔苏斯框架",
        "general-esoteric": "一般神秘学框架",
    }

    stage_rule = STAGE_RULES[stage]
    supporting_signals = [
        f"转化阶段落在{stage_name_map.get(stage, stage)}，命中的阶段线索有：{', '.join(translate_marker_hit(item) for item in stage_hits) or '未明'}。",
        f"这一阶段更对应{element_map.get(stage_rule['element'], stage_rule['element'])}性和{planet_map.get(stage_rule['planet'], stage_rule['planet'])}象征。",
        f"当前识别到的操作关键词有：{', '.join(keyword_map.get(item, item) for item in operations) or '未明'}。",
        f"当前符号组包括：{', '.join(symbol_name_map.get(symbol['name'], symbol['name']) for symbol in symbols) or '未明'}。",
        f"传统框架更接近{tradition_name_map.get(tradition['name'], tradition['name'])}，命中线索有：{', '.join(tradition['hits']) or '未明'}。",
    ]

    risk_flags = [
        "This local alchemy_and_hermeticism engine treats alchemical language as symbolic, philosophical, and process-oriented unless the user explicitly frames it as historical laboratory material.",
        "It should not be used as chemistry, toxicology, medical, or ingestion guidance.",
        "Different streams of alchemy, Hermeticism, Paracelsian medicine, and Jungian reinterpretation do not collapse into one rulebook; the chosen frame is exposed in the output.",
    ]
    if not text_or_image:
        risk_flags.append("No image or primary text was supplied, so symbol extraction is limited to the topical wording.")
    if balance["emphasis"] == "material":
        risk_flags.append("The prompt leans material/laboratory, but the engine still outputs symbolic structure rather than practical lab instruction.")

    primary_finding = (
        f"炼金术主轴落在{stage_name_map.get(stage, stage)}，当前活跃工作更接近"
        f"{'、'.join(keyword_map.get(item, item) for item in stage_rule['keywords'])}。"
        f"下一步会转向{stage_name_map.get(stage_rule['next_stage'], stage_rule['next_stage'])}。"
    )
    if balance["emphasis"] == "spiritual":
        primary_finding += " 这次问题更偏内在转化，因此会把心性变化放在字面物质处理之前。"
    elif balance["emphasis"] == "material":
        primary_finding += " 这次问题更偏材料语境，因此系统会明确区分象征过程和字面物质操作。"

    confidence = "high" if stage_hits and (operations or symbols) else "medium" if stage_hits or operations or symbols else "low"

    return {
        "system": "alchemy_and_hermeticism",
        "question_type": "transformation",
        "used_inputs": {
            "topic": topic,
            "text_or_image": text_or_image,
            "stage_model": stage_model,
            "tradition": tradition_text,
            "practical_context": practical_context,
        },
        "missing_inputs": [],
        "derived_factors": {
            "stage": {
                "name": stage,
                "markers": stage_hits,
                "selection_mode": stage_mode,
                "element": stage_rule["element"],
                "planet": stage_rule["planet"],
                "keywords": list(stage_rule["keywords"]),
                "next_stage": stage_rule["next_stage"],
            },
            "operations": operations,
            "symbols": symbols,
            "tradition": tradition,
            "layer_balance": balance,
            "transformation_path": path,
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "This reading is process-oriented and phase-based rather than tied to a specific clock time.",
        "confidence": confidence,
        "rules_path": [
            "stage detection",
            "operation extraction",
            "symbol correspondence mapping",
            "material-spiritual layer distinction",
            "transformation path synthesis",
        ],
    }
