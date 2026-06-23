from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from kerykeion import AstrologicalSubject

from .astro_common import (
    ELEMENT_ORDER,
    QUALITY_ORDER,
    count_by_key,
    dominant_keys,
    extract_houses,
    extract_points,
    normalize_aspects,
    occupied_houses,
    ordinal,
    resolve_birth_location,
    sign_name_from_index,
    whole_sign_house,
)


SEVEN_GOVERNOR_KEYS = [
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
]

NODE_AND_APOGEE_KEYS = [
    "true_north_lunar_node",
    "true_south_lunar_node",
    "true_lilith",
    "mean_lilith",
]

POINT_NAME_OVERRIDES = {
    "true_north_lunar_node": "Jidu",
    "true_south_lunar_node": "Luohou",
    "true_lilith": "Yuebo",
    "mean_lilith": "Yuebo",
}

QUESTION_HOUSES = {
    "life_house": 1,
    "wealth_house": 2,
    "travel_house": 9,
    "relationship_house": 7,
    "career_house": 10,
}


@dataclass(frozen=True)
class QizhengSiyuInput:
    birth_datetime: datetime
    birth_location: str
    birth_lat: float | None = None
    birth_lng: float | None = None
    tz_str: str = ""


def whole_sign_opposite(point: dict[str, Any], ascendant_sign_index: int) -> dict[str, Any]:
    opposite_degree = (float(point["absolute_degree"]) + 180.0) % 360.0
    sign_index = int(opposite_degree // 30) % 12
    degree_in_sign = round(opposite_degree % 30, 2)
    house_number = whole_sign_house(sign_index, ascendant_sign_index)
    return {
        "name": "Ziqi",
        "sign": sign_name_from_index(sign_index),
        "sign_full": sign_name_from_index(sign_index),
        "sign_index": sign_index,
        "degree_in_sign": degree_in_sign,
        "absolute_degree": round(opposite_degree, 2),
        "house": None,
        "house_number": house_number,
        "retrograde": False,
        "element": "",
        "quality": "",
        "speed": None,
    }


def point_summary(point: dict[str, Any]) -> str:
    return f"{point['name']} in {point['sign_full']} house {point['house_number']}"


def question_house_map(governors: dict[str, dict[str, Any]]) -> dict[str, list[str]]:
    occupied = occupied_houses(governors)
    result: dict[str, list[str]] = {}
    for label, number in QUESTION_HOUSES.items():
        result[label] = list(occupied.get(str(number), []))
    return result


def calculate_qizheng_siyu(data: QizhengSiyuInput) -> dict[str, Any]:
    resolved = resolve_birth_location(
        data.birth_location,
        lat=data.birth_lat,
        lng=data.birth_lng,
        tz_str=data.tz_str,
    )
    subject = AstrologicalSubject(
        name="Native",
        year=data.birth_datetime.year,
        month=data.birth_datetime.month,
        day=data.birth_datetime.day,
        hour=data.birth_datetime.hour,
        minute=data.birth_datetime.minute,
        lng=resolved.lng,
        lat=resolved.lat,
        tz_str=resolved.tz_str,
        online=False,
        zodiac_type="Tropical",
    )
    chart_dump = subject.model_dump()
    seven_governors = extract_points(chart_dump, SEVEN_GOVERNOR_KEYS)
    four_remainder_core = extract_points(chart_dump, NODE_AND_APOGEE_KEYS, POINT_NAME_OVERRIDES)
    houses = extract_houses(chart_dump)

    ascendant_sign_index = int(houses["1"]["sign_index"])
    yuebo = four_remainder_core.get("Yuebo")
    if not yuebo:
        raise ValueError("unable to derive Yuebo proxy from the local ephemeris")
    ziqi = whole_sign_opposite(yuebo, ascendant_sign_index)
    four_remainders = {
        "Luohou": four_remainder_core["Luohou"],
        "Jidu": four_remainder_core["Jidu"],
        "Yuebo": yuebo,
        "Ziqi": ziqi,
    }

    major_points = {**seven_governors, **four_remainders}
    aspects = normalize_aspects(subject, set(seven_governors), limit=8)
    governor_elements = count_by_key(seven_governors, "element", ELEMENT_ORDER)
    governor_qualities = count_by_key(seven_governors, "quality", QUALITY_ORDER)
    dominant_elements = dominant_keys(governor_elements)
    dominant_qualities = dominant_keys(governor_qualities)
    angular_governors = [
        name
        for name, point in seven_governors.items()
        if int(point["house_number"] or 0) in {1, 4, 7, 10}
    ]

    question_mapping = question_house_map(seven_governors)
    governor_name_map = {
        "Sun": "太阳",
        "Moon": "月亮",
        "Mercury": "水星",
        "Venus": "金星",
        "Mars": "火星",
        "Jupiter": "木星",
        "Saturn": "土星",
    }
    quality_map = {
        "Cardinal": "开创",
        "Fixed": "固定",
        "Mutable": "变动",
    }
    supporting_signals = [
        f"七政重点星曜落在{', '.join(governor_name_map.get(item, item) for item in angular_governors) if angular_governors else '非角宫分布'}。",
        f"罗喉落在第{four_remainders['Luohou']['house_number']}宫，计都落在第{four_remainders['Jidu']['house_number']}宫。",
        f"月孛代理点落在第{yuebo['house_number']}宫，紫气代理点落在第{ziqi['house_number']}宫。",
    ]
    if dominant_elements:
        supporting_signals.append(f"七政五行侧重在{', '.join(dominant_elements)}。")
    if dominant_qualities:
        supporting_signals.append(f"七政性质侧重在{', '.join(quality_map.get(item, item) for item in dominant_qualities)}。")
    if aspects:
        strongest = aspects[0]
        supporting_signals.append(
            f"最紧的主星相位是{strongest['between']} {strongest['aspect']}，容许度约为{strongest['orbit']}°。"
        )

    primary_finding = (
        f"Seven governors center on {', '.join(angular_governors[:3]) or 'a non-angular pattern'}; "
        f"Luohou/Jidu fall across houses {four_remainders['Luohou']['house_number']} and {four_remainders['Jidu']['house_number']}, "
        f"while Yuebo/Ziqi activate houses {yuebo['house_number']} and {ziqi['house_number']}."
    )

    risk_flags = [
        "This local qizheng_siyu engine computes the seven governors from astronomical positions and uses node/apogee proxies for the four remainders.",
        "Luohou and Jidu naming conventions differ across lineages; this build maps Luohou to the true south node and Jidu to the true north node following one common Chinese convention.",
        "Yuebo is modeled from the lunar apogee proxy (true Lilith), and Ziqi is modeled as its opposite point; some schools define these hidden stars differently.",
    ]
    if resolved.approximate:
        risk_flags.append(
            "出生地当前是按区域级回退匹配的，因此宫位边界与隐曜宫位侧重点应视为近似值。"
        )

    return {
        "system": "qizheng_siyu",
        "question_type": "destiny",
        "used_inputs": {
            "birth_datetime": data.birth_datetime.isoformat(sep=" ", timespec="minutes"),
            "birth_location": data.birth_location,
            "resolved_location": resolved.display_name,
            "lat": resolved.lat,
            "lng": resolved.lng,
            "tz_str": resolved.tz_str,
            "location_source": resolved.source,
            "zodiac_basis": "tropical-ecliptic",
            "four_remainders_mode": "true-node + lunar-apogee/perigee proxy",
        },
        "missing_inputs": [],
        "derived_factors": {
            "seven_governors": seven_governors,
            "four_remainders": four_remainders,
            "element_distribution": governor_elements,
            "quality_distribution": governor_qualities,
            "dominant_elements": dominant_elements,
            "dominant_qualities": dominant_qualities,
            "angular_governors": angular_governors,
            "major_aspects": aspects,
            "question_house_mapping": question_mapping,
        },
        "raw_chart": {
            "houses": houses,
            "major_points": major_points,
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "Use this as a natal structural layer; lineage-specific 岁限、宫主飞泊 and full hidden-star judgement are not fully expanded yet.",
        "confidence": "medium",
        "rules_path": [
            "birth-location resolution",
            "seven-governor astronomical positions",
            "luohou-jidu node mapping",
            "yuebo-ziqi proxy derivation",
            "house emphasis and aspect screening",
        ],
    }
