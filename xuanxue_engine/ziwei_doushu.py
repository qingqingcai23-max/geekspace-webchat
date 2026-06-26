from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .node_bridge import run_node_bridge


BRIDGE_PATH = Path(__file__).resolve().with_name("ziwei_bridge.cjs")

KEY_PALACES = ["命宫", "官禄", "财帛", "夫妻", "迁移", "疾厄", "福德", "田宅"]


@dataclass(frozen=True)
class ZiweiDoushuInput:
    birth_datetime: datetime
    gender: str
    target_date: date | None = None
    calendar: str = "solar"


def normalize_gender(value: str) -> str:
    lowered = (value or "").strip().lower()
    if lowered in {"m", "male", "男", "男性"}:
        return "male"
    if lowered in {"f", "female", "女", "女性"}:
        return "female"
    return ""


def time_index_from_datetime(dt: datetime) -> int:
    hour = dt.hour
    if hour == 23:
        return 12
    if hour == 0:
        return 0
    if 1 <= hour <= 2:
        return 1
    if 3 <= hour <= 4:
        return 2
    if 5 <= hour <= 6:
        return 3
    if 7 <= hour <= 8:
        return 4
    if 9 <= hour <= 10:
        return 5
    if 11 <= hour <= 12:
        return 6
    if 13 <= hour <= 14:
        return 7
    if 15 <= hour <= 16:
        return 8
    if 17 <= hour <= 18:
        return 9
    if 19 <= hour <= 20:
        return 10
    if 21 <= hour <= 22:
        return 11
    raise ValueError("unable to map birth hour to a Ziwei time index")


def simplify_stars(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": str(item.get("name") or ""),
            "type": str(item.get("type") or ""),
            "brightness": str(item.get("brightness") or ""),
            "mutagen": str(item.get("mutagen") or ""),
        }
        for item in items
    ]


def simplify_palace(palace: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": str(palace.get("name") or ""),
        "index": int(palace.get("index", 0)),
        "earthly_branch": str(palace.get("earthlyBranch") or ""),
        "heavenly_stem": str(palace.get("heavenlyStem") or ""),
        "is_body_palace": bool(palace.get("isBodyPalace")),
        "is_original_palace": bool(palace.get("isOriginalPalace")),
        "major_stars": simplify_stars(list(palace.get("majorStars") or [])),
        "minor_stars": simplify_stars(list(palace.get("minorStars") or [])),
        "adjective_stars": simplify_stars(list(palace.get("adjectiveStars") or [])),
        "changsheng12": str(palace.get("changsheng12") or ""),
        "boshi12": str(palace.get("boshi12") or ""),
        "jiangqian12": str(palace.get("jiangqian12") or ""),
        "suiqian12": str(palace.get("suiqian12") or ""),
        "decadal": dict(palace.get("decadal") or {}),
        "ages": list(palace.get("ages") or []),
    }


def star_names(items: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("name") or "") for item in items if item.get("name")]


