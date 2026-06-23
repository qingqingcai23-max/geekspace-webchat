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
    resolve_birth_location,
)


PLANET_KEYS = [
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
]

ANGLE_KEYS = ["ascendant", "medium_coeli"]

SIGN_NAME_MAP = {
    "Aries": "白羊座",
    "Taurus": "金牛座",
    "Gemini": "双子座",
    "Cancer": "巨蟹座",
    "Leo": "狮子座",
    "Virgo": "处女座",
    "Libra": "天秤座",
    "Scorpio": "天蝎座",
    "Sagittarius": "射手座",
    "Capricorn": "摩羯座",
    "Aquarius": "水瓶座",
    "Pisces": "双鱼座",
}

ELEMENT_NAME_MAP = {
    "Fire": "火",
    "Earth": "土",
    "Air": "风",
    "Water": "水",
}

QUALITY_NAME_MAP = {
    "Cardinal": "创始",
    "Fixed": "固定",
    "Mutable": "变动",
}

PLANET_NAME_MAP = {
    "Sun": "太阳",
    "Moon": "月亮",
    "Mercury": "水星",
    "Venus": "金星",
    "Mars": "火星",
    "Jupiter": "木星",
    "Saturn": "土星",
    "Uranus": "天王星",
    "Neptune": "海王星",
    "Pluto": "冥王星",
    "Ascendant": "上升点",
    "Medium_Coeli": "中天",
}

ASPECT_NAME_MAP = {
    "conjunction": "合相",
    "opposition": "对冲",
    "trine": "拱相",
    "square": "刑相",
    "sextile": "六合相",
}

MOON_PHASE_NAME_MAP = {
    "New Moon": "新月",
    "Waxing Crescent": "娥眉月",
    "First Quarter": "上弦月",
    "Waxing Gibbous": "盈凸月",
    "Full Moon": "满月",
    "Waning Gibbous": "亏凸月",
    "Last Quarter": "下弦月",
    "Third Quarter": "下弦月",
    "Waning Crescent": "残月",
    "Balsamic": "朔前月",
}


@dataclass(frozen=True)
class WesternAstrologyInput:
    birth_datetime: datetime
    birth_location: str
    birth_lat: float | None = None
    birth_lng: float | None = None
    tz_str: str = ""


def dominant_house_summary(planets: dict[str, dict[str, Any]]) -> list[int]:
    occupied = occupied_houses(planets)
    if not occupied:
        return []
    strongest = max(len(names) for names in occupied.values())
    return [int(house) for house, names in occupied.items() if len(names) == strongest]


def translate_sign(value: str) -> str:
    return SIGN_NAME_MAP.get(str(value or "").strip(), str(value or "").strip())


def translate_planet(value: str) -> str:
    return PLANET_NAME_MAP.get(str(value or "").strip(), str(value or "").strip())


def translate_aspect(value: str) -> str:
    return ASPECT_NAME_MAP.get(str(value or "").strip().lower(), str(value or "").strip())


def translate_moon_phase(value: str) -> str:
    return MOON_PHASE_NAME_MAP.get(str(value or "").strip(), str(value or "").strip())


def house_label(value: int | None) -> str:
    return f"第{int(value)}宫" if value else "宫位未明"


def join_cn(items: list[str]) -> str:
    return "、".join(item for item in items if item)


def translate_between(value: str) -> str:
    names = [translate_planet(part.strip()) for part in str(value or "").split("-") if part.strip()]
    return "与".join(names) if names else str(value or "").strip()


