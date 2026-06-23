from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import sxtwl

from .fengshui import parse_direction


HEAVENLY_STEMS = ["\u7532", "\u4e59", "\u4e19", "\u4e01", "\u620a", "\u5df1", "\u5e9a", "\u8f9b", "\u58ec", "\u7678"]
EARTHLY_BRANCHES = ["\u5b50", "\u4e11", "\u5bc5", "\u536f", "\u8fb0", "\u5df3", "\u5348", "\u672a", "\u7533", "\u9149", "\u620c", "\u4ea5"]
STEM_ELEMENTS = {
    "\u7532": "wood",
    "\u4e59": "wood",
    "\u4e19": "fire",
    "\u4e01": "fire",
    "\u620a": "earth",
    "\u5df1": "earth",
    "\u5e9a": "metal",
    "\u8f9b": "metal",
    "\u58ec": "water",
    "\u7678": "water",
}
YANG_STEMS = {"\u7532", "\u4e19", "\u620a", "\u5e9a", "\u58ec"}
SECTOR_ELEMENTS = {
    "N": "water",
    "NE": "earth",
    "E": "wood",
    "SE": "wood",
    "S": "fire",
    "SW": "earth",
    "W": "metal",
    "NW": "metal",
}
GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
CONTROLS = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}
BRANCH_DIRECTION = {
    "\u5b50": "N",
    "\u4e11": "NE",
    "\u5bc5": "NE",
    "\u536f": "E",
    "\u8fb0": "SE",
    "\u5df3": "SE",
    "\u5348": "S",
    "\u672a": "SW",
    "\u7533": "SW",
    "\u9149": "W",
    "\u620c": "NW",
    "\u4ea5": "NW",
}
OPPOSITE_DIRECTION = {"N": "S", "NE": "SW", "E": "W", "SE": "NW", "S": "N", "SW": "NE", "W": "E", "NW": "SE"}
OMEN_HEXAGRAM_BY_DIRECTION = {
    "N": "Open",
    "NE": "Bound",
    "E": "Ascending",
    "SE": "Pervading",
    "S": "Prospering",
    "SW": "Gnawing Bite",
    "W": "Confining",
    "NW": "Limping",
}


@dataclass(frozen=True)
class OnmyodoInput:
    event_date: date
    direction_or_location: str
    event_type: str


def element_relation(day_element: str, direction_element: str) -> tuple[str, int]:
    if day_element == direction_element:
        return "same-element resonance", 6
    if GENERATES[day_element] == direction_element:
        return "day feeds direction", 2
    if GENERATES[direction_element] == day_element:
        return "direction nourishes day", 8
    if CONTROLS[day_element] == direction_element:
        return "day restrains direction", -3
    return "direction restrains day", -8


def normalize_event_type(value: str) -> str:
    text = (value or "").strip().lower()
    aliases = {
        "\u8fc1\u5c45": "move",
        "\u642c\u5bb6": "move",
        "\u5165\u5b85": "move",
        "\u51fa\u884c": "travel",
        "\u65c5\u884c": "travel",
        "\u7948\u798f": "ritual",
        "\u4eea\u5f0f": "ritual",
    }
    return aliases.get(text, text or "general")


def inspect_day(value: date) -> dict[str, Any]:
    day = sxtwl.fromSolar(value.year, value.month, value.day)
    year_gz = day.getYearGZ()
    day_gz = day.getDayGZ()
    year_branch = EARTHLY_BRANCHES[year_gz.dz]
    day_stem = HEAVENLY_STEMS[day_gz.tg]
    return {
        "year_branch": year_branch,
        "day_stem": day_stem,
        "day_branch": EARTHLY_BRANCHES[day_gz.dz],
        "day_element": STEM_ELEMENTS[day_stem],
        "day_polarity": "yang" if day_stem in YANG_STEMS else "yin",
        "year_direction": BRANCH_DIRECTION[year_branch],
    }


