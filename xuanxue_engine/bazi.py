from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import sxtwl

from .astro_common import resolve_birth_location
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


def true_solar_offset_minutes(lng: float) -> int:
    return int(round((float(lng) - 120.0) * 4))


def apply_true_solar_time(dt: datetime, lng: float) -> datetime:
    return dt + timedelta(minutes=true_solar_offset_minutes(lng))


def element_controlled_by(element: str) -> str:
    for source, target in ELEMENT_CONTROLS.items():
        if target == element:
            return source
    raise ValueError(f"unsupported element: {element}")


def element_generating(element: str) -> str:
    for source, target in ELEMENT_GENERATES.items():
        if target == element:
            return source
    raise ValueError(f"unsupported element: {element}")


def day_master_strength(
    day_master: str,
    month_branch: str,
    counts: dict[str, int],
) -> str:
    element = STEM_ELEMENTS[day_master]
    same_side = counts.get(element, 0)
    resource_side = counts.get(element_generating(element), 0)
    draining_side = counts.get(ELEMENT_GENERATES[element], 0)
    authority_side = counts.get(element_controlled_by(element), 0)

    score = same_side + resource_side - draining_side - authority_side
    season = SEASON_BY_MONTH_BRANCH.get(month_branch, "")
    seasonal_peak = {
        "木": "春",
        "火": "夏",
        "金": "秋",
        "水": "冬",
    }.get(element)
    if seasonal_peak == season:
        score += 2
    if score >= 5:
        return "strong"
    if score <= 1:
        return "weak"
    return "balanced"


def useful_elements(day_master: str, strength: str) -> dict[str, list[str]]:
    element = STEM_ELEMENTS[day_master]
    output = ELEMENT_GENERATES[element]
    wealth = ELEMENT_CONTROLS[element]
    authority = element_controlled_by(element)
    resource = element_generating(element)

    if strength == "strong":
        favorable = [wealth, authority, output]
        caution = [element, resource]
    elif strength == "weak":
        favorable = [resource, element]
        caution = [wealth, authority]
    else:
        favorable = [output, wealth, resource]
        caution = [element]
    return {"favorable": favorable, "caution": caution}


def bazi_overview(
    day_master: str,
    strength: str,
    strongest: list[tuple[str, int]],
    weakest: list[str],
    ten_gods: dict[str, str],
) -> dict[str, str]:
    output_count = sum(1 for value in ten_gods.values() if value in {"食神", "伤官"})
    wealth_count = sum(1 for value in ten_gods.values() if value in {"正财", "偏财"})
    officer_count = sum(1 for value in ten_gods.values() if value in {"正官", "七杀"})
    resource_count = sum(1 for value in ten_gods.values() if value in {"正印", "偏印"})
    peer_count = sum(1 for value in ten_gods.values() if value in {"比肩", "劫财"})

    strongest_labels = [item[0] for item in strongest if strongest and item[1] == strongest[0][1]]
    strongest_text = "、".join(strongest_labels) if strongest_labels else "未明"
    weakest_text = "、".join(weakest) if weakest else "未明"

    personality_parts = [
        f"日主{day_master}落盘，性格底色更偏{'主动发起、先做后校正' if strength == 'strong' else '先观察再发力、重承接与稳定' if strength == 'weak' else '能主动推进，也会顾整体平衡'}。",
        f"盘里偏强的是{strongest_text}，偏弱的是{weakest_text}，说明你的能量主轴很明确，不是平均分布型。",
    ]
    if output_count >= 1:
        personality_parts.append("食伤能见，表达、拆解问题、把经验讲清楚是显性优势。")
    if resource_count >= 1:
        personality_parts.append("印星露头，学习、总结、吸收新方法的能力也在。")
    if peer_count >= 2:
        personality_parts.append("比劫偏重，自主性强，不适合长期被高压粗管。")

    career_parts = [
        "事业上更适合走能把判断力、输出能力和现实结果绑在一起的位置。"
    ]
    if officer_count >= 1:
        career_parts.append("官杀能立住，说明在职责清晰、结果可衡量、位势明确的路径上更容易出成绩。")
    if wealth_count >= 1:
        career_parts.append("财星可用，事业与收入兑现通常绑定得比较深。")
    if output_count >= 1:
        career_parts.append("不宜只做纯执行，更适合咨询、销售、方案、内容、项目推进这类需要持续输出的角色。")

    wealth_parts = [
        "财运更像靠结构化经营出来，不只是等运气上门。"
    ]
    if wealth_count >= 2:
        wealth_parts.append("财星不弱，说明现实进账通道并不少，重点在于把边界和节奏守住。")
    elif wealth_count >= 1:
        wealth_parts.append("有明确进账通道，适合把能力、项目或业务资源变成稳定收入。")
    if peer_count >= 2:
        wealth_parts.append("比劫重时最怕钱进来又被合作、人情、垫资和分流吃掉。")
    if "水" in weakest:
        wealth_parts.append("水弱时现金流缓冲偏薄，回款慢或账面热闹但落袋慢会更伤。")

    relationship_parts = [
        "婚恋更看重长期磨合后的稳定感，不太适合只靠一时热度推进。"
    ]
    if officer_count >= 1 or wealth_count >= 1:
        relationship_parts.append("你会很在意责任感、现实配合度和边界是否清楚。")
    if peer_count >= 2:
        relationship_parts.append("关系里要防双方都太强，或者第三方意见过多把节奏带偏。")
    if output_count >= 1:
        relationship_parts.append("表达直接是优点，但情绪上头时也容易把原本能谈开的事谈硬。")

    health_parts = [
        f"健康上，五行偏强在{strongest_text}、偏弱在{weakest_text}，更像提醒你生活节奏与消耗结构要调平，而不是替代医学判断。"
    ]
    if "水" in weakest:
        health_parts.append("水弱时优先留意休息、恢复、情绪缓冲和过劳后的透支感。")
    if "木" in weakest:
        health_parts.append("木弱时要防长期发散、方向频繁切换带来的精力折损。")
    if "火" in strongest_labels:
        health_parts.append("火偏旺时容易节奏过快、上头推进、睡不踏实。")

    direction_parts = [
        "发展方向上，最适合把主观能动性、表达输出和现实兑现连成一条线。"
    ]
    if output_count >= 1 and officer_count >= 1:
        direction_parts.append("先在成熟平台做出成绩，再逐步转成更自主的项目制或个人品牌，会更稳。")
    elif output_count >= 1:
        direction_parts.append("优先考虑咨询、销售、内容、培训、方案、项目型工作。")
    elif officer_count >= 1:
        direction_parts.append("优先考虑职责清晰、信用可积累、可见度高的职业路径。")

    return {
        "personality": "".join(personality_parts),
        "career": "".join(career_parts),
        "wealth": "".join(wealth_parts),
        "relationship": "".join(relationship_parts),
        "health": "".join(health_parts),
        "direction": "".join(direction_parts),
    }


