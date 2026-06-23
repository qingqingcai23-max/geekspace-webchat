from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class KabbalahInput:
    topic: str
    sephirah_or_path: str = ""
    source: str = ""
    intention: str = ""


SEPHIROTH: dict[int, dict[str, Any]] = {
    1: {
        "name": "Keter",
        "hebrew": "כתר",
        "title": "Crown",
        "pillar": "Middle",
        "triad": "Supernal",
        "correspondence": "Primum Mobile",
        "keywords": ("unity", "pure potential", "origin"),
        "aliases": ("1", "keter", "kether", "crown", "כתר", "王冠", "王冕"),
    },
    2: {
        "name": "Chokmah",
        "hebrew": "חכמה",
        "title": "Wisdom",
        "pillar": "Right",
        "triad": "Supernal",
        "correspondence": "Zodiac",
        "keywords": ("impulse", "creative force", "expansion"),
        "aliases": ("2", "chokmah", "hokmah", "wisdom", "חכמה", "智慧"),
    },
    3: {
        "name": "Binah",
        "hebrew": "בינה",
        "title": "Understanding",
        "pillar": "Left",
        "triad": "Supernal",
        "correspondence": "Saturn",
        "keywords": ("structure", "containment", "discipline"),
        "aliases": ("3", "binah", "understanding", "בינה", "理解"),
    },
    4: {
        "name": "Chesed",
        "hebrew": "חסד",
        "title": "Mercy",
        "pillar": "Right",
        "triad": "Ethical",
        "correspondence": "Jupiter",
        "keywords": ("benevolence", "scale", "trust"),
        "aliases": ("4", "chesed", "gedulah", "mercy", "חסד", "慈悲", "仁慈"),
    },
    5: {
        "name": "Gevurah",
        "hebrew": "גבורה",
        "title": "Severity",
        "pillar": "Left",
        "triad": "Ethical",
        "correspondence": "Mars",
        "keywords": ("judgement", "boundaries", "force"),
        "aliases": ("5", "gevurah", "geburah", "severity", "גבורה", "严厉", "力量", "审判"),
    },
    6: {
        "name": "Tiphereth",
        "hebrew": "תפארת",
        "title": "Beauty",
        "pillar": "Middle",
        "triad": "Ethical",
        "correspondence": "Sun",
        "keywords": ("harmony", "integration", "center"),
        "aliases": ("6", "tiphereth", "tiferet", "beauty", "תפארת", "美丽", "美"),
    },
    7: {
        "name": "Netzach",
        "hebrew": "נצח",
        "title": "Victory",
        "pillar": "Right",
        "triad": "Astral",
        "correspondence": "Venus",
        "keywords": ("desire", "attraction", "continuity"),
        "aliases": ("7", "netzach", "victory", "נצח", "胜利"),
    },
    8: {
        "name": "Hod",
        "hebrew": "הוד",
        "title": "Splendour",
        "pillar": "Left",
        "triad": "Astral",
        "correspondence": "Mercury",
        "keywords": ("analysis", "language", "systems"),
        "aliases": ("8", "hod", "splendour", "splendor", "הוד", "荣耀", "辉煌"),
    },
    9: {
        "name": "Yesod",
        "hebrew": "יסוד",
        "title": "Foundation",
        "pillar": "Middle",
        "triad": "Astral",
        "correspondence": "Moon",
        "keywords": ("substrate", "linkage", "imagination"),
        "aliases": ("9", "yesod", "foundation", "יסוד", "基础"),
    },
    10: {
        "name": "Malkuth",
        "hebrew": "מלכות",
        "title": "Kingdom",
        "pillar": "Middle",
        "triad": "Material",
        "correspondence": "Earth",
        "keywords": ("embodiment", "execution", "manifestation"),
        "aliases": ("10", "malkuth", "malkut", "kingdom", "מלכות", "王国", "王國"),
    },
}


