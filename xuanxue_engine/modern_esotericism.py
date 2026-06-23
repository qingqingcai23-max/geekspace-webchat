from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ModernEsotericismInput:
    topic: str
    source: str = ""
    practice_description: str = ""
    cultural_context: str = ""
    risk_level: str = ""


SOURCE_RULES = {
    "new-age": ("new age", "高维", "高维度", "高频", "高频率", "扬升", "揚升", "lightworker", "starseed", "星种子", "星際種子"),
    "occult-revival": ("thelema", "golden dawn", "occult revival", "hermetic order", "秘传", "祕傳", "神秘学复兴", "神祕學復興"),
    "chaos-magic": ("chaos magic", "chaos magick", "sigil", "混沌魔法", "混沌魔術"),
    "manifestation-commerce": ("manifestation", "law of attraction", "abundance", "显化", "顯化", "吸引力法则", "吸引力法則"),
    "energy-healing": ("reiki", "chakra", "aura", "energy healing", "灵气", "靈氣", "脉轮", "脈輪"),
    "channeling": ("channeling", "channelled", "阿卡西", "akashic", "guides", "导师讯息", "導師訊息", "灵讯", "靈訊"),
    "witchcraft-practice": ("moon ritual", "spell jar", "crystal grid", "witchcraft", "女巫", "月仪式", "月儀式", "蜡烛魔法", "蠟燭魔法"),
}


CONCEPT_RULES = {
    "identity-framework": ("shadow work", "inner child", "人格", "创伤", "創傷", "self concept", "identity"),
    "ritual-practice": ("ritual", "altar", "spell", "sigil", "moon water", "仪式", "儀式", "祭坛", "祭壇"),
    "energy-map": ("chakra", "aura", "frequency", "vibration", "气场", "氣場", "频率", "頻率"),
    "divinatory-message": ("oracle", "message", "synchronicity", "牌卡", "同步性", "宇宙讯息", "宇宙訊息"),
    "prosperity-technique": ("manifestation", "abundance", "money bowl", "prosperity", "显化", "招财", "招財"),
    "healing-claim": ("healing", "heal trauma", "治愈", "治癒", "cure", "疗愈", "療癒"),
}


DOMAIN_SPLIT_RULES = {
    "psychological": ("shadow work", "inner child", "journaling", "self concept", "创伤", "人格", "reflection", "therapy"),
    "religious": ("prayer", "devotion", "deity", "goddess", "spirit guide", "祈祷", "神祇", "奉献", "奉獻"),
    "commercial": ("course", "paid circle", "mentor", "membership", "高价", "高價", "收费", "收費", "变现", "變現"),
    "wellness": ("breathwork", "meditation", "somatic", "wellness", "冥想", "呼吸", "身心"),
}


HIGH_RISK_MARKERS = (
    "replace therapy",
    "stop medication",
    "all disease is energetic",
    "join only my group",
    "isolate from family",
    "pay to ascend",
    "停药",
    "停藥",
    "断亲",
    "断親",
    "包治百病",
    "替代治疗",
    "替代治療",
    "必须跟我",
    "必须离开家人",
)


LOW_RISK_MARKERS = ("journaling", "reflection", "meditation", "symbolic", "艺术", "藝術", "写作", "寫作", "记录", "記錄")

SOURCE_FAMILY_LABELS = {
    "new-age": "新时代灵性流",
    "occult-revival": "近代秘传复兴流",
    "chaos-magic": "混沌魔法流",
    "manifestation-commerce": "显化变现流",
    "energy-healing": "能量疗愈流",
    "channeling": "通灵讯息流",
    "witchcraft-practice": "现代巫术实践流",
    "unspecified-modern-mix": "未明现代混合流",
}

CONCEPT_FAMILY_LABELS = {
    "identity-framework": "自我理解框架",
    "ritual-practice": "仪式实践框架",
    "energy-map": "能量地图框架",
    "divinatory-message": "讯息占读框架",
    "prosperity-technique": "丰盛显化技巧",
    "healing-claim": "疗愈宣称框架",
    "general-symbolic": "一般象征框架",
}

USABLE_SCOPE_LABELS = {
    "cultural framing and risk warning only": "文化理解与风险提醒",
    "reflective and journaling use": "反思记录、日记整理这类低风险用法",
    "symbolic and aesthetic use": "象征体验与审美化使用",
    "motivational framing only": "作为动机框架使用",
    "self-observation with boundaries": "带边界的自我观察",
    "symbolic personal use": "个人象征化使用",
}


def normalize_text(*parts: str) -> str:
    return " ".join(part.strip().lower() for part in parts if part and part.strip())


def hits_for(text: str, markers: tuple[str, ...]) -> list[str]:
    return [marker for marker in markers if marker.lower() in text]


def detect_best_category(text: str, rules: dict[str, tuple[str, ...]], default: str) -> dict[str, Any]:
    best_name = default
    best_hits: list[str] = []
    for name, aliases in rules.items():
        found = hits_for(text, aliases)
        if len(found) > len(best_hits):
            best_name = name
            best_hits = found
    return {"name": best_name, "hits": best_hits}


def detect_domain_weights(text: str) -> dict[str, int]:
    weights = {name: 0 for name in DOMAIN_SPLIT_RULES}
    for name, aliases in DOMAIN_SPLIT_RULES.items():
        weights[name] = len(hits_for(text, aliases))
    return weights


