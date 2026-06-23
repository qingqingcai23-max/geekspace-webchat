from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import Any


BRIDGE_PATH = Path(__file__).with_name("qimen_bridge.mjs")


@dataclass(frozen=True)
class QimenDunjiaInput:
    event_datetime: datetime
    timezone: str = "Asia/Shanghai"
    question: str = ""
    pan_type: str = "zhuan"
    ju_method: str = "chaibu"
    zhi_fu_ji_gong: str = "ji_liuyi"
    time_source: str = "explicit"


def run_bridge(payload: dict[str, Any]) -> dict[str, Any]:
    completed = subprocess.run(
        ["node", str(BRIDGE_PATH)],
        input=json.dumps(payload, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError((completed.stderr or completed.stdout or "qimen bridge failed").strip())
    return json.loads(completed.stdout)


def active_palaces(palaces: list[dict[str, Any]]) -> list[int]:
    ranked: list[tuple[int, int]] = []
    for palace in palaces:
        score = 0
        score += len(list(palace.get("formations") or [])) * 3
        score += 2 if palace.get("isYiMa") else 0
        score += 1 if not palace.get("isKongWang") else 0
        score += 1 if palace.get("star") else 0
        score += 1 if palace.get("gate") else 0
        ranked.append((score, int(palace.get("palaceIndex", 0))))
    ranked.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    return [palace_index for score, palace_index in ranked if score > 0][:4]


def format_time_source(value: str) -> str:
    mapping = {
        "explicit": "explicit divination time",
        "structured-input": "structured divination time",
        "event_datetime": "event datetime",
        "date+time": "date plus time fields",
        "question-datetime": "datetime parsed from the question",
        "inferred-current-time": "current ask-time fallback",
    }
    return mapping.get(value, value)


def calculate_qimen_dunjia(data: QimenDunjiaInput) -> dict[str, Any]:
    raw = run_bridge(
        {
            "year": data.event_datetime.year,
            "month": data.event_datetime.month,
            "day": data.event_datetime.day,
            "hour": data.event_datetime.hour,
            "minute": data.event_datetime.minute,
            "timezone": data.timezone,
            "question": data.question,
            "panType": data.pan_type,
            "juMethod": data.ju_method,
            "zhiFuJiGong": data.zhi_fu_ji_gong,
        }
    )
    date_info = dict(raw.get("dateInfo") or {})
    palaces = list(raw.get("palaces") or [])
    zhi_fu = dict(raw.get("zhiFu") or {})
    zhi_shi = dict(raw.get("zhiShi") or {})
    kong_wang = dict(raw.get("kongWang") or {})
    yi_ma = dict(raw.get("yiMa") or {})
    active = active_palaces(palaces)

    time_note = ""
    if data.time_source != "explicit":
        time_note = f"Using a {format_time_source(data.time_source)} chart. "

    primary_finding = (
        f"{time_note}Chart resolves to {str(raw.get('dunType') or '').title()} Dun {raw.get('juNumber')} "
        f"with Zhi Fu {zhi_fu.get('star', '')} in palace {zhi_fu.get('palace', '')} and "
        f"Zhi Shi {zhi_shi.get('gate', '')} in palace {zhi_shi.get('palace', '')}. "
        f"Active focus clusters around palaces {', '.join(str(item) for item in active) or 'none'}."
    )

    supporting_signals = [
        f"Solar term is {date_info.get('solarTerm', '')}, with yuan {raw.get('yuan', '')} and xun shou {raw.get('xunShou', '')}.",
        f"Question time resolves to {data.event_datetime.isoformat(sep=' ', timespec='minutes')} in {data.timezone}.",
        f"Global formations: {', '.join(list(raw.get('globalFormations') or [])[:6]) or 'none detected'}.",
        f"Day-empty palaces: {', '.join(str(item) for item in list((kong_wang.get('dayKong') or {}).get('palaces') or [])) or 'none'}; "
        f"hour-empty palaces: {', '.join(str(item) for item in list((kong_wang.get('hourKong') or {}).get('palaces') or [])) or 'none'}.",
    ]
    if yi_ma:
        supporting_signals.append(
            f"Yi Ma falls in palace {yi_ma.get('palace', '')} with branch {yi_ma.get('branch', '')}."
        )

    risk_flags = [
        "This local qimen_dunjia engine uses taibu-core and its taobi-backed charting implementation.",
        "Pan style, fixed-ju method, and zhi-fu lodging rules still vary across lineages; this engine keeps the method explicit in the output.",
        "The current output focuses on chart structure and active formations; school-specific judgement rhetoric should still be treated cautiously.",
    ]
    if data.time_source == "inferred-current-time":
        risk_flags.append(
            "No explicit divination time was supplied, so the engine fell back to the current ask time."
        )

    return {
        "system": "qimen_dunjia",
        "question_type": "timing",
        "used_inputs": {
            "event_datetime": data.event_datetime.isoformat(sep=" ", timespec="minutes"),
            "timezone": data.timezone,
            "question": data.question,
            "pan_type": data.pan_type,
            "ju_method": data.ju_method,
            "zhi_fu_ji_gong": data.zhi_fu_ji_gong,
            "time_source": data.time_source,
        },
        "missing_inputs": [],
        "derived_factors": {
            "dun_type": str(raw.get("dunType") or ""),
            "ju_number": int(raw.get("juNumber", 0)),
            "yuan": str(raw.get("yuan") or ""),
            "xun_shou": str(raw.get("xunShou") or ""),
            "solar_term": str(date_info.get("solarTerm") or ""),
            "solar_term_range": str(date_info.get("solarTermRange") or ""),
            "zhi_fu": zhi_fu,
            "zhi_shi": zhi_shi,
            "active_palaces": active,
            "kong_wang": kong_wang,
            "yi_ma": yi_ma,
            "global_formations": list(raw.get("globalFormations") or []),
        },
        "raw_chart": {
            "date_info": date_info,
            "si_zhu": dict(raw.get("siZhu") or {}),
            "palaces": palaces,
            "month_phase": dict(raw.get("monthPhase") or {}),
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "This chart is tied to the divination moment and is best used for near-term timing, action, and situational readouts.",
        "confidence": "medium",
        "rules_path": [
            "divination-time normalization",
            "qimen chart generation",
            "zhi-fu and zhi-shi placement",
            "kong-wang and yi-ma extraction",
            "active palace clustering",
        ],
    }