PATHS: dict[int, dict[str, Any]] = {
    11: {"letter": "Aleph", "hebrew": "א", "tarot": "The Fool", "element": "Air", "between": (1, 2), "aliases": ("11", "aleph", "א", "fool", "愚者")},
    12: {"letter": "Beth", "hebrew": "ב", "tarot": "The Magician", "element": "Mercury", "between": (1, 3), "aliases": ("12", "beth", "ב", "magician", "魔术师", "魔術師")},
    13: {"letter": "Gimel", "hebrew": "ג", "tarot": "The High Priestess", "element": "Moon", "between": (1, 6), "aliases": ("13", "gimel", "ג", "high priestess", "女祭司")},
    14: {"letter": "Daleth", "hebrew": "ד", "tarot": "The Empress", "element": "Venus", "between": (2, 3), "aliases": ("14", "daleth", "ד", "empress", "女皇")},
    15: {"letter": "Heh", "hebrew": "ה", "tarot": "The Emperor", "element": "Aries", "between": (2, 6), "aliases": ("15", "heh", "ה", "emperor", "皇帝")},
    16: {"letter": "Vav", "hebrew": "ו", "tarot": "The Hierophant", "element": "Taurus", "between": (2, 4), "aliases": ("16", "vav", "ו", "hierophant", "教皇")},
    17: {"letter": "Zain", "hebrew": "ז", "tarot": "The Lovers", "element": "Gemini", "between": (3, 6), "aliases": ("17", "zain", "ז", "lovers", "恋人", "戀人")},
    18: {"letter": "Cheth", "hebrew": "ח", "tarot": "The Chariot", "element": "Cancer", "between": (3, 5), "aliases": ("18", "cheth", "heth", "ח", "chariot", "战车", "戰車")},
    19: {"letter": "Teth", "hebrew": "ט", "tarot": "Strength", "element": "Leo", "between": (4, 5), "aliases": ("19", "teth", "ט", "strength", "力量")},
    20: {"letter": "Yod", "hebrew": "י", "tarot": "The Hermit", "element": "Virgo", "between": (4, 6), "aliases": ("20", "yod", "י", "hermit", "隐者", "隱者")},
    21: {"letter": "Kaph", "hebrew": "כ", "tarot": "Wheel of Fortune", "element": "Jupiter", "between": (4, 7), "aliases": ("21", "kaph", "כ", "wheel of fortune", "命运之轮", "命運之輪")},
    22: {"letter": "Lamed", "hebrew": "ל", "tarot": "Justice", "element": "Libra", "between": (5, 6), "aliases": ("22", "lamed", "ל", "justice", "正义", "正義")},
    23: {"letter": "Mem", "hebrew": "מ", "tarot": "The Hanged Man", "element": "Water", "between": (5, 8), "aliases": ("23", "mem", "מ", "hanged man", "倒吊人")},
    24: {"letter": "Nun", "hebrew": "נ", "tarot": "Death", "element": "Scorpio", "between": (6, 7), "aliases": ("24", "nun", "נ", "death", "死神")},
    25: {"letter": "Samekh", "hebrew": "ס", "tarot": "Temperance", "element": "Sagittarius", "between": (6, 9), "aliases": ("25", "samekh", "ס", "temperance", "节制", "節制")},
    26: {"letter": "Ayin", "hebrew": "ע", "tarot": "The Devil", "element": "Capricorn", "between": (6, 8), "aliases": ("26", "ayin", "ע", "devil", "恶魔", "惡魔")},
    27: {"letter": "Peh", "hebrew": "פ", "tarot": "The Tower", "element": "Mars", "between": (7, 8), "aliases": ("27", "peh", "פה", "פ", "tower", "高塔")},
    28: {"letter": "Tzaddi", "hebrew": "צ", "tarot": "The Star", "element": "Aquarius", "between": (7, 9), "aliases": ("28", "tzaddi", "zaddi", "צ", "star", "星星")},
    29: {"letter": "Qoph", "hebrew": "ק", "tarot": "The Moon", "element": "Pisces", "between": (7, 10), "aliases": ("29", "qoph", "ק", "moon", "月亮")},
    30: {"letter": "Resh", "hebrew": "ר", "tarot": "The Sun", "element": "Sun", "between": (8, 9), "aliases": ("30", "resh", "ר", "sun", "太阳", "太陽")},
    31: {"letter": "Shin", "hebrew": "ש", "tarot": "Judgement", "element": "Fire", "between": (8, 10), "aliases": ("31", "shin", "ש", "judgement", "judgment", "审判", "審判")},
    32: {"letter": "Tav", "hebrew": "ת", "tarot": "The World", "element": "Saturn", "between": (9, 10), "aliases": ("32", "tav", "ת", "world", "世界")},
}


