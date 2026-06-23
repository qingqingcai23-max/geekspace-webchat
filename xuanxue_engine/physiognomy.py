from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


@dataclass(frozen=True)
class PhysiognomyInput:
    image_or_description: str
    observation_context: str = ""
    age: int | None = None
    gender: str = ""
    time_state: str = ""
    question_type: str = ""


FEATURE_RULES = {
    "forehead": {
        "region": "upper",
        "positive": ("broad", "wide", "high", "open", "bright", "smooth", "full", "额头开阔", "额头高", "额头饱满", "天庭饱满", "明亮"),
        "negative": ("narrow", "low", "scar", "dark", "sunken", "wrinkled", "额头窄", "额头低", "疤", "暗沉", "塌"),
        "domains": {"foresight": 2, "stability": 1},
    },
    "brows": {
        "region": "upper",
        "positive": ("long", "clear", "even", "orderly", "眉清", "眉齐", "眉长", "整齐"),
        "negative": ("messy", "broken", "short", "sparse", "眉乱", "断眉", "眉短", "眉稀"),
        "domains": {"discipline": 2, "social": 1},
    },
    "eyes": {
        "region": "middle",
        "positive": ("bright", "clear", "steady", "focused", "kind", "眼神清", "眼睛有神", "明亮", "稳定"),
        "negative": ("dull", "red", "scattered", "shifty", "tired", "眼神散", "无神", "发红", "疲惫"),
        "domains": {"vitality": 2, "social": 1, "emotional": 1},
    },
    "nose": {
        "region": "middle",
        "positive": ("straight", "full", "defined", "firm", "nose bridge", "鼻梁直", "鼻梁挺", "鼻头饱满", "山根稳"),
        "negative": ("crooked", "collapsed", "thin", "dark", "鼻梁歪", "塌鼻", "鼻薄", "鼻色暗"),
        "domains": {"material": 2, "execution": 1},
    },
    "mouth": {
        "region": "lower",
        "positive": ("full", "closed", "balanced", "red", "嘴唇饱满", "口角平", "唇色润"),
        "negative": ("thin", "downturned", "dry", "tight", "嘴薄", "口角下垂", "干裂"),
        "domains": {"social": 1, "emotional": 2},
    },
    "jaw_chin": {
        "region": "lower",
        "positive": ("firm", "rounded", "full chin", "defined jaw", "下巴饱满", "地阁方圆", "下颌稳"),
        "negative": ("sharp", "receding", "weak chin", "thin jaw", "下巴尖削", "后缩", "下颌薄"),
        "domains": {"will": 2, "stability": 1},
    },
    "complexion": {
        "region": "middle",
        "positive": ("even complexion", "rosy", "bright complexion", "气色好", "面色匀", "红润", "光泽"),
        "negative": ("ashy", "yellow", "blue", "swollen", "dull complexion", "气色差", "发灰", "发黄", "浮肿"),
        "domains": {"vitality": 2, "stability": 1},
    },
    "hands": {
        "region": "lower",
        "positive": ("palm full", "clear palm", "掌色润", "掌纹清", "手掌厚"),
        "negative": ("palm dry", "messy lines", "掌色枯", "掌纹乱", "手掌薄"),
        "domains": {"execution": 1, "material": 1, "will": 1},
    },
}


CONTEXT_MODIFIERS = {
    "photo_only": ("自拍", "滤镜", "修图", "photo", "portrait", "照片"),
    "makeup": ("化妆", "浓妆", "makeup"),
    "low_light": ("夜里", "低光", "逆光", "熬夜后", "深夜", "low light"),
    "fatigue": ("刚哭过", "生病", "疲惫", "宿醉", "熬夜", "after crying", "ill", "tired"),
}


AXIS_LABELS = {
    "vitality": "vitality and immediate energy",
    "social": "social readability and relational warmth",
    "emotional": "emotional steadiness and expressiveness",
    "material": "material anchoring and practical resources",
    "execution": "execution and follow-through",
    "discipline": "discipline and self-ordering",
    "foresight": "foresight and long-range framing",
    "stability": "stability and load-bearing capacity",
    "will": "willpower and persistence",
}


def normalize_gender(value: str) -> str:
    lowered = (value or "").strip().lower()
    if lowered in {"m", "male", "男", "男性"}:
        return "male"
    if lowered in {"f", "female", "女", "女性"}:
        return "female"
    return ""


def normalized_text(*parts: str) -> str:
    return " ".join(part.strip().lower() for part in parts if part and part.strip())


