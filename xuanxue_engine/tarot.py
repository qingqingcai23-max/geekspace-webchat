from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


MAJOR_ARCANA = {
    "the fool": {"number": 0, "themes": ["beginning", "risk", "trust"]},
    "the magician": {"number": 1, "themes": ["agency", "skill", "focus"]},
    "the high priestess": {"number": 2, "themes": ["intuition", "silence", "hidden knowledge"]},
    "the empress": {"number": 3, "themes": ["growth", "nurture", "fertility"]},
    "the emperor": {"number": 4, "themes": ["order", "authority", "structure"]},
    "the hierophant": {"number": 5, "themes": ["tradition", "teaching", "institution"]},
    "the lovers": {"number": 6, "themes": ["choice", "bond", "alignment"]},
    "the chariot": {"number": 7, "themes": ["will", "direction", "control"]},
    "strength": {"number": 8, "themes": ["courage", "restraint", "heart"]},
    "the hermit": {"number": 9, "themes": ["withdrawal", "search", "clarity"]},
    "wheel of fortune": {"number": 10, "themes": ["cycle", "turning point", "change"]},
    "justice": {"number": 11, "themes": ["balance", "truth", "accountability"]},
    "the hanged man": {"number": 12, "themes": ["pause", "reversal", "sacrifice"]},
    "death": {"number": 13, "themes": ["ending", "release", "transition"]},
    "temperance": {"number": 14, "themes": ["blending", "patience", "measure"]},
    "the devil": {"number": 15, "themes": ["attachment", "temptation", "entanglement"]},
    "the tower": {"number": 16, "themes": ["shock", "collapse", "exposure"]},
    "the star": {"number": 17, "themes": ["hope", "healing", "guidance"]},
    "the moon": {"number": 18, "themes": ["ambiguity", "fear", "imagination"]},
    "the sun": {"number": 19, "themes": ["clarity", "vitality", "success"]},
    "judgement": {"number": 20, "themes": ["reckoning", "calling", "renewal"]},
    "the world": {"number": 21, "themes": ["completion", "integration", "arrival"]},
}

MAJOR_ARCANA_ALIASES = {
    "\u611a\u8005": "the fool",
    "\u9b54\u672f\u5e08": "the magician",
    "\u5973\u796d\u53f8": "the high priestess",
    "\u5973\u7687": "the empress",
    "\u7687\u5e1d": "the emperor",
    "\u6559\u7687": "the hierophant",
    "\u604b\u4eba": "the lovers",
    "\u6218\u8f66": "the chariot",
    "\u529b\u91cf": "strength",
    "\u9690\u58eb": "the hermit",
    "\u547d\u8fd0\u4e4b\u8f6e": "wheel of fortune",
    "\u6b63\u4e49": "justice",
    "\u5012\u540a\u4eba": "the hanged man",
    "\u6b7b\u795e": "death",
    "\u8282\u5236": "temperance",
    "\u6076\u9b54": "the devil",
    "\u9ad8\u5854": "the tower",
    "\u661f\u661f": "the star",
    "\u6708\u4eae": "the moon",
    "\u592a\u9633": "the sun",
    "\u5ba1\u5224": "judgement",
    "\u4e16\u754c": "the world",
}

MINOR_SUIT_ALIASES = {
    "\u6743\u6756": "wands",
    "\u6b0a\u6756": "wands",
    "\u5723\u676f": "cups",
    "\u8056\u76c3": "cups",
    "\u5b9d\u5251": "swords",
    "\u5bf6\u528d": "swords",
    "\u661f\u5e01": "pentacles",
    "\u91d1\u5e01": "pentacles",
    "\u9322\u5e63": "pentacles",
}