HEBREW_VALUES = {
    "א": 1,
    "ב": 2,
    "ג": 3,
    "ד": 4,
    "ה": 5,
    "ו": 6,
    "ז": 7,
    "ח": 8,
    "ט": 9,
    "י": 10,
    "כ": 20,
    "ך": 20,
    "ל": 30,
    "מ": 40,
    "ם": 40,
    "נ": 50,
    "ן": 50,
    "ס": 60,
    "ע": 70,
    "פ": 80,
    "ף": 80,
    "צ": 90,
    "ץ": 90,
    "ק": 100,
    "ר": 200,
    "ש": 300,
    "ת": 400,
}


DOMAIN_KEYWORDS = {
    "career": ("事业", "工作", "职业", "career", "job", "business", "direction", "发展", "推进"),
    "relationship": ("感情", "关系", "伴侣", "婚姻", "love", "relationship", "partner"),
    "spiritual": ("灵性", "修行", "启示", "spiritual", "soul", "god", "divine"),
    "knowledge": ("学习", "知识", "沟通", "写作", "language", "study", "analysis", "communication"),
    "material": ("财富", "落地", "现实", "金钱", "money", "material", "manifest"),
    "conflict": ("冲突", "审判", "决断", "切断", "conflict", "fight", "boundary"),
}


DOMAIN_TO_SEPHIROTH = {
    "career": (8, 10, 4, 6),
    "relationship": (7, 6, 9),
    "spiritual": (1, 3, 6),
    "knowledge": (8, 3, 2),
    "material": (10, 9, 4),
    "conflict": (5, 3, 8),
}


def reduce_value(value: int) -> int:
    while value > 9:
        value = sum(int(char) for char in str(value))
    return value


def normalize_key(value: str) -> str:
    return re.sub(r"[\s_\-]+", " ", (value or "").strip().lower())


def alias_in_text(text: str, alias: str) -> bool:
    normalized_alias = normalize_key(alias)
    if not normalized_alias:
        return False
    if re.fullmatch(r"[a-z0-9 ]+", normalized_alias):
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])", text))
    return normalized_alias in text


def detect_topic_domains(topic: str) -> list[str]:
    lowered = normalize_key(topic)
    domains = [name for name, keywords in DOMAIN_KEYWORDS.items() if any(keyword.lower() in lowered for keyword in keywords)]
    return domains or ["general"]


def infer_source_stream(source: str) -> str:
    lowered = normalize_key(source)
    if any(token in lowered for token in ("hermetic", "golden dawn", "qabalah", "crowley", "waite")):
        return "hermetic-qabalah"
    if any(token in lowered for token in ("jewish", "hebrew", "zohar", "sefer yetzirah", "lurianic")):
        return "jewish-kabbalah"
    if any(token in lowered for token in ("christian", "pico", "reuchlin")):
        return "christian-cabala"
    return "unspecified"


def find_sephirah(value: str) -> dict[str, Any] | None:
    key = normalize_key(value)
    if not key:
        return None
    for index, record in SEPHIROTH.items():
        aliases = [normalize_key(alias) for alias in record["aliases"]]
        if key in aliases:
            return {"index": index, **record}
    for index, record in SEPHIROTH.items():
        aliases = [normalize_key(alias) for alias in record["aliases"]]
        if any(alias_in_text(key, alias) for alias in aliases):
            return {"index": index, **record}
    return None


def find_path(value: str) -> dict[str, Any] | None:
    key = normalize_key(value)
    if not key:
        return None
    for index, record in PATHS.items():
        aliases = [normalize_key(alias) for alias in record["aliases"]]
        if key in aliases:
            return {"index": index, **record}
    for index, record in PATHS.items():
        aliases = [normalize_key(alias) for alias in record["aliases"]]
        if any(alias_in_text(key, alias) for alias in aliases):
            return {"index": index, **record}
    return None


def find_all_sephiroth(value: str) -> list[dict[str, Any]]:
    key = normalize_key(value)
    if not key:
        return []
    matches: list[dict[str, Any]] = []
    for index, record in SEPHIROTH.items():
        aliases = [normalize_key(alias) for alias in record["aliases"]]
        if any(alias_in_text(key, alias) for alias in aliases):
            matches.append({"index": index, **record})
    return matches


