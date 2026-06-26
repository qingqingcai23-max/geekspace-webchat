from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Any


SECTOR_RANGES = [
    ("N", 337.5, 360.0),
    ("N", 0.0, 22.5),
    ("NE", 22.5, 67.5),
    ("E", 67.5, 112.5),
    ("SE", 112.5, 157.5),
    ("S", 157.5, 202.5),
    ("SW", 202.5, 247.5),
    ("W", 247.5, 292.5),
    ("NW", 292.5, 337.5),
]

DIRECTION_ALIASES = {
    "north": "N",
    "south": "S",
    "east": "E",
    "west": "W",
    "northeast": "NE",
    "north-east": "NE",
    "northwest": "NW",
    "north-west": "NW",
    "southeast": "SE",
    "south-east": "SE",
    "southwest": "SW",
    "south-west": "SW",
    "\u5750\u5317\u671d\u5357": "S",
    "\u5750\u5357\u671d\u5317": "N",
    "\u5750\u4e1c\u671d\u897f": "W",
    "\u5750\u897f\u671d\u4e1c": "E",
    "\u5750\u4e1c\u5357\u671d\u897f\u5317": "NW",
    "\u5750\u897f\u5317\u671d\u4e1c\u5357": "SE",
    "\u5750\u4e1c\u5317\u671d\u897f\u5357": "SW",
    "\u5750\u897f\u5357\u671d\u4e1c\u5317": "NE",
    "\u5317": "N",
    "\u5357": "S",
    "\u4e1c": "E",
    "\u897f": "W",
    "\u4e1c\u5317": "NE",
    "\u4e1c\u5357": "SE",
    "\u897f\u5317": "NW",
    "\u897f\u5357": "SW",
}

KUA_PATTERNS = {
    1: {"sheng_qi": "SE", "tian_yi": "E", "yan_nian": "S", "fu_wei": "N", "jue_ming": "SW", "wu_gui": "NE", "liu_sha": "NW", "huo_hai": "W"},
    2: {"sheng_qi": "NE", "tian_yi": "W", "yan_nian": "NW", "fu_wei": "SW", "jue_ming": "N", "wu_gui": "S", "liu_sha": "E", "huo_hai": "SE"},
    3: {"sheng_qi": "S", "tian_yi": "N", "yan_nian": "SE", "fu_wei": "E", "jue_ming": "W", "wu_gui": "NW", "liu_sha": "SW", "huo_hai": "NE"},
    4: {"sheng_qi": "N", "tian_yi": "S", "yan_nian": "E", "fu_wei": "SE", "jue_ming": "SW", "wu_gui": "NE", "liu_sha": "W", "huo_hai": "NW"},
    6: {"sheng_qi": "W", "tian_yi": "NE", "yan_nian": "SW", "fu_wei": "NW", "jue_ming": "E", "wu_gui": "SE", "liu_sha": "N", "huo_hai": "S"},
    7: {"sheng_qi": "NW", "tian_yi": "SW", "yan_nian": "NE", "fu_wei": "W", "jue_ming": "S", "wu_gui": "N", "liu_sha": "SE", "huo_hai": "E"},
    8: {"sheng_qi": "SW", "tian_yi": "NW", "yan_nian": "W", "fu_wei": "NE", "jue_ming": "SE", "wu_gui": "E", "liu_sha": "S", "huo_hai": "N"},
    9: {"sheng_qi": "E", "tian_yi": "SE", "yan_nian": "N", "fu_wei": "S", "jue_ming": "NW", "wu_gui": "W", "liu_sha": "NE", "huo_hai": "SW"},
}

KUA_GROUP = {
    1: "east",
    3: "east",
    4: "east",
    9: "east",
    2: "west",
    6: "west",
    7: "west",
    8: "west",
}

EXTERNAL_ENVIRONMENT_LABELS = {
    "hospital": "医疗场所",
    "funeral": "殡葬场所",
    "school": "学校",
    "mall": "商业综合体",
    "park": "公园绿地",
    "water": "水系",
    "bridge": "桥梁",
    "elevated": "高架/快速路",
    "subway": "地铁站",
    "government": "政府/公权力设施",
}


@dataclass(frozen=True)
class FengShuiInput:
    location_or_floorplan: str
    facing_direction: str
    birth_date: date | None = None
    gender: str = ""
    build_year: int | None = None
    map_context: dict[str, Any] | None = None