MINOR_RANK_ALIASES = {
    "\u9996\u724c": "ace",
    "\u4e00": "ace",
    "\u4e8c": "two",
    "\u4e09": "three",
    "\u56db": "four",
    "\u4e94": "five",
    "\u516d": "six",
    "\u4e03": "seven",
    "\u516b": "eight",
    "\u4e5d": "nine",
    "\u5341": "ten",
    "\u4f8d\u4ece": "page",
    "\u4f8d\u8005": "page",
    "\u4f8d\u536b": "page",
    "\u9a0e\u58eb": "knight",
    "\u7687\u540e": "queen",
    "\u738b\u540e": "queen",
    "\u56fd\u738b": "king",
    "\u570b\u738b": "king",
}

SUIT_ALIASES = {
    "wands": {"element": "fire"},
    "cups": {"element": "water"},
    "swords": {"element": "air"},
    "pentacles": {"element": "earth"},
    "coins": {"element": "earth"},
}

SPREADS = {
    "single": ["focus"],
    "three_card": ["past", "present", "future"],
    "celtic_cross": ["present", "challenge", "root", "past", "goal", "near_future", "self", "environment", "hopes_fears", "outcome"],
}

RANK_VALUE = {
    "ace": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "page": 11,
    "knight": 12,
    "queen": 13,
    "king": 14,
}


@dataclass(frozen=True)
class TarotInput:
    question: str
    spread: str
    cards: tuple[str, ...]
    time_range: str = ""


def normalize_spread(value: str) -> str:
    text = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {"single_card": "single", "three": "three_card", "3_card": "three_card"}
    return aliases.get(text, text)