def infer_target_from_topic(topic: str) -> tuple[str, dict[str, Any], str]:
    explicit = find_path(topic)
    if explicit:
        return "path", explicit, "inferred-from-topic"
    explicit = find_sephirah(topic)
    if explicit:
        return "sephirah", explicit, "inferred-from-topic"

    domains = detect_topic_domains(topic)
    for domain in domains:
        candidates = DOMAIN_TO_SEPHIROTH.get(domain)
        if candidates:
            index = candidates[0]
            return "sephirah", {"index": index, **SEPHIROTH[index]}, "domain-anchor"
    index = 10
    return "sephirah", {"index": index, **SEPHIROTH[index]}, "default-anchor"


def tree_connections() -> dict[int, list[int]]:
    connections = {index: set() for index in SEPHIROTH}
    for path in PATHS.values():
        left, right = path["between"]
        connections[left].add(right)
        connections[right].add(left)
    return {index: sorted(values) for index, values in connections.items()}


TREE_CONNECTIONS = tree_connections()


def hebrew_gematria(text: str) -> dict[str, Any] | None:
    letters = [char for char in text if char in HEBREW_VALUES]
    if not letters:
        return None
    breakdown = [{"letter": char, "value": HEBREW_VALUES[char]} for char in letters]
    total = sum(item["value"] for item in breakdown)
    return {
        "text": "".join(letters),
        "breakdown": breakdown,
        "total": total,
        "reduced": reduce_value(total),
    }


def alignment_score(domains: list[str], target_type: str, target: dict[str, Any]) -> int:
    if target_type == "path":
        return 70 if domains != ["general"] else 58
    matches = set()
    for domain in domains:
        if target["index"] in DOMAIN_TO_SEPHIROTH.get(domain, ()):
            matches.add(domain)
    if matches:
        return 86 - (list(DOMAIN_TO_SEPHIROTH[sorted(matches)[0]]).index(target["index"]) * 8)
    if domains == ["general"]:
        return 62
    return 48


def domain_readout(domains: list[str], target_type: str, target: dict[str, Any]) -> str:
    if target_type == "path":
        left, right = target["between"]
        return (
            f"This path links {SEPHIROTH[left]['name']} and {SEPHIROTH[right]['name']}, "
            f"so the reading focuses on movement between two states rather than one fixed sphere."
        )
    domain = domains[0]
    if domain == "career":
        return f"For career questions, {target['name']} points toward progress through {', '.join(target['keywords'])}."
    if domain == "relationship":
        return f"For relationship questions, {target['name']} points toward {', '.join(target['keywords'])} as the live axis."
    if domain == "spiritual":
        return f"For spiritual questions, {target['name']} emphasizes {', '.join(target['keywords'])}."
    if domain == "knowledge":
        return f"For study or communication questions, {target['name']} works through {', '.join(target['keywords'])}."
    if domain == "material":
        return f"For material questions, {target['name']} translates through {', '.join(target['keywords'])}."
    if domain == "conflict":
        return f"For conflict questions, {target['name']} highlights {', '.join(target['keywords'])}."
    return f"{target['name']} is being used as the current symbolic anchor."


def translate_triad(value: str) -> str:
    return {
        "supernal": "超上层",
        "ethical": "伦理层",
        "astral": "星光层",
        "material": "物质层",
    }.get(str(value or "").strip().lower(), str(value or "").strip())


def translate_source_stream(value: str) -> str:
    return {
        "hermetic-qabalah": "赫尔墨斯卡巴拉",
        "jewish-kabbalah": "犹太卡巴拉",
        "christian-cabala": "基督教卡巴拉",
        "mixed": "混合来源",
        "general-esoteric": "一般神秘学来源",
        "unspecified": "未明来源",
    }.get(str(value or "").strip().lower(), str(value or "").strip())


