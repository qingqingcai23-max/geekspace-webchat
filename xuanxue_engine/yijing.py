from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
from typing import Any


TRIGRAM_BY_NUMBER = {
    1: ("qian", "Qian", (1, 1, 1), "heaven"),
    2: ("dui", "Dui", (1, 1, 0), "lake"),
    3: ("li", "Li", (1, 0, 1), "fire"),
    4: ("zhen", "Zhen", (1, 0, 0), "thunder"),
    5: ("xun", "Xun", (0, 1, 1), "wind"),
    6: ("kan", "Kan", (0, 1, 0), "water"),
    7: ("gen", "Gen", (0, 0, 1), "mountain"),
    8: ("kun", "Kun", (0, 0, 0), "earth"),
}

TRIGRAM_BY_LINES = {value[2]: {"key": value[0], "name": value[1], "image": value[3]} for value in TRIGRAM_BY_NUMBER.values()}

HEXAGRAM_NAMES = {
    ("Qian", "Qian"): "Force",
    ("Kun", "Kun"): "Field",
    ("Kan", "Zhen"): "Sprouting",
    ("Gen", "Kan"): "Enveloping",
    ("Kan", "Qian"): "Attending",
    ("Qian", "Kan"): "Arguing",
    ("Kun", "Kan"): "Leading",
    ("Kan", "Kun"): "Grouping",
    ("Xun", "Qian"): "Small Accumulating",
    ("Qian", "Dui"): "Treading",
    ("Kun", "Qian"): "Pervading",
    ("Qian", "Kun"): "Obstruction",
    ("Qian", "Li"): "Concording People",
    ("Li", "Qian"): "Great Possessing",
    ("Kun", "Gen"): "Humbling",
    ("Zhen", "Kun"): "Providing For",
    ("Dui", "Zhen"): "Following",
    ("Gen", "Xun"): "Correcting",
    ("Kun", "Dui"): "Nearing",
    ("Xun", "Kun"): "Viewing",
    ("Li", "Zhen"): "Gnawing Bite",
    ("Gen", "Li"): "Adorning",
    ("Gen", "Kun"): "Stripping",
    ("Kun", "Zhen"): "Returning",
    ("Qian", "Zhen"): "Without Embroiling",
    ("Gen", "Qian"): "Great Accumulating",
    ("Gen", "Zhen"): "Swallowing",
    ("Dui", "Xun"): "Great Exceeding",
    ("Kan", "Kan"): "Gorge",
    ("Li", "Li"): "Radiance",
    ("Dui", "Gen"): "Conjoining",
    ("Zhen", "Xun"): "Persevering",
    ("Qian", "Gen"): "Retiring",
    ("Zhen", "Qian"): "Great Invigorating",
    ("Li", "Kun"): "Prospering",
    ("Kun", "Li"): "Brightness Hiding",
    ("Xun", "Li"): "Dwelling People",
    ("Li", "Dui"): "Polarising",
    ("Kan", "Gen"): "Limping",
    ("Zhen", "Kan"): "Taking Apart",
    ("Gen", "Dui"): "Diminishing",
    ("Xun", "Zhen"): "Augmenting",
    ("Dui", "Qian"): "Parting",
    ("Qian", "Xun"): "Coupling",
    ("Dui", "Kun"): "Clustering",
    ("Kun", "Xun"): "Ascending",
    ("Dui", "Kan"): "Confining",
    ("Kan", "Xun"): "Welling",
    ("Dui", "Li"): "Skinning",
    ("Li", "Xun"): "Holding",
    ("Zhen", "Zhen"): "Shake",
    ("Gen", "Gen"): "Bound",
    ("Xun", "Gen"): "Infiltrating",
    ("Zhen", "Dui"): "Converting The Maiden",
    ("Zhen", "Li"): "Abounding",
    ("Li", "Gen"): "Sojourning",
    ("Xun", "Xun"): "Ground",
    ("Dui", "Dui"): "Open",
    ("Xun", "Kan"): "Dispersing",
    ("Kan", "Dui"): "Articulating",
    ("Xun", "Dui"): "Center Confirming",
    ("Zhen", "Gen"): "Small Exceeding",
    ("Kan", "Li"): "Already Fording",
    ("Li", "Kan"): "Not Yet Fording",
}


@dataclass(frozen=True)
class YijingInput:
    question: str
    casting_method: str
    numbers: tuple[int, ...] = ()
    cast_datetime: datetime | None = None
    moving_line: int | None = None
    background: str = ""


def normalize_casting_method(value: str) -> str:
    text = (value or "").strip().lower()
    aliases = {
        "number": "numbers",
        "numeric": "numbers",
        "numbers": "numbers",
        "meihua_numbers": "numbers",
        "time": "time",
        "datetime": "time",
        "meihua_time": "time",
    }
    return aliases.get(text, text)


