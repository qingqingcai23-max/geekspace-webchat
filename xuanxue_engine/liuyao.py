from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .yijing import (
    YijingInput,
    build_lines,
    calculate_yijing,
    cast_from_numbers,
    cast_from_time,
    changed_hexagram,
    describe_hexagram,
    mutual_hexagram,
    normalize_casting_method,
    parse_numbers,
)


TRIGRAM_ELEMENTS = {
    "Qian": "metal",
    "Dui": "metal",
    "Li": "fire",
    "Zhen": "wood",
    "Xun": "wood",
    "Kan": "water",
    "Gen": "earth",
    "Kun": "earth",
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


@dataclass(frozen=True)
class LiuyaoInput:
    question: str
    casting_method: str
    numbers: tuple[int, ...] = ()
    cast_datetime: datetime | None = None
    moving_line: int | None = None
    background: str = ""


def element_relation(body_element: str, use_element: str) -> tuple[str, str]:
    if body_element == use_element:
        return "peer", "Body and use share the same element, which points to parity and direct resonance."
    if GENERATES[use_element] == body_element:
        return "support", "Use generates body, which usually reads as support, resources, or external help."
    if GENERATES[body_element] == use_element:
        return "drain", "Body generates use, which usually reads as expenditure, output, or energy drain."
    if CONTROLS[body_element] == use_element:
        return "control", "Body controls use, which usually reads as initiative, leverage, or active management."
    return "pressure", "Use controls body, which usually reads as pressure, constraint, or external dominance."


def line_zone_note(moving_line: int) -> str:
    if moving_line in {1, 2}:
        return "The movement begins from the lower trigram, so the issue is still close to the starting condition."
    if moving_line == 3:
        return "The third line is a threshold line, so the matter is near transition but not settled."
    if moving_line in {4, 5}:
        return "The movement sits in the upper trigram, so external conditions and visible outcomes matter more."
    return "The top line moves, which often points to closure, reversal, or overextension."


def calculate_liuyao(data: LiuyaoInput) -> dict[str, Any]:
    method = normalize_casting_method(data.casting_method)
    if method not in {"numbers", "time"}:
        raise ValueError("casting_method must be numbers or time")

    if method == "numbers":
        upper, lower, moving_line = cast_from_numbers(parse_numbers(data.numbers), data.moving_line)
        used_inputs: dict[str, Any] = {"question": data.question, "casting_method": method, "numbers": list(parse_numbers(data.numbers))}
    else:
        if not data.cast_datetime:
            raise ValueError("time casting requires cast_datetime")
        upper, lower, moving_line = cast_from_time(data.cast_datetime, data.moving_line)
        used_inputs = {
            "question": data.question,
            "casting_method": method,
            "cast_datetime": data.cast_datetime.isoformat(sep=" ", timespec="minutes"),
        }

    lines = build_lines(lower, upper)
    base_hexagram = describe_hexagram(lines)
    changed = changed_hexagram(lines, moving_line)
    mutual = mutual_hexagram(lines)
    yijing_result = calculate_yijing(
        YijingInput(
            question=data.question,
            casting_method=method,
            numbers=parse_numbers(data.numbers),
            cast_datetime=data.cast_datetime,
            moving_line=moving_line,
            background=data.background,
        )
    )

    if moving_line <= 3:
        body = base_hexagram["upper_trigram"]
        use = base_hexagram["lower_trigram"]
    else:
        body = base_hexagram["lower_trigram"]
        use = base_hexagram["upper_trigram"]

    body_element = TRIGRAM_ELEMENTS[body["name"]]
    use_element = TRIGRAM_ELEMENTS[use["name"]]
    relation_key, relation_note = element_relation(body_element, use_element)

    strength_map = {
        "body_element": body_element,
        "use_element": use_element,
        "relation": relation_key,
        "moving_line": moving_line,
    }

    return {
        "system": "liuyao_and_meihua",
        "question_type": "timing",
        "used_inputs": used_inputs,
        "missing_inputs": [],
        "raw_chart": {
            "base_hexagram": base_hexagram,
            "changed_hexagram": changed,
            "mutual_hexagram": mutual,
        },
        "derived_factors": {
            "body_trigram": body,
            "use_trigram": use,
            "body_use_relation": strength_map,
            "yijing_structure": yijing_result["derived_factors"],
        },
        "strength_map": strength_map,
        "question_mapping": {
            "body_focus": body["image"],
            "use_focus": use["image"],
        },
        "primary_finding": f"Body trigram is {body['name']} and use trigram is {use['name']}; relation is {relation_key}.",
        "supporting_signals": [
            f"Base hexagram: {base_hexagram['name']}; changed hexagram: {changed['name']}.",
            relation_note,
            line_zone_note(moving_line),
        ],
        "judgement_candidates": [
            relation_note,
            line_zone_note(moving_line),
            f"Mutual hexagram {mutual['name']} describes the internal pattern behind the visible question.",
        ],
        "risk_flags": [
            "This implemented branch is a meihua-style body/use engine built on real hexagram calculation.",
            "Full najia, six-kinship, and six-spirit tables are not bundled yet, so this does not claim to be a complete orthodox six-yao reading.",
        ],
        "time_window": "Use the body/use relation first, then read the changed hexagram as the next phase.",
        "confidence": "medium",
        "rules_path": [
            "hexagram casting",
            "moving line",
            "body/use assignment",
            "five-element relation",
        ],
    }
