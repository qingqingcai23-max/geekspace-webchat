from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from kerykeion import AstrologicalSubject

from .astro_common import (
    extract_points,
    resolve_birth_location,
    sign_name_from_index,
    whole_sign_house,
)


PLANET_KEYS = [
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "mean_north_lunar_node",
    "mean_south_lunar_node",
]

NAME_OVERRIDES = {
    "mean_north_lunar_node": "Rahu",
    "mean_south_lunar_node": "Ketu",
}

NAKSHATRAS = [
    ("Ashwini", "Ketu"),
    ("Bharani", "Venus"),
    ("Krittika", "Sun"),
    ("Rohini", "Moon"),
    ("Mrigashirsha", "Mars"),
    ("Ardra", "Rahu"),
    ("Punarvasu", "Jupiter"),
    ("Pushya", "Saturn"),
    ("Ashlesha", "Mercury"),
    ("Magha", "Ketu"),
    ("Purva Phalguni", "Venus"),
    ("Uttara Phalguni", "Sun"),
    ("Hasta", "Moon"),
    ("Chitra", "Mars"),
    ("Swati", "Rahu"),
    ("Vishakha", "Jupiter"),
    ("Anuradha", "Saturn"),
    ("Jyeshtha", "Mercury"),
    ("Mula", "Ketu"),
    ("Purva Ashadha", "Venus"),
    ("Uttara Ashadha", "Sun"),
    ("Shravana", "Moon"),
    ("Dhanishta", "Mars"),
    ("Shatabhisha", "Rahu"),
    ("Purva Bhadrapada", "Jupiter"),
    ("Uttara Bhadrapada", "Saturn"),
    ("Revati", "Mercury"),
]

SIGN_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

SPECIAL_ASPECTS = {
    "Mars": (4, 7, 8),
    "Jupiter": (5, 7, 9),
    "Saturn": (3, 7, 10),
}

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

PLANET_NAME_MAP = {
    "Sun": "太阳",
    "Moon": "月亮",
    "Mercury": "水星",
    "Venus": "金星",
    "Mars": "火星",
    "Jupiter": "木星",
    "Saturn": "土星",
    "Rahu": "罗喉",
    "Ketu": "计都",
}

NAKSHATRA_NAME_MAP = {
    "Ashwini": "阿湿毗尼",
    "Bharani": "婆罗尼",
    "Krittika": "计都",
    "Rohini": "毕宿",
    "Mrigashirsha": "觜宿",
    "Ardra": "参宿",
    "Punarvasu": "井宿",
    "Pushya": "鬼宿",
    "Ashlesha": "柳宿",
    "Magha": "星宿",
    "Purva Phalguni": "张宿",
    "Uttara Phalguni": "翼宿",
    "Hasta": "轸宿",
    "Chitra": "角宿",
    "Swati": "亢宿",
    "Vishakha": "氐宿",
    "Anuradha": "房宿",
    "Jyeshtha": "心宿",
    "Mula": "尾宿",
    "Purva Ashadha": "箕宿",
    "Uttara Ashadha": "斗宿",
    "Shravana": "牛宿",
    "Dhanishta": "女宿",
    "Shatabhisha": "虚宿",
    "Purva Bhadrapada": "危宿",
    "Uttara Bhadrapada": "室宿",
    "Revati": "壁宿",
}


@dataclass(frozen=True)
class VedicAstrologyInput:
    birth_datetime: datetime
    birth_location: str
    ayanamsa: str = "LAHIRI"
    birth_lat: float | None = None
    birth_lng: float | None = None
    tz_str: str = ""


def translate_sign(value: str) -> str:
    return SIGN_NAME_MAP.get(str(value or "").strip(), str(value or "").strip())


def translate_planet(value: str) -> str:
    return PLANET_NAME_MAP.get(str(value or "").strip(), str(value or "").strip())


def translate_nakshatra(value: str) -> str:
    return NAKSHATRA_NAME_MAP.get(str(value or "").strip(), str(value or "").strip())


def house_label(value: int | None) -> str:
    return f"第{int(value)}宫" if value else "宫位未明"


def join_cn(items: list[str]) -> str:
    return "、".join(item for item in items if item)