def calculate_onmyodo(data: OnmyodoInput) -> dict[str, Any]:
    event_type = normalize_event_type(data.event_type)
    direction, degrees = parse_direction(data.direction_or_location)
    day_info = inspect_day(data.event_date)
    direction_element = SECTOR_ELEMENTS[direction]
    relation, relation_score = element_relation(day_info["day_element"], direction_element)
    relation_map = {
        "same-element resonance": "同气相应",
        "day feeds direction": "日气生扶方位",
        "direction nourishes day": "方位反过来生扶当日",
        "day restrains direction": "当日气机克制方位",
        "direction restrains day": "方位之气反制当日",
    }
    direction_element_map = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
    polarity_map = {"yang": "阳", "yin": "阴"}
    direction_label_map = {
        "N": "北",
        "NE": "东北",
        "E": "东",
        "SE": "东南",
        "S": "南",
        "SW": "西南",
        "W": "西",
        "NW": "西北",
    }
    direction_label = direction_label_map.get(direction, direction)

    score = 50 + relation_score
    supporting_signals = [
        f"日干为{day_info['day_stem']}，五行为{direction_element_map.get(day_info['day_element'], day_info['day_element'])}，阴阳属性为{polarity_map.get(day_info['day_polarity'], day_info['day_polarity'])}。",
        f"方位落在{direction_label}，对应五行是{direction_element_map.get(direction_element, direction_element)}。",
        f"当日与方位的五行关系是：{relation_map.get(relation, relation)}。",
    ]
    risk_flags = [
        "This local onmyodo engine currently evaluates calendrical polarity, element relation, and direction taboo layers.",
        "It does not yet implement a complete historical rekichu, shikiban, or court-era ritual corpus.",
    ]

    if direction == "NE":
        score -= 12
        supporting_signals.append("东北在这个简化模型里视作鬼门位，因此额外提高谨慎度。")
    elif direction == "SW":
        score -= 10
        supporting_signals.append("西南在这个简化模型里视作里鬼门，因此反复与残余风险更高。")

    if direction == day_info["year_direction"]:
        score -= 6
        supporting_signals.append("计划方位与简化年支方位重叠，年度方位之气更强。")
    elif direction == OPPOSITE_DIRECTION[day_info["year_direction"]]:
        score -= 5
        supporting_signals.append("计划方位与简化年支方位对冲，所以阻力更高。")

    if event_type == "travel" and direction in {"NE", "SW"}:
        score -= 4
        supporting_signals.append("出行若经过鬼门相关方位，会再降一档。")
    elif event_type == "ritual" and direction in {"N", "E", "SE"}:
        score += 3
        supporting_signals.append("这个方位在简化模型里更利于仪式性活动。")

    if score >= 58:
        primary = f"{direction_label}方位在当前日期下整体偏顺，可用。"
        confidence = "medium"
    elif score >= 46:
        primary = f"{direction_label}方位在当前日期下不算最好，但还能用，方向禁忌与时点信号偏混合。"
        confidence = "medium"
    else:
        primary = f"{direction_label}方位在当前日期下偏不利，谨慎度要明显提高。"
        confidence = "low"

    return {
        "system": "onmyodo",
        "question_type": "space",
        "used_inputs": {
            "date": data.event_date.isoformat(),
            "direction_or_location": data.direction_or_location,
            "event_type": event_type,
            "resolved_direction": direction,
            "degrees": degrees,
        },
        "missing_inputs": [],
        "derived_factors": {
            "day_info": day_info,
            "direction_element": direction_element,
            "direction_relation": relation,
            "score": score,
            "omen_hexagram": OMEN_HEXAGRAM_BY_DIRECTION.get(direction, ""),
        },
        "primary_finding": primary,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "Use the same-day directional reading only as a local timing layer, not as a full ritual prescription.",
        "confidence": confidence,
        "rules_path": [
            "calendar conversion",
            "yin-yang and five-element day mapping",
            "direction taboo screening",
            "event-type weighting",
        ],
    }
