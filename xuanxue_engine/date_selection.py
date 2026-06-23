from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import sxtwl


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
BRANCH_CLASH = {
    "\u5b50": "\u5348",
    "\u4e11": "\u672a",
    "\u5bc5": "\u7533",
    "\u536f": "\u9149",
    "\u8fb0": "\u620c",
    "\u5df3": "\u4ea5",
    "\u5348": "\u5b50",
    "\u672a": "\u4e11",
    "\u7533": "\u5bc5",
    "\u9149": "\u536f",
    "\u620c": "\u8fb0",
    "\u4ea5": "\u5df3",
}
BRANCH_HARMONY = {
    "\u5b50": "\u4e11",
    "\u4e11": "\u5b50",
    "\u5bc5": "\u4ea5",
    "\u4ea5": "\u5bc5",
    "\u536f": "\u620c",
    "\u620c": "\u536f",
    "\u8fb0": "\u9149",
    "\u9149": "\u8fb0",
    "\u5df3": "\u7533",
    "\u7533": "\u5df3",
    "\u5348": "\u672a",
    "\u672a": "\u5348",
}
WEEKDAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
EVENT_ELEMENT_PREFERENCE = {
    "move": {"earth": 3, "water": 1, "fire": -1},
    "wedding": {"earth": 2, "water": 2, "metal": 1},
    "contract": {"metal": 3, "water": 2},
    "travel": {"water": 3, "wood": 2},
    "general": {},
}

ELEMENT_NAME_MAP = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}

WEEKDAY_NAME_MAP = {
    "Mon": "周一",
    "Tue": "周二",
    "Wed": "周三",
    "Thu": "周四",
    "Fri": "周五",
    "Sat": "周六",
    "Sun": "周日",
}


@dataclass(frozen=True)
class DateSelectionInput:
    event_type: str
    candidate_dates: tuple[date, ...]
    location: str = ""
    participant_birth_dates: tuple[date, ...] = ()


def normalize_event_type(value: str) -> str:
    text = (value or "").strip().lower()
    aliases = {
        "moving": "move",
        "move_house": "move",
        "relocation": "move",
        "\u642c\u5bb6": "move",
        "\u5165\u5b85": "move",
        "\u7ed3\u5a5a": "wedding",
        "\u5a5a\u793c": "wedding",
        "marriage": "wedding",
        "signing": "contract",
        "contract": "contract",
        "\u7b7e\u7ea6": "contract",
        "\u7b7e\u5408\u540c": "contract",
        "\u51fa\u884c": "travel",
        "travel": "travel",
    }
    return aliases.get(text, text or "general")


def gz_text(gz: Any) -> str:
    return f"{HEAVENLY_STEMS[gz.tg]}{EARTHLY_BRANCHES[gz.dz]}"


def inspect_date(candidate: date) -> dict[str, Any]:
    day = sxtwl.fromSolar(candidate.year, candidate.month, candidate.day)
    year_gz = day.getYearGZ()
    month_gz = day.getMonthGZ()
    day_gz = day.getDayGZ()
    stem = HEAVENLY_STEMS[day_gz.tg]
    branch = EARTHLY_BRANCHES[day_gz.dz]
    return {
        "date": candidate.isoformat(),
        "weekday": WEEKDAY_NAMES[candidate.weekday()],
        "lunar": {
            "year": day.getLunarYear(),
            "month": day.getLunarMonth(),
            "day": day.getLunarDay(),
            "is_leap_month": bool(day.isLunarLeap()),
        },
        "ganzhi": {
            "year": gz_text(year_gz),
            "month": gz_text(month_gz),
            "day": gz_text(day_gz),
        },
        "day_stem": stem,
        "day_branch": branch,
        "day_element": STEM_ELEMENTS[stem],
        "has_jieqi": bool(day.hasJieQi()),
    }


def participant_branch(value: date) -> str:
    day = sxtwl.fromSolar(value.year, value.month, value.day)
    return EARTHLY_BRANCHES[day.getYearGZ().dz]


def weekday_bonus(event_type: str, weekday: str) -> int:
    if event_type == "contract":
        return 2 if weekday in {"Tue", "Wed", "Thu"} else -1 if weekday in {"Sat", "Sun"} else 1
    if event_type in {"move", "wedding"}:
        return 1 if weekday in {"Sat", "Sun"} else 0
    if event_type == "travel":
        return 1 if weekday in {"Wed", "Thu", "Fri"} else 0
    return 0


