from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass(frozen=True)
class NumerologyInput:
    birth_date: date
    name: str = ""
    system: str = "pythagorean"


PYTHAGOREAN_VALUES = {
    **dict.fromkeys(list("AJS"), 1),
    **dict.fromkeys(list("BKT"), 2),
    **dict.fromkeys(list("CLU"), 3),
    **dict.fromkeys(list("DMV"), 4),
    **dict.fromkeys(list("ENW"), 5),
    **dict.fromkeys(list("FOX"), 6),
    **dict.fromkeys(list("GPY"), 7),
    **dict.fromkeys(list("HQZ"), 8),
    **dict.fromkeys(list("IR"), 9),
}


def reduce_number(value: int, keep_master: bool = True) -> int:
    if keep_master and value in {11, 22, 33}:
        return value
    while value > 9:
        value = sum(int(char) for char in str(value))
        if keep_master and value in {11, 22, 33}:
            return value
    return value


def name_number(name: str) -> int | None:
    total = 0
    for char in name.upper():
        total += PYTHAGOREAN_VALUES.get(char, 0)
    return reduce_number(total) if total else None


def calculate_numerology(data: NumerologyInput) -> dict[str, Any]:
    digits = [int(char) for char in data.birth_date.strftime("%Y%m%d")]
    life_path_raw = sum(digits)
    birth_day = reduce_number(data.birth_date.day)
    personal_year = reduce_number(sum(int(char) for char in str(date.today().year)) + data.birth_date.month + data.birth_date.day)
    expression = name_number(data.name)
    risk_flags = [
        "数字命理属于象征和轻量画像系统，不应作为重大现实决策的唯一依据。"
    ]
    if data.name and expression is None:
        risk_flags.append("当前姓名数字只支持拉丁字母；中文姓名需要另接笔画或拼音口径。")
    return {
        "system": "numerology",
        "input": {
            "birth_date": data.birth_date.isoformat(),
            "name": data.name,
            "numerology_system": data.system,
        },
        "derived_factors": {
            "life_path_raw": life_path_raw,
            "life_path": reduce_number(life_path_raw),
            "birth_day_number": birth_day,
            "personal_year": personal_year,
            "expression_number": expression,
        },
        "missing_inputs": [],
        "risk_flags": risk_flags,
        "confidence": "medium",
    }
