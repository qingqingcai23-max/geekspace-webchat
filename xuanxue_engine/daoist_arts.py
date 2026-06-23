from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DaoistArtsInput:
    topic: str
    source_or_lineage: str = ""
    ritual_text: str = ""
    region: str = ""
    ethics_limit: str = ""


LINEAGE_RULES = {
    "zhengyi": {
        "aliases": ("正一", "天师", "tianshi", "zhengyi"),
        "family": "orthodox-daoist",
        "orientation": "register-and-liturgy",
    },
    "quanzhen": {
        "aliases": ("全真", "quanzhen"),
        "family": "orthodox-daoist",
        "orientation": "monastic-cultivation",
    },
    "maoshan": {
        "aliases": ("茅山", "mao shan", "maoshan", "上清"),
        "family": "orthodox-daoist",
        "orientation": "talismanic-and-shangqing",
    },
    "lvshan": {
        "aliases": ("闾山", "闾山派", "lvshan", "lüshan"),
        "family": "folk-daoist",
        "orientation": "ritual-and-exorcistic",
    },
    "lingbao": {
        "aliases": ("灵宝", "靈寶", "lingbao"),
        "family": "orthodox-daoist",
        "orientation": "liturgical-salvation",
    },
    "qingwei": {
        "aliases": ("清微", "qingwei"),
        "family": "orthodox-daoist",
        "orientation": "thunder-rite",
    },
    "shenxiao": {
        "aliases": ("神霄", "shenxiao"),
        "family": "orthodox-daoist",
        "orientation": "thunder-rite",
    },
}


PRACTICE_RULES = {
    "protective-talismans": ("符", "符箓", "符咒", "画符", "护身符", "镇宅", "talisman"),
    "liturgical-ritual": ("科仪", "斋醮", "醮", "章表", "表文", "启坛", "请圣", "步罡", "踏斗"),
    "internal-alchemy": ("内丹", "周天", "存思", "守一", "吐纳", "静坐", "导引", "炼己"),
    "thunder-rite": ("雷法", "五雷", "掌心雷", "雷诀"),
    "cleansing-exorcistic": ("净宅", "驱邪", "禳解", "送煞", "退煞", "安宅", "cleanse"),
    "devotional-recitation": ("诵经", "持咒", "念诵", "礼斗", "朝真", "recitation"),
}


RITUAL_COMPONENTS = {
    "altar": ("法坛", "坛", "altar", "神案"),
    "incense": ("香", "焚香", "incense"),
    "talisman": ("符", "符箓", "talisman"),
    "petition": ("表", "章表", "表文", "疏文", "petition"),
    "scripture": ("经", "诵经", "科书", "scripture", "recitation"),
    "pace-pattern": ("步罡", "踏斗", "禹步"),
    "fasting-purification": ("斋", "沐浴", "净身", "fasting", "purification"),
    "offerings": ("供", "供品", "offerings"),
    "seal-or-hand-sign": ("诀", "手诀", "印", "seal"),
}


HIGH_RISK_MARKERS = (
    "血祭",
    "附体",
    "上身",
    "拘魂",
    "诅咒",
    "害人",
    "斗法",
    "符水治病",
    "吞符",
    "服符",
    "治病",
    "开天眼",
)

NEGATED_HIGH_RISK_PATTERNS = (
    "不是让我害人",
    "不是害人",
    "不想害人",
    "不会害人",
    "不是让我诅咒",
    "不是诅咒",
    "不做诅咒",
)


def normalize_text(*parts: str) -> str:
    return " ".join(part.strip().lower() for part in parts if part and part.strip())


def find_alias_hits(text: str, aliases: tuple[str, ...]) -> list[str]:
    return [alias for alias in aliases if alias.lower() in text]


def detect_lineage(text: str) -> dict[str, Any]:
    best = {
        "canonical": "unspecified",
        "family": "unspecified",
        "orientation": "unspecified",
        "hits": [],
    }
    for canonical, rule in LINEAGE_RULES.items():
        hits = find_alias_hits(text, rule["aliases"])
        if len(hits) > len(best["hits"]):
            best = {
                "canonical": canonical,
                "family": rule["family"],
                "orientation": rule["orientation"],
                "hits": hits,
            }
    return best


def detect_practice_family(text: str) -> dict[str, Any]:
    best_name = "symbolic-study"
    best_hits: list[str] = []
    for family, aliases in PRACTICE_RULES.items():
        hits = find_alias_hits(text, aliases)
        if len(hits) > len(best_hits):
            best_name = family
            best_hits = hits
    return {"name": best_name, "hits": best_hits}


def detect_components(text: str) -> list[str]:
    components = []
    for name, aliases in RITUAL_COMPONENTS.items():
        if any(alias.lower() in text for alias in aliases):
            components.append(name)
    return components