def score_candidate(event_type: str, candidate: dict[str, Any], participant_branches: list[str]) -> tuple[int, list[str]]:
    score = 50
    notes: list[str] = []

    element_pref = EVENT_ELEMENT_PREFERENCE.get(event_type, {})
    element_delta = element_pref.get(candidate["day_element"], 0)
    score += element_delta
    if element_delta:
        notes.append(f"day element {candidate['day_element']} matches event weighting {element_delta:+d}")

    for branch in participant_branches:
        if candidate["day_branch"] == BRANCH_CLASH[branch]:
            score -= 18
            notes.append(f"day branch clashes participant year branch {branch}")
        elif candidate["day_branch"] == BRANCH_HARMONY[branch]:
            score += 10
            notes.append(f"day branch harmonizes with participant year branch {branch}")

    weekday_delta = weekday_bonus(event_type, candidate["weekday"])
    score += weekday_delta
    if weekday_delta:
        notes.append(f"weekday practicality adjustment {weekday_delta:+d}")

    if candidate["has_jieqi"]:
        score -= 2
        notes.append("solar-term boundary day; treat transitions with more caution")

    return score, notes


def translate_note(note: str) -> str:
    text = str(note or "").strip()
    if not text:
        return ""
    if text.startswith("day element "):
        parts = text.split()
        if len(parts) >= 6:
            element = ELEMENT_NAME_MAP.get(parts[2], parts[2])
            delta = parts[-1]
            return f"日主五行偏{element}，与事项权重匹配 {delta}"
    if text.startswith("day branch clashes participant year branch "):
        branch = text.rsplit(" ", 1)[-1]
        return f"日支与参与者年支{branch}相冲"
    if text.startswith("day branch harmonizes with participant year branch "):
        branch = text.rsplit(" ", 1)[-1]
        return f"日支与参与者年支{branch}相合"
    if text.startswith("weekday practicality adjustment "):
        delta = text.rsplit(" ", 1)[-1]
        return f"周内安排便利度修正 {delta}"
    if text == "solar-term boundary day; treat transitions with more caution":
        return "节气交界日，切换气较重，宜多留缓冲"
    return text


def calculate_date_selection(data: DateSelectionInput) -> dict[str, Any]:
    event_type = normalize_event_type(data.event_type)
    participant_branches = [participant_branch(item) for item in data.participant_birth_dates]

    ranked = []
    for item in data.candidate_dates:
        inspected = inspect_date(item)
        score, notes = score_candidate(event_type, inspected, participant_branches)
        ranked.append({"score": score, "notes": notes, **inspected})
    ranked.sort(key=lambda entry: entry["score"], reverse=True)

    best = ranked[0]
    verdict = "auspicious" if best["score"] >= 54 else "mixed" if best["score"] >= 48 else "cautious"
    verdict_text = {
        "auspicious": "按当前本地历法规则看，这一天相对偏吉。",
        "mixed": "按当前本地历法规则看，这一天中平可用，但不算明显偏吉。",
        "cautious": "按当前本地历法规则看，这一天不算特别有利。",
    }[verdict]
    supporting = [
        f"{entry['date']} -> {entry['score']}（{'；'.join(translate_note(item) for item in entry['notes']) if entry['notes'] else '中性规则组合'}）"
        for entry in ranked
    ]

    risk_flags = [
        "This local date-selection engine ranks dates by calendrical structure, clash/harmony, and practical timing rules only.",
        "A full Huangli-style shensha layer is not bundled yet, so this result should be treated as a strong shortlist, not as a final oracle.",
    ]
    if not participant_branches:
        risk_flags.append("No participant birth data was supplied, so personal compatibility weighting was skipped.")

    return {
        "system": "date_selection",
        "question_type": event_type,
        "used_inputs": {
            "event_type": event_type,
            "candidate_dates": [item.isoformat() for item in data.candidate_dates],
            "location": data.location,
            "participant_birth_dates": [item.isoformat() for item in data.participant_birth_dates],
        },
        "missing_inputs": [],
        "derived_factors": {
            "ranked_candidates": ranked,
            "participant_year_branches": participant_branches,
            "verdict": verdict,
        },
        "primary_finding": f"候选日期里排名最高的是 {best['date']}，得分为 {best['score']}。{verdict_text}",
        "supporting_signals": supporting,
        "risk_flags": risk_flags,
        "time_window": "Compare the top 1-3 ranked dates against real-world logistics before final commitment.",
        "confidence": "medium" if participant_branches else "low",
        "rules_path": [
            "calendar normalization",
            "event-type weighting",
            "branch clash/harmony",
            "weekday practicality",
        ],
    }