def mutagen_names(items: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for item in items:
        mutagen = str(item.get("mutagen") or "")
        if mutagen:
            names.append(f"{item.get('name')}{mutagen}")
    return names


def palace_summary(palace: dict[str, Any]) -> dict[str, Any]:
    major = star_names(list(palace.get("major_stars") or []))
    minor = star_names(list(palace.get("minor_stars") or []))
    return {
        "name": palace["name"],
        "earthly_branch": palace["earthly_branch"],
        "major_stars": major,
        "minor_stars": minor,
        "mutagens": mutagen_names(list(palace.get("major_stars") or []) + list(palace.get("minor_stars") or [])),
        "is_body_palace": palace["is_body_palace"],
        "is_original_palace": palace["is_original_palace"],
        "decadal_range": list((palace.get("decadal") or {}).get("range") or []),
    }


def find_palace(palaces: list[dict[str, Any]], name: str) -> dict[str, Any]:
    for palace in palaces:
        if palace["name"] == name:
            return palace
    raise ValueError(f"unable to find palace {name}")


def current_decadal_palace(palaces: list[dict[str, Any]], nominal_age: int) -> dict[str, Any] | None:
    for palace in palaces:
        decadal_range = list((palace.get("decadal") or {}).get("range") or [])
        if len(decadal_range) == 2 and decadal_range[0] <= nominal_age <= decadal_range[1]:
            return palace
    return None


def current_cycle_focus(cycle: dict[str, Any]) -> str:
    palace_names = list(cycle.get("palaceNames") or [])
    index = int(cycle.get("index", -1))
    if 0 <= index < len(palace_names):
        return str(palace_names[index])
    return ""


def run_bridge(payload: dict[str, Any]) -> dict[str, Any]:
    return run_node_bridge(BRIDGE_PATH, payload, "ziwei bridge")


def calculate_ziwei_doushu(data: ZiweiDoushuInput) -> dict[str, Any]:
    normalized_gender = normalize_gender(data.gender)
    if not normalized_gender:
        raise ValueError("gender is required for ziwei_doushu and must resolve to male or female")

    target_date = data.target_date or date.today()
    bridge_payload = {
        "solarDate": data.birth_datetime.date().isoformat(),
        "timeIndex": time_index_from_datetime(data.birth_datetime),
        "gender": normalized_gender,
        "targetDateTime": f"{target_date.isoformat()}T12:00:00+08:00",
    }
    raw = run_bridge(bridge_payload)
    chart = dict(raw.get("chart") or {})
    horoscope = dict(raw.get("horoscope") or {})
    palaces = [simplify_palace(dict(item)) for item in list(chart.get("palaces") or [])]

    destiny = palace_summary(find_palace(palaces, "命宫"))
    career = palace_summary(find_palace(palaces, "官禄"))
    wealth = palace_summary(find_palace(palaces, "财帛"))
    relationship = palace_summary(find_palace(palaces, "夫妻"))
    body_palace = next((palace_summary(item) for item in palaces if item["is_body_palace"]), None)

    age_info = dict(horoscope.get("age") or {})
    decadal_info = dict(horoscope.get("decadal") or {})
    yearly_info = dict(horoscope.get("yearly") or {})
    decadal_focus = current_decadal_palace(palaces, int(age_info.get("nominalAge", 0)))

    supporting_signals = [
        f"命宫在{destiny['earthly_branch']}位，主星为{'、'.join(destiny['major_stars']) or '空宫'}。",
        f"官禄宫主星为{'、'.join(career['major_stars']) or '空宫'}；财帛宫主星为{'、'.join(wealth['major_stars']) or '空宫'}。",
        f"当前虚岁 {age_info.get('nominalAge', '')}，大限焦点落在{current_cycle_focus(decadal_info) or '未识别'}，流年焦点落在{current_cycle_focus(yearly_info) or '未识别'}。",
    ]
    if body_palace:
        supporting_signals.append(
            f"身宫落在{body_palace['name']}，其宫主星为{'、'.join(body_palace['major_stars']) or '空宫'}。"
        )
    if destiny["mutagens"]:
        supporting_signals.append(f"命宫四化/变曜提示：{'、'.join(destiny['mutagens'])}。")

    risk_flags = [
        "This local ziwei_doushu engine uses the open-source iztro chart core to compute the 12 palaces, stars, and current cycle overlays.",
        "Interpretation schools differ across lineages, so this version returns a structural chart reading first and keeps advanced school-specific judgement conservative.",
    ]
    if data.calendar == "lunar":
        risk_flags.append("The original query contained lunar-date input and was normalized into solar birth time before chart generation.")

    primary_finding = (
        f"命宫主轴为{'、'.join(destiny['major_stars']) or '空宫'}，"
        f"身宫落{body_palace['name'] if body_palace else '未识别'}，"
        f"当前大限重心在{decadal_focus['name'] if decadal_focus else current_cycle_focus(decadal_info) or '未识别'}。"
    )

    selected_palaces = {
        palace_name: palace_summary(find_palace(palaces, palace_name))
        for palace_name in KEY_PALACES
    }

    return {
        "system": "ziwei_doushu",
        "question_type": "destiny",
        "used_inputs": {
            "birth_datetime": data.birth_datetime.isoformat(sep=" ", timespec="minutes"),
            "gender": normalized_gender,
            "calendar": data.calendar,
            "time_index": bridge_payload["timeIndex"],
            "target_date": target_date.isoformat(),
        },
        "missing_inputs": [],
        "derived_factors": {
            "solar_date": str(chart.get("solarDate") or ""),
            "lunar_date": str(chart.get("lunarDate") or ""),
            "chinese_date": str(chart.get("chineseDate") or ""),
            "zodiac": str(chart.get("zodiac") or ""),
            "sign": str(chart.get("sign") or ""),
            "five_elements_class": str(chart.get("fiveElementsClass") or ""),
            "soul_star": str(chart.get("soul") or ""),
            "body_star": str(chart.get("body") or ""),
            "key_palaces": selected_palaces,
            "current_cycles": {
                "nominal_age": int(age_info.get("nominalAge", 0)),
                "decadal_focus": current_cycle_focus(decadal_info),
                "yearly_focus": current_cycle_focus(yearly_info),
                "age_focus": current_cycle_focus(age_info),
                "yearly_mutagen": list(yearly_info.get("mutagen") or []),
                "decadal_mutagen": list(decadal_info.get("mutagen") or []),
            },
        },
        "raw_chart": {
            "profile": {
                "gender": str(chart.get("gender") or ""),
                "time": str(chart.get("time") or ""),
                "time_range": str(chart.get("timeRange") or ""),
                "earthly_branch_of_body_palace": str(chart.get("earthlyBranchOfBodyPalace") or ""),
                "earthly_branch_of_soul_palace": str(chart.get("earthlyBranchOfSoulPalace") or ""),
            },
            "palaces": palaces,
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "Read the natal palace structure first; then use the current decadal and yearly overlays as the active timing layer.",
        "confidence": "medium",
        "rules_path": [
            "solar birth normalization",
            "ziwei twelve-palace chart generation",
            "major/minor star extraction",
            "key palace selection",
            "current cycle overlay",
        ],
    }