def calculate_bazi(data: BaziInput) -> dict[str, Any]:
    if data.calendar != "solar":
        raise ValueError("第一版八字计算器只接受公历 solar 输入。")

    dt = data.birth_datetime
    resolved_location = None
    unresolved_location = ""
    chart_dt = dt
    true_solar_delta_minutes = 0

    if data.birth_location:
        try:
            resolved_location = resolve_birth_location(data.birth_location)
        except ValueError:
            unresolved_location = data.birth_location
        if data.use_true_solar_time and resolved_location:
            chart_dt = apply_true_solar_time(dt, resolved_location.lng)
            true_solar_delta_minutes = true_solar_offset_minutes(resolved_location.lng)

    if data.late_zi_hour_next_day and chart_dt.hour == 23:
        chart_dt = chart_dt + timedelta(days=1)

    day = sxtwl.fromSolar(chart_dt.year, chart_dt.month, chart_dt.day)
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
        "hour": ganzhi(day.getHourGZ(chart_dt.hour)),
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
    strength = day_master_strength(day_master, month_branch, counts)
    favorable = useful_elements(day_master, strength)
    overview = bazi_overview(day_master, strength, strongest, weakest, ten_gods)

    risk_flags = []
    if not data.birth_location:
        risk_flags.append("未提供出生地，当前没有做真太阳时修正。")
    elif unresolved_location:
        risk_flags.append("出生地未能解析为本地城市库条目，当前未做真太阳时修正。")
    if not data.gender:
        risk_flags.append("未提供性别，当前不计算大运顺逆与起运。")
    if dt.hour == 23 and not data.late_zi_hour_next_day:
        risk_flags.append("23点子时存在早晚子时流派差异，本次按同一公历日处理。")
    if resolved_location and resolved_location.approximate:
        risk_flags.append("出生地按区域级别近似解析，真太阳时修正只能视作近似值。")

    return {
        "system": "bazi",
        "input": {
            "birth_datetime": dt.isoformat(sep=" ", timespec="minutes"),
            "chart_datetime": chart_dt.isoformat(sep=" ", timespec="minutes"),
            "gender": data.gender,
            "birth_location": data.birth_location,
            "calendar": data.calendar,
            "use_true_solar_time": data.use_true_solar_time,
            "late_zi_hour_next_day": data.late_zi_hour_next_day,
            "true_solar_offset_minutes": true_solar_delta_minutes,
            "location_resolution_failed": bool(unresolved_location),
            "resolved_location": resolved_location.display_name if resolved_location else "",
            "resolved_lng": resolved_location.lng if resolved_location else None,
            "resolved_tz_str": resolved_location.tz_str if resolved_location else "",
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
        "day_master_strength": strength,
        "favorable_elements": favorable["favorable"],
        "caution_elements": favorable["caution"],
        "overview": overview,
        "summary": {
            "strongest_elements": [item[0] for item in strongest if item[1] == strongest[0][1]],
            "weakest_elements": weakest,
            "note": "当前已能完成排盘、五行、十神与多维总评，但仍不是完整大运流年断法。",
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
        "confidence": "high" if resolved_location and data.gender else "medium",
    }