def parse_numbers(value: Any) -> tuple[int, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(int(item) for item in value)
    matches = re.findall(r"-?\d+", str(value))
    return tuple(int(item) for item in matches)


def modulo_1_indexed(value: int, base: int) -> int:
    remainder = value % base
    return base if remainder == 0 else remainder


def trigram_from_number(value: int) -> dict[str, Any]:
    number = modulo_1_indexed(value, 8)
    key, name, lines, image = TRIGRAM_BY_NUMBER[number]
    return {"number": number, "key": key, "name": name, "lines": list(lines), "image": image}


def build_lines(lower: dict[str, Any], upper: dict[str, Any]) -> list[int]:
    return lower["lines"] + upper["lines"]


def trigram_from_lines(lines: list[int]) -> dict[str, Any]:
    item = TRIGRAM_BY_LINES[tuple(lines)]
    return {"key": item["key"], "name": item["name"], "lines": list(lines), "image": item["image"]}


def describe_hexagram(lines: list[int]) -> dict[str, Any]:
    lower = trigram_from_lines(lines[:3])
    upper = trigram_from_lines(lines[3:])
    return {
        "name": HEXAGRAM_NAMES.get((upper["name"], lower["name"]), f'{upper["name"]} over {lower["name"]}'),
        "upper_trigram": upper,
        "lower_trigram": lower,
        "lines": lines,
        "yang_line_count": sum(lines),
        "yin_line_count": len(lines) - sum(lines),
    }


def mutual_hexagram(lines: list[int]) -> dict[str, Any]:
    return describe_hexagram(lines[1:4] + lines[2:5])


def opposite_hexagram(lines: list[int]) -> dict[str, Any]:
    return describe_hexagram([0 if line else 1 for line in lines])


def reverse_hexagram(lines: list[int]) -> dict[str, Any]:
    return describe_hexagram(list(reversed(lines)))


def changed_hexagram(lines: list[int], moving_line: int) -> dict[str, Any]:
    updated = lines[:]
    updated[moving_line - 1] = 0 if updated[moving_line - 1] else 1
    return describe_hexagram(updated)


def moving_line_from_numbers(numbers: tuple[int, ...]) -> int:
    if len(numbers) >= 3:
        return modulo_1_indexed(numbers[2], 6)
    return modulo_1_indexed(sum(numbers), 6)


def cast_from_numbers(numbers: tuple[int, ...], moving_line_override: int | None = None) -> tuple[dict[str, Any], dict[str, Any], int]:
    if len(numbers) < 2:
        raise ValueError("numbers casting requires at least two integers")
    upper = trigram_from_number(numbers[0])
    lower = trigram_from_number(numbers[1])
    moving_line = moving_line_override or moving_line_from_numbers(numbers)
    return upper, lower, moving_line


def cast_from_time(value: datetime, moving_line_override: int | None = None) -> tuple[dict[str, Any], dict[str, Any], int]:
    upper_seed = value.year + value.month + value.day
    lower_seed = upper_seed + value.hour
    moving_seed = lower_seed + value.minute
    upper = trigram_from_number(upper_seed)
    lower = trigram_from_number(lower_seed)
    moving_line = moving_line_override or modulo_1_indexed(moving_seed, 6)
    return upper, lower, moving_line


def line_position_note(moving_line: int) -> str:
    if moving_line in {1, 6}:
        return "The moving line sits on an outer edge, so initiation or closure pressure is high."
    if moving_line in {3, 4}:
        return "The moving line sits near the pivot of the hexagram, so transition pressure is central."
    return "The moving line sits in a support position, so the shift is more contextual than absolute."


def calculate_yijing(data: YijingInput) -> dict[str, Any]:
    method = normalize_casting_method(data.casting_method)
    if method not in {"numbers", "time"}:
        raise ValueError("casting_method must be one of: numbers, time")

    if method == "numbers":
        upper, lower, moving_line = cast_from_numbers(data.numbers, data.moving_line)
        raw_input = {
            "question": data.question,
            "casting_method": method,
            "numbers": list(data.numbers),
            "moving_line_override": data.moving_line,
        }
    else:
        if not data.cast_datetime:
            raise ValueError("time casting requires cast_datetime")
        upper, lower, moving_line = cast_from_time(data.cast_datetime, data.moving_line)
        raw_input = {
            "question": data.question,
            "casting_method": method,
            "cast_datetime": data.cast_datetime.isoformat(sep=" ", timespec="minutes"),
            "moving_line_override": data.moving_line,
        }

    base_lines = build_lines(lower, upper)
    base = describe_hexagram(base_lines)
    changed = changed_hexagram(base_lines, moving_line)
    mutual = mutual_hexagram(base_lines)
    opposite = opposite_hexagram(base_lines)
    reverse = reverse_hexagram(base_lines)

    question_type = "decision" if any(token in data.question.lower() for token in ["should", "whether", "if "]) else "general"
    judgement_candidates = [
        f"Base hexagram: {base['name']}. Changed hexagram: {changed['name']}.",
        line_position_note(moving_line),
        (
            "The base figure is yang-heavy, which points to stronger outward momentum."
            if base["yang_line_count"] >= 4
            else "The base figure is yin-heavy, which points to containment, waiting, or internal adjustment."
        ),
    ]

    return {
        "system": "yijing_and_symbolism",
        "raw_input": raw_input,
        "normalized_input": {
            "question": data.question.strip(),
            "casting_method": method,
            "moving_line": moving_line,
            "background": data.background.strip(),
        },
        "derived_factors": {
            "base_hexagram": base,
            "changed_hexagram": changed,
            "mutual_hexagram": mutual,
            "opposite_hexagram": opposite,
            "reverse_hexagram": reverse,
        },
        "question_mapping": {
            "question_type": question_type,
            "upper_image": base["upper_trigram"]["image"],
            "lower_image": base["lower_trigram"]["image"],
        },
        "judgement_candidates": judgement_candidates,
        "missing_inputs": [],
        "risk_flags": [
            "Local Yijing output computes the hexagram structure directly, but interpretive text is intentionally constrained.",
            "No line-text corpus is bundled yet, so this result emphasizes structure over commentary.",
        ],
        "confidence": "medium",
    }