def dominant_domains(weights: dict[str, int]) -> list[str]:
    ranked = sorted(weights.items(), key=lambda item: (item[1], item[0]), reverse=True)
    return [name for name, score in ranked if score > 0][:3]


def detect_risk_tier(text: str, domain_weights: dict[str, int]) -> tuple[str, list[str]]:
    high_hits = hits_for(text, HIGH_RISK_MARKERS)
    if high_hits:
        return "high", high_hits
    if domain_weights["commercial"] and ("healing" in text or "疗愈" in text or "治愈" in text or "治癒" in text):
        return "high", ["commercialized-healing-mix"]
    if domain_weights["commercial"] or "channeling" in text or "阿卡西" in text:
        return "medium", []
    if hits_for(text, LOW_RISK_MARKERS):
        return "low", []
    return "medium", []


def usable_scope(concept: str, tier: str, domains: list[str]) -> str:
    if tier == "high":
        return "cultural framing and risk warning only"
    if concept == "identity-framework":
        return "reflective and journaling use"
    if concept == "ritual-practice":
        return "symbolic and aesthetic use"
    if concept == "prosperity-technique":
        return "motivational framing only"
    if "psychological" in domains:
        return "self-observation with boundaries"
    return "symbolic personal use"


def calculate_modern_esotericism(data: ModernEsotericismInput) -> dict[str, Any]:
    topic = (data.topic or "").strip()
    if not topic:
        raise ValueError("topic is required for modern_esotericism")

    source = (data.source or "").strip()
    practice_description = (data.practice_description or "").strip()
    cultural_context = (data.cultural_context or "").strip()
    risk_level = (data.risk_level or "").strip().lower()
    combined = normalize_text(topic, source, practice_description, cultural_context, risk_level)

    source_family = detect_best_category(normalize_text(source) or combined, SOURCE_RULES, "unspecified-modern-mix")
    concept_family = detect_best_category(combined, CONCEPT_RULES, "general-symbolic")
    domain_weights = detect_domain_weights(combined)
    domains = dominant_domains(domain_weights)
    tier, high_hits = detect_risk_tier(combined, domain_weights)
    if risk_level in {"high", "medium", "low"}:
        tier = risk_level
    scope = usable_scope(concept_family["name"], tier, domains)
    source_label = SOURCE_FAMILY_LABELS.get(source_family["name"], source_family["name"])
    concept_label = CONCEPT_FAMILY_LABELS.get(concept_family["name"], concept_family["name"])
    scope_label = USABLE_SCOPE_LABELS.get(scope, scope)

    supporting_signals = [
        f"来源流派落在{source_label}，命中的线索有：{', '.join(source_family['hits']) or '未明'}。",
        f"概念框架落在{concept_label}，命中的线索有：{', '.join(concept_family['hits']) or '未明'}。",
        f"领域权重分布为：心理 {domain_weights['psychological']}、宗教 {domain_weights['religious']}、商业 {domain_weights['commercial']}、身心 {domain_weights['wellness']}。",
        f"当前更稳的使用范围是：{scope_label}。",
    ]
    if cultural_context:
        supporting_signals.append(f"给出的文化语境是：{cultural_context}。")

    risk_flags = [
        "This local modern_esotericism engine distinguishes symbolic practice, psychological framing, commercial packaging, and high-risk overreach instead of treating them as one thing.",
        "It should not replace therapy, medical care, legal advice, or financial judgement.",
        "Contemporary esoteric scenes often blend spirituality, wellness, psychology, and monetization; the engine surfaces that mixture explicitly.",
    ]
    if high_hits:
        risk_flags.append(f"High-risk markers detected: {', '.join(high_hits)}.")
    if source_family["name"] == "manifestation-commerce":
        risk_flags.append("Manifestation discourse is especially prone to overpromising control over complex real-world conditions.")
    if source_family["name"] == "channeling":
        risk_flags.append("Channeling-style material is treated as unverifiable message content, not as authoritative external fact.")

    if tier == "high":
        primary_finding = (
            f"现代神秘学主轴落在{concept_label}，来源更接近{source_label}，"
            "但当前输入已经碰到依赖、控制或伪治疗风险，所以这里只保留边界提醒。"
        )
        confidence = "high"
    elif tier == "medium":
        primary_finding = (
            f"现代神秘学主轴落在{concept_label}，来源更接近{source_label}。"
            "当前更稳的理解方式，是把它放在象征实践或反思整理里，并把权威与现实判断边界分开。"
        )
        confidence = "medium"
    else:
        primary_finding = (
            f"现代神秘学主轴落在{concept_label}，来源更接近{source_label}。"
            "当它被放在反思、象征或创作语境里时，当前风险相对可控。"
        )
        confidence = "medium"

    return {
        "system": "modern_esotericism",
        "question_type": "contemporary-esoteric",
        "used_inputs": {
            "topic": topic,
            "source": source,
            "practice_description": practice_description,
            "cultural_context": cultural_context,
            "risk_level": risk_level,
        },
        "missing_inputs": [],
        "derived_factors": {
            "source_family": source_family,
            "concept_family": concept_family,
            "domain_weights": domain_weights,
            "dominant_domains": domains,
            "risk_tier": tier,
            "usable_scope": scope,
            "high_risk_markers": high_hits,
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "This reading is about framing and boundaries, not divinatory timing.",
        "confidence": confidence,
        "rules_path": [
            "source-family detection",
            "concept classification",
            "psychological-religious-commercial split",
            "risk-tier screening",
            "usable-scope conclusion",
        ],
    }