def calculate_western_astrology(data: WesternAstrologyInput) -> dict[str, Any]:
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
    planets = extract_points(chart_dump, PLANET_KEYS)
    angles = extract_points(chart_dump, ANGLE_KEYS)
    houses = extract_houses(chart_dump)
    aspects = normalize_aspects(subject, set(planets) | set(angles))

    sun = planets["Sun"]
    moon = planets["Moon"]
    ascendant = angles["Ascendant"]
    moon_phase = chart_dump["lunar_phase"]
    element_distribution = count_by_key(planets, "element", ELEMENT_ORDER)
    quality_distribution = count_by_key(planets, "quality", QUALITY_ORDER)
    dominant_elements = dominant_keys(element_distribution)
    dominant_qualities = dominant_keys(quality_distribution)
    dominant_houses = dominant_house_summary(planets)
    midheaven = angles.get("Medium_Coeli", {})
    moon_phase_name = translate_moon_phase(str(moon_phase.get("moon_phase_name") or ""))

    supporting_signals = [
        f"太阳落在{translate_sign(sun['sign_full'])}的{house_label(sun['house_number'])}。",
        f"月亮落在{translate_sign(moon['sign_full'])}的{house_label(moon['house_number'])}。",
        f"上升点落在{translate_sign(ascendant['sign_full'])}；中天落在{translate_sign(midheaven.get('sign_full') or '')}。",
        f"月相落在{moon_phase_name or '未明'}。",
    ]
    if dominant_elements:
        supporting_signals.append(
            f"元素侧重在{join_cn([ELEMENT_NAME_MAP.get(item, item) for item in dominant_elements])}。"
        )
    if dominant_qualities:
        supporting_signals.append(
            f"模式侧重在{join_cn([QUALITY_NAME_MAP.get(item, item) for item in dominant_qualities])}。"
        )
    if dominant_houses:
        supporting_signals.append(
            "重点宫位落在" + join_cn([house_label(house) for house in dominant_houses]) + "。"
        )
    if aspects:
        strongest = aspects[0]
        supporting_signals.append(
            f"最紧的主要相位是{translate_between(strongest['between'])}形成{translate_aspect(strongest['aspect'])}，容许度为{strongest['orbit']}°。"
        )

    risk_flags = [
        "This local western astrology engine computes natal placements, houses, moon phase, and major aspects offline.",
        "It does not yet include transits, progressions, synastry, or a long-form interpretive layer.",
    ]
    if resolved.approximate:
        risk_flags.append(
            "Birth location was matched to a region-level fallback, so house cusps and angles are approximate."
        )

    primary_finding = (
        f"西洋占星看，太阳落在{translate_sign(sun['sign_full'])}，月亮落在{translate_sign(moon['sign_full'])}，"
        f"上升落在{translate_sign(ascendant['sign_full'])}，构成这张本命盘的核心骨架。"
    )

    return {
        "system": "western_astrology",
        "question_type": "destiny",
        "used_inputs": {
            "birth_datetime": data.birth_datetime.isoformat(sep=" ", timespec="minutes"),
            "birth_location": data.birth_location,
            "resolved_location": resolved.display_name,
            "lat": resolved.lat,
            "lng": resolved.lng,
            "tz_str": resolved.tz_str,
            "location_source": resolved.source,
            "zodiac_type": "Tropical",
            "house_system": chart_dump.get("houses_system_name"),
        },
        "missing_inputs": [],
        "derived_factors": {
            "big_three": {
                "sun": sun["sign_full"],
                "moon": moon["sign_full"],
                "ascendant": ascendant["sign_full"],
            },
            "element_distribution": element_distribution,
            "quality_distribution": quality_distribution,
            "dominant_elements": dominant_elements,
            "dominant_qualities": dominant_qualities,
            "dominant_houses": dominant_houses,
            "moon_phase": moon_phase,
            "major_aspects": aspects,
        },
        "raw_chart": {
            "planets": planets,
            "angles": angles,
            "houses": houses,
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "Use the natal chart as a structural layer; separate timing methods are still needed for short-window decisions.",
        "confidence": "medium",
        "rules_path": [
            "birth-location resolution",
            "tropical chart computation",
            "house extraction",
            "major aspect filtering",
            "element and modality balance",
        ],
    }
