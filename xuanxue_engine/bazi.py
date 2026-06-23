from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import sxtwl

from .constants import (
    BRANCH_HIDDEN_STEMS,
    EARTHLY_BRANCHES,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATES,
    HEAVENLY_STEMS,
    SEASON_BY_MONTH_BRANCH,
    STEM_ELEMENTS,
    STEM_POLARITY,
)


@dataclass(frozen=True)
class BaziInput:
    birth_datetime: datetime
    gender: str = ""
    birth_location: str = ""
    calendar: str = "solar"
    use_true_solar_time: bool = False
    late_zi_hour_next_day: bool = False


def ganzhi(gz: Any) -> dict[str, Any]:
    stem = HEAVENLY_STEMS[gz.tg]
    branch = EARTHLY_BRANCHES[gz.dz]
    return {
        "stem": stem,
        "branch": branch,
        "text": f"{stem}{branch}",
        "stem_index": int(gz.tg),
        "branch_index": int(gz.dz),
        "element": STEM_ELEMENTS[stem],
        "polarity": STEM_POLARITY[stem],
        "hidden_stems": BRANCH_HIDDEN_STEMS[branch],
    }


def ten_god(day_stem: str, other_stem: str) -> str:
    day_element = STEM_ELEMENTS[day_stem]
    other_element = STEM_ELEMENTS[other_stem]
    same_polarity = STEM_POLARITY[day_stem] == STEM_POLARITY[other_stem]

    if other_element == day_element:
        return "比肩" if same_polarity else "劫财"
    if ELEMENT_GENERATES[day_element] == other_element:
        return "食神" if same_polarity else "伤官"
    if ELEMENT_CONTROLS[day_element] == other_element:
        return "偏财" if same_polarity else "正财"
    if ELEMENT_CONTROLS[other_element] == day_element:
        return "七杀" if same_polarity else "正官"
    if ELEMENT_GENERATES[other_element] == day_element:
        return "偏印" if same_polarity else "正印"
    return "未知"


def element_counts(pillars: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for pillar in pillars.values():
        counts[STEM_ELEMENTS[pillar["stem"]]] += 2
        for hidden in pillar["hidden_stems"]:
            counts[STEM_ELEMENTS[hidden]] += 1
    return counts


def calculate_bazi(data: BaziInput) -> dict[str, Any]:
    if data.calendar != "solar":
        raise ValueError("第一版八字计算器只接受公历 solar 输入。")
    if data.use_true_solar_time:
        raise ValueError("第一版暂未实现真太阳时换算，请先使用标准北京时间。")

    dt = data.birth_datetime
    day = sxtwl.fromSolar(dt.year, dt.month, dt.day)
    lunar_date = {
        "year": day.getLunarYear(),
        "month": day.getLunarMonth(),
        "day": day.getLunarDay(),
        "is_leap_month": bool(day.isLunarLeap()),
        "text": f"{day.getLunarYear()}年{day.getLunarMonth()}月{day.getLunarDay()}日",
    }
    pillars = {
        "year": ganzhi(day.getYearGZ()),
        "month": ganzhi(day.getMonthGZ()),
        "day": ganzhi(day.getDayGZ()),
        "hour": ganzhi(day.getHourGZ(dt.hour)),
    }
    day_master = pillars["day"]["stem"]

    ten_gods = {}
    hidden_ten_gods = {}
    for name, pillar in pillars.items():
        ten_gods[name] = ten_god(day_master, pillar["stem"])
        hidden_ten_gods[name] = [
            {"stem": stem, "ten_god": ten_god(day_master, stem)}
            for stem in pillar["hidden_stems"]
        ]

    counts = element_counts(pillars)
    strongest = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    weakest = [element for element, value in counts.items() if value == min(counts.values())]
    month_branch = pillars["month"]["branch"]

    risk_flags = []
    if not data.birth_location:
        risk_flags.append("未提供出生地，暂未进行真太阳时或时区校正。")
    if not data.gender:
        risk_flags.append("未提供性别，暂不计算大运顺逆与起运。")
    if dt.hour == 23 and not data.late_zi_hour_next_day:
        risk_flags.append("23点子时存在早晚子时流派差异，本次按同一公历日处理。")

    return {
        "system": "bazi",
        "input": {
            "birth_datetime": dt.isoformat(sep=" ", timespec="minutes"),
            "gender": data.gender,
            "birth_location": data.birth_location,
            "calendar": data.calendar,
            "use_true_solar_time": data.use_true_solar_time,
            "late_zi_hour_next_day": data.late_zi_hour_next_day,
        },
        "lunar_date": lunar_date,
        "pillars": pillars,
        "day_master": {
            "stem": day_master,
            "element": STEM_ELEMENTS[day_master],
            "polarity": STEM_POLARITY[day_master],
        },
        "ten_gods": ten_gods,
        "hidden_ten_gods": hidden_ten_gods,
        "five_element_counts": counts,
        "season": SEASON_BY_MONTH_BRANCH.get(month_branch, ""),
        "summary": {
            "strongest_elements": [item[0] for item in strongest if item[1] == strongest[0][1]],
            "weakest_elements": weakest,
            "note": "这是排盘与结构提取结果，不等同于完整用神、格局和岁运断语。",
        },
        "missing_inputs": [
            item
            for item, missing in {
                "出生地": not data.birth_location,
                "性别": not data.gender,
            }.items()
            if missing
        ],
        "risk_flags": risk_flags,
        "confidence": "medium" if not risk_flags else "low",
    }