def calculate_kabbalah(data: KabbalahInput) -> dict[str, Any]:
    topic = (data.topic or "").strip()
    source = (data.source or "").strip()
    target_text = (data.sephirah_or_path or "").strip()
    if not topic:
        raise ValueError("topic is required")

    target_type = ""
    target: dict[str, Any] | None = None
    selection_mode = "explicit"

    if target_text:
        target = find_path(target_text)
        if target:
            target_type = "path"
        else:
            target = find_sephirah(target_text)
            if target:
                target_type = "sephirah"

    if not target:
        target_type, target, selection_mode = infer_target_from_topic(f"{topic} {source}".strip())

    assert target is not None

    domains = detect_topic_domains(topic)
    source_stream = infer_source_stream(source)
    gematria = hebrew_gematria(topic) or hebrew_gematria(source)
    score = alignment_score(domains, target_type, target)
    explicit_nodes = find_all_sephiroth(" ".join(part for part in [target_text, topic] if part).strip())
    supporting_signals: list[str] = []
    risk_flags = [
        "This local kabbalah engine mixes structural Tree-of-Life correspondences with explicit source-stream labeling.",
        "Jewish Kabbalah, Christian Cabala, and Hermetic Qabalah do not use one identical rulebook; the source stream is exposed rather than hidden.",
        "Without a cited textual lineage, this engine should be treated as a structural reading layer rather than as a final doctrinal verdict.",
    ]

    if target_type == "sephirah":
        connections = [SEPHIROTH[index]["name"] for index in TREE_CONNECTIONS[target["index"]]]
        derived_factors = {
            "target_type": "sephirah",
            "tree_index": target["index"],
            "canonical_name": target["name"],
            "hebrew_name": target["hebrew"],
            "title": target["title"],
            "pillar": target["pillar"],
            "triad": target["triad"],
            "correspondence": target["correspondence"],
            "keywords": list(target["keywords"]),
            "adjacent_nodes": connections,
            "topic_domains": domains,
            "alignment_score": score,
            "source_stream": source_stream,
            "selection_mode": selection_mode,
        }
        secondary_nodes = [
            {
                "tree_index": item["index"],
                "canonical_name": item["name"],
                "title": item["title"],
                "pillar": item["pillar"],
                "keywords": list(item["keywords"]),
            }
            for item in explicit_nodes
            if item["index"] != target["index"]
        ]
        if secondary_nodes:
            derived_factors["secondary_nodes"] = secondary_nodes[:3]
        primary_finding = (
            f"Kabbalah focus resolves to {target['name']} ({target['index']}), the {target['pillar'].lower()}-pillar "
            f"sephirah of {target['title'].lower()} and {target['correspondence']}. {domain_readout(domains, target_type, target)}"
        )
        supporting_signals.append(
            f"{target['name']}位于{translate_triad(target['triad'])}，并连接到{', '.join(connections)}。"
        )
        if secondary_nodes:
            supporting_signals.append(
                f"题面里还显式提到了：{', '.join(item['canonical_name'] for item in secondary_nodes[:3])}。"
            )
    else:
        left, right = target["between"]
        derived_factors = {
            "target_type": "path",
            "tree_index": target["index"],
            "canonical_name": target["letter"],
            "hebrew_name": target["hebrew"],
            "tarot_major": target["tarot"],
            "element_or_sign": target["element"],
            "between": [SEPHIROTH[left]["name"], SEPHIROTH[right]["name"]],
            "topic_domains": domains,
            "alignment_score": score,
            "source_stream": source_stream,
            "selection_mode": selection_mode,
        }
        primary_finding = (
            f"Kabbalah focus resolves to Path {target['index']} ({target['letter']} / {target['tarot']}), "
            f"which runs between {SEPHIROTH[left]['name']} and {SEPHIROTH[right]['name']}. {domain_readout(domains, target_type, target)}"
        )
        supporting_signals.append(
            f"路径{target['index']}使用希伯来字母{target['hebrew']}，对应{target['element']}象征。"
        )

    supporting_signals.append(f"识别到的问题主题有：{', '.join(domains)}。")
    supporting_signals.append(f"来源流派归为：{translate_source_stream(source_stream)}。")
    if gematria:
        derived_factors["gematria"] = gematria
        supporting_signals.append(
            f"输入文本里检测到希伯来字母数值：{gematria['text']} 总值为 {gematria['total']}，约简为 {gematria['reduced']}。"
        )
    else:
        risk_flags.append("No Hebrew text was supplied, so this reading cannot add a direct gematria layer.")

    confidence = "high" if target_text and score >= 70 else "medium" if score >= 58 else "low"

    return {
        "system": "kabbalah",
        "question_type": "tree_of_life",
        "used_inputs": {
            "topic": topic,
            "sephirah_or_path": target_text,
            "source": source,
            "intention": data.intention,
        },
        "missing_inputs": [],
        "derived_factors": derived_factors,
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "This reading is structural and symbolic rather than time-bound.",
        "confidence": confidence,
        "rules_path": [
            "target normalization",
            "tree-of-life target selection",
            "source-stream classification",
            "topic-domain mapping",
            "gematria extraction when Hebrew text is present",
        ],
    }