def count_hits(text: str, markers: tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for marker in markers:
        if marker.lower() in text:
            hits.append(marker)
    return hits


def age_phase(age: int | None) -> str:
    if age is None:
        return "unspecified"
    if age < 30:
        return "upper-court emphasis"
    if age < 50:
        return "middle-court emphasis"
    return "lower-court emphasis"


def infer_question_type(text: str) -> str:
    if any(token in text for token in ["面相", "face", "额头", "眼", "鼻", "嘴", "下巴"]):
        return "face-reading"
    if any(token in text for token in ["手相", "掌纹", "palm", "hand"]):
        return "hand-reading"
    if any(token in text for token in ["骨相", "骨架"]):
        return "bone-reading"
    return "observational"


def axis_summary(axis_scores: dict[str, int]) -> tuple[str, int]:
    if not axis_scores:
        return "observational ambiguity", 0
    axis, score = max(axis_scores.items(), key=lambda item: (abs(item[1]), item[1]))
    return axis, score


def calculate_physiognomy(data: PhysiognomyInput) -> dict[str, Any]:
    description = (data.image_or_description or "").strip()
    if len(description) < 6:
        raise ValueError("image_or_description is required for physiognomy")

    context = (data.observation_context or "").strip()
    combined = normalized_text(description, context, data.time_state)
    if not combined:
        raise ValueError("at least one observation text field is required")

    feature_results: dict[str, Any] = {}
    court_scores = {"upper": 0, "middle": 0, "lower": 0}
    axis_scores = {key: 0 for key in AXIS_LABELS}
    supporting_signals: list[str] = []
    risk_flags = [
        "This local physiognomy engine reads text descriptions of observed features; it does not inspect pixels or infer hidden traits from an unseen face.",
        "Physiognomy is handled here as a non-deterministic symbolic observation system, not as a medical, legal, hiring, or investment decision tool.",
        "Any strong claim should be cross-checked across multiple contexts instead of being treated as fixed destiny.",
    ]

    recognized_feature_count = 0
    for feature_name, rule in FEATURE_RULES.items():
        positive_hits = count_hits(combined, rule["positive"])
        negative_hits = count_hits(combined, rule["negative"])
        if not positive_hits and not negative_hits:
            continue

        recognized_feature_count += 1
        score = len(positive_hits) - len(negative_hits)
        leaning = "mixed"
        if score > 0:
            leaning = "positive"
        elif score < 0:
            leaning = "negative"

        feature_results[feature_name] = {
            "region": rule["region"],
            "positive_hits": positive_hits,
            "negative_hits": negative_hits,
            "score": score,
            "leaning": leaning,
        }
        court_scores[rule["region"]] += score

        for axis, weight in rule["domains"].items():
            if score > 0:
                axis_scores[axis] += weight
            elif score < 0:
                axis_scores[axis] -= weight

        if positive_hits:
            supporting_signals.append(f"{feature_name} markers lean positive: {', '.join(positive_hits[:3])}.")
        if negative_hits:
            supporting_signals.append(f"{feature_name} markers lean negative: {', '.join(negative_hits[:3])}.")

    modifiers = []
    for modifier, markers in CONTEXT_MODIFIERS.items():
        if any(marker.lower() in combined for marker in markers):
            modifiers.append(modifier)
    if modifiers:
        risk_flags.append(
            f"Observation context includes modifiers that can distort appearance: {', '.join(modifiers)}."
        )

    normalized_gender = normalize_gender(data.gender)
    phase = age_phase(data.age)
    dominant_axis, dominant_score = axis_summary(axis_scores)
    dominant_axis_label = AXIS_LABELS.get(dominant_axis, dominant_axis)

    if recognized_feature_count == 0:
        primary_finding = (
            "当前提供的相貌描述还不够具体，暂时不足以形成稳定的相术判断；"
            "系统只能先提示这轮输入偏抽象。"
        )
        confidence = "low"
        risk_flags.append("No stable feature cluster was extracted from the description.")
    else:
        polarity = "supports" if dominant_score >= 0 else "complicates"
        primary_finding = (
            f"Observation cluster centers on {dominant_axis_label}. "
            f"The extracted features currently {polarity} that axis under the local physiognomy rule set."
        )
        if recognized_feature_count >= 4 and not modifiers:
            confidence = "high"
        elif recognized_feature_count >= 2:
            confidence = "medium"
        else:
            confidence = "low"

    if data.age is None:
        risk_flags.append("Age phase is unspecified, so three-court emphasis remains generic.")
    if not context:
        risk_flags.append("Observation context was not supplied, so dynamic cues and scene bias remain under-specified.")

    derived_factors = {
        "observation_mode": "text-description",
        "question_type": data.question_type or infer_question_type(combined),
        "recognized_feature_count": recognized_feature_count,
        "features": feature_results,
        "three_courts": {
            "upper": {"score": court_scores["upper"]},
            "middle": {"score": court_scores["middle"]},
            "lower": {"score": court_scores["lower"]},
        },
        "axis_scores": axis_scores,
        "dominant_axis": {
            "name": dominant_axis,
            "label": dominant_axis_label,
            "score": dominant_score,
        },
        "age_phase": phase,
        "context_modifiers": modifiers,
    }

    return {
        "system": "physiognomy",
        "question_type": "observational",
        "used_inputs": {
            "image_or_description": description,
            "observation_context": context,
            "age": data.age,
            "gender": normalized_gender,
            "time_state": data.time_state,
            "question_type": data.question_type,
        },
        "missing_inputs": [],
        "derived_factors": derived_factors,
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals[:8],
        "risk_flags": risk_flags,
        "time_window": "This reading is a snapshot of presentation and should be rechecked across different scenes and states.",
        "confidence": confidence,
        "rules_path": [
            "observation normalization",
            "feature token extraction",
            "three-court scoring",
            "five-feature domain weighting",
            "context-bias adjustment",
        ],
    }
