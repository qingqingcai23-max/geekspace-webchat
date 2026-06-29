from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

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

JIEQI_NAMES = {
    0: "冬至",
    1: "小寒",
    2: "大寒",
    3: "立春",
    4: "雨水",
    5: "惊蛰",
    6: "春分",
    7: "清明",
    8: "谷雨",
    9: "立夏",
    10: "小满",
    11: "芒种",
    12: "夏至",
    13: "小暑",
    14: "大暑",
    15: "立秋",
    16: "处暑",
    17: "白露",
    18: "秋分",
    19: "寒露",
    20: "霜降",
    21: "立冬",
    22: "小雪",
    23: "大雪",
}
JIE_BOUNDARY_INDEXES = {1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23}
PILLAR_LABELS = {"year": "年", "month": "月", "day": "日", "hour": "时"}
BRANCH_CLASHES = {
    "子": "午",
    "丑": "未",
    "寅": "申",
    "卯": "酉",
    "辰": "戌",
    "巳": "亥",
    "午": "子",
    "未": "丑",
    "申": "寅",
    "酉": "卯",
    "戌": "辰",
    "亥": "巳",
}


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


def current_reference_datetime(tz_str: str = "Asia/Shanghai") -> datetime:
    try:
        return datetime.now(ZoneInfo(tz_str)).replace(second=0, microsecond=0, tzinfo=None)
    except Exception:
        return datetime.now().replace(second=0, microsecond=0)


def normalize_gender(gender: str) -> str:
    value = str(gender or "").strip().lower()
    if not value:
        return ""
    if "男" in value:
        return "male"
    if "女" in value:
        return "female"
    if value in {"male", "man", "m", "boy"}:
        return "male"
    if value in {"female", "woman", "f", "girl"}:
        return "female"
    return ""


def pillar_from_indices(stem_index: int, branch_index: int) -> dict[str, Any]:
    stem = HEAVENLY_STEMS[stem_index % 10]
    branch = EARTHLY_BRANCHES[branch_index % 12]
    return {
        "stem": stem,
        "branch": branch,
        "text": f"{stem}{branch}",
        "stem_index": stem_index % 10,
        "branch_index": branch_index % 12,
        "element": STEM_ELEMENTS[stem],
        "polarity": STEM_POLARITY[stem],
        "hidden_stems": BRANCH_HIDDEN_STEMS[branch],
    }


def jd_to_datetime(jd: float) -> datetime:
    time = sxtwl.JD2DD(float(jd))
    base = datetime(int(time.Y), int(time.M), int(time.D), int(time.h), int(time.m), 0)
    return base + timedelta(seconds=round(float(time.s)))


def collect_jie_boundaries(year: int) -> list[dict[str, Any]]:
    seen: set[tuple[int, int]] = set()
    boundaries: list[dict[str, Any]] = []
    for target_year in (year - 1, year, year + 1):
        for item in sxtwl.getJieQiByYear(target_year):
            jq_index = int(item.jqIndex)
            if jq_index not in JIE_BOUNDARY_INDEXES:
                continue
            jd = float(item.jd)
            dedupe_key = (jq_index, int(round(jd * 1_000_000)))
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            boundaries.append(
                {
                    "name": JIEQI_NAMES.get(jq_index, str(jq_index)),
                    "index": jq_index,
                    "jd": jd,
                    "datetime": jd_to_datetime(jd),
                }
            )
    return sorted(boundaries, key=lambda item: item["datetime"])


def select_jie_boundary(chart_dt: datetime, forward: bool) -> dict[str, Any] | None:
    boundaries = collect_jie_boundaries(chart_dt.year)
    if forward:
        for boundary in boundaries:
            if boundary["datetime"] >= chart_dt:
                return boundary
        return None
    for boundary in reversed(boundaries):
        if boundary["datetime"] <= chart_dt:
            return boundary
    return None