def detect_purpose(text: str) -> str:
    if any(token in text for token in ["护身", "镇宅", "protect", "protection"]):
        return "protection"
    if any(token in text for token in ["净宅", "cleanse", "驱邪", "退煞"]):
        return "cleansing"
    if any(token in text for token in ["修行", "内丹", "静坐", "守一"]):
        return "cultivation"
    if any(token in text for token in ["祈福", "求财", "求子", "求平安", "petition"]):
        return "petition"
    if any(token in text for token in ["诅咒", "害人", "斗法", "拘魂"]):
        return "coercive"
    return "general"


def safety_tier(practice_family: str, taboo_hits: list[str], lineage_family: str) -> str:
    if taboo_hits:
        return "cultural-only"
    if practice_family in {"thunder-rite", "liturgical-ritual", "cleansing-exorcistic", "protective-talismans"}:
        return "guided-only" if lineage_family != "unspecified" else "lineage-dependent"
    if practice_family in {"internal-alchemy", "devotional-recitation"}:
        return "low-risk-contemplative"
    return "lineage-dependent"


def calculate_daoist_arts(data: DaoistArtsInput) -> dict[str, Any]:
    topic = (data.topic or "").strip()
    if not topic:
        raise ValueError("topic is required for daoist_arts")

    source = (data.source_or_lineage or "").strip()
    ritual_text = (data.ritual_text or "").strip()
    region = (data.region or "").strip()
    ethics_limit = (data.ethics_limit or "").strip()
    combined = normalize_text(topic, source, ritual_text, region, ethics_limit)

    lineage = detect_lineage(combined)
    practice = detect_practice_family(combined)
    components = detect_components(combined)
    purpose = detect_purpose(combined)
    taboo_hits = [marker for marker in HIGH_RISK_MARKERS if marker.lower() in combined]
    taboo_hits = [
        marker
        for marker in taboo_hits
        if not any(marker in pattern and pattern in combined for pattern in NEGATED_HIGH_RISK_PATTERNS)
    ]
    tier = safety_tier(practice["name"], taboo_hits, lineage["family"])

    supporting_signals = [
        f"Practice family resolves to {practice['name']} with markers: {', '.join(practice['hits'][:4]) or 'none explicit'}.",
        f"Lineage frame resolves to {lineage['canonical']} / {lineage['family']} with orientation {lineage['orientation']}.",
        f"Detected ritual components: {', '.join(components) or 'none explicit'}.",
    ]
    if region:
        supporting_signals.append(f"Regional context supplied: {region}.")
    if ethics_limit:
        supporting_signals.append(f"Ethical boundary supplied: {ethics_limit}.")

    risk_flags = [
        "This local daoist_arts engine structures lineage, ritual components, and taboo boundaries; it does not authorize ordination-gated or dangerous procedures.",
        "Religious practice, exorcistic work, healing claims, and coercive ritual should not be operationalized from dossier rules alone.",
        "Where lineage is unclear, output should be treated as cultural mapping rather than as a reliable manual.",
    ]
    if taboo_hits:
        risk_flags.append(
            f"High-risk markers were detected: {', '.join(taboo_hits)}. Output is restricted to cultural and safety framing."
        )
    if lineage["family"] == "unspecified":
        risk_flags.append("No explicit lineage marker was supplied, so the reading remains cross-lineage and lower-confidence.")

    if tier == "cultural-only":
        primary_finding = (
            f"Daoist-arts classification resolves to {practice['name']}, but the request crosses into high-risk or coercive territory. "
            "The local engine will only preserve cultural structure and prohibitions, not procedural instruction."
        )
        confidence = "low"
    elif tier == "guided-only":
        primary_finding = (
            f"Daoist-arts classification resolves to {practice['name']} under a {lineage['canonical']} frame. "
            "This is lineage-governed ritual architecture and should be treated as supervised practice rather than solo execution."
        )
        confidence = "medium"
    elif tier == "low-risk-contemplative":
        primary_finding = (
            f"Daoist-arts classification resolves to {practice['name']}. "
            "The safest local reading is contemplative: symbolism, recitation frame, and cultivation context rather than forceful operation."
        )
        confidence = "medium"
    else:
        primary_finding = (
            f"Daoist-arts classification resolves to {practice['name']} with purpose {purpose}. "
            "The local engine can map structure, but lineage detail is still needed before treating it as concrete practice."
        )
        confidence = "low" if lineage["family"] == "unspecified" else "medium"

    derived_factors = {
        "practice_family": practice["name"],
        "practice_markers": practice["hits"],
        "purpose": purpose,
        "lineage": lineage,
        "ritual_components": components,
        "safety_tier": tier,
        "taboo_hits": taboo_hits,
        "region": region,
    }

    return {
        "system": "daoist_arts",
        "question_type": "ritual",
        "used_inputs": {
            "topic": topic,
            "source_or_lineage": source,
            "ritual_text": ritual_text,
            "region": region,
            "ethics_limit": ethics_limit,
        },
        "missing_inputs": [],
        "derived_factors": derived_factors,
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "This reading is about ritual structure and boundaries, not a timed divination window.",
        "confidence": confidence,
        "rules_path": [
            "lineage detection",
            "practice-family classification",
            "ritual-component extraction",
            "taboo and safety screening",
            "boundary-aware conclusion",
        ],
    }