def nakshatra_from_degree(abs_degree: float) -> dict[str, Any]:
    segment = 360.0 / 27.0
    pada_segment = segment / 4.0
    index = int(abs_degree // segment) % 27
    offset = abs_degree % segment
    pada = int(offset // pada_segment) + 1
    name, ruler = NAKSHATRAS[index]
    return {
        "name": name,
        "lord": ruler,
        "index": index + 1,
        "pada": min(pada, 4),
    }


def build_whole_sign_houses(lagna_sign_index: int) -> dict[str, str]:
    houses: dict[str, str] = {}
    for house in range(1, 13):
        houses[str(house)] = sign_name_from_index(lagna_sign_index + house - 1)
    return houses


def graha_drishti(points: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    occupied_by_house: dict[int, list[str]] = {}
    for name, point in points.items():
        occupied_by_house.setdefault(int(point["vedic_house"]), []).append(name)

    drishti: list[dict[str, Any]] = []
    for name, point in points.items():
        steps = SPECIAL_ASPECTS.get(name, (7,))
        for step in steps:
            target_house = ((int(point["vedic_house"]) + step - 2) % 12) + 1
            targets = occupied_by_house.get(target_house, [])
            drishti.append(
                {
                    "source": name,
                    "from_house": int(point["vedic_house"]),
                    "to_house": target_house,
                    "occupied_targets": targets,
                }
            )
    occupied_only = [item for item in drishti if item["occupied_targets"]]
    occupied_only.sort(key=lambda item: (item["source"], item["to_house"]))
    return occupied_only[:12]


def calculate_vedic_astrology(data: VedicAstrologyInput) -> dict[str, Any]:
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
        zodiac_type="Sidereal",
        sidereal_mode=(data.ayanamsa or "LAHIRI").upper(),
    )
    chart_dump = subject.model_dump()
    points = extract_points(chart_dump, PLANET_KEYS, NAME_OVERRIDES)
    lagna = extract_points(chart_dump, ["ascendant"])["Ascendant"]
    lagna_house_map = build_whole_sign_houses(lagna["sign_index"])

    for point in points.values():
        point["vedic_house"] = whole_sign_house(point["sign_index"], lagna["sign_index"])

    moon = points["Moon"]
    moon_nakshatra = nakshatra_from_degree(float(moon["absolute_degree"]))
    lagna_lord = SIGN_RULERS[lagna["sign_full"]]
    lagna_lord_point = points[lagna_lord]
    kendra_planets = [name for name, point in points.items() if point["vedic_house"] in {1, 4, 7, 10}]
    trikona_planets = [name for name, point in points.items() if point["vedic_house"] in {1, 5, 9}]
    dusthana_planets = [name for name, point in points.items() if point["vedic_house"] in {6, 8, 12}]
    drishti = graha_drishti(points)

    supporting_signals = [
        f"上升点落在{translate_sign(lagna['sign_full'])}。",
        f"月亮落在{translate_nakshatra(moon_nakshatra['name'])}第{moon_nakshatra['pada']}分段。",
        f"命主星{translate_planet(lagna_lord)}落在{house_label(lagna_lord_point['vedic_house'])}。",
    ]
    if kendra_planets:
        supporting_signals.append(
            f"四正宫位有{join_cn([translate_planet(item) for item in kendra_planets])}。"
        )
    if trikona_planets:
        supporting_signals.append(
            f"三合宫位有{join_cn([translate_planet(item) for item in trikona_planets])}。"
        )
    if drishti:
        first = drishti[0]
        if first["occupied_targets"]:
            supporting_signals.append(
                f"{translate_planet(first['source'])}照临{house_label(first['to_house'])}，该宫当前有{join_cn([translate_planet(item) for item in first['occupied_targets']])}。"
            )

    risk_flags = [
        "This local vedic astrology engine computes sidereal graha positions, lagna, nakshatra, and whole-sign house placement offline.",
        "It does not yet include divisional charts, vimshottari dasha, shadbala, or transit timing.",
    ]
    if resolved.approximate:
        risk_flags.append(
            "Birth location was matched to a region-level fallback, so lagna degree and house emphasis are approximate."
        )

    primary_finding = (
        f"吠陀盘看，命宫落在{translate_sign(lagna['sign_full'])}，月宿为{translate_nakshatra(moon_nakshatra['name'])}，"
        f"命主星{translate_planet(lagna_lord)}把盘面的主轴牵到{house_label(lagna_lord_point['vedic_house'])}。"
    )

    return {
        "system": "vedic_astrology",
        "question_type": "destiny",
        "used_inputs": {
            "birth_datetime": data.birth_datetime.isoformat(sep=" ", timespec="minutes"),
            "birth_location": data.birth_location,
            "resolved_location": resolved.display_name,
            "lat": resolved.lat,
            "lng": resolved.lng,
            "tz_str": resolved.tz_str,
            "location_source": resolved.source,
            "zodiac_type": "Sidereal",
            "ayanamsa": (data.ayanamsa or "LAHIRI").upper(),
            "ayanamsa_value": round(float(chart_dump.get("ayanamsa_value", 0.0)), 4),
        },
        "missing_inputs": [],
        "derived_factors": {
            "lagna": lagna,
            "moon_nakshatra": moon_nakshatra,
            "lagna_lord": {
                "planet": lagna_lord,
                "house": lagna_lord_point["vedic_house"],
                "sign": lagna_lord_point["sign_full"],
            },
            "whole_sign_houses": lagna_house_map,
            "kendra_planets": kendra_planets,
            "trikona_planets": trikona_planets,
            "dusthana_planets": dusthana_planets,
            "graha_drishti": drishti,
        },
        "raw_chart": {
            "planets": points,
            "lagna": lagna,
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "Use this natal sidereal reading as a structural layer; dasha and transit timing are still separate work.",
        "confidence": "medium",
        "rules_path": [
            "birth-location resolution",
            "sidereal chart computation",
            "whole-sign house mapping",
            "nakshatra extraction",
            "lagna-lord and drishti screening",
        ],
    }