def normalize_gender(value: str) -> str:
    lowered = (value or "").strip().lower()
    if lowered in {"m", "male", "\u7537", "\u7537\u6027"}:
        return "male"
    if lowered in {"f", "female", "\u5973", "\u5973\u6027"}:
        return "female"
    return ""


def parse_direction(value: str) -> tuple[str, float | None]:
    text = (value or "").strip()
    degree_match = re.search(r"(\d{1,3}(?:\.\d+)?)", text)
    if degree_match:
        degrees = float(degree_match.group(1)) % 360
        for sector, start, end in SECTOR_RANGES:
            if start <= degrees < end:
                return sector, degrees
    lowered = text.lower()
    for key, normalized in sorted(DIRECTION_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if key in lowered or key in text:
            return normalized, None
    raise ValueError("unable to parse facing direction")


def build_period(build_year: int | None) -> dict[str, Any]:
    if build_year is None:
        return {"period": None, "label": "unknown"}
    if build_year >= 2024:
        return {"period": 9, "label": "Period 9"}
    if build_year >= 2004:
        return {"period": 8, "label": "Period 8"}
    if build_year >= 1984:
        return {"period": 7, "label": "Period 7"}
    return {"period": 6, "label": "Pre-Period-7"}


def digital_root(value: int) -> int:
    result = value
    while result > 9:
        result = sum(int(char) for char in str(result))
    return result


def kua_number(birth_year: int, gender: str) -> int:
    root = digital_root(birth_year % 100)
    if gender == "male":
        result = (9 - root) if birth_year >= 2000 else (10 - root)
    elif gender == "female":
        result = (6 + root) if birth_year >= 2000 else (5 + root)
    else:
        raise ValueError("gender is required to compute kua number")

    while result > 9:
        result = sum(int(char) for char in str(result))
    if result == 5:
        return 2 if gender == "male" else 8
    if result <= 0:
        result += 9
    return result


def direction_quality(kua: int, facing_sector: str) -> tuple[str, str]:
    pattern = KUA_PATTERNS[kua]
    for quality, sector in pattern.items():
        if sector == facing_sector:
            return quality, sector
    raise ValueError("unreachable direction state")


def evaluate_external_environment(map_context: dict[str, Any] | None) -> dict[str, Any]:
    context = map_context or {}
    poi_summary = context.get("poi_summary") or {}
    poi_hits = context.get("poi_hits") or {}

    signals: list[str] = []
    cautions: list[str] = []
    supportive: list[str] = []
    score = 0

    for category, entries in poi_hits.items():
        nearest = entries[0] if isinstance(entries, list) and entries else {}
        distance = int(nearest.get("distance") or 0)
        label = EXTERNAL_ENVIRONMENT_LABELS.get(category, category)
        if category == "funeral":
            cautions.append(f"{label}距离较近时，外局气场偏阴，需重点核实视线直冲与日常感受。")
            score -= 4 if distance and distance <= 800 else 2
        elif category == "hospital":
            cautions.append(f"{label}较近时，人流与杂气偏重，宜再看主入口、窗向与夜间噪声。")
            score -= 2 if distance and distance <= 800 else 1
        elif category == "elevated":
            cautions.append(f"{label}较近时，要防噪声、压迫感与路冲感。")
            score -= 2 if distance and distance <= 600 else 1
        elif category == "bridge":
            cautions.append(f"{label}较近时，需核实是否形成直冲或反弓。")
            score -= 1
        elif category == "water":
            supportive.append(f"周边能检出水系，可进一步核实是聚水还是反弓形态。")
            score += 1
        elif category == "park":
            supportive.append(f"周边有{label}，通常有利于开阔度与缓冲带。")
            score += 1
        elif category == "school":
            signals.append(f"周边有{label}，白天活力与通行频率通常较高。")
        elif category == "mall":
            signals.append(f"周边有{label}，生活便利度较好，但也要看人流与车流压力。")
        elif category == "subway":
            signals.append(f"周边有{label}，通勤便利，但需核实噪声与出入口冲射。")
        elif category == "government":
            signals.append(f"周边有{label}，宜结合道路组织与边界感一起看。")

    verdict = "mixed"
    if score >= 2:
        verdict = "supportive"
    elif score <= -2:
        verdict = "caution"

    return {
        "verdict": verdict,
        "score": score,
        "signals": signals,
        "supportive": supportive,
        "cautions": cautions,
        "poi_summary": poi_summary,
    }


def calculate_fengshui(data: FengShuiInput) -> dict[str, Any]:
    sector, degrees = parse_direction(data.facing_direction)
    gender = normalize_gender(data.gender)
    period = build_period(data.build_year)

    used_inputs = {
        "location_or_floorplan": data.location_or_floorplan,
        "facing_direction": data.facing_direction,
        "normalized_sector": sector,
        "degrees": degrees,
        "build_year": data.build_year,
    }
    if data.map_context:
        used_inputs["map_context"] = data.map_context
    risk_flags = [
        "This local fengshui engine currently computes sector, Eight Mansions matching, and period bucket only.",
        "Without an accurate floor plan and room-level layout, the result should be treated as a directional screening layer rather than a full audit.",
    ]

    derived_factors: dict[str, Any] = {
        "facing_sector": sector,
        "period": period,
    }

    sector_label = {
        "N": "北",
        "NE": "东北",
        "E": "东",
        "SE": "东南",
        "S": "南",
        "SW": "西南",
        "W": "西",
        "NW": "西北",
    }.get(sector, sector)
    quality_label = {
        "sheng_qi": "生气位",
        "tian_yi": "天医位",
        "yan_nian": "延年位",
        "fu_wei": "伏位",
        "jue_ming": "绝命位",
        "wu_gui": "五鬼位",
        "liu_sha": "六煞位",
        "huo_hai": "祸害位",
    }

    primary_finding = f"朝向落在{sector_label}位。"
    supporting_signals = [f"房屋朝向归入{sector_label}位，这是根据当前提供的坐向直接换算出的结果。"]
    confidence = "low"

    if data.map_context:
        derived_factors["map_context"] = data.map_context
        map_title = str(data.map_context.get("title") or data.map_context.get("address") or data.location_or_floorplan).strip()
        supporting_signals.append(f"地图定位已命中：{map_title}。")
        satellite_url = str(data.map_context.get("static_map_url") or "").strip()
        if satellite_url:
            supporting_signals.append("已生成地图预览，可用于补充外局观察。")
        risk_flags.append("地图外局上下文已接入，但当前仍以地址级和朝向级筛查为主，未替代室内实勘。")
        confidence = "medium" if confidence == "low" else confidence
        external = evaluate_external_environment(data.map_context)
        derived_factors["external_environment"] = external
        for note in external.get("signals") or []:
            supporting_signals.append(note)
        for note in external.get("supportive") or []:
            supporting_signals.append(note)
        for note in external.get("cautions") or []:
            risk_flags.append(note)
        if external.get("verdict") == "supportive":
            primary_finding = f"{primary_finding.rstrip('。')} 地图外局初筛偏向可用，但仍需结合室内布局复核。"
        elif external.get("verdict") == "caution":
            primary_finding = f"{primary_finding.rstrip('。')} 地图外局初筛显示周边干扰偏多，建议谨慎复核。"

    if data.birth_date and gender:
        kua = kua_number(data.birth_date.year, gender)
        quality, _ = direction_quality(kua, sector)
        derived_factors["occupant_kua"] = kua
        derived_factors["occupant_group"] = KUA_GROUP[kua]
        derived_factors["eight_mansions"] = KUA_PATTERNS[kua]
        primary_finding = f"朝向落在{sector_label}位，命卦为{kua}，当前配向更接近{quality_label.get(quality, quality)}。"
        supporting_signals.append(f"居住者属于{KUA_GROUP[kua]}命卦组。")
        supporting_signals.append(
            f"这类命卦通常更看重{KUA_PATTERNS[kua]['sheng_qi']}、{KUA_PATTERNS[kua]['tian_yi']}、{KUA_PATTERNS[kua]['yan_nian']}和{KUA_PATTERNS[kua]['fu_wei']}这几个方位。"
        )
        confidence = "medium"
    else:
        risk_flags.append("Occupant kua matching was skipped because birth date and gender were not both available.")

    if data.build_year is None:
        risk_flags.append("Build/occupancy year was not supplied, so period-based flying-star context is only approximate.")

    return {
        "system": "fengshui",
        "question_type": "space",
        "used_inputs": used_inputs,
        "missing_inputs": [],
        "derived_factors": derived_factors,
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": period["label"],
        "confidence": confidence,
        "rules_path": [
            "direction normalization",
            "sector classification",
            "eight mansions matching",
            "period bucket",
        ],
    }