def normalize_cards(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    parts = re.split(r"[,\n;|]+", str(value))
    return tuple(part.strip() for part in parts if part.strip())


def parse_orientation(text: str) -> tuple[str, str]:
    lowered = text.lower()
    if "reversed" in lowered or "\u9006\u4f4d" in text:
        cleaned = re.sub(r"(?i)\breversed\b", "", text).replace("\u9006\u4f4d", "").strip(" -()")
        return cleaned, "reversed"
    if "upright" in lowered or "\u6b63\u4f4d" in text:
        cleaned = re.sub(r"(?i)\bupright\b", "", text).replace("\u6b63\u4f4d", "").strip(" -()")
        return cleaned, "upright"
    return text.strip(), "upright"


def parse_card(raw_card: str) -> dict[str, Any]:
    name_text, orientation = parse_orientation(raw_card)
    name_text = (
        name_text.strip()
        .replace("\u8076\u76c3", "\u5723\u676f")
        .replace("\u5bf6\u528d", "\u5b9d\u5251")
        .replace("\u6b0a\u6756", "\u6743\u6756")
        .replace("\u9322\u5e63", "\u661f\u5e01")
        .replace("\u91d1\u5e01", "\u661f\u5e01")
        .replace("\u4f8d\u8005", "\u4f8d\u4ece")
        .replace("\u4f8d\u536b", "\u4f8d\u4ece")
        .replace("\u738b\u540e", "\u7687\u540e")
        .replace("\u570b\u738b", "\u56fd\u738b")
    )
    lookup = name_text.strip().lower()
    lookup = MAJOR_ARCANA_ALIASES.get(name_text.strip(), lookup)
    if lookup in MAJOR_ARCANA:
        card = MAJOR_ARCANA[lookup]
        return {
            "name": lookup.title(),
            "arcana": "major",
            "number": card["number"],
            "orientation": orientation,
            "themes": card["themes"],
        }

    chinese_minor = re.match(
        r"^(?P<suit>[\u6743\u6b0a\u5723\u8056\u5b9d\u5bf6\u661f\u91d1\u9322][\u6756\u676f\u76c3\u5251\u528d\u5e01\u5e63])(?P<rank>[\u9996\u724c\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u4f8d\u8005\u4ece\u9a0e\u58eb\u7687\u540e\u738b\u56fd\u570b]+)$",
        name_text.strip(),
    )
    if chinese_minor:
        suit = MINOR_SUIT_ALIASES.get(chinese_minor.group("suit"))
        raw_rank = MINOR_RANK_ALIASES.get(chinese_minor.group("rank"))
        if suit and raw_rank:
            rank = RANK_VALUE[raw_rank]
            return {
                "name": f"{raw_rank.title()} of {suit.title()}",
                "arcana": "minor",
                "number": rank,
                "orientation": orientation,
                "suit": suit,
                "element": SUIT_ALIASES[suit]["element"],
                "themes": [suit, SUIT_ALIASES[suit]["element"], "flow" if suit in {"cups", "wands"} else "structure"],
            }

    minor = re.match(r"(?i)^(ace|two|three|four|five|six|seven|eight|nine|ten|page|knight|queen|king|\d+)\s+of\s+(wands|cups|swords|pentacles|coins)$", lookup)
    if minor:
        raw_rank = minor.group(1)
        rank = int(raw_rank) if raw_rank.isdigit() else RANK_VALUE[raw_rank]
        suit = minor.group(2)
        return {
            "name": f"{raw_rank.title()} of {suit.title()}",
            "arcana": "minor",
            "number": rank,
            "orientation": orientation,
            "suit": suit,
            "element": SUIT_ALIASES[suit]["element"],
            "themes": [suit, SUIT_ALIASES[suit]["element"], "flow" if suit in {"cups", "wands"} else "structure"],
        }
    raise ValueError(f"unrecognized tarot card: {raw_card}")


def spread_positions(spread: str, count: int) -> list[str]:
    if spread in SPREADS:
        labels = SPREADS[spread]
        if len(labels) != count:
            raise ValueError(f"spread {spread} expects {len(labels)} cards, got {count}")
        return labels
    return [f"position_{index}" for index in range(1, count + 1)]


def describe_card(card: dict[str, Any], position: str) -> str:
    theme_text = ", ".join(card["themes"][:2])
    if card["orientation"] == "reversed":
        return f"{position}: {card['name']} reversed emphasizes blockage, delay, or inversion around {theme_text}."
    return f"{position}: {card['name']} upright emphasizes expression, clarity, or activation around {theme_text}."


def calculate_tarot(data: TarotInput) -> dict[str, Any]:
    spread = normalize_spread(data.spread)
    cards = [parse_card(item) for item in data.cards]
    positions = spread_positions(spread, len(cards))
    positioned_cards = [{**card, "position": position} for card, position in zip(cards, positions, strict=True)]

    suit_counts: dict[str, int] = {}
    element_counts: dict[str, int] = {}
    reversed_count = 0
    major_count = 0
    for card in positioned_cards:
        if card["orientation"] == "reversed":
            reversed_count += 1
        if card["arcana"] == "major":
            major_count += 1
        if card.get("suit"):
            suit_counts[card["suit"]] = suit_counts.get(card["suit"], 0) + 1
        if card.get("element"):
            element_counts[card["element"]] = element_counts.get(card["element"], 0) + 1

    judgement_candidates = [describe_card(card, card["position"]) for card in positioned_cards]
    if major_count >= max(1, len(cards) // 2):
        judgement_candidates.append("A major-arcana-heavy spread suggests the issue is structural rather than minor or passing.")
    if reversed_count >= max(1, len(cards) // 2):
        judgement_candidates.append("Reversed cards dominate the spread, so obstruction, delay, or internal conflict should be treated as central.")

    return {
        "system": "tarot",
        "raw_input": {
            "question": data.question,
            "spread": data.spread,
            "cards": list(data.cards),
            "time_range": data.time_range,
        },
        "normalized_input": {
            "question": data.question.strip(),
            "spread": spread,
            "card_count": len(cards),
        },
        "derived_factors": {
            "cards": positioned_cards,
            "major_arcana_count": major_count,
            "reversed_count": reversed_count,
            "suit_counts": suit_counts,
            "element_counts": element_counts,
        },
        "question_mapping": {
            "time_range": data.time_range.strip(),
            "spread_positions": positions,
        },
        "judgement_candidates": judgement_candidates,
        "missing_inputs": [],
        "risk_flags": [
            "This local tarot engine requires explicit drawn cards and will not fabricate random pulls.",
            "Interpretation is rule-based and intentionally narrower than a human reader's narrative synthesis.",
        ],
        "confidence": "medium",
    }