def qiyun_offset(delta: timedelta) -> dict[str, Any]:
    total_days = max(delta.total_seconds(), 0.0) / 86400.0
    total_months = total_days * 4.0
    years = int(total_months // 12)
    remaining_months = total_months - years * 12
    months = int(remaining_months)
    days = int(round((remaining_months - months) * 30))

    if days >= 30:
        months += days // 30
        days = days % 30
    if months >= 12:
        years += months // 12
        months = months % 12

    return {
        "years": years,
        "months": months,
        "days": days,
        "age_years": round(years + months / 12 + days / 360, 2),
    }


def format_qiyun_age(offset: dict[str, Any]) -> str:
    parts = []
    years = int(offset.get("years", 0))
    months = int(offset.get("months", 0))
    days = int(offset.get("days", 0))
    if years:
        parts.append(f"{years}岁")
    if months:
        parts.append(f"{months}个月")
    if days:
        parts.append(f"{days}天")
    return "".join(parts) if parts else "出生即起运"


def add_years_months_days(dt: datetime, years: int = 0, months: int = 0, days: int = 0) -> datetime:
    month_cursor = (dt.month - 1) + years * 12 + months
    new_year = dt.year + month_cursor // 12
    new_month = month_cursor % 12 + 1
    new_day = min(dt.day, monthrange(new_year, new_month)[1])
    shifted = dt.replace(year=new_year, month=new_month, day=new_day)
    return shifted + timedelta(days=days)


def branch_relation_signals(target_branch: str, pillars: dict[str, dict[str, Any]]) -> list[str]:
    same_pillars = [
        f"{PILLAR_LABELS[name]}支"
        for name, pillar in pillars.items()
        if pillar.get("branch") == target_branch
    ]
    clash_pillars = [
        f"{PILLAR_LABELS[name]}支"
        for name, pillar in pillars.items()
        if BRANCH_CLASHES.get(str(pillar.get("branch") or "")) == target_branch
    ]

    signals = []
    if same_pillars:
        signals.append(f"与{'、'.join(same_pillars)}同气")
    if clash_pillars:
        signals.append(f"冲{'、'.join(clash_pillars)}")
    return signals


def dayun_direction(year_stem: str, gender: str) -> dict[str, Any] | None:
    normalized_gender = normalize_gender(gender)
    if not normalized_gender:
        return None

    is_yang_year = STEM_POLARITY[year_stem] == "阳"
    forward = (is_yang_year and normalized_gender == "male") or (
        not is_yang_year and normalized_gender == "female"
    )
    return {
        "normalized_gender": normalized_gender,
        "forward": forward,
        "label": "顺行" if forward else "逆行",
        "rule": "阳年男、阴年女顺行；阴年男、阳年女逆行。",
    }


def build_luck_cycle(
    chart_dt: datetime,
    pillars: dict[str, dict[str, Any]],
    day_master: str,
    gender: str,
    tz_str: str,
) -> dict[str, Any]:
    direction = dayun_direction(pillars["year"]["stem"], gender)
    if not direction:
        return {
            "available": False,
            "reason": "missing_gender",
            "cycles": [],
            "current_cycle": None,
        }

    boundary = select_jie_boundary(chart_dt, bool(direction["forward"]))
    if not boundary:
        return {
            "available": False,
            "reason": "jieqi_unavailable",
            "cycles": [],
            "current_cycle": None,
        }

    offset = qiyun_offset(abs(boundary["datetime"] - chart_dt))
    start_dt = add_years_months_days(
        chart_dt,
        years=int(offset["years"]),
        months=int(offset["months"]),
        days=int(offset["days"]),
    )
    reference_dt = current_reference_datetime(tz_str or "Asia/Shanghai")
    month_pillar = pillars["month"]
    current_cycle = None
    cycles: list[dict[str, Any]] = []
    cycle_start_dt = start_dt
    step = 1 if direction["forward"] else -1

    for index in range(1, 11):
        pillar = pillar_from_indices(
            int(month_pillar["stem_index"]) + step * index,
            int(month_pillar["branch_index"]) + step * index,
        )
        cycle_end_dt = add_years_months_days(cycle_start_dt, years=10)
        entry = {
            "index": index,
            "pillar": pillar,
            "pillar_text": pillar["text"],
            "ten_god": ten_god(day_master, pillar["stem"]),
            "branch_signals": branch_relation_signals(pillar["branch"], pillars),
            "start_age_years": round(float(offset["age_years"]) + (index - 1) * 10, 2),
            "end_age_years": round(float(offset["age_years"]) + index * 10, 2),
            "start_datetime": cycle_start_dt.isoformat(sep=" ", timespec="minutes"),
            "end_datetime": cycle_end_dt.isoformat(sep=" ", timespec="minutes"),
            "is_current": cycle_start_dt <= reference_dt < cycle_end_dt,
        }
        if entry["is_current"]:
            current_cycle = entry
        cycles.append(entry)
        cycle_start_dt = cycle_end_dt

    return {
        "available": True,
        "direction": "forward" if direction["forward"] else "backward",
        "direction_label": direction["label"],
        "gender": direction["normalized_gender"],
        "rule_basis": f"{direction['rule']} 起运换算按三天一岁、一天四个月、一个时辰十天折算。",
        "boundary": {
            "name": boundary["name"],
            "datetime": boundary["datetime"].isoformat(sep=" ", timespec="minutes"),
            "direction": "next" if direction["forward"] else "previous",
        },
        "start_age_years": float(offset["age_years"]),
        "start_age_text": format_qiyun_age(offset),
        "start_datetime": start_dt.isoformat(sep=" ", timespec="minutes"),
        "cycles": cycles,
        "current_cycle": current_cycle,
        "reference_datetime": reference_dt.isoformat(sep=" ", timespec="minutes"),
    }


def build_annual_cycles(
    day_master: str,
    pillars: dict[str, dict[str, Any]],
    reference_dt: datetime,
) -> dict[str, Any]:
    reference_year = reference_dt.year
    cycles: list[dict[str, Any]] = []
    current_year_cycle = None

    for year in range(reference_year - 2, reference_year + 5):
        pillar = ganzhi(sxtwl.fromSolar(year, 6, 15).getYearGZ())
        entry = {
            "year": year,
            "pillar": pillar,
            "pillar_text": pillar["text"],
            "ten_god": ten_god(day_master, pillar["stem"]),
            "branch_signals": branch_relation_signals(pillar["branch"], pillars),
            "is_current": year == reference_year,
        }
        if entry["is_current"]:
            current_year_cycle = entry
        cycles.append(entry)

    return {
        "available": True,
        "reference_year": reference_year,
        "rule_basis": "流年干支按节气年处理，采用每年年中日期提取该年的稳定年柱。",
        "cycles": cycles,
        "current_year": current_year_cycle,
    }


def build_monthly_cycles(
    day_master: str,
    pillars: dict[str, dict[str, Any]],
    reference_dt: datetime,
) -> dict[str, Any]:
    boundaries = collect_jie_boundaries(reference_dt.year)
    if len(boundaries) < 2:
        return {
            "available": False,
            "reason": "jieqi_unavailable",
            "cycles": [],
            "current_month": None,
        }

    current_interval_index = None
    for interval_index in range(len(boundaries) - 1):
        start_boundary = boundaries[interval_index]
        end_boundary = boundaries[interval_index + 1]
        if start_boundary["datetime"] <= reference_dt < end_boundary["datetime"]:
            current_interval_index = interval_index
            break

    if current_interval_index is None:
        current_interval_index = 0 if reference_dt < boundaries[0]["datetime"] else len(boundaries) - 2

    cycles: list[dict[str, Any]] = []
    current_month_cycle = None
    start_index = max(0, current_interval_index - 2)
    end_index = min(len(boundaries) - 2, current_interval_index + 4)

    for interval_index in range(start_index, end_index + 1):
        start_boundary = boundaries[interval_index]
        end_boundary = boundaries[interval_index + 1]
        probe_dt = start_boundary["datetime"] + (end_boundary["datetime"] - start_boundary["datetime"]) / 2
        pillar = ganzhi(sxtwl.fromSolar(probe_dt.year, probe_dt.month, probe_dt.day).getMonthGZ())
        entry = {
            "index": interval_index - start_index + 1,
            "offset_from_current": interval_index - current_interval_index,
            "gregorian_month": probe_dt.strftime("%Y-%m"),
            "window_label": f"{start_boundary['name']}~{end_boundary['name']}",
            "boundary_name": start_boundary["name"],
            "next_boundary_name": end_boundary["name"],
            "pillar": pillar,
            "pillar_text": pillar["text"],
            "ten_god": ten_god(day_master, pillar["stem"]),
            "branch_signals": branch_relation_signals(pillar["branch"], pillars),
            "start_datetime": start_boundary["datetime"].isoformat(sep=" ", timespec="minutes"),
            "end_datetime": end_boundary["datetime"].isoformat(sep=" ", timespec="minutes"),
            "is_current": interval_index == current_interval_index,
        }
        if entry["is_current"]:
            current_month_cycle = entry
        cycles.append(entry)

    return {
        "available": True,
        "reference_month": reference_dt.strftime("%Y-%m"),
        "reference_datetime": reference_dt.isoformat(sep=" ", timespec="minutes"),
        "rule_basis": "流月按节气切月处理，以当前所在节令区间及邻近数月提取稳定月柱。",
        "cycles": cycles,
        "current_month": current_month_cycle,
    }


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


def ten_god_group_counts(
    ten_gods: dict[str, str],
    hidden_ten_gods: dict[str, list[dict[str, str]]],
) -> dict[str, int]:
    direct_values = [str(value or "").strip() for value in ten_gods.values()]
    hidden_values = [
        str(item.get("ten_god") or "").strip()
        for values in hidden_ten_gods.values()
        if isinstance(values, list)
        for item in values
    ]
    all_values = direct_values + hidden_values
    return {
        "peer": sum(1 for value in all_values if value in {"比肩", "劫财"}),
        "output": sum(1 for value in all_values if value in {"食神", "伤官"}),
        "wealth": sum(1 for value in all_values if value in {"正财", "偏财"}),
        "officer": sum(1 for value in all_values if value in {"正官", "七杀"}),
        "resource": sum(1 for value in all_values if value in {"正印", "偏印"}),
    }


def identify_pattern_profile(
    day_master: str,
    strength: str,
    pillars: dict[str, dict[str, Any]],
    ten_gods: dict[str, str],
    hidden_ten_gods: dict[str, list[dict[str, str]]],
    favorable: dict[str, list[str]],
) -> dict[str, Any]:
    month_ten_god = str(ten_gods.get("month") or "").strip()
    group_counts = ten_god_group_counts(ten_gods, hidden_ten_gods)
    order = sorted(group_counts.items(), key=lambda item: item[1], reverse=True)
    primary_group = order[0][0] if order and order[0][1] > 0 else ""
    secondary_group = order[1][0] if len(order) > 1 and order[1][1] > 0 else ""
    month_branch = str((pillars.get("month") or {}).get("branch") or "")
    month_season = SEASON_BY_MONTH_BRANCH.get(month_branch, "")

    primary_label_map = {
        "peer": "比劫主轴",
        "output": "食伤主轴",
        "wealth": "财星主轴",
        "officer": "官杀主轴",
        "resource": "印星主轴",
    }
    month_label_map = {
        "比肩": "比肩格倾向",
        "劫财": "劫财格倾向",
        "食神": "食神格倾向",
        "伤官": "伤官格倾向",
        "正财": "正财格倾向",
        "偏财": "偏财格倾向",
        "正官": "正官格倾向",
        "七杀": "七杀格倾向",
        "正印": "正印格倾向",
        "偏印": "偏印格倾向",
    }
    structure_map = {
        "strong": "身强",
        "weak": "身弱",
        "balanced": "中和",
    }

    pattern_name = month_label_map.get(month_ten_god) or primary_label_map.get(primary_group) or "常规格局"
    structure = structure_map.get(strength, "中和")

    if strength == "strong":
        strategy = "宜泄、宜耗、宜财官，不宜再叠比印。"
    elif strength == "weak":
        strategy = "宜扶、宜印、宜比，不宜财官太重来压身。"
    else:
        strategy = "以流通为先，取输出、资源与现实兑现的平衡。"

    evidence = [
        f"月令十神落在{month_ten_god or '未明'}",
        f"月支节令在{month_season or '未明'}季",
    ]
    if primary_group:
        evidence.append(f"全盘十神重心偏向{primary_label_map.get(primary_group, primary_group)}")
    if secondary_group:
        evidence.append(f"次重心落在{primary_label_map.get(secondary_group, secondary_group)}")

    summary = (
        f"这盘先按{structure}{pattern_name}来看，月令主轴落在{month_ten_god or '未明'}，"
        f"全盘更偏向{primary_label_map.get(primary_group, '多轴并行')}的运作方式。{strategy}"
    )
    if favorable.get("favorable"):
        summary += f" 现阶段顺手的发力方向更偏{('、'.join(favorable['favorable']))}。"

    return {
        "pattern_name": pattern_name,
        "structure": structure,
        "month_ten_god": month_ten_god,
        "primary_axis": primary_group,
        "secondary_axis": secondary_group,
        "axis_counts": group_counts,
        "summary": summary,
        "strategy": strategy,
        "evidence": evidence,
    }


def build_yongshen_profile(
    day_master: str,
    strength: str,
    favorable: dict[str, list[str]],
    pattern_profile: dict[str, Any],
) -> dict[str, Any]:
    element = STEM_ELEMENTS[day_master]
    favorable_elements = list(favorable.get("favorable") or [])
    caution_elements = list(favorable.get("caution") or [])

    if strength == "strong":
        priority_reason = "日主偏强，先取泄耗财官来导流，避免火木继续堆高。"
        action_advice = "行动上更适合把输出、成交、规则、责任和结果感拉到台前。"
    elif strength == "weak":
        priority_reason = "日主偏弱，先扶身护身，再谈财官与结果压力。"
        action_advice = "行动上先补资源、方法、支持与稳定性，再放大竞争和兑现。"
    else:
        priority_reason = "整体中和，以流通和不过载为先。"
        action_advice = "行动上要兼顾输出、资源与现实收益，不宜单边用力。"

    summary = (
        f"首版用神方向先按{pattern_profile.get('structure') or '中和'}盘处理，"
        f"优先元素偏向{('、'.join(favorable_elements) or '未明')}，"
        f"少硬扛的方向偏在{('、'.join(caution_elements) or '未明')}。{priority_reason}"
    )

    return {
        "day_master_element": element,
        "favorable_elements": favorable_elements,
        "caution_elements": caution_elements,
        "priority_reason": priority_reason,
        "action_advice": action_advice,
        "summary": summary,
    }


def build_pattern_conditions(
    pattern_profile: dict[str, Any],
    yongshen_profile: dict[str, Any],
    strongest: list[tuple[str, int]],
    weakest: list[str],
) -> dict[str, Any]:
    primary_axis = str(pattern_profile.get("primary_axis") or "").strip()
    favorable_elements = list(yongshen_profile.get("favorable_elements") or [])
    caution_elements = list(yongshen_profile.get("caution_elements") or [])
    strongest_elements = [item[0] for item in strongest if strongest and item[1] == strongest[0][1]]

    success_conditions: list[str] = []
    risk_conditions: list[str] = []

    if primary_axis == "wealth":
        success_conditions.append("把资源、客户、项目和现金流收进稳定结构里，格局更容易成。")
        risk_conditions.append("只追短平快、边界散、回款慢时，财来财去会更明显。")
    elif primary_axis == "output":
        success_conditions.append("持续输出方案、内容、判断和结果，格局更容易被盘活。")
        risk_conditions.append("只说不落地，或者频繁换题，食伤的优势会被冲散。")
    elif primary_axis == "officer":
        success_conditions.append("站进职责清晰、规则明确、结果可衡量的位置，格局更容易立住。")
        risk_conditions.append("长期处在无边界、无规则、全靠临场救火的环境里，官杀力会被拖弱。")
    elif primary_axis == "resource":
        success_conditions.append("先把资源、方法、学习和支持系统补稳，格局更容易顺起来。")
        risk_conditions.append("准备没补够就硬扛结果，印星的保护力会不够用。")
    else:
        success_conditions.append("把自主性变成稳定主线，而不是四处分神，格局才容易成。")
        risk_conditions.append("人情、合伙、分功和情绪介入过多时，比劫容易把成果冲散。")

    if favorable_elements:
        success_conditions.append(f"环境和动作多往{('、'.join(favorable_elements))}这类元素对应的路径走，会更顺手。")
    if caution_elements:
        risk_conditions.append(f"{('、'.join(caution_elements))}过旺时，容易把原盘的失衡再推高。")
    if "水" in weakest:
        risk_conditions.append("现金流、恢复力和缓冲带偏薄时，最怕节奏过满又不给自己留余地。")
    if "火" in strongest_elements:
        risk_conditions.append("火势过旺时容易快决策、快投入，越顺的时候越要防用力过头。")

    summary = (
        f"这类格局的成局点更在于{success_conditions[0]}"
        f" 破局点则常见于{risk_conditions[0]}"
    )

    return {
        "success_conditions": success_conditions,
        "risk_conditions": risk_conditions,
        "summary": summary,
    }


def build_timing_linkage(
    day_master: str,
    yongshen_profile: dict[str, Any],
    current_cycle: dict[str, Any] | None,
    current_year: dict[str, Any] | None,
    current_month: dict[str, Any] | None,
) -> dict[str, Any]:
    favorable_elements = set(yongshen_profile.get("favorable_elements") or [])
    caution_elements = set(yongshen_profile.get("caution_elements") or [])

    def classify(entry: dict[str, Any] | None, label: str) -> dict[str, Any] | None:
        if not isinstance(entry, dict) or not entry:
            return None
        pillar = entry.get("pillar") or {}
        stem = str(pillar.get("stem") or "")
        branch = str(pillar.get("branch") or "")
        stem_element = STEM_ELEMENTS.get(stem, "")
        branch_hidden = BRANCH_HIDDEN_STEMS.get(branch, [])
        branch_elements = [STEM_ELEMENTS.get(item, "") for item in branch_hidden if STEM_ELEMENTS.get(item, "")]
        matched_favorable = [element for element in [stem_element] + branch_elements if element in favorable_elements]
        matched_caution = [element for element in [stem_element] + branch_elements if element in caution_elements]
        support_level = "neutral"
        if matched_favorable and not matched_caution:
            support_level = "supportive"
        elif matched_caution and not matched_favorable:
            support_level = "challenging"
        elif matched_favorable and matched_caution:
            support_level = "mixed"

        if support_level == "supportive":
            message = f"{label}更在托举用神，适合推进结果、定方向、把握兑现。"
        elif support_level == "challenging":
            message = f"{label}更容易把原盘压力点翻出来，适合收边界、控节奏、防透支。"
        elif support_level == "mixed":
            message = f"{label}有助推也有牵扯，适合边做边校正，不宜一把压满。"
        else:
            message = f"{label}对原盘既不算明显加分，也不算明显拖后腿，更看你怎么用力。"

        return {
            "label": label,
            "pillar_text": str(entry.get("pillar_text") or ""),
            "ten_god": str(entry.get("ten_god") or ""),
            "support_level": support_level,
            "favorable_matches": matched_favorable,
            "caution_matches": matched_caution,
            "message": message,
        }

    decadal = classify(current_cycle, "当前大运")
    yearly = classify(current_year, "当前流年")
    monthly = classify(current_month, "当前流月")
    messages = [item["message"] for item in (decadal, yearly, monthly) if isinstance(item, dict) and item.get("message")]

    summary = " ".join(messages).strip() or "当前时运联动信息暂不完整。"
    return {
        "decadal": decadal,
        "yearly": yearly,
        "monthly": monthly,
        "summary": summary,
    }


def build_theme_guidance(
    day_master: str,
    strength: str,
    overview: dict[str, str],
    pattern_profile: dict[str, Any],
    pattern_conditions: dict[str, Any],
    yongshen_profile: dict[str, Any],
    timing_linkage: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    favorable_elements = list(yongshen_profile.get("favorable_elements") or [])
    caution_elements = list(yongshen_profile.get("caution_elements") or [])
    success_conditions = list(pattern_conditions.get("success_conditions") or [])
    risk_conditions = list(pattern_conditions.get("risk_conditions") or [])
    decadal = timing_linkage.get("decadal") or {}
    yearly = timing_linkage.get("yearly") or {}
    monthly = timing_linkage.get("monthly") or {}

    def timing_focus() -> str:
        picked = []
        for item in (decadal, yearly, monthly):
            if not isinstance(item, dict) or not item:
                continue
            pillar = str(item.get("pillar_text") or "").strip()
            support = str(item.get("support_level") or "").strip()
            label = str(item.get("label") or "").strip()
            if label and pillar and support:
                picked.append(f"{label}{pillar}偏{support}")
        return "；".join(picked[:3])

    themes: dict[str, dict[str, Any]] = {
        "career": {
            "summary": str(overview.get("career") or "").strip(),
            "favorable_points": [
                "把职责、结果、表达和资源兑现放进同一条主线里。",
                success_conditions[0] if success_conditions else "",
                f"多借{('、'.join(favorable_elements))}这类元素对应的路径发力。" if favorable_elements else "",
            ],
            "risk_points": [
                risk_conditions[0] if risk_conditions else "",
                "别一边冲主业一边把太多副线同时拉满。",
                f"{('、'.join(caution_elements))}过旺时，最怕上头硬推。" if caution_elements else "",
            ],
            "timing_note": timing_focus(),
        },
        "wealth": {
            "summary": str(overview.get("wealth") or "").strip(),
            "favorable_points": [
                "收入更适合靠结构化经营，而不是只赌单点机会。",
                "先稳回款、边界和现金流，再放大规模。",
                success_conditions[1] if len(success_conditions) > 1 else "",
            ],
            "risk_points": [
                "合伙、人情、垫资和分流要一直防。",
                risk_conditions[1] if len(risk_conditions) > 1 else "",
                "节奏越热的时候，越要保留缓冲。",
            ],
            "timing_note": timing_focus(),
        },
        "relationship": {
            "summary": str(overview.get("relationship") or "").strip(),
            "favorable_points": [
                "更适合慢热筛选，先看边界、责任感和现实配合。",
                "能一起处理现实问题的人，匹配度更高。",
                "留出沟通和磨合空间，关系反而更容易稳。",
            ],
            "risk_points": [
                "第三方意见过多时，最容易把关系节奏带偏。",
                "情绪上头抢结论，会把原本能谈开的事谈硬。",
                "别把事业或现金流压力直接倒进关系里。",
            ],
            "timing_note": timing_focus(),
        },
        "health": {
            "summary": str(overview.get("health") or "").strip(),
            "favorable_points": [
                "先调节节奏、恢复力和日常消耗结构。",
                "越忙的时候越要把睡眠、休息和恢复放进安排里。",
                f"多往{('、'.join(favorable_elements))}的补偏方向做生活管理。" if favorable_elements else "",
            ],
            "risk_points": [
                "过劳、急推进、长期不收边界时，身体最容易先响铃。",
                f"{('、'.join(caution_elements))}偏旺时，更要防透支。" if caution_elements else "",
                "这部分只作命理提醒，不替代医疗判断。",
            ],
            "timing_note": timing_focus(),
        },
        "direction": {
            "summary": str(overview.get("direction") or "").strip(),
            "favorable_points": [
                f"先按{pattern_profile.get('structure') or '中和'}{pattern_profile.get('pattern_name') or '常规格'}的逻辑走主线。",
                "把主观能动性、表达输出和现实结果串成长期路径。",
                str(yongshen_profile.get("action_advice") or "").strip(),
            ],
            "risk_points": [
                "别频繁换赛道、换身份、换打法。",
                risk_conditions[0] if risk_conditions else "",
                "一旦分神太多，原盘优势就会被冲淡。",
            ],
            "timing_note": timing_focus(),
        },
    }

    for item in themes.values():
        item["favorable_points"] = [text for text in item["favorable_points"] if text]
        item["risk_points"] = [text for text in item["risk_points"] if text]
        item["timing_note"] = str(item.get("timing_note") or "").strip()
    return themes


def build_career_decision_guidance(
    ten_gods: dict[str, str],
    hidden_ten_gods: dict[str, list[dict[str, str]]],
    strongest: list[tuple[str, int]],
    weakest: list[str],
    theme_guidance: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    def clean_text(value: Any) -> str:
        return str(value or "").strip()

    counts = ten_god_group_counts(ten_gods, hidden_ten_gods)
    career_theme = theme_guidance.get("career") or {}
    direction_theme = theme_guidance.get("direction") or {}

    scores = {
        "上班": 0,
        "自由职业": 0,
        "创业": 0,
        "自己接项目": 0,
        "咨询": 0,
        "销售": 0,
    }

    if counts.get("officer", 0) >= 1:
        scores["上班"] += 3
        scores["销售"] += 1
    if counts.get("output", 0) >= 2:
        scores["自由职业"] += 3
        scores["咨询"] += 3
        scores["自己接项目"] += 1
    if counts.get("wealth", 0) >= 2:
        scores["销售"] += 2
        scores["创业"] += 1
        scores["自己接项目"] += 1
    if counts.get("peer", 0) >= 3:
        scores["创业"] -= 2
        scores["自己接项目"] -= 2
        scores["上班"] += 1
    if "火" in [item[0] for item in strongest if strongest and item[1] == strongest[0][1]]:
        scores["创业"] -= 1
        scores["自由职业"] += 1
    if "木" in weakest:
        scores["创业"] -= 1
        scores["自己接项目"] -= 1
        scores["上班"] += 1

    mode_order = sorted(
        ["上班", "自由职业", "创业", "自己接项目"],
        key=lambda item: (scores.get(item, 0), item),
        reverse=True,
    )
    style_order = sorted(
        ["咨询", "销售", "自己接项目"],
        key=lambda item: (scores.get(item, 0), item),
        reverse=True,
    )

    primary_mode = mode_order[0]
    secondary_mode = mode_order[1]
    avoid_mode = mode_order[-1]

    if primary_mode == "上班":
        summary = "职业主线更适合先借平台、岗位和明确责任位做出结果，再逐步扩展独立性。"
    elif primary_mode == "自由职业":
        summary = "职业主线更适合先把个人输出、方法和口碑做成稳定邀约，再决定要不要放大成更重模式。"
    else:
        summary = "职业主线更适合先用结果验证路径，但不要一开始就把全部变量压满。"

    avoid_reason = {
        "创业": "创业目前更像后置题，太早会把资源、关系和节奏压力一起抬上来。",
        "自己接项目": "自己接项目更容易卡在客户来源、交付边界和回款节奏上。",
        "自由职业": "自由职业若太早切主线，容易先遇到稳定度不够的问题。",
        "上班": "上班不是不能做，但如果完全只靠被安排，盘里的主动输出会被压住。",
    }.get(avoid_mode, "")

    sequencing = [
        f"更适合先走{primary_mode}主线，再把{secondary_mode}当过渡或第二阶段。",
        "先把稳定结果、信用和方法沉淀出来，再决定是否放大不确定性。",
        clean_text(career_theme.get("timing_note") or ""),
    ]

    return {
        "scores": scores,
        "mode_order": mode_order,
        "style_order": style_order,
        "primary_mode": primary_mode,
        "secondary_mode": secondary_mode,
        "avoid_mode": avoid_mode,
        "summary": summary,
        "avoid_reason": avoid_reason,
        "sequencing": [item for item in sequencing if item],
        "career_summary": clean_text(career_theme.get("summary") or ""),
        "direction_summary": clean_text(direction_theme.get("summary") or ""),
    }


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
    pattern_profile = identify_pattern_profile(day_master, strength, pillars, ten_gods, hidden_ten_gods, favorable)
    yongshen_profile = build_yongshen_profile(day_master, strength, favorable, pattern_profile)
    tz_str = resolved_location.tz_str if resolved_location else "Asia/Shanghai"
    reference_dt = current_reference_datetime(tz_str)
    luck_cycle = build_luck_cycle(chart_dt, pillars, day_master, data.gender, tz_str)
    annual_cycles = build_annual_cycles(day_master, pillars, reference_dt)
    monthly_cycles = build_monthly_cycles(day_master, pillars, reference_dt)

    risk_flags = []
    if not data.birth_location:
        risk_flags.append("未提供出生地，当前没有做真太阳时修正。")
    elif unresolved_location:
        risk_flags.append("出生地未能解析为本地城市库条目，当前未做真太阳时修正。")
    if not data.gender:
        risk_flags.append("未提供性别，当前不计算大运顺逆与起运。")
    elif not luck_cycle.get("available"):
        risk_flags.append("大运层未能完整起出，当前只保留本命结构与流年参考。")
    if dt.hour == 23 and not data.late_zi_hour_next_day:
        risk_flags.append("23点子时存在早晚子时流派差异，本次按同一公历日处理。")
    if resolved_location and resolved_location.approximate:
        risk_flags.append("出生地按区域级别近似解析，真太阳时修正只能视作近似值。")
    risk_flags.append("大运起运按常用三天一岁口径折算，具体门派若采用别的换算规则，起运时点会有小幅差异。")
    if not monthly_cycles.get("available"):
        risk_flags.append("流月层未能完整起出，当前只保留本命结构、大运与流年参考。")

    summary_note = "当前已能完成排盘、五行、十神、多维总评、首版格局倾向与用神方向，以及首版大运顺逆、起运、当前大运、流年与流月。"
    if not luck_cycle.get("available"):
        summary_note = "当前已能完成排盘、五行、十神、多维总评、首版格局倾向与用神方向，以及当前流年、流月层；大运顺逆和起运仍依赖性别等信息补齐后再落全。"

    current_cycle = luck_cycle.get("current_cycle") if isinstance(luck_cycle, dict) else None
    current_year = annual_cycles.get("current_year") if isinstance(annual_cycles, dict) else None
    current_month = monthly_cycles.get("current_month") if isinstance(monthly_cycles, dict) else None
    pattern_conditions = build_pattern_conditions(pattern_profile, yongshen_profile, strongest, weakest)
    timing_linkage = build_timing_linkage(day_master, yongshen_profile, current_cycle, current_year, current_month)
    theme_guidance = build_theme_guidance(
        day_master,
        strength,
        overview,
        pattern_profile,
        pattern_conditions,
        yongshen_profile,
        timing_linkage,
    )
    career_decision = build_career_decision_guidance(
        ten_gods,
        hidden_ten_gods,
        strongest,
        weakest,
        theme_guidance,
    )

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
        "pattern_profile": pattern_profile,
        "pattern_conditions": pattern_conditions,
        "yongshen_profile": yongshen_profile,
        "theme_guidance": theme_guidance,
        "career_decision": career_decision,
        "luck_cycle": luck_cycle,
        "dayun": luck_cycle.get("cycles", []) if isinstance(luck_cycle, dict) else [],
        "annual_cycles": annual_cycles,
        "liunian": annual_cycles.get("cycles", []) if isinstance(annual_cycles, dict) else [],
        "monthly_cycles": monthly_cycles,
        "liuyue": monthly_cycles.get("cycles", []) if isinstance(monthly_cycles, dict) else [],
        "timing_linkage": timing_linkage,
        "current_cycles": {
            "decadal": current_cycle,
            "yearly": current_year,
            "monthly": current_month,
            "reference_datetime": reference_dt.isoformat(sep=" ", timespec="minutes"),
        },
        "overview": overview,
        "summary": {
            "strongest_elements": [item[0] for item in strongest if item[1] == strongest[0][1]],
            "weakest_elements": weakest,
            "note": summary_note,
            "has_decadal_timing": bool(luck_cycle.get("available")),
            "current_dayun": current_cycle.get("pillar_text", "") if isinstance(current_cycle, dict) else "",
            "current_liunian": current_year.get("pillar_text", "") if isinstance(current_year, dict) else "",
            "current_liuyue": current_month.get("pillar_text", "") if isinstance(current_month, dict) else "",
            "pattern_name": pattern_profile.get("pattern_name") or "",
            "structure": pattern_profile.get("structure") or "",
            "yongshen_summary": yongshen_profile.get("summary") or "",
            "pattern_conditions_summary": pattern_conditions.get("summary") or "",
            "timing_linkage_summary": timing_linkage.get("summary") or "",
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
